from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import hashlib
import json
import os
import re
import threading
import time

GLOBAL_SCHEMA_VERSION = 1
_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home
        return Path(get_hermes_home()).expanduser()
    except Exception:
        return Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes")).expanduser()


def _json_clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = _json_clone(value)
    return out


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        text = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _normalize_message(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def looks_cross_session_instruction(user_message: str) -> bool:
    """Conservative hint for instructions that should survive the current turn/session.

    This does not parse or execute the instruction. It only lets the runtime require the
    model to persist explicit future intent through the structured instruction state.
    """
    text = _normalize_message(user_message)
    if not text:
        return False
    hints = (
        "when i say ", "when i ask ", "next time i ", "next session", "tomorrow when ",
        "after i restart", "after restart", "when hermes restarts", "when i reopen",
        "when i launch hermes", "when i start hermes", "remember to respond", "remember to reply",
    )
    return any(hint in text for hint in hints)


@contextmanager
def _file_lock(path: Path, timeout: float = 3.0) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(timeout, 0.1)
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"pid={os.getpid()} at={utc_now()}\n".encode())
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > 30:
                    path.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for HCP global-state lock: {path}")
            time.sleep(0.025)
    try:
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            path.unlink(missing_ok=True)


class GlobalStateStore:
    """CWD-independent continuity shared by every Hermes launch for one profile/home."""

    def __init__(self, home: Path | str | None = None):
        base = Path(home).expanduser() if home else _hermes_home()
        self.root = base / "hcp" / "global"
        self.global_file = self.root / "GLOBAL_STATE.json"
        self.instructions_file = self.root / "PENDING_INSTRUCTIONS.json"
        self.trace_file = self.root / "GLOBAL_TRACE.jsonl"
        self.lock_file = self.root / ".write.lock"

    @staticmethod
    def _global_defaults() -> dict[str, Any]:
        return {
            "schema_version": GLOBAL_SCHEMA_VERSION,
            "durable_user_constraints": [],
            "session_handoffs": [],
            "recent_projects": [],
            "updated_at": utc_now(),
        }

    @staticmethod
    def _instruction_defaults() -> dict[str, Any]:
        return {"schema_version": GLOBAL_SCHEMA_VERSION, "instructions": [], "updated_at": utc_now()}

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with _file_lock(self.lock_file):
            if not self.global_file.exists():
                self._atomic_json(self.global_file, self._global_defaults())
            if not self.instructions_file.exists():
                self._atomic_json(self.instructions_file, self._instruction_defaults())

    def _atomic_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def _read_json(self, path: Path, defaults: dict[str, Any]) -> dict[str, Any]:
        self.ensure()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else deepcopy(defaults)
        except (OSError, json.JSONDecodeError):
            return deepcopy(defaults)

    def read_global(self) -> dict[str, Any]:
        return self._read_json(self.global_file, self._global_defaults())

    def update_global(self, patch: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(patch, dict):
            raise TypeError("patch must be an object")
        self.ensure()
        with _file_lock(self.lock_file):
            current = self._read_json_unlocked(self.global_file, self._global_defaults())
            result = _deep_merge(current, patch)
            result.setdefault("schema_version", GLOBAL_SCHEMA_VERSION)
            result["updated_at"] = utc_now()
            self._atomic_json(self.global_file, result)
        self.trace("global_state_update", {"keys": sorted(patch)})
        return result

    @staticmethod
    def _read_json_unlocked(path: Path, defaults: dict[str, Any]) -> dict[str, Any]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else deepcopy(defaults)
        except (OSError, json.JSONDecodeError):
            return deepcopy(defaults)

    def note_project(self, project_root: str) -> None:
        raw = str(project_root or "").strip()
        if not raw:
            return
        root = Path(raw)
        # Do not turn an arbitrary launch directory such as the user's home into a project.
        if not ((root / ".git").exists() or (root / ".hcp" / "state").exists()):
            return
        state = self.read_global()
        recent = [x for x in state.get("recent_projects", []) if isinstance(x, dict)]
        normalized = str(root.expanduser().resolve())
        recent = [x for x in recent if str(x.get("root") or "").casefold() != normalized.casefold()]
        recent.insert(0, {"root": normalized, "last_seen": utc_now()})
        self.update_global({"recent_projects": recent[:20]})

    def _read_instructions_payload(self) -> dict[str, Any]:
        return self._read_json(self.instructions_file, self._instruction_defaults())

    def instructions(self, *, statuses: set[str] | None = None) -> list[dict[str, Any]]:
        items = self._read_instructions_payload().get("instructions", [])
        result = [x for x in items if isinstance(x, dict)]
        if statuses is not None:
            result = [x for x in result if str(x.get("status") or "pending") in statuses]
        return result

    def record_instruction(self, payload: dict[str, Any], *, project_root: str = "", session_id: str = "") -> dict[str, Any]:
        action = str(payload.get("action") or "").strip()
        if not action:
            raise ValueError("instruction action is required")
        trigger_type = str(payload.get("trigger_type") or "contains_any")
        if trigger_type not in {"contains_any", "exact", "regex", "next_session", "always"}:
            raise ValueError("unsupported trigger_type")
        patterns = [str(x).strip() for x in (payload.get("trigger_patterns") or []) if str(x).strip()]
        if trigger_type in {"contains_any", "exact", "regex"} and not patterns:
            raise ValueError("trigger_patterns are required for this trigger_type")
        scope = str(payload.get("scope") or "global")
        if scope not in {"global", "project"}:
            raise ValueError("scope must be global or project")
        if scope == "project" and not project_root:
            raise ValueError("project-scoped instruction requires a project root")
        seed = f"{utc_now()}|{session_id}|{action}|{patterns}"
        item = {
            "id": str(payload.get("id") or hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]),
            "schema_version": GLOBAL_SCHEMA_VERSION,
            "action": action,
            "action_type": str(payload.get("action_type") or "instruction"),
            "trigger_type": trigger_type,
            "trigger_patterns": patterns,
            "scope": scope,
            "project_root": str(project_root) if scope == "project" else "",
            "consume_after_success": bool(payload.get("consume_after_success", True)),
            "active_after": str(payload.get("active_after") or ""),
            "expires_at": str(payload.get("expires_at") or ""),
            "priority": str(payload.get("priority") or "normal"),
            "status": "pending",
            "source_session_id": session_id,
            "created_at": utc_now(),
            "triggered_at": "",
            "triggered_session_id": "",
            "completed_at": "",
            "note": str(payload.get("note") or ""),
        }
        self.ensure()
        with _file_lock(self.lock_file):
            current = self._read_json_unlocked(self.instructions_file, self._instruction_defaults())
            items = [x for x in current.get("instructions", []) if isinstance(x, dict)]
            items.append(item)
            current["instructions"] = items[-500:]
            current["updated_at"] = utc_now()
            self._atomic_json(self.instructions_file, current)
        self.trace("instruction_recorded", {"id": item["id"], "scope": scope, "trigger_type": trigger_type})
        return item

    def update_instruction(self, instruction_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        self.ensure()
        found: dict[str, Any] | None = None
        with _file_lock(self.lock_file):
            current = self._read_json_unlocked(self.instructions_file, self._instruction_defaults())
            items = [x for x in current.get("instructions", []) if isinstance(x, dict)]
            for index, item in enumerate(items):
                if str(item.get("id") or "") != instruction_id:
                    continue
                found = _deep_merge(item, patch)
                status = str(found.get("status") or "pending")
                if status not in {"pending", "triggered", "completed", "cancelled", "superseded", "expired"}:
                    raise ValueError("invalid instruction status")
                if status == "completed" and not found.get("completed_at"):
                    found["completed_at"] = utc_now()
                items[index] = found
                break
            if found is None:
                raise KeyError(f"unknown instruction id: {instruction_id}")
            current["instructions"] = items
            current["updated_at"] = utc_now()
            self._atomic_json(self.instructions_file, current)
        self.trace("instruction_updated", {"id": instruction_id, "status": found.get("status")})
        return found

    @staticmethod
    def _time_active(item: dict[str, Any], now: datetime) -> bool:
        active_after = _parse_time(str(item.get("active_after") or ""))
        expires_at = _parse_time(str(item.get("expires_at") or ""))
        if active_after and now < active_after:
            return False
        if expires_at and now > expires_at:
            return False
        return True

    @staticmethod
    def _matches(item: dict[str, Any], user_message: str, session_id: str) -> bool:
        trigger_type = str(item.get("trigger_type") or "contains_any")
        message = _normalize_message(user_message)
        patterns = [str(x) for x in item.get("trigger_patterns", [])]
        if trigger_type == "always":
            return True
        if trigger_type == "next_session":
            source = str(item.get("source_session_id") or "")
            return bool(session_id and source and session_id != source)
        if trigger_type == "exact":
            return any(message == _normalize_message(pattern) for pattern in patterns)
        if trigger_type == "contains_any":
            return any(_normalize_message(pattern) in message for pattern in patterns if _normalize_message(pattern))
        if trigger_type == "regex":
            for pattern in patterns:
                try:
                    if re.search(pattern, user_message, flags=re.IGNORECASE):
                        return True
                except re.error:
                    continue
        return False

    def match(self, user_message: str, *, session_id: str = "", project_root: str = "") -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        matched: list[dict[str, Any]] = []
        for item in self.instructions(statuses={"pending", "triggered"}):
            if not self._time_active(item, now):
                expires = _parse_time(str(item.get("expires_at") or ""))
                if expires and now > expires and str(item.get("status")) != "expired":
                    try:
                        self.update_instruction(str(item.get("id")), {"status": "expired"})
                    except Exception:
                        pass
                continue
            if str(item.get("scope") or "global") == "project":
                left = str(item.get("project_root") or "").casefold()
                right = str(project_root or "").casefold()
                if not left or left != right:
                    continue
            if not self._matches(item, user_message, session_id):
                continue
            try:
                item = self.update_instruction(str(item.get("id")), {
                    "status": "triggered",
                    "triggered_at": utc_now(),
                    "triggered_session_id": session_id,
                })
            except Exception:
                pass
            matched.append(item)
        return matched

    def settle_after_response(self, instruction_id: str, assistant_response: str) -> None:
        items = {str(x.get("id")): x for x in self.instructions()}
        item = items.get(instruction_id)
        if not item or str(item.get("status")) != "triggered":
            return
        satisfied = False
        if str(item.get("action_type") or "instruction") == "respond_exact":
            satisfied = _normalize_message(assistant_response) == _normalize_message(str(item.get("action") or ""))
        if satisfied and bool(item.get("consume_after_success", True)):
            self.update_instruction(instruction_id, {"status": "completed"})
        elif satisfied:
            self.update_instruction(instruction_id, {"status": "pending", "triggered_at": "", "triggered_session_id": ""})
        else:
            # Failed execution must not silently consume a one-shot instruction.
            self.update_instruction(instruction_id, {"status": "pending", "triggered_at": "", "triggered_session_id": ""})

    def trace(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        event = {"timestamp": utc_now(), "event": event_type, "data": data or {}}
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        with _LOCK:
            with self.trace_file.open("a", encoding="utf-8") as fh:
                fh.write(line)

    def summary(self, *, pending_limit: int = 12) -> dict[str, Any]:
        state = self.read_global()
        pending = self.instructions(statuses={"pending", "triggered"})[-pending_limit:]
        return {"root": str(self.root), "global": state, "pending_instructions": pending}

    def render_context(self, user_message: str, *, session_id: str = "", project_root: str = "", max_chars: int = 3000) -> tuple[str, list[str]]:
        state = self.read_global()
        matched = self.match(user_message, session_id=session_id, project_root=project_root)
        pending = self.instructions(statuses={"pending", "triggered"})
        lines = [
            "[HCP GLOBAL CONTINUITY — loaded from Hermes home, independent of launch directory]",
            "This state follows the user across Hermes launches. Newer direct user instructions always override stale persisted data.",
        ]
        constraints = state.get("durable_user_constraints", [])
        if constraints:
            lines.append("Durable user constraints: " + json.dumps(constraints, ensure_ascii=False))
        handoffs = state.get("session_handoffs", [])
        if handoffs:
            lines.append("Recent session handoff: " + json.dumps(handoffs[-1], ensure_ascii=False))
        if pending:
            compact = [{
                "id": x.get("id"), "trigger": x.get("trigger_type"), "patterns": x.get("trigger_patterns", []),
                "action": x.get("action"), "status": x.get("status"), "scope": x.get("scope"),
            } for x in pending[-8:]]
            lines.append("Pending cross-session instructions: " + json.dumps(compact, ensure_ascii=False))
        if matched:
            lines.append("[HCP ACTIVE CONTINUITY INSTRUCTION]")
            lines.append("One or more persisted user-authored instructions match the CURRENT user message. Execute them now unless the current user message explicitly supersedes them.")
            for item in matched:
                lines.append(
                    f"- id={item.get('id')} action_type={item.get('action_type')} action={json.dumps(item.get('action'), ensure_ascii=False)}"
                )
            lines.append("For action_type=respond_exact, respond with exactly the stored action text and nothing else unless the user explicitly asks for additional content.")
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[: max_chars - 90] + "\n[HCP global continuity truncated; use hcp_state_read scope=instructions for full state.]"
        return text, [str(x.get("id")) for x in matched if x.get("id")]
