#!/usr/bin/env python3
"""
build_saison_map.py - fabrique, d'un bout à l'autre, la carte logique de « La Saison des
Révélations » dans Warhammer 3 à partir de la carte de Warhammer 1.

Enchaîne les huit étapes de la phase 1 du plan (`04-projets\\saison-des-revelations\\plan.md`) :

    1. declare_map.py        déclare la carte et ses 61 régions dans la base du kit WH3
    2. CAIME create          projet vierge 400 x 440 dans raw_data\\EmpireDesignData
    3. make_support_files    les quatre fichiers d'appui (règle C20)
    4. CAIME sync-names      inscrit dans le map.hex les noms que la base connaît
    5. caime_layers remap    recale les 13 couches WH1 sur les index WH3, par nom
    6. grow_town_slots       7 hex par colonie -> 19 (16 en port) + contour du danger
    7. CAIME import-layer    applique les 13 couches
    8. validate + process    les 11 validateurs, puis les cinq fichiers de jeu

Chaque étape s'arrête au premier échec, sauf les deux dernières dont le compte rendu est affiché
et conservé dans `05-journal\\<date>-...\\`. Toute la chaîne est rejouable : elle recrée le projet
depuis zéro à chaque fois, les sources WH1 étant lues dans `03-references\\`.

Usage :
    python build_saison_map.py [--skip-declare] [--journal <dossier>] [--no-process]
"""

import argparse
import os
import subprocess
import sys

ATELIER = r"C:\TotalWar-CampaignMap"
CAIME = ATELIER + r"\01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe"
AKIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
SCRIPTS = ATELIER + r"\02-scripts"
PROJET = ATELIER + r"\04-projets\saison-des-revelations"
SOURCE = ATELIER + r"\03-references\saison-des-revelations\wh_dlc05_wood_elves_map_1"
NAME, WIDTH, HEIGHT = "wh_dlc05_wood_elves_map_1", 400, 440

MAP_DIR = os.path.join(AKIT, "raw_data", "EmpireDesignData", "campaign_maps", NAME)
MAP_HEX = os.path.join(MAP_DIR, "map.hex")


def playable_area_index():
    """L'index (clé) de la zone jouable, lu dans la fiche du projet."""
    import json
    spec = json.load(open(os.path.join(PROJET, "map_spec.json"), encoding="utf-8"))
    return spec["playable_area"]["index"]


def step(label, cmd, keep=None):
    print(f"\n##### {label}")
    print("> " + " ".join(f'"{a}"' if " " in a else a for a in cmd[:4]) + (" ..." if len(cmd) > 4 else ""))
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.splitlines():
        if line.startswith(("Info: ", "App root")):
            continue
        if keep is None or any(k in line for k in keep):
            print("   " + line)
    print(f"[exit {p.returncode}]")
    return p.returncode, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-declare", action="store_true", help="la carte est déjà déclarée dans la base")
    ap.add_argument("--no-process", action="store_true", help="s'arrêter après les validateurs")
    ap.add_argument("--journal", default=None, help="dossier où écrire les comptes rendus")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not a.skip_declare:
        rc, _ = step("1. déclarer la carte dans la base du kit WH3",
                     ["python", os.path.join(SCRIPTS, "declare_map.py"), "--spec",
                      os.path.join(PROJET, "map_spec.json"), "--asskit", AKIT, "--apply"],
                     keep=["ajout", "Écrit", "Sauvegardes"])
        if rc != 0:
            return rc

        # Contournement d'un défaut de l'Assembly Kit : MapDataBuilder plante si la zone jouable
        # de la carte traitée est la dernière ligne de sa table (voir fix_playable_area_order.py).
        rc, _ = step("1 bis. ordre des zones jouables",
                     ["python", os.path.join(SCRIPTS, "fix_playable_area_order.py"),
                      "--asskit", AKIT, "--index", str(playable_area_index())])
        if rc != 0:
            return rc

    rc, _ = step(f"2. créer le projet {WIDTH} x {HEIGHT}",
                 [CAIME, "create", "--name", NAME, "--game", "Warhammer3", "--width", str(WIDTH),
                  "--height", str(HEIGHT), "--out", os.path.dirname(MAP_DIR), "--overwrite"],
                 keep=["created", "Size:", "error"])
    if rc != 0:
        return rc

    rc, _ = step("3. les quatre fichiers d'appui",
                 ["python", os.path.join(SCRIPTS, "make_support_files.py"), "--map", MAP_DIR,
                  "--width", str(WIDTH), "--height", str(HEIGHT)])
    if rc != 0:
        return rc

    rc, _ = step("4. inscrire les noms de la base dans la carte",
                 [CAIME, "sync-names", "--map", MAP_HEX], keep=["Map now holds", "Names:", "error"])
    if rc != 0:
        return rc

    rc, _ = step("5. recaler les couches WH1 sur les index WH3",
                 ["python", os.path.join(SCRIPTS, "caime_layers.py"), "remap", "--caime", CAIME,
                  "--source-map", os.path.join(SOURCE, "map.hex"), "--target-map", MAP_HEX,
                  "--layers", os.path.join(SOURCE, "couches-wh1-binaire"),
                  "--out", os.path.join(PROJET, "couches")])
    if rc != 0:
        return rc

    rc, _ = step("6. agrandir les emplacements de colonie",
                 ["python", os.path.join(SCRIPTS, "grow_town_slots.py"), "--caime", CAIME,
                  "--map", MAP_HEX, "--layers", os.path.join(PROJET, "couches"),
                  "--out", os.path.join(PROJET, "couches-slots")])
    if rc != 0:
        return rc

    sys.path.insert(0, SCRIPTS)
    from caime_layers import read_layer                     # noqa: E402
    layers_dir = os.path.join(PROJET, "couches-slots")
    args = [CAIME, "import-layer", "--map", MAP_HEX]
    for f in sorted(os.listdir(layers_dir)):
        if f.endswith(".hex_layer"):
            layer, _ = read_layer(os.path.join(layers_dir, f))   # le nom vient de l'en-tête du fichier
            args += ["--layer", layer, "--file", os.path.join(layers_dir, f)]
    rc, _ = step("7. importer les 13 couches", args, keep=["Saved:", "error"])
    if rc != 0:
        return rc

    rc, validate_out = step("8. les 11 validateurs", [CAIME, "validate", "--map", MAP_HEX, "--all"],
                            keep=[": OK", ": FAILED"])
    process_out = ""
    if not a.no_process:
        _, process_out = step("9. produire les cinq fichiers de jeu",
                              [CAIME, "process", "--map", MAP_HEX, "--map-data", "--pathfinding",
                               "--borders", "--trade-routes", "--lookup"],
                              keep=[": OK", ": FAILED", "MapDataBuilder"])

    if a.journal:
        os.makedirs(a.journal, exist_ok=True)
        open(os.path.join(a.journal, "validate-saison-wh3.txt"), "w", encoding="utf-8").write(validate_out)
        if process_out:
            open(os.path.join(a.journal, "process-saison-wh3.txt"), "w", encoding="utf-8").write(process_out)
        print(f"\ncomptes rendus écrits dans {a.journal}")

    produced = os.path.join(AKIT, "working_data", "campaign_maps", NAME)
    print("\nFichiers produits :")
    for f in sorted(os.listdir(produced)) if os.path.isdir(produced) else []:
        full = os.path.join(produced, f)
        if os.path.isfile(full):
            print(f"   {os.path.getsize(full):>12,} o  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
