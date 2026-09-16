---
name: git-change-safety
description: Preserve user work and keep repository changes reviewable, attributable, and recoverable.
version: 1.0.0
metadata:
  hermes:
    tags: [git, coding, safety, review]
    category: development
---

# Git Change Safety

## When to Use
Use before and after substantive repository modifications, especially in dirty working trees or long autonomous sessions.

## Procedure
1. Inspect status, current branch, and relevant diff before editing.
2. Treat unrelated changes as user-owned; do not revert or rewrite them for convenience.
3. Avoid generated files, secrets, caches, and large artifacts unless intentionally tracked by the project.
4. Keep the change set coherent enough to review and revert.
5. Inspect final status/diff for accidental scope expansion or missing files.
6. Only claim commit/push/PR success when the corresponding tool command confirms it.

## Pitfalls
- Resetting a dirty tree.
- Committing credentials or local build output.
- Staging unrelated user edits.
- Saying "pushed" because a local commit exists.

## Verification
The final diff contains only intended work, user-owned changes remain intact, and any publication action is confirmed by the repository service.
