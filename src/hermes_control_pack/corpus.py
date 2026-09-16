from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator
import hashlib
import json
import re
import zipfile

from .mechanisms import mechanism_hits

TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".py",
    ".js", ".jsx", ".ts", ".tsx", ".d.ts", ".sh", ".ps1", ".html", ".css",
    ".xml", ".csv", ".ini", ".cfg", ".conf", ".rst",
}

CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "exploration": ("explore", "inspect", "search", "read", "understand", "codebase", "repository"),
    "planning": ("plan", "todo", "approach", "strategy", "steps", "before implementing"),
    "implementation": ("implement", "edit", "modify", "patch", "write code", "make changes"),
    "debugging": ("debug", "root cause", "reproduce", "trace", "diagnose", "failure", "error"),
    "verification": ("verify", "test", "build", "lint", "typecheck", "validate", "evidence"),
    "review": ("review", "self-review", "regression", "quality", "critique", "check your work"),
    "delegation": ("delegate", "subagent", "parallel", "agent", "spawn", "workstream"),
    "context": ("context", "memory", "compress", "handoff", "summary", "persistent"),
    "tools": ("tool", "terminal", "browser", "shell", "grep", "search files", "screenshot"),
    "autonomy": ("continue", "persist", "do not ask", "without asking", "autonomous", "proactive"),
    "git": ("git", "commit", "branch", "diff", "worktree", "pull request"),
    "visual": ("visual", "screenshot", "browser", "pixel", "render", "ui", "frontend"),
    "research": ("research", "source", "citation", "evidence", "web search", "documentation"),
    "safety": ("destructive", "permission", "credential", "secret", "security", "approval"),
}


@dataclass(frozen=True)
class CorpusEntry:
    path: str
    bytes: int
    sha256: str
    extension: str
    top_level: str
    text: bool
    words: int
    category_hits: dict[str, int]
    mechanism_hits: dict[str, int]
    artifact_kind: str


def _is_text_path(name: str) -> bool:
    lower = name.lower()
    if lower.endswith(".d.ts"):
        return True
    return Path(lower).suffix in TEXT_EXTENSIONS


def _safe_decode(data: bytes) -> str | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if text and text.count("\x00") / max(len(text), 1) > 0.001:
        return None
    return text


def _category_hits(text: str) -> dict[str, int]:
    lower = text.lower()
    hits: dict[str, int] = {}
    for category, needles in CATEGORY_PATTERNS.items():
        score = sum(lower.count(needle) for needle in needles)
        if score:
            hits[category] = score
    return hits


def _artifact_kind(path: str, is_text: bool) -> str:
    if not is_text:
        return "asset"
    low = path.lower().replace("\\", "/")
    name = Path(low).name
    if "/skills/" in low or low.startswith("skills/"):
        return "skill"
    if "/commands/" in low or low.startswith("commands/"):
        return "command"
    if any(token in low for token in ("/tools/", "schema", "mcp")):
        return "tool_or_schema"
    if any(token in low for token in ("claude-code", "/codex/", "cursor", "devin", "opencode", "commandcode", "hermes")):
        return "agent_prompt"
    if "system" in name or "prompt" in name:
        return "system_prompt"
    if name.startswith("readme") or name in {"license", "contributing.md"}:
        return "documentation"
    if Path(low).suffix in {".md", ".txt"}:
        return "prompt_or_notes"
    return "source"


def _entry(path: str, data: bytes, strip_prefix: str | None = None) -> CorpusEntry:
    logical_path = path
    if strip_prefix and logical_path.startswith(strip_prefix + "/"):
        logical_path = logical_path[len(strip_prefix) + 1 :]
    text_value = _safe_decode(data) if _is_text_path(path) else None
    parts = Path(logical_path).parts
    top = parts[0] if len(parts) > 1 else "[root]"
    words = len(re.findall(r"\b\w+\b", text_value)) if text_value is not None else 0
    return CorpusEntry(
        path=path,
        bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        extension=".d.ts" if path.lower().endswith(".d.ts") else Path(path).suffix.lower(),
        top_level=top,
        text=text_value is not None,
        words=words,
        category_hits=_category_hits(text_value or ""),
        mechanism_hits=mechanism_hits(text_value or ""),
        artifact_kind=_artifact_kind(logical_path, text_value is not None),
    )


def _zip_root_prefix(names: list[str]) -> str | None:
    roots = {Path(name).parts[0] for name in names if Path(name).parts}
    return next(iter(roots)) if len(roots) == 1 else None


