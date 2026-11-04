"""
TÂCHE 2 — Sonde l'API AxisMngr de Robot 2013.

Usage : python scripts/probe_axes.py
Robot doit être ouvert avec un projet actif.
"""
import win32com.client as w
import sys

app = w.gencache.EnsureDispatch("Robot.Application")
proj = app.Project

# 1. Vérifier AxisMngr
print("=== 1. AxisMngr disponible ? ===")
has_mngr = hasattr(proj, "AxisMngr")
in_dir   = "AxisMngr" in dir(proj)
print(f"  'AxisMngr' in dir(proj) = {in_dir}")
print(f"  hasattr(proj, 'AxisMngr') = {has_mngr}")

if not has_mngr:
    print("\n[ERREUR] AxisMngr n'existe PAS dans proj en Robot 2013.")
    print("Arrêt — reporter à l'utilisateur.")
    sys.exit(1)

mngr = proj.AxisMngr
print(f"\n=== 2. Méthodes de AxisMngr ===")
methods = [m for m in dir(mngr) if not m.startswith("_")]
print(" ", methods)

# 2. Lire les constantes énumérées
print("\n=== 3. Constantes I_SAGT / I_SALT ===")
try:
    consts = w.constants
    for name in dir(consts):
        if "SAGT" in name or "SALT" in name:
            print(f"  {name} = {getattr(consts, name)}")
except Exception as exc:
    print(f"  (constants inaccessibles: {exc})")
    print("  Tentative de lecture manuelle via typelib...")

# Valeurs typiques Robot 2013 (documentées dans l'API Robot) :
#   I_SAGT_CARTESIAN = 0
#   I_SALT_VALUE     = 0
#   I_SALT_123       = 1
#   I_SALT_ABC       = 2
#   I_SALT_DEFINE    = 3
I_SAGT_CARTESIAN = 0
I_SALT_VALUE     = 0
I_SALT_123       = 1
I_SALT_ABC       = 2
I_SALT_DEFINE    = 3

# 3. Créer une grille de test
print("\n=== 4. Création d'une grille de test ===")
TEST_NAME = "TEST_AXES_PROBE"

# Supprimer si elle existe déjà
try:
    existing = mngr.FindByName(TEST_NAME)
    if existing is not None:
        mngr.Delete(existing.Number)
        print(f"  Ancienne grille '{TEST_NAME}' supprimée.")
except Exception:
    pass

print(f"  Count avant création : {mngr.Count}")

# Essai 1 : Create(type, name)
grid = mngr.Create(I_SAGT_CARTESIAN, TEST_NAME)
print(f"  Create(0, name) → {grid!r}")

# Essai 2 : si Create renvoie None, GetByName après
if grid is None:
    print("  Create a renvoyé None → tentative GetByName...")
    try:
        grid = mngr.GetByName(TEST_NAME)
        print(f"  GetByName → {grid!r}")
    except Exception as e:
        print(f"  GetByName échoué : {e}")

# Essai 3 : Create(name, type)
if grid is None:
    print("  Tentative Create(name, type) ...")
    try:
        grid = mngr.Create(TEST_NAME, I_SAGT_CARTESIAN)
        print(f"  Create(name, 0) → {grid!r}")
    except Exception as e:
        print(f"  Create(name, type) échoué : {e}")

# Essai 4 : Create(name) seul
if grid is None:
    print("  Tentative Create(name) seul ...")
    try:
        grid = mngr.Create(TEST_NAME)
        print(f"  Create(name) → {grid!r}")
    except Exception as e:
        print(f"  Create(name) seul échoué : {e}")

# Essai 5 : Get(1) si count a changé
print(f"  Count après Create : {mngr.Count}")
if grid is None and mngr.Count > 0:
    print("  Count > 0 → tentative Get(1)...")
    try:
        grid = mngr.Get(1)
        print(f"  Get(1) → {grid!r}")
    except Exception as e:
        print(f"  Get(1) échoué : {e}")

if grid is None:
    print("\n[ERREUR] Impossible d'obtenir un objet grille valide. Arrêt.")
    # Nettoyage tentative
    try:
        g_del = mngr.FindByName(TEST_NAME)
        if g_del is not None:
            mngr.Delete(g_del.Number)
    except Exception:
        pass
    sys.exit(1)

print(f"\n  Objet grille obtenu : {grid!r}")
print(f"  dir(grid) = {[m for m in dir(grid) if not m.startswith('_')]}")

# AddSequence : on passe 3 valeurs
# Si absolu  → axes à 0, 3, 4.9
# Si espacement → axes à 0, 3, 7.9
try:
    grid.X.AddSequence(0, 1)
    grid.X.AddSequence(3, 1)
    grid.X.AddSequence(4.9, 1)
    grid.Save()
    print("  AddSequence(0,1), (3,1), (4.9,1) appelé et Save() fait.")
except Exception as exc:
    print(f"  AddSequence/Save erreur : {exc}")
    print(f"  dir(grid.X) = {[m for m in dir(grid.X) if not m.startswith('_')]}")

# 4. Relire la grille pour déduire la sémantique
print("\n=== 5. Relecture des axes X ===")
try:
    g2 = mngr.FindByName(TEST_NAME)
    if g2 is None:
        print("  FindByName a renvoyé None.")
    else:
        count = g2.X.Count
        print(f"  Nombre d'axes X : {count}")
        for i in range(1, count + 1):
            try:
                ax = g2.X.Get(i)
                print(f"    axe[{i}] : position = {ax.Position}  label = {ax.Label}")
            except Exception as e:
                try:
                    val = g2.X.GetValue(i)
                    print(f"    axe[{i}] : GetValue = {val}")
                except Exception as e2:
                    print(f"    axe[{i}] : inaccessible ({e} / {e2})")
except Exception as exc:
    print(f"  Impossible de relire : {exc}")
    print("  → Regarder dans Robot UI : Structure > Axes de la structure")
    print("    et noter les cotes affichées pour X (attendu 0, 3, 4.9 si absolu)")

# 5. Nettoyage
print("\n=== 6. Suppression de la grille de test ===")
try:
    g3 = mngr.FindByName(TEST_NAME)
    if g3 is not None:
        mngr.Delete(g3.Number)
        print(f"  Grille '{TEST_NAME}' supprimée.")
    else:
        print("  Grille introuvable (déjà supprimée?).")
except Exception as exc:
    print(f"  Erreur suppression : {exc}")

print("\n=== Sonde terminée. ===")
