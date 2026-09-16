---
name: ui-visual-verification
description: Verify UI changes against rendered output, interactions, assets, and reference visuals.
version: 1.0.0
metadata:
  hermes:
    tags: [frontend, ui, browser, visual, testing]
    category: development
---

# UI Visual Verification

## When to Use
Use for frontend layout, styling, graphics, responsive behavior, visual parity, or interaction changes.

## Procedure
1. Identify the target viewport/platform and any supplied reference image or original implementation.
2. Inspect existing component/layout/asset conventions before editing.
3. Build/run the relevant frontend and exercise the target screen in a browser when tools permit.
4. Inspect the rendered result, not just DOM/source code.
5. Check sizing, alignment, clipping, stacking, fonts/assets, loading/error states, and relevant interactions.
6. Compare against references at the same state/viewport when parity matters.
7. Re-test after final CSS/layout changes because small edits can introduce regressions elsewhere.

## Pitfalls
- Claiming parity from source inspection alone.
- Testing only the happy-state screenshot while ignoring interaction/state changes.
- Replacing provided assets with approximations without need.

## Verification
The requested screen is visibly correct at the target state/viewport and its relevant interactions still work.
