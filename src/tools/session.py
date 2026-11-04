"""
Session tools — connection, project lifecycle, preferences.
"""
from __future__ import annotations
import time
from mcp.types import Tool, TextContent
from ..robot_client import robot, _is_robot_running, _server_count, PROJECT_TYPES, PROJECT_TYPES_INV, VIEW_PROJECTIONS


TOOLS: list[Tool] = [
    Tool(
        name="robot_health",
        description=(
            "Check the connection to Autodesk Robot Structural Analysis 2013: "
            "is Robot running, Robot version, is a project open (name, file, type), "
            "element/case counts and results availability. "
            "Call this first — and whenever you need to confirm Robot is reachable."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_launch",
        description=(
            "Start Robot Structural Analysis if it is not running. "
            "Waits until the COM server responds. Optionally creates a new project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "projectType": {
                    "type": "string",
                    "description": "Project type to create if no project is open",
                    "enum": list(PROJECT_TYPES.keys()),
                },
                "newProject": {
                    "type": "boolean",
                    "description": "Create an empty project if none is open (default true)",
                },
                "waitMs": {
                    "type": "integer",
                    "description": "Max wait for Robot to respond in ms (default 60000)",
                },
            },
        },
    ),
    Tool(
        name="robot_project_new",
        description=(
            "Create a new empty project. "
            "frame3d/frame2d/truss projects support bars only — "
            "use 'shell' for bars+panels or 'plate' for slabs. "
            "Refuses to discard a non-empty project unless discardCurrent=true."
        ),
        inputSchema={
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": list(PROJECT_TYPES.keys()),
                },
                "discardCurrent": {
                    "type": "boolean",
                    "description": "Replace current non-empty project without saving",
                },
            },
        },
    ),
    Tool(
        name="robot_project_open",
        description="Open a Robot project file (.rtd).",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Full path to the .rtd file"},
                "discardCurrent": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_project_save",
        description=(
            "Save the current project in place (omit path) or to a new absolute path. "
            "When supplying a path it must be absolute and end with .rtd "
            "(example: 'C:\\\\Projects\\\\my_model.rtd'). "
            "Relative paths cause Robot to write to an unknown working directory. "
            "Note: Robot 2013 may show a spurious 'not enough free disk space' warning "
            "on large disks due to a 32-bit overflow in its free-space check — "
            "the save still succeeds; dismiss the dialog normally."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute target path ending in .rtd (omit to save in place)",
                },
            },
        },
    ),
    Tool(
        name="robot_project_close",
        description="Close the current project WITHOUT saving. Requires confirm=true.",
        inputSchema={
            "type": "object",
            "required": ["confirm"],
            "properties": {
                "confirm": {"type": "boolean"},
            },
        },
    ),
    Tool(
        name="robot_project_info",
        description=(
            "Project metadata: name, file path, type, element/case counts, "
            "results availability, Robot version."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_set_interactive",
        description=(
            "Set Robot's Interactive flag (whether Robot may show question dialogs) "
            "and window visibility."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "interactive": {"type": "boolean", "description": "Allow Robot dialogs"},
                "visible":     {"type": "boolean", "description": "Show/hide Robot window"},
            },
        },
    ),
    Tool(
        name="robot_get_settings",
        description=(
            "Read current Robot application and project settings: "
            "language, units (length, force), active design norms, databases."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_set_settings",
        description=(
            "Change Robot application/project settings. "
            "language: 'english'|'french'|'german'|'polish'|'spanish'|'italian'|'portuguese'|'russian'|'czech'|'dutch'|'chinese'|… — requires Robot restart. "
            "unitLength: 'm'|'cm'|'mm'|'ft'|'in'. "
            "unitForce: 'N'|'kN'|'MN'|'kgf'|'tf'|'lbf'|'kip'. "
            "normConcrete / normSteel: design code name string (e.g. 'EC2', 'BAEL', 'ACI')."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "language":      {"type": "string"},
                "unitLength":    {"type": "string"},
                "unitForce":     {"type": "string"},
                "normConcrete":  {"type": "string"},
                "normSteel":     {"type": "string"},
            },
        },
    ),
    Tool(
        name="robot_quit",
        description=(
            "Quit Robot Structural Analysis cleanly. "
            "save=true (default): saves the project before quitting. "
            "save=false: discards unsaved changes. "
            "Requires confirm=true. "
            "Use before robot_set_settings {language} which requires a restart."
        ),
        inputSchema={
            "type": "object",
            "required": ["confirm"],
            "properties": {
                "confirm": {"type": "boolean", "description": "Must be true to proceed"},
                "save":    {"type": "boolean", "description": "Save project before quitting (default true)"},
            },
        },
    ),
    Tool(
        name="robot_restart",
        description=(
            "Save, quit, and relaunch Robot Structural Analysis — reopening the last project. "
            "Use after robot_set_settings {language} to apply the new language. "
            "Requires confirm=true."
        ),
        inputSchema={
            "type": "object",
            "required": ["confirm"],
            "properties": {
                "confirm": {"type": "boolean", "description": "Must be true to proceed"},
                "save":    {"type": "boolean", "description": "Save project before restart (default true)"},
                "waitMs":  {"type": "integer", "description": "Max wait for Robot to respond after restart (default 60000)"},
            },
        },
    ),
    Tool(
        name="robot_set_view",
        description=(
            "Control the Robot viewport: projection, section shapes in 3D volume, "
            "panel thickness, shading, node/bar numbers, support symbols, "
            "structural axes, grid, zoom. "
            "Uses view.ParamsDisplay.Set(I_VDA_*, bool) + view.Redraw(True)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "projection": {
                    "type": "string",
                    "enum": ["3d", "xy", "plan", "top", "xz", "front", "yz", "side", "right"],
                    "description": (
                        "'3d' = 3D axonometric, "
                        "'xy'/'plan'/'top' = plan, "
                        "'xz'/'front' = front elevation, "
                        "'yz'/'side'/'right' = side elevation."
                    ),
                },
                "sectionShapes": {
                    "type": "boolean",
                    "description": (
                        "Show bar/column sections as 3D solid shapes "
                        "(I_VDA_SECTIONS_SHAPE=14). "
                        "Automatically switches to projection='3d' and solid=true "
                        "because section shapes are invisible in 2D views. "
                        "false = back to centre-line."
                    ),
                },
                "panelThickness": {
                    "type": "boolean",
                    "description": (
                        "Show panel/slab thickness in 3D "
                        "(I_VDA_FE_THICKNESS=35 + I_VDA_FE_PANEL_THICKNESSES=89). "
                        "Also enables panel interior fill."
                    ),
                },
                "solid": {
                    "type": "boolean",
                    "description": (
                        "Shaded solid rendering with visible edges "
                        "(I_VDA_VIEW_SHADING_EDGES=114). "
                        "Best combined with sectionShapes=true."
                    ),
                },
                "nodeNumbers": {
                    "type": "boolean",
                    "description": "Show node numbers (I_VDA_STRUCTURE_NODE_NUMBERS=2).",
                },
                "barNumbers": {
                    "type": "boolean",
                    "description": "Show bar/element numbers (I_VDA_STRUCTURE_BAR_NUMBERS=3).",
                },
                "supports": {
                    "type": "boolean",
                    "description": "Show support symbols (I_VDA_STRUCTURE_SUPPORT_SYMBOLS=4).",
                },
                "struct_axes": {
                    "type": "boolean",
                    "description": "Show/hide structural axes grid (view.StructAxisVisible).",
                },
                "grid": {
                    "type": "boolean",
                    "description": "Show/hide reference grid (view.GridVisible).",
                },
                "zoom_all": {
                    "type": "boolean",
                    "description": "Zoom to fit entire model after applying changes (default true).",
                },
            },
        },
    ),
]


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

