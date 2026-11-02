"""
Preferences tools — project design norms / codes.

Probed against Robot 2013 (French-language build):
  app.Project.Preferences.GetActiveCode(typeIndex) → code name string
  app.Project.Preferences.SetActiveCode(typeIndex, codeName)
  Valid typeIndex range: 0–9 (10+ raise COM exceptions in Robot 2013)
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import robot

# ──────────────────────────────────────────────────────────────────
# IRobotCodeType — confirmed by live probe on Robot 2013
# ──────────────────────────────────────────────────────────────────
# Index → design discipline
CODE_TYPES: dict[str, int] = {
    "steel":       0,   # steel member design (e.g. EN 1993-1-1)
    "connections": 1,   # steel connections   (e.g. EN 1993-1-8)
    "timber":      2,   # timber / aluminium  (e.g. EN 1995-1)
    "concrete":    3,   # concrete / RC       (e.g. EN 1992-1-1)
    "concrete_rc": 4,   # RC detailed design  (same family as concrete)
    "foundation":  5,   # geotechnical        (e.g. BS 8004)
    "loads":       6,   # load codes          (e.g. EN 1991-1-3/4)
    "seismic":     7,   # seismic             (e.g. EN 1998-1-1)
    "bridges":     8,   # bridge codes        (e.g. AASHTO)
    "basis":       9,   # basis of design     (e.g. EN 1990)
}
CODE_TYPES_INV: dict[int, str] = {v: k for k, v in CODE_TYPES.items()}

# ──────────────────────────────────────────────────────────────────
# Tool schemas
# ──────────────────────────────────────────────────────────────────

TOOLS: list[Tool] = [
    Tool(
        name="robot_get_norms",
        description=(
            "Return all active design codes / norms set for this project "
            "(steel, connections, timber, concrete, foundation, loads, seismic, "
            "bridges, basis). Use this to inspect the current norm configuration "
            "before running a design check."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_set_norm",
        description=(
            "Set the active design code for one discipline. "
            "codeType must be one of: "
            + ", ".join(CODE_TYPES.keys())
            + ". "
            "codeName is the exact Robot code string — use robot_get_norms first "
            "to see the current value and format (e.g. 'EN 1993-1-1:2005/AC:2009', "
            "'BS-EN 1993-1:2005/NA:2008/AC:2009'). "
            "The change applies to the open project; call robot_project_save afterwards "
            "to persist it."
        ),
        inputSchema={
            "type": "object",
            "required": ["codeType", "codeName"],
            "properties": {
                "codeType": {
                    "type": "string",
                    "enum": list(CODE_TYPES.keys()),
                    "description": "Design discipline to change",
                },
                "codeName": {
                    "type": "string",
                    "description": (
                        "Exact Robot code name string. "
                        "Robot will reject unknown names with a COM error."
                    ),
                },
            },
        },
    ),
]

# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_get_norms(args: dict) -> dict:
    prefs = robot().app(launch=False).Project.Preferences
    norms: dict = {}
    for type_name, type_idx in CODE_TYPES.items():
        try:
            norms[type_name] = {
                "code": str(prefs.GetActiveCode(type_idx)),
                "typeIndex": type_idx,
            }
        except Exception:
            # Type not supported in this Robot version / project type
            pass
    return {"norms": norms}


async def handle_robot_set_norm(args: dict) -> dict:
    code_type: str = args["codeType"]
    code_name: str = args["codeName"]

    type_idx = CODE_TYPES.get(code_type)
    if type_idx is None:
        raise ValueError(
            f"Unknown codeType '{code_type}'. "
            f"Valid values: {list(CODE_TYPES.keys())}"
        )

    prefs = robot().app(launch=False).Project.Preferences
    prefs.SetActiveCode(type_idx, code_name)

    # Read back to confirm Robot accepted the name
    try:
        confirmed = str(prefs.GetActiveCode(type_idx))
    except Exception as e:
        confirmed = f"(read-back failed: {e})"

    return {
        "set": True,
        "codeType": code_type,
        "typeIndex": type_idx,
        "codeName": confirmed,
    }


HANDLERS: dict[str, object] = {
    "robot_get_norms": handle_robot_get_norms,
    "robot_set_norm":  handle_robot_set_norm,
}
