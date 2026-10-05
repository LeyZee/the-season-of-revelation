#!/usr/bin/env python3
"""
startpos_db_expanded.py - fabrique `zz_startpos_db_expanded.pack` : les tables de départ (`start_pos_*`) de la campagne
`saison_expanded`, lues dans le kit, au format du pack des tables de départ de la Saison.

Pourquoi (03.10.2026, pack d'Expanded ; Charles : « attaque tout ça ») : le jeu génère le startpos à partir des tables
d'un PACK (`zz_startpos_db.pack` pour la Saison, recette CLAUDE.md § 5), pas des XML du kit. La campagne d'Expanded a ses
lignes dans le kit (départ de la Saison recopié par `recopier_depart_expanded.py`, départ de l'Atlas par la session
Expanded) ; il lui faut son propre pack, à part : celui de la Saison n'est jamais touché.

Méthode : copie de `zz_startpos_db.pack` sous le nouveau nom (mêmes fichiers de table, mêmes versions de schéma), puis,
table par table, ses lignes remplacées par celles du kit pour `saison_expanded` (filtre et conversions de
`synchroniser_pack_startpos` : `lignes_kit`, `valeur`, textes laissés vides). Les noms des fichiers de table restent ceux
du pack copié (`*_wh_dlc05_wood_elves`) : le jeu ne lit que le contenu.

Usage :
    python startpos_db_expanded.py            # à blanc : comptes par table
    python startpos_db_expanded.py --apply    # écrit <jeu>\\data\\zz_startpos_db_expanded.pack (l'ancien rangé)
Prérequis : rpfm_server lancé.
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402
import synchroniser_pack_startpos as S                               # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
SOURCE = S.PACK
CIBLE = os.path.join(os.path.dirname(S.PACK), "zz_startpos_db_expanded.pack").replace("\\", "/")
CAMPAGNE = "saison_expanded"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.apply:
        if os.path.exists(CIBLE):
            rangement = os.path.join(ATELIER, "05-journal", "db-backups",
                                     time.strftime("%Y%m%d-%H%M%S") + "-zz-startpos-db-expanded")
            os.makedirs(rangement, exist_ok=True)
            shutil.move(CIBLE, rangement)
            print(f"ancien {os.path.basename(CIBLE)} rangé dans {rangement}")
        shutil.copy2(SOURCE, CIBLE)
    pack = CIBLE if a.apply else SOURCE
    sid = session()
    i = [1]

    def c(outil, args):
        i[0] += 1
        return text(call(sid, outil, args, i[0]))

    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    c("open_packfiles", {"paths": [pack]})
    chemins = sorted(set(re.findall(r'"(db/start_pos_[a-z_]+_tables/[^"]+)"', c("open_pack_info", {"pack_key": pack}))))
    total, vides = 0, []
    for chemin in chemins:
        table = chemin.split("/")[1][:-len("_tables")]
        brut = c("decode_packed_file", {"pack_key": pack, "path": chemin, "source": "PackFile"})
        try:
            h = json.loads(brut)["DBRFileInfo"][0]
        except (ValueError, KeyError):
            # table que rpfm ne décode pas : laissée telle que dans le pack de la Saison, à condition qu'elle n'ait aucune
            # ligne pour la campagne d'Expanded dans le kit
            try:
                n_kit = len(S.lignes_kit(table, CAMPAGNE))
            except SystemExit:
                n_kit = 0
            if n_kit:
                raise SystemExit(f"{table} : non décodée par rpfm ({brut[:150]}) et {n_kit} lignes dans le kit")
            print(f"  {table:52s}     - non décodée, laissée telle quelle (0 ligne au kit) : {brut[:80]}")
            vides.append(table)
            continue
        rep = json.loads(c("fields_processed", {"definition": json.dumps(h["table"]["definition"])}))
        champs = rep if isinstance(rep, list) else list(rep.values())[0]
        noms = [f["name"] for f in champs]
        types = {f["name"]: f["field_type"] for f in champs}
        try:
            kit = S.lignes_kit(table, CAMPAGNE)
        except SystemExit:
            # table sans lien à une campagne (start_pos_technologies : clé de faction, pas d'identifiant de départ ;
            # start_pos_past_events vide) : gardée telle que dans le pack de la Saison
            print(f"  {table:52s} {len(h['table']['table_data']):5d} lignes gardées (table sans campagne)")
            total += len(h["table"]["table_data"])
            continue
        manque = sorted({n for k in kit for n in noms if n not in k})
        if manque:
            raise SystemExit(f"{table} : colonnes du pack absentes du kit : {manque}")
        textes_vides = S.TEXTES_VIDES_PAR_TABLE.get(table, set())
        h["table"]["table_data"] = [[{types[n]: "" if n in textes_vides else S.valeur(types[n], k[n])} for n in noms]
                                    for k in kit]
        print(f"  {table:52s} {len(kit):5d} lignes")
        total += len(kit)
        if not kit:
            vides.append(table)
        if a.apply:
            res = c("save_packed_file_from_view", {"pack_key": pack, "path": chemin, "data": json.dumps({"DB": h})})
            if "Success" not in res:
                raise SystemExit(f"{table} : {res[:200]}")
    print(f"{total} lignes pour {CAMPAGNE} ; tables vides : {vides}")
    if a.apply:
        res = c("save_packfile", {"pack_key": pack})
        c("close_all_packs", {})
        if '"Error"' in res:
            raise SystemExit(f"pack non enregistré : {res[:200]}")
        print(f"écrit : {CIBLE} ({os.path.getsize(CIBLE)} octets) ; {SOURCE} inchangé")
    else:
        c("close_all_packs", {})
        print("à blanc ; relancer avec --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
