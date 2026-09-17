from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import threading

from .global_store import GlobalStateStore, looks_cross_session_instruction
from .intent_capture import capture_explicit_future_response
from .core import _root_for

logger = logging.getLogger(__name__)
_LOCK = threading.RLock()
_ACTIVE_BY_SESSION: dict[str, list[str]] = {}


def _equivalent_pending(store: GlobalStateStore, payload: dict[str, Any]) -> dict[str, Any] | None:
    action = str(payload.get("action") or "").casefold().strip()
    patterns = [str(x).casefold().strip() for x in payload.get("trigger_patterns", [])]
    for item in store.instructions(statuses={"pending", "triggered"}):
        if str(item.get("action") or "").casefold().strip() != action:
            continue
        existing = [str(x).casefold().strip() for x in item.get("trigger_patterns", [])]
        if existing == patterns and str(item.get("trigger_type") or "") == str(payload.get("trigger_type") or ""):
            return item
    return None


def _explicit_supersession(user_message: str) -> bool:
    """Return True when the current turn plainly asks not to follow prior intent.

    New direct user intent outranks HCP persistence. This conservative guard keeps
    an old trigger from forcing output while the user is cancelling or correcting it.
    """
    text = " ".join(str(user_message or "").casefold().split())
    return any(phrase in text for phrase in (
        "ignore that instruction",
        "ignore the previous instruction",
        "ignore my previous instruction",
        "cancel that instruction",
        "cancel the previous instruction",
        "forget that instruction",
        "don't do that",
        "do not do that",
        "don't follow that",
        "do not follow that",
        "instead of the previous instruction",
    ))


def _pre_llm_call(session_id: str, **kwargs):
    """Always inject cwd-independent continuity before the model sees the turn."""
    try:
        user_message = str(kwargs.get("user_message") or "")
        turn_id = str(kwargs.get("turn_id") or "")
        store = GlobalStateStore()
        store.ensure()

        # Detect a new explicit future-response instruction before matching existing
        # triggers, so mentioning the trigger while defining it cannot fire it now.
        captured = capture_explicit_future_response(user_message)
        supersedes = _explicit_supersession(user_message)
        match_message = "" if (captured or supersedes) else user_message
        project_root = str(_root_for(session_id))
        context, active_ids = store.render_context(
            match_message,
            session_id=session_id,
            project_root=project_root,
            max_chars=3000,
        )

        capture_note = ""
        if captured:
            existing = _equivalent_pending(store, captured)
            if existing is None:
                item = store.record_instruction(captured, session_id=session_id)
                capture_note = (
                    "\n[HCP AUTO-PERSISTED FUTURE INSTRUCTION]\n"
                    f"HCP stored this explicit cross-session instruction as id={item.get('id')}. "
                    "Do not claim that it is only in transcript memory."
                )
            else:
                capture_note = (
                    "\n[HCP FUTURE INSTRUCTION ALREADY PERSISTED]\n"
                    f"Equivalent pending instruction id={existing.get('id')} already exists."
                )
        elif supersedes:
            capture_note = (
                "\n[HCP CURRENT USER OVERRIDE]\n"
                "The current turn explicitly cancels or supersedes prior intent. Do not activate a persisted trigger from "
                "this message. If a stored instruction is being cancelled or replaced, update its structured HCP status "
                "rather than leaving stale intent active."
            )
        elif looks_cross_session_instruction(user_message):
            capture_note = (
                "\n[HCP PERSISTENCE REQUIRED]\n"
                "This user turn appears to contain future/cross-session intent that the narrow automatic parser did not "
                "fully structure. Before finishing, use hcp_state_update with scope=instruction to preserve the user's exact "
                "intent. Do not rely on transcript/session search alone."
            )

        with _LOCK:
            _ACTIVE_BY_SESSION[session_id] = list(active_ids)
        store.trace("ambient_pre_turn", {
            "session_id": session_id,
            "turn_id": turn_id,
            "is_first_turn": bool(kwargs.get("is_first_turn", False)),
            "active_instruction_ids": active_ids,
            "auto_captured": bool(captured),
            "current_user_override": supersedes,
        })
        return {"context": context + capture_note}
    except Exception as exc:
        logger.warning("HCP global continuity injection failed: %s", exc)
        return None


def _transform_llm_output(response_text: str, session_id: str, **kwargs):
    """Deterministically execute explicit respond_exact instructions that matched this turn."""
    try:
        with _LOCK:
            active_ids = list(_ACTIVE_BY_SESSION.get(session_id, []))
        if not active_ids:
            return None
        store = GlobalStateStore()
        by_id = {str(x.get("id")): x for x in store.instructions()}
        priority = {"blocking": 3, "important": 2, "normal": 1}
        candidates = [
            by_id[i] for i in active_ids
            if i in by_id and str(by_id[i].get("action_type") or "") == "respond_exact"
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: priority.get(str(item.get("priority") or "normal"), 1), reverse=True)
        action = str(candidates[0].get("action") or "")
        if not action:
            return None
        store.trace("exact_response_enforced", {
            "session_id": session_id,
            "instruction_id": candidates[0].get("id"),
        })
        return action
    except Exception as exc:
        logger.debug("HCP exact-response transform failed: %s", exc)
        return None


def _post_llm_call(session_id: str, **kwargs) -> None:
    try:
        assistant_response = str(kwargs.get("assistant_response") or "")
        with _LOCK:
            active_ids = list(_ACTIVE_BY_SESSION.pop(session_id, []))
        if not active_ids:
            return
        store = GlobalStateStore()
        for instruction_id in active_ids:
            store.settle_after_response(instruction_id, assistant_response)
        store.trace("ambient_post_turn", {
            "session_id": session_id,
            "turn_id": str(kwargs.get("turn_id") or ""),
            "settled_instruction_ids": active_ids,
        })
    except Exception as exc:
        logger.debug("HCP global post-turn settlement failed: %s", exc)


def _on_session_start(session_id: str, **kwargs) -> None:
    try:
        store = GlobalStateStore()
        store.ensure()
        store.trace("global_session_start", {
            "session_id": session_id,
            "platform": str(kwargs.get("platform") or ""),
            "model": str(kwargs.get("model") or ""),
        })
    except Exception as exc:
        logger.debug("HCP global session bootstrap failed: %s", exc)


def _on_session_finalize(session_id: str | None = None, **kwargs) -> None:
    if not session_id:
        return
    with _LOCK:
        _ACTIVE_BY_SESSION.pop(session_id, None)


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("transform_llm_output", _transform_llm_output)
    ctx.register_hook("post_llm_call", _post_llm_call)
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_finalize", _on_session_finalize)
