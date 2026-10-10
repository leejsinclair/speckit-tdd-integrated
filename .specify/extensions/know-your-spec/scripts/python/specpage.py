#!/usr/bin/env python3
"""Know Your Spec's spec page: ``spec.md`` as a read-only page in the browser.

    python3 specpage.py serve --spec <path/to/spec.md>            start it (prints one JSON line)
    python3 specpage.py serve --spec <path/to/spec.md> --status   is one running, and where
    python3 specpage.py serve --spec <path/to/spec.md> --stop     stop it

Standard library only. The page shows the spec and nothing else: it has no route that changes
anything, and the Comprehension Checkpoint itself stays in the conversation. The one file this
script writes is a runtime file in the OS temporary directory, outside the repository, removed
when the page stops (spec FR-012, SC-005).

The Markdown renderer (``tokenize`` to ``render_markdown``) is copied from the engineer-in-the-loop
extension's ``eil/pagerender.py``, itself copied from the rich specification viewer,
``rich-specification-viewer/specview.py`` at commit a267058. ``find_definitions`` comes from the
viewer. Adaptations:

* a reference code is any ``XX-000`` style id or ``T000`` task id, so ``FR-012``, ``SC-005`` and a
  project's own prefixes all resolve; a code this spec does not define is left as plain text;
* a page whose spec has a Mermaid diagram loads the viewer's diagram script (``MERMAID_URL``) and
  draws it in the browser; if the script cannot be loaded the source stays. A spec without a
  diagram loads nothing from anywhere. This script itself never fetches anything.

The server follows the same extension's ``eil/reviewpage.py``: one request at a time, a ``Host``
check and a per-process token on every request. Unlike it, the default bind is every interface
(``0.0.0.0``) so that a forwarded port reaches the page; ``--host 127.0.0.1`` keeps it to this machine. Tests: ``tests/unit/``.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import signal
import socket
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

# ---- reference codes

CODE = r"(?:[A-Z]{2,5}-\d{3,}|T\d{3,})"
CODE_RE = re.compile(r"\b" + CODE + r"\b")
ITEM_DEF_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*(" + CODE + r")\*\*\s*:")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
HEADING_DEF_RE = re.compile(r"^(" + CODE + r")\b")
TASK_DEF_RE = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(T\d{3,})\b")


def anchor_for(code: str) -> str:
    return code


# ---- Markdown renderer (copied; see the module docstring)

FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([^\s`]*)")
EIL_BEGIN_RE = re.compile(r"^\s*<!--\s*eil:begin\s+(\w+)\s*-->\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
QUOTE_RE = re.compile(r"^ {0,3}>\s?(.*)$")
TASK_BOX_RE = re.compile(r"^\[([ xX])\]\s+(.*)$", re.S)
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
STRONG_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
EM_STAR_RE = re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])")
EM_UNDER_RE = re.compile(r"(?<!\w)_(?=\S)(.+?)(?<=\S)_(?!\w)")


@dataclass
class Fence:
    info: str
    lines: list[str]


def tokenize(text: str) -> tuple[list[Any], list[tuple[str, str]]]:
    """Split a document into line strings and Fence tokens, dropping HTML comments and ``eil:``
    regions and blocks. Returns the tokens and the dropped ``eil:`` fenced blocks as ``(kind, body)``."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    tokens: list[Any] = []
    eil_blocks: list[tuple[str, str]] = []
    i = 0
    in_comment = False
    while i < len(lines):
        line = lines[i]
        if in_comment:
            end = line.find("-->")
            if end < 0:
                i += 1
                continue
            in_comment = False
            line = line[end + 3 :]
            if not line.strip():
                tokens.append("")
                i += 1
                continue
        begin = EIL_BEGIN_RE.match(line)
        if begin:
            end_marker = re.compile(r"^\s*<!--\s*eil:end\s+" + re.escape(begin.group(1)) + r"\s*-->\s*$")
            j = i + 1
            while j < len(lines) and not end_marker.match(lines[j]):
                j += 1
            i = j + 1
            continue
        fence = FENCE_OPEN_RE.match(line)
        if fence:
            marker, info = fence.group(1), fence.group(2)
            close = re.compile(r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$")
            body = []
            j = i + 1
            while j < len(lines) and not close.match(lines[j]):
                body.append(lines[j])
                j += 1
            if info.startswith("eil:"):
                eil_blocks.append((info[4:], "\n".join(body)))
            else:
                tokens.append(Fence(info.lower(), body))
            i = j + 1
            continue
        # HTML comments, possibly several on one line or spanning lines
        out = ""
        rest = line
        while "<!--" in rest:
            before, _, after = rest.partition("<!--")
            out += before
            end = after.find("-->")
            if end < 0:
                in_comment = True
                rest = ""
                break
            rest = after[end + 3 :]
        out += rest
        tokens.append(out if out.strip() or out == line else "")
        i += 1
    return tokens, eil_blocks


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", slug) or "section"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def safe_href(href: str) -> str:
    scheme = href.split(":", 1)[0].lower() if ":" in href.split("/", 1)[0] else ""
    if scheme and scheme not in ("http", "https", "mailto"):
        return "#"
    return href


class RenderContext:
    """What the renderer needs from its caller: how to mark a code, and whether it renders a
    preview (no marking, diagrams replaced by a note)."""

    def __init__(self, marker: Any = None, tooltip: bool = False) -> None:
        self.marker = marker
        self.tooltip = tooltip
        self.slugs: dict[str, int] = {}

    def unique_id(self, base: str) -> str:
        count = self.slugs.get(base, 0)
        self.slugs[base] = count + 1
        return base if count == 0 else "%s-%d" % (base, count + 1)


def render_inline(text: str, ctx: RenderContext, skip_code: str | None = None) -> str:
    """Escape first, then inline code, links and emphasis, then mark codes outside code."""
    held: list[str] = []

    def hold(fragment: str) -> str:
        held.append(fragment)
        return "\x00%d\x00" % (len(held) - 1)

    text = CODE_SPAN_RE.sub(lambda m: hold("<code>" + esc(m.group(2).strip()) + "</code>"), text)
    text = LINK_RE.sub(
        lambda m: hold('<a href="%s">%s</a>' % (esc(safe_href(m.group(2))), _emphasis(esc(m.group(1))))), text
    )
    text = _emphasis(esc(text))
    if ctx.marker is not None:
        skipped = [False]

        def mark(m: re.Match[str]) -> str:
            code = m.group(0)
            if skip_code == code and not skipped[0]:
                skipped[0] = True
                return code
            return str(ctx.marker(code))

        text = CODE_RE.sub(mark, text)
    return re.sub("\x00(\\d+)\x00", lambda m: held[int(m.group(1))], text)


def _emphasis(text: str) -> str:
    text = STRONG_RE.sub(r"<strong>\1</strong>", text)
    text = EM_STAR_RE.sub(r"<em>\1</em>", text)
    return EM_UNDER_RE.sub(r"<em>\1</em>", text)


def _is_blank(token: Any) -> bool:
    return isinstance(token, str) and not token.strip()


def _starts_block(token: Any, following: Any = None) -> bool:
    if isinstance(token, Fence):
        return True
    return bool(
        HEADING_RE.match(token)
        or HR_RE.match(token)
        or LIST_RE.match(token)
        or QUOTE_RE.match(token)
        or (token.lstrip().startswith("|") and isinstance(following, str) and TABLE_SEP_RE.match(following))
    )


def render_tokens(tokens: list[Any], ctx: RenderContext) -> str:
    out: list[str] = []
    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if isinstance(token, Fence):
            out.append(_render_fence(token, ctx))
            i += 1
            continue
        if not token.strip():
            i += 1
            continue
        heading = HEADING_RE.match(token)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2)
            code = HEADING_DEF_RE.match(title)
            ident = ctx.unique_id(anchor_for(code.group(1)) if code else slugify(title))
            body = render_inline(title, ctx, code.group(1) if code else None)
            out.append('<h%d id="%s">%s</h%d>' % (level, esc(ident), body, level))
            i += 1
            continue
        if HR_RE.match(token):
            out.append("<hr>")
            i += 1
            continue
        following = tokens[i + 1] if i + 1 < n else None
        if token.lstrip().startswith("|") and isinstance(following, str) and TABLE_SEP_RE.match(following):
            j = i + 2
            rows = [token]
            while j < n and isinstance(tokens[j], str) and tokens[j].lstrip().startswith("|"):
                rows.append(tokens[j])
                j += 1
            out.append(_render_table(rows, ctx))
            i = j
            continue
        if QUOTE_RE.match(token):
            inner = []
            while i < n and isinstance(tokens[i], str) and QUOTE_RE.match(tokens[i]):
                inner.append(QUOTE_RE.match(tokens[i]).group(1))  # type: ignore[union-attr]
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_tokens(inner, ctx))
            continue
        if LIST_RE.match(token):
            block = [token]
            first = LIST_RE.match(token)
            assert first is not None
            base, ordered = len(first.group(1)), first.group(2)[0].isdigit()

            def sibling_of_other_kind(line: str, base: int = base, ordered: bool = ordered) -> bool:
                m = LIST_RE.match(line)
                return bool(m) and len(m.group(1)) <= base and m.group(2)[0].isdigit() != ordered  # type: ignore[union-attr]

            j = i + 1
            while j < n and isinstance(tokens[j], str):
                line = tokens[j]
                if not line.strip():
                    nxt = tokens[j + 1] if j + 1 < n else None
                    if (
                        isinstance(nxt, str)
                        and nxt.strip()
                        and (LIST_RE.match(nxt) or nxt[:1] in " \t")
                        and not sibling_of_other_kind(nxt)
                    ):
                        block.append(line)
                        j += 1
                        continue
                    break
                if sibling_of_other_kind(line):
                    break
                if LIST_RE.match(line) or line[:1] in " \t":
                    block.append(line)
                    j += 1
                    continue
                if HEADING_RE.match(line) or HR_RE.match(line) or QUOTE_RE.match(line):
                    break
                block.append(line)  # lazy continuation of the last item
                j += 1
            out.append(_render_list(block, ctx))
            i = j
            continue
        para = [token]
        j = i + 1
        while j < n and isinstance(tokens[j], str) and tokens[j].strip():
            if _starts_block(tokens[j], tokens[j + 1] if j + 1 < n else None):
                break
            para.append(tokens[j])
            j += 1
        text = "\n".join(line.strip() for line in para)
        item = ITEM_DEF_RE.match(para[0])
        attr = ' id="%s"' % esc(ctx.unique_id(anchor_for(item.group(1)))) if item else ""
        out.append("<p%s>%s</p>" % (attr, render_inline(text, ctx, item.group(1) if item else None)))
        i = j
    return "\n".join(out)


