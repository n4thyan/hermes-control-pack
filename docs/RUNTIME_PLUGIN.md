# HCP runtime plugin

`hcp-runtime` is the deep-integration layer for HCP 2.0. It uses documented Hermes plugin surfaces and does not monkey-patch the agent loop.

## System kernel

The plugin registers a cache-safe system-prompt section named `hcp.runtime-kernel`. Hermes renders that section once for a new session and freezes the resulting bytes across compression/resume, preserving prompt-cache stability.

The kernel establishes the runtime contract: structured continuity, fact/hypothesis/evidence separation, evidence-backed completion, and state repair when durable state becomes stale.

## Dynamic continuity

`pre_llm_call` injects current structured continuity because task state is dynamic and should not mutate the frozen system prefix. This is deliberately separate from the cache-safe kernel.

## Completion gate

Hermes' `pre_verify` hook is a bounded continue/stop gate after code edits. HCP uses it to request missing evidence such as:

- fresh verification after the latest observed mutation;
- a durable active task objective;
- rendered-state verification after UI-affecting changes;
- diff/status review on larger multi-file edits.

Hermes itself caps verification nudges, so a faulty HCP gate cannot loop forever.

The gate is evidence-oriented rather than command-oriented. HCP recognizes common test/build/lint/type-check commands automatically, while unusual checks can be recorded explicitly with `hcp_evidence_record`.

## Observable telemetry

HCP records events such as:

- session/turn boundaries;
- tool outcomes and observed mutations;
- verification/diff/visual checks;
- completion-gate continue/pass events;
- provider request successes/failures;
- persistent state updates.

This is **decision provenance at the harness level**, not chain-of-thought capture. HCP does not request or store hidden model reasoning.

## Safety and reversibility

HCP's runtime layer is installed as a normal Hermes plugin. The recommended setup also selects the optional `hcp-continuity` context engine; switch back at any time with:

```bash
hermes config set context.engine compressor
```

Project state is stored locally under `.hcp/` and can be archived or removed independently of Hermes' own session database.
