"""Tests for the HCP Evidence Cache (tool_evidence_reuse mechanism)."""
import tempfile
import unittest
from pathlib import Path

from hermes_control_pack.evidence_cache import (
    EvidenceCache, _make_evidence_key, _normalize_args, get_cache,
)


class EvidenceCacheTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)
        self.project_dir = self.tmpdir / "project"
        self.project_dir.mkdir()
        import os
        self._orig_cache_path = os.environ.get("HCP_EVIDENCE_CACHE_PATH")
        os.environ["HCP_EVIDENCE_CACHE_PATH"] = str(self.tmpdir / "evidence-cache.jsonl")
        self.cache = EvidenceCache(str(self.project_dir))

    def tearDown(self):
        self._tmpdir.cleanup()
        import os
        if self._orig_cache_path is None:
            os.environ.pop("HCP_EVIDENCE_CACHE_PATH", None)
        else:
            os.environ["HCP_EVIDENCE_CACHE_PATH"] = self._orig_cache_path

    def test_make_evidence_key_is_deterministic(self):
        key1 = _make_evidence_key("read_file", {"path": "/tmp/test.py"})
        key2 = _make_evidence_key("read_file", {"path": "/tmp/test.py"})
        key3 = _make_evidence_key("read_file", {"path": "/tmp/other.py"})
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

    def test_normalize_args_strips_session_noise(self):
        normalized = _normalize_args({
            "command": "git status",
            "session_id": "abc",
            "task_id": "xyz",
            "user_message": "hello",
        })
        self.assertNotIn("session_id", normalized)
        self.assertNotIn("task_id", normalized)
        self.assertEqual(normalized["command"], "git status")

    def test_store_and_lookup(self):
        self.cache.store("read_file", {"path": "/tmp/test.py"}, "content")
        result = self.cache.lookup("read_file", {"path": "/tmp/test.py"})
        self.assertIsNotNone(result)
        self.assertEqual(result["result"], "content")

    def test_lookup_returns_none_for_stale_entries(self):
        self.cache.store("read_file", {"path": "/tmp/test.py"}, "content")
        result = self.cache.lookup("read_file", {"path": "/tmp/test.py"}, max_age_seconds=0)
        self.assertIsNone(result)

    def test_lookup_returns_none_for_missing_entries(self):
        result = self.cache.lookup("read_file", {"path": "/tmp/nonexistent.py"})
        self.assertIsNone(result)

    def test_project_isolation(self):
        cache1 = EvidenceCache(str(self.project_dir))
        project_dir2 = self.tmpdir / "project2"
        project_dir2.mkdir()
        cache2 = EvidenceCache(str(project_dir2))
        cache1.store("read_file", {"path": "/tmp/test.py"}, "output1")
        result = cache2.lookup("read_file", {"path": "/tmp/test.py"})
        self.assertIsNone(result)

    def test_invalidate(self):
        self.cache.store("read_file", {"path": "/tmp/a.py"}, "output1")
        self.cache.store("read_file", {"path": "/tmp/b.py"}, "output2")
        count = self.cache.invalidate(tool_name="read_file")
        self.assertEqual(count, 2)
        self.assertIsNone(self.cache.lookup("read_file", {"path": "/tmp/a.py"}))
        self.assertIsNone(self.cache.lookup("read_file", {"path": "/tmp/b.py"}))

    def test_invalidate_by_project(self):
        cache1 = EvidenceCache(str(self.project_dir))
        project_dir2 = self.tmpdir / "project2"
        project_dir2.mkdir()
        cache2 = EvidenceCache(str(project_dir2))
        cache1.store("read_file", {"path": "/tmp/a.py"}, "output1")
        cache2.store("read_file", {"path": "/tmp/b.py"}, "output2")
        # Invalidate only cache1's project
        cache1.invalidate(project_root=str(self.project_dir))
        self.assertIsNone(cache1.lookup("read_file", {"path": "/tmp/a.py"}))
        # cache2 should still have its entry
        self.assertIsNotNone(cache2.lookup("read_file", {"path": "/tmp/b.py"}))

    def test_factory_get_cache(self):
        cache = get_cache(str(self.project_dir))
        self.assertEqual(cache.project_root, str(Path(self.project_dir).resolve()))

    def test_max_entries_pruning(self):
        cache = EvidenceCache(str(self.project_dir), max_entries=5)
        for i in range(10):
            cache.store("read_file", {"path": f"/tmp/file-{i}.py"}, f"output-{i}")
        # Should have pruned to max_entries=5
        all_entries = cache._read_all()
        self.assertEqual(len(all_entries), 5)
        # The oldest entries should be gone
        self.assertIsNone(cache.lookup("read_file", {"path": "/tmp/file-0.py"}))
        self.assertIsNotNone(cache.lookup("read_file", {"path": "/tmp/file-9.py"}))


if __name__ == "__main__":
    unittest.main()
