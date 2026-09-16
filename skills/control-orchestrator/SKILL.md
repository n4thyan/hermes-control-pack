---
name: control-orchestrator
description: Route substantive work through exploration, implementation, verification, review, and handoff.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Control Orchestrator

## When to Use
Use for multi-step coding, repo maintenance, integrations, or autonomous/AFK work.

## Procedure
1. Classify the requested outcome: explain, diagnose, plan, implement, review, or verify.
2. Inspect repository context and current state before changing files.
3. Build a short working plan only when complexity warrants it.
4. Delegate independent discovery/review workstreams when useful; avoid parallel edits to the same surface.
5. Implement the smallest coherent solution.
6. Load the verification skill and gather concrete evidence.
7. Load the review skill for substantive/high-risk changes.
8. End with a compact evidence-based handoff.

## Pitfalls
- Treating a written patch as a verified result.
- Asking the user for facts available in the repo.
- Parallelizing tightly coupled edits that will conflict.
- Expanding scope into unrelated cleanup.

## Verification
The task is complete only when the user's acceptance criteria are checked with the strongest practical evidence.
