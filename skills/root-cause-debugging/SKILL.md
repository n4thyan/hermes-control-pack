---
name: root-cause-debugging
description: Debug from reproduction and execution evidence instead of speculative edits.
version: 1.0.0
metadata:
  hermes:
    tags: [debugging, root-cause, testing]
    category: development
---

Use when the user reports a defect, test failure, incorrect output, or regression and the cause is not already proven.

# Trigger conditions

- A test is failing.
- The application crashes, returns wrong output, or behaves unexpectedly.
- A previous "fix" did not resolve the issue.
- The user says "debug this" or "why is X happening".

# Procedure

1. **Reproduce or precisely characterize the failure**
   - Run the failing command, test, endpoint, or interaction.
   - Capture the smallest useful evidence: error message, log, stack trace, request/response, state diff, or screenshot.
   - If reproduction is not possible, state precisely what is unknown and proceed with the strongest available evidence.

2. **Collect narrow evidence**
   - Add targeted logging or a focused test only if needed; avoid speculative changes.
   - Compare actual behavior against expected behavior at the first point of divergence.

3. **Form a root-cause hypothesis**
   - State the hypothesis explicitly.
   - Test it against code and runtime evidence. Do not treat a hypothesis as a fix.

4. **Patch the cause, not the symptom**
   - Make the smallest change that addresses the root cause.
   - Avoid suppressing the visible symptom while leaving the underlying defect.

5. **Re-run the original failure path**
   - Verify the specific failure is resolved.
   - Run adjacent regression checks to detect unintended consequences.

6. **Record the finding**
   - Use `hcp_decision_record` to record the root cause and the evidence that proved it.
   - Use `hcp_evidence_record` to record the verification result.

# Anti-patterns

- Speculative edits (changing things at random hoping the bug disappears).
- Repeatedly re-running the same failing command without new evidence.
- Claiming a fix merely because a file changed.
- Treating a correlation as a root cause.
- Leaving temporary debugging scaffolding in the final diff.

# Pitfalls

- Do not use random edits as a debugging strategy.
- Do not suppress a defect without proving the cause is addressed.
- Do not claim a fix without re-running the original failure path.
- Do not leave temporary debug scaffolding in the final change.
