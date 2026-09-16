from __future__ import annotations

from pathlib import Path
import filecmp
import json
import shutil
import subprocess
import time

from .state import ProjectStateStore
from .kernel import KERNEL

SOUL_BEGIN = "# BEGIN HCP MANAGED SOUL"
SOUL_END = "# END HCP MANAGED SOUL"


def _runtime_root() -> Path:
    return Path(__file__).resolve().parent / "runtime"


def _stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _same_file(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)


def _tree_files(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.suffix not in {".pyc", ".pyo"}
    }


def _same_tree(a: Path, b: Path) -> bool:
    if not a.is_dir() or not b.is_dir():
        return False
    left = _tree_files(a)
    right = _tree_files(b)
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


def _install_text(content: str, dst: Path, force: bool, messages: list[str], label: str) -> None:
    normalized = content if content.endswith("\n") else content + "\n"
    if dst.exists():
        try:
            if dst.read_text(encoding="utf-8") == normalized:
                messages.append(f"Already current {label}: {dst}")
                return
        except OSError:
            pass
        if not force:
            raise FileExistsError(f"{dst} differs from HCP. Re-run with --force to back it up and replace it.")
        backup = _backup_file(dst)
        messages.append(f"Backed up existing {label}: {backup}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(normalized, encoding="utf-8")
    messages.append(f"Installed {label}: {dst}")


def _merge_soul_profile(src: Path, dst: Path, messages: list[str], profile: str) -> None:
    """Install HCP identity as a managed block while preserving user-authored SOUL text."""
    body = src.read_text(encoding="utf-8").strip()
    block = f"{SOUL_BEGIN}\n{body}\n{SOUL_END}"
    existing = dst.read_text(encoding="utf-8") if dst.exists() else ""
    begin = existing.find(SOUL_BEGIN)
    end = existing.find(SOUL_END, begin + len(SOUL_BEGIN)) if begin >= 0 else -1
    if begin >= 0 and end < 0:
        raise ValueError(
            f"{dst} contains {SOUL_BEGIN!r} without a matching end marker; "
            "repair the file before HCP updates the managed SOUL block."
        )
    if begin >= 0:
        end += len(SOUL_END)
        merged = existing[:begin].rstrip()
        suffix = existing[end:].strip()
        merged = "\n\n".join(part for part in (merged, block, suffix) if part).rstrip() + "\n"
    else:
        prefix = existing.rstrip()
        merged = "\n\n".join(part for part in (prefix, block) if part).rstrip() + "\n"
    if existing == merged:
        messages.append(f"Already current SOUL profile {profile}: {dst}")
        return
    if dst.exists():
        backup = _backup_file(dst)
        messages.append(f"Backed up existing SOUL.md before managed merge: {backup}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(merged, encoding="utf-8")
    messages.append(f"Merged HCP SOUL profile {profile}: {dst}")


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
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    messages.append(f"Installed {label}: {dst}")


def validate_build(build_dir: Path) -> list[str]:
    errors: list[str] = []
    required = [
        ".hermes.md", "corpus-index.json", "hcp-manifest.json", "MECHANISMS.json",
        "skills", "bundles", "souls", "plugins/hcp-runtime",
    ]
    for name in required:
        if not (build_dir / name).exists():
            errors.append(f"missing {name}")
    manifest_path = build_dir / "hcp-manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not manifest.get("corpus_fingerprint"):
                errors.append("manifest missing corpus_fingerprint")
            if not manifest.get("hcp_version"):
                errors.append("manifest missing hcp_version")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid manifest: {exc}")
    return errors


def _enable_runtime_plugin(messages: list[str], hermes_home: Path) -> None:
    hermes = shutil.which("hermes")
    if not hermes:
        messages.append("Hermes CLI not found; enable later with: hermes plugins enable hcp-runtime")
        return
    try:
        env = dict(__import__("os").environ)
        env["HERMES_HOME"] = str(hermes_home)
        proc = subprocess.run(
            [hermes, "plugins", "enable", "hcp-runtime"],
            capture_output=True, text=True, timeout=60, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        messages.append(f"Could not enable hcp-runtime automatically: {exc}")
        return
    output = (proc.stdout or proc.stderr or "").strip().replace("\n", " | ")
    if proc.returncode == 0:
        messages.append("Enabled Hermes plugin: hcp-runtime" + (f" ({output})" if output else ""))
    else:
        messages.append(
            f"Plugin installed but automatic enable failed (exit {proc.returncode}). "
            f"Run: hermes plugins enable hcp-runtime" + (f" — {output}" if output else "")
        )


def _select_context_engine(messages: list[str], hermes_home: Path) -> None:
    hermes = shutil.which("hermes")
    if not hermes:
        messages.append(
            "Hermes CLI not found; select later with: hermes config set context.engine hcp-continuity"
        )
        return
    try:
        env = dict(__import__("os").environ)
        env["HERMES_HOME"] = str(hermes_home)
        proc = subprocess.run(
            [hermes, "config", "set", "context.engine", "hcp-continuity"],
            capture_output=True, text=True, timeout=60, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        messages.append(f"Could not select hcp-continuity automatically: {exc}")
        return
    output = (proc.stdout or proc.stderr or "").strip().replace("\n", " | ")
    if proc.returncode == 0:
        messages.append("Selected Hermes context engine: hcp-continuity" + (f" ({output})" if output else ""))
    else:
        messages.append(
            f"Context engine installed but automatic selection failed (exit {proc.returncode}). "
            f"Run: hermes config set context.engine hcp-continuity" + (f" — {output}" if output else "")
        )


def install_pack(
    build_dir: Path | None,
    project_dir: Path,
    hermes_home: Path,
    force: bool = False,
    install_context: bool = True,
    install_skills: bool = True,
    install_bundles: bool = True,
    install_plugin: bool = True,
    enable_plugin: bool = False,
    soul_profile: str | None = None,
    install_context_engine: bool = False,
    select_context_engine: bool = False,
    initialize_state: bool = True,
) -> list[str]:
    if build_dir is not None:
        build_dir = build_dir.resolve()
        errors = validate_build(build_dir)
        if errors:
            raise ValueError("Invalid HCP build: " + "; ".join(errors))
        assets = build_dir
    else:
        assets = _runtime_root()

    messages: list[str] = []
    project_dir = project_dir.resolve()
    hermes_home = hermes_home.expanduser().resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    if install_context:
        if build_dir is not None:
            _install_file(build_dir / ".hermes.md", project_dir / ".hermes.md", force, messages, "project context")
        else:
            _install_text(KERNEL, project_dir / ".hermes.md", force, messages, "project context")

    if install_skills:
        for skill in sorted((assets / "skills").iterdir()):
            if skill.is_dir():
                _install_tree(skill, hermes_home / "skills" / skill.name, force, messages, f"skill {skill.name}")

    if install_bundles:
        for bundle in sorted((assets / "bundles").glob("*.yaml")):
            _install_file(bundle, hermes_home / "skill-bundles" / bundle.name, force, messages, f"bundle {bundle.stem}")

    if install_plugin:
        _install_tree(
            assets / "plugins" / "hcp-runtime",
            hermes_home / "plugins" / "hcp-runtime",
            force,
            messages,
            "runtime plugin hcp-runtime",
        )
        if enable_plugin:
            _enable_runtime_plugin(messages, hermes_home)
        else:
            messages.append("Runtime plugin is opt-in in Hermes; enable with: hermes plugins enable hcp-runtime")

    if install_context_engine:
        engine_src = assets / "plugins" / "context_engine" / "hcp-continuity"
        if not engine_src.exists():
            raise FileNotFoundError(f"HCP continuity context engine missing: {engine_src}")
        _install_tree(
            engine_src,
            hermes_home / "plugins" / "context_engine" / "hcp-continuity",
            force,
            messages,
            "context engine hcp-continuity",
        )
        if select_context_engine:
            _select_context_engine(messages, hermes_home)
        else:
            messages.append(
                "Context engine installed but not selected. Activate with: "
                "hermes config set context.engine hcp-continuity"
            )

    if soul_profile:
        soul = assets / "souls" / f"{soul_profile}.md"
        if not soul.exists():
            available = ", ".join(p.stem for p in sorted((assets / "souls").glob("*.md")))
            raise ValueError(f"Unknown SOUL profile {soul_profile!r}. Available: {available}")
        _merge_soul_profile(soul, hermes_home / "SOUL.md", messages, soul_profile)

    if initialize_state:
        state = ProjectStateStore(project_dir)
        state.ensure()
        messages.append(f"Initialized persistent HCP continuity state: {state.state_root}")

    return messages