def _project_counts(struc: object) -> dict:
    # Robot 2013 servers (Nodes/Bars/Objects/Cases) have no .Count — use GetAll().Count.
    counts: dict = {}
    for attr, key in [("Nodes", "nodes"), ("Bars", "bars"),
                      ("Objects", "panels"), ("Cases", "cases")]:
        try:
            counts[key] = _server_count(getattr(struc, attr))  # type: ignore[arg-type]
        except Exception:
            counts[key] = None
    return counts


async def handle_robot_health(args: dict) -> dict:
    try:
        try:
            # Use the shared connect logic (Dispatch-first, no launch).
            app = robot().app(launch=False)
        except RuntimeError as e:
            return {"running": False, "error": str(e)}

        info: dict = {"running": True}

        try:
            info["visible"] = bool(app.Visible)
            info["interactive"] = bool(app.Interactive)
        except Exception:
            pass

        # IRobotApplication.Version is the real version number (e.g. 26.0 for 2013)
        try:
            info["robotVersion"] = str(app.Version)
        except Exception as e:
            info["robotVersionError"] = str(e)

        try:
            proj = app.Project
            info["projectOpen"] = True
            try: info["projectName"] = str(proj.FileName)
            except Exception: pass
            try:
                pt = proj.Type
                info["projectType"] = PROJECT_TYPES_INV.get(pt, str(pt))
            except Exception: pass

            struc = proj.Structure
            info["counts"] = _project_counts(struc)
            try:
                info["resultsAvailable"] = bool(struc.Results.Available)
            except Exception:
                info["resultsAvailable"] = False
        except Exception as e:
            info["projectOpen"] = False
            info["projectError"] = str(e)

        return info
    except Exception as e:
        return {"running": False, "error": str(e)}


