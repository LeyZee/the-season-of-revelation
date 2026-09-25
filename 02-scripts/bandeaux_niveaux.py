#!/usr/bin/env python3
"""
bandeaux_niveaux.py - hauteur des bandeaux (noms des colonies) par niveau de bâtiment, à la manière de CA.

Pourquoi (25.09.2026, 04 h 45 ; Charles : les noms des villes « cachés sur toutes les grosses colonies »). Enquête du
rendu (scratchpad `enquete_bandeaux`, mesure sur les triangles des modèles de CA) : la hauteur du bandeau est globale
(`_kv_ui_tweakers.campaign_citybar_height` = 1 u) et `campaign_map_settlements.citybar_height_offset` vaut 0 chez CA
partout ; l'outil de CA pour les modèles hauts est `settlement_nameplate_offsets_per_primary_building_levels` (décalage
par niveau du bâtiment principal : Cathay, Nagash, sylvaine majeure 5). Un bandeau de 3 u posé à 1 u du sol est caché de
15 à 77 % par nos grandes colonies. Décision de Charles (04 h 45) : « Niveaux de CA », en sachant que ces clés sont des
niveaux de CA (mod actif, les mêmes bandeaux sont relevés aux Empires) et que la ligne de CA de la sylvaine majeure 5
passe de 1 à 4,75. Valeur = hauteur du modèle au-dessus de laquelle le bandeau est libre (vue à 55°), moins 1 u ; port
et terre partagent la clé : la plus haute des deux.

Écrit aussi `citybar_height_offset` à 0 dans le kit et `map_spec.json` : voir `etiquettes_colonies.py`.

Usage :
    python bandeaux_niveaux.py            # contrôle
    python bandeaux_niveaux.py --apply    # écrit (sauvegarde d'abord dans 05-journal\\db-backups\\)
"""

import argparse
import os
import re
import shutil
import sys
import time
import uuid

DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
ATELIER = r"C:\TotalWar-CampaignMap"
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "db-backups")
TABLE = "settlement_nameplate_offsets_per_primary_building_levels"

BANDEAUX = {
    "wh_main_brt_settlement_major_1": 0.25,
    "wh_main_brt_settlement_major_2": 0.75,
    "wh_main_brt_settlement_major_3": 1.75,     # port 1,75 ; terre 1,0
    "wh_main_brt_settlement_major_4": 1.5,
    "wh_main_brt_settlement_major_5": 4,
    "wh_main_brt_settlement_minor_3": 0.25,
    "wh_main_vmp_settlement_major_2": 0.5,
    "wh_main_vmp_settlement_major_3": 1.25,     # Mousillon (port)
    "wh_main_vmp_settlement_major_4": 2,
    "wh_main_vmp_settlement_major_5": 2.5,
    "wh_dlc05_wef_settlement_major_main_1": 1.5,
    "wh_dlc05_wef_settlement_major_main_2": 1.75,
    "wh_dlc05_wef_settlement_major_main_3": 3.25,
    "wh_dlc05_wef_settlement_major_main_4": 3.5,
    "wh_dlc05_wef_settlement_major_main_5": 4.75,   # ligne de CA (1) : accord de Charles
    "wh_dlc05_wef_oak_of_ages_1": 4.75,
    "wh_main_dwf_settlement_minor_2": 0.75,
    "wh_main_dwf_settlement_minor_3": 1,
}
LIGNE_DE_CA = {"wh_dlc05_wef_settlement_major_main_5": "1"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    niveaux = open(os.path.join(DB, "building_levels.xml"), encoding="utf-8").read()
    absents = [k for k in BANDEAUX if f"<level_name>{k}</level_name>" not in niveaux]
    if absents:
        raise SystemExit(f"niveaux de bâtiment absents du kit : {absents}")

    chemin = os.path.join(DB, TABLE + ".xml")
    t = open(chemin, encoding="utf-8").read()
    horodatage = str(int(time.time() * 1000))
    ajouts, changes = [], 0
    for cle, v in BANDEAUX.items():
        blocs = [m for m in re.finditer(rf"<{TABLE}\b[^>]*>.*?</{TABLE}>", t, re.S)
                 if f"<building_level>{cle}</building_level>" in m.group(0)]
        if len(blocs) > 1:
            raise SystemExit(f"{cle} : {len(blocs)} lignes")
        if blocs:
            m = blocs[0]
            ancien = re.search(r"<nameplate_offset>([^<]*)</nameplate_offset>", m.group(0)).group(1)
            if cle not in LIGNE_DE_CA and ancien != str(v):
                print(f"  {cle} : déjà présente à {ancien} (ligne à nous d'un passage précédent)")
            if float(ancien) != float(v):
                neuf = m.group(0).replace(f"<nameplate_offset>{ancien}</nameplate_offset>",
                                          f"<nameplate_offset>{v}</nameplate_offset>")
                t = t[:m.start()] + neuf + t[m.end():]
                changes += 1
                print(f"  {cle} : {ancien} -> {v}")
            continue
        ajouts.append(f'<{TABLE} record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{horodatage}" record_key="{cle}">\n'
                      f"<building_level>{cle}</building_level>\n<nameplate_offset>{v}</nameplate_offset>\n</{TABLE}>\n")
        print(f"  {cle} : ajoutée à {v}")
    print(f"{len(ajouts)} ligne(s) ajoutée(s), {changes} changée(s)")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply")
        return 0
    if not ajouts and not changes:
        print("rien à écrire")
        return 0
    t = t.replace("</dataroot>", "".join(ajouts) + "</dataroot>")
    dest = os.path.join(SAUVEGARDES, time.strftime("%Y%m%d-%H%M%S") + "-bandeaux-niveaux")
    os.makedirs(dest)
    shutil.copy(chemin, dest)
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(t)
    print(f"écrit ; sauvegarde : {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
