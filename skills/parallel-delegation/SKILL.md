---
name: parallel-delegation
description: Split independent work into bounded subagents without duplicating effort or creating edit conflicts.
version: 1.0.0
metadata:
  hermes:
    tags: [delegation, parallelism, subagents]
    category: development
---

Use when a task has genuinely independent workstreams that can be delegated, and the parallelism would save real time.

# Trigger conditions

- The task contains independent sub-problems (e.g., parallel research, independent implementations, separate review passes).
- The sub-problems do not edit the same files or surfaces.
- The user explicitly or implicitly allows delegation (e.g., "check these three things", "investigate in parallel").

Do NOT use when the workstreams are tightly coupled, share files, or require sequential reasoning.

# Procedure

1. **Confirm independence**
   - Each delegated unit must have a bounded question, a concrete deliverable, relevant paths, and a stop condition.
   - Ensure no two units edit the same files or surfaces without explicit merge coordination.

2. **Write a bounded contract**
   For each unit, specify:
   - the question or objective;
   - the expected deliverable (findings, diff, verification result);
   - the relevant paths or scope;
   - a stop condition (when to report back rather than continuing indefinitely).

3. **Avoid duplication**
   - Search for existing implementation before delegating creation of new helpers.
   - Share established facts across units; do not repeatedly rediscover the same thing.

4. **Verify delegated conclusions before incorporating**
   - Do not treat a subagent's "success" message as verified proof.
   - Cross-check material claims against repository/runtime evidence.

5. **Reconcile and integrate**
   - Merge results into the main task.
   - Update TASK_STATE with combined changed paths and next steps.

# Pitfalls

- Do not delegate tightly coupled work.
- Do not let multiple agents edit the same files simultaneously.
- Do not treat delegated conclusions as verified without evidence.
- Do not invent fake parallelism for sequential work.
- Do not give agents unbounded or ambiguous objectives.
