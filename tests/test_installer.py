import tempfile
import unittest
from pathlib import Path

from hermes_control_pack.installer import install_pack


class InstallerTests(unittest.TestCase):
    def _build(self, root: Path) -> Path:
        build = root / "build"
        (build / "skills" / "x").mkdir(parents=True)
        (build / "bundles").mkdir()
        (build / ".hermes.md").write_text("kernel", encoding="utf-8")
        (build / "corpus-index.json").write_text("{}", encoding="utf-8")
        (build / "hcp-manifest.json").write_text('{"corpus_fingerprint":"abc"}', encoding="utf-8")
        (build / "skills" / "x" / "SKILL.md").write_text("skill", encoding="utf-8")
        (build / "bundles" / "x.yaml").write_text("name: x\nskills: [x]\n", encoding="utf-8")
        return build

    def test_install_is_idempotent_and_installs_bundles(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            home = root / "hermes"
            first = install_pack(build, project, home)
            second = install_pack(build, project, home)
            self.assertTrue((project / ".hermes.md").exists())
            self.assertTrue((home / "skills" / "x" / "SKILL.md").exists())
            self.assertTrue((home / "skill-bundles" / "x.yaml").exists())
            self.assertTrue(any("Already current" in line for line in second))
            self.assertGreater(len(first), 0)

    def test_install_protects_differing_existing_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = self._build(root)
            project = root / "project"
            project.mkdir()
            (project / ".hermes.md").write_text("user rules", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install_pack(build, project, root / "home")
            messages = install_pack(build, project, root / "home", force=True)
            self.assertEqual((project / ".hermes.md").read_text(), "kernel")
            self.assertTrue(any("Backed up existing project context" in m for m in messages))
            self.assertTrue(list(project.glob(".hermes.md.hcp-backup-*")))


if __name__ == "__main__":
    unittest.main()
