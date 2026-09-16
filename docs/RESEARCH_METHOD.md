# Research Method

## Goal

HCP uses a broad public prompt/agent corpus to identify **transferable agent-harness mechanisms** for Hermes: task routing, exploration, planning, debugging, verification, review, delegation, context management, tool discipline, and autonomous progress.

The project deliberately avoids the claim that a leaked prompt can reproduce another model's intrinsic intelligence or private infrastructure.

## Corpus

Primary bootstrap source:

- `asgeirtj/system_prompts_leaks`

HCP accepts arbitrary ZIPs/directories, so the analysis is reproducible against future upstream snapshots or other legally obtained corpora.

## What the scanner measures

HCP v1 uses deterministic phrase families as a **coverage instrument**. It records how often broad concepts appear and across how many top-level source groups/files. These numbers answer questions such as:

- did the supplied corpus actually contain material about verification?
- is delegation represented across multiple source families?
- which source families were included in this exact build?

The numbers do **not** mean:

- one vendor is better than another;
- a frequently mentioned rule should automatically have higher priority;
- every matched phrase is semantically equivalent;
- source prompts are authentic/current simply because they were present in the corpus.

## Distillation policy

Runtime HCP instructions are authored in vendor-neutral language. We extract mechanisms, not passages.

A proposed runtime rule should generally satisfy all of the following:

1. transferable to Hermes' actual tools/architecture;
2. useful across a meaningful class of tasks;
3. not dependent on a proprietary unavailable tool or UI;
4. compatible with user intent and project-specific instructions;
5. testable or operationally observable where possible.

Product-specific tool schemas, branding, private URLs, UI-only instructions, model-specific identity language, and mutually contradictory instructions are not copied into the runtime kernel.

## Provenance

Generated builds include:

- a source fingerprint;
- every file path + SHA-256 in `corpus-index.json`;
- aggregate source-family coverage;
- aggregate behavior-family coverage;
- a manifest hashing every emitted runtime artifact.

This lets a researcher reproduce *which corpus snapshot was used* without HCP redistributing the source text.

## Limitations

Captured prompts may be stale, altered, incomplete, mislabeled, or unauthenticated. Aggregate phrase matching is intentionally simple and can produce false positives. HCP treats the corpus as research evidence, not authoritative documentation.

Future research can add opt-in semantic clustering and benchmarked A/B evaluation while keeping raw source text local.
