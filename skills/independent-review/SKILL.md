---
name: independent-review
description: Review the final diff for regressions, incomplete integration, and unsupported claims.
version: 1.0.0
metadata:
  hermes:
    tags: [coding, orchestration, reliability]
    category: development
---

# Independent Review

## When to Use
Use for multi-file, high-risk, user-facing, or long-running autonomous changes.

## Procedure
1. Inspect the final diff rather than relying on implementation memory.
2. Compare each acceptance criterion to a concrete code path and verification result.
3. Search for stale names, missed call sites, TODOs, dead branches, and duplicated logic.
4. Examine error paths and rollback/cleanup behavior.
5. If delegation is available, have a separate reviewer challenge the result without being told what to conclude.
6. Fix material findings, then re-run impacted verification.

## Pitfalls
- Rubber-stamping the implementer's own assumptions.
- Reviewing style while missing behavioral regressions.

## Verification
No unresolved material finding remains without being explicitly disclosed.
