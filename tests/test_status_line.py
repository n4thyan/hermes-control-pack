"""Tests for HCP startup status-line builder."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_status_line():
    """Load status_line module despite hyphenated directory name."""
    # The runtime plugin dir is named hcp-runtime (with a hyphen), which
    # cannot be a Python module name. Load by file path instead.
    pkg_root = Path(__file__).resolve().parents[1]
    src = pkg_root / "src" / "hermes_control_pack" / "runtime" / "plugins" / "hcp-runtime" / "status_line.py"
    spec = importlib.util.spec_from_file_location("hcp_status_line", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


status_line = _load_status_line()
build_startup_line = status_line.build_startup_line


class StartupStatusLineTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)
        self.home = self.tmpdir / "hermes"
        self.home.mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _setup_plugin(self, version="2.2.0"):
        plugin_dir = self.home / "plugins" / "hcp-runtime"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text(
            "name: hcp-runtime\nversion: {}\n".format(version)
        )
        # Copy real bundled files so drift detection passes.
        # Use binary copy to preserve exact line endings — write_text() on
        # Windows converts LF→CRLF, which would falsely trigger drift.
        src_root = Path(__file__).resolve().parents[1] / "src" / "hermes_control_pack" / "runtime" / "plugins" / "hcp-runtime"
        if src_root.exists():
            for f in ("__init__.py", "core.py", "schemas.py", "tools.py", "ambient.py", "state_store.py"):
                src_file = src_root / f
                if src_file.exists():
                    (plugin_dir / f).write_bytes(src_file.read_bytes())
                else:
                    (plugin_dir / f).write_bytes(b"placeholder\n")
        else:
            for f in ("__init__.py", "core.py", "schemas.py", "tools.py", "ambient.py"):
                (plugin_dir / f).write_bytes(b"placeholder\n")
            (plugin_dir / "state_store.py").write_bytes(b"placeholder\n")

    def test_line_contains_version_and_enabled(self):
        self._setup_plugin()
        line = build_startup_line(self.home)
        self.assertIn("HCP 2.2.0", line)
        self.assertIn("ENABLED", line)

    def test_synced_runtime(self):
        self._setup_plugin()
        line = build_startup_line(self.home)
        self.assertIn("runtime synced", line)
        self.assertNotIn("WARNING", line)

    def test_version_mismatch_warning(self):
        self._setup_plugin(version="2.1.0")
        line = build_startup_line(self.home)
        self.assertIn("WARNING: installed 2.1.0 vs bundled 2.2.0", line)

    def test_not_installed_warning(self):
        # No plugin at all
        line = build_startup_line(self.home)
        self.assertIn("WARNING", line)
        self.assertIn("not installed", line)

    def test_stale_backup_detected(self):
        self._setup_plugin()
        # Create stale backup dir
        stale = self.home / "plugins" / "hcp-runtime.hcp-backup-20200101-000000"
        stale.mkdir(parents=True)
        (stale / "plugin.yaml").write_text("name: hcp-runtime\nversion: 2.1.0\n")
        line = build_startup_line(self.home)
        self.assertIn("WARNING", line)
        self.assertIn("stale backup", line)

    def test_continuity_uninitialized_first_run(self):
        self._setup_plugin()
        line = build_startup_line(self.home)
        self.assertIn("continuity", line.lower())
        self.assertIn("uninitialized", line)

    def test_continuity_ready(self):
        self._setup_plugin()
        # Create global state
        gcp_dir = self.home / "hcp" / "global"
        gcp_dir.mkdir(parents=True)
        (gcp_dir / "PENDING_INSTRUCTIONS.json").write_text("[]\n")
        line = build_startup_line(self.home)
        self.assertIn("continuity ready", line)

    def test_update_status_unknown_when_no_cache(self):
        self._setup_plugin()
        line = build_startup_line(self.home)
        self.assertIn("not checked", line)

    def test_no_fakery_current_version(self):
        """The status line must never claim 'latest' unless proven so."""
        self._setup_plugin()
        line = build_startup_line(self.home)
        self.assertNotIn("latest", line.lower())
        self.assertNotIn("up to date", line.lower())

    def test_line_is_single_line(self):
        self._setup_plugin()
        (self.home / "hcp" / "global").mkdir(parents=True)
        (self.home / "hcp" / "global" / "PENDING_INSTRUCTIONS.json").write_text("[]\n")
        line = build_startup_line(self.home)
        self.assertEqual(len(line.strip().split("\n")), 1)


if __name__ == "__main__":
    unittest.main()
