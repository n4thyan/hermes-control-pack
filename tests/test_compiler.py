import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from hermes_control_pack.compiler import build_pack


class CompilerTests(unittest.TestCase):
    def test_build_emits_complete_runtime_pack(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            zpath = td / "sample.zip"
            out = td / "out"
            with zipfile.ZipFile(zpath, "w") as z:
                z.writestr(
                    "root/Misc/hermes.md",
                    "Explore the relevant files before editing. Reproduce root cause, implement, test, review, delegate, and preserve context.",
                )
            idx = build_pack(zpath, out, project_root)
            self.assertEqual(idx["entry_count"], 1)
            expected = [
                ".hermes.md",
                "corpus-index.json",
                "CORPUS_COVERAGE.md",
                "RESEARCH_SIGNALS.md",
                "MECHANISMS.json",
                "MECHANISM_MATRIX.md",
                "hcp-manifest.json",
                "skills/verification-gate/SKILL.md",
                "skills/ui-visual-verification/SKILL.md",
                "bundles/hcp-coding.yaml",
                "bundles/hcp-afk.yaml",
                "souls/balanced.md",
                "plugins/hcp-runtime/plugin.yaml",
                "plugins/hcp-runtime/__init__.py",
                "plugins/context_engine/hcp-continuity/plugin.yaml",
            ]
            for rel in expected:
                self.assertTrue((out / rel).exists(), rel)
            manifest = json.loads((out / "hcp-manifest.json").read_text())
            self.assertEqual(manifest["hcp_version"], "2.0.0")
            self.assertEqual(manifest["corpus_fingerprint"], idx["source_sha256"])
            self.assertIn(".hermes.md", manifest["artifacts"])
            self.assertGreaterEqual(manifest["mechanism_count"], 1)

    def test_packaged_runtime_assets_match_reviewable_top_level_assets(self):
        root = Path(__file__).resolve().parents[1]
        for group in ("skills", "bundles", "souls", "plugins"):
            public = root / group
            packaged = root / "src" / "hermes_control_pack" / "runtime" / group
            def source_files(base: Path):
                return {
                    p.relative_to(base).as_posix(): p.read_bytes()
                    for p in base.rglob("*")
                    if p.is_file()
                    and "__pycache__" not in p.parts
                    and p.suffix not in {".pyc", ".pyo"}
                }

            public_files = source_files(public)
            packaged_files = source_files(packaged)
            self.assertEqual(public_files, packaged_files, group)


if __name__ == "__main__":
    unittest.main()
