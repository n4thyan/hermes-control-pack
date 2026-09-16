from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MechanismSpec:
    name: str
    purpose: str
    terms: tuple[str, ...]
    min_distinct_terms: int = 2
    hcp_target: str = "skill"


MECHANISMS: tuple[MechanismSpec, ...] = (
    MechanismSpec("task_intent_routing", "Distinguish explain/plan/diagnose/implement/review outcomes before acting.",
                  ("plan mode", "diagnose", "implement", "review", "user asked", "requested outcome"), 2, "system+runtime"),
    MechanismSpec("inspect_before_edit", "Ground mutations in repository/code evidence.",
                  ("read before", "before editing", "inspect", "search", "codebase", "relevant files"), 2, "system+skill"),
    MechanismSpec("root_cause_debugging", "Reproduce, trace, hypothesize, patch cause, re-test.",
                  ("root cause", "reproduce", "trace", "diagnose", "failing test", "failure path"), 2, "skill"),
    MechanismSpec("evidence_gated_completion", "Require observed checks before completion claims.",
                  ("verify", "verification", "before finishing", "before declaring", "tests pass", "evidence"), 2, "runtime+system"),
    MechanismSpec("independent_review", "Challenge completed work with a separate review pass.",
                  ("review", "reviewer", "self-review", "critique", "check your work", "regression"), 2, "skill+subagent"),
    MechanismSpec("parallel_delegation", "Fan out independent work with bounded subagent contracts.",
                  ("subagent", "delegate", "parallel", "spawn", "independent", "workstream"), 2, "skill+runtime"),
    MechanismSpec("context_compaction", "Keep long-running work viable by reducing transcript pressure.",
                  ("compress", "compression", "compaction", "context window", "summarize", "token"), 2, "context-engine"),
    MechanismSpec("persistent_memory_routing", "Route durable facts/procedures to the right persistence layer.",
                  ("persistent memory", "memory", "skills", "across sessions", "user profile", "durable"), 2, "runtime+memory"),
    MechanismSpec("structured_handoff", "Preserve goal/current-state/failures/next actions across boundaries.",
                  ("handoff", "next steps", "current state", "resume", "summary", "context"), 2, "runtime+skill"),
    MechanismSpec("visual_verification", "Treat rendered UI state as evidence for visual work.",
                  ("screenshot", "visual", "browser", "render", "ui", "viewport"), 2, "runtime+skill"),
    MechanismSpec("git_change_safety", "Protect user changes and review final repository deltas.",
                  ("git diff", "git status", "working tree", "worktree", "uncommitted", "revert"), 2, "system+skill"),
    MechanismSpec("failure_recovery", "Change strategy after failures instead of looping or stopping prematurely.",
                  ("retry", "fallback", "recover", "failure", "try another", "error handling"), 2, "runtime+system"),
    MechanismSpec("interruption_resume", "Preserve coherent state across user steering and interrupted turns.",
                  ("interrupt", "resume", "steer", "correction", "cancel", "continue"), 2, "runtime"),
    MechanismSpec("prompt_cache_stability", "Keep stable prompt bytes separate from per-turn context.",
                  ("prompt cache", "cache", "stable", "system prompt", "prefix", "ephemeral"), 2, "runtime"),
    MechanismSpec("provider_adaptation", "Adapt request/prompt behavior to provider/model contracts without identity copying.",
                  ("provider", "model", "anthropic", "openai", "gemini", "api mode"), 2, "runtime"),
    MechanismSpec("source_grounding", "Ground research claims in current/primary sources and provenance.",
                  ("source", "citation", "primary source", "documentation", "search", "current"), 2, "skill"),
    MechanismSpec("bounded_autonomy", "Continue independently while respecting scope and consequential-action boundaries.",
                  ("autonomous", "do not ask", "continue", "without asking", "approval", "destructive"), 2, "system+skill"),
    MechanismSpec("tool_evidence_reuse", "Reuse tool results and avoid redundant rediscovery.",
                  ("tool result", "reuse", "already", "do not repeat", "search results", "cache"), 2, "system"),
    MechanismSpec("state_machine_execution", "Maintain explicit task phase/state across long tool loops.",
                  ("state", "phase", "lifecycle", "plan", "execute", "verify"), 3, "runtime"),
)


def mechanism_hits(text: str) -> dict[str, int]:
    lower = text.lower()
    result: dict[str, int] = {}
    for spec in MECHANISMS:
        counts = [(term, lower.count(term)) for term in spec.terms]
        distinct = sum(1 for _, count in counts if count)
        if distinct >= spec.min_distinct_terms:
            result[spec.name] = sum(count for _, count in counts)
    return result


def mechanism_specs() -> dict[str, MechanismSpec]:
    return {m.name: m for m in MECHANISMS}
