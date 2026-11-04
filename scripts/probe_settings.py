"""
Probe script — explore IRobotApplication and IRobotPreferences settings.
Tests: language, units, design norms, database paths.
Robot must be running with a project open.
Usage: python scripts/probe_settings.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import win32com.client as win32
import pythoncom

pythoncom.CoInitialize()
app = win32.Dispatch("Robot.Application")
app.Visible = True

print("=" * 60)
print("IRobotApplication — top-level settings")
print("=" * 60)

# ── Language ────────────────────────────────────────────────────────
print("\n[1] app.Language")
try:
    lang = app.Language
    print(f"  app.Language = {lang}  (type: {type(lang).__name__})")
except Exception as e:
    print(f"  app.Language ERROR: {e}")

# ── Version / ServerName ────────────────────────────────────────────
for attr in ["Version", "ServerName", "RobotPath", "UserPath", "ExePath"]:
    try:
        val = getattr(app, attr)
        print(f"  app.{attr} = {val!r}")
    except Exception as e:
        print(f"  app.{attr} ERROR: {e}")

# ── app.Preferences ────────────────────────────────────────────────
print("\n[2] app.Preferences (IRobotPreferences)")
try:
    prefs = app.Preferences
    print(f"  app.Preferences accessible: {prefs}")

    # Try common properties
    for attr in [
        "Language", "DisplayLanguage", "DataLanguage",
        "ActiveDir", "UserDir", "SystemDir",
        "NumberFormat", "DecimalSeparator",
    ]:
        try:
            val = getattr(prefs, attr)
            print(f"  prefs.{attr} = {val!r}")
        except Exception as e:
            print(f"  prefs.{attr} ERROR: {e}")
except Exception as e:
    print(f"  app.Preferences ERROR: {e}")

# ── Project preferences ─────────────────────────────────────────────
print("\n[3] app.Project.Preferences (IRobotProjectPreferences)")
try:
    pp = app.Project.Preferences
    print(f"  Project.Preferences accessible: {pp}")

    # Units
    print("\n  [3a] Units:")
    for attr in [
        "UnitLength", "UnitForce", "UnitMass", "UnitTemperature",
        "UnitAngle", "UnitDimension", "UnitMoment", "UnitArea",
        "UnitVolume", "UnitDensity", "UnitPressure", "UnitStress",
        "UnitAcceleration", "UnitVelocity", "UnitEnergy", "UnitPower",
        "LengthUnit", "ForceUnit", "MassUnit",
    ]:
        try:
            val = getattr(pp, attr)
            print(f"  pp.{attr} = {val!r}")
        except Exception:
            pass

    # Norms / design codes
    print("\n  [3b] Norms/Codes:")
    for attr in [
        "NormConc", "NormSteel", "NormTimber", "NormAlum",
        "ConcreteNorm", "SteelNorm", "TimberNorm", "AluNorm",
        "DesignCode", "DesignNorm", "NormCode",
        "ConcNorm", "RebarNorm",
    ]:
        try:
            val = getattr(pp, attr)
            print(f"  pp.{attr} = {val!r}")
        except Exception:
            pass

    # Database paths
    print("\n  [3c] Databases:")
    for attr in [
        "SteelDatabase", "ConcDatabase", "SectionDatabase", "MaterialDatabase",
        "ActiveDatabases", "Database", "DatabasePath",
        "SteelDBase", "ConcDBase",
    ]:
        try:
            val = getattr(pp, attr)
            print(f"  pp.{attr} = {val!r}")
        except Exception:
            pass

    # Other
    print("\n  [3d] Other:")
    for attr in [
        "GravDir", "GravityDir", "GravDirection",
        "GravFactor", "GravityFactor",
        "StructureType", "ProjectType",
        "MapCodes", "NormMap",
    ]:
        try:
            val = getattr(pp, attr)
            print(f"  pp.{attr} = {val!r}")
        except Exception:
            pass

except Exception as e:
    print(f"  Project.Preferences ERROR: {e}")

# ── Enumerate Preferences via COM typelib ───────────────────────────
print("\n[4] Introspect IRobotPreferences methods/properties (dir)")
try:
    prefs = app.Preferences
    members = [m for m in dir(prefs) if not m.startswith('_')]
    print(f"  dir(prefs) = {members}")
except Exception as e:
    print(f"  dir(prefs) ERROR: {e}")

print("\n[5] Introspect Project.Preferences methods/properties (dir)")
try:
    pp = app.Project.Preferences
    members = [m for m in dir(pp) if not m.startswith('_')]
    print(f"  dir(pp) = {members}")
except Exception as e:
    print(f"  dir(pp) ERROR: {e}")

# ── Norm constants in typelib ───────────────────────────────────────
print("\n[6] Try loading norms from typelib constants")
try:
    from win32com.client import gencache
    mod = gencache.EnsureModule('{F3A37BD0-AA2D-11D2-9844-0080C86BE4DF}', 0, 1, 0)
    items = [(k, v) for k, v in vars(mod).items()
             if ('NORM' in k.upper() or 'I_DN' in k.upper() or 'I_LU' in k.upper())
             and isinstance(v, int)]
    items.sort(key=lambda x: x[1])
    if items:
        print("  Norm/unit constants found:")
        for k, v in items[:60]:
            print(f"    {k} = {v}")
    else:
        print("  No norm/unit constants found in typelib")
    # Language constants
    lang_items = [(k, v) for k, v in vars(mod).items()
                  if 'I_LA' in k and isinstance(v, int)]
    if lang_items:
        lang_items.sort(key=lambda x: x[1])
        print("\n  Language constants (I_LA_*):")
        for k, v in lang_items:
            print(f"    {k} = {v}")
except Exception as e:
    print(f"  typelib probe ERROR: {e}")

print("\nDone.")
