---
name: control-orchestrator
description: Route substantive work through exploration, planning, implementation, verification, review, and handoff.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, routing, lifecycle]
    category: development
---

Use when the user asks Hermes to build, fix, or change something non-trivial, and the outcome matters enough that skipping evidence-producing phases would be risky.

# Trigger conditions

- A feature, fix, refactor, or integration that touches more than one file or concept.
- A bug report or regression where the root cause is not already proven.
- A multi-step request where partial delivery would look complete but leave the job broken.
- Any task where "I changed files" is not the same as "the acceptance criteria are met".

Do not force trivial questions (look up a command, explain one function, rename one variable) through the full workflow.

# Procedure

## 1. Classify the task outcome

Identify the dominant mode before acting:

- EXPLAIN — answer from evidence; do not modify files.
- EXPLORE — map architecture/code paths; stop when enough is known to act.
- PLAN — inspect as needed and produce an executable plan; do not implement unless asked.
- DIAGNOSE — reproduce, trace, and root-cause; do not claim a fix merely because a hypothesis exists.
- IMPLEMENT — make the smallest coherent end-to-end change.
- REVIEW — challenge the diff/result independently.
- VERIFY — gather evidence against explicit acceptance criteria.

## 2. Use the smallest useful workflow

For substantive implementation, apply the loop:

**EXPLORE → PLAN/DIAGNOSE → IMPLEMENT → VERIFY → REVIEW → HANDOFF**

Skip a phase only when the task genuinely does not need it (a single-line rename does not need exploration; a pure explanation does not need implementation).

## 3. Explore before editing

- Read the relevant project context, repository status, entry points, nearby implementations, tests, and configuration.
- Search for an existing helper, convention, or abstraction before creating another.
- Trace only the code paths that can affect the requested result; stop exploring once the edit surface is supported by evidence.
- Batch independent reads/searches where tools allow it.

## 4. Plan when the work is non-obvious

State the objective, the concrete acceptance criteria, and the evidence that will prove the work is done. For larger work, record decisions and changed paths in TASK_STATE.

## 5. Implement completely

- Finish the in-scope integration, including required call sites, config, tests, and docs when they are part of the same behavior.
- Do not leave placeholder, TODO, mock, or disconnected implementations unless the user requested a scaffold.
- Follow existing project conventions unless there is a concrete, documented reason not to.

## 6. Verify against real evidence

Choose evidence that actually proves the acceptance criteria:

- targeted tests, followed by relevant broader regression tests;
- build, typecheck, lint, or static analysis;
- application or service startup;
- representative runtime, API, or network checks;
- browser interaction and rendered-state inspection for UI work;
- screenshots or reference comparison where appearance matters;
- `git diff`/`git status` review for accidental changes.

Read exit codes and failure output. If a check cannot be run, state precisely what remains unverified and why.

## 7. Review before declaring complete

Inspect the final diff rather than relying on implementation memory. Map each acceptance criterion to a code path and verification result. Search for stale references, missed call sites, TODOs, dead branches, duplicated logic, and accidental scope expansion.

## 8. Handoff

Leave a concise record of what changed, what was verified, concrete verification results, and anything remaining or unverified. Update TASK_STATE if the phase, changed paths, or next steps changed.

# Pitfalls

- Do not equate "code was written" with "it works".
- Do not skip evidence-producing phases when runtime behavior can break.
- Do not force every trivial request through every stage.
- Do not leave the user with a partial integration that looks complete.
- Do not claim a fix merely because a file changed.
