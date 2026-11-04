"""
TÂCHE 4 — Test direct du handler handle_robot_create_axes (hors MCP).

Usage : python scripts/test_axes_direct.py
Robot doit être ouvert avec un projet actif.
"""
import sys
import os
import asyncio
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.tools.model_write import handle_robot_create_axes

args = {
    "x":       [0, 3.0, 4.9, 6.0, 6.7, 9.8],
    "xLabels": ["A", "B", "C", "D", "E", "F"],
    "y":       [0, 3.2, 6.4, 9.8],
    "yLabels": ["1", "2", "3", "4"],
    "z":       [0, 3, 6, 9, 12],
    "zLabels": ["Fondations", "PH RDC", "PH 1er", "PH 2e", "Couv. escalier"],
    "name":    "Grille DXF",
    "replace": True,
}

result = asyncio.run(handle_robot_create_axes(args))
print("Result:", result)

if "error" in result:
    print("\n[ECHEC] Erreur:", result["error"])
    sys.exit(1)
else:
    print("\n[OK] Grille creee avec succes.")
    print(f"  X: {result['axes']['x']} axes (A..F a 0, 3.0, 4.9, 6.0, 6.7, 9.8 m)")
    print(f"  Y: {result['axes']['y']} axes (1..4 a 0, 3.2, 6.4, 9.8 m)")
    print(f"  Z: {result['axes']['z']} axes (niveaux)")
    if result.get("warnings"):
        print("  Avertissements:", result["warnings"])
    print("\nVerifier dans Robot : Structure > Axes de la structure")
