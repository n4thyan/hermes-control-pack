import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins" / "hcp-runtime"
ENGINE_DIR = ROOT / "plugins" / "context_engine" / "hcp-continuity"


def load_package(name: str, directory: Path):
    spec = importlib.util.spec_from_file_location(
        name, directory / "__init__.py", submodule_search_locations=[str(directory)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FakeCtx:
    def __init__(self):
        self.tools = {}
        self.hooks = {}
        self.sections = {}
        self.commands = {}

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools[name] = (toolset, schema, handler)

    def register_hook(self, name, callback):
        self.hooks[name] = callback

    def register_system_prompt_section(self, name, callback, **kwargs):
        self.sections[name] = (callback, kwargs)

    def register_command(self, name, handler, description="", **kwargs):
        self.commands[name] = handler


class PluginTests(unittest.TestCase):
    def test_runtime_plugin_registers_documented_surfaces(self):
        mod = load_package("hcp_runtime_test", PLUGIN_DIR)
        ctx = FakeCtx()
        mod.register(ctx)
        self.assertEqual(set(ctx.tools), {
            "hcp_state_read", "hcp_state_update", "hcp_decision_record", "hcp_evidence_record"
        })
        self.assertIn("pre_llm_call", ctx.hooks)
        self.assertIn("pre_verify", ctx.hooks)
        self.assertIn("post_tool_call", ctx.hooks)
        self.assertIn("hcp.runtime-kernel", ctx.sections)
        callback, opts = ctx.sections["hcp.runtime-kernel"]
        with tempfile.TemporaryDirectory() as home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = home
            try:
                text = callback({
                    "session_id": "s1", "cwd": str(ROOT), "model": "m", "provider": "p",
                    "platform": "cli", "profile_name": "default",
                })
            finally:
                if previous is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous
        self.assertLessEqual(len(text), 4000)
        self.assertIn("PROJECT_STATE", text)
        self.assertEqual(opts["position"], "after_memory")

    def test_plugin_tools_persist_and_pre_verify_gates_until_evidence(self):
        mod = load_package("hcp_runtime_test2", PLUGIN_DIR)
        ctx = FakeCtx()
        mod.register(ctx)
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = home
            self.addCleanup(lambda: os.environ.__setitem__("HERMES_HOME", previous) if previous is not None else os.environ.pop("HERMES_HOME", None))
            # Seed session->workspace mapping through the documented system-section callback.
            cb, _ = ctx.sections["hcp.runtime-kernel"]
            cb({"session_id": "s2", "cwd": td, "model": "m", "provider": "p", "platform": "cli", "profile_name": "default"})
            _, _, update = ctx.tools["hcp_state_update"]
            payload = json.loads(update({"scope": "task", "patch": {"objective": "Fix bug"}}, session_id="s2"))
            self.assertTrue(payload["ok"])
            # A write makes verification stale.
            ctx.hooks["post_tool_call"](
                tool_name="write_file", args={"path": "x.py"}, result="ok", task_id="t", session_id="s2",
                turn_id="turn", duration_ms=1, status="success",
            )
            directive = ctx.hooks["pre_verify"](
                session_id="s2", platform="cli", model="m", coding=True, attempt=0,
                final_response="done", changed_paths=["x.py"],
            )
            self.assertEqual(directive["action"], "continue")
            # A successful test command satisfies the fresh-evidence requirement.
            ctx.hooks["post_tool_call"](
                tool_name="terminal", args={"command": "python -m unittest"}, result="OK", task_id="t",
                session_id="s2", turn_id="turn", duration_ms=1, status="success",
            )
            self.assertIsNone(ctx.hooks["pre_verify"](
                session_id="s2", platform="cli", model="m", coding=True, attempt=1,
                final_response="done", changed_paths=["x.py"],
            ))

    def test_session_root_mapping_survives_in_memory_reset(self):
        mod = load_package("hcp_runtime_resume_test", PLUGIN_DIR)
        ctx = FakeCtx()
        mod.register(ctx)
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = home
            try:
                cb, _ = ctx.sections["hcp.runtime-kernel"]
                cb({"session_id": "resume-1", "cwd": td, "model": "m", "provider": "p", "platform": "cli", "profile_name": "default"})
                mod._SESSION_CWD.clear()
                self.assertEqual(mod._root_for("resume-1"), Path(td).resolve())
            finally:
                if previous is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous

    def test_terminal_mutation_after_test_makes_evidence_stale(self):
        mod = load_package("hcp_runtime_terminal_mutation", PLUGIN_DIR)
        ctx = FakeCtx()
        mod.register(ctx)
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = home
            try:
                cb, _ = ctx.sections["hcp.runtime-kernel"]
                cb({"session_id": "s3", "cwd": td, "model": "m", "provider": "p", "platform": "cli", "profile_name": "default"})
                _, _, update = ctx.tools["hcp_state_update"]
                update({"scope": "task", "patch": {"objective": "Fix bug"}}, session_id="s3")
                ctx.hooks["post_tool_call"](tool_name="terminal", args={"command": "python -m unittest"}, result="OK", session_id="s3", turn_id="t", status="success")
                ctx.hooks["post_tool_call"](tool_name="terminal", args={"command": "sed -i 's/a/b/' x.py"}, result="", session_id="s3", turn_id="t", status="success")
                directive = ctx.hooks["pre_verify"](session_id="s3", platform="cli", model="m", coding=True, attempt=0, final_response="done", changed_paths=["x.py"])
                self.assertEqual(directive["action"], "continue")
                self.assertIn("fresh verification", directive["message"])
            finally:
                if previous is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous

    def test_pre_verify_persists_changed_paths_and_requires_objective(self):
        mod = load_package("hcp_runtime_state_gate", PLUGIN_DIR)
        ctx = FakeCtx()
        mod.register(ctx)
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = home
            try:
                cb, _ = ctx.sections["hcp.runtime-kernel"]
                cb({"session_id": "s4", "cwd": td, "model": "m", "provider": "p", "platform": "cli", "profile_name": "default"})
                directive = ctx.hooks["pre_verify"](session_id="s4", platform="cli", model="m", coding=True, attempt=0, final_response="done", changed_paths=["a.py", "b.py"])
                self.assertEqual(directive["action"], "continue")
                self.assertIn("TASK_STATE objective", directive["message"])
                task = mod._store("s4").read_task()
                self.assertEqual(task["changed_paths"], ["a.py", "b.py"])
            finally:
                if previous is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous

    def test_continuity_engine_augments_memory_context(self):
        fake_agent = types.ModuleType("agent")
        fake_cc = types.ModuleType("agent.context_compressor")

        class FakeCompressor:
            def __init__(self, *args, **kwargs):
                self.init = (args, kwargs)
            def compress(self, messages, **kwargs):
                return [{"role": "assistant", "content": kwargs.get("memory_context", "")}]

        fake_cc.ContextCompressor = FakeCompressor
        old_agent = sys.modules.get("agent")
        old_cc = sys.modules.get("agent.context_compressor")
        sys.modules["agent"] = fake_agent
        sys.modules["agent.context_compressor"] = fake_cc
        try:
            mod = load_package("hcp_continuity_test", ENGINE_DIR)
            with tempfile.TemporaryDirectory() as td:
                cwd = Path.cwd()
                try:
                    import os
                    os.chdir(td)
                    engine = mod.HCPContinuityEngine()
                    result = engine.compress([{"role": "user", "content": "hi"}], memory_context="existing")
                finally:
                    os.chdir(cwd)
            self.assertIn("existing", result[0]["content"])
            self.assertIn("HCP STRUCTURED CONTINUITY", result[0]["content"])
        finally:
            if old_agent is None:
                sys.modules.pop("agent", None)
            else:
                sys.modules["agent"] = old_agent
            if old_cc is None:
                sys.modules.pop("agent.context_compressor", None)
            else:
                sys.modules["agent.context_compressor"] = old_cc


if __name__ == "__main__":
    unittest.main()
