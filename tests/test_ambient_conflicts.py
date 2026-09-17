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


class AmbientConflictTests(unittest.TestCase):
    def test_current_user_override_prevents_exact_response_transform(self):
        mod = load_package("hcp_ambient_conflict_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.ambient.GlobalStateStore()
                store.record_instruction(
                    {
                        "action": "pong",
                        "action_type": "respond_exact",
                        "trigger_type": "contains_any",
                        "trigger_patterns": ["ping"],
                        "scope": "global",
                        "consume_after_success": True,
                    },
                    session_id="older-session",
                )
                context = mod.ambient._pre_llm_call(
                    "new-session",
                    turn_id="turn",
                    user_message="ping, but ignore that instruction",
                    is_first_turn=True,
                    model="m",
                    platform="cli",
                )["context"]
                self.assertIn("HCP CURRENT USER OVERRIDE", context)
                self.assertNotIn("HCP ACTIVE CONTINUITY INSTRUCTION", context)
                self.assertIsNone(
                    mod.ambient._transform_llm_output(
                        "newer user request wins",
                        "new-session",
                        model="m",
                        platform="cli",
                    )
                )
                pending = store.instructions(statuses={"pending"})
                self.assertEqual(len(pending), 1)
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
