---
name: verification-gate
description: Require concrete test, build, runtime, API, or visual evidence before claiming completion.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Verification Gate

## When to Use
Use after any substantive implementation or fix and before saying it works.

## Procedure
1. Identify what evidence would actually prove the acceptance criteria.
2. Run the narrowest high-signal checks first.
3. Run broader regression checks appropriate to the touched surface.
4. For UI work, exercise the page in a browser and inspect rendered output/screenshot when tools permit.
5. For services, verify startup and representative request/response paths when practical.
6. Inspect command exit codes and failure output; do not infer success from silence.
7. Record exactly what was and was not verified.

## Pitfalls
- Claiming success because code compiles when runtime behavior matters.
- Claiming visual parity without viewing the render.
- Ignoring flaky/failing checks.

## Verification
A final claim must map directly to observed evidence.
