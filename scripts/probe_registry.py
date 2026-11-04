"""
Probe script — find Robot 2013 language setting in registry and via COM.
Run with Robot CLOSED, change language manually in Tools > Preferences > Languages,
then run again to see what changed.

Usage: python scripts/probe_registry.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import winreg

def dump_key(root, path, depth=0):
    indent = "  " * depth
    try:
        k = winreg.OpenKey(root, path)
    except OSError as e:
        print(f"{indent}[CANNOT OPEN] {path}: {e}")
        return
    # Values
    i = 0
    while True:
        try:
            name, val, vtype = winreg.EnumValue(k, i)
            print(f"{indent}  [{name}] = {val!r}  (type={vtype})")
            i += 1
        except OSError:
            break
    # Sub-keys
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(k, i)
            print(f"{indent}  KEY: {sub}")
            dump_key(root, path + "\\" + sub, depth + 1)
            i += 1
        except OSError:
            break
    winreg.CloseKey(k)

ROOT_PATHS = [
    # Robot stores most settings here
    r"Software\Autodesk\Structural",
    r"Software\Autodesk\Robot Structural Analysis",
    r"Software\Autodesk\Robot Structural Analysis Professional 2013",
    r"Software\Autodesk\RSA Professional 2013",
    r"Software\Robots",
    # Robot old-style path
    r"Software\Autodesk\AutoCAD Structural Detailing",
]

print("=" * 60)
print("HKEY_CURRENT_USER robot/structural keys")
print("=" * 60)
for p in ROOT_PATHS:
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, p)
        winreg.CloseKey(k)
        print(f"\nFound: HKCU\\{p}")
        dump_key(winreg.HKEY_CURRENT_USER, p)
    except OSError:
        pass

print("\n" + "=" * 60)
print("HKEY_LOCAL_MACHINE robot/structural keys")
print("=" * 60)
for p in ROOT_PATHS:
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, p)
        winreg.CloseKey(k)
        print(f"\nFound: HKLM\\{p}")
        dump_key(winreg.HKEY_LOCAL_MACHINE, p)
    except OSError:
        pass

# Also scan HKCU\Software\Autodesk for anything with "robot" in the subkey name
print("\n" + "=" * 60)
print("All HKCU\\Software\\Autodesk subkeys")
print("=" * 60)
try:
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Autodesk")
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(k, i)
            print(f"  {sub}")
            i += 1
        except OSError:
            break
    winreg.CloseKey(k)
except OSError as e:
    print(f"Cannot open HKCU\\Software\\Autodesk: {e}")

# COM probe — try app.Preferences.GetLanguage / SetLanguage
print("\n" + "=" * 60)
print("COM probe — app.Preferences")
print("=" * 60)
try:
    import win32com.client as win32
    import pythoncom
    pythoncom.CoInitialize()
    app = win32.Dispatch("Robot.Application")
    prefs = app.Preferences
    print(f"  app.Preferences = {prefs}")
    print(f"  dir(prefs) = {[m for m in dir(prefs) if not m.startswith('_')]}")

    # Try I_L_WORK=1, I_L_PRINTOUT=2, I_L_REGIONAL=3
    for i_l, name in [(1, "I_L_WORK"), (2, "I_L_PRINTOUT"), (3, "I_L_REGIONAL")]:
        try:
            val = prefs.GetLanguage(i_l)
            print(f"  prefs.GetLanguage({i_l} = {name}) = {val!r}")
        except Exception as e:
            print(f"  prefs.GetLanguage({i_l} = {name}) ERROR: {e}")

    # Try direct attribute access
    for attr in ["Language", "WorkLanguage", "PrintLanguage", "RegionalLanguage",
                 "LangWork", "LangPrint", "LangRegional"]:
        try:
            val = getattr(prefs, attr)
            print(f"  prefs.{attr} = {val!r}")
        except Exception as e:
            print(f"  prefs.{attr} ERROR: {e}")
except Exception as e:
    print(f"  COM probe ERROR (is Robot running?): {e}")

print("\nDone.")
print("To find the language key: change language manually in Robot (Tools > Preferences > Languages)")
print("then run this script again and compare the output.")
