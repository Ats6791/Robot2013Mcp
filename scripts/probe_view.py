"""
Probe script — test IRobotViewDisplayAttributes (I_VDA_*) for robot_set_view.
Robot must be open with a project loaded.
Usage: python scripts/probe_view.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import win32com.client as win32
import pythoncom

pythoncom.CoInitialize()
app = win32.Dispatch("Robot.Application")
app.Visible = True

vm = app.Project.ViewMngr
print(f"ViewMngr.ViewCount = {vm.ViewCount}")

# Use view index 1 (first view)
v = vm.GetView(1)
pd = v.ParamsDisplay

# ── Constants confirmed from IRobotViewDisplayAttributes typelib ──────────
I_VDA_STRUCTURE_NODE_NUMBERS   = 2
I_VDA_STRUCTURE_BAR_NUMBERS    = 3
I_VDA_STRUCTURE_SUPPORT_SYMBOLS = 4
I_VDA_SECTIONS_SHAPE           = 14   # <-- section shapes in volume
I_VDA_FE_PANEL_CONTOURS        = 33
I_VDA_FE_PANEL_INTERIOR        = 34
I_VDA_FE_THICKNESS             = 35   # <-- panel thickness (bars-only view)
I_VDA_FE_PANEL_NUMBERS         = 36
I_VDA_OTHER_STRUCTURAL_AXIS    = 45
I_VDA_OTHER_GRID               = 47
I_VDA_FE_PANEL_THICKNESSES     = 89   # <-- panel thickness (FE view)
I_VDA_VIEW_SHADING             = 113  # <-- shaded/solid rendering
I_VDA_VIEW_SHADING_EDGES       = 114  # <-- shaded + edges
I_VDA_VIEW_QUICK_SHADING       = 115

# ── Print current state of key attributes ────────────────────────────────
print("\nCurrent display attribute states:")
attrs = [
    ("I_VDA_STRUCTURE_NODE_NUMBERS",  I_VDA_STRUCTURE_NODE_NUMBERS),
    ("I_VDA_STRUCTURE_BAR_NUMBERS",   I_VDA_STRUCTURE_BAR_NUMBERS),
    ("I_VDA_STRUCTURE_SUPPORT_SYMBOLS", I_VDA_STRUCTURE_SUPPORT_SYMBOLS),
    ("I_VDA_SECTIONS_SHAPE",          I_VDA_SECTIONS_SHAPE),
    ("I_VDA_FE_PANEL_CONTOURS",       I_VDA_FE_PANEL_CONTOURS),
    ("I_VDA_FE_PANEL_INTERIOR",       I_VDA_FE_PANEL_INTERIOR),
    ("I_VDA_FE_THICKNESS",            I_VDA_FE_THICKNESS),
    ("I_VDA_FE_PANEL_THICKNESSES",    I_VDA_FE_PANEL_THICKNESSES),
    ("I_VDA_OTHER_STRUCTURAL_AXIS",   I_VDA_OTHER_STRUCTURAL_AXIS),
    ("I_VDA_OTHER_GRID",              I_VDA_OTHER_GRID),
    ("I_VDA_VIEW_SHADING",            I_VDA_VIEW_SHADING),
    ("I_VDA_VIEW_SHADING_EDGES",      I_VDA_VIEW_SHADING_EDGES),
    ("I_VDA_VIEW_QUICK_SHADING",      I_VDA_VIEW_QUICK_SHADING),
]
for name, val in attrs:
    try:
        state = bool(pd.IsOn(val))
        print(f"  {name:45s} = {val:3d}  currently={'ON ' if state else 'off'}")
    except Exception as e:
        print(f"  {name:45s} = {val:3d}  ERROR: {e}")

# ── Set section shapes and panel thickness ON ─────────────────────────────
print("\nSetting sectionShapes=True, panelThickness=True, shading=True …")
errors = []
for name, val, enable in [
    ("I_VDA_SECTIONS_SHAPE",         I_VDA_SECTIONS_SHAPE,        True),
    ("I_VDA_FE_THICKNESS",           I_VDA_FE_THICKNESS,          True),
    ("I_VDA_FE_PANEL_THICKNESSES",   I_VDA_FE_PANEL_THICKNESSES,  True),
    ("I_VDA_FE_PANEL_INTERIOR",      I_VDA_FE_PANEL_INTERIOR,     True),
    ("I_VDA_VIEW_SHADING_EDGES",     I_VDA_VIEW_SHADING_EDGES,    True),
]:
    try:
        pd.Set(val, 1 if enable else 0)
        print(f"  Set {name} = {enable} -> OK")
    except Exception as e:
        print(f"  Set {name} = {enable} -> ERROR: {e}")
        errors.append((name, str(e)))

# Set 3D projection
from src.robot_client import I_VP_3DXYZ
try:
    v.Projection = I_VP_3DXYZ
    print("  Set Projection = I_VP_3DXYZ (3D axonometric) -> OK")
except Exception as e:
    print(f"  Set Projection -> ERROR: {e}")

# Redraw with zoom
try:
    v.Redraw(1)
    print("  Redraw(1) -> OK")
except Exception as e:
    print(f"  Redraw -> ERROR: {e}")

print("\n>>> Check Robot viewport now: bars should appear as 3D solid sections,")
print(">>> panels (footings/stair slabs) should show thickness.")
print(">>> Press Enter to restore to wireframe …")
input()

# ── Restore wireframe ─────────────────────────────────────────────────────
print("Restoring wireframe …")
for name, val, enable in [
    ("I_VDA_SECTIONS_SHAPE",       I_VDA_SECTIONS_SHAPE,       False),
    ("I_VDA_FE_THICKNESS",         I_VDA_FE_THICKNESS,         False),
    ("I_VDA_FE_PANEL_THICKNESSES", I_VDA_FE_PANEL_THICKNESSES, False),
    ("I_VDA_FE_PANEL_INTERIOR",    I_VDA_FE_PANEL_INTERIOR,    True),
    ("I_VDA_VIEW_SHADING_EDGES",   I_VDA_VIEW_SHADING_EDGES,   False),
]:
    try:
        pd.Set(val, 1 if enable else 0)
    except Exception:
        pass
try:
    v.Redraw(1)
    print("  Restored wireframe and redrawn.")
except Exception:
    pass

print("\nDone. Summary of I_VDA_* constants for robot_set_view:")
print("  sectionShapes  -> I_VDA_SECTIONS_SHAPE        = 14")
print("  panelThickness -> I_VDA_FE_THICKNESS           = 35")
print("                    I_VDA_FE_PANEL_THICKNESSES   = 89 (FE mesh view)")
print("  solid          -> I_VDA_VIEW_SHADING_EDGES     = 114")
print("  nodeNumbers    -> I_VDA_STRUCTURE_NODE_NUMBERS = 2")
print("  barNumbers     -> I_VDA_STRUCTURE_BAR_NUMBERS  = 3")
print("  supports       -> I_VDA_STRUCTURE_SUPPORT_SYMBOLS = 4")
