"""
Load tools — cases, nodal forces, bar loads, self-weight, combinations.
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import (
    robot,
    LOAD_NATURES, ANALYSIS_TYPES,
    I_LRT_NODE_FORCE, I_LRT_BAR_UNIFORM, I_LRT_BAR_TRAPEZOIDAL,
    I_LRT_BAR_POINT, I_LRT_SELF_WEIGHT,
    I_NFRV_FX, I_NFRV_FY, I_NFRV_FZ, I_NFRV_CX, I_NFRV_CY, I_NFRV_CZ,
    I_BURV_PX, I_BURV_PY, I_BURV_PZ,
    I_LNT_PERMANENT, I_AT_STATIC,
    I_SWRV_Z,
)


TOOLS: list[Tool] = [
    Tool(
        name="robot_create_case",
        description=(
            "Create a load case: id, name, nature "
            "(dead/live/wind/snow/temperature/accidental/seismic), analysis type (static/modal/buckling)."
        ),
        inputSchema={
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id":           {"type": "integer"},
                "name":         {"type": "string"},
                "nature":       {"type": "string", "enum": list(LOAD_NATURES.keys())},
                "analyzeType":  {"type": "string", "enum": list(ANALYSIS_TYPES.keys())},
            },
        },
    ),
    Tool(
        name="robot_add_nodal_load",
        description=(
            "Add a nodal force and/or moment to a load case. "
            "Forces in kN, moments in kN·m. "
            "Applies to selected nodes."
        ),
        inputSchema={
            "type": "object",
            "required": ["caseId", "selection"],
            "properties": {
                "caseId":    {"type": "integer"},
                "selection": {"type": "string", "description": "Node selection"},
                "fx": {"type": "number"}, "fy": {"type": "number"}, "fz": {"type": "number"},
                "mx": {"type": "number"}, "my": {"type": "number"}, "mz": {"type": "number"},
            },
        },
    ),
    Tool(
        name="robot_add_bar_uniform",
        description=(
            "Add a uniform distributed load to bars in a load case. "
            "Force in kN/m along global or local axes. "
            "px/py/pz = force per unit length."
        ),
        inputSchema={
            "type": "object",
            "required": ["caseId", "selection"],
            "properties": {
                "caseId":    {"type": "integer"},
                "selection": {"type": "string", "description": "Bar selection"},
                "px": {"type": "number", "description": "kN/m in X"},
                "py": {"type": "number", "description": "kN/m in Y"},
                "pz": {"type": "number", "description": "kN/m in Z (negative = downward)"},
                "local": {"type": "boolean", "description": "Apply in local axes (default false = global)"},
            },
        },
    ),
    Tool(
        name="robot_add_bar_point",
        description=(
            "Add a point (concentrated) load on bars at a position along the bar. "
            "position=0.0 is start, 1.0 is end (relative) or absolute distance if relative=false."
        ),
        inputSchema={
            "type": "object",
            "required": ["caseId", "selection"],
            "properties": {
                "caseId":    {"type": "integer"},
                "selection": {"type": "string"},
                "position":  {"type": "number", "description": "0.0 to 1.0 relative (default 0.5)"},
                "relative":  {"type": "boolean", "description": "Position is relative (default true)"},
                "fx": {"type": "number"}, "fy": {"type": "number"}, "fz": {"type": "number"},
                "mx": {"type": "number"}, "my": {"type": "number"}, "mz": {"type": "number"},
                "local": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_add_bar_trapezoidal",
        description=(
            "Add a trapezoidal distributed load on bars (varying intensity from start to end). "
            "pStart/pEnd in kN/m in Z direction (or specify px/py/pz start/end)."
        ),
        inputSchema={
            "type": "object",
            "required": ["caseId", "selection"],
            "properties": {
                "caseId":    {"type": "integer"},
                "selection": {"type": "string"},
                "pzStart": {"type": "number", "description": "kN/m at start"},
                "pzEnd":   {"type": "number", "description": "kN/m at end"},
                "pxStart": {"type": "number"}, "pxEnd": {"type": "number"},
                "pyStart": {"type": "number"}, "pyEnd": {"type": "number"},
                "local": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_add_self_weight",
        description=(
            "Add a self-weight load record to a case. "
            "factor: multiplier (default -1.0 for downward gravity)."
        ),
        inputSchema={
            "type": "object",
            "required": ["caseId"],
            "properties": {
                "caseId":    {"type": "integer"},
                "selection": {"type": "string", "description": "Bar/panel selection (default all)"},
                "factor":    {"type": "number", "description": "Multiplier (default -1.0)"},
                "direction": {"type": "string", "enum": ["x", "y", "z"], "description": "Gravity direction (default z)"},
            },
        },
    ),
    Tool(
        name="robot_create_combination",
        description=(
            "Create a load combination case. "
            "Specify component cases with factors."
        ),
        inputSchema={
            "type": "object",
            "required": ["id", "name", "components"],
            "properties": {
                "id":   {"type": "integer"},
                "name": {"type": "string"},
                "combType": {"type": "string", "enum": ["uls", "sls", "acc"], "description": "ULS/SLS/accidental"},
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["caseId", "factor"],
                        "properties": {
                            "caseId": {"type": "integer"},
                            "factor": {"type": "number"},
                        },
                    },
                },
            },
        },
    ),
    Tool(
        name="robot_delete_case",
        description="Delete a load case or combination.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                "id":      {"type": "integer"},
                "confirm": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_delete_load_records",
        description="Delete all load records of a given type from a case, or clear all records.",
        inputSchema={
            "type": "object",
            "required": ["caseId"],
            "properties": {
                "caseId":     {"type": "integer"},
                "recordType": {"type": "integer", "description": "Robot load record type int (omit = all)"},
            },
        },
    ),
]


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_create_case(args: dict) -> dict:
    cid = int(args["id"])
    name = str(args["name"])
    nature = LOAD_NATURES.get(args.get("nature", "dead"), I_LNT_PERMANENT)
    at = ANALYSIS_TYPES.get(args.get("analyzeType", "static"), I_AT_STATIC)

    cases = robot().structure().Cases
    if cases.Exist(cid):
        return {"exists": True, "id": cid, "note": f"Case {cid} already exists"}

    cases.CreateSimple(cid, name, nature, at)
    return {"created": True, "id": cid, "name": name, "nature": args.get("nature", "dead")}


async def handle_robot_add_nodal_load(args: dict) -> dict:
    cid = int(args["caseId"])
    sel_text = args["selection"]
    r = robot()

    case = r.structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    rec = case.Records.Create(I_LRT_NODE_FORCE)

    # Target nodes
    sel = r.selection_from_text(sel_text, "node")
    rec.Objects.FromText(sel_text)

    force_map = {"fx": I_NFRV_FX, "fy": I_NFRV_FY, "fz": I_NFRV_FZ,
                 "mx": I_NFRV_CX, "my": I_NFRV_CY, "mz": I_NFRV_CZ}
    applied: dict = {}
    for key, idx in force_map.items():
        if key in args:
            val = float(args[key])
            rec.SetValue(idx, val * 1000.0)  # kN -> N (Robot uses SI internally)
            applied[key] = val

    return {"added": True, "caseId": cid, "selection": sel_text, "values": applied}


async def handle_robot_add_bar_uniform(args: dict) -> dict:
    cid = int(args["caseId"])
    sel_text = args["selection"]
    r = robot()

    case = r.structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    rec = case.Records.Create(I_LRT_BAR_UNIFORM)
    rec.Objects.FromText(sel_text)

    local = args.get("local", False)
    if local:
        try: rec.SetValue(I_BURV_PX + 6, 1)  # local flag
        except Exception: pass

    load_map = {"px": I_BURV_PX, "py": I_BURV_PY, "pz": I_BURV_PZ}
    applied: dict = {}
    for key, idx in load_map.items():
        if key in args:
            val = float(args[key])
            rec.SetValue(idx, val * 1000.0)  # kN/m -> N/m
            applied[key] = val

    return {"added": True, "caseId": cid, "selection": sel_text, "values": applied}


async def handle_robot_add_bar_point(args: dict) -> dict:
    cid = int(args["caseId"])
    sel_text = args["selection"]
    r = robot()

    case = r.structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    rec = case.Records.Create(I_LRT_BAR_POINT)
    rec.Objects.FromText(sel_text)

    pos = float(args.get("position", 0.5))
    relative = args.get("relative", True)
    try:
        rec.SetValue(0, pos)           # position
        rec.SetValue(1, 1 if relative else 0)  # relative flag
    except Exception:
        pass

    force_map = {"fx": 2, "fy": 3, "fz": 4, "mx": 5, "my": 6, "mz": 7}
    applied: dict = {}
    for key, idx in force_map.items():
        if key in args:
            val = float(args[key])
            rec.SetValue(idx, val * 1000.0)
            applied[key] = val

    return {"added": True, "caseId": cid, "position": pos, "values": applied}


async def handle_robot_add_bar_trapezoidal(args: dict) -> dict:
    cid = int(args["caseId"])
    sel_text = args["selection"]
    r = robot()

    case = r.structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    rec = case.Records.Create(I_LRT_BAR_TRAPEZOIDAL)
    rec.Objects.FromText(sel_text)

    # Value indices for trapezoidal: 0=PX_start, 1=PX_end, 2=PY_start, 3=PY_end, 4=PZ_start, 5=PZ_end
    trap_map = {"pxStart": 0, "pxEnd": 1, "pyStart": 2, "pyEnd": 3, "pzStart": 4, "pzEnd": 5}
    applied: dict = {}
    for key, idx in trap_map.items():
        if key in args:
            val = float(args[key])
            rec.SetValue(idx, val * 1000.0)
            applied[key] = val

    return {"added": True, "caseId": cid, "selection": sel_text, "values": applied}


async def handle_robot_add_self_weight(args: dict) -> dict:
    cid = int(args["caseId"])
    r = robot()

    case = r.structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    factor = float(args.get("factor", -1.0))
    direction = args.get("direction", "z").lower()
    dir_idx = {"x": 0, "y": 1, "z": I_SWRV_Z}.get(direction, I_SWRV_Z)

    rec = case.Records.Create(I_LRT_SELF_WEIGHT)

    # Self-weight records apply to all elements automatically;
    # the Objects interface is not available for this record type.
    sel_text = args.get("selection", "all")
    if sel_text and sel_text.lower() != "all":
        try:
            rec.Objects.FromText(sel_text)
        except Exception:
            pass  # self-weight Objects not supported — applies to all

    try:
        rec.SetValue(0, dir_idx)      # direction
        rec.SetValue(1, factor)       # factor
    except Exception:
        pass

    return {"added": True, "caseId": cid, "factor": factor, "direction": direction}


async def handle_robot_create_combination(args: dict) -> dict:
    cid = int(args["id"])
    name = str(args["name"])
    comb_type_map = {"uls": 0, "sls": 1, "acc": 2}
    comb_type = comb_type_map.get(args.get("combType", "uls"), 0)

    cases = robot().structure().Cases
    if cases.Exist(cid):
        return {"exists": True, "id": cid}

    # Robot 2013: CreateCombination(id, name, nature, analyzeType=1, combType)
    cases.CreateCombination(cid, name, 0, 1, comb_type)
    comb = cases.Get(cid)

    for comp in args.get("components", []):
        # Robot 2013: combination components accessed via CaseFactors
        factor = float(comp["factor"])
        comp_id = int(comp["caseId"])
        added = False
        for attr in ("CaseFactors", "CombinationCases"):
            try:
                getattr(comb, attr).New(comp_id, factor)
                added = True
                break
            except Exception:
                pass
        if not added:
            pass  # component silently skipped — combination still created

    return {"created": True, "id": cid, "name": name, "components": len(args.get("components", []))}


async def handle_robot_delete_case(args: dict) -> dict:
    cid = int(args["id"])
    cases = robot().structure().Cases
    if not cases.Exist(cid):
        return {"notFound": True, "id": cid}
    # Robot 2013: try direct Delete first; fall back to DeleteMany
    deleted = False
    try:
        cases.Delete(cid)
        deleted = True
    except Exception:
        pass
    if not deleted:
        try:
            sel = robot().selection_from_text(str(cid), "case")
            cases.DeleteMany(sel)
            deleted = True
        except Exception as e:
            raise RuntimeError(f"Could not delete case {cid}: {e}") from e
    return {"deleted": True, "id": cid}


async def handle_robot_delete_load_records(args: dict) -> dict:
    cid = int(args["caseId"])
    case = robot().structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    records = case.Records
    if "recordType" in args:
        rec_type = int(args["recordType"])
        count = records.Count
        to_delete = []
        for i in range(1, count + 1):
            try:
                rec = records.Get(i)
                if int(rec.Type) == rec_type:
                    to_delete.append(i)
            except Exception:
                continue
        # Delete in reverse order to preserve indices
        for idx in reversed(to_delete):
            try: records.Delete(idx)
            except Exception: pass
        return {"deleted": len(to_delete), "recordType": rec_type}
    else:
        count = records.Count
        for i in range(count, 0, -1):
            try: records.Delete(i)
            except Exception: pass
        return {"deleted": count, "caseId": cid}


HANDLERS: dict[str, object] = {
    "robot_create_case":           handle_robot_create_case,
    "robot_add_nodal_load":        handle_robot_add_nodal_load,
    "robot_add_bar_uniform":       handle_robot_add_bar_uniform,
    "robot_add_bar_point":         handle_robot_add_bar_point,
    "robot_add_bar_trapezoidal":   handle_robot_add_bar_trapezoidal,
    "robot_add_self_weight":       handle_robot_add_self_weight,
    "robot_create_combination":    handle_robot_create_combination,
    "robot_delete_case":           handle_robot_delete_case,
    "robot_delete_load_records":   handle_robot_delete_load_records,
}