async def handle_robot_launch(args: dict) -> dict:
    project_type = args.get("projectType", "frame3d")
    new_project = args.get("newProject", True)

    already_running = _is_robot_running()

    # Shared connect logic handles attach-vs-launch and the 60 s startup wait.
    app = robot().app(launch=True)
    app.Visible = True
    app.Interactive = True

    result: dict = {"launched": not already_running, "alreadyRunning": already_running}

    if new_project:
        try:
            proj = app.Project
            node_count = _server_count(proj.Structure.Nodes)
            if node_count > 0:
                result["projectCreated"] = False
                result["note"] = "Project already open; skipped new project creation"
            else:
                pt = PROJECT_TYPES.get(project_type, 1)
                proj.New(pt)
                result["projectCreated"] = True
                result["projectType"] = project_type
        except Exception as e:
            result["projectError"] = str(e)

    return result


async def handle_robot_project_new(args: dict) -> dict:
    pt_name = args["type"]
    discard = args.get("discardCurrent", False)
    pt_id = PROJECT_TYPES.get(pt_name)
    if pt_id is None:
        raise ValueError(f"Unknown project type: {pt_name}")

    app = robot().app()

    if not discard:
        try:
            struc = app.Project.Structure
            count = (_server_count(struc.Nodes) + _server_count(struc.Bars))
            if count > 0:
                raise ValueError(
                    f"Project has {count} elements. Pass discardCurrent=true to replace it."
                )
        except ValueError:
            raise
        except Exception:
            pass  # no project open, proceed

    app.Project.New(pt_id)
    return {"created": True, "type": pt_name}


async def handle_robot_project_open(args: dict) -> dict:
    path = args["path"]
    discard = args.get("discardCurrent", False)
    app = robot().app()

    if not discard:
        try:
            count = _server_count(app.Project.Structure.Nodes)
            if count > 0:
                raise ValueError(
                    "Project has unsaved elements. Pass discardCurrent=true to replace."
                )
        except ValueError:
            raise
        except Exception:
            pass

    app.Project.Open(path)
    struc = app.Project.Structure
    return {
        "opened": True,
        "path": path,
        "counts": _project_counts(struc),
        "resultsAvailable": bool(struc.Results.Available),
    }


