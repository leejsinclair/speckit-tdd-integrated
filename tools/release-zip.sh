#!/usr/bin/env bash
# Build the release zip for a tag: only the files marked for shipping in .gitattributes.
# Usage: tools/release-zip.sh <tag> [output-dir]      e.g. tools/release-zip.sh v0.1.0
# The result matches GitHub's own tag archive: speckit-tdd-integrated-<version>/ at the top.
set -euo pipefail

tag="${1:?usage: release-zip.sh <tag> [output-dir]}"
out="${2:-dist}"
name="speckit-tdd-integrated"

cd "$(git rev-parse --show-toplevel)"

# A tag that exists only on GitHub is fetched; a local one is used as it is.
git rev-parse -q --verify "refs/tags/${tag}^{commit}" >/dev/null ||
  git fetch --quiet origin "refs/tags/${tag}:refs/tags/${tag}"

# The tag must name the version both packages declare.
version="${tag#v}"
for manifest in extension.yml preset.yml; do
  declared="$(git show "${tag}:${manifest}" | sed -n 's/^ *version: *"\{0,1\}\([0-9][^"]*\)"\{0,1\} *$/\1/p' | head -1)"
  if [ "$declared" != "$version" ]; then
    echo "error: ${manifest} at ${tag} declares version ${declared:-none}, not ${version}" >&2
    exit 1
  fi
done

mkdir -p "$out"
zip="${out}/${name}-${version}.zip"
git archive --format=zip --prefix="${name}-${version}/" -o "$zip" "$tag"
echo "$zip"
unzip -l "$zip" | tail -1
