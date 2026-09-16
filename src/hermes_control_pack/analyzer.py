from __future__ import annotations

from .mechanisms import mechanism_specs

NOISE_GROUPS = {"assets", ".github", "[root]", ""}


def meaningful_groups(index: dict) -> list[str]:
    return [g for g in index.get("top_level_counts", {}) if g not in NOISE_GROUPS]


def cross_source_coverage(index: dict) -> dict[str, dict[str, int]]:
    """Summarize how broadly each behavior family appears across source groups."""
    groups = set(meaningful_groups(index))
    provider_files = index.get("provider_category_files", {})
    provider_hits = index.get("provider_category_hits", {})
    categories = set(index.get("category_hits", {}))
    result: dict[str, dict[str, int]] = {}
    for category in sorted(categories):
        supporting = [g for g in groups if provider_files.get(g, {}).get(category, 0) > 0]
        result[category] = {
            "source_groups": len(supporting),
            "files": sum(provider_files.get(g, {}).get(category, 0) for g in supporting),
            "hits": sum(provider_hits.get(g, {}).get(category, 0) for g in supporting),
        }
    return result


def mechanism_coverage(index: dict) -> dict[str, dict]:
    groups = set(meaningful_groups(index))
    files = index.get("provider_mechanism_files", {})
    hits = index.get("provider_mechanism_hits", {})
    specs = mechanism_specs()
    result: dict[str, dict] = {}
    for name in specs:
        supporting = sorted(g for g in groups if files.get(g, {}).get(name, 0) > 0)
        paths = [
            entry["path"] for entry in index.get("entries", [])
            if entry.get("mechanism_hits", {}).get(name, 0) > 0 and entry.get("top_level") not in NOISE_GROUPS
        ]
        result[name] = {
            "purpose": specs[name].purpose,
            "hcp_target": specs[name].hcp_target,
            "source_groups": supporting,
            "source_group_count": len(supporting),
            "files": sum(files.get(g, {}).get(name, 0) for g in supporting),
            "hits": sum(hits.get(g, {}).get(name, 0) for g in supporting),
            "example_paths": paths[:8],
        }
    return result


def signal_markdown(index: dict) -> str:
    coverage = cross_source_coverage(index)
    rows = "\n".join(
        f"| `{cat}` | {values['source_groups']} | {values['files']:,} | {values['hits']:,} |"
        for cat, values in sorted(coverage.items(), key=lambda kv: (-kv[1]["source_groups"], -kv[1]["files"], kv[0]))
    )
    groups = meaningful_groups(index)
    group_rows = "\n".join(
        f"| `{group}` | {index['top_level_counts'].get(group, 0):,} | {sum(index.get('provider_category_files', {}).get(group, {}).values()):,} |"
        for group in groups
    )
    return f"""# Research Signal Report

This is a deterministic **coverage report**, not a model-quality ranking and not a claim that repeated wording is correct. HCP uses it to check that the runtime design is informed by the breadth of the supplied corpus instead of a single source.

- Source fingerprint: `{index['source_sha256']}`
- Files scanned: **{index['entry_count']:,}**
- Decoded text files: **{index['text_entry_count']:,}**
- Approximate decoded words: **{index['total_words']:,}**
- Meaningful top-level source groups: **{len(groups)}**

## Behavior-family coverage

| Behavior family | Source groups | Files containing signal | Raw phrase hits |
|---|---:|---:|---:|
{rows}

## Source groups

The last column sums per-category file presence and therefore can exceed the number of files.

| Source group | Files | Category-bearing file counts |
|---|---:|---:|
{group_rows}

## Interpretation

HCP deliberately converts this evidence into authored, vendor-neutral operating procedures. It does not concatenate source prompts, reproduce proprietary tool schemas, or treat keyword frequency as an instruction priority.
"""


def mechanism_markdown(index: dict) -> str:
    coverage = mechanism_coverage(index)
    rows = []
    for name, item in sorted(coverage.items(), key=lambda kv: (-kv[1]["source_group_count"], -kv[1]["files"], kv[0])):
        groups = ", ".join(item["source_groups"][:8])
        if len(item["source_groups"]) > 8:
            groups += ", …"
        rows.append(
            f"| `{name}` | {item['source_group_count']} | {item['files']:,} | `{item['hcp_target']}` | {groups} |"
        )
    return """# Agent Mechanism Matrix

HCP treats the supplied corpus as an **agent-architecture dataset**. This matrix records where transferable mechanisms are observed across independent top-level source families. It contains metadata and authored generalizations, not copied prompt passages.

| Mechanism | Source groups | Files | HCP implementation target | Example supporting groups |
|---|---:|---:|---|---|
""" + "\n".join(rows) + "\n\n## Interpretation\n\nA mechanism's presence does not prove that it is optimal. HCP implements mechanisms as hypotheses and validates them with Hermes benchmarks. `source_groups` is breadth evidence, not a vendor score.\n"
