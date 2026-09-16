import tempfile
import unittest
import zipfile
from pathlib import Path

from hermes_control_pack.corpus import build_index


class CorpusTests(unittest.TestCase):
    def test_zip_index_scans_all_entries_and_strips_wrapper_for_grouping(self):
        with tempfile.TemporaryDirectory() as td:
            zpath = Path(td) / "sample.zip"
            with zipfile.ZipFile(zpath, "w") as z:
                z.writestr("root/OpenAI/a.md", "Inspect the repo, implement, then verify with tests.")
                z.writestr("root/Anthropic/b.txt", "Reproduce the failure and find the root cause.")
                z.writestr("root/assets/x.bin", b"\x00\x01\x02")
            idx = build_index(zpath)
            self.assertEqual(idx["entry_count"], 3)
            self.assertEqual(idx["text_entry_count"], 2)
            self.assertEqual(idx["top_level_counts"]["OpenAI"], 1)
            self.assertEqual(idx["top_level_counts"]["Anthropic"], 1)
            self.assertGreater(idx["category_hits"]["verification"], 0)
            self.assertGreater(idx["category_hits"]["debugging"], 0)
            self.assertEqual(len(idx["source_sha256"]), 64)

    def test_directory_fingerprint_is_content_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "OpenAI").mkdir()
            p = root / "OpenAI" / "a.md"
            p.write_text("verify it", encoding="utf-8")
            first = build_index(root)["source_sha256"]
            second = build_index(root)["source_sha256"]
            self.assertEqual(first, second)
            p.write_text("verify it carefully", encoding="utf-8")
            third = build_index(root)["source_sha256"]
            self.assertNotEqual(first, third)


if __name__ == "__main__":
    unittest.main()
