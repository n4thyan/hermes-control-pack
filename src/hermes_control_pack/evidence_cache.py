"""Tool Evidence Cache for Hermes Control Pack.

Stores tool call results with TTL-based staleness detection to avoid
redundant rediscovery across sessions. Addresses the ``tool_evidence_reuse``
mechanism identified across 13 independent agent-prompt source families
in the system_prompts_leaks corpus.

The cache lives at ``~/.hermes/hcp/evidence-cache.jsonl`` and is
project-aware: entries are keyed by an evidence_key (hash of tool
name + normalized arguments) and tagged with the project root so
different projects can have independent cached results.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import hashlib
import json
import os
import re
import threading


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _evidence_cache_path() -> Path:
    # Test override
    test_path = os.environ.get("HCP_EVIDENCE_CACHE_PATH")
    if test_path:
        return Path(test_path)
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:
        home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
    return home / "hcp" / "evidence-cache.jsonl"


def _normalize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Strip session-specific noise from tool arguments for stable hashing."""
    if not isinstance(args, dict):
        return {}
    skip_keys = {"session_id", "task_id", "turn_id", "user_task", "enabled_toolsets",
                 "disabled_toolsets", "tool_call_id", "api_request_id"}
    normalized = {}
    for k, v in sorted(args.items()):
        if k in skip_keys:
            continue
        if isinstance(v, str):
            try:
                abs_path = Path(v).expanduser().resolve()
                cwd = Path.cwd()
                try:
                    v = abs_path.relative_to(cwd).as_posix()
                except ValueError:
                    v = abs_path.as_posix()
            except (OSError, ValueError):
                pass
        normalized[k] = v
    return normalized


def _make_evidence_key(tool_name: str, args: dict[str, Any]) -> str:
    normalized = _normalize_args(args)
    canonical = f"{tool_name}:"
    if normalized:
        canonical += json.dumps(normalized, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


# Default TTLs per tool kind (seconds)
_DEFAULT_TTLS: dict[str, int] = {
    "read_file": 600,
    "search_files": 300,
    "web_search": 1800,
    "web_extract": 3600,
    "terminal": 0,
    "hcp_state_read": 60,
    "_default": 900,
}


class EvidenceCache:
    """Persistent, project-aware tool evidence cache."""

    def __init__(self, project_root: Path | str | None = None, max_entries: int = 2000):
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = str(Path(project_root).expanduser().resolve())
        self.lock = threading.RLock()
        self.max_entries = max_entries

    @property
    def path(self) -> Path:
        # Lazy so tests can override env var before instantiation
        return _evidence_cache_path()

    def lookup(self, tool_name: str, args: dict[str, Any], max_age_seconds: int | None = None) -> dict[str, Any] | None:
        """Return a cached evidence entry if fresh enough, else None."""
        key = _make_evidence_key(tool_name, args)
        ttl = max_age_seconds if max_age_seconds is not None else _DEFAULT_TTLS.get(tool_name, _DEFAULT_TTLS["_default"])
        if ttl <= 0:
            return None
        
        with self.lock:
            for entry in self._read_all():
                if entry.get("evidence_key") != key:
                    continue
                if entry.get("project_root") != self.project_root:
                    continue
                if entry.get("tool_name") != tool_name:
                    continue
                ts = entry.get("timestamp")
                if not ts:
                    continue
                try:
                    cached_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                except (ValueError, TypeError):
                    continue
                if age <= ttl:
                    return entry
            return None

    def store(self, tool_name: str, args: dict[str, Any], result: Any, result_digest: str | None = None,
              staleness_hint: str | None = None, source: str = "auto") -> dict[str, Any]:
        """Store a tool result in the cache."""
        key = _make_evidence_key(tool_name, args)
        entry = {
            "timestamp": utc_now(),
            "project_root": self.project_root,
            "tool_name": tool_name,
            "evidence_key": key,
            "args": _normalize_args(args),
            "result": result,
            "result_digest": result_digest,
            "staleness_hint": staleness_hint,
            "source": source,
            "schema_version": 1,
        }
        with self.lock:
            self._append_entry(entry)
            self._prune()
        return entry

    def invalidate(self, tool_name: str | None = None, project_root: str | None = None) -> int:
        """Remove matching entries. Returns count removed."""
        if project_root is not None:
            target_project = str(Path(project_root).expanduser().resolve())
        else:
            target_project = self.project_root
        with self.lock:
            entries = self._read_all()
            kept = []
            removed = 0
            for entry in entries:
                if project_root and entry.get("project_root") != target_project:
                    kept.append(entry)
                    continue
                if tool_name and entry.get("tool_name") != tool_name:
                    kept.append(entry)
                    continue
                removed += 1
            self._write_all(entries=kept)
            return removed

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        result = []
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        result.append(obj)
                except json.JSONDecodeError:
                    continue
        except OSError:
            return []
        return result

    def _write_all(self, entries: list[dict[str, Any]]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
            tmp.write_text("\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in entries) + "\n",
                           encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    def _append_entry(self, entry: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
        except OSError:
            pass

    def _prune(self) -> None:
        entries = self._read_all()
        if len(entries) <= self.max_entries:
            return
        entries.sort(key=lambda e: e.get("timestamp", ""))
        self._write_all(entries[-self.max_entries:])

    def summary(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock:
            entries = self._read_all()
            if self.project_root:
                entries = [e for e in entries if e.get("project_root") == self.project_root]
            return entries[-limit:]


def get_cache(project_root: Path | str | None = None) -> EvidenceCache:
    """Factory: return a project-scoped EvidenceCache."""
    return EvidenceCache(project_root)
