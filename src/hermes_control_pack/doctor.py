from __future__ import annotations

from pathlib import Path
import shutil
import sys

from .installer import validate_build


def doctor(build_dir: Path | None = None, project: Path | None = None, hermes_home: Path | None = None) -> tuple[bool, list[str]]:
    lines = [f"Python: {sys.version.split()[0]} ({'OK' if sys.version_info >= (3, 11) else 'FAIL: need 3.11+'})"]
    ok = sys.version_info >= (3, 11)

    hermes_bin = shutil.which("hermes")
    lines.append(f"Hermes CLI: {hermes_bin or 'not found (install is still possible; runtime not verified)'}")

    if build_dir is not None:
        errors = validate_build(build_dir.resolve())
        lines.append(f"Build: {'OK' if not errors else 'FAIL: ' + '; '.join(errors)}")
        ok = ok and not errors

    if project is not None:
        p = project.resolve()
        lines.append(f"Project: {p} ({'exists' if p.exists() else 'will be created'})")
        if (p / ".hermes.md").exists():
            lines.append("Project context: .hermes.md present")

    if hermes_home is not None:
        h = hermes_home.expanduser().resolve()
        lines.append(f"Hermes home: {h}")
        lines.append(f"Skills directory: {h / 'skills'}")
        lines.append(f"Bundles directory: {h / 'skill-bundles'}")

    return ok, lines
