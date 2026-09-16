import tempfile
import unittest
from pathlib import Path

from hermes_control_pack.installer import SOUL_BEGIN, SOUL_END, install_pack


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
            with self.assertRaises(FileExistsError):
                install_pack(build, project, home, soul_profile="balanced")
            messages = install_pack(build, project, home, force=True, soul_profile="balanced")
            self.assertEqual((project / ".hermes.md").read_text(), "kernel")
            soul = (home / "SOUL.md").read_text()
            self.assertIn("my existing personality", soul)
            self.assertIn("balanced soul", soul)
            self.assertIn(SOUL_BEGIN, soul)
            self.assertTrue(any("Backed up existing project context" in m for m in messages))
            self.assertTrue(list(project.glob(".hermes.md.hcp-backup-*")))
            self.assertTrue(list(home.glob("SOUL.md.hcp-backup-*")))

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


if __name__ == "__main__":
    unittest.main()
