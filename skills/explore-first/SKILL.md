---
name: explore-first
description: Map a repository or unfamiliar subsystem efficiently before editing.
version: 1.0.0
metadata:
  hermes:
    tags: [exploration, codebase, understanding]
    category: development
---

Use when Hermes is about to edit code in an unfamiliar area, or when the user asks for an architectural understanding before any change.

# Trigger conditions

- The edit surface spans more than one file or module.
- The relevant code paths, entry points, or conventions are not already in active context.
- A previous exploration has been invalidated by context compression or a new session.
- The user asks "how does X work" or "where is Y implemented".

# Procedure

1. **Find the project root and conventions**
   - Use `hcp state show --scope project` (or `hcp_state_read`) to recall any stored architecture facts, constraints, and do-not-regress rules.
   - Run `git status` / `ls` / inspect `pyproject.toml`, `package.json`, or equivalent to understand the stack and entry points.

2. **Locate the implementation**
   - Search for the feature, symbol, config key, or error message.
   - Read entry points (main, app, router, handler, component) before leaf utilities.
   - Read tests to understand intended behavior and edge cases.

3. **Trace the relevant paths**
   - Follow only code paths that can affect the requested result.
   - Stop exploring once the edit surface is supported by evidence.
   - Note state transitions, error paths, cleanup, and boundary conditions.

4. **Record durable facts**
   - If the exploration surfaces reusable architecture facts (entry points, conventions, constraints), update PROJECT_STATE via `hcp state set --scope project`.
   - Keep exploration findings compact; they belong in structured state, not in conversational prose.

5. **Proceed to the actual work**
   - Hand off to the implementation, planning, or diagnosis skill with the gathered evidence.
   - Do not edit during exploration unless that was the explicit request.

# Stop conditions

- You have read the relevant entry points, nearby implementations, tests, and configuration.
- You can describe the edit surface and its dependencies to the user.
- The user explicitly asked you to stop exploring and produce a plan or answer.

# Pitfalls

- Do not read an entire repository; scope exploration to what can affect the result.
- Do not edit during exploration unless explicitly asked.
- Do not rediscover facts already stored in PROJECT_STATE.
- Do not treat exploration as implementation.
