"""Tool handlers for the HCP runtime plugin."""
from __future__ import annotations

import json
from typing import Any

from .state_store import ProjectStateStore


def _store(kwargs: dict[str, Any]) -> ProjectStateStore:
    root = kwargs.get("hcp_project_root")
    return ProjectStateStore(root)


def _ok(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def state_read(args: dict, **kwargs) -> str:
    try:
        store = _store(kwargs)
        scope = str(args.get("scope") or "summary")
        limit = max(1, min(int(args.get("limit") or 30), 200))
        if scope == "summary":
            value = store.summary(decisions=min(limit, 20), evidence=min(limit, 30))
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
        value = _store(kwargs).update(scope, patch, replace=bool(args.get("replace", False)))
        return _ok({"ok": True, "scope": scope, "value": value})
    except Exception as exc:
        return _ok({"error": f"hcp_state_update failed: {exc}"})


def decision_record(args: dict, **kwargs) -> str:
    try:
        decision = str(args.get("decision") or "").strip()
        if not decision:
            return _ok({"error": "decision is required"})
        event = _store(kwargs).record_decision(
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
        event = _store(kwargs).record_evidence(
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
