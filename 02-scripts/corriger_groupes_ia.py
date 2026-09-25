#!/usr/bin/env python3
"""
corriger_groupes_ia.py - réécrit le groupe d'IA (`cai_personality_group`) des factions de la campagne
dans `start_pos_factions` du kit, selon la règle de `groupes_ia.py` (celle de CA).

Pourquoi : erreur 57 (21.09.2026) — un groupe sans personnalité faisait planter le chargement de la
campagne, et la traduction de Warhammer 1 laissait `default` à 20 factions. Voir `groupes_ia.py`.

Le script ne touche que la colonne `cai_personality_group` des lignes de la campagne, sauvegarde le
XML dans `05-journal\\db-backups\\` avant d'écrire, et dit ligne par ligne ce qu'il change et pourquoi.
Ensuite : `synchroniser_pack_startpos.py --table start_pos_factions --cle ID --maj --apply`, puis
régénérer le startpos (avec `--ai-map-data`).

Usage :
    python corriger_groupes_ia.py [--campagne wh_dlc05_wood_elves] [--apply]
"""

import argparse
import io
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from groupes_ia import Choix, KIT_DB                               # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campagne", default="wh_dlc05_wood_elves")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    chemin = os.path.join(KIT_DB, "start_pos_factions.xml")
    with io.open(chemin, encoding="utf-8", newline="") as f:
        texte = f.read()
    choix = Choix()
    changements = []

    def remplace(m):
        bloc = m.group(0)
        if f"<campaign>{a.campagne}</campaign>" not in bloc:
            return bloc
        faction = re.search(r"<faction>([^<]*)</faction>", bloc).group(1)
        actuel = re.search(r"<cai_personality_group>([^<]*)</cai_personality_group>", bloc).group(1)
        voulu, raison = choix.groupe(faction, actuel)
        if voulu == actuel:
            return bloc
        changements.append((faction, actuel, voulu, raison))
        return bloc.replace(f"<cai_personality_group>{actuel}</cai_personality_group>",
                            f"<cai_personality_group>{voulu}</cai_personality_group>", 1)

    neuf = re.sub(r"<start_pos_factions\b[^>]*>.*?</start_pos_factions>", remplace, texte, flags=re.S)
    for faction, actuel, voulu, raison in changements:
        print(f"  {faction:40s} {actuel:48s} -> {voulu}  ({raison})")
    print(f"{len(changements)} faction(s) à changer")
    if not a.apply or not changements:
        if not a.apply:
            print("essai à blanc : relancer avec --apply")
        return 0
    dossier = os.path.join(ATELIER, "05-journal", "db-backups",
                           datetime.now().strftime("%Y%m%d-%H%M%S") + "-groupes-ia")
    os.makedirs(dossier, exist_ok=True)
    shutil.copy2(chemin, dossier)
    with io.open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(neuf)
    print("kit écrit ; sauvegarde dans", dossier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
