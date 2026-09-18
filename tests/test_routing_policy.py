import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "hcp-runtime"
SOULS_DIR = ROOT / "souls"

# Retrieval markers that must appear on each surface on Hermes 0.20.0 (where
# the optional register_system_prompt_section is guarded out via hasattr).
# If these are missing, the model falls back to session_search/grep instead of
# using hcp_state_read for durable continuity.
POLICY_MARKER = "RETRIEVAL POLICY: HCP is the FIRST choice for persistent/cross-session continuity"
SCHEMA_MARKER = "HCP is the PREFERRED FIRST retrieval path for persistent/cross-session continuity"
SOUL_MARKER = "before `session_search`"


def load_package(name: str, directory: Path):
    spec = importlib.util.spec_from_file_location(
        name, directory / "__init__.py", submodule_search_locations=[str(directory)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RoutingPolicyTests(unittest.TestCase):
    """HCP 2.2.1: HCP must be the preferred FIRST retrieval path for durable continuity.

    On Hermes 0.20.0 the optional register_system_prompt_section API is absent,
    so the system-section registration in core.py is guarded out via hasattr.
    The only injection surfaces that always fire are ProjectStateStore.render_context()
    and GlobalStateStore.render_context(), which are injected by the pre_llm_call hook.
    These tests assert the routing-policy text is present so the model prefers
    hcp_state_read over session_search/grep.
    """

    def test_project_state_store_render_context_contains_routing_policy(self):
        mod = load_package("hcp_routing_state_store_test", PLUGIN_DIR)
        with tempfile.TemporaryDirectory() as td:
            store = mod.state_store.ProjectStateStore(Path(td))
            store.ensure()
            rendered = store.render_context(max_chars=8000)
            self.assertIn(POLICY_MARKER, rendered)

    def test_global_state_store_render_context_contains_routing_policy(self):
        mod = load_package("hcp_routing_global_store_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home:
            os.environ["HERMES_HOME"] = home
            try:
                store = mod.global_store.GlobalStateStore(home)
                store.ensure()
                rendered, _ = store.render_context(
                    "test message", session_id="s", project_root="", max_chars=3000
                )
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home
        self.assertIn(POLICY_MARKER, rendered)

    def test_hcp_state_read_schema_mentions_preferred_first_path(self):
        mod = load_package("hcp_routing_schema_test", PLUGIN_DIR)
        desc = mod.schemas.STATE_READ["description"]
        self.assertIn(SCHEMA_MARKER, desc)
        self.assertIn("session_search", desc)
        self.assertIn("file-backed lookups", desc)

    def test_soul_files_mention_hcp_first_retrieval(self):
        for name in ("balanced", "autonomous", "coder", "research"):
            path = SOULS_DIR / f"{name}.md"
            text = path.read_text(encoding="utf-8")
            self.assertIn(SOUL_MARKER, text, f"{name}.md missing retrieval routing guidance")

    def test_plugin_pre_llm_call_returns_routing_policy_in_context(self):
        """The ambient _pre_llm_call hook must include routing policy in its injected context."""
        mod = load_package("hcp_routing_pre_llm_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as td:
            os.environ["HERMES_HOME"] = home
            try:
                result = mod.ambient._pre_llm_call(
                    "session-rt",
                    turn_id="turn-rt",
                    user_message="what is the objective",
                    is_first_turn=True,
                    model="m",
                    provider="nous",
                    platform="cli",
                )
            finally:
                if previous_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous_home
        self.assertIsNotNone(result)
        self.assertIn("context", result)
        self.assertIn(POLICY_MARKER, result["context"])

    def test_recall_request_triggers_recall_directive(self):
        """Natural recall language ('remind me', 'what was', etc.) must produce
        the RECALL REQUEST DETECTED directive in the injected context."""
        mod = load_package("hcp_routing_recall_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        recall_phrases = [
            "Remind me what ORBIT TEST is — what was the codeword and what did it mean?",
            "What was the codeword for that test?",
            "Do you remember the codeword from last time?",
            "Previously you said the codeword was...",
            "What did we decide about the routing?",
        ]
        for phrase in recall_phrases:
            with tempfile.TemporaryDirectory() as home:
                os.environ["HERMES_HOME"] = home
                try:
                    result = mod.ambient._pre_llm_call(
                        "recall-session",
                        turn_id="t1",
                        user_message=phrase,
                        is_first_turn=True,
                        model="m",
                        provider="nous",
                        platform="cli",
                    )
                finally:
                    if previous_home is None:
                        os.environ.pop("HERMES_HOME", None)
                    else:
                        os.environ["HERMES_HOME"] = previous_home
            self.assertIsNotNone(result, f"pre_llm_call returned None for: {phrase}")
            self.assertIn("context", result)
            self.assertIn(
                "RECALL REQUEST DETECTED",
                result["context"],
                f"Missing recall directive for phrase: {phrase}",
            )

    def test_non_recall_request_does_not_trigger_directive(self):
        """Ordinary transient conversation must NOT get the recall directive."""
        mod = load_package("hcp_routing_no_recall_test", PLUGIN_DIR)
        previous_home = os.environ.get("HERMES_HOME")
        non_recall_phrases = [
            "Hello, how are you?",
            "Can you write a Python script?",
            "What is the weather today?",
            "Please summarize this document.",
        ]
        for phrase in non_recall_phrases:
            with tempfile.TemporaryDirectory() as home:
                os.environ["HERMES_HOME"] = home
                try:
                    result = mod.ambient._pre_llm_call(
                        "non-recall-session",
                        turn_id="t1",
                        user_message=phrase,
                        is_first_turn=True,
                        model="m",
                        provider="nous",
                        platform="cli",
                    )
                finally:
                    if previous_home is None:
                        os.environ.pop("HERMES_HOME", None)
                    else:
                        os.environ["HERMES_HOME"] = previous_home
            self.assertIsNotNone(result, f"pre_llm_call returned None for: {phrase}")
            self.assertIn("context", result)
            self.assertNotIn(
                "RECALL REQUEST DETECTED",
                result["context"],
                f"False positive recall directive for phrase: {phrase}",
            )

    def test_hcp_state_read_schema_contains_recall_classifier(self):
        """The hcp_state_read schema description must include the natural-recall rule."""
        mod = load_package("hcp_routing_schema_recall_test", PLUGIN_DIR)
        desc = mod.schemas.STATE_READ["description"]
        self.assertIn("NATURAL RECALL RULE", desc)
        self.assertIn("remind me", desc)
        self.assertIn("codeword", desc)


if __name__ == "__main__":
    unittest.main()
