import unittest

from hermes_control_pack.analyzer import cross_source_coverage, signal_markdown


class AnalyzerTests(unittest.TestCase):
    def test_cross_source_coverage_counts_groups_files_and_hits(self):
        index = {
            "source_sha256": "a" * 64,
            "entry_count": 3,
            "text_entry_count": 3,
            "total_words": 10,
            "top_level_counts": {"OpenAI": 2, "Anthropic": 1},
            "category_hits": {"verification": 6},
            "provider_category_hits": {
                "OpenAI": {"verification": 4},
                "Anthropic": {"verification": 2},
            },
            "provider_category_files": {
                "OpenAI": {"verification": 2},
                "Anthropic": {"verification": 1},
            },
        }
        cov = cross_source_coverage(index)
        self.assertEqual(cov["verification"], {"source_groups": 2, "files": 3, "hits": 6})
        report = signal_markdown(index)
        self.assertIn("Behavior-family coverage", report)
        self.assertIn("`verification`", report)


if __name__ == "__main__":
    unittest.main()
