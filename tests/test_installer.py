import tempfile
import unittest
from pathlib import Path

from hermes_control_pack.installer import (
    SOUL_BEGIN, SOUL_END, install_pack,
    _backup_dir, _backup_file, _cleanup_stale_plugin_backups,
    _hermes_backup_root,
)


class InstallerTests(unittest.TestCase):
    def _build(self, root: Path) -> Path:
        build = root / "build"
        (build / "skills" / "x").mkdir(parents=True)
        (build / "bundles").mkdir()
        (build / "souls").mkdir()
        (build / "plugins" / "hcp-runtime").mkdir(parents=True)
        (build / "plugins" / "context_engine" / "hcp-continuity").mkdir(parents=True)
        (build / ".hermes.md").write_text("kernel", encoding="utf-8")
        (build / "corpus-index.json").write_text("{}", encoding="utf-8")
        (build / "MECHANISMS.json").write_text("{}", encoding="utf-8")
        (build / "hcp-manifest.json").write_text(
            '{"corpus_fingerprint":"abc","hcp_version":"2.0.0"}', encoding="utf-8"
        )
        (build / "skills" / "x" / "SKILL.md").write_text("skill", encoding="utf-8")
        (build / "bundles" / "x.yaml").write_text("name: x\nskills: [x]\n", encoding="utf-8")
        (build / "souls" / "balanced.md").write_text("balanced soul", encoding="utf-8")
        (build / "souls" / "coder.md").write_text("coder soul", encoding="utf-8")
        (build / "plugins" / "hcp-runtime" / "plugin.yaml").write_text("name: hcp-runtime\n", encoding="utf-8")
        (build / "plugins" / "hcp-runtime" / "__init__.py").write_text("def register(ctx): pass\n", encoding="utf-8")
        (build / "plugins" / "context_engine" / "hcp-continuity" / "plugin.yaml").write_text(
            "name: hcp-continuity\n", encoding="utf-8"
        )
        return build

    def test_install_is_idempotent_and_installs_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "hermes"
            first = install_pack(build, project, home, soul_profile="balanced")
            second = install_pack(build, project, home, soul_profile="balanced")
            self.assertTrue((project / ".hermes.md").exists())
            self.assertTrue((project / ".hcp" / "state" / "TASK_STATE.json").exists())
            self.assertTrue((home / "skills" / "x" / "SKILL.md").exists())
            self.assertTrue((home / "skill-bundles" / "x.yaml").exists())
            self.assertTrue((home / "plugins" / "hcp-runtime" / "plugin.yaml").exists())
            soul = (home / "SOUL.md").read_text()
            self.assertIn(SOUL_BEGIN, soul)
            self.assertIn("balanced soul", soul)
            self.assertIn(SOUL_END, soul)
            self.assertTrue(any("Already current" in line for line in second))
            self.assertGreater(len(first), 0)

    def test_install_from_packaged_runtime_needs_no_corpus_build(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            home = root / "hermes"
            install_pack(
                None, project, home,
                install_context=False,
                soul_profile="balanced",
                install_context_engine=True,
            )
            self.assertTrue((home / "plugins" / "hcp-runtime" / "plugin.yaml").exists())
            self.assertTrue((home / "plugins" / "context_engine" / "hcp-continuity" / "plugin.yaml").exists())
            self.assertTrue((home / "skills" / "control-orchestrator" / "SKILL.md").exists())
            self.assertTrue((project / ".hcp" / "state" / "TASK_STATE.json").exists())

    def test_install_optional_continuity_engine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            home = root / "home"
            install_pack(build, root / "project", home, install_context_engine=True)
            self.assertTrue((home / "plugins" / "context_engine" / "hcp-continuity" / "plugin.yaml").exists())

    def test_install_protects_context_but_merges_existing_soul(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()
            (project / ".hermes.md").write_text("user rules", encoding="utf-8")
            (home / "SOUL.md").write_text("my existing personality\n", encoding="utf-8")
            messages = []
            with self.assertRaises(FileExistsError):
                install_pack(build, project, home, soul_profile="balanced")
            messages = install_pack(build, project, home, force=True, soul_profile="balanced")
            self.assertEqual((project / ".hermes.md").read_text(), "kernel")
            soul = (home / "SOUL.md").read_text()
            self.assertIn("my existing personality", soul)
            self.assertIn("balanced soul", soul)
            self.assertIn(SOUL_BEGIN, soul)
            self.assertTrue(any("Backed up existing project context" in m for m in messages))
            # Backups now go to .hcp-backups, NOT inside the plugin dir or hermes_home root
            self.assertTrue(list((home / ".hcp-backups").glob(".hermes.md.hcp-backup-*")))
            self.assertTrue(list((home / ".hcp-backups").glob("SOUL.md.hcp-backup-*")))

    def test_switching_soul_profile_replaces_only_managed_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "home"
            home.mkdir()
            (home / "SOUL.md").write_text("custom preface\n", encoding="utf-8")
            install_pack(build, project, home, install_context=False, soul_profile="balanced")
            install_pack(build, project, home, install_context=False, soul_profile="coder", force=True)
            soul = (home / "SOUL.md").read_text()
            self.assertIn("custom preface", soul)
            self.assertNotIn("balanced soul", soul)
            self.assertEqual(soul.count(SOUL_BEGIN), 1)
            self.assertIn("coder soul", soul)

    def test_generated_python_cache_does_not_break_plugin_idempotence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "home"
            install_pack(build, project, home, install_context=False)
            cache = home / "plugins" / "hcp-runtime" / "__pycache__"
            cache.mkdir()
            (cache / "plugin.pyc").write_bytes(b"generated")
            messages = install_pack(build, project, home, install_context=False)
            self.assertTrue(any("Already current runtime plugin" in m for m in messages))

    def test_backups_go_to_hcp_backups_not_plugins(self):
        """Backups must be stored in .hcp-backups/, never inside plugins/."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "hermes"
            messages = install_pack(build, project, home, soul_profile="balanced")

            # Create a stale old-style backup dir inside plugins/ to simulate
            # a leftover from a previous buggy installer run.
            stale_backup = home / "plugins" / "hcp-runtime.hcp-backup-20250101-000000"
            stale_backup.mkdir(parents=True)
            (stale_backup / "plugin.yaml").write_text("name: hcp-runtime\nversion: 2.0.0\n", encoding="utf-8")
            (stale_backup / "__init__.py").write_text("# stale backup", encoding="utf-8")

            # Now run install with force=True to trigger the cleanup path
            messages2 = install_pack(build, project, home, soul_profile="balanced", force=True)

            # The stale backup should be removed
            self.assertFalse(stale_backup.exists(),
                             "Stale backup dir inside plugins/ should have been cleaned up")
            self.assertTrue(any("Cleaned up" in m for m in messages2),
                            "Should report cleanup of stale backup dirs")

            # New backups should go to .hcp-backups/
            backup_dirs = home.glob("plugins/*.hcp-backup-*")
            self.assertEqual(list(backup_dirs), [],
                             "No backup dirs should exist inside plugins/")

    def test_plugin_scanner_dedup_does_not_pick_up_backup_dirs(self):
        """Simulate Hermes' plugin discovery dedup with stale backup dirs present.

        This is the core regression test for the bug where
        hcp-runtime.hcp-backup-* (with name: hcp-runtime) inside plugins/
        shadows the real hcp-runtime plugin during plugin discovery.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "hermes"
            install_pack(build, project, home, soul_profile="balanced")

            # Simulate a stale backup with version 2.0.0 and a conflicting schema
            stale_backup = home / "plugins" / "hcp-runtime.hcp-backup-20300101-000000"
            stale_backup.mkdir(parents=True)
            # Same name, different version — this is what triggers the dedup collision
            (stale_backup / "plugin.yaml").write_text(
                "name: hcp-runtime\nversion: 2.0.0\n", encoding="utf-8"
            )
            stale_init = stale_backup / "__init__.py"
            stale_init.write_text("# STALE BACKUP CONTENT", encoding="utf-8")

            # Run install again with force — should clean up stale backup
            # and NOT leave any backup dirs inside plugins/
            install_pack(build, project, home, soul_profile="balanced", force=True)

            # Verify no stale backup directories remain in plugins/
            remaining = list(home.glob("plugins/hcp-runtime.hcp-backup-*"))
            self.assertEqual(remaining, [],
                             f"Stale backup dirs should have been cleaned: {remaining}")

            # Verify the real plugin is intact and not shadowed
            self.assertTrue((home / "plugins" / "hcp-runtime" / "plugin.yaml").exists())

    def test_backup_dir_uses_hermes_backups_path(self):
        """_backup_dir should create backups in <hermes_home>/.hcp-backups, not in plugins/."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = root / "hermes"
            home.mkdir()
            plugins_dir = home / "plugins"
            plugins_dir.mkdir()

            # Create a real plugin dir
            plugin_dir = plugins_dir / "hcp-runtime"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.yaml").write_text("name: hcp-runtime\n", encoding="utf-8")

            # Backup should go to .hcp-backups, NOT next to the plugin
            messages = []
            backup = _backup_dir(plugin_dir, home, messages, "test plugin")

            backup_parent = backup.parent
            expected_root = _hermes_backup_root(home)
            self.assertEqual(backup_parent, expected_root)
            self.assertIn(".hcp-backups", str(backup))
            self.assertNotIn("plugins", str(backup))

    def test_backup_file_uses_hermes_backups_path(self):
        """_backup_file should create backups in <hermes_home>/.hcp-backups, not in plugins/."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = root / "hermes"
            home.mkdir()

            # Create a file to backup
            test_file = home / "SOUL.md"
            test_file.write_text("original content", encoding="utf-8")

            messages = []
            backup = _backup_file(test_file, home, messages, "SOUL.md")

            expected_root = _hermes_backup_root(home)
            self.assertEqual(backup.parent, expected_root)
            self.assertIn(".hcp-backups", str(backup))
            # The backup should not be inside plugins/
            self.assertNotIn("plugins", str(backup))


if __name__ == "__main__":
    unittest.main()
