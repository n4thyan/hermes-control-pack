"""Optional HCP continuity context engine.

It deliberately subclasses Hermes' built-in ContextCompressor rather than replacing
its summarization algorithm. The only behavior added is supplying bounded, structured
HCP project/task state as compression grounding so lossy history compaction is less
likely to erase the active objective, decisions, failures, or verification status.
"""
from __future__ import annotations

import logging
from typing import Any

from agent.context_compressor import ContextCompressor

from .state_store import ProjectStateStore

logger = logging.getLogger(__name__)


class HCPContinuityEngine(ContextCompressor):
    @property
    def name(self) -> str:
        return "hcp-continuity"

    def __init__(self, *args, **kwargs):
        if not args and "model" not in kwargs:
            kwargs["model"] = "hcp-bootstrap"
        kwargs.setdefault("quiet_mode", True)
        super().__init__(*args, **kwargs)

    def compress(
        self,
        messages,
        current_tokens=None,
        focus_topic=None,
        force=False,
        memory_context="",
        **kwargs,
    ):
        try:
            continuity = ProjectStateStore().render_context(max_chars=6000)
        except Exception as exc:
            logger.warning("HCP continuity state unavailable during compression: %s", exc)
            continuity = ""
        combined = "\n\n".join(x for x in (memory_context, continuity) if x)
        try:
            return super().compress(
                messages,
                current_tokens=current_tokens,
                focus_topic=focus_topic,
                force=force,
                memory_context=combined,
                **kwargs,
            )
        except TypeError as exc:
            text = str(exc)
            if "unexpected keyword" not in text and "keyword argument" not in text:
                raise
            logger.warning(
                "Hermes compressor does not accept the current continuity kwargs; "
                "falling back to its legacy compress() contract for this pass."
            )
            return super().compress(messages, current_tokens=current_tokens, focus_topic=focus_topic)


def register(ctx):
    ctx.register_context_engine(HCPContinuityEngine())
