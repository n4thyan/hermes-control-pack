# Hermes Control Pack

**A research-driven orchestration, verification, and autonomy layer for [NousResearch/Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Hermes Control Pack (HCP) converts a large local prompt/agent research corpus into a **Hermes-native runtime pack**: a concise project execution kernel, progressive-disclosure skills, skill bundles, reproducible corpus metadata, and safe installation tooling.

The goal is practical: make Hermes more disciplined during real repository work — inspect before editing, diagnose from evidence, finish integrations end-to-end, verify before claiming success, delegate independent work cleanly, protect user changes, and leave executable handoffs after long sessions.

> HCP improves the **agent harness and operating procedure**. It does not modify model weights and does not claim to make one base model intrinsically equivalent to GPT, Claude, Gemini, Grok, or any other model.

## Research corpus and credit

HCP was bootstrapped against the public research corpus:

- **Original corpus:** [`asgeirtj/system_prompts_leaks`](https://github.com/asgeirtj/system_prompts_leaks)
- **Hermes target:** [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)

The upstream corpus does the substantial work of collecting and organizing system-prompt and agent material across many products. HCP's original work is the **Hermes-specific compiler, indexing and provenance layer, execution kernel, skills/bundles, installer, tests, and evaluation spec**.

At project bootstrap time the upstream corpus declared CC0-1.0. HCP still does **not vendor the raw corpus by default**. You provide a local ZIP or checkout, and HCP emits metadata/aggregate signals rather than republishing source passages. See [CREDITS.md](CREDITS.md), [THIRD_PARTY.md](THIRD_PARTY.md), and [docs/RESEARCH_METHOD.md](docs/RESEARCH_METHOD.md).

## What HCP installs

```text
project/.hermes.md
~/.hermes/skills/
  control-orchestrator/
  explore-first/
  root-cause-debugging/
  implementation-discipline/
  verification-gate/
  independent-review/
  afk-autonomy/
  context-handoff/
  parallel-delegation/
  git-change-safety/
  ui-visual-verification/
  research-evidence/

~/.hermes/skill-bundles/
  hcp-coding.yaml
  hcp-debug.yaml
  hcp-afk.yaml
  hcp-ui.yaml
  hcp-research.yaml
```

The always-loaded `.hermes.md` remains concise. Specialist procedures are loaded only when relevant, matching Hermes' progressive-disclosure skill architecture.

## Operating model

HCP first distinguishes what the user actually asked for:

`EXPLAIN / EXPLORE / PLAN / DIAGNOSE / IMPLEMENT / REVIEW / VERIFY`

Substantive coding work normally follows the smallest useful subset of:

```text
EXPLORE → PLAN / DIAGNOSE → IMPLEMENT → VERIFY → REVIEW → HANDOFF
```

The important invariant is not the arrows — it is that **editing is not proof**, and **a completion claim needs evidence**.

## Quick start

Requirements:

- Python 3.11+
- Hermes Agent installed for runtime use
- a local ZIP/checkout of the research corpus you want to analyze

### Easiest option: let Hermes set itself up

If Hermes Agent is already running, paste this directly into Hermes:

```text
Set up Hermes Control Pack for this Hermes installation using:
https://github.com/n4thyan/hermes-control-pack

Read the repository README and relevant installation/compatibility docs first, then install and configure HCP end to end yourself. Inspect my current Hermes installation before changing anything. Preserve and back up any existing SOUL.md, .hermes.md, skills, bundles, plugins, config, and user customizations before replacing or merging them. Prefer HCP's supported plugin/integration path over patching Hermes core. Install the recommended runtime assets and default balanced setup, run HCP's doctor/validation checks, verify the HCP skills/bundles/integration actually load, and diagnose any failures instead of stopping at the first error. Do not delete unrelated files or user data. At the end, briefly report what you installed, what you backed up, what verification passed, and any optional features that remain unconfigured.
```

A longer version with extra safeguards is in [docs/SELF_SETUP_PROMPT.md](docs/SELF_SETUP_PROMPT.md).

### Manual install

```bash
git clone https://github.com/n4thyan/hermes-control-pack.git
cd hermes-control-pack
python -m pip install .
```

### Build against the corpus

```bash
hcp build /path/to/system_prompts_leaks-main.zip --out build/hcp
```

HCP scans **every file**, fingerprints the source, writes a per-file metadata index, computes cross-source behavior coverage, and packages the Hermes runtime assets.

### Install into your project

```bash
hcp install --build build/hcp --project /path/to/your-project
```

Existing differing HCP-managed files are protected. To replace them, HCP requires `--force` and creates timestamped backups first.

```bash
hcp install --build build/hcp --project /path/to/your-project --force
```

### Validate

```bash
hcp doctor --build build/hcp --project /path/to/your-project
```

See [docs/USAGE.md](docs/USAGE.md) for selective installs, updates, and Windows examples.

## Hermes bundles

After installation you can invoke task profiles directly inside Hermes:

```text
/hcp-coding implement this feature end to end
/hcp-debug find and fix the root cause of this regression
/hcp-ui match this screen to the reference and verify the interactions
/hcp-afk finish the remaining in-scope work while I'm away
/hcp-research investigate the current API behavior using primary sources
```

Each bundle is a small Hermes-native YAML alias that loads the relevant HCP skills together.

## Corpus analysis

HCP can be used without installing anything into Hermes:

```bash
hcp scan /path/to/corpus.zip --out corpus-index.json
hcp analyze /path/to/corpus.zip --out RESEARCH_SIGNALS.md
```

The index records each entry's path, bytes, SHA-256, text/binary status, approximate word count, source family, and aggregate behavior signals. The signal report measures how broadly categories such as debugging, verification, delegation, context management, visual checking, research, git safety, and autonomy appear across the supplied source families.

Those are **coverage signals, not vendor scores or truth rankings**.

## Why not concatenate the whole leak into one prompt?

A giant prompt is the wrong runtime representation:

- product-specific instructions conflict with each other;
- proprietary tool schemas are irrelevant to Hermes;
- millions of tokens crowd out the actual repository and task;
- stale UI/product rules can become actively harmful;
- Hermes already has a better mechanism: concise context + on-demand skills.

HCP therefore uses the complete supplied corpus as **research input**, then compiles transferable mechanisms into Hermes-native layers.

## Reproducibility

Every build includes:

- `corpus-index.json` — per-file hashes and metadata;
- `CORPUS_COVERAGE.md` — source-family + signal counts;
- `RESEARCH_SIGNALS.md` — cross-source behavior coverage;
- `hcp-manifest.json` — HCP version, corpus fingerprint, and SHA-256 of every emitted runtime artifact;
- `.hermes.md`, `skills/`, and `bundles/` — the actual runtime pack.

ZIP inputs are fingerprinted from the archive bytes. Directory inputs use a deterministic digest of ordered `(path, file SHA-256)` pairs.

## Evaluation

The repository includes a model-agnostic [benchmark specification](benchmarks/README.md). It intentionally ships **no fabricated performance numbers**. To compare stock Hermes vs HCP fairly, keep the model/provider/tool configuration fixed and evaluate observable behaviors such as:

- edits before inspection;
- unnecessary clarification requests;
- reproduction/root-cause quality;
- verification-backed completion claims;
- unrelated change rate;
- rendered-state UI checks;
- final diff review;
- long-session handoff quality.

## Repository layout

```text
src/hermes_control_pack/   compiler, analyzer, installer, CLI, packaged runtime assets
skills/                    reviewable HCP skill sources
bundles/                   reviewable Hermes skill bundles
docs/                      architecture, usage, research method, provenance
benchmarks/                 evaluation specification
examples/                   project-context examples
sources/                    source policy + bootstrap fingerprint
reports/                    aggregate bootstrap reports (no raw prompt text)
tests/                      corpus/compiler/installer/analyzer tests
```

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src/hermes_control_pack
hcp --version
```

CI runs on Windows and Linux across Python 3.11, 3.12, and 3.13 and separately smoke-tests a built wheel.

When changing a top-level skill or bundle, mirror it into `src/hermes_control_pack/runtime/`; the test suite rejects drift between the reviewable and packaged copies.

## Design principles

1. Use the whole supplied corpus as research input, not one magic prompt.
2. Transfer mechanisms, not vendor identity or proprietary tool instructions.
3. Keep always-loaded context compact.
4. Load specialist procedures on demand.
5. Diagnose bugs from evidence.
6. Require appropriate evidence before completion claims.
7. Preserve user work and keep changes reviewable.
8. Use parallelism only where work is actually independent.
9. Treat rendered UI as evidence for visual work.
10. Keep autonomous work bounded, recoverable, and aligned to the user's scope.

## Non-affiliation

Hermes Control Pack is independent and is not endorsed by or affiliated with Nous Research, OpenAI, Anthropic, Google, xAI, Cursor, Microsoft, Meta, Perplexity, or the maintainers of the upstream research corpus.

## License

HCP's original code and authored runtime material are MIT licensed. Third-party source material remains subject to its own rights and terms. See [THIRD_PARTY.md](THIRD_PARTY.md).
