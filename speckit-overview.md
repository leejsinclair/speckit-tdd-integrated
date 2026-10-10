# Project Context: GitHub Spec Kit — Presets and Extensions
 
## Overview
 
GitHub Spec Kit is an open-source toolkit for specification-driven software development with AI coding agents. It provides a structured workflow that transforms business intent into requirements, technical plans, implementation tasks and working software.
 
The core lifecycle is:
 
**Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement**
 
Spec Kit coordinates the process through agent commands, templates and persistent project artefacts. The coding agent interprets requirements and generates artefacts and code; Spec Kit provides the workflow and structure.
 
Repository: https://github.com/github/spec-kit
 
## Customisation Architecture
 
Spec Kit supports several complementary customisation mechanisms:
 
* **Presets:** Customise existing commands and templates to establish consistent document structures, development practices and quality standards.
* **Extensions:** Introduce new commands, templates, scripts, hooks and capabilities that extend the standard workflow.
* **Workflows:** Coordinate sequences of development activities into repeatable processes.
* **Bundles:** Package related customisations for distribution and reuse.
 
Use presets to change how existing stages operate, extensions to introduce new capabilities, workflows to coordinate activities, and bundles to distribute a complete configuration.
 
Presets use a `preset.yml` manifest, while extensions use an `extension.yml` manifest. Exact schemas, supported artefact types and installation commands must be verified against the current Spec Kit implementation.
 
## Development and Testing
 
Customisations should be tested at four levels:
 
1. **Structural validation:** Validate manifests, file paths, required files and identifiers.
2. **Installation and registration:** Confirm components install correctly and commands and templates become available.
3. **Behavioural testing:** Execute commands against representative inputs and assert that generated artefacts satisfy explicit acceptance criteria.
4. **Regression testing:** Verify compatibility with other components, existing workflows and component removal.
 
Successful installation does not establish that an AI-driven command behaves correctly. Tests should evaluate output quality, requirements traceability, ambiguity handling and preservation of developer intent.
 
## Engineering Principles
 
* Keep developers actively involved in requirements, design, implementation and review.
* Separate business intent, functional requirements and technical design where this improves readability and accountability.
* Prefer deterministic scripts for objective checks and AI agents for interpretation, reasoning and collaborative problem-solving.
* Make quality expectations explicit and testable.
* Minimise unnecessary workflow friction while preserving meaningful review and approval gates.
* Treat generated artefacts as persistent, reviewable engineering assets rather than disposable prompts.
* Validate customisations independently before combining them into a team-wide development process.
 
## Project Direction
 
The objective is to build a maintainable, testable and developer-friendly Spec Kit customisation framework that supports an AI-enabled software development lifecycle. The framework should make business intent explicit, improve specification and design quality, provide traceability across development stages, and introduce appropriate validation and feedback mechanisms.
 
Development should begin by examining the current Spec Kit source, official documentation, bundled presets and extensions, and existing test infrastructure. Implementation decisions should be based on the current repository rather than assumptions drawn from older tutorials or examples.
 
## Primary References
 
* Repository: https://github.com/github/spec-kit/tree/main
* Customisation guide: https://github.com/github/spec-kit/blob/main/docs/guides/customization.md
* Preset publishing guide: https://github.com/github/spec-kit/blob/main/presets/PUBLISHING.md
* Extension reference: https://github.com/github/spec-kit/blob/main/docs/reference/extensions.md
