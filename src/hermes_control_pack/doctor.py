from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import os

from .installer import SOUL_BEGIN, SOUL_END, validate_build
from .state import ProjectStateStore


def doctor(build_dir: Path | None = None, project: Path | None = None, hermes_home: Path | None = None) -> tuple[bool, list[str]]:
    lines = [f"Python: {sys.version.split()[0]} ({'OK' if sys.version_info >= (3, 11) else 'FAIL: need 3.11+'})"]
    ok = sys.version_info >= (3, 11)

    hermes_bin = shutil.which("hermes")
    lines.append(f"Hermes CLI: {hermes_bin or 'not found (install is still possible; live plugin validation unavailable)'}")

    if build_dir is not None:
        errors = validate_build(build_dir.resolve())
        lines.append(f"Build: {'OK' if not errors else 'FAIL: ' + '; '.join(errors)}")
        ok = ok and not errors

    if project is not None:
        p = project.resolve()
        lines.append(f"Project: {p} ({'exists' if p.exists() else 'will be created'})")
        if (p / ".hermes.md").exists():
            lines.append("Project context: .hermes.md present")
        state = ProjectStateStore(p)
        lines.append(f"Continuity state: {state.state_root} ({'present' if state.state_root.exists() else 'not initialized'})")

    if hermes_home is not None:
        h = hermes_home.expanduser().resolve()
        lines.append(f"Hermes home: {h}")
        skills = h / "skills"
        bundles = h / "skill-bundles"
        plugin = h / "plugins" / "hcp-runtime"
        soul = h / "SOUL.md"
        engine = h / "plugins" / "context_engine" / "hcp-continuity"
        lines.append(f"Skills directory: {skills} ({'present' if skills.exists() else 'missing'})")
        lines.append(f"Bundles directory: {bundles} ({'present' if bundles.exists() else 'missing'})")
        lines.append(f"HCP runtime plugin: {plugin} ({'installed' if plugin.exists() else 'MISSING'})")
        ok = ok and plugin.exists()
        soul_text = ""
        try:
            soul_text = soul.read_text(encoding="utf-8") if soul.exists() else ""
        except OSError:
            pass
        managed = SOUL_BEGIN in soul_text and SOUL_END in soul_text
        lines.append(f"HCP SOUL overlay: {soul} ({'installed' if managed else 'not installed'})")
        lines.append(f"HCP continuity engine: {engine} ({'installed' if engine.exists() else 'not installed'})")

        if hermes_bin:
            try:
                env = dict(os.environ)
                env["HERMES_HOME"] = str(h)
                proc = subprocess.run(
                    [hermes_bin, "config", "get", "context.engine"],
                    capture_output=True, text=True, timeout=20, check=False, env=env,
                )
                value = (proc.stdout or proc.stderr or "").strip().replace("\n", " | ")
                if proc.returncode == 0:
                    lines.append(f"Hermes context.engine: {value or '(unset)'}")
                else:
                    lines.append(f"Hermes context.engine: could not query (exit {proc.returncode})")
            except (OSError, subprocess.TimeoutExpired) as exc:
                lines.append(f"Hermes context.engine: could not query ({exc})")

    return ok, lines
