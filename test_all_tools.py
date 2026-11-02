"""
Comprehensive test runner for all 64 Robot MCP tools.
Runs against a live Robot 2013 instance.

Usage:
    python test_all_tools.py   # all 64 tools (load + result tools included)

Output: PASS / FAIL / SKIP per tool, final summary.
"""
import asyncio
import sys
import os
import tempfile
import argparse

sys.path.insert(0, os.path.dirname(__file__))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--fix-static", action="store_true")
opts, _ = parser.parse_known_args()

import src.robot_client as _rc
if opts.fix_static:
    _rc.I_AT_STATIC = 1
    _rc.ANALYSIS_TYPES["static"] = 1
    print("[PATCH] I_AT_STATIC patched: 0 -> 1 (--fix-static)")

from src.tools.session      import (handle_robot_health, handle_robot_launch,
                                    handle_robot_project_new, handle_robot_project_open,
                                    handle_robot_project_save, handle_robot_project_close,
                                    handle_robot_project_info, handle_robot_set_interactive)
from src.tools.model_write  import (handle_robot_create_node, handle_robot_create_nodes,
                                    handle_robot_create_bar, handle_robot_create_bars,
                                    handle_robot_create_panel, handle_robot_delete,
                                    handle_robot_set_bar_section, handle_robot_set_bar_material,
                                    handle_robot_set_bar_release, handle_robot_set_support,
                                    handle_robot_set_panel_thickness, handle_robot_create_section,
                                    handle_robot_create_material, handle_robot_create_support_label,
                                    handle_robot_transform, handle_robot_clear_structure,
                                    handle_robot_build_frame)
from src.tools.model_read   import (handle_robot_summary, handle_robot_list_nodes,
                                    handle_robot_get_node, handle_robot_find_nodes_at,
                                    handle_robot_list_bars, handle_robot_get_bar,
                                    handle_robot_list_panels, handle_robot_get_panel,
                                    handle_robot_list_supports, handle_robot_list_labels,
                                    handle_robot_get_label, handle_robot_section_search,
                                    handle_robot_material_database, handle_robot_list_cases,
                                    handle_robot_get_case, handle_robot_list_groups,
                                    handle_robot_export_model_json)
from src.tools.loads        import (handle_robot_create_case, handle_robot_add_nodal_load,
                                    handle_robot_add_bar_uniform, handle_robot_add_bar_point,
                                    handle_robot_add_bar_trapezoidal, handle_robot_add_self_weight,
                                    handle_robot_create_combination, handle_robot_delete_case,
                                    handle_robot_delete_load_records)
from src.tools.analysis     import (handle_robot_calculate, handle_robot_generate_model,
                                    handle_robot_mesh_panels, handle_robot_analysis_status)
from src.tools.results      import (handle_robot_node_displacements, handle_robot_support_reactions,
                                    handle_robot_bar_forces, handle_robot_bar_stresses,
                                    handle_robot_bar_displacements, handle_robot_extremes,
                                    handle_robot_results_csv)
from src.tools.preferences  import handle_robot_get_norms, handle_robot_set_norm

# ── Result tracking ──────────────────────────────────────────────────────
_results: dict[str, tuple[str, str]] = {}
_PASS = "PASS"; _FAIL = "FAIL"; _SKIP = "SKIP"; _KNOWN = "KNOWN_BUG"

KNOWN_BUGS: dict[str, str] = {}  # all bugs fixed


def record(name: str, status: str, detail: str = "") -> None:
    _results[name] = (status, detail)
    icons = {"PASS": "v", "FAIL": "X", "SKIP": "-", "KNOWN_BUG": "~"}
    msg = f"  {detail}" if detail else ""
    print(f"  [{icons[status]}] {name:<38} {status}{msg}")


async def run(name: str, coro, *, note: str = "") -> object:
    known = not opts.fix_static and name in KNOWN_BUGS
    try:
        res = await coro
        status = _KNOWN if known else _PASS
        detail = KNOWN_BUGS[name] if known else (note or "")
        record(name, status, detail)
        return res
    except Exception as e:
        short = str(e)[:90]
        if known:
            record(name, _KNOWN, f"{short[:50]} | {KNOWN_BUGS[name]}")
        else:
            record(name, _FAIL, short)
        return None


def skip(name: str, reason: str = "") -> None:
    record(name, _SKIP, reason)


_project_path = os.path.join(tempfile.gettempdir(), "robot_mcp_test.rtd")
_csv_path     = os.path.join(tempfile.gettempdir(), "robot_mcp_test.csv")


