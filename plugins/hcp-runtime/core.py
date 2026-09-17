"""Hermes Control Pack runtime plugin core.

This is the HCP 2.0 runtime kernel kept intact so HCP 2.1 can layer cwd-independent
ambient continuity hooks around it without regressing the existing verification,
telemetry, project-state, or tool behavior.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import logging
import os
import re
import threading

from . import schemas, tools
from .state_store import ProjectStateStore, find_project_root, utc_now

logger = logging.getLogger(__name__)
_SESSION_CWD: dict[str, str] = {}
_SESSION_RUNTIME: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()

_VERIFY_RE = re.compile(
    r"(?:^|[;&| ](?:python\s+-m\s+)?)"
    r"(?:pytest|unittest|tox|nox|npm\s+(?:test|run\s+(?:test|build|lint|typecheck))|"
    r"pnpm\s+(?:test|build|lint|typecheck)|yarn\s+(?:test|build|lint|typecheck)|"
    r"bun\s+(?:test|run\s+(?:test|build|lint))|ruff|mypy|pyright|eslint|tsc|"
    r"cargo\s+(?:test|check|clippy|build)|go\s+test|dotnet\s+(?:test|build)|"
    r"mvn\s+(?:test|verify|package)|gradle\s+(?:test|build)|make\s+(?:test|check|build))\b",
    re.IGNORECASE,
)
_DIFF_RE = re.compile(r"\bgit\s+(?:diff|status)(?:\s|$)", re.IGNORECASE)
_TERMINAL_MUTATION_RE = re.compile(
    r"(?:^|[;&|]\s*)(?:"
    r"sed\s+-[^;&|]*i\b|perl\s+-[^;&|]*pi\b|"
    r"(?:cat|echo|printf)\b[^;&|]*(?:>>|>)|tee\b|"
    r"(?:cp|mv|rm|touch)\b|git\s+(?:apply|restore|checkout\s+--|clean\b)"
    r")",
    re.IGNORECASE,
)
_MUTATING_TOOLS = {
    "write_file", "patch", "file_edit", "edit_file", "apply_patch", "create_file",
    "filesystem_write", "replace_file", "str_replace_editor",
}
_VISUAL_TOOL_HINTS = ("browser", "screenshot", "vision", "playwright", "chromium", "render")
_UI_EXTENSIONS = (".tsx", ".jsx", ".css", ".scss", ".sass", ".less", ".html", ".vue", ".svelte")


def _session_map_path() -> Path:
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:
        home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
    return home / "hcp" / "session-roots.json"


def _load_session_root(session_id: str) -> str | None:
    path = _session_map_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        item = payload.get(session_id) if isinstance(payload, dict) else None
        root = item.get("root") if isinstance(item, dict) else None
        return str(root) if root else None
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _remember_session_root(session_id: str, root: str) -> None:
    if not session_id or not root:
        return
    path = _session_map_path()
    with _LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raw = json.loads(path.read_text(encoding="utf-8"))
                payload = raw if isinstance(raw, dict) else {}
            else:
                payload = {}
        except (OSError, json.JSONDecodeError):
            payload = {}
        payload[session_id] = {"root": str(root), "updated_at": utc_now()}
        if len(payload) > 500:
            ordered = sorted(
                payload.items(),
                key=lambda kv: str(kv[1].get("updated_at", "")) if isinstance(kv[1], dict) else "",
                reverse=True,
            )[:500]
            payload = dict(ordered)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(tmp, path)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass


def _root_for(session_id: str | None = None) -> Path:
    if session_id:
        with _LOCK:
            known = _SESSION_CWD.get(session_id)
        if not known:
            known = _load_session_root(session_id)
            if known:
                with _LOCK:
                    _SESSION_CWD[session_id] = known
        if known:
            return find_project_root(known)
    return find_project_root()


def _store(session_id: str | None = None) -> ProjectStateStore:
    return ProjectStateStore(_root_for(session_id))


def _runtime(session_id: str | None) -> dict[str, Any]:
    key = session_id or "unknown"
    with _LOCK:
        return _SESSION_RUNTIME.setdefault(key, {
            "mutation_seq": 0,
            "verification_seq": -1,
            "diff_review_seq": -1,
            "visual_seq": -1,
            "tool_calls": 0,
        })


def _redact_command(command: str) -> str:
    text = re.sub(r"(?i)(api[_-]?key|token|password|secret)(\s*[=:]\s*)[^\s]+", r"\1\2[REDACTED]", command)
    text = re.sub(r"(?i)(authorization:\s*(?:bearer\s+)?)\S+", r"\1[REDACTED]", text)
    return text[:800]


def _system_section(session_info: dict[str, str]) -> str:
    session_id = str(session_info.get("session_id") or "")
    cwd = str(session_info.get("cwd") or "")
    if session_id and cwd:
        root = str(find_project_root(cwd))
        with _LOCK:
            _SESSION_CWD[session_id] = root
        _remember_session_root(session_id, root)
    model = str(session_info.get("model") or "unknown")
    provider = str(session_info.get("provider") or "unknown")
    return f"""# Hermes Control Pack runtime kernel
