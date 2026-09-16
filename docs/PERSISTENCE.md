# Persistent continuity

HCP treats a model context window as a **working set**, not as the authoritative project database.

## State hierarchy

HCP stores project-local runtime state under `.hcp/state/`:

- `PROJECT_STATE.json` — durable architecture, constraints, verified project facts, do-not-regress items, known verification commands.
- `TASK_STATE.json` — active objective, phase, acceptance criteria, current state, completed items, changed paths, blockers, next actions, last session/model.
- `DECISION_LOG.jsonl` — append-only material decisions with concise rationale/provenance.
- `EVIDENCE_LEDGER.jsonl` — append-only verification and observed-result records.
- `TRACE.jsonl` — observable harness telemetry. It records events and outcomes, not private model reasoning.

The state store is intentionally structured so a compressed or fresh session can recover a useful task model in a few thousand characters instead of replaying a large transcript.

## Git hygiene

When HCP detects a Git checkout it adds `/.hcp/` to that checkout's private `.git/info/exclude`. It does not edit a tracked `.gitignore`. Linked worktrees are supported by resolving the `gitdir:` pointer in the worktree's `.git` file.

Outside Git, HCP places an internal `.hcp/.gitignore` as defensive hygiene.

## Turn rehydration

The `hcp-runtime` plugin uses Hermes' `pre_llm_call` hook to inject a bounded structured continuity block on each user turn. This contains current project/task state plus recent decision/evidence entries.

The model can retrieve or update state explicitly through:

- `hcp_state_read`
- `hcp_state_update`
- `hcp_decision_record`
- `hcp_evidence_record`

A session-to-project mapping is persisted under `<HERMES_HOME>/hcp/session-roots.json`. This matters because Hermes restores frozen system-prompt sections after process restart/resume without re-running the section renderer. The durable mapping lets HCP still reconnect a resumed session to the correct project state.

## Compression

`hcp-continuity` subclasses Hermes' built-in `ContextCompressor`. It does not replace Hermes' summarization strategy. Immediately before a compaction, it renders bounded structured HCP continuity and supplies it through the compressor's `memory_context` input.

That yields two complementary layers:

```text
Hermes session history     complete searchable transcript / archive
Hermes compression         compact conversational handoff
HCP structured state       durable task/project/decision/evidence working model
```

Compression is still lossy prose summarization, so HCP does not pretend token limits disappear. Instead, high-value task information is persisted separately and rehydrated, while detailed historical material can remain in Hermes' session history for retrieval.

## Conflict policy

Persistent state is not allowed to override newer truth. When HCP state conflicts with:

1. a newer direct user instruction, or
2. verified current repository/runtime evidence,

Hermes should update the persistent state rather than obey stale state.

This prevents a compressed historical assumption from becoming an immortal instruction.

## Facts vs hypotheses

HCP encourages durable entries to distinguish:

- verified facts;
- unverified hypotheses;
- explicit decisions;
- evidence supporting a claim.

That distinction is important across long sessions: compression should not silently promote an old hypothesis into a project fact.
