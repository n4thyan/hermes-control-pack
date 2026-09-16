# Architecture

HCP is a **model-agnostic harness augmentation layer** for Hermes Agent. It separates research input from runtime output so millions of tokens of source material do not become millions of tokens of live system prompt.

## Layers

### 1. Research corpus

A ZIP or directory of captured system prompts, agent instructions, skills, tool guidance, and other product internals is scanned file-by-file. HCP records hashes, source families, artifact kinds, behavior signals, and explicit transferable mechanism hits.

### 2. Mechanism model

The mechanism database generalizes recurring harness ideas such as inspect-before-edit, task routing, root-cause debugging, verification-gated completion, delegation, context compaction, memory routing, structured handoff, provider adaptation, visual verification, and bounded autonomy.

Each mechanism has an HCP implementation target: system guidance, SOUL, skill, runtime, state, or provider adaptation. This keeps provenance separate from implementation.

### 3. Packaged runtime

HCP wheels contain the compiled runtime artifacts. Normal users do not need the research corpus:

- `hcp-runtime` plugin;
- `hcp-continuity` context engine;
- 12 skills and 5 bundles;
- four SOUL overlays;
- project execution kernel.

### 4. Persistent project state

`.hcp/state` is the task-level continuity database. It is deliberately separate from the conversation transcript and Hermes' global user memory.

### 5. Hermes runtime integration

The plugin uses stable documented seams:

```text
cache-safe system section   -> HCP runtime contract
pre_llm_call                -> dynamic structured continuity
model-callable HCP tools    -> state/decision/evidence updates
post_tool_call              -> observable evidence/mutation ledger
pre_verify                  -> bounded completion gate
API/session observers       -> harness telemetry
```

The optional `hcp-continuity` engine subclasses Hermes' built-in compressor and adds structured state as compaction grounding.

## Prompt/state hierarchy

Conceptually a running session sees:

```text
Hermes native system prompt
  + HCP frozen runtime kernel
  + global SOUL (including HCP managed overlay)
  + project context if present
  + relevant skills/bundles
  + Hermes memory
  + HCP dynamic project/task continuity
  + current conversation working set
```

The dynamic continuity block is not put in the frozen prompt prefix because task state changes during work.

## Why no default Hermes fork

A fork would couple HCP to private implementation details and make every Hermes update a merge problem. Hermes now exposes enough plugin/context-engine surfaces for the important HCP2 behaviors, so core patches are unnecessary for the default architecture.

If a future capability genuinely requires a core patch, HCP's policy is to make it explicit, version/hash-gated, optional, and testable rather than silently modifying Hermes files.

## Evidence vs reasoning

`TRACE.jsonl` is intentionally an **observable event ledger**. It may record a tool call, a verification outcome, a provider error, a gate decision, or a state update. It does not attempt to expose or reconstruct hidden chain-of-thought.
