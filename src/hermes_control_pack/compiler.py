from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil

from . import __version__
from .analyzer import signal_markdown
from .corpus import build_index
from .kernel import KERNEL


def coverage_markdown(index: dict) -> str:
    top = "\n".join(f"| `{k}` | {v} |" for k, v in index["top_level_counts"].items())
    cats = "\n".join(f"| `{k}` | {v} |" for k, v in index["category_hits"].items())
    return f"""# Corpus Coverage Report

This report proves which local research corpus was scanned by Hermes Control Pack. It intentionally contains metadata and aggregate signals rather than redistributing source prompt text.

- Entries scanned: **{index['entry_count']:,}**
- Text entries decoded: **{index['text_entry_count']:,}**
- Approximate words across decoded text: **{index['total_words']:,}**
- Bytes indexed: **{index['total_bytes']:,}**
- Source SHA-256/fingerprint: `{index['source_sha256']}`

## Top-level coverage

| Group | Files |
|---|---:|
{top}

## Control-pattern signal coverage

These counts are deterministic keyword/phrase hits used as a coverage signal, not an evaluation score.

| Pattern family | Hits |
|---|---:|
{cats}
"""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest(output: Path, index: dict) -> dict:
    artifacts = {}
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "hcp-manifest.json"):
        artifacts[path.relative_to(output).as_posix()] = _sha256(path)
    return {
        "schema_version": 1,
        "hcp_version": __version__,
        "corpus_fingerprint": index["source_sha256"],
        "corpus_entries": index["entry_count"],
        "artifacts": artifacts,
    }


def build_pack(source: Path, output: Path, project_root: Path | None = None) -> dict:
    output = output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    index = build_index(source)

    (output / "corpus-index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / ".hermes.md").write_text(KERNEL, encoding="utf-8")
    (output / "CORPUS_COVERAGE.md").write_text(coverage_markdown(index), encoding="utf-8")
    (output / "RESEARCH_SIGNALS.md").write_text(signal_markdown(index), encoding="utf-8")

    runtime_root = Path(__file__).resolve().parent / "runtime"
    # Prefer repository assets during development, but always fall back to packaged assets.
    asset_root = project_root if project_root and (project_root / "skills").exists() else runtime_root
    for dirname in ("skills", "bundles"):
        src = asset_root / dirname
        dst = output / dirname
        if not src.exists():
            raise FileNotFoundError(f"HCP runtime asset directory missing: {src}")
        shutil.copytree(src, dst)

    manifest = _manifest(output, index)
    (output / "hcp-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return index
