# Changelog

All notable HCP changes are documented here.

## 2.0.0 — 2026-09-16

Harness reconstruction and persistent continuity release.

### Deep Hermes integration
- Added `hcp-runtime`, a Hermes plugin using documented system-prompt, tool, lifecycle, telemetry, and bounded `pre_verify` hooks.
- Added a cache-safe HCP runtime system kernel plus dynamic per-turn continuity injection.
- Added four model-callable continuity tools: `hcp_state_read`, `hcp_state_update`, `hcp_decision_record`, and `hcp_evidence_record`.
- Added observable harness telemetry without requesting or storing model chain-of-thought.
- Added bounded evidence-based completion gating for code, UI, and multi-file work.

### Persistent continuity
- Added project-local `PROJECT_STATE`, `TASK_STATE`, `DECISION_LOG`, and `EVIDENCE_LEDGER` stores plus operational `TRACE` telemetry.
- Added durable session-to-project mapping so resumed processes reconnect to the correct project state.
- Added private Git exclusion for `.hcp/` without modifying tracked `.gitignore` files.
- Added `hcp-continuity`, a `ContextCompressor` subclass that grounds Hermes' existing compression in structured HCP state.

### Identity and setup
- Added balanced, coder, autonomous, and research SOUL overlays.
- SOUL installation now uses an HCP-managed block, preserving and backing up existing user-authored personality text.
- Added `hcp setup` as the recommended one-command installation path.
- Runtime installation no longer requires a local prompt corpus; packaged assets are sufficient.
- Added a copy/paste README prompt that lets a running Hermes install HCP for itself.

### Research compiler
- Added an explicit cross-agent mechanism database and mechanism matrix with source-family provenance.
- Expanded corpus classification beyond keyword totals into transferable harness mechanisms and implementation targets.

### Quality
- Expanded tests for packaged installs, SOUL merges, Git hygiene, resumed session routing, stale evidence after edits, persistent changed paths, continuity compression, and runtime plugin registration.
- Generated Python bytecode/cache files are ignored by build/install parity checks and runtime copying.

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

### Installer and quality
- Added idempotent installs, backups before forced replacement, `hcp doctor`, Linux/Windows CI, wheel packaging, and unit tests.
- Added architecture, usage, research methodology, provenance, examples, benchmark specification, issue templates, and PR template.

### Attribution
- Credited `asgeirtj/system_prompts_leaks` as the primary bootstrap research corpus.
- Credited `NousResearch/hermes-agent` as the target runtime.
