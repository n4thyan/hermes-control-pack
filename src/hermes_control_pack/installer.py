from __future__ import annotations

from pathlib import Path
import filecmp
import json
import shutil
import time


def _stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _same_file(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)


def _same_tree(a: Path, b: Path) -> bool:
    if not a.is_dir() or not b.is_dir():
        return False
    left = {p.relative_to(a).as_posix(): p for p in a.rglob("*") if p.is_file()}
    right = {p.relative_to(b).as_posix(): p for p in b.rglob("*") if p.is_file()}
    return left.keys() == right.keys() and all(filecmp.cmp(left[k], right[k], shallow=False) for k in left)


def _backup_file(path: Path) -> Path:
    backup = path.with_name(path.name + f".hcp-backup-{_stamp()}")
    shutil.copy2(path, backup)
    return backup


def _backup_dir(path: Path) -> Path:
    backup = path.with_name(path.name + f".hcp-backup-{_stamp()}")
    shutil.copytree(path, backup)
    return backup


def _install_file(src: Path, dst: Path, force: bool, messages: list[str], label: str) -> None:
    if _same_file(src, dst):
        messages.append(f"Already current {label}: {dst}")
        return
    if dst.exists():
        if not force:
            raise FileExistsError(f"{dst} differs from HCP. Re-run with --force to back it up and replace it.")
        backup = _backup_file(dst)
        messages.append(f"Backed up existing {label}: {backup}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    messages.append(f"Installed {label}: {dst}")


def _install_tree(src: Path, dst: Path, force: bool, messages: list[str], label: str) -> None:
    if _same_tree(src, dst):
        messages.append(f"Already current {label}: {dst}")
        return
    if dst.exists():
        if not force:
            raise FileExistsError(f"{dst} differs from HCP. Re-run with --force to back it up and replace it.")
        backup = _backup_dir(dst)
        messages.append(f"Backed up existing {label}: {backup}")
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    messages.append(f"Installed {label}: {dst}")


def validate_build(build_dir: Path) -> list[str]:
    errors: list[str] = []
    required = [".hermes.md", "corpus-index.json", "hcp-manifest.json", "skills"]
    for name in required:
        if not (build_dir / name).exists():
            errors.append(f"missing {name}")
    manifest_path = build_dir / "hcp-manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not manifest.get("corpus_fingerprint"):
                errors.append("manifest missing corpus_fingerprint")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid manifest: {exc}")
    return errors


def install_pack(
    build_dir: Path,
    project_dir: Path,
    hermes_home: Path,
    force: bool = False,
    install_context: bool = True,
    install_skills: bool = True,
    install_bundles: bool = True,
) -> list[str]:
    build_dir = build_dir.resolve()
    errors = validate_build(build_dir)
    if errors:
        raise ValueError("Invalid HCP build: " + "; ".join(errors))

    messages: list[str] = []
    project_dir = project_dir.resolve()
    hermes_home = hermes_home.expanduser().resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    if install_context:
        _install_file(build_dir / ".hermes.md", project_dir / ".hermes.md", force, messages, "project context")

    if install_skills:
        skills_dir = build_dir / "skills"
        for skill in sorted(skills_dir.iterdir()):
            if skill.is_dir():
                _install_tree(skill, hermes_home / "skills" / skill.name, force, messages, f"skill {skill.name}")

    bundles_dir = build_dir / "bundles"
    if install_bundles and bundles_dir.exists():
        for bundle in sorted(bundles_dir.glob("*.yaml")):
            _install_file(bundle, hermes_home / "skill-bundles" / bundle.name, force, messages, f"bundle {bundle.stem}")

    return messages
