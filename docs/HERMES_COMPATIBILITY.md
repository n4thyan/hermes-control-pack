# Hermes compatibility

HCP 2.1 is designed around documented Hermes extension contracts rather than source patches.

## APIs used

`hcp-runtime` uses:

- `ctx.register_system_prompt_section()` for a frozen/cache-safe system kernel;
- `ctx.register_tool()` for HCP state/decision/evidence tools;
- `ctx.register_hook("pre_llm_call", ...)` for dynamic continuity injection;
- `post_tool_call`, `post_api_request`, `api_request_error`, and session hooks for observable telemetry;
- `pre_verify` for the bounded completion-evidence gate;
- `transform_llm_output` for deterministic exact-response enforcement;
- `ctx.register_command()` for `/hcp-status`.

The optional continuity engine subclasses `agent.context_compressor.ContextCompressor` and exposes the standard context-engine `name`/`compress` contract. HCP passes structured state via `memory_context` and otherwise delegates compression to Hermes.

## Upgrade policy

HCP prefers a compatibility failure over silently patching Hermes internals. `hcp doctor` checks installed runtime assets, and CI exercises the HCP package independently on supported Python versions.

If a future Hermes release changes an extension signature, HCP should adapt its plugin/engine layer. Core Hermes patches are a last resort and, if ever required, should be version/hash-gated and explicitly documented.

## Context-engine activation

Hermes intentionally does not auto-activate third-party context engines. `hcp setup` is an explicit user-invoked installer, so its recommended flow installs and selects `hcp-continuity`. Users can opt out with `--no-context-engine` or revert with:

```bash
hermes config set context.engine compressor
```
