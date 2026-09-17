# Hermes Control Pack

**Hermes Control Pack 2.1 — Install once. Use Hermes anywhere.**

[![HCP 2.1](https://img.shields.io/badge/HCP-2.1-purple?style=flat-square)](https://github.com/n4thyan/hermes-control-pack)
[![Tests](https://img.shields.io/github/actions/workflow/status/n4thyan/hermes-control-pack/tests.yml?style=flat-square&label=tests)](https://github.com/n4thyan/hermes-control-pack/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.13-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-supported-success?style=flat-square&logo=windows)](https://github.com/n4thyan/hermes-control-pack/actions/workflows/tests.yml)
[![Linux](https://img.shields.io/badge/Linux-supported-success?style=flat-square&logo=linux)](https://github.com/n4thyan/hermes-control-pack/actions/workflows/tests.yml)
[![MIT License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-8A2BE2?style=flat-square)](https://github.com/NousResearch/hermes-agent)

A research-driven agent-harness augmentation layer for [NousResearch/Hermes Agent](https://github.com/NousResearch/hermes-agent).

HCP makes whichever model Hermes uses **more coherent and reliable during real work** — understand before editing, preserve your objective across sessions, recover from failed approaches, verify claims before finishing, and resume after compression or a new session without reconstructing the project from scratch.

## What HCP 2.1 does differently

> **Install HCP once, then use Hermes from any directory.** HCP 2.1 no longer requires you to launch Hermes from inside the `hermes-control-pack` clone.

After installation, HCP runtime assets live inside your Hermes installation/profile, and global continuity state lives under `HERMES_HOME` — **not** inside the HCP repository. The HCP Git clone is the **source/development** repository; it does not need to be your working directory for normal use.

Normal use after installation:

```bash
cd C:\Users\pc
hermes
```

```bash
cd C:\Users\pc\Desktop\some-project
hermes
```

```bash
cd C:\Users\pc\my-bin-weevils-project
hermes
```

HCP should still be active in all of cases.

### Two complementary scopes

```text
                Hermes Agent core
                       │
            ┌──────────┴──────────┐
            │                     │
     🌐 GLOBAL continuity     📁 PROJECT continuity
     (blue/purple)            (green/orange)
     follows you everywhere   augments when a project is detected
```

| | 🌐 GLOBAL (blue/purple) | 📁 PROJECT (green/orange) |
|---|---|---|
| **Lives where** | `<HERMES_HOME>/hcp/global/` | `.hcp/state/` in the project |
| **Follows** | the Hermes user/profile | the project/workspace |
| **CWD-dependent** | No — always available | Yes — attached to the project |
| **Contains** | pending instructions, cross-session continuity, durable user constraints | objective, phase, decisions, evidence, next steps, project-scoped instructions |

Project state **augments** global state when a project is detected. Project state never leaks into unrelated projects. Global state works regardless of which directory Hermes was launched from.

## Architecture

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

### How HCP is discovered when Hermes launches outside the clone

The `hcp setup` / `hcp install` commands copy HCP runtime assets (plugin, skills, bundles, SOUL overlay) into the user's Hermes home (`~/.hermes` on Linux, `%USERPROFILE%\.hermes` on Windows). Hermes discovers them from there on the next launch. **The HCP clone itself is not required at runtime.**

HCP runtime assets installed to `~/.hermes/`:

- `plugins/hcp-runtime/` — runtime plugin with hooks and tools
- `plugins/context_engine/hcp-continuity/` — optional continuity compressor
- `skills/` — 12 progressive-disclosure skills
- `skill-bundles/` — 5 Hermes skill bundles
- `SOUL.md` — managed balanced identity overlay (your custom text preserved)
- `hcp/global/` — cwd-independent global state
- `hcp/session-roots.json` — session-to-project mapping for resumed sessions

### What HCP improves

- [x] forgetting the real objective after a long session
- [x] restarting a project from scratch after context compression
- [x] editing code before understanding the repository
- [x] repeatedly patching symptoms instead of finding root cause
- [x] claiming something works without actually verifying it
- [x] losing blockers, next steps, or known-good state between sessions

HCP does **not** turn Hermes into GPT, Claude, Gemini, or any other model. The underlying model remains whatever provider/model Hermes is configured to use.

## Quick start

### Requirements

- Python 3.11+
- Hermes Agent installed

### Let Hermes set itself up

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

After running `hcp setup`, you can launch Hermes from **any** directory — HCP stays active.

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

## HCP 2.1 architecture details

### Global continuity (`🌐` blue/purple)

- **cwd-independent** — stored under `<HERMES_HOME>/hcp/global/`, not tied to any project
- **structured pending instructions** with trigger, timing, scope, lifecycle, priority, and one-shot consumption
- **explicit future-intent capture** — e.g. "next session when I say X, reply with Y"
- **trigger/activation semantics** — exact, contains, regex, next-session, always-active
- **one-shot completion** — successful `respond_exact` instructions are marked completed, not repeated forever
- **current-user supersession** — new direct user intent outranks stale persisted triggers
- **interruption/restart recovery** via `session-roots.json` mapping

### Project continuity (`📁` green/orange)

- **associated with the detected project/workspace** — stored in `.hcp/state/`
- **objective, phase, acceptance criteria, changed paths, blockers, next steps**
- **decisions + evidence ledgers** with append-only records
- **project-scoped pending instructions** that activate only inside their project
- **project state AUGMENTS global state** — never replaces it

### Other HCP 2.1 changes

- ambient pre-turn continuity bootstrap via `pre_llm_call` hook
- packaged runtime/source synchronization between `plugins/` and `src/hermes_control_pack/runtime/`
- the project_root ambient routing bug fixed during final release work (`project_root=""` → resolved via session→project mapping)
- expanded tests for launch-directory independence, project-scoped isolation, and cross-session behavior

## HCP 2.0 kernel preserved

HCP 2.1 keeps the proven HCP 2.0 project kernel intact:

- `PROJECT_STATE`, `TASK_STATE`, `DECISION_LOG`, `EVIDENCE_LEDGER`, `TRACE` stores
- four model-callable tools: `hcp_state_read`, `hcp_state_update`, `hcp_decision_record`, `hcp_evidence_record`
- bounded evidence-based completion gating (`pre_verify`)
- observable harness telemetry without requesting or storing model chain-of-thought
- private Git exclusion for `.hcp/` without modifying tracked `.gitignore`

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
plugins/hcp-runtime/       Hermes runtime plugin (reviewable top-level sources)
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
