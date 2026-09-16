---
name: context-handoff
description: Compress long-session state into an executable handoff without losing critical constraints.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Context Handoff

## When to Use
Use before context compression, model/session changes, or the end of a long work block.

## Procedure
Capture only durable execution state under:
- GOAL
- ACCEPTANCE CRITERIA
- CURRENT STATE
- DISCOVERIES
- CHANGES MADE
- VERIFICATION / RESULTS
- FAILURES / ATTEMPTS NOT TO REPEAT
- DO NOT REGRESS
- NEXT EXECUTABLE STEPS

Include exact paths, commands, ports, branches, and error text only when they matter to continuation. Separate facts from hypotheses.

## Pitfalls
- Narrative diary entries.
- Omitting failed approaches, causing the next session to repeat them.
- Saying 'continue debugging' instead of specifying the next executable check.

## Verification
A fresh agent should be able to continue without re-discovering the core state.
