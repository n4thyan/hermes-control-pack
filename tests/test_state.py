import tempfile
import unittest
from pathlib import Path

from hermes_control_pack.state import ProjectStateStore


class StateTests(unittest.TestCase):
    def test_state_survives_reopen_and_renders_continuity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = ProjectStateStore(root)
            store.update("task", {
                "objective": "Finish renderer",
                "phase": "VERIFY",
                "acceptance_criteria": ["room loads", "hitboxes work"],
                "next_steps": ["test room B"],
            })
            store.update("project", {"do_not_regress": ["shell sizing"]})
            store.record_decision("Use atlas renderer", rationale="Existing assets are atlas based", session_id="s1")
            store.record_evidence("npm test", result="pass", kind="test", session_id="s1")

            reopened = ProjectStateStore(root)
            self.assertEqual(reopened.read_task()["objective"], "Finish renderer")
            self.assertEqual(reopened.decisions(1)[0]["decision"], "Use atlas renderer")
            self.assertEqual(reopened.evidence(1)[0]["result"], "pass")
            rendered = reopened.render_context()
            self.assertIn("Finish renderer", rendered)
            self.assertIn("shell sizing", rendered)
            self.assertIn("Use atlas renderer", rendered)

    def test_deep_merge_preserves_existing_fields(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStateStore(Path(td))
            store.update("task", {"objective": "A", "next_steps": ["x"]})
            store.update("task", {"phase": "IMPLEMENT"})
            task = store.read_task()
            self.assertEqual(task["objective"], "A")
            self.assertEqual(task["next_steps"], ["x"])
            self.assertEqual(task["phase"], "IMPLEMENT")

    def test_trace_is_observable_event_log(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStateStore(Path(td))
            store.trace("completion_gate_continue", {"missing": ["tests"]})
            event = store.trace_events(1)[0]
            self.assertEqual(event["event"], "completion_gate_continue")
            self.assertEqual(event["data"]["missing"], ["tests"])

    def test_state_is_privately_ignored_in_git_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git" / "info").mkdir(parents=True)
            store = ProjectStateStore(root)
            store.ensure()
            exclude = (root / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("/.hcp/", exclude)
            self.assertFalse((root / ".hcp" / ".gitignore").exists())


if __name__ == "__main__":
    unittest.main()
