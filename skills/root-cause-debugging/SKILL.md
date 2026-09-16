---
name: root-cause-debugging
description: Debug from reproduction and execution evidence instead of speculative edits.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Root-Cause Debugging

## When to Use
Use for bugs, crashes, incorrect output, regressions, broken integrations, or unexplained runtime behavior.

## Procedure
1. Reproduce or precisely characterize the failure.
2. Capture the smallest useful evidence: error, log, request/response, state, screenshot, or failing test.
3. Trace backward to the first point where actual behavior diverges from expected behavior.
4. Form a root-cause hypothesis and test it against the code/runtime.
5. Patch the cause, not merely the visible symptom.
6. Re-run the original failing path and adjacent regression checks.

## Pitfalls
- Random changes.
- Suppressing errors without fixing the cause.
- Fixing one call site while leaving identical broken paths elsewhere.

## Verification
Show that the original failure no longer reproduces and that relevant neighboring behavior still passes.
