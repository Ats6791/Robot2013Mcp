"""
Robot COM connection layer — Robot 2013 compatible.

Key Robot 2013 constraints:
  - results.Available (bool) is safe; results.Status does NOT exist in 2013
  - IRobotResultServer has no get_Status() — use .Available only
  - COM ProgID: "Robot.Application" (version-independent)
  - win32com late binding — no CastTo(), work with returned objects directly
"""

from __future__ import annotations
import sys
import subprocess
import time
from typing import Any


def _is_robot_running() -> bool:
    """Return True if a robot.exe process is currently running."""
    try:
        import psutil  # type: ignore
        return any(
            (p.info["name"] or "").lower() == "robot.exe"
            for p in psutil.process_iter(["name"])
        )
    except Exception:
        return False


def _server_count(server: Any) -> int:
    """Return element count for a Robot 2013 object server.

    IRobotNodeServer / IRobotBarServer / IRobotObjectServer / IRobotCaseServer
    do NOT expose a .Count property in Robot 2013 — use GetAll().Count instead.
    """
    try:
        return int(server.GetAll().Count)
    except Exception:
        return 0

# ──────────────────────────────────────────────────────────────────
# COM constants (Robot 2013 enum values)
# ──────────────────────────────────────────────────────────────────

# IRobotProjectType
I_PT_FRAME_3D       = 1
I_PT_FRAME_2D       = 2
I_PT_TRUSS_3D       = 3
I_PT_TRUSS_2D       = 4
I_PT_SHELL          = 5
I_PT_PLATE          = 7
I_PT_GRILLAGE       = 8
I_PT_BUILDING       = 9
I_PT_AXISYMMETRIC   = 10
I_PT_VOLUMETRIC     = 12
I_PT_PLANE_STRESS   = 13
I_PT_PLANE_DEFORM   = 14

PROJECT_TYPES: dict[str, int] = {
    "frame3d":       I_PT_FRAME_3D,
    "frame2d":       I_PT_FRAME_2D,
    "truss3d":       I_PT_TRUSS_3D,
    "truss2d":       I_PT_TRUSS_2D,
    "shell":         I_PT_SHELL,
    "plate":         I_PT_PLATE,
    "grillage":      I_PT_GRILLAGE,
    "building":      I_PT_BUILDING,
    "axisymmetric":  I_PT_AXISYMMETRIC,
    "volumetric":    I_PT_VOLUMETRIC,
    "plane_stress":  I_PT_PLANE_STRESS,
    "plane_deformation": I_PT_PLANE_DEFORM,
}
PROJECT_TYPES_INV: dict[int, str] = {v: k for k, v in PROJECT_TYPES.items()}

# IRobotLabelType
I_LT_NODE_SUPPORT    = 2
I_LT_NODE_MASS       = 3
I_LT_BAR_CABLE       = 7
I_LT_BAR_OFFSET      = 9
I_LT_BAR_MEMBER_TYPE = 11
I_LT_THICKNESS       = 17
I_LT_BAR_MATERIAL    = 20
I_LT_EDGE_SUPPORT    = 22
I_LT_BAR_SECTION     = 3
I_LT_BAR_RELEASE     = 25
I_LT_PANEL_RL_TYPE   = 40

LABEL_TYPES: dict[str, int] = {
    "support":       I_LT_NODE_SUPPORT,
    "node_mass":     I_LT_NODE_MASS,
    "cable":         I_LT_BAR_CABLE,
    "offset":        I_LT_BAR_OFFSET,
    "member_type":   I_LT_BAR_MEMBER_TYPE,
    "thickness":     I_LT_THICKNESS,
    "material":      I_LT_BAR_MATERIAL,
    "edge_support":  I_LT_EDGE_SUPPORT,
    "section":       I_LT_BAR_SECTION,
    "release":       I_LT_BAR_RELEASE,
    "reinforcement": I_LT_PANEL_RL_TYPE,
}

