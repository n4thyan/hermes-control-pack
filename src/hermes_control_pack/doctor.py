from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import os

from .installer import SOUL_BEGIN, SOUL_END, validate_build, _cleanup_stale_plugin_backups
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


def runtime_health_check(hermes_home: Path) -> tuple[bool, list[str]]:
    """Truthful health check for HCP runtime plugin installation.

    This function performs real filesystem checks and reports honestly about
    what it finds. It never fabricates or assumes status that it cannot verify.
    It actively detects and reports the plugin-shadowing bug where a stale
    backup directory inside plugins/ can shadow the real plugin.
    """
    from . import __version__
    h = hermes_home.expanduser().resolve()
    lines = [
        f"Hermes Control Pack {__version__}",
        f"Hermes home: {h}",
    ]
    ok = True

    plugin_dir = h / "plugins" / "hcp-runtime"
    plugin_yaml = plugin_dir / "plugin.yaml"

    # Check if plugin is installed
    if not plugin_dir.exists():
        lines.append("HCP runtime plugin: NOT INSTALLED")
        ok = False
    else:
        lines.append(f"HCP runtime plugin: installed at {plugin_dir}")

    # Detect stale backup directories that could shadow the real plugin
    # (the root cause of the 2.0-vs-2.1 schema mismatch)
    plugins_dir = h / "plugins"
    stale_backups = []
    if plugins_dir.is_dir():
        for child in plugins_dir.iterdir():
            if child.is_dir() and ".hcp-backup-" in child.name:
                stale_backups.append(child.name)

    if stale_backups:
        lines.append(f"WARNING: {len(stale_backups)} stale backup(s) detected inside plugins/:")
        for name in stale_backups:
            lines.append(f"  - {name}")
        lines.append("  These can shadow the real plugin. Run 'hcp install --force' to clean them up.")
        ok = False
    else:
        lines.append("Plugin shadow check: OK (no stale backups in plugins/)")

    # Check installed plugin version
    if plugin_yaml.exists():
        try:
            content = plugin_yaml.read_text()
            for line in content.splitlines():
                if line.startswith("version:"):
                    installed_version = line.split(":", 1)[1].strip()
                    lines.append(f"Installed plugin version: {installed_version}")
                    if installed_version != __version__:
                        lines.append(f"  NOTE: Package is {__version__}, installed plugin is {installed_version}")
                    break
        except OSError:
            lines.append("Could not read installed plugin version")

    # Verify schemas contain global/instruction scopes (the fix)
    schemas_file = plugin_dir / "schemas.py"
    if schemas_file.exists():
        content = schemas_file.read_text()
        has_global = '"global"' in content and '"instructions"' in content
        if has_global:
            lines.append("Schema scopes: OK (global/instruction present)")
        else:
            lines.append("Schema scopes: MISSING global/instruction — old plugin version!")
            ok = False

    # Check backup directory location
    backup_root = h / ".hcp-backups"
    if backup_root.exists():
        lines.append(f"HCP backups: {backup_root} (exists)")
    else:
        lines.append(f"HCP backups: {backup_root} (no backups yet)")

    return ok, lines
