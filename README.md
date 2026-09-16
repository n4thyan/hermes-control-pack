# Hermes Control Pack

**A research-driven agent-harness augmentation layer for [NousResearch/Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Hermes Control Pack (HCP) studies captured system instructions and agent internals from major AI products, extracts transferable orchestration mechanisms, and reimplements them for Hermes as **system guidance, SOUL overlays, skills, persistent task state, verification gates, decision telemetry, and compression-safe continuity**.

The goal is practical: make whichever model Hermes is using **more capable and coherent during real tasks** — understand before editing, preserve the user's objective across long sessions, recover from failed approaches, use tools deliberately, verify claims before finishing, and resume after compression or a new session without reconstructing the project from scratch.

> HCP improves the **agent harness**, not the model weights. It does not claim to turn one base model into GPT, Claude, Gemini, Grok, or any other model. Its purpose is to transfer useful harness mechanisms into an open, model-agnostic runtime where they can be inspected and evaluated.

## Research corpus and credit

HCP was bootstrapped against:

- **Primary research corpus:** [`asgeirtj/system_prompts_leaks`](https://github.com/asgeirtj/system_prompts_leaks)
- **Target runtime:** [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)

The upstream corpus does the substantial work of collecting and organizing captured system-prompt and agent material. HCP's original work is the **cross-agent mechanism model, Hermes-specific runtime integration, persistent continuity model, compiler/indexer, SOUL profiles, skills/bundles, verification/telemetry layer, installer, tests, and evaluation tooling**.

At project bootstrap time the upstream corpus declared CC0-1.0. HCP does **not vendor the raw corpus by default**. Runtime installation does not require the corpus. You only need a local ZIP/checkout when you want to reproduce the research analysis or rebuild from a particular corpus snapshot. See [CREDITS.md](CREDITS.md), [THIRD_PARTY.md](THIRD_PARTY.md), and [docs/RESEARCH_METHOD.md](docs/RESEARCH_METHOD.md).

## HCP 2.0 architecture

```text
                         base model
          GPT / Claude / Gemini / open-weight / ...
                              │
                              ▼
                     Hermes Agent core
                              │
                   documented plugin hooks
                              │
             ┌────────────────┴────────────────┐
             │      HCP runtime controller      │
             │                                  │
             │ system kernel + task routing     │
             │ persistent project/task state    │
             │ decision + evidence ledgers      │
             │ completion verification gate     │
             │ observable decision telemetry    │
             │ compression continuity grounding │
             └────────────────┬─────────────────┘
                              │
               SOUL + skills + project context
```

HCP deliberately prefers Hermes' documented plugin and context-engine APIs over patching Hermes core. This keeps the integration inspectable and upgradeable.

## Quick start

Requirements:

- Python 3.11+
- Hermes Agent installed

### Easiest option: let Hermes set itself up

If Hermes is already running, paste this into Hermes:

```text
Set up Hermes Control Pack for this Hermes installation using:
https://github.com/n4thyan/hermes-control-pack

Read the repository README and relevant installation/compatibility docs first, then install and configure HCP end to end yourself. Inspect my current Hermes installation before changing anything. Preserve and back up any existing SOUL.md, .hermes.md, skills, bundles, plugins, config, and user customizations before replacing or merging them. Prefer HCP's supported plugin/integration path over patching Hermes core. Use the recommended `hcp setup` flow where available, run HCP's doctor/validation checks afterward, verify the HCP plugin/skills/bundles and continuity integration actually load, and diagnose any failures instead of stopping at the first error. Do not delete unrelated files or user data. At the end, briefly report what you installed, what you backed up, what verification passed, and any optional features that remain unconfigured.
```

A longer safeguarded version is in [docs/SELF_SETUP_PROMPT.md](docs/SELF_SETUP_PROMPT.md).

### One-command setup

```bash
git clone https://github.com/n4thyan/hermes-control-pack.git
cd hermes-control-pack
python -m pip install .
hcp setup --project /path/to/your-project
hcp doctor --project /path/to/your-project
```

`hcp setup` uses the runtime assets packaged with HCP. By default it:

- installs the `hcp-runtime` Hermes plugin and asks Hermes to enable it;
- installs the HCP skills and skill bundles;
- merges the **balanced** HCP identity block into `SOUL.md` without deleting existing user-authored personality text;
- initializes project-local structured continuity under `.hcp/state/`;
- installs and selects `hcp-continuity`, a thin subclass of Hermes' built-in `ContextCompressor` that supplies structured HCP state as compaction grounding;
- leaves an existing project `.hermes.md` alone unless `--project-context` is explicitly requested.

Keep Hermes' normal compressor instead with:

```bash
hcp setup --project /path/to/project --no-context-engine
```

The context-engine choice is reversible:

```bash
hermes config set context.engine compressor
```

## Persistent continuity

HCP keeps the model's active working set small without treating compression as memory deletion. Four durable project-local objects survive context compaction, process restarts, and new sessions:

```text
PROJECT_STATE.json    architecture, constraints, facts, do-not-regress rules
TASK_STATE.json       objective, phase, acceptance criteria, changed paths, next steps
DECISION_LOG.jsonl    material decisions + concise externally defensible rationale
EVIDENCE_LEDGER.jsonl verification observations and results
```

An additional `TRACE.jsonl` records **observable harness events** such as tool calls, verification gates, API outcomes, and state transitions. It is deliberately not a chain-of-thought log.

HCP injects a bounded state summary into each turn. The optional continuity engine also provides the same structured state to Hermes' own compressor when compaction occurs. Full conversation history remains Hermes' searchable archive; HCP state is the compact task-level continuity layer. See [docs/PERSISTENCE.md](docs/PERSISTENCE.md).

## Runtime completion gates

Editing code is not proof that it works. HCP observes tool activity and uses Hermes' bounded `pre_verify` hook to continue a coding turn when important evidence is missing.

Examples include:

- verification after the most recent observed edit;
- a durable task objective so the job can survive a session boundary;
- rendered-state evidence for UI-affecting changes;
- final diff/status review for larger multi-file changes.

The gate is bounded by Hermes, so HCP cannot trap the model in an infinite verification loop. See [docs/RUNTIME_PLUGIN.md](docs/RUNTIME_PLUGIN.md).

## SOUL profiles

HCP ships four identity overlays:

- `balanced` — recommended default; evidence-led, direct, coherent, persistent;
- `coder` — software-engineering and debugging emphasis;
- `autonomous` — longer bounded/AFK execution with recovery discipline;
- `research` — source/provenance and fact-vs-hypothesis discipline.

Switch the HCP-managed block without deleting your own SOUL content:

```bash
hcp install --project . --soul coder --no-context --no-skills --no-bundles --no-plugin
```

## Hermes skills and bundles

HCP includes 12 progressive-disclosure skills covering orchestration, exploration, root-cause debugging, implementation discipline, verification, review, AFK autonomy, context handoff, delegation, Git safety, UI verification, and evidence-grounded research.

Common bundles:

```text
/hcp-coding implement this feature end to end
/hcp-debug find and fix the root cause of this regression
/hcp-ui match this screen to the reference and verify interactions
/hcp-afk finish the remaining in-scope work while I'm away
/hcp-research investigate this using current primary sources
```

## Research/compiler mode

Runtime users do **not** need the prompt corpus. Researchers can reproduce HCP's source analysis against any ZIP or directory:

```bash
hcp scan /path/to/system_prompts_leaks-main.zip --out corpus-index.json
hcp analyze /path/to/system_prompts_leaks-main.zip --out RESEARCH_SIGNALS.md
hcp mechanisms /path/to/system_prompts_leaks-main.zip --out MECHANISM_MATRIX.md
hcp build /path/to/system_prompts_leaks-main.zip --out build/hcp
```

HCP scans every file, hashes the source, classifies source families/artifact types, measures behavior signals, and builds a **mechanism matrix** mapping observed cross-agent patterns to HCP implementation targets. These are coverage/provenance signals, not vendor rankings.

The supplied bootstrap corpus snapshot contained 493 files, 461 decoded text files, and roughly 2.165 million words. Its source fingerprint is recorded in [`sources/bootstrap-source-lock.json`](sources/bootstrap-source-lock.json).

## Why not concatenate every leaked prompt into Hermes?

Because that would usually make the agent worse:

- vendor/product instructions conflict;
- proprietary tool schemas do not match Hermes;
- millions of tokens would crowd out the actual task and repository;
- stale product/UI instructions would become active noise;
- prompt caching would suffer;
- the same mechanism is often expressed repeatedly across products.

HCP instead treats the corpus as an **agent-architecture dataset**. It extracts transferable mechanisms and assigns each one to the appropriate implementation layer:

```text
PROMPT / SYSTEM KERNEL   persistent general behavior
SOUL                     identity and communication posture
SKILL                    task-specific procedure
RUNTIME                  mechanically enforced or observed behavior
STATE                    cross-session continuity
PROVIDER ADAPTER         model/provider-specific accommodation
```

## Evaluation

The project is intended to make harness improvements measurable. Keep model, provider, tools, repository, and task fixed, then compare stock Hermes vs Hermes + HCP on observable outcomes such as:

- premature edits;
- unnecessary clarification requests;
- root-cause quality;
- recovery after failed approaches;
- completion claims without evidence;
- regressions/unrelated changes;
- rendered-state UI validation;
- token/context pressure;
- session-resume quality;
- repeated work after compaction;
- final diff quality.

See [benchmarks/README.md](benchmarks/README.md). The repository intentionally ships no fabricated benchmark wins.

## Repository layout

```text
src/hermes_control_pack/   CLI, compiler, analysis, installer, state model
plugins/hcp-runtime/       Hermes runtime plugin
plugins/context_engine/    optional compression-continuity engine
souls/                     managed SOUL overlays
skills/                    task procedures
bundles/                   Hermes skill bundles
docs/                      architecture, runtime, persistence, usage, provenance
benchmarks/                model-agnostic evaluation spec
sources/                    source policy + bootstrap fingerprint
reports/                    aggregate bootstrap reports, no raw prompt corpus
```

## Development and verification

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src/hermes_control_pack plugins
python -m pip wheel . -w dist
hcp --version
hcp setup --help
```

CI runs on Windows and Linux across Python 3.11–3.13 and separately installs a built wheel and smoke-tests runtime setup.

## Design principles

1. Optimize for real task capability and coherence, not sophisticated-sounding prose.
2. Use the whole supplied corpus as research input, not one magic prompt.
3. Transfer mechanisms, not vendor identity or proprietary tool instructions.
4. Preserve the user's objective across context and session boundaries.
5. Separate facts, hypotheses, decisions, and verification evidence.
6. Diagnose from evidence before patching.
7. Require appropriate evidence before completion claims.
8. Keep always-loaded context bounded; retrieve deeper history when needed.
9. Preserve user customizations and keep changes reversible.
10. Prefer documented Hermes extension surfaces over fragile core patches.

## Non-affiliation

Hermes Control Pack is independent and is not endorsed by or affiliated with Nous Research, OpenAI, Anthropic, Google, xAI, Cursor, Microsoft, Meta, Perplexity, or the maintainers of the upstream research corpus.

## License

HCP's original code and authored runtime material are MIT licensed. Third-party source material remains subject to its own rights and terms. See [THIRD_PARTY.md](THIRD_PARTY.md).
