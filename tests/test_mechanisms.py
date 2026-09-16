import tempfile
import unittest
import zipfile
from pathlib import Path

from hermes_control_pack.analyzer import mechanism_coverage, mechanism_markdown
from hermes_control_pack.corpus import build_index


class MechanismTests(unittest.TestCase):
    def test_mechanisms_are_attributed_across_source_groups(self):
        with tempfile.TemporaryDirectory() as td:
            zpath = Path(td) / "sample.zip"
            with zipfile.ZipFile(zpath, "w") as z:
                z.writestr("root/OpenAI/a.md", "Before editing inspect relevant files. Verify with tests and evidence before finishing.")
                z.writestr("root/Anthropic/b.md", "Inspect the codebase before editing. Verification and tests are required before declaring success.")
            idx = build_index(zpath)
            cov = mechanism_coverage(idx)
            self.assertGreaterEqual(cov["inspect_before_edit"]["source_group_count"], 2)
            self.assertGreaterEqual(cov["evidence_gated_completion"]["source_group_count"], 2)
            report = mechanism_markdown(idx)
            self.assertIn("inspect_before_edit", report)
            self.assertIn("runtime+system", report)


if __name__ == "__main__":
    unittest.main()