HCP augments this Hermes session with structured continuity and evidence-based completion. Base provider/model: {provider}/{model}. Do not imitate another vendor's identity; transfer useful agent mechanisms only.

Maintain four durable objects outside the transcript: PROJECT_STATE, TASK_STATE, DECISION_LOG, and EVIDENCE_LEDGER. Use `hcp_state_read` when resuming or when compressed context leaves uncertainty. Use `hcp_state_update` when the objective, acceptance criteria, phase, architecture facts, changed paths, blockers, or next actions materially change. Record material decisions with `hcp_decision_record`; store concise externally defensible rationale, never private chain-of-thought. Record checks that actually establish a claim with `hcp_evidence_record` when HCP cannot observe them automatically.

Keep facts, hypotheses, decisions, and evidence distinct. Compression may summarize conversation prose; durable HCP state is the continuity authority for active work and is re-injected each user turn. If durable state conflicts with newer direct user instructions or verified repository/runtime evidence, update the state rather than following stale data.

For code changes, completion requires evidence after the relevant edits. Prefer targeted verification, then broader checks appropriate to risk. UI-affecting changes require rendered-state evidence when browser/vision tooling is available. Multi-file work should include final diff review. The bounded HCP `pre_verify` gate may continue the turn when required evidence is missing; satisfy the missing check rather than merely rephrasing the answer.

