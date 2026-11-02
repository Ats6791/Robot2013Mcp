"""
Model write tools — create/modify nodes, bars, panels, sections, materials, supports.
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import (
    robot,
    PROJECT_TYPES,
    I_LT_BAR_SECTION, I_LT_BAR_MATERIAL, I_LT_NODE_SUPPORT,
    I_LT_BAR_RELEASE, I_LT_THICKNESS,
    I_MT_STEEL, I_MT_CONCRETE, I_MT_TIMBER, I_MT_ALUMINIUM, I_MT_OTHER,
    MATERIAL_TYPES,
)


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
                "thickness":   {"type": "number",  "description": "Thickness in mm"},
                "thicknessLabel": {"type": "string", "description": "Existing thickness label name"},
                "material":    {"type": "string"},
                "number":      {"type": "integer"},
                "force":       {"type": "boolean", "description": "Create even in bars-only project"},
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
            "(shape: rect | box | i | tube | t | c) with dimensions in mm."
        ),
        inputSchema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name":         {"type": "string"},
                "fromDatabase": {"type": "string", "description": "Database section name to copy"},
                "shape":        {"type": "string", "enum": ["rect", "box", "i", "tube", "t", "c"]},
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
        r.structure().Nodes.Get(nid).SetLabel(I_LT_NODE_SUPPORT, support)

    return {"created": True, "id": nid, "x": x, "y": y, "z": z}


async def handle_robot_create_nodes(args: dict) -> dict:
    reuse = args.get("reuseExisting", True)
    r = robot()
    created = []
    for item in args["nodes"]:
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
            r.structure().Nodes.Get(nid).SetLabel(I_LT_NODE_SUPPORT, support)
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
    r = robot()
    if r.is_bars_only_project() and not args.get("force"):
        raise ValueError(
            "Current project type (frame/truss) does not support panels. "
            "Use a 'shell' or 'plate' project, or pass force=true."
        )

    points = args["points"]
    contour = r.make_contour(points)

    panels = r.structure().Objects
    pid = args.get("number") or panels.FreeNumber
    panels.CreateContour(pid, contour)

    # Thickness
    th_label = args.get("thicknessLabel")
    if not th_label and "thickness" in args:
        th_mm = float(args["thickness"])
        th_label = f"TH{int(th_mm)}"
        labels = r.structure().Labels
        try:
            labels.Get(I_LT_THICKNESS, th_label)
        except Exception:
            lbl = labels.Create(I_LT_THICKNESS, th_label)
            data = lbl.Data
            data.ThickConst = th_mm / 1000.0
            if "material" in args:
                r.load_material(args["material"])
                try: data.MaterialName = args["material"]
                except Exception: pass
            labels.Store(lbl)

    if th_label:
        try:
            panels.Get(pid).Main.SetLabel(I_LT_THICKNESS, th_label)
        except Exception:
            pass

    return {"created": True, "id": pid, "points": len(points)}


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

    sel = r.selection_from_text(args["selection"], "bar")
    bars = r.structure().Bars
    count = sel.Count
    for i in range(1, count + 1):
        try:
            bid = int(sel.Get(i))
            bar = bars.Get(bid)
            bar.SetLabel(I_LT_BAR_SECTION, section)
            if "material" in args:
                bar.SetLabel(I_LT_BAR_MATERIAL, args["material"])
        except Exception:
            continue
    return {"assigned": True, "section": section, "barCount": count}


async def handle_robot_set_bar_material(args: dict) -> dict:
    r = robot()
    material = args["material"]
    r.load_material(material)

    sel = r.selection_from_text(args["selection"], "bar")
    bars = r.structure().Bars
    count = sel.Count
    for i in range(1, count + 1):
        try:
            bar = bars.Get(int(sel.Get(i)))
            bar.SetLabel(I_LT_BAR_MATERIAL, material)
        except Exception:
            continue
    return {"assigned": True, "material": material, "barCount": count}


async def handle_robot_set_bar_release(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    labels = struc.Labels
    remove = args.get("remove", False)
    sel_text = args["selection"]

    if remove:
        sel = r.selection_from_text(sel_text, "bar")
        for i in range(1, sel.Count + 1):
            try: struc.Bars.Get(int(sel.Get(i))).RemoveLabel(I_LT_BAR_RELEASE)
            except Exception: pass
        return {"removed": True}

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

    sel = r.selection_from_text(sel_text, "bar")
    bars = struc.Bars
    for i in range(1, sel.Count + 1):
        try: bars.Get(int(sel.Get(i))).SetLabel(I_LT_BAR_RELEASE, rel_name)
        except Exception: pass

    return {"assigned": True, "release": rel_name, "barCount": sel.Count}


async def handle_robot_set_support(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    labels = struc.Labels
    remove = args.get("remove", False)
    sel_text = args["selection"]
    preset = args.get("preset")
    sup_name = args.get("support", preset or "Support")

    if remove:
        sel = r.selection_from_text(sel_text, "node")
        for i in range(1, sel.Count + 1):
            try: struc.Nodes.Get(int(sel.Get(i))).RemoveLabel(I_LT_NODE_SUPPORT)
            except Exception: pass
        return {"removed": True}

    # Build label if it doesn't exist
    try:
        labels.Get(I_LT_NODE_SUPPORT, sup_name)
    except Exception:
        lbl = labels.Create(I_LT_NODE_SUPPORT, sup_name)
        data = lbl.Data
        if preset == "fixed":
            data.SetFixed(1)
        elif preset == "pinned":
            data.UX = 1; data.UY = 1; data.UZ = 1
            data.RX = 0; data.RY = 0; data.RZ = 0
        elif preset == "roller_x":
            data.UY = 1; data.UZ = 1
        elif preset == "roller_y":
            data.UX = 1; data.UZ = 1
        else:
            # Explicit DOF flags
            for dof in ["UX", "UY", "UZ", "RX", "RY", "RZ"]:
                if dof.lower() in args:
                    setattr(data, dof, 1 if args[dof.lower()] else 0)
            # Springs
            for spring in ["KX", "KY", "KZ", "HX", "HY", "HZ"]:
                if spring.lower() in args:
                    setattr(data, spring, float(args[spring.lower()]))
        labels.Store(lbl)

    sel = r.selection_from_text(sel_text, "node")
    nodes = struc.Nodes
    count = sel.Count
    for i in range(1, count + 1):
        try: nodes.Get(int(sel.Get(i))).SetLabel(I_LT_NODE_SUPPORT, sup_name)
        except Exception: pass

    return {"assigned": True, "support": sup_name, "nodeCount": count}


async def handle_robot_set_panel_thickness(args: dict) -> dict:
    r = robot()
    th_mm = float(args.get("thickness", 0))
    name = args.get("name") or (f"TH{int(th_mm)}" if th_mm else None)
    if not name:
        raise ValueError("Provide thickness (mm) or name")

    labels = r.structure().Labels
    try:
        labels.Get(I_LT_THICKNESS, name)
    except Exception:
        lbl = labels.Create(I_LT_THICKNESS, name)
        data = lbl.Data
        if th_mm:
            data.ThickConst = th_mm / 1000.0
        if "material" in args:
            r.load_material(args["material"])
            try: data.MaterialName = args["material"]
            except Exception: pass
        labels.Store(lbl)

    sel = r.selection_from_text(args["selection"], "panel")
    panels = r.structure().Objects
    for i in range(1, sel.Count + 1):
        try: panels.Get(int(sel.Get(i))).Main.SetLabel(I_LT_THICKNESS, name)
        except Exception: pass

    return {"assigned": True, "label": name, "panelCount": sel.Count}


async def handle_robot_create_section(args: dict) -> dict:
    r = robot()
    name = args["name"]
    labels = r.structure().Labels

    # Create label or retrieve if it already exists (struc.Clear() does not clear labels)
    try:
        lbl = labels.Create(I_LT_BAR_SECTION, name)
    except Exception:
        try:
            lbl = labels.Get(I_LT_BAR_SECTION, name)
        except Exception:
            lbl = None
    if lbl is None:
        raise ValueError(f"Could not create or retrieve section label '{name}'")

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

    from ..robot_client import (I_BST_NS_RECT, I_BST_NS_BOX, I_BST_NS_I,
                                 I_BST_NS_TUBE, I_BST_NS_T, I_BST_NS_C)
    shape_map = {
        "rect": I_BST_NS_RECT, "box": I_BST_NS_BOX, "i": I_BST_NS_I,
        "tube": I_BST_NS_TUBE, "t":   I_BST_NS_T,   "c": I_BST_NS_C,
    }
    shape = args.get("shape", "rect")
    shape_id = shape_map.get(shape, I_BST_NS_RECT)

    data = lbl.Data
    try:
        data.Type = shape_id  # Read-only in some Robot 2013 builds — safe to skip
    except Exception:
        pass

    # Common dimension mapping (SetValue indices vary by Robot version; try both)
    dim_map = {"b": 2, "h": 3, "tf": 6, "tw": 5, "t": 4, "d": 2}
    for dim, idx in dim_map.items():
        if dim in args:
            try: data.SetValue(idx, float(args[dim]) / 1000.0)
            except Exception: pass

    if "material" in args:
        r.load_material(args["material"])
        try: data.MaterialName = args["material"]
        except Exception: pass

    try:
        labels.Store(lbl)
    except Exception:
        pass  # Robot 2013: Store may fail for incomplete parametric sections; label remains in session
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
            lbl = labels.Create(I_LT_NODE_SUPPORT, sup_name)
            data = lbl.Data
            if support_type == "fixed":
                data.SetFixed(1)
            else:
                data.UX = 1; data.UY = 1; data.UZ = 1
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
    "robot_clear_structure":      handle_robot_clear_structure,
    "robot_build_frame":          handle_robot_build_frame,
}
