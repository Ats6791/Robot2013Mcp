"""
Regression test — robot_create_nodes, _server_count, find_or_create_node.

Requires a running Robot 2013 instance (will start one if needed).

Pass conditions
---------------
1. Creates a fresh frame3d project.
2. Creates 3 nodes at distinct coordinates; count == 3.
3. Re-creating a node at existing coordinates reuses it (count stays 3).
4. robot_project_info returns nodes == 3.
5. Creates the 17-node layout from the task specification; count == 17.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.robot_client import robot, _server_count
from src.tools.session import handle_robot_launch, handle_robot_project_info
from src.tools.model_write import handle_robot_create_nodes, handle_robot_clear_structure


async def main() -> None:
    # ── Connect / start Robot ────────────────────────────────────
    print("Connecting to Robot 2013 ...")
    launch = await handle_robot_launch({"newProject": True, "projectType": "frame3d"})
    print(f"  launch: {launch}")

    # ── Clean slate ──────────────────────────────────────────────
    await handle_robot_clear_structure({"confirm": True})
    struc = robot().structure()
    assert _server_count(struc.Nodes) == 0, "Expected 0 nodes after clear"

    # ── Test 1: create 3 distinct nodes, count == 3 ──────────────
    print("\nTest 1: create 3 nodes ...")
    result = await handle_robot_create_nodes({
        "nodes": [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 3.0, "y": 0.0, "z": 0.0},
            {"x": 6.0, "y": 0.0, "z": 0.0},
        ]
    })
    print(f"  created ids: {result['created']}")
    count = _server_count(struc.Nodes)
    print(f"  node count:  {count}")
    assert count == 3, f"Expected 3 nodes, got {count}"
    print("  PASS")

    # ── Test 2: reuse existing node at same coords ────────────────
    print("\nTest 2: reuse node at (0, 0, 0) ...")
    result2 = await handle_robot_create_nodes({
        "nodes": [{"x": 0.0, "y": 0.0, "z": 0.0}],
        "reuseExisting": True,
    })
    reused_id = result2["created"][0]
    count2 = _server_count(struc.Nodes)
    print(f"  reused id:   {reused_id}  (should be 1 or the original id)")
    print(f"  node count:  {count2}  (should still be 3)")
    assert count2 == 3, f"Expected count still 3 after reuse, got {count2}"
    print("  PASS")

    # ── Test 3: robot_project_info returns correct count ─────────
    print("\nTest 3: robot_project_info ...")
    info = await handle_robot_project_info({})
    print(f"  counts: {info['counts']}")
    assert info["counts"]["nodes"] == 3, (
        f"Expected nodes==3 in project_info, got {info['counts']['nodes']}"
    )
    print("  PASS")

    # ── Test 4: 17-node layout ────────────────────────────────────
    print("\nTest 4: create 17-node layout ...")
    await handle_robot_clear_structure({"confirm": True})

    seventeen = [
        {"x": 0.0,  "y": 0.0,  "z": 0.0},
        {"x": 3.0,  "y": 0.0,  "z": 0.0},
        {"x": 6.0,  "y": 0.0,  "z": 0.0},
        {"x": 9.8,  "y": 0.0,  "z": 0.0},
        {"x": 0.0,  "y": 3.2,  "z": 0.0},
        {"x": 3.0,  "y": 3.2,  "z": 0.0},
        {"x": 6.0,  "y": 3.2,  "z": 0.0},
        {"x": 6.7,  "y": 3.2,  "z": 0.0},
        {"x": 9.8,  "y": 3.2,  "z": 0.0},
        {"x": 0.0,  "y": 6.4,  "z": 0.0},
        {"x": 3.0,  "y": 6.4,  "z": 0.0},
        {"x": 4.9,  "y": 6.4,  "z": 0.0},
        {"x": 6.7,  "y": 6.4,  "z": 0.0},
        {"x": 9.8,  "y": 6.4,  "z": 0.0},
        {"x": 0.0,  "y": 9.8,  "z": 0.0},
        {"x": 4.9,  "y": 9.8,  "z": 0.0},
        {"x": 9.8,  "y": 9.8,  "z": 0.0},
    ]
    r17 = await handle_robot_create_nodes({"nodes": seventeen})
    count17 = _server_count(struc.Nodes)
    print(f"  created:    {r17['count']} nodes")
    print(f"  actual count in Robot: {count17}")
    assert count17 == 17, f"Expected 17 nodes, got {count17}"

    info17 = await handle_robot_project_info({})
    assert info17["counts"]["nodes"] == 17, (
        f"project_info shows {info17['counts']['nodes']}, expected 17"
    )
    print(f"  project_info nodes: {info17['counts']['nodes']}")
    print("  PASS")

    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