def _render_fence(fence: Fence, ctx: RenderContext) -> str:
    source = "\n".join(fence.lines)
    if fence.info == "mermaid":
        if ctx.tooltip:
            return '<p class="diagram-note">A diagram is shown here in the document.</p>'
        return '<pre class="mermaid-src">%s</pre>' % esc(source)
    lang = ' class="language-%s"' % esc(fence.info) if fence.info else ""
    return "<pre><code%s>%s</code></pre>" % (lang, esc(source))


def _split_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    cells = re.split(r"(?<!\\)\|", row)
    return [cell.strip().replace("\\|", "|") for cell in cells]


def _render_table(rows: list[str], ctx: RenderContext) -> str:
    head = _split_row(rows[0])
    body = [_split_row(r) for r in rows[1:]]
    parts = ["<table><thead><tr>"]
    parts += ["<th>%s</th>" % render_inline(c, ctx) for c in head]
    parts.append("</tr></thead><tbody>")
    for cells in body:
        parts.append("<tr>" + "".join("<td>%s</td>" % render_inline(c, ctx) for c in cells) + "</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_list(lines: list[str], ctx: RenderContext) -> str:
    first = LIST_RE.match(lines[0])
    assert first is not None
    base = len(first.group(1).expandtabs(4))
    ordered = first.group(2)[0].isdigit()
    items: list[tuple[list[str], list[str], str]] = []  # (text lines, child lines, first raw line)
    for line in lines:
        m = LIST_RE.match(line)
        if m and len(m.group(1).expandtabs(4)) <= base:
            items.append(([m.group(3)], [], line))
            continue
        text_lines, child_lines, _ = items[-1]
        if not line.strip():
            if child_lines:
                child_lines.append("")
            continue
        if child_lines or m:
            child_lines.append(line)
        else:
            text_lines.append(line.strip())
    tag = "ol" if ordered else "ul"
    start = ""
    if ordered:
        number = int(re.match(r"\d+", first.group(2)).group(0))  # type: ignore[union-attr]
        if number != 1:
            start = ' start="%d"' % number
    out = ["<%s%s>" % (tag, start)]
    for text_lines, child_lines, raw in items:
        text = "\n".join(text_lines)
        ident = ""
        skip = None
        definition = ITEM_DEF_RE.match(raw) or TASK_DEF_RE.match(raw)
        if definition:
            skip = definition.group(1)
            ident = ' id="%s"' % esc(ctx.unique_id(anchor_for(skip)))
        box = TASK_BOX_RE.match(text)
        prefix = ""
        cls = ""
        if box:
            checked = " checked" if box.group(1) in "xX" else ""
            prefix = '<input type="checkbox" disabled%s> ' % checked
            text = box.group(2)
            cls = ' class="task"'
        body = prefix + render_inline(text, ctx, skip)
        if child_lines:
            indents = [len(c) - len(c.lstrip()) for c in child_lines if c.strip()]
            cut = min(indents) if indents else 0
            body += render_tokens([c[cut:] for c in child_lines], ctx)
        out.append("<li%s%s>%s</li>" % (ident, cls, body))
    out.append("</%s>" % tag)
    return "".join(out)


def render_markdown(text: str, ctx: RenderContext | None = None) -> str:
    tokens, _ = tokenize(text)
    return render_tokens(tokens, ctx or RenderContext())


# ---- definitions, for the preview shown on a reference code (copied from the viewer)


def find_definitions(text: str) -> dict[str, list[str]]:
    """Every code this document introduces, with the rendered HTML of each section defining it."""
    tokens, _ = tokenize(text)
    found: list[tuple[int, str, int]] = []  # (token index, code, heading level or 7)
    for index, token in enumerate(tokens):
        if isinstance(token, Fence):
            continue
        heading = HEADING_RE.match(token)
        if heading:
            code = HEADING_DEF_RE.match(heading.group(2))
            if code:
                found.append((index, code.group(1), len(heading.group(1))))
            continue
        item = TASK_DEF_RE.match(token) or ITEM_DEF_RE.match(token)
        if item:
            found.append((index, item.group(1), 7))
    starts = {index for index, *_ in found}
    definitions: dict[str, list[str]] = {}
    for index, code, level in found:
        end = index + 1
        while end < len(tokens):
            token = tokens[end]
            if end in starts:
                break
            if isinstance(token, str):
                heading = HEADING_RE.match(token)
                if heading and (level == 7 or len(heading.group(1)) <= level):
                    break
            end += 1
        section = render_tokens(tokens[index:end], RenderContext(tooltip=True))
        definitions.setdefault(code, []).append(section)
    return definitions


def reference_marker(text: str, used: set[str] | None = None) -> Any:
    """A ``RenderContext`` marker: a code defined once links to its definition and names that
    section's preview; one defined more than once carries the error mark; any other is plain.
    Each code it links is added to ``used``."""
    definitions = find_definitions(text)

    def mark(code: str) -> str:
        found = definitions.get(code, [])
        if not found:
            return esc(code)
        if len(found) > 1:
            why = "%s is defined %d times in this spec" % (code, len(found))
            return '<span class="ref-error" title="%s">%s</span>' % (esc(why), esc(code))
        if used is not None:
            used.add(code)
        return '<a class="ref" href="#%s" aria-describedby="pv-%s">%s</a>' % (esc(code), esc(code), esc(code))

    return mark


def previews_html(text: str, used: set[str]) -> str:
    """The preview of each linked code, kept after the document so a preview's own block elements
    never sit inside a paragraph. A preview carries no ids: the document's are the link targets."""
    definitions = find_definitions(text)
    return "".join(
        '<div class="preview" id="pv-%s" role="tooltip" hidden>%s</div>'
        % (esc(code), re.sub(r' id="[^"]*"', "", definitions[code][0]))
        for code in sorted(used)
    )


def anchors_of(text: str) -> dict[str, str]:
    """``{heading text: id}`` as ``render_markdown`` assigns them, so a link to a heading need not
    guess its id. A heading text used twice maps to its first id."""
    tokens, _ = tokenize(text)
    ctx = RenderContext()
    anchors: dict[str, str] = {}
    for token in tokens:
        heading = None if isinstance(token, Fence) else HEADING_RE.match(token)
        if not heading:
            continue
        title = heading.group(2)
        code = HEADING_DEF_RE.match(title)
        ident = ctx.unique_id(anchor_for(code.group(1)) if code else slugify(title))
        anchors.setdefault(title, ident)
    return anchors


# ---- the page

POLL_MS = 4000  # how often the page asks for ``/state``
STOPPED = "The spec page has stopped; ask the agent to start it again"
CHANGED = "spec.md changed since this page was loaded"
NOT_DRAWN = "This diagram could not be drawn; its source is shown above."
NOT_LOADED = "The diagram script could not be loaded, so this diagram is shown as its source."
OPEN_THE_ADDRESS = (
    "This page opens only from the address the agent gave you, which carries a one-time key. "
    "Open the address the agent gave you, including its ?t= part."
)


# The one thing a page may load from elsewhere, and only when its spec has a diagram to draw.
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
MERMAID_ORIGIN = "https://cdn.jsdelivr.net"
DIAGRAM_SOURCE = '<pre class="mermaid-src">'


def csp(nonce: str, diagrams: bool = False) -> str:
    """The page's policy: nothing loads from anywhere but the page itself. A page with a diagram
    may also load the diagram script, and takes the inline styles a drawn diagram carries."""
    scripts = f"'nonce-{nonce}'" + (f" {MERMAID_ORIGIN}" if diagrams else "")
    styles = "'unsafe-inline'" if diagrams else f"'nonce-{nonce}'"
    return (
        f"default-src 'none'; script-src {scripts}; style-src {styles}; connect-src 'self'; "
        "img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    )


def spec_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _head(title: str, nonce: str, metas: dict[str, str]) -> str:
    tags = "".join(f'<meta name="{esc(name)}" content="{esc(value)}">' for name, value in metas.items())
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{esc(title)}</title>{tags}<style nonce="{esc(nonce)}">{CSS}</style></head>'
    )


def message_page(text: str, nonce: str) -> str:
    """A short page with one message: never the token, never document text."""
    return _head("Spec page", nonce, {}) + f'<body><main class="message"><p>{esc(text)}</p></main></body></html>\n'


def spec_page(text: str, label: str, token: str, nonce: str) -> str:
    """``GET /``: the spec, rendered, read-only."""
    used: set[str] = set()
    document = render_markdown(text, RenderContext(marker=reference_marker(text, used)))
    metas = {"kys-token": token, "kys-hash": spec_hash(text)}
    if DIAGRAM_SOURCE in document:
        metas["kys-diagram-script"] = MERMAID_URL
    body = (
        f'<body><header class="top"><p class="story">{esc(label)}</p>'
        "<h1>Specification (read-only)</h1></header>"
        '<div id="notice" class="notice" role="status" aria-live="polite" hidden></div>'
        f'<main id="doc">{document}</main>{previews_html(text, used)}<script nonce="{esc(nonce)}">{SCRIPT}</script></body></html>\n'
    )
    return _head(f"Specification: {label}", nonce, metas) + body


CSS = """
:root{--fg:#1d1d1f;--bg:#fff;--muted:#5f6368;--line:#d0d4d9;--edge:#e0a800;--panel:#f6f7f9;--notice:#fde8e8;--error:#b3261e}
@media (prefers-color-scheme:dark){:root{--fg:#e8eaed;--bg:#16181b;--muted:#a0a4a8;--line:#3c4043;--edge:#c79500;--panel:#202327;--notice:#3a1d1d;--error:#f2b8b5}}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--fg);background:var(--bg);margin:0 auto;max-width:56rem;padding:0 1rem 4rem;line-height:1.55}
a{color:inherit}
header.top{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:.6rem 0;z-index:2}
header.top h1{font-size:1.15rem;margin:.1rem 0}.story{margin:0;color:var(--muted);font-size:.9rem}
.notice{position:sticky;top:4.5rem;background:var(--notice);border:1px solid var(--line);padding:.5rem .75rem;margin:.5rem 0;z-index:1}
.notice button{margin-left:.75rem}
main#doc h1{font-size:1.4rem}main#doc h2{font-size:1.2rem;margin-top:2rem}
main#doc [id]{scroll-margin-top:5rem}main#doc :target{outline:3px solid var(--edge);outline-offset:4px}
button{font:inherit;padding:.3rem .8rem;border:1px solid var(--line);border-radius:.3rem;background:var(--bg);color:var(--fg);cursor:pointer}
button:focus-visible,a:focus-visible{outline:3px solid var(--edge);outline-offset:2px}
pre{overflow:auto;background:var(--panel);padding:.5rem}
table{display:block;overflow-x:auto;max-width:100%;border-collapse:collapse}td,th{border:1px solid var(--line);padding:.2rem .5rem;text-align:left;vertical-align:top}
.ref{text-decoration:underline dotted}.ref-error{color:var(--error);text-decoration:underline wavy}
.preview{position:absolute;max-width:min(32rem,calc(100vw - 2rem));max-height:60vh;overflow:auto;background:var(--bg);border:1px solid var(--line);padding:.5rem;box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:3}
.diagram-note{color:var(--muted)}.diagram{margin:.5rem 0;overflow-x:auto}.diagram svg{max-width:100%;height:auto}
"""

# The page's one script. It only shows: a notice when the spec changed or the page stopped, the
# preview of a reference code, and the spec's diagrams. It reads values only as text
# (``textContent``), never as HTML, except a diagram the diagram script drew.
SCRIPT = r"""
(() => {
  "use strict";
  const meta = (name) => { const el = document.querySelector('meta[name="' + name + '"]'); return el ? el.getAttribute("content") : null; };
  const TOKEN = meta("kys-token");
  const HASH = meta("kys-hash");
  const notice = document.getElementById("notice");

  function showNotice(text, reload) {
    if (!notice) return;
    notice.textContent = "";
    const line = document.createElement("span");
    line.textContent = text;
    notice.appendChild(line);
    if (reload) {
      const button = document.createElement("button");
      button.type = "button"; button.textContent = "Reload";
      button.addEventListener("click", () => location.reload());
      notice.appendChild(button);
    }
    notice.hidden = false;
  }

  async function poll() {
    try {
      const response = await fetch("/state", {headers: {"X-KYS-Token": TOKEN}, credentials: "same-origin"});
      const state = await response.json();
      if (state.hash !== HASH) return showNotice("__CHANGED__", true);
    } catch (error) {
      return showNotice("__STOPPED__", false);
    }
    setTimeout(poll, __POLL_MS__);
  }
  if (TOKEN && HASH) setTimeout(poll, __POLL_MS__);

  function preview(link, show) {
    const tip = document.getElementById(link.getAttribute("aria-describedby") || "");
    if (!tip) return;
    if (show) {
      const box = link.getBoundingClientRect();
      tip.hidden = false;
      const left = Math.max(8, Math.min(box.left, document.documentElement.clientWidth - tip.offsetWidth - 8));
      tip.style.left = (left + window.scrollX) + "px";
      tip.style.top = (box.bottom + window.scrollY + 4) + "px";
    } else {
      tip.hidden = true;
    }
  }
  document.addEventListener("mouseover", (e) => { const a = e.target.closest("a.ref"); if (a) preview(a, true); });
  document.addEventListener("mouseout", (e) => { const a = e.target.closest("a.ref"); if (a) preview(a, false); });
  document.addEventListener("focusin", (e) => { const a = e.target.closest("a.ref"); if (a) preview(a, true); });
  document.addEventListener("focusout", (e) => { const a = e.target.closest("a.ref"); if (a) preview(a, false); });

  const diagrams = meta("kys-diagram-script");
  if (diagrams) {
    const sources = [...document.querySelectorAll("pre.mermaid-src")];
    const fail = (source, text) => {
      const note = document.createElement("p");
      note.className = "diagram-note";
      note.textContent = text;
      source.after(note);
    };
    import(diagrams).then(async (module) => {
      const mermaid = module.default || module;
      const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      mermaid.initialize({startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "default"});
      for (const [index, source] of sources.entries()) {
        try {
          const out = await mermaid.render("kys-diagram-" + index, source.textContent);
          const drawn = document.createElement("div");
          drawn.className = "diagram";
          drawn.innerHTML = out.svg;
          source.replaceWith(drawn);
        } catch (error) {
          document.querySelectorAll("#dkys-diagram-" + index).forEach((el) => el.remove());
          fail(source, "__NOT_DRAWN__");
        }
      }
    }).catch(() => sources.forEach((source) => fail(source, "__NOT_LOADED__")));
  }
})();
""".replace("__POLL_MS__", str(POLL_MS)).replace("__CHANGED__", CHANGED).replace("__STOPPED__", STOPPED).replace(
    "__NOT_DRAWN__", NOT_DRAWN
).replace("__NOT_LOADED__", NOT_LOADED)


# ---- the server

LOOPBACK = ("127.0.0.1", "localhost", "::1")
# Every interface, so a forwarded port (a container, a remote machine) reaches the page. The token
# in the address is what admits a request; the address still names 127.0.0.1, the forwarded end.
DEFAULT_HOST = "0.0.0.0"
FIRST_PORT, LAST_PORT = 8100, 8199
IDLE_MINUTES = 60.0


class Refused(Exception):
    """A request the helper will not carry out: a code, what is wrong, and what to do about it."""

    def __init__(self, code: str, message: str, fix: str) -> None:
        super().__init__(message)
        self.payload = {"ok": False, "refusals": [{"code": code, "message": message, "fix": fix}]}


class PageServer(HTTPServer):
    """The page's process state. Nothing here is written anywhere."""

    def __init__(
        self, address: tuple[str, int], spec: Path, *, public_name: str | None, idle_minutes: float
    ) -> None:
        self.stopped = threading.Event()  # set when the idle stop ended the server
        self._closed = threading.Event()
        self._idle: threading.Thread | None = None
        super().__init__(address, Handler)
        self.spec = Path(spec)
        self.token = secrets.token_urlsafe(32)
        self.bound_host = address[0]
        self.public_name = public_name if public_name and not _loopback(address[0]) else None
        self.idle_seconds = float(idle_minutes) * 60
        self.last_use = time.monotonic()

    @property
    def port(self) -> int:
        return int(self.server_address[1])

    @property
    def address(self) -> str:
        """The address a person opens, with the token."""
        host = self.public_name or ("127.0.0.1" if self.bound_host in ("0.0.0.0", "") else self.bound_host)
        if ":" in host:
            host = f"[{host}]"
        return f"http://{host}:{self.port}/?t={self.token}"

    def allowed_hosts(self) -> set[str]:
        hosts = {"127.0.0.1", "localhost", self.bound_host.lower()}
        if self.public_name:
            hosts.add(self.public_name.lower())
        return hosts - {"0.0.0.0", ""}

    def used(self) -> None:
        self.last_use = time.monotonic()

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        if self.idle_seconds > 0:
            self._idle = threading.Thread(target=self._watch_idle, daemon=True)
            self._idle.start()
        super().serve_forever(poll_interval)

    def server_close(self) -> None:
        self._closed.set()
        super().server_close()

    def _watch_idle(self) -> None:
        step = max(0.02, min(5.0, self.idle_seconds / 4))
        while not self.stopped.is_set() and not self._closed.is_set():
            time.sleep(step)
            if time.monotonic() - self.last_use > self.idle_seconds:
                self.stopped.set()
                self.shutdown()
                return


def _loopback(host: str) -> bool:
    return host in LOOPBACK or host.startswith("127.")


def _hostname(header: str | None) -> str | None:
    """The host part of a ``Host`` header, lower-cased; ``None`` when there is none."""
    if not header or not header.strip():
        return None
    host = header.strip().lower()
    if host.startswith("["):
        return host[1 : host.find("]")] if "]" in host else None
    return host.rsplit(":", 1)[0] if ":" in host else host


class Handler(BaseHTTPRequestHandler):
    server: PageServer
    protocol_version = "HTTP/1.0"
    server_version = "kys-spec-page"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - the base class's name
        return None

    def __getattr__(self, name: str) -> Any:
        if name.startswith("do_"):
            return self._not_allowed
        raise AttributeError(name)

    # ---- responses

    def end_headers(self) -> None:
        nonce = self.__dict__.setdefault("nonce", secrets.token_urlsafe(16))
        self.send_header("Content-Security-Policy", csp(nonce, self.__dict__.get("diagrams", False)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _reply(self, status: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _json(self, status: int, payload: Any) -> None:
        self._reply(status, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")

    def _message(self, status: int, text: str) -> None:
        self._reply(status, message_page(text, self.nonce))

    def _not_allowed(self) -> None:
        self.__dict__["nonce"] = secrets.token_urlsafe(16)
        self.send_response(405)
        self.send_header("Allow", "GET, POST")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---- dispatch

    def do_GET(self) -> None:  # noqa: N802 - the base class's name
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        self.__dict__["nonce"] = secrets.token_urlsafe(16)
        try:
            url = urlsplit(self.path)
            if _hostname(self.headers.get("Host")) not in self.server.allowed_hosts():
                return self._message(403, "This page answers only at the address the agent gave you.")
            path = url.path
            page_route = method == "GET" and path == "/"
            given = (parse_qs(url.query).get("t") or [""])[0] if page_route else self.headers.get("X-KYS-Token", "")
            if not given or not hmac.compare_digest(given.encode("utf-8"), self.server.token.encode("utf-8")):
                return self._message(403, OPEN_THE_ADDRESS)
            if path != "/state":
                self.server.used()
            if method == "POST":
                return self._post(path)
            if path == "/":
                page = spec_page(self._spec(), self._label(), self.server.token, self.nonce)
                self.__dict__["diagrams"] = DIAGRAM_SOURCE in page
                return self._reply(200, page)
            if path == "/state":
                return self._json(200, {"ok": True, "hash": spec_hash(self._spec())})
            return self._message(404, "Nothing is served here.")
        except OSError as exc:
            return self._message(404, f"The spec cannot be read: {exc.strerror or exc}")
        except Exception as exc:  # noqa: BLE001 - the page reports, it never crashes the server
            return self._json(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    def _post(self, path: str) -> None:
        """The one ``POST`` is ``/stop``, which ends this process and changes nothing else."""
        if self.headers.get("Origin") != f"http://{self.headers.get('Host', '')}":
            return self._message(403, "A request to stop must come from the helper itself.")
        if path != "/stop":
            return self._message(404, "Nothing is served here.")
        threading.Thread(target=self.server.shutdown, daemon=True).start()
        return self._json(200, {"ok": True, "stopped": True})

    # ---- the spec as it is on disk now: read fresh for every request

    def _spec(self) -> str:
        return self.server.spec.read_text(encoding="utf-8")

    def _label(self) -> str:
        spec = self.server.spec
        return f"{spec.parent.name}/{spec.name}"


# ---- starting the server


def _first_free(host: str) -> int:
    for port in range(FIRST_PORT, LAST_PORT + 1):
        with socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET) as probe:
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return port
    raise Refused(
        "port-unavailable",
        f"no free port from {FIRST_PORT} to {LAST_PORT} on {host}",
        "Pass a free port with --port, or stop another page",
    )


def make_server(
    spec: Path,
    *,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    public_name: str | None = None,
    idle_minutes: float = IDLE_MINUTES,
) -> PageServer:
    """Bind the page for ``spec``. ``port=None`` takes the first free port from 8100; ``0`` lets the
    system choose. Refuses ``no-spec`` and ``port-unavailable``."""
    spec = Path(spec)
    if not spec.is_file():
        raise Refused("no-spec", f"there is no spec at {spec}", "Pass the feature's spec.md with --spec")
    chosen = _first_free(host) if port is None else port
    server_class = _server_class(host)
    try:
        return server_class((host, chosen), spec.resolve(), public_name=public_name, idle_minutes=idle_minutes)
    except OSError as exc:
        raise Refused(
            "port-unavailable",
            f"cannot listen on {host}:{chosen}: {exc.strerror or exc}",
            "Pass a free port with --port",
        ) from exc


def _server_class(host: str) -> type[PageServer]:
    if ":" in host:

        class V6(PageServer):
            address_family = socket.AF_INET6

        return V6
    return PageServer


# ---- the runtime file, and serve, status and stop


PROJECT_MARKS = (".git", ".specify")


def project_root(spec: Path) -> Path:
    """The outermost folder above ``spec`` that is a repository or a Spec Kit project; with neither,
    the spec's own folder."""
    spec = Path(spec).resolve()
    roots = [folder for folder in spec.parents if any((folder / mark).exists() for mark in PROJECT_MARKS)]
    return roots[-1] if roots else spec.parent


def runtime_dir(spec: Path) -> Path:
    """Where the runtime file goes: the OS temporary directory, or, when ``TMPDIR`` puts that inside
    the project, the first usual place outside it. Refuses ``no-runtime-dir`` when there is none,
    because the page never writes inside the project (spec FR-012, SC-005)."""
    root = project_root(spec)
    for candidate in (tempfile.gettempdir(), "/tmp", "/var/tmp", Path.home()):
        folder = Path(candidate).resolve()
        if folder != root and root not in folder.parents and folder.is_dir() and os.access(folder, os.W_OK):
            return folder
    raise Refused(
        "no-runtime-dir",
        f"the temporary directory is inside the project at {root}, and there is no other place to keep the page's address",
        "Set TMPDIR to a directory outside the project",
    )


def runtime_path(spec: Path) -> Path:
    """``<runtime dir>/kys-spec-page-<sha256(spec path)[:12]>.json``: outside the project, so starting
    the page changes nothing in it."""
    digest = hashlib.sha256(str(Path(spec).resolve()).encode("utf-8")).hexdigest()[:12]
    return runtime_dir(spec) / f"kys-spec-page-{digest}.json"


def _read_runtime(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _runtime_request(data: dict[str, Any], path: str, *, post: bool = False) -> dict[str, Any] | None:
    """Call a runtime's token-protected endpoint, proving the file still names this page process."""
    address = data.get("address")
    if not isinstance(address, str):
        return None
    parsed = urlsplit(address)
    token = (parse_qs(parsed.query).get("t") or [""])[0]
    if parsed.scheme != "http" or not parsed.netloc or not token:
        return None
    origin = f"{parsed.scheme}://{parsed.netloc}"
    headers = {"X-KYS-Token": token}
    body = None
    if post:
        headers["Origin"] = origin
        body = b"{}"
    try:
        with urlopen(Request(origin + path, data=body, headers=headers), timeout=1.0) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    return result if isinstance(result, dict) else None


def _anchors(spec: Path) -> dict[str, str]:
    try:
        return anchors_of(Path(spec).read_text(encoding="utf-8"))
    except OSError:
        return {}


def status(spec: Path) -> dict[str, Any]:
    """``serve --status``: verify the runtime file through the page's authenticated state endpoint."""
    path = runtime_path(spec)
    data = _read_runtime(path)
    if data is None or _runtime_request(data, "/state") is None:
        path.unlink(missing_ok=True)
        return {"ok": True, "running": False, "address": None, "pid": None, "text": "No spec page is running."}
    return {
        "ok": True,
        "running": True,
        "address": data.get("address"),
        "pid": int(data.get("pid") or 0),
        "anchors": _anchors(spec),
        "text": f"The spec page is running at {data.get('address')}",
    }


def stop(spec: Path, wait: float = 5.0) -> dict[str, Any]:
    """``serve --stop``: authenticate to the page and ask it to stop."""
    path = runtime_path(spec)
    data = _read_runtime(path)
    if data is None or _runtime_request(data, "/stop", post=True) is None:
        path.unlink(missing_ok=True)
        return {"ok": True, "stopped": False, "text": "No spec page was running."}
    deadline = time.monotonic() + wait
    while path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    path.unlink(missing_ok=True)
    return {"ok": True, "stopped": True, "text": "Stopped the spec page."}


def serve(
    spec: Path,
    *,
    emit: Any,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    public_name: str | None = None,
    idle_minutes: float = IDLE_MINUTES,
) -> dict[str, Any]:
    """Start the page and serve until it is stopped or idle. ``emit`` prints the one JSON line with
    the address as soon as the page listens. Refuses ``page-running``, ``no-spec``, ``port-unavailable``, ``no-runtime-dir``."""
    running = status(spec)
    if running["running"]:
        raise Refused(
            "page-running",
            f"the spec page is already running at {running['address']}",
            f"Ask the person to reload {running['address']}, or stop it with serve --stop",
        )
    server = make_server(spec, host=host, port=port, public_name=public_name, idle_minutes=idle_minutes)
    path = runtime_path(spec)
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(json.dumps({"address": server.address, "pid": os.getpid()}))
    os.chmod(path, 0o600)

    def end(signum: int, frame: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    previous = {sig: signal.signal(sig, end) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        emit({"ok": True, "address": server.address, "pid": os.getpid(), "anchors": _anchors(spec)})
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        held = _read_runtime(path)
        if held is not None and held.get("pid") == os.getpid():
            path.unlink(missing_ok=True)
    reason = "idle" if server.stopped.is_set() else "stopped"
    return {"ok": True, "stopped": reason, "text": f"The spec page stopped{' after being idle' if reason == 'idle' else ''}."}


# ---- command line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show a Spec Kit spec.md as a read-only page in the browser.")
    actions = parser.add_subparsers(dest="action", required=True)
    a = actions.add_parser("serve", help="start the page, or with --status / --stop report or end it")
    a.add_argument("--spec", required=True, type=Path, help="the spec.md to show")
    a.add_argument("--host", default=DEFAULT_HOST, help=f"bind address (default: {DEFAULT_HOST}, every interface)")
    a.add_argument("--port", type=int, help=f"use exactly this port (default: first free from {FIRST_PORT})")
    a.add_argument("--public-name", help="the host name the person opens, when --host is not loopback")
    a.add_argument("--idle-minutes", type=float, default=IDLE_MINUTES, help="stop after this long without use")
    a.add_argument("--status", action="store_true", help="report whether a page is running for this spec")
    a.add_argument("--stop", action="store_true", help="stop the page running for this spec")
    a.add_argument("--json", action="store_true", help="accepted for symmetry; output is always JSON")
    args = parser.parse_args(argv)

    def emit(payload: dict[str, Any]) -> None:
        print(json.dumps(payload, ensure_ascii=False), flush=True)

    try:
        if args.status:
            emit(status(args.spec))
        elif args.stop:
            emit(stop(args.spec))
        else:
            emit(
                serve(
                    args.spec, emit=emit, host=args.host, port=args.port,
                    public_name=args.public_name, idle_minutes=args.idle_minutes,
                )
            )  # fmt: skip
    except Refused as exc:
        emit(exc.payload)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
