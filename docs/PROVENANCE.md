# Runtime Rule Provenance

HCP runtime rules are original, vendor-neutral syntheses informed by recurring mechanisms across the supplied research corpus and by Hermes' documented architecture.

This document describes **mechanism provenance**, not sentence-level copying.

| HCP mechanism | Corpus signal families used to check breadth | Hermes runtime surface |
|---|---|---|
| Inspect before editing | exploration, tools | `.hermes.md`, `explore-first` |
| Diagnose before patching | debugging, exploration | `root-cause-debugging` |
| Complete integrations end-to-end | implementation, context | `implementation-discipline` |
| Evidence before completion claims | verification, review | `verification-gate` |
| Independent final challenge | review, verification | `independent-review` |
| Parallel bounded workstreams | delegation, tools | `parallel-delegation` |
| Preserve user changes | git, safety | `git-change-safety` |
| Rendered-state UI checks | visual, verification | `ui-visual-verification` |
| Source-grounded external research | research, tools | `research-evidence` |
| Bounded unattended progress | autonomy, context, safety | `afk-autonomy` |
| Executable context compression | context, planning | `context-handoff` |

The exact source groups and counts for a local build are generated into `RESEARCH_SIGNALS.md` and `corpus-index.json`.
