# Architecture

Hermes Control Pack (HCP) is a **downstream agent-harness layer** for Hermes Agent. It does not replace Hermes, alter model weights, or inject the raw research corpus into every turn.

## Runtime layers

```text
research corpus ZIP / checkout
        │
        ▼
  corpus scanner
  - every file hashed
  - text/binary classification
  - source-family counts
  - aggregate behavior signals
        │
        ├──────────────► corpus-index.json
        ├──────────────► CORPUS_COVERAGE.md
        └──────────────► RESEARCH_SIGNALS.md

HCP-authored runtime assets
        │
        ├── .hermes.md execution kernel
        ├── skills/*/SKILL.md
        └── bundles/*.yaml
                 │
                 ▼
      compiled HCP build directory
                 │
                 ▼
          safe installer
        ┌────────┴────────┐
        ▼                 ▼
project/.hermes.md   ~/.hermes/skills + skill-bundles
```

## Why this design

Hermes supports project context files and progressive-disclosure skills. The always-loaded kernel therefore contains only cross-task invariants. Specialized procedures are skills loaded when needed. Bundles provide ergonomic task profiles without mutating the system prompt.

This avoids three failure modes of a giant concatenated prompt:

1. contradictory product-specific instructions;
2. context budget wasted on irrelevant tool schemas and UI rules;
3. stale third-party implementation details overpowering the actual repository.

## Source processing

The scanner never writes raw source text into public reports. Each corpus entry records:

- path;
- byte count;
- SHA-256;
- text/binary status;
- approximate word count;
- top-level source family;
- deterministic behavior-signal counts.

For directory input, HCP computes a deterministic fingerprint over ordered `(path, file-sha256)` pairs. ZIP input is fingerprinted by the ZIP bytes, making the exact supplied archive reproducible.

## Execution kernel

The kernel routes work by requested outcome:

`EXPLAIN / EXPLORE / PLAN / DIAGNOSE / IMPLEMENT / REVIEW / VERIFY`

Substantive implementation normally follows:

`EXPLORE → PLAN/DIAGNOSE → IMPLEMENT → VERIFY → REVIEW → HANDOFF`

The phases are not ceremony. Hermes should use the smallest applicable subset while preserving evidence-producing steps.

## Skills

HCP skills encode reusable procedures rather than project facts. Current skills cover:

- orchestration;
- exploration;
- root-cause debugging;
- implementation discipline;
- verification;
- independent review;
- AFK autonomy;
- context handoff;
- parallel delegation;
- git/change safety;
- UI visual verification;
- evidence-grounded research.

## Bundles

Bundles are Hermes-native YAML aliases that preload related skills. HCP ships:

- `/hcp-coding`
- `/hcp-debug`
- `/hcp-afk`
- `/hcp-ui`
- `/hcp-research`

## Safety model

HCP is intentionally conservative around destructive and externally consequential actions. Autonomous coding does not imply authorization for credential rotation, purchases, publishing, destructive migrations, or unrelated cleanup.

## Packaging

Runtime skills and bundle files are included inside the Python package so `pip install .`, wheels, and editable installs behave consistently. Top-level `skills/` and `bundles/` mirror those assets for review and contribution. Tests enforce parity.
