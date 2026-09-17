"""Tool handlers for the HCP runtime plugin."""
from __future__ import annotations

import json
from typing import Any

from .global_store import GlobalStateStore
from .state_store import ProjectStateStore


def _store(args: dict[str, Any], kwargs: dict[str, Any]) -> ProjectStateStore:
    explicit_root = str(args.get("project_root") or "").strip()
    root = explicit_root or kwargs.get("hcp_project_root")
    store = ProjectStateStore(root)
    try:
        GlobalStateStore().note_project(str(store.project_root))
    except Exception:
        pass
    return store


def _global() -> GlobalStateStore:
    return GlobalStateStore()


def _ok(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def state_read(args: dict, **kwargs) -> str:
    try:
        store = _store(args, kwargs)
        global_store = _global()
        scope = str(args.get("scope") or "summary")
        limit = max(1, min(int(args.get("limit") or 30), 200))
        if scope == "summary":
            value = {
                "project": store.summary(decisions=min(limit, 20), evidence=min(limit, 30)),
                "global": global_store.summary(pending_limit=min(limit, 30)),
            }
        elif scope == "project":
            value = store.read_project()
        elif scope == "task":
            value = store.read_task()
        elif scope == "decisions":
            value = store.decisions(limit)
        elif scope == "evidence":
            value = store.evidence(limit)
        elif scope == "trace":
            value = store.trace_events(limit)
        elif scope == "global":
            value = global_store.read_global()
        elif scope == "instructions":
            value = global_store.instructions()[-limit:]
        else:
            return _ok({"error": f"unknown scope: {scope}"})
        return _ok({"scope": scope, "project_root": str(store.project_root), "value": value})
    except Exception as exc:
        return _ok({"error": f"hcp_state_read failed: {exc}"})


def state_update(args: dict, **kwargs) -> str:
    try:
        scope = str(args.get("scope") or "")
        patch = args.get("patch")
        if not isinstance(patch, dict):
            return _ok({"error": "patch must be an object"})
        if scope in {"project", "task"}:
            value = _store(args, kwargs).update(scope, patch, replace=bool(args.get("replace", False)))
        elif scope == "global":
            value = _global().update_global(patch)
        elif scope == "instruction":
            global_store = _global()
            instruction_id = str(patch.get("instruction_id") or patch.get("id") or "").strip()
            if instruction_id and any(key in patch for key in ("status", "completed_at", "note", "priority")):
                changes = {k: v for k, v in patch.items() if k not in {"instruction_id", "id"}}
                value = global_store.update_instruction(instruction_id, changes)
            else:
                value = global_store.record_instruction(
                    patch,
                    project_root=str(_store(args, kwargs).project_root),
                    session_id=str(kwargs.get("session_id") or ""),
                )
        else:
            return _ok({"error": "scope must be project, task, global, or instruction"})
        return _ok({"ok": True, "scope": scope, "value": value})
    except Exception as exc:
        return _ok({"error": f"hcp_state_update failed: {exc}"})


def decision_record(args: dict, **kwargs) -> str:
    try:
        decision = str(args.get("decision") or "").strip()
        if not decision:
            return _ok({"error": "decision is required"})
        event = _store(args, kwargs).record_decision(
            decision,
            rationale=str(args.get("rationale") or ""),
            alternatives=[str(x) for x in (args.get("alternatives") or [])],
            evidence_refs=[str(x) for x in (args.get("evidence_refs") or [])],
            session_id=str(kwargs.get("session_id") or ""),
            status=str(args.get("status") or "accepted"),
        )
        return _ok({"ok": True, "decision": event})
    except Exception as exc:
        return _ok({"error": f"hcp_decision_record failed: {exc}"})


def evidence_record(args: dict, **kwargs) -> str:
    try:
        subject = str(args.get("subject") or "").strip()
        if not subject:
            return _ok({"error": "subject is required"})
        event = _store(args, kwargs).record_evidence(
            subject,
            result=str(args.get("result") or "unknown"),
            kind=str(args.get("kind") or "verification"),
            source=str(args.get("source") or "manual"),
            details=str(args.get("details") or ""),
            command=str(args.get("command") or ""),
            changed_paths=[str(x) for x in (args.get("changed_paths") or [])],
            session_id=str(kwargs.get("session_id") or ""),
            turn_id=str(kwargs.get("turn_id") or ""),
        )
        return _ok({"ok": True, "evidence": event})
    except Exception as exc:
        return _ok({"error": f"hcp_evidence_record failed: {exc}"})
