---
name: ui-visual-verification
description: Verify UI changes against rendered output, interactions, assets, and reference visuals.
version: 1.0.0
metadata:
  hermes:
    tags: [frontend, ui, browser, visual, testing]
    category: development
---

Use when Hermes has made UI-affecting changes and the rendered output is the actual product.

# Trigger conditions

- The change touches `.tsx`, `.jsx`, `.css`, `.scss`, `.sass`, `.less`, `.html`, `.vue`, `.svelte`, or similar.
- The user explicitly asks for visual verification.
- Appearance, layout, sizing, clipping, responsive behavior, loading/error state, or interaction correctness matters.
- Browser/vision tooling is available.

# Procedure

1. **Confirm compilation first**
   - Ensure the project builds. Compilation alone is not visual verification, but a broken build makes rendering moot.

2. **Render and inspect**
   - Open the actual page/screen using browser/vision tools.
   - Compare layout, sizing, clipping, responsive behavior, loading/error states, and interactions relevant to the request.

3. **Use references when available**
   - Prefer provided reference images/assets over approximating from memory.
   - Compare against the reference, not against an imagined ideal.

4. **Verify at the target viewport/platform**
   - If the request is platform-specific, verify at the target viewport.
   - Check responsive behavior across breakpoints when relevant.

5. **Record visual evidence**
   - Use `hcp_evidence_record` with kind "visual" to record what was actually observed.
   - Screenshots or vision analysis serve as the evidence; do not claim "it looks right" without inspection.

# Pitfalls

- Do not treat compilation as visual verification.
- Do not approximate UI from memory when references or rendered output are available.
- Do not claim visual correctness without actually inspecting the rendered page.
- Do not ignore loading/error states.
