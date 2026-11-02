"""
Aggregate all tool modules into TOOLS list and HANDLERS dict.
"""
from __future__ import annotations
from mcp.types import Tool

from . import session, model_read, model_write, loads, analysis, results, preferences

# ── All tools ──────────────────────────────────────────────────────
_modules = [session, model_read, model_write, loads, analysis, results, preferences]

TOOLS: list[Tool] = []
HANDLERS: dict[str, object] = {}

for _mod in _modules:
    TOOLS.extend(_mod.TOOLS)
    HANDLERS.update(_mod.HANDLERS)

# Deduplicate by name (last wins)
_seen: dict[str, Tool] = {}
for t in TOOLS:
    _seen[t.name] = t
TOOLS = list(_seen.values())
