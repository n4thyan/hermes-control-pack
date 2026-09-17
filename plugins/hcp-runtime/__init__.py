"""Hermes Control Pack runtime plugin.

HCP 2.1 keeps the proven HCP 2.0 project/verification kernel in ``core`` and
adds cwd-independent ambient continuity in ``ambient``. Both use documented
Hermes plugin surfaces only.
"""
from __future__ import annotations

from . import ambient, core


def register(ctx) -> None:
    core.register(ctx)
    ambient.register(ctx)


def __getattr__(name):
    """Preserve access to HCP 2.0 runtime internals used by tests/diagnostics."""
    return getattr(core, name)