# IRobotLoadRecordType
I_LRT_NODE_FORCE             = 0
I_LRT_NODE_DISPLACEMENT      = 1
I_LRT_NODE_VELOCITY          = 2
I_LRT_NODE_ACCELERATION      = 3
I_LRT_BAR_UNIFORM            = 5
I_LRT_BAR_MOMENT             = 6
I_LRT_BAR_TRAPEZOIDAL        = 8
I_LRT_BODY_FORCE             = 9
I_LRT_NODAL_THERMAL          = 10
I_LRT_BAR_THERMAL            = 11
I_LRT_SELF_WEIGHT            = 12
I_LRT_NODE_ADDITIONAL_MASS   = 14
I_LRT_BAR_POINT              = 7   # probed: type 20 has no Objects; type 7 works

# IRobotBarUniformRecordValues
I_BURV_PX = 0; I_BURV_PY = 1; I_BURV_PZ = 2
I_BURV_ALPHA = 3; I_BURV_BETA = 4; I_BURV_GAMMA = 5
I_BURV_LOCAL = 6

# IRobotNodeForceRecordValues
I_NFRV_FX = 0; I_NFRV_FY = 1; I_NFRV_FZ = 2
I_NFRV_CX = 3; I_NFRV_CY = 4; I_NFRV_CZ = 5

# IRobotLoadNature
I_LNT_PERMANENT      = 0
I_LNT_EXPLOATATION   = 1
I_LNT_WIND           = 2
I_LNT_SNOW           = 3
I_LNT_TEMPERATURE    = 4
I_LNT_ACCIDENTAL     = 5
I_LNT_SEISMIC        = 6

LOAD_NATURES: dict[str, int] = {
    "dead":          I_LNT_PERMANENT,
    "permanent":     I_LNT_PERMANENT,
    "live":          I_LNT_EXPLOATATION,
    "exploatation":  I_LNT_EXPLOATATION,
    "wind":          I_LNT_WIND,
    "snow":          I_LNT_SNOW,
    "temperature":   I_LNT_TEMPERATURE,
    "accidental":    I_LNT_ACCIDENTAL,
    "seismic":       I_LNT_SEISMIC,
}

# IRobotCaseAnalizeType
# I_AT_STATIC=0 causes CreateSimple to produce cases with no Records interface;
# use 1 so that load records can be added to static cases.
I_AT_STATIC   = 1
I_AT_MODAL    = 2
I_AT_BUCKLING = 3
I_AT_HARMONIC = 4
I_AT_SEISMIC  = 5

ANALYSIS_TYPES: dict[str, int] = {
    "static":   I_AT_STATIC,
    "modal":    I_AT_MODAL,
    "buckling": I_AT_BUCKLING,
    "harmonic": I_AT_HARMONIC,
    "seismic":  I_AT_SEISMIC,
}

# IRobotCombinationType
I_CBT_ULS = 0; I_CBT_SLS = 1; I_CBT_ACC = 2

# IRobotBarSectionType (shape)
I_BST_NS_RECT  = 1
I_BST_NS_BOX   = 5
I_BST_NS_I     = 7
I_BST_NS_T     = 9
I_BST_NS_C     = 13
I_BST_NS_TUBE  = 18

# IRobotMaterialType
I_MT_STEEL     = 1
I_MT_CONCRETE  = 2
I_MT_TIMBER    = 3
I_MT_ALUMINIUM = 4
I_MT_OTHER     = 5

MATERIAL_TYPES: dict[str, int] = {
    "steel":     I_MT_STEEL,
    "concrete":  I_MT_CONCRETE,
    "timber":    I_MT_TIMBER,
    "aluminium": I_MT_ALUMINIUM,
    "other":     I_MT_OTHER,
}

# Self-weight direction values
I_SWRV_Z  = 2  # I_SWRV_GX=0, I_SWRV_GY=1, I_SWRV_GZ=2

# ──────────────────────────────────────────────────────────────────
# RobotClient — singleton
# ──────────────────────────────────────────────────────────────────

