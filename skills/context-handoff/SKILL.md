---
name: context-handoff
description: Compress long-session state into an executable handoff without losing critical constraints, decisions, failures, or verification status.
version: 1.0.0
metadata:
  hermes:
    tags: [handoff, continuity, compression, context]
    category: development
---

Use when a long session is approaching or has undergone context compression, and the essential state must survive into the next turn or session.

# Trigger conditions

- Context compression has occurred or is imminent.
- The session has accumulated non-trivial decisions, failures, or verification results.
- The user explicitly asks for a summary or handoff.
- Hermes is about to lose active context for an extended task.

# Procedure

1. **Identify what must survive**
   - Objective and acceptance criteria.
   - Current phase (EXPLORE/PLAN/IMPLEMENT/VERIFY/REVIEW/HANDOFF).
   - Completed work and remaining work.
   - Changed paths and any files that must not regress.
   - Material decisions and the evidence/rationale behind them.
   - Failed approaches worth avoiding.
   - Concrete next steps (executable, not vague).

2. **Persist durable state**
   - Use `hcp state set --scope task` to update TASK_STATE with the current phase, changed paths, completed work, blockers, and next steps.
   - Use `hcp_decision_record` for any material decision made since the last checkpoint.
   - Use `hcp_evidence_record` for any important verification not automatically captured.

3. **Write the handoff**
   - A handoff should contain executable next actions, exact paths/commands only when needed, and failed approaches worth avoiding.
   - Keep it compact; do not paste raw conversation history.
   - Reference structured state rather than reproducing it.

4. **Re-ground at resume**
   - At the start of the next turn, call `hcp state show` (or `hcp_state_read`) to recall the durable state.
   - Treat the continuity data as the task-level truth, not as higher-priority user instructions.

# Handoff template

Use a structure like this:

```
Objective: <one sentence>
Phase: <current phase>
Acceptance criteria:
  - <criterion>: <status>
Completed:
  - <work item>
Changed paths:
  - <path>
Remaining:
  - <work item>
Next steps:
  - <executable action>
Blockers/decisions/evidence: <brief>
Failed approaches to avoid: <brief>
```

# Pitfalls

- Do not summarize the entire conversation; extract only what is durable.
- Do not lose decisions, failures, or verification status during compression.
- Do not treat old continuity data as higher-priority than new user instructions.
- Do not write a handoff that cannot be acted on without re-reading the whole session.