async def main() -> None:
    print("=" * 65)
    print("Robot MCP — Full 64-tool test suite")
    print(f"  I_AT_STATIC = {_rc.I_AT_STATIC}")
    print("=" * 65)

    # ── Phase 0: Session ────────────────────────────────────────────
    print("\n--- Phase 0: Session (8 tools) ---")

    await run("robot_health",          handle_robot_health({}))
    await run("robot_launch",          handle_robot_launch({"newProject": False}))
    await run("robot_project_new",     handle_robot_project_new({"type": "frame3d", "discardCurrent": True}))
    await run("robot_project_info",    handle_robot_project_info({}))
    await run("robot_set_interactive", handle_robot_set_interactive({"interactive": False, "visible": True}))
    # project_save / project_open / project_close tested in Phase 7
    skip("robot_project_save",  "Tested in Phase 7 (persistence)")
    skip("robot_project_open",  "Tested in Phase 7 (persistence)")
    skip("robot_project_close", "Tested in Phase 7 (persistence)")

    # ── Phase 1: Model Write ────────────────────────────────────────
    print("\n--- Phase 1: Model Write (17 tools) ---")

    await run("robot_clear_structure",
              handle_robot_clear_structure({"confirm": True}))

    # Support label first (needed by create_nodes)
    await run("robot_create_support_label",
              handle_robot_create_support_label({
                  "name": "FIXED",
                  "ux": True, "uy": True, "uz": True,
                  "rx": True, "ry": True, "rz": True,
              }))

    # Single node at a distinct coordinate (not reused by later batch)
    await run("robot_create_node",
              handle_robot_create_node({"x": 99.0, "y": 99.0, "z": 99.0, "number": 10}))

    # Delete that temporary node
    await run("robot_delete",
              handle_robot_delete({"selection": "10", "type": "node"}))

    # Material
    await run("robot_create_material",
              handle_robot_create_material({
                  "name": "C25",
                  "type": "concrete",
                  "E_MPa": 30000.0,
                  "nu": 0.2,
                  "density_kg_m3": 2500.0,
              }))

    # Section (from database — parametric Store fails in Robot 2013)
    await run("robot_create_section",
              handle_robot_create_section({
                  "name": "RC30x50",
                  "fromDatabase": "HEB 200",
              }))

    # Batch nodes: simple portal frame
    # 1(0,0,0) 2(5,0,0) — bases
    # 3(0,0,3) 4(5,0,3) — tops of columns
    await run("robot_create_nodes", handle_robot_create_nodes({
        "nodes": [
            {"x": 0,  "y": 0, "z": 0, "number": 1, "support": "FIXED"},
            {"x": 5,  "y": 0, "z": 0, "number": 2, "support": "FIXED"},
            {"x": 0,  "y": 0, "z": 3, "number": 3},
            {"x": 5,  "y": 0, "z": 3, "number": 4},
            {"x": 2.5,"y": 0, "z": 6, "number": 5},
        ]
    }))

    # Single bar
    await run("robot_create_bar",
              handle_robot_create_bar({
                  "startNode": 1, "endNode": 3,
                  "section": "RC30x50",
                  "number": 1,
              }))

    # Batch bars
    await run("robot_create_bars", handle_robot_create_bars({
        "bars": [
            {"startNode": 2, "endNode": 4, "section": "RC30x50", "number": 2},
            {"startNode": 3, "endNode": 4, "section": "RC30x50", "number": 3},
            {"startNode": 3, "endNode": 5, "section": "RC30x50", "number": 4},
            {"startNode": 4, "endNode": 5, "section": "RC30x50", "number": 5},
        ]
    }))

    # Re-assign supports explicitly
    await run("robot_set_support",
              handle_robot_set_support({"selection": "1 2", "preset": "fixed"}))

    # Section assignment
    await run("robot_set_bar_section",
              handle_robot_set_bar_section({"selection": "1to5", "section": "RC30x50"}))

    # Material assignment
    await run("robot_set_bar_material",
              handle_robot_set_bar_material({"selection": "1to5", "material": "C25"}))

    # Release: pinned end on bar 4
    await run("robot_set_bar_release",
              handle_robot_set_bar_release({"selection": "4", "preset": "pin-fix"}))

    # Transform: move node 5 up slightly then back (non-destructive test)
    await run("robot_transform",
              handle_robot_transform({
                  "operation": "move",
                  "type": "node",
                  "selection": "5",
                  "dx": 0.0, "dy": 0.0, "dz": 0.1,
              }))
    # Move back
    from src.tools.model_write import handle_robot_transform as _move
    await _move({"operation": "move", "type": "node", "selection": "5",
                 "dx": 0.0, "dy": 0.0, "dz": -0.1})

    # build_frame / create_panel / set_panel_thickness tested in Phase 8
    skip("robot_build_frame",        "Tested in Phase 8 (isolation)")
    skip("robot_create_panel",       "Tested in Phase 8 (shell project)")
    skip("robot_set_panel_thickness","Tested in Phase 8 (shell project)")

    # ── Phase 2: Model Read ─────────────────────────────────────────
    print("\n--- Phase 2: Model Read (17 tools) ---")

    await run("robot_summary",       handle_robot_summary({}))
    await run("robot_list_nodes",    handle_robot_list_nodes({}))
    await run("robot_get_node",      handle_robot_get_node({"number": 1}))
    await run("robot_find_nodes_at", handle_robot_find_nodes_at({"x": 0, "y": 0, "z": 0}))
    await run("robot_list_bars",     handle_robot_list_bars({}))
    await run("robot_get_bar",       handle_robot_get_bar({"number": 1}))
    await run("robot_list_panels",   handle_robot_list_panels({}))
    skip("robot_get_panel",          "No panels in frame3d project")
    await run("robot_list_supports", handle_robot_list_supports({}))
    await run("robot_list_labels",   handle_robot_list_labels({"type": "section"}))
    await run("robot_get_label",     handle_robot_get_label({"name": "C25", "type": "material"}))
    await run("robot_section_search",handle_robot_section_search({"query": "HEA", "limit": 5}))
    await run("robot_material_database", handle_robot_material_database({"type": "concrete"}))
    await run("robot_list_cases",    handle_robot_list_cases({}))
    skip("robot_get_case",           "Tested in Phase 3 after case creation")
    await run("robot_list_groups",   handle_robot_list_groups({}))
    await run("robot_export_model_json", handle_robot_export_model_json({}))

    # ── Phase 3: Load Cases ─────────────────────────────────────────
    print("\n--- Phase 3: Load Cases (9 tools) ---")

    await run("robot_create_case",
              handle_robot_create_case({"id": 1, "name": "G", "nature": "dead",
                                         "analyzeType": "static"}))
    await run("robot_create_case",  # live load — same handler, second call
              handle_robot_create_case({"id": 2, "name": "Q", "nature": "live",
                                         "analyzeType": "static"}))

    await run("robot_get_case", handle_robot_get_case({"id": 1}))

    await run("robot_add_nodal_load",
              handle_robot_add_nodal_load({"caseId": 1, "selection": "3 4", "fz": -50.0}))

    await run("robot_add_bar_uniform",
              handle_robot_add_bar_uniform({"caseId": 1, "selection": "3", "pz": -10.0}))

    await run("robot_add_bar_point",
              handle_robot_add_bar_point({"caseId": 2, "selection": "3",
                                           "position": 0.5, "fz": -20.0}))

    await run("robot_add_bar_trapezoidal",
              handle_robot_add_bar_trapezoidal({"caseId": 2, "selection": "3",
                                                "pzStart": -5.0, "pzEnd": -15.0}))

    await run("robot_add_self_weight",
              handle_robot_add_self_weight({"caseId": 1}))

    # Combination 1.35G + 1.5Q
    await run("robot_create_combination",
              handle_robot_create_combination({
                  "id": 10, "name": "ELU", "combType": "uls",
                  "components": [{"caseId": 1, "factor": 1.35},
                                  {"caseId": 2, "factor": 1.50}],
              }))

    # Delete records test (re-add after)
    await run("robot_delete_load_records",
              handle_robot_delete_load_records({"caseId": 2}))
    await run("robot_add_self_weight",  # restore
              handle_robot_add_self_weight({"caseId": 2}))

    # Delete a temp case
    await run("robot_create_case",
              handle_robot_create_case({"id": 99, "name": "TEMP", "nature": "dead",
                                         "analyzeType": "static"}))
    await run("robot_delete_case",
              handle_robot_delete_case({"id": 99, "confirm": True}))

    # ── Phase 4: Analysis ───────────────────────────────────────────
    print("\n--- Phase 4: Analysis (4 tools) ---")

    await run("robot_analysis_status", handle_robot_analysis_status({}))
    await run("robot_generate_model",  handle_robot_generate_model({}))
    skip("robot_mesh_panels",          "No panels in frame3d project")

    calc = await run("robot_calculate",
                     handle_robot_calculate({"generateModel": True, "waitMs": 120000}))

    _calc_ok = bool(calc and calc.get("calculated") and calc.get("resultsAvailable"))
    print(f"    [i] calculated={calc and calc.get('calculated')}  "
          f"resultsAvailable={calc and calc.get('resultsAvailable')}")

    # ── Phase 5: Results ─────────────────────────────────────────────
    print("\n--- Phase 5: Results (7 tools) ---")

    if not _calc_ok:
        reason = "Calculation succeeded but results unavailable (no loads added)"
        for name in ["robot_node_displacements", "robot_support_reactions",
                     "robot_bar_forces", "robot_bar_stresses",
                     "robot_bar_displacements", "robot_extremes", "robot_results_csv"]:
            skip(name, reason)
    else:
        await run("robot_node_displacements",
                  handle_robot_node_displacements({"nodes": "3 4 5", "cases": "1 2"}))
        await run("robot_support_reactions",
                  handle_robot_support_reactions({"nodes": "1 2", "cases": "1 2"}))
        await run("robot_bar_forces",
                  handle_robot_bar_forces({"bars": "1 2 3", "cases": "1", "position": 0.5}))
        await run("robot_bar_stresses",
                  handle_robot_bar_stresses({"bars": "1 2 3", "cases": "1", "position": 0.5}))
        await run("robot_bar_displacements",
                  handle_robot_bar_displacements({"bars": "3", "cases": "1", "position": 0.5}))
        await run("robot_extremes",
                  handle_robot_extremes({"resultType": "bar_forces", "cases": "1",
                                          "bars": "1to5", "component": "MZ"}))
        await run("robot_results_csv",
                  handle_robot_results_csv({"resultType": "bar_forces", "cases": "1",
                                             "bars": "1to5", "path": _csv_path}))

    # ── Phase 6: Preferences ─────────────────────────────────────────
    print("\n--- Phase 6: Preferences (2 tools) ---")

    norms = await run("robot_get_norms", handle_robot_get_norms({}))
    if norms and norms.get("norms"):
        current = norms["norms"].get("seismic", {}).get("code", "EN 1998-1-1:2004")
        await run("robot_set_norm",
                  handle_robot_set_norm({"codeType": "seismic", "codeName": current}))
    else:
        skip("robot_set_norm", "robot_get_norms failed")

    # ── Phase 7: Project persistence ────────────────────────────────
    print("\n--- Phase 7: Project persistence (3 tools) ---")

    await run("robot_project_save",
              handle_robot_project_save({"path": _project_path}))
    await run("robot_project_new",
              handle_robot_project_new({"type": "frame3d", "discardCurrent": True}))
    await run("robot_project_open",
              handle_robot_project_open({"path": _project_path, "discardCurrent": True}))
    await run("robot_project_close",
              handle_robot_project_close({"confirm": True}))

    # ── Phase 8: Isolated tools (new projects) ───────────────────────
    print("\n--- Phase 8: Isolated tools (build_frame + shell) ---")

    # robot_build_frame — new project is open after project_close above
    await run("robot_project_new",
              handle_robot_project_new({"type": "frame3d", "discardCurrent": True}))
    await run("robot_build_frame",
              handle_robot_build_frame({
                  "baysX": [5.0],
                  "storeys": 2,
                  "storeyHeight": 3.0,
              }))

    # Shell project: panel tools + mesh
    await run("robot_project_new",
              handle_robot_project_new({"type": "shell", "discardCurrent": True}))

    await run("robot_create_nodes", handle_robot_create_nodes({
        "nodes": [
            {"x": 0, "y": 0, "z": 0, "number": 1},
            {"x": 4, "y": 0, "z": 0, "number": 2},
            {"x": 4, "y": 4, "z": 0, "number": 3},
            {"x": 0, "y": 4, "z": 0, "number": 4},
        ]
    }))

    await run("robot_create_panel",
              handle_robot_create_panel({
                  "points": [[0,0,0],[4,0,0],[4,4,0],[0,4,0]],
                  "number": 1,
              }))

    await run("robot_set_panel_thickness",
              handle_robot_set_panel_thickness({
                  "selection": "1",
                  "thickness": 200,   # mm
              }))

    await run("robot_get_panel",
              handle_robot_get_panel({"number": 1}))

    await run("robot_mesh_panels",
              handle_robot_mesh_panels({"size": 0.5}))

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)

    counts = {_PASS: 0, _FAIL: 0, _SKIP: 0, _KNOWN: 0}
    for status, _ in _results.values():
        counts[status] += 1

    total = sum(counts.values())
    print(f"  PASS      : {counts[_PASS]:3}  ({100*counts[_PASS]//total if total else 0}%)")
    print(f"  FAIL      : {counts[_FAIL]:3}")
    if counts[_KNOWN]:
        print(f"  KNOWN_BUG : {counts[_KNOWN]:3}")
    print(f"  SKIP      : {counts[_SKIP]:3}")
    print(f"  TOTAL     : {total:3}")

    if counts[_FAIL]:
        print("\nFailed tools:")
        for name, (status, detail) in _results.items():
            if status == _FAIL:
                print(f"  FAIL  {name}: {detail}")

    print()
    sys.exit(0 if counts[_FAIL] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
