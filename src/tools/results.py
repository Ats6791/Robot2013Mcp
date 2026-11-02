"""
Results tools — node displacements, support reactions, bar forces, bar stresses.
Robot 2013 compatible: uses .Available (not .Status).
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import robot


TOOLS: list[Tool] = [
    Tool(
        name="robot_node_displacements",
        description=(
            "Node displacements and rotations for a selection of nodes and cases. "
            "Returns UX, UY, UZ (mm), RX, RY, RZ (mrad)."
        ),
        inputSchema={
            "type": "object",
            "required": ["cases"],
            "properties": {
                "nodes":    {"type": "string", "description": "Node selection (default all)"},
                "cases":    {"type": "string", "description": "Case selection, e.g. '1 2 3'"},
                "limit":    {"type": "integer"},
                "components": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["UX", "UY", "UZ", "RX", "RY", "RZ"]},
                    "description": "Components to return (default all)",
                },
            },
        },
    ),
    Tool(
        name="robot_support_reactions",
        description=(
            "Support reactions at supported nodes for selected cases. "
            "Forces in kN, moments in kN·m."
        ),
        inputSchema={
            "type": "object",
            "required": ["cases"],
            "properties": {
                "cases": {"type": "string"},
                "nodes": {"type": "string", "description": "Supported node selection (default: all supported nodes)"},
                "limit": {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_bar_forces",
        description=(
            "Bar internal forces for selected bars and cases. "
            "FX (axial, kN), FY/FZ (shear, kN), MX (torsion, kN·m), MY/MZ (moment, kN·m). "
            "position: 0.0=start, 0.5=mid, 1.0=end."
        ),
        inputSchema={
            "type": "object",
            "required": ["cases"],
            "properties": {
                "bars":       {"type": "string", "description": "Bar selection (default all)"},
                "cases":      {"type": "string"},
                "position":   {"type": "number",  "description": "0.0-1.0 along bar (default 0.0 and 0.5 and 1.0)"},
                "positions":  {"type": "array", "items": {"type": "number"}},
                "limit":      {"type": "integer"},
                "components": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["FX", "FY", "FZ", "MX", "MY", "MZ"]},
                },
            },
        },
    ),
    Tool(
        name="robot_bar_stresses",
        description=(
            "Bar stresses for selected bars and cases: Smax, Smin, SmaxMY, SmaxMZ, "
            "SminMY, SminMZ, FXSX (axial). Stresses in MPa. position 0.0-1.0 (default 0.5)."
        ),
        inputSchema={
            "type": "object",
            "required": ["cases"],
            "properties": {
                "bars":     {"type": "string"},
                "cases":    {"type": "string"},
                "position": {"type": "number"},
                "limit":    {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_bar_displacements",
        description="Bar transverse displacements (deflection) along the bar for selected cases.",
        inputSchema={
            "type": "object",
            "required": ["cases"],
            "properties": {
                "bars":      {"type": "string"},
                "cases":     {"type": "string"},
                "position":  {"type": "number"},
                "limit":     {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_extremes",
        description=(
            "Envelope extremes (max, min, absMax) of one component for bar forces, node displacements "
            "or support reactions across all selected objects and cases. Scans everything; "
            "limit only caps the optional sample list. Useful for design-governing values."
        ),
        inputSchema={
            "type": "object",
            "required": ["resultType", "cases"],
            "properties": {
                "resultType": {"type": "string", "enum": ["bar_forces", "node_displacements", "reactions"]},
                "cases":      {"type": "string"},
                "bars":       {"type": "string"},
                "nodes":      {"type": "string"},
                "component":  {"type": "string", "enum": ["FX", "FY", "FZ", "MX", "MY", "MZ",
                                                           "UX", "UY", "UZ", "RX", "RY", "RZ"]},
                "limit":      {"type": "integer"},
            },
        },
    ),
    Tool(
        name="robot_results_csv",
        description="Export bar forces, node displacements or reactions to a CSV file.",
        inputSchema={
            "type": "object",
            "required": ["resultType", "cases", "path"],
            "properties": {
                "resultType": {"type": "string", "enum": ["bar_forces", "node_displacements", "reactions"]},
                "cases":      {"type": "string"},
                "bars":       {"type": "string"},
                "nodes":      {"type": "string"},
                "path":       {"type": "string", "description": "Output CSV file path"},
                "positions":  {"type": "array", "items": {"type": "number"}},
            },
        },
    ),
]


# ──────────────────────────────────────────────────────────────────
# Helpers
#
# RobotOM result API (Robot 2013+):
#   Results.Nodes.Displacements.Value(node, case)      -> .UX .UY .UZ .RX .RY .RZ  (m, rad)
#   Results.Nodes.Reactions.Value(node, case)          -> .FX .FY .FZ .MX .MY .MZ  (N, N·m)
#   Results.Bars.Forces.Value(bar, case, pos)          -> .FX .FY .FZ .MX .MY .MZ  (N, N·m)
#   Results.Bars.Stresses.Value(bar, case, pos)        -> .Smax .Smin .SmaxMY ...  (Pa)
#   Results.Bars.Deflections.Value(bar, case, pos)     -> .UX .UY .UZ              (m, local)
# Value() returns a data OBJECT — components are read as attributes,
# never passed as an extra index argument.
# ──────────────────────────────────────────────────────────────────

DISP_COMPS   = ["UX", "UY", "UZ", "RX", "RY", "RZ"]
FORCE_COMPS  = ["FX", "FY", "FZ", "MX", "MY", "MZ"]
STRESS_COMPS = ["Smax", "Smin", "SmaxMY", "SmaxMZ", "SminMY", "SminMZ", "FXSX"]
DEFL_COMPS   = ["UX", "UY", "UZ"]

# Kept for backward compatibility with any external import
DISP_IDX   = {c: i + 1 for i, c in enumerate(DISP_COMPS)}
FORCE_IDX  = {c: i + 1 for i, c in enumerate(FORCE_COMPS)}
STRESS_IDX = {c: i + 1 for i, c in enumerate(STRESS_COMPS[:4])}

# SI -> output unit factors
F_DISP   = {"UX": 1000.0, "UY": 1000.0, "UZ": 1000.0,   # m   -> mm
            "RX": 1000.0, "RY": 1000.0, "RZ": 1000.0}   # rad -> mrad
F_FORCE  = 1 / 1000.0                                   # N, N·m -> kN, kN·m
F_STRESS = 1 / 1e6                                      # Pa -> MPa


class _Errors:
    """Collects the first few distinct COM errors so failures are never silent."""
    def __init__(self, cap: int = 5) -> None:
        self.cap = cap
        self.items: list[str] = []
        self.count = 0

    def add(self, where: str, exc: Exception) -> None:
        self.count += 1
        msg = f"{where}: {exc}"
        if len(self.items) < self.cap and msg not in self.items:
            self.items.append(msg)

    def attach(self, out: dict) -> dict:
        if self.count:
            out["errors"] = self.items
            out["errorCount"] = self.count
        return out


def _read(data: object, comps: list[str], factor) -> dict:
    """Read named attributes from a RobotOM result data object."""
    row: dict = {}
    for c in comps:
        f = factor[c] if isinstance(factor, dict) else factor
        try:
            row[c] = round(float(getattr(data, c)) * f, 6)
        except Exception:
            row[c] = None
    return row


def _require_results() -> object:
    r = robot()
    if not r.results_available():
        raise RuntimeError("No analysis results available. Run robot_calculate first.")
    return r.structure().Results


def _parse_id_list(text: str, obj_type: str, struc: object) -> list[int]:
    """Parse a selection text ('all', '1to10 12', ...) into integer IDs."""
    r = robot()
    if not text or str(text).lower() == "all":
        server = {"node": struc.Nodes, "bar": struc.Bars, "case": struc.Cases}.get(obj_type)
        if server is None:
            return []
        count = server.Count
        ids: list[int] = []
        i = 0
        # IDs may be non-contiguous; scan until we have found `count` objects
        while len(ids) < count and i < count + 100000:
            i += 1
            try:
                if server.Exist(i):
                    ids.append(i)
            except Exception:
                continue
        return ids
    return r.ids_from_selection(str(text), obj_type)


def _positions(args: dict, default: list[float]) -> list[float]:
    if "position" in args:
        return [float(args["position"])]
    if args.get("positions"):
        return [float(p) for p in args["positions"]]
    return default


def _supported_nodes(struc: object) -> list[int]:
    from ..robot_client import I_LT_NODE_SUPPORT
    out: list[int] = []
    for nid in _parse_id_list("all", "node", struc):
        try:
            node = struc.Nodes.Get(nid)
            if node.HasLabel(I_LT_NODE_SUPPORT):
                out.append(nid)
        except Exception:
            continue
    return out


def _done(rows: list, limit: int) -> bool:
    return len(rows) >= limit


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_node_displacements(args: dict) -> dict:
    res = _require_results()
    struc = robot().structure()
    server = res.Nodes.Displacements
    cases = _parse_id_list(args.get("cases", "all"), "case", struc)
    nodes = _parse_id_list(args.get("nodes", "all"), "node", struc)
    limit = int(args.get("limit", 200))
    comps = [c for c in (args.get("components") or DISP_COMPS) if c in DISP_COMPS]
    err = _Errors()

    rows: list[dict] = []
    for nid in nodes:
        for cid in cases:
            try:
                d = server.Value(nid, cid)
                rows.append({"node": nid, "case": cid, **_read(d, comps, F_DISP)})
            except Exception as e:
                err.add(f"node {nid} case {cid}", e)
            if _done(rows, limit): break
        if _done(rows, limit): break

    return err.attach({"displacements": rows, "count": len(rows),
                       "truncated": _done(rows, limit),
                       "units": "UX/UY/UZ: mm, RX/RY/RZ: mrad"})


async def handle_robot_support_reactions(args: dict) -> dict:
    res = _require_results()
    struc = robot().structure()
    server = res.Nodes.Reactions
    cases = _parse_id_list(args.get("cases", "all"), "case", struc)
    limit = int(args.get("limit", 200))
    nsel = args.get("nodes")
    nodes = (robot().ids_from_selection(nsel, "node")
             if nsel and str(nsel).lower() != "all" else _supported_nodes(struc))
    err = _Errors()

    if not nodes:
        return {"reactions": [], "count": 0, "note": "No supported nodes found"}

    rows: list[dict] = []
    for nid in nodes:
        for cid in cases:
            try:
                r = server.Value(nid, cid)
                rows.append({"node": nid, "case": cid, **_read(r, FORCE_COMPS, F_FORCE)})
            except Exception as e:
                err.add(f"node {nid} case {cid}", e)
            if _done(rows, limit): break
        if _done(rows, limit): break

    return err.attach({"reactions": rows, "count": len(rows),
                       "truncated": _done(rows, limit),
                       "units": "FX/FY/FZ: kN, MX/MY/MZ: kN·m"})


async def handle_robot_bar_forces(args: dict) -> dict:
    res = _require_results()
    struc = robot().structure()
    server = res.Bars.Forces
    cases = _parse_id_list(args.get("cases", "all"), "case", struc)
    bars  = _parse_id_list(args.get("bars", "all"), "bar", struc)
    limit = int(args.get("limit", 300))
    comps = [c for c in (args.get("components") or FORCE_COMPS) if c in FORCE_COMPS]
    positions = _positions(args, [0.0, 0.5, 1.0])
    err = _Errors()

    rows: list[dict] = []
    for bid in bars:
        for cid in cases:
            for pos in positions:
                try:
                    f = server.Value(bid, cid, pos)
                    rows.append({"bar": bid, "case": cid, "position": pos,
                                 **_read(f, comps, F_FORCE)})
                except Exception as e:
                    err.add(f"bar {bid} case {cid} pos {pos}", e)
                if _done(rows, limit): break
            if _done(rows, limit): break
        if _done(rows, limit): break

    return err.attach({"forces": rows, "count": len(rows),
                       "truncated": _done(rows, limit),
                       "units": "FX/FY/FZ: kN, MX/MY/MZ: kN·m"})


async def handle_robot_bar_stresses(args: dict) -> dict:
    res = _require_results()
    struc = robot().structure()
    server = res.Bars.Stresses
    cases = _parse_id_list(args.get("cases", "all"), "case", struc)
    bars  = _parse_id_list(args.get("bars", "all"), "bar", struc)
    limit = int(args.get("limit", 300))
    positions = _positions(args, [0.5])
    err = _Errors()

    rows: list[dict] = []
    for bid in bars:
        for cid in cases:
            for pos in positions:
                try:
                    s = server.Value(bid, cid, pos)
                    row = {"bar": bid, "case": cid, "position": pos,
                           **_read(s, STRESS_COMPS, F_STRESS)}
                    # drop fields this Robot version doesn't expose
                    rows.append({k: v for k, v in row.items() if v is not None})
                except Exception as e:
                    err.add(f"bar {bid} case {cid} pos {pos}", e)
                if _done(rows, limit): break
            if _done(rows, limit): break
        if _done(rows, limit): break

    return err.attach({"stresses": rows, "count": len(rows),
                       "truncated": _done(rows, limit), "units": "MPa"})


async def handle_robot_bar_displacements(args: dict) -> dict:
    res = _require_results()
    struc = robot().structure()
    try:
        server = res.Bars.Deflections
    except Exception:
        server = res.Bars.Displacements   # older naming fallback
    cases = _parse_id_list(args.get("cases", "all"), "case", struc)
    bars  = _parse_id_list(args.get("bars", "all"), "bar", struc)
    limit = int(args.get("limit", 200))
    positions = _positions(args, [0.5])
    err = _Errors()

    rows: list[dict] = []
    for bid in bars:
        for cid in cases:
            for pos in positions:
                try:
                    d = server.Value(bid, cid, pos)
                    rows.append({"bar": bid, "case": cid, "position": pos,
                                 **_read(d, DEFL_COMPS, 1000.0)})
                except Exception as e:
                    err.add(f"bar {bid} case {cid} pos {pos}", e)
                if _done(rows, limit): break
            if _done(rows, limit): break
        if _done(rows, limit): break

    return err.attach({"barDisplacements": rows, "count": len(rows),
                       "truncated": _done(rows, limit),
                       "units": "mm (local deflection relative to chord)"})


async def handle_robot_extremes(args: dict) -> dict:
    """Envelope over all selected objects/cases. Scans everything (no limit
    on the scan); `limit` only caps the number of sample values returned."""
    result_type = args["resultType"]
    comp = args.get("component")
    limit = int(args.get("limit", 0))
    big = 10**9

    if result_type == "bar_forces":
        comp = comp or "MY"
        if comp not in FORCE_COMPS:
            return {"error": f"component must be one of {FORCE_COMPS}"}
        data = await handle_robot_bar_forces({**args, "components": [comp], "limit": big})
        rows, key, units = data.get("forces", []), "bar", "kN or kN·m"
    elif result_type == "node_displacements":
        comp = comp or "UZ"
        if comp not in DISP_COMPS:
            return {"error": f"component must be one of {DISP_COMPS}"}
        data = await handle_robot_node_displacements({**args, "components": [comp], "limit": big})
        rows, key, units = data.get("displacements", []), "node", "mm or mrad"
    elif result_type == "reactions":
        comp = comp or "FZ"
        if comp not in FORCE_COMPS:
            return {"error": f"component must be one of {FORCE_COMPS}"}
        data = await handle_robot_support_reactions({**args, "limit": big})
        rows, key, units = data.get("reactions", []), "node", "kN or kN·m"
    else:
        return {"error": f"Unknown resultType: {result_type}"}

    vals = [r for r in rows if r.get(comp) is not None]
    out: dict = {"component": comp, "units": units, "scanned": len(vals)}
    if vals:
        mx = max(vals, key=lambda r: r[comp])
        mn = min(vals, key=lambda r: r[comp])
        ab = max(vals, key=lambda r: abs(r[comp]))
        pick = lambda r: {k: v for k, v in r.items() if k in (key, "case", "position", comp)}
        out["extremes"] = {"max": pick(mx), "min": pick(mn), "absMax": pick(ab)}
        if limit:
            out["sample"] = [pick(r) for r in vals[:limit]]
    else:
        out["extremes"] = None
    if "errors" in data:
        out["errors"], out["errorCount"] = data["errors"], data["errorCount"]
    return out


async def handle_robot_results_csv(args: dict) -> dict:
    import csv
    result_type = args["resultType"]
    path = args["path"]
    big = 10**9

    if result_type == "bar_forces":
        data = await handle_robot_bar_forces({
            "cases": args.get("cases", "all"), "bars": args.get("bars", "all"),
            "positions": args.get("positions") or [0.0, 0.5, 1.0], "limit": big})
        rows = data.get("forces", [])
    elif result_type == "node_displacements":
        data = await handle_robot_node_displacements({
            "cases": args.get("cases", "all"), "nodes": args.get("nodes", "all"), "limit": big})
        rows = data.get("displacements", [])
    elif result_type == "reactions":
        data = await handle_robot_support_reactions({
            "cases": args.get("cases", "all"), "nodes": args.get("nodes", "all"), "limit": big})
        rows = data.get("reactions", [])
    else:
        return {"error": f"Unknown resultType: {result_type}"}

    if not rows:
        out = {"written": False, "note": "No data to write"}
        if "errors" in data:
            out["errors"] = data["errors"]
        return out

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    out = {"written": True, "path": path, "rows": len(rows), "units": data.get("units")}
    if "errors" in data:
        out["errors"], out["errorCount"] = data["errors"], data["errorCount"]
    return out


HANDLERS: dict[str, object] = {
    "robot_node_displacements":  handle_robot_node_displacements,
    "robot_support_reactions":   handle_robot_support_reactions,
    "robot_bar_forces":          handle_robot_bar_forces,
    "robot_bar_stresses":        handle_robot_bar_stresses,
    "robot_bar_displacements":   handle_robot_bar_displacements,
    "robot_extremes":            handle_robot_extremes,
    "robot_results_csv":         handle_robot_results_csv,
}
