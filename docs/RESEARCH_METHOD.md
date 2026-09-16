# Research method

HCP treats captured system prompts and agent instructions as an **agent-architecture research corpus**, not as a monolithic prompt to copy into Hermes.

## Input

`hcp scan`, `hcp analyze`, `hcp mechanisms`, and `hcp build` accept a local ZIP or directory. Every file is indexed regardless of whether HCP recognizes its provider/product family.

For each entry HCP records deterministic metadata including path, byte size, SHA-256, text/binary status, approximate word count, top-level source family, artifact classification, behavior-family signals, and mechanism hits.

ZIP inputs are fingerprinted from the exact archive bytes. Directory fingerprints are deterministic over ordered `(relative path, file SHA-256)` pairs.

## Two analysis levels

### Behavior signals

Behavior-family counts answer broad questions such as: how often does the supplied corpus contain language about verification, delegation, context, debugging, research, tools, Git, UI/visual work, or autonomy?

These are simple reproducible coverage signals. They are not model-quality scores.

### Transferable mechanisms

HCP 2.0 adds an authored mechanism taxonomy. Examples include:

- inspect before edit;
- task-intent routing;
- root-cause debugging;
- evidence-gated completion;
- independent review;
- parallel delegation;
- context compaction;
- persistent memory routing;
- structured handoff;
- visual verification;
- Git change safety;
- failure recovery;
- interruption/resume;
- prompt-cache stability;
- provider adaptation;
- source grounding;
- bounded autonomy;
- tool-evidence reuse;
- state-machine execution.

For each mechanism the analyzer records supporting source families, file counts, raw phrase hits, example paths, purpose, and the intended HCP implementation layer.

A mechanism appearing in many products is **breadth evidence**, not proof that it is optimal. HCP implements these mechanisms as engineering hypotheses and evaluates their effects separately.

## Distillation rule

HCP does not concatenate raw vendor prompts into the runtime. Instead it asks:

1. What general harness behavior is being attempted?
2. Is the mechanism transferable to Hermes?
3. Which layer should own it: system kernel, SOUL, skill, runtime enforcement, persistent state, or provider adaptation?
4. Can its effect be measured with observable task outcomes?

This avoids importing conflicting product identity, proprietary tool schemas, stale UI rules, or millions of irrelevant tokens.

## Runtime provenance

The bootstrap source fingerprint and aggregate reports live under `sources/` and `reports/`. Generated HCP builds include their own `corpus-index.json`, `MECHANISMS.json`, mechanism matrix, and manifest hashing every emitted runtime artifact.

## Evaluation discipline

HCP does not infer that a mechanism improves capability merely because multiple commercial products use it. A fair comparison keeps the base model/provider/tools/task constant and measures observable outcomes such as successful completion, unnecessary clarification, premature mutation, evidence quality, regression rate, recovery behavior, token/context pressure, and cross-session continuity.
