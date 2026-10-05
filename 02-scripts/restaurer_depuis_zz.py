#!/usr/bin/env python3
"""
restaurer_depuis_zz.py - remet dans le kit (raw_data\\db) les lignes de départ de la Saison que `zz_startpos_db.pack` porte
encore et que le kit a perdues.

Pourquoi (03.10.2026, erreur 326) : la mise à jour du 27.09 a vidé `raw_data\\db` (erreur 290) ; la restauration de la session
« Lakemen » a rejoué les lots numérotés et les dernières copies des tables, mais pas les lignes écrites par les outils à part
(`ajouter_seigneurs_jouables.py`, `seigneur_soeurs.py`, `seigneurs_drycha_kemmler_grom.py`, `declare_campaign.py`) :
7 relations diplomatiques, 10 options de départ des seigneurs (écran de sélection), 1 trait, 1 calendrier. Le pack des
tables de départ les a gardées (c'est lui qui sert à générer le startpos) : on les relit dans le pack (rpfm) et on les
ajoute au kit sur le gabarit d'une ligne de la même table, la clé d'enregistrement recomposée par les valeurs.
Rien n'est retiré ni modifié ; une ligne déjà dans le kit est laissée.

Usage :
    python restaurer_depuis_zz.py            # à blanc
    python restaurer_depuis_zz.py --apply    # préavis du kit d'abord ; sauvegarde dans 05-journal\\db-backups\\
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from donnees_campagne import TableKit                                 # noqa: E402
from rpfm_mcp import session, call, text                              # noqa: E402
from synchroniser_pack_startpos import PACK, lignes_kit               # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
CAMPAGNE = "wh_dlc05_wood_elves"
TABLES = {"start_pos_diplomacy": "key", "start_pos_starting_general_options": "id",
          "start_pos_character_traits": "id", "start_pos_calendars": "campaign"}


def en_texte(cell):
    v = list(cell.values())[0] if isinstance(cell, dict) else cell
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sid = session()
    i = [1]

    def c(outil, args):
        i[0] += 1
        return text(call(sid, outil, args, i[0]))

    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    c("open_packfiles", {"paths": [PACK]})
    info = c("open_pack_info", {"pack_key": PACK})
    tables, total = {}, 0
    for nom, cle in TABLES.items():
        chemins = sorted(set(re.findall(rf'"(db/{nom}_tables/[^"]+)"', info)))
        if len(chemins) != 1:
            raise SystemExit(f"{nom} : {len(chemins)} fichier(s) dans le pack")
        h = json.loads(c("decode_packed_file", {"pack_key": PACK, "path": chemins[0], "source": "PackFile"}))["DBRFileInfo"][0]
        rep = json.loads(c("fields_processed", {"definition": json.dumps(h["table"]["definition"])}))
        noms = [f["name"] for f in (rep if isinstance(rep, list) else list(rep.values())[0])]
        kit = {str(k.get(cle, "")) for k in lignes_kit(nom, CAMPAGNE)}
        t = TableKit(nom)
        modele = t.lignes[0][0]
        for ligne in h["table"]["table_data"]:
            valeurs = {n: en_texte(v) for n, v in zip(noms, ligne)}
            if valeurs[cle] in kit:
                continue
            valeurs.setdefault("unique", "0")
            colonnes = set(t.valeurs(dict(t.lignes)[modele]))
            valeurs = {k: v for k, v in valeurs.items() if k in colonnes}
            if t.ajouter_sur_modele(modele, valeurs):
                total += 1
                print(f"  {nom} : + {valeurs}")
        tables[nom] = t
    c("close_all_packs", {})
    print(f"{total} ligne(s) à remettre dans le kit")
    if not a.apply:
        print("à blanc ; relancer avec --apply (préavis du kit d'abord)")
        return 0
    dossier = os.path.join(ATELIER, "05-journal", "db-backups", time.strftime("%Y%m%d-%H%M%S") + "-restaurer-depuis-zz")
    n = sum(t.ecrire(dossier) for t in tables.values())
    print(f"écrit : {n} ; sauvegarde {dossier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
