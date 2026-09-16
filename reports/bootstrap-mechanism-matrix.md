# Agent Mechanism Matrix

HCP treats the supplied corpus as an **agent-architecture dataset**. This matrix records where transferable mechanisms are observed across independent top-level source families. It contains metadata and authored generalizations, not copied prompt passages.

| Mechanism | Source groups | Files | HCP implementation target | Example supporting groups |
|---|---:|---:|---|---|
| `source_grounding` | 16 | 306 | `skill` | Anthropic, Cursor, DeepSeek, Google, Kimi, Meta, Microsoft, Misc, … |
| `visual_verification` | 13 | 251 | `runtime+skill` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `structured_handoff` | 13 | 185 | `runtime+skill` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `state_machine_execution` | 13 | 176 | `runtime` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `tool_evidence_reuse` | 13 | 144 | `system` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `task_intent_routing` | 12 | 133 | `system+runtime` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `evidence_gated_completion` | 12 | 110 | `runtime+system` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, Mistral, … |
| `inspect_before_edit` | 11 | 132 | `system+skill` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, OpenAI, … |
| `context_compaction` | 11 | 130 | `context-engine` | Anthropic, Google, Kimi, Meta, Microsoft, Misc, Mistral, Notion, … |
| `interruption_resume` | 11 | 130 | `runtime` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, OpenAI, … |
| `parallel_delegation` | 11 | 91 | `skill+runtime` | Anthropic, Cursor, Google, Kimi, Meta, Microsoft, Misc, OpenAI, … |
| `bounded_autonomy` | 10 | 129 | `system+skill` | Anthropic, Cursor, Google, Meta, Microsoft, Misc, OpenAI, OpenCode, … |
| `prompt_cache_stability` | 10 | 98 | `runtime` | Anthropic, Kimi, Meta, Microsoft, Misc, Notion, OpenAI, OpenCode, … |
| `persistent_memory_routing` | 9 | 89 | `runtime+memory` | Anthropic, Google, Kimi, Meta, Microsoft, Misc, OpenAI, Perplexity, … |
| `git_change_safety` | 9 | 53 | `system+skill` | Anthropic, Cursor, Google, Kimi, Meta, Misc, OpenAI, OpenCode, … |
| `provider_adaptation` | 8 | 208 | `runtime` | Anthropic, Google, Meta, Misc, OpenAI, Perplexity, Pi, xAI |
| `failure_recovery` | 8 | 112 | `runtime+system` | Anthropic, Google, Meta, Microsoft, Misc, OpenAI, Perplexity, xAI |
| `independent_review` | 8 | 84 | `skill+subagent` | Anthropic, Google, Meta, Microsoft, Misc, OpenAI, Perplexity, xAI |
| `root_cause_debugging` | 8 | 55 | `skill` | Anthropic, Google, Kimi, Meta, Microsoft, Misc, OpenAI, xAI |

## Interpretation

A mechanism's presence does not prove that it is optimal. HCP implements mechanisms as hypotheses and validates them with Hermes benchmarks. `source_groups` is breadth evidence, not a vendor score.
