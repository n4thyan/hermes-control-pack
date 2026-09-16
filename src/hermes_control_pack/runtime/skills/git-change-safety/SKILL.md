---
name: git-change-safety
description: Preserve user work and keep repository changes reviewable, attributable, and recoverable.
version: 1.0.0
metadata:
  hermes:
    tags: [git, safety, review, workflow]
    category: development
---

Use when Hermes is making changes in a Git repository and the changes must be safe, reviewable, and recoverable.

# Trigger conditions

- The current project is a Git checkout.
- Hermes is about to create, modify, or delete files.
- The user explicitly asks for a commit, branch, or PR workflow.
- There is a risk of overwriting user changes or committing secrets.

# Procedure

1. **Inspect state before and after changes**
   - Run `git status` before substantive changes to understand the working tree.
   - Run `git diff`/`git status` after substantive changes to verify the delta is intended.

2. **Protect user changes**
   - Do not overwrite unrelated working-tree changes.
   - Treat user changes as intentional unless evidence proves otherwise.

3. **Avoid committing generated artifacts, secrets, and local config**
   - Do not commit `__pycache__`, `.pyc`, build artifacts, wheels, egg-info, or temporary files.
   - Do not commit secrets, API keys, tokens, or credentials.

4. **Use commits, branches, and worktrees appropriately**
   - Follow the project's established workflow.
   - Keep commits reviewable and attributable.
   - Prefer reversible changes over sweeping rewrites.

5. **Never claim a commit/push/PR occurred unless the tool result confirms it**
   - Verify the actual Git operation succeeded.
   - Report the commit SHA or PR URL only after confirmation.

# Pitfalls

- Do not overwrite unrelated user changes.
- Do not commit secrets or generated artifacts.
- Do not claim a Git operation occurred without tool confirmation.
- Do not change the user's `.gitignore` without need (HCP uses private git exclude instead).