async def handle_robot_project_save(args: dict) -> dict:
    import os
    path = args.get("path")
    proj = robot().project()
    if path:
        if not os.path.isabs(path):
            raise ValueError(
                f"Path must be absolute, not relative. Got: '{path}'. "
                "Example: 'C:\\\\Projects\\\\my_model.rtd'"
            )
        if not path.lower().endswith(".rtd"):
            raise ValueError(
                f"Path must end with .rtd. Got: '{path}'"
            )
        proj.SaveAs(path)
        return {"saved": True, "path": path}
    else:
        proj.Save()
        return {"saved": True}


async def handle_robot_project_close(args: dict) -> dict:
    if not args.get("confirm"):
        raise ValueError("confirm=true is required to close the project")
    robot().project().Close()
    return {"closed": True}


async def handle_robot_project_info(args: dict) -> dict:
    app = robot().app()
    proj = app.Project
    info: dict = {}
    try: info["fileName"] = str(proj.FileName)
    except Exception: pass
    try:
        pt = proj.Type
        info["projectType"] = PROJECT_TYPES_INV.get(pt, str(pt))
    except Exception: pass

    struc = proj.Structure
    info["counts"] = _project_counts(struc)
    try: info["resultsAvailable"] = bool(struc.Results.Available)
    except Exception: info["resultsAvailable"] = False

    try: info["robotVisible"] = bool(app.Visible)
    except Exception: pass
    try: info["robotVersion"] = str(app.Version)
    except Exception: pass

    return info


async def handle_robot_set_interactive(args: dict) -> dict:
    app = robot().app()
    changed: dict = {}
    if "interactive" in args:
        app.Interactive = 1 if args["interactive"] else 0
        changed["interactive"] = args["interactive"]
    if "visible" in args:
        app.Visible = 1 if args["visible"] else 0
        changed["visible"] = args["visible"]
    return {"set": changed}


