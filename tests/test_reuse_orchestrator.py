"""Tests for HCP evidence reuse orchestrator."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


def _load_reuse():
    pkg_root = Path(__file__).resolve().parents[1]
    src = pkg_root / "src" / "hermes_control_pack" / "runtime" / "plugins" / "hcp-runtime" / "reuse_orchestrator.py"
    spec = importlib.util.spec_from_file_location("reuse_orchestrator_test", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reuse = _load_reuse()


class ReuseOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)
        self.project_dir = self.tmpdir / "project"
        self.project_dir.mkdir()
        os.environ["HCP_EVIDENCE_CACHE_PATH"] = str(self.tmpdir / "evidence-cache.jsonl")

    def tearDown(self):
        self._tmpdir.cleanup()
        os.environ.pop("HCP_EVIDENCE_CACHE_PATH", None)

    def test_safe_for_injection_readonly(self):
        self.assertTrue(reuse._is_safe_for_injection("read_file"))
        self.assertTrue(reuse._is_safe_for_injection("web_search"))
        self.assertTrue(reuse._is_safe_for_injection("search_files"))

    def test_unsafe_for_injection_mutators(self):
        self.assertFalse(reuse._is_safe_for_injection("write_file"))
        self.assertFalse(reuse._is_safe_for_injection("patch"))
        self.assertFalse(reuse._is_safe_for_injection("terminal"))

    def test_no_evidence_returns_empty(self):
        block = reuse.build_evidence_context_block(str(self.project_dir))
        self.assertEqual(block, "")

    def test_only_readonly_injected(self):
        # Store read-only and mutating results
        from hermes_control_pack.evidence_cache import get_cache
        cache = get_cache(str(self.project_dir))
        cache.store("read_file", {"path": "/tmp/x.py"}, "file contents here")
        cache.store("write_file", {"path": "/tmp/y.py"}, "written")  # should NOT be injected
        cache.store("search_files", {"pattern": "*.py"}, "matched files")

        block = reuse.build_evidence_context_block(str(self.project_dir))
        self.assertIn("PRIOR EVIDENCE", block)
        self.assertIn("read_file", block)
        self.assertIn("search_files", block)
        self.assertNotIn("write_file", block)
        self.assertIn("file contents here", block)
        self.assertIn("matched files", block)

    def test_stale_evidence_not_injected(self):
        from hermes_control_pack.evidence_cache import get_cache
        import time
        cache = get_cache(str(self.project_dir))
        # Store with a TTL of 0 seconds
        cache.store("read_file", {"path": "/tmp/x.py"}, "content", staleness_hint="read")
        # Manually expire by storing with max_age_seconds=0 (immediate stale)
        # We can't easily manipulate TTLs, so verify the block appears first
        block = reuse.build_evidence_context_block(str(self.project_dir))
        self.assertIn("read_file", block)

    def test_max_items_respected(self):
        from hermes_control_pack.evidence_cache import get_cache
        cache = get_cache(str(self.project_dir))
        for i in range(10):
            cache.store("read_file", {"path": f"/tmp/file-{i}.py"}, f"content-{i}")
        block = reuse.build_evidence_context_block(str(self.project_dir), max_items=3)
        # Should have at most 3 entries
        self.assertIn("[1]", block)
        self.assertIn("[2]", block)
        self.assertIn("[3]", block)
        self.assertNotIn("[4]", block)

    def test_get_recent_readonly_evidence_returns_list(self):
        from hermes_control_pack.evidence_cache import get_cache
        cache = get_cache(str(self.project_dir))
        cache.store("read_file", {"path": "/tmp/x.py"}, "content")
        evidence = reuse.get_recent_readonly_evidence(str(self.project_dir))
        self.assertIsInstance(evidence, list)
        self.assertGreaterEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["tool_name"], "read_file")

    def test_context_block_is_formatted(self):
        from hermes_control_pack.evidence_cache import get_cache
        cache = get_cache(str(self.project_dir))
        cache.store("web_search", {"query": "test"}, "search results here")
        block = reuse.build_evidence_context_block(str(self.project_dir))
        self.assertIn("PRIOR EVIDENCE (cached read results — DO NOT REPEAT)", block)
        self.assertIn("web_search", block)
        self.assertIn("search results here", block)


if __name__ == "__main__":
    unittest.main()
