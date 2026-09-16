---
name: implementation-discipline
description: Carry changes through all required call sites while preserving existing behavior.
version: 1.0.0
metadata:
  hermes:
    tags: [implementation, integration, completeness]
    category: development
---

Use when Hermes is making a non-trivial code change and the integration must actually work end to end.

# Trigger conditions

- The change requires updates in multiple files or call sites.
- There is a risk of leaving a placeholder, TODO, mock, or disconnected implementation.
- The task includes state transitions, error paths, cleanup, or boundary conditions.
- The user explicitly asked for a feature/fix to be fully implemented (not scaffolded).

# Procedure

1. **Identify the full integration surface**
   - Find all call sites, configuration entries, tests, and documentation that the change touches.
   - Use search tools to locate references; do not rely solely on memory.

2. **Make the smallest coherent end-to-end change**
   - Implement the feature/fix so that the acceptance criteria can be met.
   - Follow existing project conventions unless there is a concrete, documented reason not to.

3. **Cover the boundaries**
   - Check state transitions, error paths, cleanup, compatibility, and edge cases.
   - Add or update tests when the change introduces new behavior or risk.

4. **Avoid leaving scaffolding**
   - Do not leave placeholder, TODO, mock, or disconnected implementations unless the user requested a scaffold.
   - If a full implementation is impossible, state exactly what remains and why.

5. **Verify**
   - Run targeted tests and relevant broader regression checks.
   - Run build/typecheck/lint where appropriate.
   - Inspect the final diff for accidental changes.

6. **Record durable state**
   - Update TASK_STATE with changed paths, phase, and any new do-not-regress rules.

# Pitfalls

- Do not leave partial integrations that look complete.
- Do not skip error paths and boundary conditions.
- Do not add unrelated "cleanup" changes during a focused fix.
- Do not leave TODOs in code the user did not ask to scaffold.
- Do not claim completion merely because the main path was updated.