async def handle_robot_set_view(args: dict) -> dict:
    """Control the Robot viewport via app.Project.ViewMngr.GetView(1).

    API path (Robot 2013):
      vm  = app.Project.ViewMngr                       (IRobotViewMngr)
      v   = vm.GetView(1)                              (IRobotView2)
      v.Projection = I_VP_*                            (IRobotViewProjection enum)
      v.ParamsDisplay.Set(I_VDA_*, 0|1)                (IRobotViewDisplayAttributes)
      v.ParamsDisplay.IsOn(I_VDA_*)                    — read current state
      v.StructAxisVisible = 0|1
      v.GridVisible       = 0|1
      v.Redraw(force_init_zoom: 0|1)
    """
    # ── IRobotViewDisplayAttributes constants (Robot 2013 typelib) ────────
    I_VDA_STRUCTURE_NODE_NUMBERS   = 2
    I_VDA_STRUCTURE_BAR_NUMBERS    = 3
    I_VDA_STRUCTURE_SUPPORT_SYMBOLS = 4
    I_VDA_SECTIONS_SHAPE           = 14   # bar/column section shapes in 3D volume
    I_VDA_FE_PANEL_INTERIOR        = 34   # panel fill / interior surface
    I_VDA_FE_THICKNESS             = 35   # panel thickness rendering (structural view)
    I_VDA_FE_PANEL_THICKNESSES     = 89   # panel thicknesses (FE mesh view)
    I_VDA_VIEW_SHADING_EDGES       = 114  # shaded solid rendering with edges

    app = robot().app()

    # ── get ViewMngr and first view ───────────────────────────────────────
    try:
        vm = app.Project.ViewMngr
    except Exception as exc:
        return {"error": f"app.Project.ViewMngr inaccessible: {exc}"}

    try:
        view_count = int(vm.ViewCount)
    except Exception as exc:
        return {"error": f"ViewMngr.ViewCount failed: {exc}"}

    if view_count < 1:
        return {"error": "No views open. Open a project first."}

    view_idx = 1
    try:
        v = vm.GetView(view_idx)
    except Exception as exc:
        return {"error": f"ViewMngr.GetView(1) failed: {exc}"}

    applied: dict = {}
    unsupported: list = []

    # ── sectionShapes implies 3D projection + solid rendering ─────────────
    # I_VDA_SECTIONS_SHAPE has no visual effect in a 2D (XY/XZ/YZ) view —
    # sections always render as centre lines in plan/elevation.  When the
    # caller enables shapes we silently upgrade the defaults so the result
    # is immediately visible (the caller can still override each individually).
    if args.get("sectionShapes"):
        if "projection" not in args:
            args = dict(args, projection="3d")
        if "solid" not in args:
            args = dict(args, solid=True)

    # ── projection ────────────────────────────────────────────────────────
    proj_name = args.get("projection")
    if proj_name is not None:
        proj_id = VIEW_PROJECTIONS.get(proj_name.lower())
        if proj_id is None:
            return {
                "error": f"Unknown projection '{proj_name}'. "
                         f"Valid: {list(VIEW_PROJECTIONS.keys())}"
            }
        try:
            v.Projection = proj_id
            applied["projection"] = proj_name
        except Exception as exc:
            return {"error": f"Setting Projection={proj_id} failed: {exc}"}

    # ── ParamsDisplay.Set helper ──────────────────────────────────────────
    try:
        pd = v.ParamsDisplay
        has_pd = True
    except Exception:
        has_pd = False
        pd = None

    def _pd_set(param_name: str, vda_const: int, enable: bool) -> None:
        if not has_pd:
            unsupported.append(param_name)
            return
        try:
            pd.Set(vda_const, 1 if enable else 0)
            applied[param_name] = enable
        except Exception as exc:
            applied[f"{param_name}_error"] = str(exc)

    # ── sectionShapes: I_VDA_SECTIONS_SHAPE = 14 ─────────────────────────
    if "sectionShapes" in args:
        _pd_set("sectionShapes", I_VDA_SECTIONS_SHAPE, bool(args["sectionShapes"]))

    # ── panelThickness: I_VDA_FE_THICKNESS=35 + I_VDA_FE_PANEL_THICKNESSES=89
    if "panelThickness" in args:
        enable = bool(args["panelThickness"])
        _pd_set("panelThickness_fe",         I_VDA_FE_THICKNESS,          enable)
        _pd_set("panelThickness_fe_panels",  I_VDA_FE_PANEL_THICKNESSES,  enable)
        # Also show panel interior fill when thickness is on (needed to see the slab body)
        if enable:
            _pd_set("panelInterior", I_VDA_FE_PANEL_INTERIOR, True)
        applied["panelThickness"] = enable

    # ── solid: I_VDA_VIEW_SHADING_EDGES = 114 ────────────────────────────
    if "solid" in args:
        _pd_set("solid", I_VDA_VIEW_SHADING_EDGES, bool(args["solid"]))

    # ── nodeNumbers, barNumbers, supports ────────────────────────────────
    if "nodeNumbers" in args:
        _pd_set("nodeNumbers", I_VDA_STRUCTURE_NODE_NUMBERS,   bool(args["nodeNumbers"]))
    if "barNumbers" in args:
        _pd_set("barNumbers",  I_VDA_STRUCTURE_BAR_NUMBERS,    bool(args["barNumbers"]))
    if "supports" in args:
        _pd_set("supports",    I_VDA_STRUCTURE_SUPPORT_SYMBOLS, bool(args["supports"]))

    # ── struct_axes (view property + ParamsDisplay fallback) ─────────────
    if "struct_axes" in args:
        enable = bool(args["struct_axes"])
        try:
            v.StructAxisVisible = 1 if enable else 0
            applied["struct_axes"] = enable
        except Exception as exc:
            applied["struct_axes_error"] = str(exc)

    # ── grid (view property) ─────────────────────────────────────────────
    if "grid" in args:
        enable = bool(args["grid"])
        try:
            v.GridVisible = 1 if enable else 0
            applied["grid"] = enable
        except Exception as exc:
            applied["grid_error"] = str(exc)

    # ── redraw (before zoom so shapes appear before zoom is computed) ─────
    zoom_all = args.get("zoom_all", True)
    try:
        v.Redraw(1 if zoom_all else 0)
        applied["zoom_all"] = zoom_all
    except Exception as exc:
        applied["redraw_error"] = str(exc)

    result: dict = {"applied": applied, "view": view_idx}
    if unsupported:
        result["unsupported"] = unsupported
    return result




