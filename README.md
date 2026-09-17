# Hermes Control Pack

**A research-driven agent-harness augmentation layer for [NousResearch/Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Hermes Control Pack (HCP) studies captured system instructions and agent internals from major AI products, extracts transferable orchestration mechanisms, and reimplements them for Hermes as **system guidance, SOUL overlays, skills, persistent task state, verification gates, decision telemetry, and compression-safe continuity**.

The practical goal is simple: make whichever model Hermes is using **more coherent and reliable during real work** — understand before editing, preserve the user's objective across long sessions, recover from failed approaches, use tools deliberately, verify claims before finishing, and resume after compression or a new session without reconstructing the project from scratch.

> HCP improves the **agent harness**, not the model weights. It does not turn Hermes into GPT, Claude, Gemini, Grok, Fable, or any other model. The underlying model remains whatever provider/model Hermes is configured to use.

## What HCP actually does

A useful mental model is:

```text
base model
   │
   ▼
Hermes Agent
   │
   ▼
HCP orchestration / continuity / verification layer
   │
   ▼
SOUL + skills + project state + evidence + tools
```

HCP is not a second model and it is not a collection of prompts that the user must manually invoke. It is intended to become **ambient behavior around normal Hermes usage**.

The project takes useful patterns observed across larger agent systems — task decomposition, durable state, verification discipline, recovery, handoff, evidence tracking, bounded autonomy, tool-use discipline, and context continuity — and adapts those ideas to Hermes using documented extension points.

That means HCP can improve how the same underlying model behaves without changing the model's weights. In practice, HCP aims to reduce failure modes such as:

- forgetting the real objective after a long session;
- restarting a project from scratch after context compression;
- editing code before understanding the repository;
- repeatedly patching symptoms instead of finding the root cause;
- reversing an earlier architectural decision accidentally;
- claiming something works without actually verifying it;
- repeating a failed approach after a restart;
- losing blockers, next steps, or known-good state between sessions;
- performing unrelated refactors while fixing a narrow issue.

HCP does **not** make the model literally learn new weights at runtime. Its "adaptation" comes from durable project/task state, recorded decisions, evidence, procedural skills, SOUL guidance, runtime hooks, and continuity-aware context handling.

## How Hermes / the AI is expected to understand HCP

After HCP is installed, Hermes should not think of it as "a database the user maintains" or as four extra tools that are only used when explicitly requested.

The intended model is:

> **HCP is the harness Hermes operates within. The persistence tools are only the surface API.**

For substantive work, Hermes should automatically use the relevant HCP mechanisms when they help. The normal pattern is roughly:

```text
EXPLORE
   ↓
PLAN / DIAGNOSE
   ↓
IMPLEMENT
   ↓
VERIFY
   ↓
REVIEW
   ↓
HANDOFF / RESUME
```

During that flow Hermes should, when appropriate:

- inspect the repository and existing implementation before changing code;
- preserve the current objective, constraints, blockers, next steps, and acceptance criteria;
- record material architectural or implementation decisions so they are not re-litigated later;
- distinguish verified facts from assumptions and hypotheses;
- record concrete verification evidence after edits;
- use root-cause debugging rather than looping over superficial fixes;
- review its own changes before declaring completion;
- preserve Git/change safety and avoid unrelated scope creep;
- use visual verification for UI-affecting work;
- use bounded delegation and AFK autonomy where useful;
- persist a coherent handoff before a session ends or context is compressed;
- recover from persisted state in a new session instead of asking the user to explain the project again.

The user should still be able to use Hermes normally. HCP is designed so the user does **not** need to say "record this in HCP" after every decision. Hermes should notice important state, decisions, blockers, evidence, and milestones itself and persist them when appropriate.

### What this feels like to a normal Hermes user

Install HCP once and keep using Hermes as usual. The visible differences should be things like:

- Hermes resumes a multi-session task with the correct objective and next step;
- it remembers important constraints and earlier decisions;
- it explores working code before replacing it;
- it is less likely to announce success before testing the result;
- it can survive a restart or context compaction without losing the project thread;
- long-running work gets a cleaner handoff instead of a vague "where were we?" reset.

In other words: **same model, better operating discipline around the model.**

## HCP 2.1 architecture

HCP 2.1 keeps the proven HCP 2.0 project kernel and adds cwd-independent ambient continuity:

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
             │                                  │
             │ + cwd-independent global state   │
             │ + structured pending intents     │
             │ + automatic future-instruction   │
             │   capture                        │
             └────────────────┬─────────────────┘
                              │
               SOUL + skills + project context
```

HCP deliberately prefers Hermes' documented plugin and context-engine APIs over patching Hermes core. This keeps the integration inspectable, reversible, and easier to upgrade.

## Research corpus and credit

HCP was bootstrapped against:

- **Primary research corpus:** [`asgeirtj/system_prompts_leaks`](https://github.com/asgeirtj/system_prompts_leaks)
- **Target runtime:** [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)

The upstream corpus does the substantial work of collecting and organizing captured system-prompt and agent material. HCP's original work is the **cross-agent mechanism model, Hermes-specific runtime integration, persistent continuity model, compiler/indexer, SOUL profiles, skills/bundles, verification/telemetry layer, installer, tests, and evaluation tooling**.

HCP does **not vendor the raw corpus by default**. Runtime installation does not require it. A local ZIP/checkout is only needed when reproducing the research analysis or rebuilding against a particular corpus snapshot. See [CREDITS.md](CREDITS.md), [THIRD_PARTY.md](THIRD_PARTY.md), and [docs/RESEARCH_METHOD.md](docs/RESEARCH_METHOD.md).

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

### Manual setup

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

### Cross-session behavior

A fresh Hermes process can read the project-scoped HCP state and recover the active objective, previous phase, constraints, recorded decisions, evidence, and next step. That is the mechanism intended to make long-running work survive a full process restart without relying on the model to reconstruct everything from vague conversational memory.

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

The bundles are convenient entry points, but HCP is not limited to explicit `/hcp-*` commands. The installed runtime, SOUL guidance, continuity integration, and skills are meant to influence ordinary Hermes operation where relevant.

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

## Why not concatenate every captured prompt into Hermes?

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

HCP is intended to make harness improvements measurable. Keep model, provider, tools, repository, and task fixed, then compare stock Hermes vs Hermes + HCP on observable outcomes such as:

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
