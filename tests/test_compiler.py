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
                z.writestr("root/Misc/hermes.md", "Explore, implement, test, review and delegate.")
            idx = build_pack(zpath, out, project_root)
            self.assertEqual(idx["entry_count"], 1)
            expected = [
                ".hermes.md",
                "corpus-index.json",
                "CORPUS_COVERAGE.md",
                "RESEARCH_SIGNALS.md",
                "hcp-manifest.json",
                "skills/verification-gate/SKILL.md",
                "skills/ui-visual-verification/SKILL.md",
                "bundles/hcp-coding.yaml",
                "bundles/hcp-afk.yaml",
            ]
            for rel in expected:
                self.assertTrue((out / rel).exists(), rel)
            manifest = json.loads((out / "hcp-manifest.json").read_text())
            self.assertEqual(manifest["hcp_version"], "1.0.0")
            self.assertEqual(manifest["corpus_fingerprint"], idx["source_sha256"])
            self.assertIn(".hermes.md", manifest["artifacts"])

    def test_packaged_runtime_assets_match_reviewable_top_level_assets(self):
        root = Path(__file__).resolve().parents[1]
        for group in ("skills", "bundles"):
            public = root / group
            packaged = root / "src" / "hermes_control_pack" / "runtime" / group
            public_files = {p.relative_to(public).as_posix(): p.read_bytes() for p in public.rglob("*") if p.is_file()}
            packaged_files = {p.relative_to(packaged).as_posix(): p.read_bytes() for p in packaged.rglob("*") if p.is_file()}
            self.assertEqual(public_files, packaged_files, group)


if __name__ == "__main__":
    unittest.main()