# ── Language / units / norm constants ─────────────────────────────────────
# Robot 2013 uses telephone country codes for language IDs (from Lang.cfg).
# Read via:  app.Preferences.GetLanguage(1)   (I_L_WORK=1)
# Write via: registry HKCU\Software\Autodesk\Structural\koo\Settings
#            values LangWork and LangPrint  (REG_SZ, e.g. "33" for French)
_LANG_REGISTRY_KEY = r"Software\Autodesk\Structural\koo\Settings"

_LANGUAGES: dict[str, int] = {
    "english":        1,
    "french":         33,
    "spanish":        34,
    "portuguese":     35,
    "italian":        39,
    "polish":         48,
    "german":         49,
    "portuguese_br":  55,
    "russian":        70,
    "japanese":       81,
    "chinese":        86,
    "uk":             44,
}
_LANGUAGES_INV: dict[int, str] = {v: k for k, v in _LANGUAGES.items()}

# IRobotUnitType / IRobotProjectUnitType (length, force, …)
# Values confirmed from Robot 2013 typelib I_UT_* / I_FU_*
_UNIT_LENGTH: dict[str, int] = {"m": 0, "cm": 1, "mm": 2, "ft": 3, "in": 4}
_UNIT_FORCE:  dict[str, int] = {"N": 0, "kN": 1, "MN": 2, "kgf": 3, "tf": 4,
                                 "lbf": 5, "kip": 6}
_UNIT_LENGTH_INV = {v: k for k, v in _UNIT_LENGTH.items()}
_UNIT_FORCE_INV  = {v: k for k, v in _UNIT_FORCE.items()}

# Common concrete norms (I_CN_*) and steel norms (I_SN_*) in Robot 2013
# Values are robot internal integers; user passes the string name.
_CONCRETE_NORMS = ["BAEL", "EC2", "ACI", "BS8110", "DIN1045", "NF P 18-110",
                   "PN-B-03264", "SNIP", "NBR", "GB50010"]
_STEEL_NORMS    = ["EC3", "AISC", "BS5950", "DIN18800", "PN-90/B-03200",
                   "CM66", "NF P 22-311", "SNIP", "NBR", "GB50017"]


async def handle_robot_get_settings(args: dict) -> dict:
    """Read current application + project settings."""
    app = robot().app()
    result: dict = {}

    # ── Language via registry (same source set_settings writes — registry is authoritative) ──
    # IRobotApplication has no .Language property (typelib confirmed).
    # IRobotPreferences.GetLanguage(lang_type) returns the telephone-code int.
    # Read language from registry (same source set_settings writes — registry is authoritative)
    import winreg as _winreg
    try:
        _key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, _LANG_REGISTRY_KEY)
        _reg_val = _winreg.QueryValueEx(_key, "LangWork")[0]
        _winreg.CloseKey(_key)
        lang_id = int(_reg_val)
        result["language"] = _LANGUAGES_INV.get(lang_id, str(lang_id))
        result["languageId"] = lang_id
    except Exception:
        # Fallback to COM (reflects current session, not necessarily persisted value)
        try:
            prefs = app.Preferences
            lang_id = int(prefs.GetLanguage(1))   # 1 = I_L_WORK
            result["language"] = _LANGUAGES_INV.get(lang_id, str(lang_id))
            result["languageId"] = lang_id
            result["language_source"] = "com_session"
        except Exception as e:
            result["language_error"] = str(e)

    try:
        result["version"] = str(app.Version)
    except Exception:
        pass

    # ── Project-level preferences ──────────────────────────────────────────
    try:
        pp = app.Project.Preferences
    except Exception as e:
        result["preferences_error"] = str(e)
        return result

    # Units
    for attr, inv_map, key in [
        ("UnitLength", _UNIT_LENGTH_INV, "unitLength"),
        ("UnitForce",  _UNIT_FORCE_INV,  "unitForce"),
    ]:
        try:
            val = int(getattr(pp, attr))
            result[key] = inv_map.get(val, str(val))
            result[f"{key}Id"] = val
        except Exception:
            pass

    # Design norms — try several property names Robot 2013 may use
    for attr, key in [
        ("NormConc",   "normConcrete"),
        ("NormSteel",  "normSteel"),
        ("ConcreteNorm","normConcrete"),
        ("SteelNorm",  "normSteel"),
    ]:
        if key in result:
            continue
        try:
            val = getattr(pp, attr)
            if val is not None:
                result[key] = str(val)
        except Exception:
            pass

    # Active databases
    for attr, key in [
        ("SteelDatabase",   "steelDatabase"),
        ("SectionDatabase", "sectionDatabase"),
        ("ConcDatabase",    "concDatabase"),
    ]:
        try:
            val = getattr(pp, attr)
            if val is not None:
                result[key] = str(val)
        except Exception:
            pass

    result["note"] = (
        "language change requires Robot restart to fully apply. "
        "Run robot_launch after robot_set_settings {language:...}."
    )
    return result