class RobotClient:
    """
    Lazy-init singleton that manages the COM connection to
    Autodesk Robot Structural Analysis 2013.
    Thread-unsafe by design: Robot COM is STA/single-threaded.
    """
    _instance: "RobotClient | None" = None

    def __init__(self) -> None:
        self._app: Any = None

    @classmethod
    def instance(cls) -> "RobotClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── connection ──────────────────────────────────────────────

    def _connect(self, launch: bool = True) -> Any:
        """Return a live IRobotApplication, (re)connecting as needed.

        Connection strategy (Robot 2013 compatible):
          1. Return cached object if it still responds.
          2. If robot.exe is running, attach via Dispatch() — Robot 2013 does
             not reliably register in the ROT so GetActiveObject() often fails.
             Fall back to GetActiveObject only as a secondary attempt.
          3. If robot.exe is not running and launch=False, raise RuntimeError.
          4. If robot.exe is not running and launch=True, start Robot via
             Dispatch(), set Visible and Interactive, then wait up to 60 s.
        """
        import pythoncom  # type: ignore
        import win32com.client as win32  # type: ignore

        # Ensure COM is initialised for this thread (safe to call multiple times).
        pythoncom.CoInitialize()

        # Return cached connection if still alive.
        if self._app is not None:
            try:
                _ = self._app.Visible   # ping
                return self._app
            except Exception:
                self._app = None

        robot_running = _is_robot_running()

        if robot_running:
            # Dispatch() attaches to the running single-instance server.
            try:
                self._app = win32.Dispatch("Robot.Application")
                _ = self._app.Visible   # verify alive
                return self._app
            except Exception:
                self._app = None
            # Fallback: try the ROT (may work on some Robot builds).
            try:
                self._app = win32.GetActiveObject("Robot.Application")
                return self._app
            except Exception:
                self._app = None

        if not launch:
            raise RuntimeError(
                "Robot is not running. Call robot_launch first, "
                "or open Robot manually and try again."
            )

        # Start Robot and wait up to 60 s for the project object to be ready.
        self._app = win32.Dispatch("Robot.Application")
        self._app.Visible = True
        self._app.Interactive = True
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                _ = self._app.Project
                break
            except Exception:
                time.sleep(1)
        return self._app

    def app(self, launch: bool = True) -> Any:
        return self._connect(launch)

    def project(self) -> Any:
        return self._connect().Project

    def structure(self) -> Any:
        return self._connect().Project.Structure

    # ── results availability (Robot 2013 safe) ──────────────────

    def results_available(self) -> bool:
        """
        Check if analysis results exist.
        Uses .Available only — .Status does NOT exist in Robot 2013.
        """
        try:
            return bool(self.structure().Results.Available)
        except Exception:
            return False

    # ── GeoContour helper ────────────────────────────────────────

    def make_contour(self, points: list[list[float]]) -> Any:
        """Create an IRobotPointsArray from [[x,y,z], ...] list.

        Robot 2013: Objects.CreateContour(id, IRobotPointsArray).
        IRobotPointsArray is created via Robot.PointsArray COM object.
        Indices are 1-based.
        """
        import win32com.client as win32  # type: ignore
        pa = win32.Dispatch("Robot.PointsArray")
        pa.SetSize(len(points))
        for i, p in enumerate(points):
            try:
                pa.Set(i + 1, float(p[0]), float(p[1]), float(p[2]))
            except Exception:
                pass
        return pa

    # ── selection helpers ────────────────────────────────────────

    def selection_from_text(self, text: str, obj_type: str = "bar") -> Any:
        """
        Return an IRobotSelection for the given Robot selection text
        (e.g. '1to10 15 20by2' or 'all').
        obj_type: 'node' | 'bar' | 'panel' | 'case'
        """
        struc = self.structure()
        sel = struc.Selections.Create({
            "node":  1,
            "bar":   2,
            "panel": 6,
            "case":  18,
        }.get(obj_type, 2))
        sel.FromText(text)
        return sel

    def ids_from_selection(self, sel_text: str, obj_type: str) -> list[int]:
        """Return sorted list of integer IDs for a Robot selection text."""
        try:
            sel = self.selection_from_text(sel_text, obj_type)
            count = sel.Count
            ids = []
            for i in range(1, count + 1):
                try:
                    ids.append(int(sel.Get(i)))
                except Exception:
                    pass
            return sorted(ids)
        except Exception:
            return []

    # ── label helpers ────────────────────────────────────────────

    def get_or_create_label(self, lbl_type: int, name: str) -> Any:
        labels = self.structure().Labels
        try:
            lbl = labels.Get(lbl_type, name)
            if lbl is not None:
                return lbl
        except Exception:
            pass
        return labels.Create(lbl_type, name)

    def store_label(self, lbl: Any) -> None:
        self.structure().Labels.Store(lbl)

    # ── section from database ─────────────────────────────────────

    def load_section(self, name: str) -> bool:
        """
        Ensure section label *name* exists in the project labels
        by loading it from the active databases.
        Returns True if found/loaded, False otherwise.
        """
        labels = self.structure().Labels
        try:
            lbl = labels.Get(I_LT_BAR_SECTION, name)
            if lbl is not None:
                return True
        except Exception:
            pass
        try:
            lbl = labels.Create(I_LT_BAR_SECTION, name)
            lbl.Data.LoadFromDBase(name)
            labels.Store(lbl)
            return True
        except Exception:
            return False

    def load_material(self, name: str) -> bool:
        """Load material from database into project labels."""
        labels = self.structure().Labels
        try:
            lbl = labels.Get(I_LT_BAR_MATERIAL, name)
            if lbl is not None:
                return True
        except Exception:
            pass
        try:
            lbl = labels.Create(I_LT_BAR_MATERIAL, name)
            lbl.Data.LoadFromDBase(name)
            labels.Store(lbl)
            return True
        except Exception:
            return False

    # ── node / bar helpers ───────────────────────────────────────

    def find_or_create_node(
        self,
        x: float, y: float, z: float,
        tolerance: float = 1e-4,
        number: int | None = None,
    ) -> int:
        """Return node number at (x,y,z), creating one if not found.

        Uses GetAll() for iteration (Robot 2013 servers have no .Count).
        Raises ValueError if the requested number is already taken by a
        node at different coordinates.
        """
        nodes = self.structure().Nodes

        # Search existing nodes via GetAll()
        try:
            coll = nodes.GetAll()
            for i in range(1, int(coll.Count) + 1):
                try:
                    n = coll.Get(i)
                    if (abs(n.X - x) < tolerance and
                            abs(n.Y - y) < tolerance and
                            abs(n.Z - z) < tolerance):
                        return int(n.Number)
                except Exception:
                    continue
        except Exception:
            pass

        # Check whether the requested number conflicts with an existing node
        if number is not None:
            if nodes.Exist(number):
                existing = nodes.Get(number)
                if (abs(existing.X - x) >= tolerance or
                        abs(existing.Y - y) >= tolerance or
                        abs(existing.Z - z) >= tolerance):
                    raise ValueError(
                        f"Node {number} already exists at "
                        f"({existing.X:.4f}, {existing.Y:.4f}, {existing.Z:.4f}), "
                        f"not at ({x:.4f}, {y:.4f}, {z:.4f}). "
                        "Use a different number or omit it to auto-assign."
                    )
                return number
            nid = number
        else:
            nid = int(nodes.FreeNumber)

        nodes.Create(nid, x, y, z)
        return nid

    def bar_free_number(self) -> int:
        return self.structure().Bars.FreeNumber

    def node_free_number(self) -> int:
        return self.structure().Nodes.FreeNumber

    # ── project type name ────────────────────────────────────────

    def project_type_name(self) -> str:
        try:
            pt = self.project().Type
            return PROJECT_TYPES_INV.get(pt, str(pt))
        except Exception:
            return "unknown"

    def is_bars_only_project(self) -> bool:
        """True for frame/truss projects that don't support panels."""
        try:
            pt = self.project().Type
            return pt in (I_PT_FRAME_3D, I_PT_FRAME_2D,
                          I_PT_TRUSS_3D, I_PT_TRUSS_2D)
        except Exception:
            return False


# Module-level singleton accessor
def robot() -> RobotClient:
    return RobotClient.instance()
