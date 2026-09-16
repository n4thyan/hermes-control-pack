# Changelog

All notable HCP changes are documented here.

## 1.0.0 — 2026-09-16

First complete public release.

### Runtime
- Added a concise Hermes project execution kernel with explicit task routing.
- Added 12 progressive-disclosure skills covering orchestration, exploration, debugging, implementation, verification, review, AFK autonomy, handoff, delegation, git safety, UI verification, and evidence-grounded research.
- Added five Hermes-native skill bundles: `hcp-coding`, `hcp-debug`, `hcp-afk`, `hcp-ui`, and `hcp-research`.

### Compiler and research tooling
- Added full ZIP/directory corpus scanning with per-file SHA-256 metadata.
- Added deterministic directory fingerprints.
- Added source-family, behavior-family, and cross-source aggregate reports.
- Added reproducible build manifests hashing every emitted runtime artifact.
- Raw source text is not copied into generated public reports.

### Installer
- Added idempotent installs.
- Added protection for differing existing project context/skills/bundles.
- `--force` creates timestamped backups before replacement.
- Added selective `--no-context`, `--no-skills`, and `--no-bundles` modes.
- Added `hcp doctor` validation.

### Packaging and quality
- Runtime skills/bundles are packaged inside the wheel, so normal and editable installs behave consistently.
- Added Linux/Windows CI on Python 3.11–3.13 and a wheel smoke test.
- Added unit tests for scanning, fingerprints, analysis, compilation, packaging parity, installation safety, and idempotence.
- Added architecture, usage, research methodology, provenance, examples, benchmark specification, issue templates, and PR template.

### Attribution
- Credited `asgeirtj/system_prompts_leaks` as the primary bootstrap research corpus.
- Credited `NousResearch/hermes-agent` as the target runtime.