async def handle_robot_set_settings(args: dict) -> dict:
    """Change application language and/or project units / design norms."""
    app = robot().app()
    changed: dict = {}
    errors: dict = {}

    # ── Language — write to registry (IRobotPreferences has no SetLanguage) ─
    # Path: HKCU\Software\Autodesk\Structural\koo\Settings
    # Values: LangWork, LangPrint  (REG_SZ, telephone-code as string, e.g. "33")
    if "language" in args:
        import winreg
        lang_name = str(args["language"]).lower().replace("-", "_").replace(" ", "_")
        lang_id = _LANGUAGES.get(lang_name)
        if lang_id is None:
            errors["language"] = (
                f"Unknown language '{args['language']}'. "
                f"Valid: {list(_LANGUAGES.keys())}"
            )
        else:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    _LANG_REGISTRY_KEY,
                    0,
                    winreg.KEY_SET_VALUE,
                )
                lang_str = str(lang_id)
                winreg.SetValueEx(key, "LangWork",  0, winreg.REG_SZ, lang_str)
                winreg.SetValueEx(key, "LangPrint", 0, winreg.REG_SZ, lang_str)
                winreg.CloseKey(key)
                changed["language"] = lang_name
                changed["languageId"] = lang_id
                changed["restartRequired"] = True
            except FileNotFoundError:
                errors["language"] = (
                    f"Registry key not found: HKCU\\{_LANG_REGISTRY_KEY}. "
                    "Start Robot at least once to create this key."
                )
            except Exception as e:
                errors["language"] = str(e)

    # ── Project preferences ────────────────────────────────────────────────
    try:
        pp = app.Project.Preferences
    except Exception as e:
        errors["preferences"] = str(e)
        return {"changed": changed, "errors": errors}

    # Unit: length
    if "unitLength" in args:
        unit = str(args["unitLength"]).lower()
        uid = _UNIT_LENGTH.get(unit)
        if uid is None:
            errors["unitLength"] = f"Unknown unit '{args['unitLength']}'. Valid: {list(_UNIT_LENGTH.keys())}"
        else:
            try:
                pp.UnitLength = uid
                changed["unitLength"] = unit
            except Exception as e:
                errors["unitLength"] = str(e)

    # Unit: force
    if "unitForce" in args:
        unit = str(args["unitForce"])
        uid = _UNIT_FORCE.get(unit)
        if uid is None:
            errors["unitForce"] = f"Unknown unit '{args['unitForce']}'. Valid: {list(_UNIT_FORCE.keys())}"
        else:
            try:
                pp.UnitForce = uid
                changed["unitForce"] = unit
            except Exception as e:
                errors["unitForce"] = str(e)

    # Concrete norm
    if "normConcrete" in args:
        norm = str(args["normConcrete"])
        for attr in ["NormConc", "ConcreteNorm"]:
            try:
                setattr(pp, attr, norm)
                changed["normConcrete"] = norm
                break
            except Exception as e:
                errors[f"normConcrete_{attr}"] = str(e)

    # Steel norm
    if "normSteel" in args:
        norm = str(args["normSteel"])
        for attr in ["NormSteel", "SteelNorm"]:
            try:
                setattr(pp, attr, norm)
                changed["normSteel"] = norm
                break
            except Exception as e:
                errors[f"normSteel_{attr}"] = str(e)

    result: dict = {"changed": changed}
    if errors:
        result["errors"] = errors
    return result


