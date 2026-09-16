---
name: implementation-discipline
description: Carry changes through all required call sites while preserving existing behavior.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Implementation Discipline

## When to Use
Use once the target behavior and edit surface are understood.

## Procedure
1. Re-read the acceptance criteria and relevant conventions.
2. Make the smallest coherent change set.
3. Update all required call sites/config/tests/docs that are part of the same integration.
4. Preserve unrelated user changes.
5. Check errors, cleanup paths, compatibility, and state transitions.
6. Run focused verification before broad verification.

## Pitfalls
- Placeholder code presented as complete.
- Unrelated refactors mixed into a bug fix.
- Hidden behavior changes without tests or explanation.

## Verification
The requested behavior is implemented end-to-end, with no known disconnected pieces.
