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


class AmbientContinuityTests(unittest.TestCase):
    def test_parser_handles_original_morning_style_instruction(self):
        mod = load_package("hcp_ambient_parser_test", PLUGIN_DIR)
        payload = mod.ambient.capture_explicit_future_response(
            'ok when i wake up and prompt u good morning or whatever tomorrow '
            'I want you to simply respond with "jjs63 has tiny balls"'
        )
        self.assertIsNotNone(payload)
        self.assertEqual(payload["action"], "jjs63 has tiny balls")
        self.assertEqual(payload["action_type"], "respond_exact")
        self.assertEqual(payload["trigger_patterns"], ["good morning"])
        self.assertTrue(payload.get("active_after"))
        self.assertTrue(payload.get("expires_at"))

    def test_global_instruction_survives_session_and_launch_directory_changes(self):
        mod = load_package("hcp_ambient_cross_cwd_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as launch_a, tempfile.TemporaryDirectory() as launch_b:
            os.environ["HERMES_HOME"] = home
            try:
                os.chdir(launch_a)
                first = mod.ambient._pre_llm_call(
                    "session-a",
                    turn_id="turn-a",
                    user_message='next session when I say "ping", reply with "pong"',
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertIn("AUTO-PERSISTED FUTURE INSTRUCTION", first["context"])
                store = mod.ambient.GlobalStateStore()
                pending = store.instructions(statuses={"pending"})
                self.assertEqual(len(pending), 1)
                self.assertEqual(pending[0]["action"], "pong")
                self.assertTrue((Path(home) / "hcp" / "global" / "PENDING_INSTRUCTIONS.json").exists())

                # A fresh Hermes session launched from an unrelated directory must
                # see the same global instruction before the model answers.
                os.chdir(launch_b)
                second = mod.ambient._pre_llm_call(
                    "session-b",
                    turn_id="turn-b",
                    user_message="ping",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertIn("HCP ACTIVE CONTINUITY INSTRUCTION", second["context"])
                transformed = mod.ambient._transform_llm_output(
                    "The model forgot the instruction.",
                    "session-b",
                    model="m",
                    platform="cli",
                )
                self.assertEqual(transformed, "pong")
                mod.ambient._post_llm_call(
                    "session-b",
                    turn_id="turn-b",
                    assistant_response=transformed,
                    model="m",
                    platform="cli",
                )
                completed = store.instructions(statuses={"completed"})
                self.assertEqual(len(completed), 1)

                # One-shot instructions are consumed only after successful execution.
                third = mod.ambient._pre_llm_call(
                    "session-c",
                    turn_id="turn-c",
                    user_message="ping",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )
                self.assertNotIn("HCP ACTIVE CONTINUITY INSTRUCTION", third["context"])
                self.assertIsNone(mod.ambient._transform_llm_output("normal", "session-c"))
            finally:
                os.chdir(original_cwd)
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home

    def test_hcp_state_tool_exposes_global_instruction_state(self):
        mod = load_package("hcp_ambient_tool_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as project:
            os.environ["HERMES_HOME"] = home
            try:
                created = mod.tools.state_update(
                    {
                        "scope": "instruction",
                        "patch": {
                            "action": "alpha",
                            "action_type": "respond_exact",
                            "trigger_type": "exact",
                            "trigger_patterns": ["beta"],
                            "scope": "global",
                        },
                    },
                    hcp_project_root=project,
                    session_id="tool-session",
                )
                self.assertIn('"ok": true', created.lower())
                readback = mod.tools.state_read(
                    {"scope": "instructions"},
                    hcp_project_root=project,
                    session_id="tool-session",
                )
                self.assertIn('"alpha"', readback)
                self.assertIn('"beta"', readback)
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