async def handle_robot_quit(args: dict) -> dict:
    """Quit Robot cleanly using IRobotQuitOption."""
    if not args.get("confirm"):
        raise ValueError("confirm=true is required to quit Robot")
    save = args.get("save", True)
    # I_QO_SAVE_CHANGES=2, I_QO_DISCARD_CHANGES=0
    quit_option = 2 if save else 0
    app = robot().app(launch=False)
    proj_name = None
    try: proj_name = str(app.Project.FileName)
    except Exception: pass
    try:
        app.Quit(quit_option)
    except Exception as e:
        # Robot may close the window and kill COM before the call returns
        if "RPC" in str(e) or "disconnected" in str(e).lower() or "-2147023174" in str(e):
            pass  # expected — Robot is gone
        else:
            raise
    # Invalidate cached COM object
    from ..robot_client import robot as _robot_fn
    _robot_fn()._app = None
    return {"quit": True, "saved": save, "lastProject": proj_name}


async def handle_robot_restart(args: dict) -> dict:
    """Save, quit, and relaunch Robot reopening the last project."""
    if not args.get("confirm"):
        raise ValueError("confirm=true is required to restart Robot")
    save = args.get("save", True)
    wait_ms = int(args.get("waitMs", 60000))

    app = robot().app(launch=False)
    proj_path = None
    try: proj_path = str(app.Project.FileName)
    except Exception: pass

    # Quit cleanly
    quit_option = 2 if save else 0
    try:
        app.Quit(quit_option)
    except Exception as e:
        if "RPC" in str(e) or "disconnected" in str(e).lower() or "-2147023174" in str(e):
            pass
        else:
            raise

    from ..robot_client import robot as _robot_fn
    _robot_fn()._app = None

    # Wait for Robot.exe to exit
    import subprocess, time as _time
    deadline = _time.time() + 15
    while _time.time() < deadline:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Robot.exe", "/NH"],
            capture_output=True, text=True
        )
        if "Robot.exe" not in result.stdout:
            break
        _time.sleep(1)

    # Relaunch
    import win32com.client as _wc
    new_app = _wc.Dispatch("Robot.Application")
    new_app.Visible = True
    new_app.Interactive = True

    # Wait for COM to respond
    deadline2 = _time.time() + wait_ms / 1000
    while _time.time() < deadline2:
        try:
            _ = new_app.Project
            break
        except Exception:
            _time.sleep(1)

    _robot_fn()._app = new_app

    # Reopen last project
    if proj_path:
        try:
            new_app.Project.Open(proj_path)
        except Exception as e:
            return {"restarted": True, "projectReopened": False, "reopenError": str(e)}

    return {"restarted": True, "projectReopened": bool(proj_path), "project": proj_path}


HANDLERS: dict[str, object] = {
    "robot_health":          handle_robot_health,
    "robot_launch":          handle_robot_launch,
    "robot_quit":            handle_robot_quit,
    "robot_restart":         handle_robot_restart,
    "robot_project_new":     handle_robot_project_new,
    "robot_project_open":    handle_robot_project_open,
    "robot_project_save":    handle_robot_project_save,
    "robot_project_close":   handle_robot_project_close,
    "robot_project_info":    handle_robot_project_info,
    "robot_set_interactive": handle_robot_set_interactive,
    "robot_set_view":        handle_robot_set_view,
    "robot_get_settings":    handle_robot_get_settings,
    "robot_set_settings":    handle_robot_set_settings,
}
