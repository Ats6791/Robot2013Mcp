"""
Model write tools — create/modify nodes, bars, panels, sections, materials, supports.
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import (
    robot,
    _parse_id_text,
    PROJECT_TYPES,
    I_LT_BAR_SECTION, I_LT_BAR_MATERIAL, I_LT_NODE_SUPPORT,
    I_LT_BAR_RELEASE, I_LT_PANEL_THICKNESS,
    I_MT_STEEL, I_MT_CONCRETE, I_MT_TIMBER, I_MT_ALUMINIUM, I_MT_OTHER,
    MATERIAL_TYPES,
    I_SAGT_CARTESIAN,
    I_SALT_123, I_SALT_ABC, I_SALT_VALUE, I_SALT_DEFINE,
    PANEL_KIND_TO_OST,
)
I_LT_THICKNESS = I_LT_PANEL_THICKNESS  # local alias


def _bar_ids_for_selection(sel_text: str, bars_srv) -> list[int]:
    """Return bar IDs for a selection text, bypassing the broken COM Selections API.

    For 'all': iterates via GetAll().
    Otherwise: parses the text directly (supports '1 2 5to10 15by2').
    """
    if sel_text.strip().lower() == "all":
        ids: list[int] = []
        try:
            coll = bars_srv.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    ids.append(int(coll.Get(i).Number))
                except Exception:
                    pass
        except Exception:
            pass
        return ids
    return _parse_id_text(sel_text)


def _panel_ids_for_selection(sel_text: str, panels_srv, only_panels: bool = True) -> list[int]:
    """Return panel object IDs for a selection text.

    For 'all': iterates via GetAll(), filtering to panels only when only_panels=True.
    Otherwise: parses the text directly.
    """
    if sel_text.strip().lower() == "all":
        ids: list[int] = []
        try:
            coll = panels_srv.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    proxy = coll.Get(i)
                    if only_panels:
                        try:
                            if int(proxy.Main.DefPoints.Count) < 3:
                                continue
                        except Exception:
                            continue
                    ids.append(int(proxy.Number))
                except Exception:
                    pass
        except Exception:
            pass
        return ids
    return _parse_id_text(sel_text)


TOOLS: list[Tool] = [
    Tool(
        name="robot_create_node",
        description=(
            "Create a node at (x,y,z) in metres. "
            "Reuses an existing node at same coordinates by default. "
            "Optionally assign a support label."
        ),
        inputSchema={
            "type": "object",
            "required": ["x", "y", "z"],
            "properties": {
                "x":             {"type": "number"},
                "y":             {"type": "number"},
                "z":             {"type": "number"},
                "number":        {"type": "integer", "description": "Node number (default: next free)"},
                "support":       {"type": "string",  "description": "Support label name to assign"},
                "reuseExisting": {"type": "boolean", "description": "Reuse node at same position (default true)"},
            },
        },
    ),
    Tool(
        name="robot_create_nodes",
        description="Create many nodes in one call. Each item is {x, y, z, number?, support?}.",
        inputSchema={
            "type": "object",
            "required": ["nodes"],
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["x", "y", "z"],
                        "properties": {
                            "x":       {"type": "number"},
                            "y":       {"type": "number"},
                            "z":       {"type": "number"},
                            "number":  {"type": "integer"},
                            "support": {"type": "string"},
                        },
                    },
                },
                "reuseExisting": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_create_bar",
        description=(
            "Create a bar between two nodes (startNode/endNode) or two points (start/end [x,y,z]). "
            "Section and material are loaded from the active databases when not yet in the project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "startNode":    {"type": "integer"},
                "endNode":      {"type": "integer"},
                "start":        {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "end":          {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "section":      {"type": "string"},
                "material":     {"type": "string"},
                "release":      {"type": "string", "description": "Release label name"},
                "gamma":        {"type": "number", "description": "Rotation about bar axis (degrees)"},
                "number":       {"type": "integer", "description": "Bar number (default: next free)"},
                "reuseNodes":   {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_create_bars",
        description="Create many bars at once. Each item like robot_create_bar; 'defaults' applies to all.",
        inputSchema={
            "type": "object",
            "required": ["bars"],
            "properties": {
                "bars":       {"type": "array", "items": {"type": "object"}},
                "defaults":   {"type": "object", "description": "Default properties for every bar"},
                "reuseNodes": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_create_panel",
        description=(
            "Create a panel (slab/wall/shell) from contour points [[x,y,z], …] in metres. "
            "Requires shell/plate project type — refuses bars-only projects unless force=true."
        ),
        inputSchema={
            "type": "object",
            "required": ["points"],
            "properties": {
                "points": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                    "minItems": 3,
                },
                "kind": {
                    "type": "string",
                    "enum": ["slab", "wall", "shell"],
                    "description": "Panel structural type: 'slab' (horizontal), 'wall' (vertical voile), 'shell' (generic). Default: 'slab'.",
                },
                "thickness":      {"type": "number", "description": "Thickness in metres (e.g. 0.20 = 200 mm)"},
                "thicknessLabel": {"type": "string", "description": "Existing thickness label name"},
                "material":       {"type": "string", "description": "Material name (e.g. BA25_BAEL) — stored in thickness label"},
                "number":         {"type": "integer"},
                "force":          {"type": "boolean", "description": "Create even in bars-only project"},
            },
        },
    ),
    Tool(
        name="robot_delete",
        description="Delete nodes, bars, panels or cases by selection ('all' requires confirm=true).",
        inputSchema={
            "type": "object",
            "required": ["type", "selection"],
            "properties": {
                "type":      {"type": "string", "enum": ["node", "bar", "panel", "case"]},
                "selection": {"type": "string"},
                "confirm":   {"type": "boolean", "description": "Required when selection='all'"},
            },
        },
    ),
    Tool(
        name="robot_set_bar_section",
        description="Assign a section to bars. Loads from active databases if needed.",
        inputSchema={
            "type": "object",
            "required": ["selection", "section"],
            "properties": {
                "selection": {"type": "string"},
                "section":   {"type": "string"},
                "material":  {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_set_bar_material",
        description="Assign a material to bars (from the material database).",
        inputSchema={
            "type": "object",
            "required": ["selection", "material"],
            "properties": {
                "selection": {"type": "string"},
                "material":  {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_set_bar_release",
        description=(
            "Assign end releases to bars: preset 'pinned'/'pin-fix'/'fix-pin'/'truss' "
            "or explicit start/end DOF objects. remove=true clears releases."
        ),
        inputSchema={
            "type": "object",
            "required": ["selection"],
            "properties": {
                "selection": {"type": "string"},
                "preset":    {"type": "string", "enum": ["pinned", "pin-fix", "fix-pin", "truss"]},
                "start":     {"type": "object", "description": "{ux,uy,uz,rx,ry,rz: true/false}"},
                "end":       {"type": "object"},
                "name":      {"type": "string", "description": "Release label name"},
                "remove":    {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_set_support",
        description=(
            "Assign supports to nodes: preset 'fixed'/'pinned'/'roller_x'/'roller_y', "
            "an existing support label, or explicit DOF flags. remove=true removes supports."
        ),
        inputSchema={
            "type": "object",
            "required": ["selection"],
            "properties": {
                "selection": {"type": "string"},
                "preset":    {"type": "string", "enum": ["fixed", "pinned", "roller_x", "roller_y"]},
                "support":   {"type": "string", "description": "Existing support label name"},
                "ux": {"type": "boolean"}, "uy": {"type": "boolean"}, "uz": {"type": "boolean"},
                "rx": {"type": "boolean"}, "ry": {"type": "boolean"}, "rz": {"type": "boolean"},
                "kx": {"type": "number"}, "ky": {"type": "number"}, "kz": {"type": "number"},
                "hx": {"type": "number"}, "hy": {"type": "number"}, "hz": {"type": "number"},
                "remove": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_set_panel_thickness",
        description="Create/update a thickness label and assign it to panels.",
        inputSchema={
            "type": "object",
            "required": ["selection"],
            "properties": {
                "selection": {"type": "string"},
                "thickness": {"type": "number", "description": "Thickness in mm"},
                "name":      {"type": "string",  "description": "Label name (default TH<mm>)"},
                "material":  {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_create_section",
        description=(
            "Define a section label: load from database, or parametric "
            "(shape: rect | box | i | tube | t | c) with dimensions in mm. "
            "For concrete rectangular sections use shape='rect' with kind='column' (default) "
            "or kind='beam'. For steel solid rect pass kind='steel'."
        ),
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name":         {"type": "string"},
                "fromDatabase": {"type": "string", "description": "Database section name to copy"},
                "shape":        {"type": "string", "enum": ["rect", "box", "i", "tube", "t", "c"]},
                "kind": {
                    "type": "string",
                    "enum": ["column", "beam", "steel"],
                    "description": (
                        "Only for shape='rect'. "
                        "'column' = RC rectangular column (default), "
                        "'beam' = RC rectangular beam, "
                        "'steel' = plain steel solid rectangle."
                    ),
                },
                "b":  {"type": "number", "description": "Width mm"},
                "h":  {"type": "number", "description": "Height mm"},
                "tf": {"type": "number", "description": "Flange thickness mm"},
                "tw": {"type": "number", "description": "Web thickness mm"},
                "t":  {"type": "number", "description": "Wall thickness mm"},
                "d":  {"type": "number", "description": "Diameter mm"},
                "material":  {"type": "string"},
                "overwrite": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_create_material",
        description="Define a material label or copy fromDatabase.",
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name":           {"type": "string"},
                "type":           {"type": "string", "enum": ["steel", "concrete", "timber", "aluminium", "other"]},
                "fromDatabase":   {"type": "string"},
                "E_MPa":          {"type": "number"},
                "nu":             {"type": "number"},
                "density_kg_m3":  {"type": "number"},
                "fy_MPa":         {"type": "number"},
                "fu_MPa":         {"type": "number"},
            },
        },
    ),
    Tool(
        name="robot_create_support_label",
        description="Create a support label from DOF flags and stiffnesses without assigning it.",
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "ux": {"type": "boolean"}, "uy": {"type": "boolean"}, "uz": {"type": "boolean"},
                "rx": {"type": "boolean"}, "ry": {"type": "boolean"}, "rz": {"type": "boolean"},
                "kx": {"type": "number"}, "ky": {"type": "number"}, "kz": {"type": "number"},
                "hx": {"type": "number"}, "hy": {"type": "number"}, "hz": {"type": "number"},
            },
        },
    ),
    Tool(
        name="robot_transform",
        description="Move, copy, rotate or mirror a selection of nodes/bars/panels.",
        inputSchema={
            "type": "object",
            "required": ["operation", "selection"],
            "properties": {
                "operation": {"type": "string", "enum": ["move", "copy", "rotate", "mirror"]},
                "type":      {"type": "string", "enum": ["node", "bar", "panel"]},
                "selection": {"type": "string"},
                "dx": {"type": "number"}, "dy": {"type": "number"}, "dz": {"type": "number"},
                "angle":      {"type": "number", "description": "Degrees"},
                "axisPoint":  {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "axisPoint2": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "center":     {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "copy":        {"type": "boolean"},
                "repetitions": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_create_axes",
        description=(
            "Create a cartesian structural-axes grid (construction lines) visible in Robot. "
            "Pass arrays of ABSOLUTE positions in metres for each direction. "
            "Optional label arrays set axis names; defaults: X=ABC, Y=123, Z=value. "
            "Uses app.Project.AxisMngr (Robot 2013 API)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "x":       {"type": "array", "items": {"type": "number"}, "description": "Absolute X positions in m"},
                "y":       {"type": "array", "items": {"type": "number"}, "description": "Absolute Y positions in m"},
                "z":       {"type": "array", "items": {"type": "number"}, "description": "Absolute Z positions in m (storey levels)"},
                "xLabels": {"type": "array", "items": {"type": "string"}, "description": "Labels for X axes (e.g. A,B,C,D)"},
                "yLabels": {"type": "array", "items": {"type": "string"}, "description": "Labels for Y axes (e.g. 1,2,3)"},
                "zLabels": {"type": "array", "items": {"type": "string"}, "description": "Labels for Z axes (storey names)"},
                "name":    {"type": "string", "description": "Grid name (default: 'Grille DXF')"},
                "replace": {"type": "boolean", "description": "If true (default), delete any existing grid with the same name before creating"},
            },
        },
    ),
    Tool(
        name="robot_set_bar_gamma",
        description=(
            "Set the gamma rotation angle (degrees) of bars about their own axis. "
            "Useful to orient rectangular sections: 0° = strong axis vertical, 90° = rotated."
        ),
        inputSchema={
            "type": "object",
            "required": ["selection", "angle"],
            "properties": {
                "selection": {"type": "string", "description": "Bar selection: '1 2 5to10' or 'all'"},
                "angle":     {"type": "number",  "description": "Gamma angle in degrees"},
            },
        },
    ),
    Tool(
        name="robot_get_axes",
        description=(
            "Read back the structural-axes grids defined in the project "
            "(name, X/Y/Z positions in m, axis labels). "
            "Useful to verify robot_create_axes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Filter by grid name (omit for all grids)"},
            },
        },
    ),
    Tool(
        name="robot_clear_structure",
        description="Delete EVERYTHING in the model. Requires confirm=true.",
        inputSchema={
            "type": "object",
            "required": ["confirm"],
            "properties": {
                "confirm": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_build_frame",
        description=(
            "Generate a regular multi-bay, multi-storey frame from parameters. "
            "Fastest way to create a typical structural frame."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "baysX":          {"type": "array", "items": {"type": "number"}, "description": "Bay spans along X in m"},
                "baysY":          {"type": "array", "items": {"type": "number"}, "description": "Bay spans along Y in m (omit for 2D frame)"},
                "storeyHeights":  {"type": "array", "items": {"type": "number"}},
                "storeys":        {"type": "integer"},
                "storeyHeight":   {"type": "number", "description": "Uniform storey height m"},
                "columnSection":  {"type": "string"},
                "beamSection":    {"type": "string"},
                "beamSectionY":   {"type": "string"},
                "material":       {"type": "string"},
                "support":        {"type": "string", "enum": ["fixed", "pinned", "none"]},
                "beamRelease":    {"type": "string", "enum": ["pinned", "none"]},
                "origin":         {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "dryRun":         {"type": "boolean"},
            },
        },
    ),
]


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_create_node(args: dict) -> dict:
    x, y, z = float(args["x"]), float(args["y"]), float(args["z"])
    reuse = args.get("reuseExisting", True)
    number = args.get("number")
    support = args.get("support")

    r = robot()
    if reuse:
        nid = r.find_or_create_node(x, y, z, number=number)
    else:
        nodes = r.structure().Nodes
        nid = number or nodes.FreeNumber
        nodes.Create(nid, x, y, z)

    if support:
        _set_node_label(r.structure().Nodes, nid, I_LT_NODE_SUPPORT, support)

    return {"created": True, "id": nid, "x": x, "y": y, "z": z}


def _set_node_label(nodes_srv, nid: int, label_type: int, label_name: str) -> bool:
    """Assign a label to a node, using the GetAll() proxy (not server.Get).

    Robot 2013: nodes_srv.Get(id) returns IRobotDataObject (no SetLabel).
    coll.Get(i) from GetAll() returns IRobotNode which does have SetLabel.
    Returns True on success.
    """
    try:
        coll = nodes_srv.GetAll()
        for i in range(1, int(coll.Count) + 1):
            try:
                proxy = coll.Get(i)
                if int(proxy.Number) == nid:
                    proxy.SetLabel(label_type, label_name)
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


async def handle_robot_create_nodes(args: dict) -> dict:
    import json as _json
    reuse = args.get("reuseExisting", True)
    r = robot()
    nodes_arg = args["nodes"]
    if isinstance(nodes_arg, str):
        try:
            nodes_arg = _json.loads(nodes_arg)
        except Exception:
            raise ValueError("'nodes' must be a JSON array of node objects")
    created = []
    for item in nodes_arg:
        x, y, z = float(item["x"]), float(item["y"]), float(item["z"])
        number = item.get("number")
        support = item.get("support")
        if reuse:
            nid = r.find_or_create_node(x, y, z, number=number)
        else:
            nodes = r.structure().Nodes
            nid = number or nodes.FreeNumber
            nodes.Create(nid, x, y, z)
        if support:
            _set_node_label(r.structure().Nodes, nid, I_LT_NODE_SUPPORT, support)
        created.append(nid)
    return {"created": created, "count": len(created)}


async def handle_robot_create_bar(args: dict) -> dict:
    r = robot()
    reuse = args.get("reuseNodes", True)

    if "startNode" in args and "endNode" in args:
        sn, en = int(args["startNode"]), int(args["endNode"])
    elif "start" in args and "end" in args:
        sp, ep = args["start"], args["end"]
        sn = r.find_or_create_node(sp[0], sp[1], sp[2]) if reuse else None
        en = r.find_or_create_node(ep[0], ep[1], ep[2]) if reuse else None
        if sn is None:
            nodes = r.structure().Nodes
            sn = nodes.FreeNumber
            nodes.Create(sn, sp[0], sp[1], sp[2])
        if en is None:
            nodes = r.structure().Nodes
            en = nodes.FreeNumber
            nodes.Create(en, ep[0], ep[1], ep[2])
    else:
        raise ValueError("Provide startNode/endNode or start/end coordinates")

    bars = r.structure().Bars
    bid = args.get("number") or bars.FreeNumber
    bars.Create(bid, sn, en)

    # Robot 2013: bars.Get(id) returns IRobotDataObject after Create().
    # bars.GetAll() refreshes the collection and Get(id) returns IRobotBar.
    bars.GetAll()
    bar = bars.Get(bid)

    if "section" in args:
        r.load_section(args["section"])
        bar.SetLabel(I_LT_BAR_SECTION, args["section"])

    if "material" in args:
        r.load_material(args["material"])
        bar.SetLabel(I_LT_BAR_MATERIAL, args["material"])

    if "release" in args:
        bar.SetLabel(I_LT_BAR_RELEASE, args["release"])

    if "gamma" in args:
        bar.Gamma = float(args["gamma"])

    return {"created": True, "id": bid, "startNode": sn, "endNode": en}


async def handle_robot_create_bars(args: dict) -> dict:
    defaults = args.get("defaults", {})
    reuse = args.get("reuseNodes", True)
    created = []
    for item in args["bars"]:
        merged = {**defaults, **item}
        result = await handle_robot_create_bar({**merged, "reuseNodes": reuse})
        created.append(result["id"])
    return {"created": created, "count": len(created)}


async def handle_robot_create_panel(args: dict) -> dict:
    import json as _json
    r = robot()
    if r.is_bars_only_project() and not args.get("force"):
        raise ValueError(
            "Current project type (frame/truss) does not support panels. "
            "Use a 'shell' or 'plate' project, or pass force=true."
        )

    points = args["points"]
    if isinstance(points, str):
        try:
            points = _json.loads(points)
        except Exception:
            raise ValueError("'points' must be a JSON array of [x,y,z] arrays")

    contour = r.make_contour(points)

    panels = r.structure().Objects
    pid = args.get("number") or panels.FreeNumber
    panels.CreateContour(pid, contour)

    # ── Structural type (kind) ───────────────────────────────────
    kind = args.get("kind", "slab")
    ost = PANEL_KIND_TO_OST.get(kind, 0)

    # ── Thickness label ──────────────────────────────────────────
    # thickness parameter is in metres (e.g. 0.20 = 200 mm)
    th_label = args.get("thicknessLabel")
    if not th_label and "thickness" in args:
        th_m = float(args["thickness"])
        th_label = f"TH{round(th_m * 1000)}mm"
        labels = r.structure().Labels
        lbl = None
        try:
            lbl = labels.Create(I_LT_THICKNESS, th_label)
        except Exception:
            try:
                lbl = labels.Get(I_LT_THICKNESS, th_label)
            except Exception:
                pass
        if lbl is not None:
            th_data = lbl.Data
            # IRobotThicknessData → IRobotThicknessHomoData.ThickConst (metres)
            try:
                th_data.Data.ThickConst = th_m
            except Exception:
                try:
                    th_data.ThickConst = th_m
                except Exception:
                    pass
            if "material" in args:
                r.load_material(args["material"])
                try: th_data.MaterialName = args["material"]
                except Exception:
                    try: th_data.Data.MaterialName = args["material"]
                    except Exception: pass
            labels.Store(lbl)

    # ── Apply structural type + thickness label to panel ─────────
    # Robot 2013: use IRobotObj.SetLabel / .StructuralType directly (not .Main)
    try:
        coll2 = panels.GetAll()
        for _i in range(1, int(coll2.Count) + 1):
            try:
                _px = coll2.Get(_i)
                if int(_px.Number) == pid:
                    if th_label:
                        _px.SetLabel(I_LT_THICKNESS, th_label)
                    try:
                        _px.StructuralType = ost
                    except Exception:
                        pass
                    break
            except Exception:
                pass
    except Exception:
        pass

    return {"created": True, "id": pid, "kind": kind, "pointCount": len(points)}


async def handle_robot_delete(args: dict) -> dict:
    obj_type = args["type"]
    sel_text = args["selection"]

    if sel_text.lower() == "all" and not args.get("confirm"):
        raise ValueError("confirm=true required when selection='all'")

    r = robot()
    struc = r.structure()
    server_map = {"node": struc.Nodes, "bar": struc.Bars,
                  "panel": struc.Objects, "case": struc.Cases}
    server = server_map.get(obj_type)
    if server is None:
        raise ValueError(f"Unknown type: {obj_type}")

    sel = r.selection_from_text(sel_text, obj_type)
    server.DeleteMany(sel)
    return {"deleted": True, "selection": sel_text, "type": obj_type}


async def handle_robot_set_bar_section(args: dict) -> dict:
    r = robot()
    section = args["section"]
    r.load_section(section)

    if "material" in args:
        r.load_material(args["material"])

    bars = r.structure().Bars
    bar_ids = _bar_ids_for_selection(args["selection"], bars)
    if not bar_ids:
        raise ValueError(
            f"Selection '{args['selection']}' resolved to 0 bars."
        )

    bars.GetAll()
    assigned = 0
    for bid in bar_ids:
        try:
            bar = bars.Get(bid)
            bar.SetLabel(I_LT_BAR_SECTION, section)
            if "material" in args:
                bar.SetLabel(I_LT_BAR_MATERIAL, args["material"])
            assigned += 1
        except Exception:
            continue
    return {"assigned": True, "section": section, "barCount": assigned}


async def handle_robot_set_bar_material(args: dict) -> dict:
    r = robot()
    material = args["material"]
    loaded = r.load_material(material)
    if not loaded:
        raise ValueError(
            f"Material '{material}' not found in project or active databases. "
            "Create it first with robot_create_material or check the name."
        )

    bars = r.structure().Bars
    bar_ids = _bar_ids_for_selection(args["selection"], bars)
    if not bar_ids:
        raise ValueError(
            f"Selection '{args['selection']}' resolved to 0 bars. "
            "Check that the bar IDs exist in the model."
        )

    # Warm up bar server so Get(id) returns IRobotBar
    bars.GetAll()
    assigned = 0
    for bid in bar_ids:
        try:
            bars.Get(bid).SetLabel(I_LT_BAR_MATERIAL, material)
            assigned += 1
        except Exception:
            continue
    return {"assigned": True, "material": material, "barCount": assigned}


async def handle_robot_set_bar_release(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    labels = struc.Labels
    remove = args.get("remove", False)
    sel_text = args["selection"]

    if remove:
        bars = struc.Bars
        bar_ids = _bar_ids_for_selection(sel_text, bars)
        bars.GetAll()
        for bid in bar_ids:
            try: bars.Get(bid).RemoveLabel(I_LT_BAR_RELEASE)
            except Exception: pass
        return {"removed": True, "barCount": len(bar_ids)}

    preset = args.get("preset")
    rel_name = args.get("name", preset or "Release")

    # Build or reuse release label
    try:
        labels.Get(I_LT_BAR_RELEASE, rel_name)
    except Exception:
        lbl = labels.Create(I_LT_BAR_RELEASE, rel_name)
        data = lbl.Data
        if preset == "pinned":
            data.StartNode.RX = True; data.StartNode.RY = True; data.StartNode.RZ = True
            data.EndNode.RX   = True; data.EndNode.RY   = True; data.EndNode.RZ   = True
        elif preset == "pin-fix":
            data.StartNode.RX = True; data.StartNode.RY = True; data.StartNode.RZ = True
        elif preset == "fix-pin":
            data.EndNode.RX   = True; data.EndNode.RY   = True; data.EndNode.RZ   = True
        elif preset == "truss":
            for end in [data.StartNode, data.EndNode]:
                end.RX = True; end.RY = True; end.RZ = True
                end.UY = True; end.UZ = True
        elif "start" in args or "end" in args:
            for end_name, key in [("StartNode", "start"), ("EndNode", "end")]:
                if key in args:
                    end_data = getattr(data, end_name)
                    for dof, val in args[key].items():
                        try: setattr(end_data, dof.upper(), bool(val))
                        except Exception: pass
        labels.Store(lbl)

    bars = struc.Bars
    bar_ids = _bar_ids_for_selection(sel_text, bars)
    bars.GetAll()
    for bid in bar_ids:
        try: bars.Get(bid).SetLabel(I_LT_BAR_RELEASE, rel_name)
        except Exception: pass

    return {"assigned": True, "release": rel_name, "barCount": len(bar_ids)}


def _node_ids_for_selection(sel_text: str, nodes_srv) -> list[int]:
    """Return node IDs for a selection text, bypassing the COM Selections API
    which does not work reliably for nodes in Robot 2013.

    For 'all': iterates via GetAll().
    Otherwise: parses the text directly (supports '1 2 5to10 15by2').
    """
    if sel_text.strip().lower() == "all":
        ids: list[int] = []
        try:
            coll = nodes_srv.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    ids.append(int(coll.Get(i).Number))
                except Exception:
                    pass
        except Exception:
            pass
        return ids
    return _parse_id_text(sel_text)


async def handle_robot_set_support(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    labels = struc.Labels
    remove = args.get("remove", False)
    sel_text = args["selection"]
    preset = args.get("preset")
    sup_name = args.get("support", preset or "Support")

    nodes_srv = struc.Nodes
    # Warm up the nodes collection so Get(id) returns real objects
    nodes_srv.GetAll()

    if remove:
        node_ids = _node_ids_for_selection(sel_text, nodes_srv)
        removed = 0
        try:
            coll = nodes_srv.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    proxy = coll.Get(i)
                    if int(proxy.Number) in node_ids:
                        proxy.RemoveLabel(I_LT_NODE_SUPPORT)
                        removed += 1
                except Exception:
                    pass
        except Exception:
            pass
        return {"removed": True, "nodeCount": removed}

    # ── Build / verify support label ──────────────────────────────
    existing = None
    try:
        existing = labels.Get(I_LT_NODE_SUPPORT, sup_name)
    except Exception:
        pass

    if existing is None:
        # Create the label only when it truly doesn't exist
        if preset is None and not any(
            k in args for k in ["ux", "uy", "uz", "rx", "ry", "rz",
                                 "kx", "ky", "kz", "hx", "hy", "hz"]
        ):
            raise ValueError(
                f"Support label '{sup_name}' not found. "
                "Create it first with robot_create_support_label, "
                "or pass preset='fixed'/'pinned' to auto-create."
            )
        # Remove any conflicting label with the same name but wrong type
        # (Robot.Create returns the existing one instead of creating a new one)
        import win32com.client as _wc
        for _ct in [1, 2]:  # I_LT_NODE_RELEASE=1, I_LT_NODE_COMPATIBILITY=2
            try: labels.Delete(_ct, sup_name)
            except Exception: pass
        lbl = labels.Create(I_LT_NODE_SUPPORT, sup_name)
        # Force IRobotNodeSupportData interface (lbl.Data returns typeless IDispatch)
        try:
            data = _wc.CastTo(lbl.Data, "IRobotNodeSupportData")
        except Exception:
            data = lbl.Data
        # I_NSFD_UX=0 .. I_NSFD_RZ=5 — use SetFixed(direction, 1) if available
        # else fall back to property assignment (works on both support/compat data)
        def _fix_dof(d, direction_idx, dof_name):
            try: d.SetFixed(direction_idx, 1)
            except Exception:
                try: setattr(d, dof_name, 1)
                except Exception: pass
        def _free_dof(d, direction_idx, dof_name):
            try: d.SetFixed(direction_idx, 0)
            except Exception:
                try: setattr(d, dof_name, 0)
                except Exception: pass
        if preset == "fixed":
            for _di, _dn in enumerate(["UX", "UY", "UZ", "RX", "RY", "RZ"]):
                _fix_dof(data, _di, _dn)
        elif preset == "pinned":
            for _di, _dn in enumerate(["UX", "UY", "UZ"]):
                _fix_dof(data, _di, _dn)
            for _di, _dn in enumerate(["RX", "RY", "RZ"], 3):
                _free_dof(data, _di, _dn)
        elif preset == "roller_x":
            _fix_dof(data, 1, "UY"); _fix_dof(data, 2, "UZ")
        elif preset == "roller_y":
            _fix_dof(data, 0, "UX"); _fix_dof(data, 2, "UZ")
        else:
            for _di, dof in enumerate(["UX", "UY", "UZ", "RX", "RY", "RZ"]):
                if dof.lower() in args:
                    if args[dof.lower()]: _fix_dof(data, _di, dof)
                    else: _free_dof(data, _di, dof)
            for spring in ["KX", "KY", "KZ", "HX", "HY", "HZ"]:
                if spring.lower() in args:
                    try: setattr(data, spring, float(args[spring.lower()]))
                    except Exception: pass
        labels.Store(lbl)

    # ── Assign label to nodes ──────────────────────────────────────
    node_ids = _node_ids_for_selection(sel_text, nodes_srv)
    if not node_ids:
        raise ValueError(
            f"Selection '{sel_text}' resolved to 0 nodes. "
            "Check that the node IDs exist in the model."
        )

    assigned = 0
    for nid in node_ids:
        if _set_node_label(nodes_srv, nid, I_LT_NODE_SUPPORT, sup_name):
            assigned += 1

    return {"assigned": True, "support": sup_name, "nodeCount": assigned}


async def handle_robot_set_panel_thickness(args: dict) -> dict:
    r = robot()
    th_mm = float(args.get("thickness", 0))
    name = args.get("name") or (f"TH{int(th_mm)}" if th_mm else None)
    if not name:
        raise ValueError("Provide thickness (mm) or name")

    # ── Create/update thickness label ────────────────────────────
    labels = r.structure().Labels
    lbl = None
    try:
        lbl = labels.Create(I_LT_THICKNESS, name)
    except Exception:
        try:
            lbl = labels.Get(I_LT_THICKNESS, name)
        except Exception:
            pass
    if lbl is not None:
        th_data = lbl.Data
        if th_mm:
            # IRobotThicknessData → IRobotThicknessHomoData.ThickConst (metres)
            try:
                th_data.Data.ThickConst = th_mm / 1000.0
            except Exception:
                try:
                    th_data.ThickConst = th_mm / 1000.0
                except Exception:
                    pass
        if "material" in args:
            r.load_material(args["material"])
            try: th_data.MaterialName = args["material"]
            except Exception:
                try: th_data.Data.MaterialName = args["material"]
                except Exception: pass
        labels.Store(lbl)

    # ── Parse selection ───────────────────────────────────────────
    sel_text = args.get("selection", "all")
    is_all = sel_text.strip().lower() == "all"
    panel_ids = None if is_all else set(_parse_id_text(sel_text))

    # ── Assign using GetAll() + obj.SetLabel (IRobotObj.SetLabel, not .Main.SetLabel)
    # Robot 2013: IRobotObj has SetLabel directly; .Main.SetLabel does not exist.
    panels_srv = r.structure().Objects
    assigned = 0
    try:
        coll = panels_srv.GetAll()
        n = int(coll.Count)
    except Exception:
        n = 0
        coll = None
    for i in range(1, n + 1):
        try:
            proxy = coll.Get(i)
        except Exception:
            continue
        # Skip non-panel objects (bars can appear in struc.Objects in some project types)
        try:
            if int(proxy.Main.DefPoints.Count) < 3:
                continue
        except Exception:
            continue
        try:
            pid = int(proxy.Number)
        except Exception:
            continue
        if panel_ids is not None and pid not in panel_ids:
            continue
        try:
            proxy.SetLabel(I_LT_THICKNESS, name)
            assigned += 1
        except Exception:
            pass

    return {"assigned": True, "label": name, "panelCount": assigned}


async def handle_robot_create_section(args: dict) -> dict:
    r = robot()
    name = args["name"]
    labels = r.structure().Labels

    # Create (or overwrite) the section label
    if args.get("overwrite"):
        try:
            labels.Delete(I_LT_BAR_SECTION, name)
        except Exception:
            pass
    lbl = None
    try:
        lbl = labels.Create(I_LT_BAR_SECTION, name)
    except Exception:
        try:
            lbl = labels.Get(I_LT_BAR_SECTION, name)
        except Exception:
            pass
    if lbl is None:
        raise ValueError(f"Could not create or retrieve section label '{name}'")

    # ── Load from database (catalogued section) ───────────────────────────
    if args.get("fromDatabase"):
        loaded = False
        try:
            lbl.Data.LoadFromDBase(args["fromDatabase"])
            loaded = True
        except Exception:
            pass
        labels.Store(lbl)
        return {"created": True, "name": name, "source": "database", "dbLoaded": loaded}

    # ── Parametric / non-standard section ─────────────────────────────────
    # Two distinct Robot 2013 API paths:
    #
    # A. CONCRETE rect (kind="column" or "beam"):
    #    data.Type = I_BST_NS_RECT
    #    data.ShapeType = I_BSST_CONCR_COL_R (-108) or I_BSST_CONCR_BEAM_RECT (-3)
    #    conc = data.Concrete                 (IRobotBarSectionConcreteData)
    #    conc.SetValue(I_BSCDV_COL_H=0, h_m)
    #    conc.SetValue(I_BSCDV_COL_B=1, b_m)
    #    data.CalcNonstdGeometry()
    #    data.MaterialName = ...
    #    labels.Store(lbl)
    #
    # B. STEEL / nonstd (all other shapes, or shape="rect" kind="steel"):
    #    data.Type = I_BST_NS_*
    #    data.CreateNonstd(0)
    #    data.SetValue(I_BSNDV_H/B/TF/TW, m)
    #    data.CalcNonstdGeometry()
    #    data.MaterialName = ...
    #    labels.Store(lbl)
    from ..robot_client import (
        I_BST_NS_RECT, I_BST_NS_BOX, I_BST_NS_I,
        I_BST_NS_TUBE, I_BST_NS_T,   I_BST_NS_C,
        I_BSNDV_H, I_BSNDV_B, I_BSNDV_TF, I_BSNDV_TW, I_BSNDV_D, I_BSNDV_T,
        I_BSST_CONCR_COL_R, I_BSST_CONCR_BEAM_RECT,
        I_BSCDV_COL_H, I_BSCDV_COL_B,
        I_BSCDV_BEAM_RECT_H, I_BSCDV_BEAM_RECT_B,
    )

    shape = args.get("shape", "rect")
    kind  = args.get("kind", "column")   # "column" | "beam" | "steel"

    # Path A — concrete rectangular section
    if shape == "rect" and kind in ("column", "beam"):
        data = lbl.Data
        try:
            data.Type = I_BST_NS_RECT
        except Exception:
            pass
        try:
            data.ShapeType = I_BSST_CONCR_COL_R if kind == "column" else I_BSST_CONCR_BEAM_RECT
        except Exception:
            pass

        h_m = float(args.get("h", 0)) / 1000.0
        b_m = float(args.get("b", 0)) / 1000.0
        try:
            conc = data.Concrete
            if kind == "column":
                if h_m: conc.SetValue(I_BSCDV_COL_H, h_m)
                if b_m: conc.SetValue(I_BSCDV_COL_B, b_m)
            else:
                if h_m: conc.SetValue(I_BSCDV_BEAM_RECT_H, h_m)
                if b_m: conc.SetValue(I_BSCDV_BEAM_RECT_B, b_m)
        except Exception:
            pass

        if "material" in args:
            r.load_material(args["material"])
            try: data.MaterialName = args["material"]
            except Exception: pass

        try:
            data.CalcNonstdGeometry()
        except Exception:
            pass

        if "material" in args:
            # Re-apply after CalcNonstdGeometry (Robot may reset it)
            try: data.MaterialName = args["material"]
            except Exception: pass

        labels.Store(lbl)
        return {"created": True, "name": name, "shape": shape, "kind": kind}

    # Path B — steel / nonstd section
    shape_map = {
        "rect": I_BST_NS_RECT, "box": I_BST_NS_BOX, "i": I_BST_NS_I,
        "tube": I_BST_NS_TUBE, "t":   I_BST_NS_T,   "c": I_BST_NS_C,
    }
    shape_id = shape_map.get(shape, I_BST_NS_RECT)
    data = lbl.Data

    try:
        data.Type = shape_id
    except Exception:
        pass

    # Allocate non-standard geometry slot (required before SetValue for steel path)
    try:
        data.CreateNonstd(0)
    except Exception:
        pass

    def _sv(idx: int, mm_val: float) -> None:
        try:
            data.SetValue(idx, mm_val / 1000.0)
        except Exception:
            pass

    if shape == "tube":
        if "d" in args: _sv(I_BSNDV_D, float(args["d"]))
        if "t" in args: _sv(I_BSNDV_T, float(args["t"]))
    else:
        if "h"  in args: _sv(I_BSNDV_H,  float(args["h"]))
        if "b"  in args: _sv(I_BSNDV_B,  float(args["b"]))
        if "tf" in args: _sv(I_BSNDV_TF, float(args["tf"]))
        if "tw" in args: _sv(I_BSNDV_TW, float(args["tw"]))

    try:
        data.CalcNonstdGeometry()
    except Exception:
        pass

    if "material" in args:
        r.load_material(args["material"])
        try:
            data.MaterialName = args["material"]
        except Exception:
            pass

    labels.Store(lbl)
    return {"created": True, "name": name, "shape": shape}


async def handle_robot_create_material(args: dict) -> dict:
    r = robot()
    name = args["name"]
    labels = r.structure().Labels

    # Create label or retrieve if it already exists
    try:
        lbl = labels.Create(I_LT_BAR_MATERIAL, name)
    except Exception:
        try:
            lbl = labels.Get(I_LT_BAR_MATERIAL, name)
        except Exception:
            lbl = None
    if lbl is None:
        raise ValueError(f"Could not create or retrieve material label '{name}'")

    if args.get("fromDatabase"):
        loaded = False
        try:
            lbl.Data.LoadFromDBase(args["fromDatabase"])
            loaded = True
        except Exception:
            pass
        try:
            labels.Store(lbl)
        except Exception:
            pass
        return {"created": True, "name": name, "source": "database", "dbLoaded": loaded}

    data = lbl.Data
    mat_type = MATERIAL_TYPES.get(args.get("type", "steel"), I_MT_STEEL)
    try:
        data.Type = mat_type  # Read-only in some Robot 2013 builds — safe to skip
    except Exception:
        pass

    prop_map = {"E_MPa": ("E", 1e6), "nu": ("NU", 1),
                "density_kg_m3": ("RO", 1), "fy_MPa": ("RE", 1e6), "fu_MPa": ("RT", 1e6)}
    for key, (attr, scale) in prop_map.items():
        if key in args:
            try: setattr(data, attr, float(args[key]) * scale)
            except Exception: pass

    try:
        labels.Store(lbl)
    except Exception:
        pass
    return {"created": True, "name": name}


async def handle_robot_create_support_label(args: dict) -> dict:
    r = robot()
    name = args["name"]
    labels = r.structure().Labels
    lbl = labels.Create(I_LT_NODE_SUPPORT, name)
    data = lbl.Data

    for dof in ["UX", "UY", "UZ", "RX", "RY", "RZ"]:
        key = dof.lower()
        if key in args:
            setattr(data, dof, 1 if args[key] else 0)

    for spring in ["kx", "ky", "kz", "hx", "hy", "hz"]:
        if spring in args:
            setattr(data, spring.upper(), float(args[spring]))

    labels.Store(lbl)
    return {"created": True, "name": name}


async def handle_robot_transform(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    op = args["operation"]
    obj_type = args.get("type", "bar")
    sel_text = args["selection"]
    copy_mode = args.get("copy", False)
    reps = args.get("repetitions", 1)

    sel = r.selection_from_text(sel_text, obj_type)
    obj_server_map = {"node": struc.Nodes, "bar": struc.Bars, "panel": struc.Objects}
    server = obj_server_map.get(obj_type, struc.Bars)

    if op == "move":
        dx = float(args.get("dx", 0))
        dy = float(args.get("dy", 0))
        dz = float(args.get("dz", 0))
        # Robot 2013: Move is done by direct coordinate update (no server.Move)
        ids = r.ids_from_selection(sel_text, obj_type)
        if obj_type == "node":
            for nid in ids:
                try:
                    n = struc.Nodes.Get(nid)
                    n.X = float(n.X) + dx
                    n.Y = float(n.Y) + dy
                    n.Z = float(n.Z) + dz
                except Exception:
                    pass
        elif obj_type == "bar":
            moved: set = set()
            for bid in ids:
                try:
                    bar = struc.Bars.Get(bid)
                    for nid in (int(bar.StartNode), int(bar.EndNode)):
                        if nid in moved:
                            continue
                        n = struc.Nodes.Get(nid)
                        n.X = float(n.X) + dx
                        n.Y = float(n.Y) + dy
                        n.Z = float(n.Z) + dz
                        moved.add(nid)
                except Exception:
                    pass

    elif op == "copy":
        dx = float(args.get("dx", 0))
        dy = float(args.get("dy", 0))
        dz = float(args.get("dz", 0))
        # Robot 2013: copy nodes by creating new nodes at offset positions
        if obj_type == "node":
            ids = r.ids_from_selection(sel_text, "node")
            for nid in ids:
                try:
                    n = struc.Nodes.Get(nid)
                    new_id = int(struc.Nodes.FreeNumber)
                    struc.Nodes.Create(new_id,
                                       float(n.X) + dx,
                                       float(n.Y) + dy,
                                       float(n.Z) + dz)
                except Exception:
                    pass

    elif op == "rotate":
        angle = float(args.get("angle", 0))
        ap = args.get("axisPoint", [0, 0, 0])
        ap2 = args.get("axisPoint2", [0, 0, 1])
        import win32com.client as win32  # type: ignore
        pt1 = win32.Dispatch("Robot.GeoPoint3D")
        pt1.X = ap[0]; pt1.Y = ap[1]; pt1.Z = ap[2]
        pt2 = win32.Dispatch("Robot.GeoPoint3D")
        pt2.X = ap2[0]; pt2.Y = ap2[1]; pt2.Z = ap2[2]
        if copy_mode:
            server.RotateCopy(sel, pt1, pt2, angle)
        else:
            server.Rotate(sel, pt1, pt2, angle)

    elif op == "mirror":
        pts = args.get("plane", [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        import win32com.client as win32  # type: ignore
        plane_pts = []
        for p in pts[:3]:
            pt = win32.Dispatch("Robot.GeoPoint3D")
            pt.X = p[0]; pt.Y = p[1]; pt.Z = p[2]
            plane_pts.append(pt)
        if copy_mode:
            server.MirrorCopy(sel, plane_pts[0], plane_pts[1], plane_pts[2])
        else:
            server.Mirror(sel, plane_pts[0], plane_pts[1], plane_pts[2])

    return {"operation": op, "type": obj_type, "selection": sel_text}


async def handle_robot_create_axes(args: dict) -> dict:
    """Create a cartesian structural-axes grid in Robot 2013.

    Robot 2013 COM API path:
      app.Project.AxisMngr  (IRobotStructuralAxisGridMngr)
        .Create(I_SAGT_CARTESIAN, name)  -> IRobotStructuralAxisGrid
        CastTo -> IRobotStructuralAxisGridCartesian  (has .X / .Y / .Z)
          .X  ->  IRobotStructuralAxisSequenceList
            .StartPosition = first_pos
            .AddSequence(spacing, 1)  for each interval
            .SetLabelFormat(I_SALT_*)
            .SetAxisLabel(1-based-idx, label)
        .Save()
      mngr.Activate(FindByName(name), True)
    """
    import win32com.client as win32  # type: ignore

    name    = args.get("name", "Grille DXF")
    replace = args.get("replace", True)
    x_vals   = args.get("x", [])
    y_vals   = args.get("y", [])
    z_vals   = args.get("z", [])
    x_labels = args.get("xLabels", [])
    y_labels = args.get("yLabels", [])
    z_labels = args.get("zLabels", [])

    app = robot().app()

    # ── Step 1: get AxisMngr ─────────────────────────────────────
    try:
        mngr = app.Project.AxisMngr
    except Exception as exc:
        return {"error": f"app.Project.AxisMngr inaccessible: {exc}"}

    # ── Step 2: delete existing grid if replace=True ─────────────
    try:
        existing_idx = mngr.FindByName(name)
        if existing_idx:
            if replace:
                mngr.Delete(existing_idx)
            else:
                return {"error": f"A grid named '{name}' already exists (index {existing_idx}). Use replace=true to overwrite."}
    except Exception as exc:
        return {"error": f"FindByName/Delete failed: {exc}"}

    # ── Step 3: create grid ──────────────────────────────────────
    try:
        grid_base = mngr.Create(I_SAGT_CARTESIAN, name)
    except Exception as exc:
        return {"error": f"mngr.Create(I_SAGT_CARTESIAN, '{name}') failed: {exc}"}

    if grid_base is None:
        return {"error": f"mngr.Create returned None for name='{name}'. Project type may not support structural axes."}

    # ── Step 4: cast to cartesian interface (has .X/.Y/.Z) ───────
    try:
        grid = win32.CastTo(grid_base, "IRobotStructuralAxisGridCartesian")
    except Exception as exc:
        return {"error": f"CastTo IRobotStructuralAxisGridCartesian failed: {exc}"}

    # ── Step 5: populate each axis ───────────────────────────────
    def _fill_axis(seq, positions: list, labels: list, default_label_type: int, axis_name: str) -> str | None:
        """Fill an IRobotStructuralAxisSequenceList from absolute positions.

        AddSequence(_distance, _repeat_number) uses SPACING (interval),
        not absolute positions. The first position is set via StartPosition.
        Returns an error string on failure, or None on success.
        """
        if not positions:
            return None
        try:
            seq.Clear()
            seq.StartPosition = float(positions[0])
            for i in range(1, len(positions)):
                spacing = float(positions[i]) - float(positions[i - 1])
                seq.AddSequence(spacing, 1)
        except Exception as exc:
            return f"{axis_name} AddSequence failed: {exc}"
        try:
            if labels:
                seq.SetLabelFormat(I_SALT_DEFINE)
                for i, lbl in enumerate(labels):
                    seq.SetAxisLabel(i + 1, str(lbl))
            else:
                seq.SetLabelFormat(default_label_type)
        except Exception as exc:
            return f"{axis_name} SetLabelFormat/SetAxisLabel failed: {exc}"
        return None

    errors: list[str] = []
    for seq_attr, positions, labels, default_ltype, aname in (
        ("X", x_vals, x_labels, I_SALT_ABC,   "X"),
        ("Y", y_vals, y_labels, I_SALT_123,   "Y"),
        ("Z", z_vals, z_labels, I_SALT_VALUE, "Z"),
    ):
        if not positions:
            continue
        try:
            seq = getattr(grid, seq_attr)
        except Exception as exc:
            errors.append(f"grid.{seq_attr} inaccessible: {exc}")
            continue
        err = _fill_axis(seq, positions, labels, default_ltype, aname)
        if err:
            errors.append(err)

    # ── Step 6: save and activate ────────────────────────────────
    try:
        grid.Save()
    except Exception as exc:
        return {"error": f"grid.Save() failed: {exc}"}

    try:
        grid_idx = mngr.FindByName(name)
        if grid_idx:
            mngr.Activate(grid_idx, True)
    except Exception as exc:
        errors.append(f"Activate failed: {exc}")

    result: dict = {
        "grid": name,
        "axes": {
            "x": len(x_vals),
            "y": len(y_vals),
            "z": len(z_vals),
        },
        "total": len(x_vals) + len(y_vals) + len(z_vals),
    }
    if errors:
        result["warnings"] = errors
    return result


async def handle_robot_set_bar_gamma(args: dict) -> dict:
    """N2 — Set bar gamma (rotation about bar axis) in degrees."""
    r = robot()
    angle = float(args["angle"])
    bars = r.structure().Bars
    bar_ids = _bar_ids_for_selection(args["selection"], bars)
    if not bar_ids:
        raise ValueError(
            f"Selection '{args['selection']}' resolved to 0 bars."
        )

    bar_ids_set = set(bar_ids)
    assigned = 0
    try:
        coll = bars.GetAll()
        for _i in range(1, int(coll.Count) + 1):
            try:
                proxy = coll.Get(_i)
                if int(proxy.Number) not in bar_ids_set:
                    continue
                proxy.Gamma = angle
                assigned += 1
            except Exception:
                continue
    except Exception:
        pass
    return {"assigned": True, "angle": angle, "barCount": assigned}


async def handle_robot_get_axes(args: dict) -> dict:
    """N3 — Read back structural-axes grids from app.Project.AxisMngr.

    Robot 2013 API (confirmed by probing):
      mngr.Count                  → number of grids
      mngr.Get(idx)               → IRobotStructuralAxisGrid
      CastTo IRobotStructuralAxisGridCartesian → grid.X / .Y / .Z
      seq.AxisCount               → total number of axes in this direction
      seq.GetAxis(i)              → (active: bool, label: str, position: float, ...)
                                     1-based; stops when active==False
    """
    import win32com.client as win32  # type: ignore

    name_filter = args.get("name", "").strip()
    app = robot().app()

    try:
        mngr = app.Project.AxisMngr
    except Exception as exc:
        return {"error": f"app.Project.AxisMngr inaccessible: {exc}"}

    try:
        grid_count = int(mngr.Count)
    except Exception as exc:
        return {"error": f"AxisMngr.Count failed: {exc}"}

    def _read_seq(seq) -> dict:
        """Read one IRobotStructuralAxisSequenceList → {positions, labels}."""
        positions: list = []
        labels: list = []
        try:
            ax_count = int(seq.AxisCount)
        except Exception:
            ax_count = 0

        for i in range(1, ax_count + 1):
            try:
                entry = seq.GetAxis(i)
                # entry = (active: bool, label: str, position: float, highlighted: bool)
                active   = bool(entry[0])
                label    = str(entry[1])
                position = float(entry[2])
                if not active:
                    break
                positions.append(round(position, 6))
                labels.append(label)
            except Exception:
                break

        result: dict = {"positions": positions}
        if labels:
            result["labels"] = labels
        return result

    grids: list = []
    for idx in range(1, grid_count + 1):
        try:
            grid_base = mngr.Get(idx)
            if grid_base is None:
                continue
        except Exception:
            continue

        grid_info: dict = {}
        try:
            grid_info["name"] = str(grid_base.Name)
        except Exception:
            grid_info["name"] = f"Grid{idx}"

        if name_filter and name_filter.lower() not in grid_info["name"].lower():
            continue

        grid_info["index"] = idx

        try:
            grid = win32.CastTo(grid_base, "IRobotStructuralAxisGridCartesian")
        except Exception:
            grid = grid_base

        for axis_attr in ("X", "Y", "Z"):
            try:
                seq = getattr(grid, axis_attr)
                data = _read_seq(seq)
                if data["positions"]:
                    grid_info[axis_attr.lower()] = data
            except Exception:
                pass

        grids.append(grid_info)

    return {"grids": grids, "count": len(grids)}


async def handle_robot_clear_structure(args: dict) -> dict:
    if not args.get("confirm"):
        raise ValueError("confirm=true is required to clear the structure")
    struc = robot().structure()
    struc.Clear()
    return {"cleared": True}


async def handle_robot_build_frame(args: dict) -> dict:
    """Generate a regular multi-bay multi-storey frame."""
    r = robot()
    struc = r.structure()
    nodes = struc.Nodes
    bars = struc.Bars

    bays_x = args.get("baysX", [5.0])
    bays_y = args.get("baysY", [])
    storey_heights = args.get("storeyHeights", [])
    n_storeys = args.get("storeys", 3)
    storey_h = args.get("storeyHeight", 3.0)
    col_sec = args.get("columnSection", "HEA200")
    beam_sec_x = args.get("beamSection", "IPE300")
    beam_sec_y = args.get("beamSectionY", beam_sec_x)
    material = args.get("material", "S 355")
    support_type = args.get("support", "fixed")
    beam_release = args.get("beamRelease", "none")
    origin = args.get("origin", [0.0, 0.0, 0.0])
    dry_run = args.get("dryRun", False)

    if not storey_heights:
        storey_heights = [storey_h] * n_storeys

    # Grid
    xs = [origin[0]]
    for b in bays_x:
        xs.append(xs[-1] + b)

    ys = [origin[1]]
    if bays_y:
        for b in bays_y:
            ys.append(ys[-1] + b)

    zs = [origin[2]]
    for h in storey_heights:
        zs.append(zs[-1] + h)

    n_bays_x = len(bays_x)
    n_bays_y = len(bays_y) if bays_y else 0
    n_storeys_actual = len(storey_heights)
    total_nodes = len(xs) * len(ys) * len(zs)
    total_cols = len(xs) * len(ys) * n_storeys_actual
    total_beams_x = n_bays_x * len(ys) * (n_storeys_actual)
    total_beams_y = (n_bays_y * len(xs) * n_storeys_actual) if bays_y else 0

    if dry_run:
        return {
            "dryRun": True,
            "grid": {"x": xs, "y": ys, "z": zs},
            "estimatedNodes": total_nodes,
            "estimatedColumns": total_cols,
            "estimatedBeamsX": total_beams_x,
            "estimatedBeamsY": total_beams_y,
        }

    # Load sections/material
    r.load_section(col_sec)
    r.load_section(beam_sec_x)
    if bays_y:
        r.load_section(beam_sec_y)
    r.load_material(material)

    # Node number map: (xi, yi, zi) -> node_id
    node_map: dict = {}

    def get_node(xi: int, yi: int, zi: int) -> int:
        key = (xi, yi, zi)
        if key in node_map:
            return node_map[key]
        x = xs[xi]; y = ys[yi] if ys else 0.0; z = zs[zi]
        nid = nodes.FreeNumber
        nodes.Create(nid, x, y, z)
        node_map[key] = nid
        return nid

    cols_created = 0
    beams_created = 0
    n_yi = max(len(ys), 1)

    for yi in range(n_yi):
        for xi in range(len(xs)):
            for zi in range(len(zs)):
                get_node(xi, yi, zi)

    # Columns
    for yi in range(n_yi):
        for xi in range(len(xs)):
            for zi in range(n_storeys_actual):
                sn = get_node(xi, yi, zi)
                en = get_node(xi, yi, zi + 1)
                bid = bars.FreeNumber
                bars.Create(bid, sn, en)
                bar = bars.Get(bid)
                bar.SetLabel(I_LT_BAR_SECTION, col_sec)
                bar.SetLabel(I_LT_BAR_MATERIAL, material)
                cols_created += 1

    # Beams X
    for yi in range(n_yi):
        for xi in range(n_bays_x):
            for zi in range(1, len(zs)):
                sn = get_node(xi, yi, zi)
                en = get_node(xi + 1, yi, zi)
                bid = bars.FreeNumber
                bars.Create(bid, sn, en)
                bar = bars.Get(bid)
                bar.SetLabel(I_LT_BAR_SECTION, beam_sec_x)
                bar.SetLabel(I_LT_BAR_MATERIAL, material)
                if beam_release == "pinned":
                    try: bar.SetLabel(I_LT_BAR_RELEASE, "Pinned")
                    except Exception: pass
                beams_created += 1

    # Beams Y
    if bays_y:
        for xi in range(len(xs)):
            for yi in range(n_bays_y):
                for zi in range(1, len(zs)):
                    sn = get_node(xi, yi, zi)
                    en = get_node(xi, yi + 1, zi)
                    bid = bars.FreeNumber
                    bars.Create(bid, sn, en)
                    bar = bars.Get(bid)
                    bar.SetLabel(I_LT_BAR_SECTION, beam_sec_y)
                    bar.SetLabel(I_LT_BAR_MATERIAL, material)
                    beams_created += 1

    # Supports at base
    if support_type != "none":
        base_nodes = [get_node(xi, yi, 0) for yi in range(n_yi) for xi in range(len(xs))]
        sup_name = "Fixed" if support_type == "fixed" else "Pinned"
        labels = struc.Labels
        try:
            labels.Get(I_LT_NODE_SUPPORT, sup_name)
        except Exception:
            import win32com.client as _wc2
            for _ct2 in [1, 2]:
                try: labels.Delete(_ct2, sup_name)
                except Exception: pass
            lbl = labels.Create(I_LT_NODE_SUPPORT, sup_name)
            try: data = _wc2.CastTo(lbl.Data, "IRobotNodeSupportData")
            except Exception: data = lbl.Data
            if support_type == "fixed":
                for _di2, _dn2 in enumerate(["UX", "UY", "UZ", "RX", "RY", "RZ"]):
                    try: data.SetFixed(_di2, 1)
                    except Exception:
                        try: setattr(data, _dn2, 1)
                        except Exception: pass
            else:
                for _di2, _dn2 in enumerate(["UX", "UY", "UZ"]):
                    try: data.SetFixed(_di2, 1)
                    except Exception:
                        try: setattr(data, _dn2, 1)
                        except Exception: pass
            labels.Store(lbl)

        for nid in base_nodes:
            try: nodes.Get(nid).SetLabel(I_LT_NODE_SUPPORT, sup_name)
            except Exception: pass

    return {
        "built": True,
        "nodesCreated": len(node_map),
        "columnsCreated": cols_created,
        "beamsCreated": beams_created,
        "storeys": n_storeys_actual,
        "columnSection": col_sec,
        "beamSection": beam_sec_x,
    }


HANDLERS: dict[str, object] = {
    "robot_create_node":          handle_robot_create_node,
    "robot_create_nodes":         handle_robot_create_nodes,
    "robot_create_bar":           handle_robot_create_bar,
    "robot_create_bars":          handle_robot_create_bars,
    "robot_create_panel":         handle_robot_create_panel,
    "robot_delete":               handle_robot_delete,
    "robot_set_bar_section":      handle_robot_set_bar_section,
    "robot_set_bar_material":     handle_robot_set_bar_material,
    "robot_set_bar_release":      handle_robot_set_bar_release,
    "robot_set_support":          handle_robot_set_support,
    "robot_set_panel_thickness":  handle_robot_set_panel_thickness,
    "robot_create_section":       handle_robot_create_section,
    "robot_create_material":      handle_robot_create_material,
    "robot_create_support_label": handle_robot_create_support_label,
    "robot_transform":            handle_robot_transform,
    "robot_create_axes":          handle_robot_create_axes,
    "robot_set_bar_gamma":        handle_robot_set_bar_gamma,
    "robot_get_axes":             handle_robot_get_axes,
    "robot_clear_structure":      handle_robot_clear_structure,
    "robot_build_frame":          handle_robot_build_frame,
}
