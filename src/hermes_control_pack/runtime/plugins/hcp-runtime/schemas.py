"""Hermes tool schemas for structured HCP continuity."""

STATE_READ = {
    "name": "hcp_state_read",
    "description": (
        "Read Hermes Control Pack persistent project/task continuity. Use at the start of a resumed task, "
        "after context compression when details are uncertain, or before making a decision that may already "
        "have been recorded. Returns structured state, recent decisions, and verification evidence."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "enum": ["summary", "project", "task", "decisions", "evidence", "trace"],
                "description": "Which durable HCP view to return.",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "description": "Tail length for log scopes."},
        },
    },
}

STATE_UPDATE = {
    "name": "hcp_state_update",
    "description": (
        "Update persistent HCP PROJECT_STATE or TASK_STATE. Use when goals, acceptance criteria, architecture facts, "
        "constraints, changed paths, blockers, current phase, completed work, or next steps materially change. "
        "Pass only concise durable state, not transcript prose or hidden reasoning."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["project", "task"]},
            "patch": {"type": "object", "description": "JSON object merged into the selected state object."},
            "replace": {"type": "boolean", "description": "Replace the object instead of deep-merging it. Usually false."},
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
        },
        "required": ["subject", "result"],
    },
}
