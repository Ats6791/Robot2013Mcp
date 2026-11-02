"""
Test script — verifies robot_launch → robot_health chain.

Usage:
    python test_connection.py

Robot 2013 must be running (or will be started).
Expected output: running=True, robotVersion present, projectOpen reported.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from src.tools.session import handle_robot_launch, handle_robot_health


async def main() -> None:
    print("=== robot_launch ===")
    launch = await handle_robot_launch({"newProject": True, "projectType": "frame3d"})
    print(launch)

    print("\n=== robot_health ===")
    health = await handle_robot_health({})
    print(health)

    # Assertions
    assert health.get("running") is True, (
        f"FAIL: expected running=True, got: {health}"
    )
    assert "robotVersion" in health, (
        f"FAIL: robotVersion missing from health response: {health}"
    )
    print("\n✓ robot_health reports running=True")
    print(f"  version : {health.get('robotVersion')}")
    print(f"  project : {health.get('projectOpen')} — {health.get('projectName', '(no file)')}")
    print(f"  counts  : {health.get('counts')}")


if __name__ == "__main__":
    asyncio.run(main())
