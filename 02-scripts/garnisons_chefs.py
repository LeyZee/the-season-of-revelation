#!/usr/bin/env python3
"""
garnisons_chefs.py - met en garnison dans leur capitale, comme WH1, les chefs de faction de la mini-campagne.

Pourquoi (22.09.2026, 23 h 45 ; Charles : « je veux que ça soit à l'identique ») : `placer_chefs_capitale.py` avait
posé les 23 chefs à la case de leur capitale ; le jeu les a mis à deux cases, hors les murs. WH1 les avait DANS leur
capitale (lu dans son startpos : même case que la garnison). Le mécanisme, relevé dans les tables :
- WH1 : ces 23 chefs sont en (0, 0) ET liés à leur capitale par `start_pos_character_to_settlements` (23 lignes) ;
- CA dans WH3 fait pareil : 198 des 202 personnages liés à une colonie sont en (0, 0) ;
- `declare_campaign.py` n'avait pas porté cette table : nos chefs n'avaient aucun lien, d'où la case (1, 1) du
  coin de la carte, puis les deux cases de `placer_chefs_capitale.py`.

Ce script, sur le kit (sauvegarde dans `05-journal\\db-backups\\` avant écriture) :
1. remet (0, 0) aux chefs liés dans WH1 (annule `placer_chefs_capitale.py`) ;
2. ajoute les liens de WH1 à `start_pos_character_to_settlements.xml` (mêmes identifiants : WH1 et notre kit partagent
   ceux des personnages et des colonies ; vérifiés un par un).
Ensuite : recopier les deux tables dans `zz_startpos_db.pack` (synchroniser, filtre par personnage), régénérer le
startpos, le recopier dans le projet.

Usage :
    python garnisons_chefs.py            # à blanc
    python garnisons_chefs.py --apply
"""

import argparse
import os
import re
import shutil
import sys
import time
import uuid
from datetime import datetime

ATELIER = r"C:\TotalWar-CampaignMap"
DB1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
DB3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
CAMPAGNE = "wh_dlc05_wood_elves"
LIENS = "start_pos_character_to_settlements"


def lignes(db, table):
    t = open(os.path.join(db, table + ".xml"), encoding="utf-8", errors="replace").read()
    return t, [(m.start(), m.end(), dict(re.findall(r"<(\w+)>([^<]*)</\1>", m.group(1))))
               for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    _, f3 = lignes(DB3, "start_pos_factions")
    fac3 = {r["ID"]: r["faction"] for _, _, r in f3 if r.get("campaign") == CAMPAGNE}
    tc, c3 = lignes(DB3, "start_pos_characters")
    nos = {r["ID"]: (d, f, r) for d, f, r in c3 if r.get("faction") in fac3}
    _, s3 = lignes(DB3, "start_pos_settlements")
    colonies = {r["id"]: r.get("settlement_id") for _, _, r in s3}
    _, l1 = lignes(DB1, LIENS)
    tl, l3 = lignes(DB3, LIENS)
    deja = {r["character"] for _, _, r in l3}
    a_lier, a_remettre = [], []
    for _, _, r in l1:
        if r["character"] not in nos:
            continue
        if r["settlement"] not in colonies:
            print(f"  !! colonie {r['settlement']} absente de notre kit : lien ignoré")
            continue
        d, f, c = nos[r["character"]]
        print(f"  {fac3[c['faction']]:34s} ({c['startx']}, {c['starty']}) -> (0, 0) + {colonies[r['settlement']]}"
              f"{'  [lien déjà là]' if r['character'] in deja else ''}")
        if r["character"] not in deja:
            a_lier.append(r)
        if (c["startx"], c["starty"]) != ("0", "0"):
            a_remettre.append((d, f))
    print(f"{len(a_lier)} lien(s) à ajouter ; {len(a_remettre)} chef(s) à remettre en (0, 0)")
    if not a.apply or (not a_lier and not a_remettre):
        return 0
    dossier = os.path.join(ATELIER, "05-journal", "db-backups", datetime.now().strftime("%Y%m%d-%H%M%S") + "-garnisons")
    os.makedirs(dossier, exist_ok=True)
    for t in ("start_pos_characters", LIENS):
        shutil.copy2(os.path.join(DB3, t + ".xml"), dossier)
    # 1. (0, 0)
    morceaux, pos = [], 0
    for d, f in sorted(a_remettre):
        bloc = re.sub(r"<startx>[^<]*</startx>", "<startx>0</startx>", tc[d:f], count=1)
        bloc = re.sub(r"<starty>[^<]*</starty>", "<starty>0</starty>", bloc, count=1)
        morceaux += [tc[pos:d], bloc]
        pos = f
    morceaux.append(tc[pos:])
    with open(os.path.join(DB3, "start_pos_characters.xml"), "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(morceaux))
    # 2. liens, avant </dataroot>, au format des lignes du kit
    horodatage = int(time.time() * 1000)
    neuves = "".join(
        f'<{LIENS} record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{horodatage}" record_key="{r["character"]}">\n'
        f'<character>{r["character"]}</character>\n<settlement>{r["settlement"]}</settlement>\n'
        f'<unique>{r.get("unique", "0")}</unique>\n</{LIENS}>\n' for r in a_lier)
    fin = tl.rindex("</dataroot>")
    with open(os.path.join(DB3, LIENS + ".xml"), "w", encoding="utf-8", newline="") as fh:
        fh.write(tl[:fin] + neuves + tl[fin:])
    print(f"écrit : start_pos_characters.xml et {LIENS}.xml du kit ; sauvegarde dans {dossier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
