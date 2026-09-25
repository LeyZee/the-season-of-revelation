#!/usr/bin/env python3
"""
etiquettes_colonies.py - hauteur des étiquettes (citybar) des colonies de la Saison, reprise de WH1.

Pourquoi (24.09.2026, 22 h 50 ; Charles : les noms des villes « en retrait derrière l'icône 3D », Chêne des Âges,
Mousillon). Enquête du rendu : dans le kit de WH1, 13 des 57 colonies de la Saison avaient
`campaign_map_settlements.citybar_height_offset` = 1 (les 194 autres de WH1 à 0) ; chez nous 56 à 0 et le Chêne à 3
(`etiquette_chene.py`, 23.09), encore dans la couronne (modèle jusqu'à ~6,7 u). Le champ est lu en jeu (pas de
retraitement du startpos) : le pack suffit.

Ce script remplace `etiquette_chene.py` : les 13 valeurs de WH1, le Chêne à 7 (au-dessus de sa couronne) ; il les écrit
dans le kit ET dans `map_spec.json` (sinon `declare_map.py` les remettrait à 0).

Usage :
    python etiquettes_colonies.py            # contrôle (ce qui changerait)
    python etiquettes_colonies.py --apply    # écrit (sauvegarde d'abord dans 05-journal\\db-backups\\)
"""

import argparse
import json
import os
import re
import shutil
import sys
import time

DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
ATELIER = r"C:\TotalWar-CampaignMap"
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "db-backups")
SPEC = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "map_spec.json")
TABLE = "campaign_map_settlements"

# 25.09.2026, 04 h 50 (« prends les valeurs de Warhammer 3 », Charles ; enquête des bandeaux du rendu) : 0 partout, comme
# les 833 lignes de CA ; la hauteur par modèle passe par les niveaux de bâtiment (`bandeaux_niveaux.py`). Anciennes
# valeurs (kit de WH1 : 1 pour ces 12 colonies ; le Chêne à 7) : sauvegardes `db-backups\*-etiquettes-colonies`.
HAUTEURS = {r: 0 for r in (
    "wh_dlc05_oak_of_ages",
    "wh_dlc05_talsyn_tal_eth_ayr",
    "wh_dlc05_torgovann_vauls_anvil",
    "wh_dlc05_argwylon_waterfall_palace",
    "wh_dlc05_fyr_darric_threllock",
    "wh_dlc05_tirsyth_glade_of_eternal_moonlight",
    "wh_dlc05_mousillon_yremy",
    "wh_dlc05_gisoreux_gisoreux",
    "wh_dlc05_grey_mountains_2_blackstone_post",
    "wh_dlc05_grey_mountains_2_karak_tzor",
    "wh_dlc05_grey_mountains_2_karak_ziflin",
    "wh_dlc05_grey_mountains_axe_bite_pass",
    "wh_dlc05_grey_mountains_gragrut_pass",
)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    chemin = os.path.join(DB, TABLE + ".xml")
    t = open(chemin, encoding="utf-8").read()
    remplacements = []
    for region, h in HAUTEURS.items():
        cle = f"settlement:{region}"
        blocs = [m for m in re.finditer(rf"<{TABLE}\b[^>]*>.*?</{TABLE}>", t, re.S)
                 if f"<settlement_id>{cle}</settlement_id>" in m.group(0)]
        if len(blocs) != 1:
            raise SystemExit(f"kit : {cle} : {len(blocs)} ligne(s) au lieu d'une")
        m = blocs[0]
        ancien = re.search(r"<citybar_height_offset>([^<]*)</citybar_height_offset>", m.group(0))
        print(f"kit  {cle} : {ancien.group(1)} -> {h}")
        if ancien.group(1) != str(h):
            neuf = m.group(0).replace(ancien.group(0), f"<citybar_height_offset>{h}</citybar_height_offset>")
            remplacements.append((m.start(), m.end(), neuf))

    brut = open(SPEC, encoding="utf-8").read()
    spec = json.loads(brut)
    par_region = {s["region"]: s for s in spec.get("settlements", [])}
    manquantes = [r for r in HAUTEURS if r not in par_region]
    if manquantes:
        raise SystemExit(f"map_spec : colonies absentes : {manquantes}")
    for region, h in HAUTEURS.items():
        print(f"spec {region} : {par_region[region].get('citybar_height_offset', 0)} -> {h}")
        par_region[region]["citybar_height_offset"] = h
    # même mise en forme que le fichier (retrait d'un espace, accents tels quels) : vérifié par le nombre de lignes changées
    neuf_spec = json.dumps(spec, indent=1, ensure_ascii=False) + ("\n" if brut.endswith("\n") else "")
    avant, apres = brut.splitlines(), neuf_spec.splitlines()
    ajoutees = len(apres) - len(avant)
    print(f"map_spec : {ajoutees} ligne(s) ajoutée(s) (au plus {len(HAUTEURS)})")
    # contrôle : sans les lignes citybar et les virgules, le fichier réécrit doit être identique à l'ancien
    def norme(lignes):
        return [l.rstrip(",") for l in lignes if "citybar_height_offset" not in l]
    if norme(avant) != norme(apres):
        raise SystemExit("map_spec : la réécriture change autre chose que les hauteurs (mise en forme différente) ; rien écrit")

    if not a.apply:
        print(f"contrôle fait ({len(remplacements)} ligne(s) du kit à changer) ; relancer avec --apply")
        return 0
    dest = os.path.join(SAUVEGARDES, time.strftime("%Y%m%d-%H%M%S") + "-etiquettes-colonies")
    os.makedirs(dest)
    shutil.copy(chemin, dest)
    shutil.copy(SPEC, dest)
    for debut, fin, neuf in sorted(remplacements, reverse=True):
        t = t[:debut] + neuf + t[fin:]
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(t)
    with open(SPEC, "w", encoding="utf-8", newline="") as f:
        f.write(neuf_spec)
    print(f"écrit ; sauvegarde : {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
