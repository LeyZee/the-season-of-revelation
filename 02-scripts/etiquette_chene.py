#!/usr/bin/env python3
"""
etiquette_chene.py - l'étiquette (citybar) du Chêne des Âges au-dessus de son arbre.

Pourquoi (23.09.2026, 00 h 50 ; Charles : « la vignette qui annonce le nom de la ville, on ne la voit pas, elle est cachée
par l'arbre »). Le modèle de colonie de WH3 (`prefabs/campaign/wef_oak_of_ages_0N.bmd`) est un arbre géant ; CA laisse
`citybar_height_offset` à 0 pour ses 887 colonies, Chêne des Empires compris : l'étiquette naît au pied de l'arbre, dans
le tronc. On la relève pour la seule colonie du Chêne (`HAUTEUR`, unités du monde).

Usage :
    python etiquette_chene.py            # contrôle
    python etiquette_chene.py --apply    # écrit dans raw_data\\db (sauvegarde d'abord dans 05-journal\\db-backups\\)
"""

import argparse
import os
import re
import shutil
import sys
import time

DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
SAUVEGARDES = r"C:\TotalWar-CampaignMap\05-journal\db-backups"
TABLE = "campaign_map_settlements"
COLONIE = "settlement:wh_dlc05_oak_of_ages"
HAUTEUR = "3"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    chemin = os.path.join(DB, TABLE + ".xml")
    t = open(chemin, encoding="utf-8").read()
    blocs = [m for m in re.finditer(rf"<{TABLE}\b[^>]*>.*?</{TABLE}>", t, re.S) if f"<settlement_id>{COLONIE}</settlement_id>" in m.group(0)]
    if len(blocs) != 1:
        raise SystemExit(f"{COLONIE} : {len(blocs)} ligne(s) au lieu d'une")
    m = blocs[0]
    ancien = re.search(r"<citybar_height_offset>([^<]*)</citybar_height_offset>", m.group(0))
    print(f"{COLONIE} : citybar_height_offset {ancien.group(1)} -> {HAUTEUR}")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply")
        return 0
    os.makedirs(SAUVEGARDES, exist_ok=True)
    dest = os.path.join(SAUVEGARDES, time.strftime("%Y%m%d-%H%M%S") + "-etiquette-chene")
    os.makedirs(dest)
    shutil.copy(chemin, dest)
    neuf = m.group(0).replace(ancien.group(0), f"<citybar_height_offset>{HAUTEUR}</citybar_height_offset>")
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(t[:m.start()] + neuf + t[m.end():])
    print(f"écrit ; sauvegarde : {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
