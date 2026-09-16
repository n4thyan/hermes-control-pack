---
name: independent-review
description: Challenge completed work with a separate review pass for regressions, incomplete integration, and unsupported claims.
version: 1.0.0
metadata:
  hermes:
    tags: [review, quality, verification]
    category: development
---

Use when Hermes has completed substantive work and should challenge its own output before declaring done.

# Trigger conditions

- A non-trivial feature, fix, refactor, or integration was just implemented.
- The user explicitly asked for a review.
- The work touches multiple files, error paths, or high-risk surfaces.
- A previous review found issues and the work was modified again.

# Procedure

1. **Inspect the final diff rather than relying on memory**
   - Read the changed files.
   - Check `git diff`/`git status` for accidental changes.

2. **Map acceptance criteria to evidence**
   - For each acceptance criterion, find a code path and verification result that proves it.
   - Verify that claimed behavior is actually supported by the implementation.

3. **Search for common defects**
   - Stale references and missed call sites.
   - TODOs, dead branches, and duplicated logic.
   - Accidental scope expansion (unrelated changes sneaking in).
   - Error paths and regressions.
   - Hardcoded paths, secrets, or local configuration left in.

4. **Challenge completion claims**
   - Are "fixed", "working", "complete" claims supported by observed evidence?
   - Is any claimed capability, test result, or runtime behavior actually demonstrated?

5. **Decide and report**
   - If issues are found, fix them and re-run impacted verification.
   - If the work passes, record the review outcome concisely.

# Pitfalls

- Do not skip review for substantive changes.
- Do not rely on memory of what the code does; read the actual diff.
- Do not treat "it looks right" as evidence without verification.
- Do not ignore accidental changes just because the main feature works.
