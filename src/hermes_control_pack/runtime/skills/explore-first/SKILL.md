---
name: explore-first
description: Map a repository or unfamiliar subsystem efficiently before editing.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Explore First

## When to Use
Use when the relevant code path, architecture, ownership, or existing implementation is not yet clear.

## Procedure
1. Read project context and git status.
2. Search for entry points, symbols, routes, config, tests, and analogous implementations.
3. Batch independent reads/searches.
4. Trace only the paths that can affect the requested outcome.
5. Record candidate edit surfaces and risks.
6. Stop exploration once there is enough evidence to act.

## Pitfalls
- Reading the repository linearly.
- Editing the first match before understanding call sites.
- Creating new abstractions when the project already has one.

## Verification
Be able to name the relevant entry point, execution/data path, likely edit surface, and nearby tests before implementation.
