---
name: verification-gate
description: Require concrete test, build, runtime, API, or visual evidence before claiming completion.
version: 1.0.0
metadata:
  hermes:
    tags: [verification, testing, evidence, completion]
    category: development
---

Use when Hermes is about to declare work complete — especially after code changes, UI work, or multi-file modifications.

# Trigger conditions

- The agent is about to claim a feature, fix, or change is "done".
- The user explicitly asked for verification.
- Code was changed in the current session and no evidence has been gathered yet.
- UI-affecting changes were made and rendered-state evidence is available.

# Procedure

1. **Map acceptance criteria to evidence**
   - What must be true for the work to be considered complete?
   - For each criterion, choose evidence that actually proves it:
     - targeted tests, followed by relevant broader regression tests;
     - build/typecheck/lint/static analysis;
     - application or service startup;
     - representative runtime, API, or network checks;
     - browser interaction and rendered-state inspection for UI work;
     - screenshots or reference comparison where appearance matters;
     - `git diff`/`git status` review for accidental changes.

2. **Run the evidence**
   - Read exit codes and failure output.
   - If a check fails, fix and re-run rather than rephrasing the completion claim.

3. **Handle missing verification gracefully**
   - If a check cannot be run, state precisely what remains unverified and why.
   - A task may finish with an explicit limitation if verification is genuinely impossible.

4. **Record evidence**
   - HCP automatically records verification events from tool calls.
   - Use `hcp_evidence_record` for important checks that HCP cannot observe (screenshots, manual comparisons, custom scripts).

5. **Challenge completion claims**
   - Words like "fixed", "working", "complete", "done", "pushed", "deployed" require observed evidence.
   - Do not claim model-level capabilities, test results, runtime behavior, publication, or deployment that was not actually demonstrated.

# Completion contract

A final completion report should state, compactly:

- what changed;
- what was verified;
- the concrete verification result;
- anything genuinely remaining or unverified.

# Pitfalls

- Do not equate "code was written" with "it works".
- Do not claim completion without evidence after edits.
- Do not demand meaningless tests for every trivial task.
- Do not fabricate verification results.
