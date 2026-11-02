"""
Model read tools — query nodes, bars, panels, labels, sections, materials.
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import (
    robot, _server_count, LABEL_TYPES,
    I_LT_BAR_SECTION, I_LT_BAR_MATERIAL, I_LT_NODE_SUPPORT,
    I_LT_BAR_RELEASE, I_LT_THICKNESS,
)


TOOLS: list[Tool] = [
    Tool(
        name="robot_summary",
        description=(
            "Model at a glance: node/bar/panel/case counts, "
            "bounding box, sections used, materials used, results status."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_list_nodes",
        description="List nodes with coordinates (m) and support label.",
        inputSchema={
            "type": "object",
            "properties": {
                "selection": {"type": "string", "description": "Node selection: numbers/ranges like '1 4 7to12' or 'all'"},
                "limit":     {"type": "integer", "description": "Max rows (default 500)"},
                "onlySupported": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_get_node",
        description="One node in detail: coordinates, support definition, connected bars.",
        inputSchema={
            "type": "object",
            "required": ["number"],
            "properties": {
                "number": {"type": "integer", "description": "Node number"},
            },
        },
    ),
    Tool(
        name="robot_find_nodes_at",
        description="Find nodes at/near a coordinate (metres).",
        inputSchema={
            "type": "object",
            "required": ["x", "y", "z"],
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "tolerance": {"type": "number", "description": "Distance tolerance m (default 0.001)"},
            },
        },
    ),
    Tool(
        name="robot_list_bars",
        description="List bars: start/end nodes, length, section, material, gamma.",
        inputSchema={
            "type": "object",
            "properties": {
                "selection":      {"type": "string", "description": "Bar selection"},
                "limit":          {"type": "integer"},
                "sectionFilter":  {"type": "string"},
                "materialFilter": {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_get_bar",
        description="One bar in detail: end nodes + coords, section properties, material, releases.",
        inputSchema={
            "type": "object",
            "required": ["number"],
            "properties": {
                "number": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_list_panels",
        description="List panels/slabs/walls: thickness, material, area, structural type.",
        inputSchema={
            "type": "object",
            "properties": {
                "selection":  {"type": "string"},
                "limit":      {"type": "integer"},
                "withPoints": {"type": "boolean", "description": "Include contour points"},
            },
        },
    ),
    Tool(
        name="robot_get_panel",
        description="One panel in detail: contour points, thickness, material, area.",
        inputSchema={
            "type": "object",
            "required": ["number"],
            "properties": {
                "number": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_list_supports",
        description="All support labels used in the project with their DOF definitions.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_list_labels",
        description="Labels of a given type defined in the project.",
        inputSchema={
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": list(LABEL_TYPES.keys()),
                    "description": "Label type",
                },
                "filter": {"type": "string", "description": "Substring filter"},
                "limit":  {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_get_label",
        description="Full definition of one label (section, material, support, release, thickness).",
        inputSchema={
            "type": "object",
            "required": ["type", "name"],
            "properties": {
                "type": {"type": "string", "enum": list(LABEL_TYPES.keys())},
                "name": {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_section_search",
        description="Search section names across active databases.",
        inputSchema={
            "type": "object",
            "properties": {
                "query":          {"type": "string", "description": "Substring"},
                "database":       {"type": "string"},
                "limit":          {"type": "integer", "description": "Max results (default 60)"},
                "withProperties": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_material_database",
        description="List materials in the material database.",
        inputSchema={
            "type": "object",
            "properties": {
                "type":       {"type": "string", "enum": ["steel", "concrete", "timber", "aluminium"]},
                "query":      {"type": "string"},
                "properties": {"type": "string", "description": "Material name to detail"},
                "limit":      {"type": "integer", "description": "Max names (default 100)"},
            },
        },
    ),
    Tool(
        name="robot_list_cases",
        description="List all load cases and combinations with id, name, nature, analysis type.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_get_case",
        description="One load case in detail: all load records with targets and values.",
        inputSchema={
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer", "description": "Case number"},
            },
        },
    ),
    Tool(
        name="robot_list_groups",
        description="Named object groups (bars/nodes/panels/cases).",
        inputSchema={
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["node", "bar", "panel", "case"]},
            },
        },
    ),
    Tool(
        name="robot_export_model_json",
        description=(
            "Export the whole model as JSON: nodes with supports, bars with section/material/release, "
            "panels with contour points, load cases with records. "
            "Optionally write to a file instead of returning inline."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "withLoads": {"type": "boolean", "description": "Include load data (default true)"},
                "path":      {"type": "string",  "description": "Write to this file instead of returning inline"},
            },
        },
    ),
]


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_summary(args: dict) -> dict:
    struc = robot().structure()
    result: dict = {}

    for attr, key in [("Nodes", "nodes"), ("Bars", "bars"),
                      ("Objects", "panels"), ("Cases", "cases")]:
        try:
            result[key] = _server_count(getattr(struc, attr))
        except Exception:
            result[key] = None

    result["resultsAvailable"] = robot().results_available()

    # Bounding box via nodes
    try:
        xs, ys, zs = [], [], []
        for _, n in _iter_server(struc.Nodes):
            xs.append(n.X); ys.append(n.Y); zs.append(n.Z)
        if xs:
            result["boundingBox"] = {
                "x": [round(min(xs), 4), round(max(xs), 4)],
                "y": [round(min(ys), 4), round(max(ys), 4)],
                "z": [round(min(zs), 4), round(max(zs), 4)],
            }
    except Exception:
        pass

    # Sections used
    try:
        sections: dict[str, int] = {}
        for _, bar in _iter_server(struc.Bars):
            try:
                name = str(bar.GetLabel(I_LT_BAR_SECTION).Name)
                sections[name] = sections.get(name, 0) + 1
            except Exception:
                continue
        if sections:
            result["sections"] = sections
    except Exception:
        pass

    return result


def _iter_server(server):
    """Yield (id, obj) pairs from a Robot 2013 object server.

    Robot 2013 servers (Nodes/Bars/Objects/Cases) have no .Count property.
    Uses GetAll() for enumeration and obj.Number for IDs, then server.Get(id)
    to retrieve the full COM object (collection proxies lack some methods).
    """
    try:
        coll = server.GetAll()
        n = int(coll.Count)
    except Exception:
        return
    for i in range(1, n + 1):
        try:
            proxy = coll.Get(i)
            try:
                oid = int(proxy.Number)
            except Exception:
                oid = i  # non-sequential fallback (shouldn't happen in practice)
            try:
                obj = server.Get(oid)
            except Exception:
                obj = proxy  # fallback to proxy if direct Get fails
            yield oid, obj
        except Exception:
            continue


async def handle_robot_list_nodes(args: dict) -> dict:
    struc = robot().structure()
    nodes = struc.Nodes
    limit = args.get("limit", 500)
    only_supported = args.get("onlySupported", False)
    sel_text = args.get("selection", "all")

    result_nodes = []
    total = _server_count(nodes)

    for i, node in _iter_server(nodes):
        if len(result_nodes) >= limit:
            break
        try:
            sup_label = None
            try:
                lbl = node.GetLabel(I_LT_NODE_SUPPORT)
                sup_label = str(lbl.Name)
            except Exception:
                pass
            if only_supported and not sup_label:
                continue
            result_nodes.append({
                "id": i,
                "x": round(node.X, 6),
                "y": round(node.Y, 6),
                "z": round(node.Z, 6),
                "support": sup_label,
            })
        except Exception:
            continue

    return {"nodes": result_nodes, "total": total, "returned": len(result_nodes)}


async def handle_robot_get_node(args: dict) -> dict:
    nid = int(args["number"])
    nodes_server = robot().structure().Nodes
    node = None
    x = y = z = None

    # Robot 2013: direct Get(id) can return a phantom COM proxy before GetAll() is called.
    # Use _iter_server (which calls GetAll() first) to locate the node reliably.
    for oid, obj in _iter_server(nodes_server):
        if oid == nid:
            try:
                x = round(float(obj.X), 6)
                y = round(float(obj.Y), 6)
                z = round(float(obj.Z), 6)
                node = obj
            except Exception:
                pass
            break

    if node is None:
        raise ValueError(f"Node {nid} not found")

    info: dict = {"id": nid, "x": x, "y": y, "z": z}

    # Support
    try:
        lbl = node.GetLabel(I_LT_NODE_SUPPORT)
        info["support"] = str(lbl.Name)
        data = lbl.Data
        dofs = {}
        for dof in ["UX", "UY", "UZ", "RX", "RY", "RZ"]:
            try: dofs[dof] = bool(getattr(data, dof))
            except Exception: pass
        info["supportDOFs"] = dofs
    except Exception:
        info["support"] = None

    # Connected bars
    try:
        bars = robot().structure().Bars
        connected = []
        for i, bar in _iter_server(bars):
            try:
                if bar.StartNode == nid or bar.EndNode == nid:
                    connected.append(i)
            except Exception:
                continue
        info["connectedBars"] = connected
    except Exception:
        pass

    return info


async def handle_robot_find_nodes_at(args: dict) -> dict:
    x, y, z = float(args["x"]), float(args["y"]), float(args["z"])
    tol = float(args.get("tolerance", 0.001))
    nodes = robot().structure().Nodes
    found = []
    for i, node in _iter_server(nodes):
        if abs(node.X - x) < tol and abs(node.Y - y) < tol and abs(node.Z - z) < tol:
            found.append({"id": i, "x": round(node.X, 6), "y": round(node.Y, 6), "z": round(node.Z, 6)})
    return {"found": found, "count": len(found)}


async def handle_robot_list_bars(args: dict) -> dict:
    struc = robot().structure()
    bars = struc.Bars
    nodes = struc.Nodes
    limit = args.get("limit", 500)
    sec_filter = args.get("sectionFilter", "").lower()
    mat_filter = args.get("materialFilter", "").lower()

    result_bars = []
    total = _server_count(bars)

    for i, bar in _iter_server(bars):
        if len(result_bars) >= limit:
            break
        try:
            sn, en = bar.StartNode, bar.EndNode
            row: dict = {"id": i, "startNode": sn, "endNode": en}

            # Length
            try:
                n1 = nodes.Get(sn); n2 = nodes.Get(en)
                dx = n2.X - n1.X; dy = n2.Y - n1.Y; dz = n2.Z - n1.Z
                row["length"] = round((dx**2 + dy**2 + dz**2)**0.5, 4)
            except Exception:
                pass

            # Section
            try:
                lbl = bar.GetLabel(I_LT_BAR_SECTION)
                sec_name = str(lbl.Name)
                row["section"] = sec_name
                if sec_filter and sec_filter not in sec_name.lower():
                    continue
            except Exception:
                if sec_filter:
                    continue

            # Material
            try:
                lbl = bar.GetLabel(I_LT_BAR_MATERIAL)
                mat_name = str(lbl.Name)
                row["material"] = mat_name
                if mat_filter and mat_filter not in mat_name.lower():
                    continue
            except Exception:
                if mat_filter:
                    continue

            # Gamma
            try: row["gamma"] = round(bar.Gamma, 3)
            except Exception: pass

            result_bars.append(row)
        except Exception:
            continue

    return {"bars": result_bars, "total": total, "returned": len(result_bars)}


async def handle_robot_get_bar(args: dict) -> dict:
    bid = int(args["number"])
    struc = robot().structure()
    bars_server = struc.Bars
    bar = None
    try:
        bar = bars_server.Get(bid)
        _ = bar.StartNode  # probe
    except Exception:
        bar = None
    if bar is None:
        try:
            coll = bars_server.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    proxy = coll.Get(i)
                    try:
                        pbid = int(proxy.Number)
                    except Exception:
                        pbid = i
                    if pbid == bid:
                        bar = proxy
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if bar is None:
        raise ValueError(f"Bar {bid} not found")

    sn, en = bar.StartNode, bar.EndNode
    info: dict = {"id": bid, "startNode": sn, "endNode": en}

    try:
        n1 = struc.Nodes.Get(sn); n2 = struc.Nodes.Get(en)
        info["start"] = [round(n1.X, 6), round(n1.Y, 6), round(n1.Z, 6)]
        info["end"]   = [round(n2.X, 6), round(n2.Y, 6), round(n2.Z, 6)]
        dx = n2.X - n1.X; dy = n2.Y - n1.Y; dz = n2.Z - n1.Z
        info["length"] = round((dx**2 + dy**2 + dz**2)**0.5, 4)
    except Exception:
        pass

    # Section
    try:
        lbl = bar.GetLabel(I_LT_BAR_SECTION)
        sec_data = lbl.Data
        sec_info: dict = {"name": str(lbl.Name)}
        for prop in ["Ax", "Iy", "Iz", "Ix", "Wply", "Wplz", "Wely", "Welz",
                     "b", "h", "tf", "tw", "d", "WeightPerLength"]:
            try:
                val = getattr(sec_data, prop)
                if val is not None:
                    sec_info[prop] = round(float(val), 8)
            except Exception:
                pass
        info["section"] = sec_info
    except Exception:
        info["section"] = None

    # Material
    try:
        lbl = bar.GetLabel(I_LT_BAR_MATERIAL)
        mat_data = lbl.Data
        mat_info: dict = {"name": str(lbl.Name)}
        for prop in ["E", "NU", "RO", "RE", "RT", "Kirch"]:
            try:
                val = getattr(mat_data, prop)
                if val is not None:
                    mat_info[prop] = float(val)
            except Exception:
                pass
        info["material"] = mat_info
    except Exception:
        info["material"] = None

    # Gamma
    try: info["gamma"] = round(bar.Gamma, 3)
    except Exception: pass

    # Release
    try:
        lbl = bar.GetLabel(I_LT_BAR_RELEASE)
        info["release"] = str(lbl.Name)
    except Exception:
        info["release"] = None

    return info


async def handle_robot_list_panels(args: dict) -> dict:
    struc = robot().structure()
    panels = struc.Objects
    limit = args.get("limit", 300)
    with_pts = args.get("withPoints", False)

    result_panels = []
    total = _server_count(panels)

    for i, panel in _iter_server(panels):
        if len(result_panels) >= limit:
            break
        try:
            row: dict = {"id": i}
            try:
                main = panel.Main
                try: row["structuralType"] = str(main.StructuralType)
                except Exception: pass
                try: row["thickness"] = str(main.GetLabel(I_LT_THICKNESS).Name)
                except Exception: pass
            except Exception:
                pass
            try: row["area"] = round(float(panel.Area), 4)
            except Exception: pass

            if with_pts:
                try:
                    contour = panel.Main.Contour
                    pts = contour.Points
                    cnt = pts.Count
                    row["contour"] = [
                        [round(pts.Get(j).X, 4), round(pts.Get(j).Y, 4), round(pts.Get(j).Z, 4)]
                        for j in range(1, cnt + 1)
                    ]
                except Exception:
                    pass

            result_panels.append(row)
        except Exception:
            continue

    return {"panels": result_panels, "total": total, "returned": len(result_panels)}


async def handle_robot_get_panel(args: dict) -> dict:
    pid = int(args["number"])
    objects_server = robot().structure().Objects
    panel = None
    # Robot 2013: Objects.Get(id) may return None; fall back to GetAll() collection
    try:
        panel = objects_server.Get(pid)
        if panel is not None:
            _ = panel.Main  # probe
    except Exception:
        panel = None
    if panel is None:
        try:
            coll = objects_server.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    proxy = coll.Get(i)
                    try:
                        ppid = int(proxy.Number)
                    except Exception:
                        ppid = i
                    if ppid == pid:
                        panel = proxy
                        break
                except Exception:
                    continue
        except Exception:
            pass
    if panel is None:
        raise ValueError(f"Panel {pid} not found")

    info: dict = {"id": pid}
    try: info["area"] = round(float(panel.Area), 4)
    except Exception: pass

    try:
        main = panel.Main
        try:
            lbl = main.GetLabel(I_LT_THICKNESS)
            info["thickness"] = str(lbl.Name)
            data = lbl.Data
            try: info["thicknessMm"] = round(float(data.ThickConst) * 1000, 2)
            except Exception: pass
        except Exception:
            pass

        try:
            contour = main.Contour
            pts = contour.Points
            cnt = pts.Count
            info["contour"] = [
                [round(pts.Get(j).X, 6), round(pts.Get(j).Y, 6), round(pts.Get(j).Z, 6)]
                for j in range(1, cnt + 1)
            ]
        except Exception:
            pass
    except Exception:
        pass

    return info


async def handle_robot_list_supports(args: dict) -> dict:
    struc = robot().structure()
    labels = struc.Labels
    result: list = []
    try:
        names = labels.GetAvailableNames(I_LT_NODE_SUPPORT)
        count = names.Count
        for i in range(1, count + 1):
            try:
                name = str(names.Get(i))
                lbl = labels.Get(I_LT_NODE_SUPPORT, name)
                data = lbl.Data
                sup: dict = {"name": name}
                for dof in ["UX", "UY", "UZ", "RX", "RY", "RZ"]:
                    try: sup[dof] = bool(getattr(data, dof))
                    except Exception: pass
                for spring in ["KX", "KY", "KZ", "HX", "HY", "HZ"]:
                    try:
                        val = float(getattr(data, spring))
                        if val != 0:
                            sup[spring] = val
                    except Exception:
                        pass
                result.append(sup)
            except Exception:
                continue
    except Exception:
        pass
    return {"supports": result}


async def handle_robot_list_labels(args: dict) -> dict:
    lbl_key = args["type"]
    lbl_type = LABEL_TYPES.get(lbl_key)
    if lbl_type is None:
        raise ValueError(f"Unknown label type: {lbl_key}")
    limit = args.get("limit", 300)
    filt = args.get("filter", "").lower()

    labels = robot().structure().Labels
    names: list[str] = []
    try:
        avail = labels.GetAvailableNames(lbl_type)
        count = avail.Count
        for i in range(1, count + 1):
            try:
                name = str(avail.Get(i))
                if filt and filt not in name.lower():
                    continue
                names.append(name)
                if len(names) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return {"type": lbl_key, "labels": names, "count": len(names)}


async def handle_robot_get_label(args: dict) -> dict:
    lbl_key = args["type"]
    name = args["name"]
    lbl_type = LABEL_TYPES.get(lbl_key)
    if lbl_type is None:
        raise ValueError(f"Unknown label type: {lbl_key}")

    labels = robot().structure().Labels
    lbl = labels.Get(lbl_type, name)
    if lbl is None:
        raise ValueError(f"Label '{name}' of type '{lbl_key}' not found")

    info: dict = {"type": lbl_key, "name": name}
    data = lbl.Data

    if lbl_type == I_LT_BAR_SECTION:
        for prop in ["Ax", "Iy", "Iz", "Ix", "Wply", "Wplz", "b", "h",
                     "tf", "tw", "d", "WeightPerLength"]:
            try:
                val = getattr(data, prop)
                if val is not None:
                    info[prop] = round(float(val), 8)
            except Exception:
                pass

    elif lbl_type == I_LT_BAR_MATERIAL:
        for prop in ["E", "NU", "RO", "RE", "RT", "LX"]:
            try:
                val = getattr(data, prop)
                if val is not None:
                    info[prop] = float(val)
            except Exception:
                pass

    elif lbl_type == I_LT_NODE_SUPPORT:
        for dof in ["UX", "UY", "UZ", "RX", "RY", "RZ"]:
            try: info[dof] = bool(getattr(data, dof))
            except Exception: pass
        for k in ["KX", "KY", "KZ", "HX", "HY", "HZ"]:
            try:
                val = float(getattr(data, k))
                if val: info[k] = val
            except Exception:
                pass

    elif lbl_type == I_LT_THICKNESS:
        try: info["thicknessMm"] = round(float(data.ThickConst) * 1000, 2)
        except Exception: pass

    return info


async def handle_robot_section_search(args: dict) -> dict:
    query = args.get("query", "").upper()
    limit = args.get("limit", 60)
    with_props = args.get("withProperties", False)

    labels = robot().structure().Labels
    results: list = []

    try:
        avail = labels.GetAvailableNames(I_LT_BAR_SECTION)
        count = avail.Count
        for i in range(1, count + 1):
            try:
                name = str(avail.Get(i))
                if query and query not in name.upper():
                    continue
                row: dict = {"name": name}
                if with_props:
                    try:
                        lbl = labels.Get(I_LT_BAR_SECTION, name)
                        data = lbl.Data
                        for prop in ["Ax", "Iy", "Iz", "WeightPerLength"]:
                            try: row[prop] = round(float(getattr(data, prop)), 8)
                            except Exception: pass
                    except Exception:
                        pass
                results.append(row)
                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass

    return {"results": results, "count": len(results)}


async def handle_robot_material_database(args: dict) -> dict:
    limit = args.get("limit", 100)
    type_filter = args.get("type", "").lower()
    query = args.get("query", "").upper()
    prop_name = args.get("properties")

    labels = robot().structure().Labels
    results: list = []

    try:
        avail = labels.GetAvailableNames(I_LT_BAR_MATERIAL)
        count = avail.Count
        for i in range(1, count + 1):
            try:
                name = str(avail.Get(i))
                if query and query not in name.upper():
                    continue
                results.append(name)
                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass

    if prop_name:
        try:
            lbl = labels.Get(I_LT_BAR_MATERIAL, prop_name)
            data = lbl.Data
            props: dict = {}
            for p in ["E", "NU", "RO", "RE", "RT", "LX"]:
                try: props[p] = float(getattr(data, p))
                except Exception: pass
            return {"name": prop_name, "properties": props}
        except Exception as e:
            return {"error": str(e)}

    return {"materials": results, "count": len(results)}


async def handle_robot_list_cases(args: dict) -> dict:
    cases = robot().structure().Cases
    result: list = []
    for i, case in _iter_server(cases):
        try:
            row: dict = {"id": i}
            try: row["name"] = str(case.Name)
            except Exception: pass
            try: row["nature"] = int(case.Nature)
            except Exception: pass
            try: row["analyzeType"] = int(case.AnalizeType)
            except Exception: pass
            result.append(row)
        except Exception:
            continue
    return {"cases": result, "total": len(result)}


async def handle_robot_get_case(args: dict) -> dict:
    cid = args["id"]
    case = robot().structure().Cases.Get(cid)
    if case is None:
        raise ValueError(f"Case {cid} not found")

    info: dict = {"id": cid}
    try: info["name"] = str(case.Name)
    except Exception: pass
    try: info["nature"] = int(case.Nature)
    except Exception: pass

    # Records
    try:
        records = case.Records
        count = records.Count
        recs = []
        for i in range(1, count + 1):
            try:
                rec = records.Get(i)
                rec_info: dict = {}
                try: rec_info["type"] = int(rec.Type)
                except Exception: pass
                try: rec_info["objects"] = str(rec.Objects.ToText())
                except Exception: pass
                recs.append(rec_info)
            except Exception:
                continue
        info["records"] = recs
    except Exception:
        info["records"] = []

    return info


async def handle_robot_list_groups(args: dict) -> dict:
    return {"groups": [], "note": "Group listing not yet implemented"}


async def handle_robot_export_model_json(args: dict) -> dict:
    import json
    with_loads = args.get("withLoads", True)
    out_path = args.get("path")

    struc = robot().structure()
    model: dict = {"nodes": [], "bars": [], "panels": [], "cases": []}

    # Nodes
    for i, node in _iter_server(struc.Nodes):
        n: dict = {"id": i, "x": round(node.X, 6), "y": round(node.Y, 6), "z": round(node.Z, 6)}
        try:
            lbl = node.GetLabel(I_LT_NODE_SUPPORT)
            n["support"] = str(lbl.Name)
        except Exception:
            pass
        model["nodes"].append(n)

    # Bars
    for i, bar in _iter_server(struc.Bars):
        b: dict = {"id": i, "startNode": bar.StartNode, "endNode": bar.EndNode}
        try: b["section"]  = str(bar.GetLabel(I_LT_BAR_SECTION).Name)
        except Exception: pass
        try: b["material"] = str(bar.GetLabel(I_LT_BAR_MATERIAL).Name)
        except Exception: pass
        try: b["release"]  = str(bar.GetLabel(I_LT_BAR_RELEASE).Name)
        except Exception: pass
        try: b["gamma"]    = round(bar.Gamma, 3)
        except Exception: pass
        model["bars"].append(b)

    # Panels (brief)
    for i, panel in _iter_server(struc.Objects):
        p: dict = {"id": i}
        try: p["area"] = round(float(panel.Area), 4)
        except Exception: pass
        model["panels"].append(p)

    # Cases
    if with_loads:
        for i, case in _iter_server(struc.Cases):
            try:
                c: dict = {"id": i}
                try: c["name"] = str(case.Name)
                except Exception: pass
                model["cases"].append(c)
            except Exception:
                continue

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(model, f, indent=2)
        return {"written": True, "path": out_path,
                "counts": {k: len(v) for k, v in model.items()}}

    return model


HANDLERS: dict[str, object] = {
    "robot_summary":           handle_robot_summary,
    "robot_list_nodes":        handle_robot_list_nodes,
    "robot_get_node":          handle_robot_get_node,
    "robot_find_nodes_at":     handle_robot_find_nodes_at,
    "robot_list_bars":         handle_robot_list_bars,
    "robot_get_bar":           handle_robot_get_bar,
    "robot_list_panels":       handle_robot_list_panels,
    "robot_get_panel":         handle_robot_get_panel,
    "robot_list_supports":     handle_robot_list_supports,
    "robot_list_labels":       handle_robot_list_labels,
    "robot_get_label":         handle_robot_get_label,
    "robot_section_search":    handle_robot_section_search,
    "robot_material_database": handle_robot_material_database,
    "robot_list_cases":        handle_robot_list_cases,
    "robot_get_case":          handle_robot_get_case,
    "robot_list_groups":       handle_robot_list_groups,
    "robot_export_model_json": handle_robot_export_model_json,
}
