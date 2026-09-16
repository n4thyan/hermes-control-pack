# Benchmark specification

HCP includes a small, model-agnostic evaluation spec for comparing **stock Hermes** with **Hermes + HCP**. The repository does not publish fabricated benchmark numbers.

`tasks.json` contains behavioral scenarios and observable pass criteria. Run the same model/provider/tool configuration twice, changing only whether HCP is installed. Record evidence in your own results file.

Suggested dimensions:

- unnecessary clarification rate;
- edits made before repository inspection;
- original failure reproduced before patching;
- completion claims with verification evidence;
- unrelated change rate;
- final diff review performed;
- UI claims backed by rendered-state inspection;
- handoff completeness after long sessions.

Model intelligence, latency, provider availability, and tool configuration are confounders; keep them fixed when evaluating the harness.
