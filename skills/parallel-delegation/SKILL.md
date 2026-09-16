---
name: parallel-delegation
description: Split independent work into bounded subagents without duplicating effort or creating edit conflicts.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, delegation, parallel]
    category: development
---

# Parallel Delegation

## When to Use
Use when two or more independent discovery, research, review, or implementation workstreams can proceed without contending for the same files/state.

## Procedure
1. Identify truly independent workstreams and the dependency graph between them.
2. Give each delegate a bounded question, relevant paths/context, a concrete deliverable, and a stop condition.
3. Prefer parallel reads/research/review; parallel writes require non-overlapping ownership.
4. Keep one parent responsible for integration decisions and acceptance criteria.
5. Reconcile delegate findings against repository/runtime evidence instead of accepting them blindly.
6. Re-run integrated verification after merging conclusions or edits.

## Pitfalls
- Sending multiple agents to rediscover the same facts.
- Allowing concurrent edits to the same surface without coordination.
- Delegating the final decision while losing user acceptance criteria.
- Treating a delegate's confidence as verification.

## Verification
Each delegated result has a clear provenance and the integrated result passes the parent task's actual verification gate.
