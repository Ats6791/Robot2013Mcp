"""
Analysis tools — calculate, generate model, mesh panels.
"""
from __future__ import annotations
from mcp.types import Tool
from ..robot_client import robot


TOOLS: list[Tool] = [
    Tool(
        name="robot_calculate",
        description=(
            "Run the structural analysis (static/modal/buckling). "
            "Generates the FE model first if needed. "
            "Returns whether results are now available."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "generateModel": {"type": "boolean", "description": "Generate FE model before calculation (default true)"},
                "waitMs":        {"type": "integer",  "description": "Max wait in ms (default 600000 = 10 min)"},
            },
        },
    ),
    Tool(
        name="robot_generate_model",
        description=(
            "Generate the finite element model (mesh panels, apply boundary conditions) "
            "without running the analysis."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="robot_mesh_panels",
        description=(
            "Mesh all panels with a target element size. "
            "Equivalent to Robot's automatic mesh generation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "size":      {"type": "number",  "description": "Target mesh size in m (default 0.5)"},
                "selection": {"type": "string",  "description": "Panel selection (default all)"},
            },
        },
    ),
    Tool(
        name="robot_analysis_status",
        description=(
            "Check analysis status: results available, calculation warnings/errors. "
            "Robot 2013 safe: uses .Available only (not .Status)."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
]


# ──────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────

async def handle_robot_calculate(args: dict) -> dict:
    r = robot()
    calc = r.project().CalcEngine
    gen_model = args.get("generateModel", True)

    if gen_model:
        try:
            calc.GenerateModel()
        except Exception as e:
            return {"error": f"GenerateModel failed: {e}"}

    try:
        calc.Calculate()
    except Exception as e:
        return {"error": f"Calculate failed: {e}"}

    available = r.results_available()
    return {
        "calculated": True,
        "resultsAvailable": available,
        "note": "Results are ready" if available else "Calculation finished but results not yet available",
    }


async def handle_robot_generate_model(args: dict) -> dict:
    calc = robot().project().CalcEngine
    try:
        calc.GenerateModel()
        return {"generated": True}
    except Exception as e:
        return {"error": str(e)}


async def handle_robot_mesh_panels(args: dict) -> dict:
    r = robot()
    struc = r.structure()
    size = float(args.get("size", 0.5))
    sel_text = args.get("selection", "all")

    try:
        # Robot's automatic mesh via CalcEngine
        calc = r.project().CalcEngine
        # Set mesh parameters if available
        try:
            params = calc.AutoMeshParams
            params.MeshType = 0        # I_MT_UNIFORM
            params.ElementSize = size
        except Exception:
            pass

        panels = struc.Objects
        count = panels.Count
        for i in range(1, count + 5000):
            try:
                if not panels.Exist(i): continue
                panel = panels.Get(i)
                try:
                    mesh = panel.FiniteElems
                    if mesh is not None:
                        mesh.Generate(size)
                except Exception:
                    pass
                if i >= count: break
            except Exception:
                continue

        # Fallback: trigger via GenerateModel
        calc.GenerateModel()
        return {"meshed": True, "targetSize": size}
    except Exception as e:
        return {"error": str(e)}


async def handle_robot_analysis_status(args: dict) -> dict:
    r = robot()
    available = r.results_available()
    struc = r.structure()

    status: dict = {"resultsAvailable": available}

    if available:
        # Try to count result nodes/bars
        try:
            res = struc.Results
            node_res = res.Nodes
            bar_res  = res.Bars
            status["note"] = "Results are current and accessible"
        except Exception:
            status["note"] = "Results available but result server query failed"
    else:
        status["note"] = "No analysis results — run robot_calculate first"

    # Case count
    try:
        status["casesCount"] = struc.Cases.Count
    except Exception:
        pass

    return status


HANDLERS: dict[str, object] = {
    "robot_calculate":       handle_robot_calculate,
    "robot_generate_model":  handle_robot_generate_model,
    "robot_mesh_panels":     handle_robot_mesh_panels,
    "robot_analysis_status": handle_robot_analysis_status,
}
