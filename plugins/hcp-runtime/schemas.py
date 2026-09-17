"""Hermes tool schemas for structured HCP continuity."""

_PROJECT_ROOT = {
    "type": "string",
    "description": (
        "Optional project/workspace root. Use this when Hermes was launched outside the project directory. "
        "If omitted, HCP uses the current session's mapped project root."
    ),
}

STATE_READ = {
    "name": "hcp_state_read",
    "description": (
        "Read Hermes Control Pack continuity. Project/task state is project-scoped; global state and pending continuity "
        "items live under the Hermes home and are available independently of the current working directory. Use project_root "
        "to read a specific project even when Hermes was launched elsewhere."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "enum": ["summary", "project", "task", "decisions", "evidence", "trace", "global", "instructions"],
                "description": "Which durable HCP view to return.",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "description": "Tail length for log/list scopes."},
            "project_root": _PROJECT_ROOT,
        },
    },
}

STATE_UPDATE = {
    "name": "hcp_state_update",
    "description": (
        "Update persistent HCP state. Use project/task for project continuity, global for cwd-independent durable context, "
        "and instruction for explicit future or cross-session continuity items. Use project_root when operating on a project "
        "that is not the directory Hermes was launched from."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["project", "task", "global", "instruction"]},
            "patch": {
                "type": "object",
                "description": (
                    "For project/task/global: object merged into state. For instruction creation: include action, action_type, "
                    "trigger_type, trigger_patterns, scope, consume_after_success, and optional timing/priority. For an existing "
                    "instruction include instruction_id and the fields to change."
                ),
            },
            "replace": {"type": "boolean", "description": "Replace project/task object instead of deep-merging it."},
            "project_root": _PROJECT_ROOT,
        },
        "required": ["scope", "patch"],
    },
}

DECISION_RECORD = {
    "name": "hcp_decision_record",
    "description": (
        "Record a material, externally defensible project/task decision so later sessions do not rediscover or reverse it. "
        "Store the decision and concise rationale/evidence, never private chain-of-thought."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "decision": {"type": "string"},
            "rationale": {"type": "string"},
            "alternatives": {"type": "array", "items": {"type": "string"}},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "enum": ["accepted", "superseded", "rejected", "tentative"]},
            "project_root": _PROJECT_ROOT,
        },
        "required": ["decision"],
    },
}

EVIDENCE_RECORD = {
    "name": "hcp_evidence_record",
    "description": (
        "Record verification or observed evidence that supports a completion/root-cause claim. Use for tests, builds, "
        "runtime/browser checks, screenshots, API checks, diff review, or an important failed check not automatically "
        "captured by HCP. Evidence must describe what was actually observed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "What this evidence establishes."},
            "result": {"type": "string", "enum": ["pass", "fail", "unknown", "observed"]},
            "kind": {"type": "string", "description": "test/build/runtime/visual/diff/research/etc."},
            "source": {"type": "string", "description": "tool/command/browser/manual/source name."},
            "details": {"type": "string"},
            "command": {"type": "string"},
            "changed_paths": {"type": "array", "items": {"type": "string"}},
            "project_root": _PROJECT_ROOT,
        },
        "required": ["subject", "result"],
    },
}
