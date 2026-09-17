# Persistent continuity

HCP treats a model context window as a **working set**, not as the authoritative continuity database.

## Two persistence scopes

HCP 2.1 separates continuity into **global/user state** and **project state**.

### Global state (🌐 blue/purple — cwd-independent)

Global state lives under `<HERMES_HOME>/hcp/global/` and is deliberately independent of the directory from which Hermes was launched:

- `GLOBAL_STATE.json` — cwd-independent durable user constraints, recent handoffs, and global continuity metadata.
- `PENDING_INSTRUCTIONS.json` — structured future/cross-session instructions with triggers, lifecycle state, scope, timing, and one-shot consumption semantics.
- `GLOBAL_TRACE.jsonl` — observable global continuity events.

This means global continuity still works whether Hermes is launched from a project checkout, `C:\Users\pc`, the user's home directory, or another arbitrary path.

### Project state (📁 green/orange — project-attached)

Project-local runtime state remains under `.hcp/state/`:

- `PROJECT_STATE.json` — durable architecture, constraints, verified project facts, do-not-regress items, known verification commands.
- `TASK_STATE.json` — active objective, phase, acceptance criteria, current state, completed items, changed paths, blockers, next actions, last session/model.
- `DECISION_LOG.jsonl` — append-only material decisions with concise rationale/provenance.
- `EVIDENCE_LEDGER.jsonl` — append-only verification and observed-result records.
- `TRACE.jsonl` — observable harness telemetry. It records events and outcomes, not private model reasoning.

### How they relate

The two layers are intentionally complementary: global state follows the Hermes user/profile everywhere, while project state stays attached to the repository/workspace it describes. **Project state augments global state when a project is detected — it never replaces it.**

| | 🌐 Global | 📁 Project |
|---|---|---|
| Lives where | `<HERMES_HOME>/hcp/global/` | `.hcp/state/` in the project |
| Follows | the Hermes user/profile | the project/workspace |
| CWD-dependent | No | Yes |
| Contains | pending instructions, cross-session continuity, durable user constraints | objective, phase, decisions, evidence, next steps |

## Pending instructions

Future user intent should not be buried as prose in transcript history. HCP 2.1 can persist explicit cross-session instructions as structured objects with fields such as:

```text
id
scope: global | project
trigger_type: contains_any | exact | regex | next_session | always
trigger_patterns
action
action_type
active_after
expires_at
priority
status: pending | triggered | completed | cancelled | superseded | expired
consume_after_success
```

On every user turn, HCP checks relevant pending instructions before the model answers. Matching instructions are injected as **active continuity instructions**, not merely passive memories.

For narrow, explicit forms such as "next session when I say X, reply with Y" or "tomorrow when I say X, respond with Y", HCP can capture the instruction automatically. Ambiguous future intent is not silently promoted into an executable instruction; instead the runtime tells Hermes to persist it explicitly through `hcp_state_update`.

For `respond_exact` instructions, HCP also uses Hermes' documented `transform_llm_output` surface. If the model ignores a matched exact-response instruction, the runtime can replace the final text with the user-authored response. Successful one-shot instructions are then marked completed rather than repeated forever.

## Git hygiene

When HCP detects a Git checkout it adds `/.hcp/` to that checkout's private `.git/info/exclude`. It does not edit a tracked `.gitignore`. Linked worktrees are supported by resolving the `gitdir:` pointer in the worktree's `.git` file.

Outside Git, HCP places an internal `.hcp/.gitignore` as defensive hygiene for project-local state. Global state is stored under Hermes home and is never tied to a repository checkout.

## Turn rehydration

The `hcp-runtime` plugin uses Hermes' `pre_llm_call` hook on every user turn.

HCP 2.1 layers two bounded context blocks:

1. cwd-independent global continuity from `<HERMES_HOME>/hcp/global/`;
2. project/task continuity from the current project state when a project root is available.

The model does not need to remember to call HCP before global continuity can influence a turn. The harness loads it first.

The model can also retrieve or update continuity explicitly through:

- `hcp_state_read`
- `hcp_state_update`
- `hcp_decision_record`
- `hcp_evidence_record`

`hcp_state_read` includes `global` and `instructions` scopes in addition to project/task/decision/evidence views. `hcp_state_update` can write `global` state and structured `instruction` entries.

A session-to-project mapping is persisted under `<HERMES_HOME>/hcp/session-roots.json`. This matters because Hermes restores frozen system-prompt sections after process restart/resume without re-running the section renderer. The durable mapping lets HCP reconnect a resumed session to the correct project state when one exists, while global continuity remains available regardless of launch path.

## Compression

`hcp-continuity` subclasses Hermes' built-in `ContextCompressor`. It does not replace Hermes' summarization strategy. Immediately before a compaction, it renders bounded structured HCP continuity and supplies it through the compressor's `memory_context` input.

The resulting continuity stack is:

```text
Hermes session history     complete searchable transcript / archive
Hermes compression         compact conversational handoff
HCP global state           cwd-independent user/future-intent continuity
HCP project state          durable task/project/decision/evidence working model
```

Compression is still lossy prose summarization, so HCP does not pretend token limits disappear. Instead, high-value task information and future intent are persisted separately and rehydrated, while detailed historical material can remain in Hermes' session history for retrieval.

## Conflict policy

Persistent state is not allowed to override newer truth. When HCP state conflicts with:

1. a newer direct user instruction, or
2. verified current repository/runtime evidence,

Hermes should update, cancel, supersede, or complete the persistent state rather than obey stale data.

This prevents an old compressed assumption or pending instruction from becoming immortal.

## Facts vs hypotheses

HCP encourages durable entries to distinguish:

- verified facts;
- unverified hypotheses;
- explicit decisions;
- evidence supporting a claim;
- pending future instructions.

That distinction is important across long sessions: compression should not silently promote an old hypothesis into a project fact, and a historical instruction should not be treated as active unless its structured trigger actually matches.
