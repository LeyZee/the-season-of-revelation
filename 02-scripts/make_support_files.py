#!/usr/bin/env python3
"""
make_support_files.py - crée les quatre fichiers d'appui qu'un projet de carte Warhammer 3 doit
contenir à côté de son map.hex, sans quoi **MapDataBuilder plante** (access violation 0xC0000005,
aucun message) : `trees.png`, `tree_database.xml`, `dynamic_resources.png`,
`dynamic_resources_database.xml`.

C'est la règle C20 de `ERREURS-ET-LECONS.md`, apprise le 20.09.2026 sur la première carte inventée
et re-apprise (à mes dépens) sur « La Saison des Révélations ».

Proportions mesurées sur les cartes livrées par CA (prologue 800 x 600, île 240 x 160) :
    trees.png              7,04 px par hex en largeur, 7,375 en hauteur
    dynamic_resources.png  2,5417 px par hex en largeur, 2,40 en hauteur
Les images sont créées vides (transparentes) : elles ne portent que le visuel, et le validateur
comme MapDataBuilder ne demandent que leur présence et leur format. Les deux XML sont copiés d'un
projet existant (le prologue par défaut), ce sont des définitions de jeu, pas des données de carte.

Usage :
    python make_support_files.py --map <dossier du projet> --width 400 --height 440
        [--from <dossier modèle>] [--force]
"""

import argparse
import os
import shutil
import sys

from PIL import Image

TREES_X, TREES_Y = 7.04, 7.375
RESOURCES_X, RESOURCES_Y = 2.5417, 2.40
PROLOGUE = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
            r"\assembly_kit\raw_data\EmpireDesignData\campaign_maps\wh3_main_prologue_map")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", required=True, help="dossier du projet (celui qui contient map.hex)")
    ap.add_argument("--width", type=int, required=True, help="largeur de la carte en hex")
    ap.add_argument("--height", type=int, required=True, help="hauteur de la carte en hex")
    ap.add_argument("--from", dest="model", default=PROLOGUE, help="projet d'où copier les deux XML")
    ap.add_argument("--force", action="store_true", help="réécrire les fichiers déjà présents")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not os.path.isdir(a.map):
        raise SystemExit(f"dossier introuvable : {a.map}")

    images = {
        "trees.png": (round(a.width * TREES_X), round(a.height * TREES_Y)),
        "dynamic_resources.png": (round(a.width * RESOURCES_X), round(a.height * RESOURCES_Y)),
    }
    for name, size in images.items():
        path = os.path.join(a.map, name)
        if os.path.exists(path) and not a.force:
            print(f"  {name:32s} déjà présent")
            continue
        Image.new("RGBA", size, (0, 0, 0, 0)).save(path)
        print(f"  {name:32s} créé  {size[0]} x {size[1]} px")

    for name in ("tree_database.xml", "dynamic_resources_database.xml"):
        path = os.path.join(a.map, name)
        if os.path.exists(path) and not a.force:
            print(f"  {name:32s} déjà présent")
            continue
        source = os.path.join(a.model, name)
        if not os.path.exists(source):
            raise SystemExit(f"modèle introuvable : {source}")
        shutil.copyfile(source, path)
        print(f"  {name:32s} copié depuis {os.path.basename(a.model)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