def iter_entries(source: Path) -> Iterator[CorpusEntry]:
    source = source.expanduser().resolve()
    if source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            prefix = _zip_root_prefix([i.filename for i in infos])
            for info in infos:
                yield _entry(info.filename, zf.read(info), prefix)
        return
    if source.is_dir():
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = path.relative_to(source).as_posix()
            yield _entry(rel, path.read_bytes())
        return
    raise FileNotFoundError(f"Corpus source does not exist or is not a ZIP/directory: {source}")


def source_sha256(source: Path, entries: list[CorpusEntry] | None = None) -> str:
    source = source.expanduser().resolve()
    if source.is_file():
        h = hashlib.sha256()
        with source.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    entries = entries if entries is not None else list(iter_entries(source))
    h = hashlib.sha256()
    for entry in sorted(entries, key=lambda e: e.path):
        h.update(entry.path.encode("utf-8"))
        h.update(b"\0")
        h.update(entry.sha256.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def build_index(source: Path) -> dict:
    entries = list(iter_entries(source))
    providers: dict[str, int] = {}
    category_totals: dict[str, int] = {}
    provider_category_hits: dict[str, dict[str, int]] = {}
    provider_category_files: dict[str, dict[str, int]] = {}
    extension_counts: dict[str, int] = {}
    artifact_counts: dict[str, int] = {}
    mechanism_totals: dict[str, int] = {}
    provider_mechanism_hits: dict[str, dict[str, int]] = {}
    provider_mechanism_files: dict[str, dict[str, int]] = {}
    text_files = 0
    words = 0
    byte_count = 0

    for entry in entries:
        providers[entry.top_level] = providers.get(entry.top_level, 0) + 1
        extension_counts[entry.extension or "[none]"] = extension_counts.get(entry.extension or "[none]", 0) + 1
        artifact_counts[entry.artifact_kind] = artifact_counts.get(entry.artifact_kind, 0) + 1
        byte_count += entry.bytes
        if entry.text:
            text_files += 1
            words += entry.words
        p_hits = provider_category_hits.setdefault(entry.top_level, {})
        p_files = provider_category_files.setdefault(entry.top_level, {})
        pm_hits = provider_mechanism_hits.setdefault(entry.top_level, {})
        pm_files = provider_mechanism_files.setdefault(entry.top_level, {})
        for key, value in entry.mechanism_hits.items():
            mechanism_totals[key] = mechanism_totals.get(key, 0) + value
            pm_hits[key] = pm_hits.get(key, 0) + value
            pm_files[key] = pm_files.get(key, 0) + 1
        for key, value in entry.category_hits.items():
            category_totals[key] = category_totals.get(key, 0) + value
            p_hits[key] = p_hits.get(key, 0) + value
            p_files[key] = p_files.get(key, 0) + 1

    return {
        "schema_version": 3,
        "source": str(source.expanduser().resolve()),
        "source_sha256": source_sha256(source, entries),
        "entry_count": len(entries),
        "text_entry_count": text_files,
        "total_bytes": byte_count,
        "total_words": words,
        "top_level_counts": dict(sorted(providers.items(), key=lambda kv: (-kv[1], kv[0]))),
        "extension_counts": dict(sorted(extension_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "artifact_counts": dict(sorted(artifact_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "mechanism_hits": dict(sorted(mechanism_totals.items(), key=lambda kv: (-kv[1], kv[0]))),
        "category_hits": dict(sorted(category_totals.items(), key=lambda kv: (-kv[1], kv[0]))),
        "provider_category_hits": {
            provider: dict(sorted(values.items(), key=lambda kv: (-kv[1], kv[0])))
            for provider, values in sorted(provider_category_hits.items())
        },
        "provider_mechanism_hits": {
            provider: dict(sorted(values.items(), key=lambda kv: (-kv[1], kv[0])))
            for provider, values in sorted(provider_mechanism_hits.items())
        },
        "provider_mechanism_files": {
            provider: dict(sorted(values.items(), key=lambda kv: (-kv[1], kv[0])))
            for provider, values in sorted(provider_mechanism_files.items())
        },
        "provider_category_files": {
            provider: dict(sorted(values.items(), key=lambda kv: (-kv[1], kv[0])))
            for provider, values in sorted(provider_category_files.items())
        },
        "entries": [asdict(e) for e in entries],
    }


def write_index(source: Path, output: Path) -> dict:
    index = build_index(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return index
