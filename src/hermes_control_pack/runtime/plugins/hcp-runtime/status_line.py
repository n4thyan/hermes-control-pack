"""Truthful startup status-line builder for the HCP runtime plugin.

Called from ambient._on_session_start on the first turn of a fresh
Hermes process. Produces a single concise line showing HCP version,
runtime health, and continuity status — never faked.

The line format is:

    HCP <version> ENABLED | runtime: <status> | continuity: <status> | updates: <status>

Examples:
    HCP 2.2.0 ENABLED | runtime synced | continuity ready
    HCP 2.2.0 ENABLED | WARNING: runtime mismatch
    HCP 2.2.0 ENABLED | update status: unreachable
"""
from __future__ import annotations

from pathlib import Path
import filecmp
import os


def _hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".hermes").resolve()


def _installed_runtime_version(hermes_home: Path) -> str | None:
    plugin_yaml = hermes_home / "plugins" / "hcp-runtime" / "plugin.yaml"
    if not plugin_yaml.exists():
        return None
    try:
        for line in plugin_yaml.read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def _bundled_runtime_version() -> str | None:
    """Read version from the HCP package metadata (what we *intend* to install)."""
    try:
        from hermes_control_pack import __version__
        return __version__
    except Exception:
        return None


def _check_runtime_sync(hermes_home: Path) -> tuple[str, str]:
    """Compare installed runtime files against bundled source.

    Returns (status_code, detail). status_code is short enough for
    the status line; detail is a human description.
    """
    plugin_dir = hermes_home / "plugins" / "hcp-runtime"
    if not plugin_dir.exists():
        return ("not-installed", "runtime plugin not installed")

    installed_version = _installed_runtime_version(hermes_home)
    bundled_version = _bundled_runtime_version()

    # Check for stale backup dirs (the old shadowing bug)
    stale_backups = []
    plugins_dir = hermes_home / "plugins"
    if plugins_dir.is_dir():
        for child in plugins_dir.iterdir():
            if child.is_dir() and ".hcp-backup-" in child.name:
                stale_backups.append(child.name)
    if stale_backups:
        return ("stale-backups",
                f"stale backup dirs in plugins/: {stale_backups}")

    if installed_version != bundled_version:
        return ("version-mismatch",
                f"installed {installed_version} vs bundled {bundled_version}")

    # Spot-check a few key files for content drift
    try:
        # hcp-runtime dir has a hyphen so we can't import it directly; load by path
        import importlib.util
        state_store_path = Path(__file__).resolve().parent / "state_store.py"
        if state_store_path.exists():
            bundled_root = Path(__file__).resolve().parent
            drift_files = []
            for name in ("core.py", "schemas.py", "tools.py", "ambient.py"):
                installed = plugin_dir / name
                bundled = bundled_root / name
                if installed.exists() and bundled.exists():
                    if not filecmp.cmp(installed, bundled, shallow=False):
                        drift_files.append(name)
            if drift_files:
                return ("file-drift", f"content drift in: {', '.join(drift_files)}")
    except Exception:
        pass

    return ("synced", "runtime synced")


def _check_continuity(hermes_home: Path) -> tuple[str, str]:
    """Check that global continuity state is initialized."""
    global_store = hermes_home / "hcp" / "GLOBAL_STATE.json"
    if global_store.exists():
        return ("ready", "continuity ready")

    # Check the old-style pending instructions store
    pending = hermes_home / "hcp" / "global" / "PENDING_INSTRUCTIONS.json"
    if pending.exists():
        return ("ready", "continuity ready")

    # Global state not yet created — first run
    return ("uninitialized", "continuity uninitialized (first run)")


def _check_update_status() -> tuple[str, str]:
    """Lightweight cached update check (no network on startup)."""
    # Read last known update status from a cached file
    hermes_home = _hermes_home()
    cache_file = hermes_home / "hcp" / ".update-cache.json"
    if not cache_file.exists():
        return ("unknown", "update status: not checked")
    try:
        import json
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        latest = data.get("latest_version", "unknown")
        cached_at = data.get("checked_at", "unknown")
        current = data.get("current_version", "unknown")
        if latest == current:
            return ("current", f"up to date (checked {cached_at})")
        return ("available", f"update available: {latest} (checked {cached_at})")
    except Exception:
        return ("error", "update status: error reading cache")


def build_startup_line(hermes_home: Path | str | None = None) -> str:
    """Build the one-line HCP startup status.

    Always lightweight: no network, no blocking operations. Just
    filesystem checks that complete in milliseconds.
    """
    if hermes_home is None:
        hermes_home = _hermes_home()
    else:
        hermes_home = Path(hermes_home).expanduser().resolve()

    from hermes_control_pack import __version__
    parts: list[str] = [f"HCP {__version__} ENABLED"]
    rt_status, rt_detail = _check_runtime_sync(hermes_home)
    if rt_status == "synced":
        parts.append("runtime synced")
    elif rt_status == "not-installed":
        parts.append("WARNING: runtime not installed")
    elif rt_status == "version-mismatch":
        parts.append(f"WARNING: {rt_detail}")
    elif rt_status == "stale-backups":
        parts.append(f"WARNING: {rt_detail}")
    elif rt_status == "file-drift":
        parts.append(f"WARNING: {rt_detail}")
    else:
        parts.append(f"WARNING: {rt_detail}")

    cont_status, cont_detail = _check_continuity(hermes_home)
    if cont_status == "ready":
        parts.append("continuity ready")
    else:
        parts.append(cont_detail)

    upd_status, upd_detail = _check_update_status()
    parts.append(upd_detail)

    return " | ".join(parts)


if __name__ == "__main__":
    print(build_startup_line())
