"""
Session tools — connection, project lifecycle, preferences.
"""
from __future__ import annotations
import time
from mcp.types import Tool, TextContent
from ..robot_client import robot, _is_robot_running, _server_count, PROJECT_TYPES, PROJECT_TYPES_INV


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


HANDLERS: dict[str, object] = {
    "robot_health":          handle_robot_health,
    "robot_launch":          handle_robot_launch,
    "robot_project_new":     handle_robot_project_new,
    "robot_project_open":    handle_robot_project_open,
    "robot_project_save":    handle_robot_project_save,
    "robot_project_close":   handle_robot_project_close,
    "robot_project_info":    handle_robot_project_info,
    "robot_set_interactive": handle_robot_set_interactive,
}
