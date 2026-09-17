import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "hcp-runtime"


def load_package(name: str, directory: Path):
    spec = importlib.util.spec_from_file_location(
        name, directory / "__init__.py", submodule_search_locations=[str(directory)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ProjectScopedRoutingTests(unittest.TestCase):
    """Project-scoped instructions should match only their project."""

    def test_project_scoped_instruction_matches_only_its_project(self):
        mod = load_package("hcp_project_scope_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as home, \
             tempfile.TemporaryDirectory() as project_a, \
             tempfile.TemporaryDirectory() as project_b:
            os.environ["HERMES_HOME"] = home
            os.chdir(project_a)
            try:
                store = mod.ambient.GlobalStateStore()
                store.record_instruction(
                    {
                        "action": "echo-from-a",
                        "action_type": "respond_exact",
                        "trigger_type": "contains_any",
                        "trigger_patterns": ["trigger-word"],
                        "scope": "project",
                        "project_root": str(Path(project_a).resolve()),
                        "consume_after_success": True,
                    },
                    project_root=str(Path(project_a).resolve()),
                    session_id="session-a",
                )

                # Session A (project_a) — should match
                ctx_a = mod.ambient._pre_llm_call(
                    "session-a",
                    turn_id="t1",
                    user_message="please use the trigger-word now",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertIn("HCP ACTIVE CONTINUITY INSTRUCTION", ctx_a["context"])

                # Session B (project_b) — should NOT match
                os.chdir(project_b)
                ctx_b = mod.ambient._pre_llm_call(
                    "session-b",
                    turn_id="t2",
                    user_message="please use the trigger-word now",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertNotIn("HCP ACTIVE CONTINUITY INSTRUCTION", ctx_b["context"])
            finally:
                os.chdir(original_cwd)
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


class StateDurabilityTests(unittest.TestCase):
    """State operations should be safe against malformed/stale data."""

    def test_malformed_json_degrades_to_defaults(self):
        mod = load_package("hcp_malformed_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.ambient.GlobalStateStore()
                # Corrupt the instructions file
                instructions_file = Path(home) / "hcp" / "global" / "PENDING_INSTRUCTIONS.json"
                instructions_file.parent.mkdir(parents=True, exist_ok=True)
                instructions_file.write_text("{not valid json", encoding="utf-8")

                # Should not crash — degrades to defaults
                items = store.instructions()
                self.assertEqual(items, [])

                # Match on corrupted store should also be safe
                result = store.match("anything")
                self.assertEqual(result, [])
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home

    def test_record_and_update_instruction_idempotent(self):
        mod = load_package("hcp_idempotent_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.ambient.GlobalStateStore()
                item = store.record_instruction(
                    {
                        "action": "greet",
                        "action_type": "respond_exact",
                        "trigger_type": "contains_any",
                        "trigger_patterns": ["hello"],
                        "scope": "global",
                    },
                    session_id="s1",
                )
                item_id = item["id"]

                # Setting completed twice should not crash
                store.update_instruction(item_id, {"status": "completed"})
                store.update_instruction(item_id, {"status": "completed"})

                completed = store.instructions(statuses={"completed"})
                self.assertEqual(len(completed), 1)
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


class TriggerSemanticsTests(unittest.TestCase):
    """Triggers should only fire when their conditions are met."""

    def test_never_trigger_fails_without_patterns(self):
        mod = load_package("hcp_trigger_fail_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.ambient.GlobalStateStore()
                with self.assertRaises(ValueError):
                    store.record_instruction(
                        {
                            "action": "oops",
                            "trigger_type": "contains_any",
                            "trigger_patterns": [],
                            "scope": "global",
                        }
                    )
                with self.assertRaises(ValueError):
                    store.record_instruction(
                        {
                            "action": "oops",
                            "trigger_type": "regex",
                            "trigger_patterns": [],
                            "scope": "global",
                        }
                    )
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home

    def test_always_trigger_fires_every_time(self):
        mod = load_package("hcp_always_trigger_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.ambient.GlobalStateStore()
                store.record_instruction(
                    {
                        "action": "always-on",
                        "action_type": "respond_exact",
                        "trigger_type": "always",
                        "scope": "global",
                        "consume_after_success": False,
                    },
                    session_id="s1",
                )
                first = store.match("anything", session_id="s2")
                self.assertEqual(len(first), 1)
                # Since consume_after_success is False, it should fire again
                second = store.match("something else", session_id="s3")
                self.assertEqual(len(second), 1)
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


class OutsideRepoAmbientTests(unittest.TestCase):
    """HCP must work when Hermes is launched outside the HCP repository."""

    def test_ambient_works_from_unrelated_directory(self):
        mod = load_package("hcp_outside_repo_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as unrelated_dir:
            os.environ["HERMES_HOME"] = home
            try:
                os.chdir(unrelated_dir)
                result = mod.ambient._pre_llm_call(
                    "outside-session",
                    turn_id="t-out",
                    user_message="hello",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertIsNotNone(result)
                self.assertIn("HCP GLOBAL CONTINUITY", result["context"])
            finally:
                os.chdir(original_cwd)
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