HCP decision trace records observable harness events (tools, checks, provider usage, state transitions, gates). It is not a chain-of-thought log and must never be used to fabricate hidden reasoning."""


def _pre_llm_call(session_id: str, **kwargs):
    try:
        store = _store(session_id)
        store.ensure()
        store.trace("turn_start", {
            "session_id": session_id,
            "turn_id": str(kwargs.get("turn_id") or ""),
            "model": str(kwargs.get("model") or ""),
            "platform": str(kwargs.get("platform") or ""),
            "is_first_turn": bool(kwargs.get("is_first_turn", False)),
        })
        return {"context": store.render_context(max_chars=6500)}
    except Exception as exc:
        logger.warning("HCP continuity injection failed: %s", exc)
        return None


def _post_tool_call(tool_name: str, args: dict, result: str, **kwargs) -> None:
    session_id = str(kwargs.get("session_id") or kwargs.get("task_id") or "")
    turn_id = str(kwargs.get("turn_id") or "")
    status = str(kwargs.get("status") or "")
    rt = _runtime(session_id)
    rt["tool_calls"] += 1
    store = _store(session_id)
    low_name = (tool_name or "").lower()
    command = str((args or {}).get("command") or "")
    success = status in {"", "success", "ok"} and not str(result).lstrip().lower().startswith(("error", "failed"))

    mutation_observed = low_name in _MUTATING_TOOLS or (low_name == "terminal" and bool(_TERMINAL_MUTATION_RE.search(command)))
    if mutation_observed:
        rt["mutation_seq"] += 1
        store.trace("mutation_tool", {
            "tool": tool_name, "command": _redact_command(command) if command else "",
            "session_id": session_id, "turn_id": turn_id,
        })

    if low_name == "terminal" and _VERIFY_RE.search(command):
        if success:
            rt["verification_seq"] = rt["mutation_seq"]
        store.record_evidence(
            f"Verification command: {_redact_command(command)}",
            result="pass" if success else "fail",
            kind="command-verification",
            source="post_tool_call",
            command=_redact_command(command),
            session_id=session_id,
            turn_id=turn_id,
        )
    elif low_name == "terminal" and _DIFF_RE.search(command):
        if success:
            rt["diff_review_seq"] = rt["mutation_seq"]
        store.record_evidence(
            f"Change review command: {_redact_command(command)}",
            result="observed" if success else "fail",
            kind="diff-review",
            source="post_tool_call",
            command=_redact_command(command),
            session_id=session_id,
            turn_id=turn_id,
        )
    elif any(hint in low_name for hint in _VISUAL_TOOL_HINTS):
        if success:
            rt["visual_seq"] = rt["mutation_seq"]
        store.record_evidence(
            f"Rendered/visual check via {tool_name}",
            result="observed" if success else "fail",
            kind="visual",
            source="post_tool_call",
            session_id=session_id,
            turn_id=turn_id,
        )
    elif low_name == "hcp_evidence_record" and success:
        evidence_result = str((args or {}).get("result") or "")
        if evidence_result in {"pass", "observed"}:
            rt["verification_seq"] = rt["mutation_seq"]
            if str((args or {}).get("kind") or "").lower() in {"diff", "diff-review", "review"}:
                rt["diff_review_seq"] = rt["mutation_seq"]
            if str((args or {}).get("kind") or "").lower() in {"visual", "browser", "screenshot", "ui"}:
                rt["visual_seq"] = rt["mutation_seq"]

    store.trace("tool_result", {
        "tool": tool_name,
        "status": status or ("success" if success else "unknown"),
        "duration_ms": kwargs.get("duration_ms"),
        "session_id": session_id,
        "turn_id": turn_id,
    })


def _pre_verify(session_id: str, coding: bool, attempt: int, changed_paths: list, **kwargs):
    if not coding or not changed_paths or attempt >= 2:
        return None
    store = _store(session_id)
    task = store.read_task()
    normalized_paths = list(dict.fromkeys(str(path) for path in changed_paths if str(path)))
    prior_paths = [str(path) for path in task.get("changed_paths", []) if str(path)]
    merged_paths = list(dict.fromkeys([*prior_paths, *normalized_paths]))
    if merged_paths != prior_paths:
        store.update("task", {"changed_paths": merged_paths})
    rt = _runtime(session_id)
    missing: list[str] = []
    if not str(task.get("objective") or "").strip():
        missing.append("a durable TASK_STATE objective for session continuity")
    if rt["verification_seq"] < rt["mutation_seq"]:
        missing.append("fresh verification evidence after the latest edit")
    ui_change = any(str(path).lower().endswith(_UI_EXTENSIONS) for path in changed_paths)
    if ui_change and rt["visual_seq"] < rt["mutation_seq"]:
        missing.append("rendered-state/UI verification")
    if len(changed_paths) >= 4 and rt["diff_review_seq"] < rt["mutation_seq"]:
        missing.append("a final git diff/status review for the multi-file change")
    if not missing:
        store.trace("completion_gate_pass", {
            "session_id": session_id, "attempt": attempt, "changed_paths": normalized_paths
        })
        return None
    message = (
        "HCP completion gate: before finishing, gather " + ", ".join(missing) + ". "
        "Use the project's real checks; for nonstandard evidence record what you actually observed with "
        "hcp_evidence_record. Then update TASK_STATE if the phase/next steps changed."
    )
    store.trace("completion_gate_continue", {
        "session_id": session_id, "attempt": attempt, "missing": missing,
        "changed_paths": normalized_paths,
    })
    return {"action": "continue", "message": message}


def _post_api_request(**kwargs) -> None:
    session_id = str(kwargs.get("session_id") or "")
    usage = kwargs.get("usage") if isinstance(kwargs.get("usage"), dict) else {}
    _store(session_id).trace("api_response", {
        "session_id": session_id,
        "turn_id": str(kwargs.get("turn_id") or ""),
        "api_request_id": str(kwargs.get("api_request_id") or ""),
        "provider": str(kwargs.get("provider") or ""),
        "model": str(kwargs.get("model") or ""),
        "finish_reason": str(kwargs.get("finish_reason") or ""),
        "api_call_count": kwargs.get("api_call_count"),
        "message_count": kwargs.get("message_count"),
        "usage": {k: v for k, v in usage.items() if isinstance(v, (int, float))},
    })


def _api_request_error(**kwargs) -> None:
    session_id = str(kwargs.get("session_id") or "")
    error = kwargs.get("error") if isinstance(kwargs.get("error"), dict) else {}
    _store(session_id).trace("api_error", {
        "session_id": session_id,
        "turn_id": str(kwargs.get("turn_id") or ""),
        "provider": str(kwargs.get("provider") or ""),
        "model": str(kwargs.get("model") or ""),
        "status_code": kwargs.get("status_code"),
        "retry_count": kwargs.get("retry_count"),
        "retryable": kwargs.get("retryable"),
        "reason": str(kwargs.get("reason") or ""),
        "error_type": str(error.get("type") or ""),
    })


def _post_llm_call(session_id: str, **kwargs) -> None:
    try:
        patch = {
            "last_session_id": session_id,
            "last_model": str(kwargs.get("model") or ""),
        }
        _store(session_id).update("task", patch)
        _store(session_id).trace("turn_complete", {
            "session_id": session_id,
            "turn_id": str(kwargs.get("turn_id") or ""),
            "model": str(kwargs.get("model") or ""),
        })
    except Exception as exc:
        logger.debug("HCP post-turn checkpoint failed: %s", exc)


def _on_session_start(session_id: str, model: str = "", platform: str = "", **kwargs) -> None:
    store = _store(session_id)
    store.ensure()
    store.trace("session_start", {"session_id": session_id, "model": model, "platform": platform, "at": utc_now()})


def _on_session_end(session_id: str, **kwargs) -> None:
    _store(session_id).trace("session_turn_end", {
        "session_id": session_id,
        "completed": kwargs.get("completed"),
        "failed": kwargs.get("failed"),
        "interrupted": kwargs.get("interrupted"),
        "turn_exit_reason": kwargs.get("turn_exit_reason"),
    })


def _on_session_finalize(session_id: str | None = None, **kwargs) -> None:
    if not session_id:
        return
    _store(session_id).trace("session_finalize", {
        "session_id": session_id,
        "platform": str(kwargs.get("platform") or ""),
        "reason": str(kwargs.get("reason") or ""),
    })
    with _LOCK:
        _SESSION_CWD.pop(session_id, None)
        _SESSION_RUNTIME.pop(session_id, None)


def _wrap_tool(handler: Callable) -> Callable:
    def wrapped(args: dict, **kwargs):
        session_id = str(kwargs.get("session_id") or kwargs.get("task_id") or "")
        kwargs["hcp_project_root"] = str(_root_for(session_id))
        return handler(args, **kwargs)
    wrapped.__name__ = getattr(handler, "__name__", "hcp_tool")
    return wrapped


def _status_command(raw_args: str = "") -> str:
    store = _store(None)
    summary = store.summary(decisions=3, evidence=4)
    task = summary["task"]
    return (
        f"HCP project: {summary['project_root']}\n"
        f"Objective: {task.get('objective') or '(not set)'}\n"
        f"Phase: {task.get('phase') or '(not set)'}\n"
        f"Next: {json.dumps(task.get('next_steps') or [], ensure_ascii=False)}\n"
        f"Evidence entries: {len(store.evidence(200))}; decisions: {len(store.decisions(200))}"
    )


def register(ctx) -> None:
    for name, schema, handler in (
        ("hcp_state_read", schemas.STATE_READ, tools.state_read),
        ("hcp_state_update", schemas.STATE_UPDATE, tools.state_update),
        ("hcp_decision_record", schemas.DECISION_RECORD, tools.decision_record),
        ("hcp_evidence_record", schemas.EVIDENCE_RECORD, tools.evidence_record),
    ):
        ctx.register_tool(name=name, toolset="hcp", schema=schema, handler=_wrap_tool(handler))

    ctx.register_system_prompt_section(
        "hcp.runtime-kernel", _system_section, position="after_memory", max_chars=4000
    )
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_tool_call", _post_tool_call)
    ctx.register_hook("pre_verify", _pre_verify)
    ctx.register_hook("post_api_request", _post_api_request)
    ctx.register_hook("api_request_error", _api_request_error)
    ctx.register_hook("post_llm_call", _post_llm_call)
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_hook("on_session_finalize", _on_session_finalize)
    ctx.register_command("hcp-status", _status_command, description="Show HCP persistent task/verification state")
