"""HCP Evidence Reuse Orchestrator.

Conservative, production-safe evidence reuse:

- After every successful tool call, the post_tool_call hook stores the result
  in the EvidenceCache (project-aware, TTL-based).
- Before every LLM call, the pre_llm_call hook injects a short "PRIOR
  EVIDENCE" context block containing recent read-only results that are
  still fresh (within TTL). The model sees this and naturally avoids
  redundant tool calls.
- Mutating-tool results are NEVER injected — only reads and searches.
- Continuity state and the HCP kernel section already use pre_llm_call.
  This module extends that section with evidence reuse.

This is the safest form of "tool_evidence_reuse" because:
1. We don't skip or modify tool execution — we only inject context.
2. The model still has full agency to run whatever it wants.
3. Cached evidence is clearly labeled as such, never as live results.
4. TTLs and project isolation are respected.
5. We never present stale mutation evidence as if it were current.
"""
from __future__ import annotations

from typing import Any


# Tools whose results are safe to inject as context
# (pure reads / searches, no side effects, idempotent)
_SAFE_FOR_INJECTION = frozenset({
    "read_file",
    "search_files",
    "web_search",
    "web_extract",
    "hcp_state_read",
})


def _is_safe_for_injection(tool_name: str) -> bool:
    """Return True if this tool's result can be safely reused as context."""
    name = (tool_name or "").lower()
    return name in _SAFE_FOR_INJECTION


def get_recent_readonly_evidence(
    project_root: str,
    max_items: int = 5,
    max_chars_per_item: int = 400,
) -> list[dict[str, Any]]:
    """Get recent read-only evidence entries that are still fresh (within TTL).

    Returns a list of dicts with keys: tool_name, args, result, timestamp.
    Mutating-tool results are never returned.
    """
    try:
        from hermes_control_pack.evidence_cache import get_cache
        cache = get_cache(project_root)
    except Exception:
        return []

    try:
        entries = cache.summary(limit=max_items * 3)
    except Exception:
        return []

    results = []
    for entry in entries:
        tool = entry.get("tool_name", "")
        if not _is_safe_for_injection(tool):
            continue
        # Re-verify freshness (cache.summary may return slightly stale entries)
        try:
            cached = cache.lookup(tool, entry.get("args", {}))
            if cached is None:
                continue  # stale
        except Exception:
            continue
        result_str = str(entry.get("result", ""))
        if len(result_str) > max_chars_per_item:
            result_str = result_str[:max_chars_per_item] + "...[truncated]"
        results.append({
            "tool_name": tool,
            "args": entry.get("args", {}),
            "result": result_str,
            "timestamp": entry.get("timestamp", ""),
        })
        if len(results) >= max_items:
            break
    return results


def build_evidence_context_block(project_root: str, max_items: int = 5) -> str:
    """Build a context block of recent read-only evidence, or empty string."""
    entries = get_recent_readonly_evidence(project_root, max_items=max_items)
    if not entries:
        return ""
    lines = ["## PRIOR EVIDENCE (cached read results — DO NOT REPEAT)"]
    for i, entry in enumerate(entries, 1):
        tool = entry["tool_name"]
        args = entry["args"]
        result = entry["result"]
        lines.append(f"### [{i}] {tool}({args})")
        lines.append(result)
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    block = build_evidence_context_block(project)
    if block:
        print(block)
    else:
        print("(no cached evidence)")
