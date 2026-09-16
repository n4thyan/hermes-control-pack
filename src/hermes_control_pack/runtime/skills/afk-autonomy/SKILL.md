---
name: afk-autonomy
description: Run long unattended work with bounded scope, evidence checkpoints, and recoverable state.
version: 1.0.0
metadata:
  hermes:
    tags: [autonomy, reliability, long-running]
    category: development
---

Use when the user explicitly leaves Hermes working without them ("AFK", "while I'm away", "keep going", "finish the remaining work").

# Trigger conditions

- The user explicitly indicates they will be away.
- The task is bounded in scope and the acceptance criteria are known.
- The user has pre-authorized autonomous execution within a defined scope.

# Procedure

1. **Preserve the original objective**
   - State the objective, scope, and acceptance criteria at the start of the unattended stretch.
   - If they are not already in TASK_STATE, record them now.

2. **Inspect before asking**
   - Do not ask the user for facts obtainable from the repo, environment, docs, logs, or available tools.
   - Answer locally first; ask only when a material blocker is genuinely unavailable or a consequential ambiguity cannot be resolved safely from evidence.

3. **Work in small explore/change/verify checkpoints**
   - Each checkpoint should be a coherent, verifiable unit of work.
   - Checkpoint state after each step (changed paths, phase, next steps in TASK_STATE).

4. **Repair failures**
   - Diagnose from evidence before patching.
   - If one path is blocked, switch to another independent in-scope item instead of idling.
   - Change strategy after repeated failure instead of looping.

5. **Keep a bounded scope**
   - Do not invent extra scope merely to remain busy.
   - Avoid purchases, credential rotations, publishing, destructive migrations, or consequential product decisions unless already explicitly authorized.

6. **Verify and hand off**
   - Verify each checkpoint with evidence appropriate to the work.
   - Leave an executable handoff: what was completed, what remains, what failed, what to try next.

# Stop conditions

- The acceptance criteria are met.
- A material blocker is genuinely unavailable.
- The pre-authorized scope is exhausted.

# Pitfalls

- Do not invent extra scope to stay busy.
- Do not loop on the same failing approach without changing strategy.
- Do not ask questions answerable from the local repo/environment.
- Do not treat the user's absence as authorization for consequential actions outside the defined scope.
- Do not abandon state; always leave a recoverable handoff.
