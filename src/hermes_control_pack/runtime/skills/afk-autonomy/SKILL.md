---
name: afk-autonomy
description: Run long unattended work with bounded scope, evidence checkpoints, and recoverable state.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# AFK Autonomy

## When to Use
Use when the user wants Hermes to keep working while they are away.

## Procedure
1. Establish the requested outcome and strict scope boundary from existing context.
2. Inspect repo state and preserve/backup fragile surfaces when appropriate.
3. Work in small checkpoints: explore, change, verify, then continue.
4. Resolve routine blockers independently using repo/docs/tools.
5. Avoid destructive operations, credential changes, purchases, publishing, or irreversible product decisions unless already authorized.
6. Maintain a compact handoff state after meaningful milestones.
7. If a task proves blocked, move to another in-scope independent item rather than idling.
8. Before stopping, run final verification and summarize evidence plus remaining blockers.

## Pitfalls
- Wandering into unrelated cleanup simply to stay busy.
- Accumulating many unverified edits before testing.
- Repeatedly retrying the same failing approach without diagnosis.

## Verification
The working tree should end in a coherent, explainable state with tested checkpoints and a usable handoff.
