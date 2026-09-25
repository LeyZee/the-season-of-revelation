#!/usr/bin/env python3
"""
valider_start_pos.py - verifier nos tables `start_pos_*` contre les cles que Warhammer 3 connait.

Pourquoi : le 20.09.2026 a 22 h 44, le jeu a refuse notre pack de tables de depart et a ecrit
`crash_report\\bad_mods_report.txt` :

    first_invalid_database_record : 2120137457
    first_invalid_database_table  : start_pos_factions_tables
    first_invalid_packfile        : zz_startpos_db.pack

Il ne nomme que **le premier** enregistrement fautif, et il faut relancer le jeu pour connaitre le
suivant. Ce script les trouve tous d'un coup, sans lancer le jeu.

Methode : le schema de chaque table, tel que RPFM le rend (`decode_packed_file` ->
`definition.fields`), porte pour chaque colonne un `is_reference` = `[table, colonne]`. On lit les
valeurs valides dans `raw_data\\db\\<table>.xml` du kit Warhammer 3 et on signale toute cellule qui
n'en fait pas partie. (L'outil `get_reference_data_from_definition` de RPFM, lui, rend une reponse
vide : ne pas compter dessus.)

Usage :
    python valider_start_pos.py
    python valider_start_pos.py --pack "<chemin.pack>" [--table start_pos_characters]
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402

AK = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/assembly_kit/raw_data/db"
PACK = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data/zz_startpos_db.pack"
_cache = {}


def valeurs(table, colonne):
    """Les valeurs que le kit connait pour `<table>.<colonne>`, ou None si la table manque."""
    if (table, colonne) in _cache:
        return _cache[(table, colonne)]
    p = os.path.join(AK, table + ".xml")
    out = None
    if os.path.exists(p):
        out = set()
        for r in ET.parse(p).getroot():
            if r.tag == "edit_uuid":
                continue
            e = r.find(colonne)
            if e is not None and e.text:
                out.add(e.text.strip())
    _cache[(table, colonne)] = out
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default=PACK)
    ap.add_argument("--table", default=None)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    sid = session()
    i = [1]

    def c(tool, args):
        i[0] += 1
        return text(call(sid, tool, args, i[0]))

    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": True})
    c("open_packfiles", {"paths": [a.pack]})
    d = json.loads(c("get_packed_files_names_starting_with_path_from_all_sources",
                     {"pack_key": a.pack, "path": json.dumps({"Folder": "db"})}))
    d = d.get("HashMapDataSourceHashSetContainerPath", {})
    chemins = sorted(v for it in d.get("PackFile", []) for v in (it.values() if isinstance(it, dict) else [it]))
    if a.table:
        chemins = [p for p in chemins if a.table in p]
    print(f"{len(chemins)} tables dans {os.path.basename(a.pack)}\n")

    lignes_vues = fautes_total = 0
    for chemin in chemins:
        brut = c("decode_packed_file", {"pack_key": a.pack, "path": chemin, "source": "PackFile"})
        try:
            h = json.loads(brut)["DBRFileInfo"][0]
        except (ValueError, KeyError):
            # RPFM ne reconnait pas ce fichier comme une table (rend `"Unknown"`)
            print(f"  {chemin.split('/')[1]:44s} non reconnu comme table, ignore")
            continue
        definition = h["table"]["definition"]
        refs = {f["name"]: tuple(f["is_reference"][:2])
                for f in definition["fields"] if f.get("is_reference")}
        rep = json.loads(c("fields_processed", {"definition": json.dumps(definition)}))
        noms = [f["name"] for f in (rep if isinstance(rep, list) else list(rep.values())[0])]
        donnees = h["table"]["table_data"]
        lignes_vues += len(donnees)

        fautes = {}
        manquantes = set()
        for n, ligne in enumerate(donnees):
            for j, cell in enumerate(ligne):
                col = noms[j] if j < len(noms) else None
                if col not in refs:
                    continue
                t, k = refs[col]
                valides = valeurs(t, k)
                v = list(cell.values())[0] if isinstance(cell, dict) else cell
                if valides is None:
                    manquantes.add((col, t))
                    continue
                if isinstance(v, str) and v and v not in valides:
                    fautes.setdefault((col, f"{t}.{k}", v), []).append(n)

        nom = chemin.split("/")[1]
        if fautes or manquantes:
            fautes_total += sum(len(v) for v in fautes.values())
            print(f"  {nom:44s} {len(donnees):4d} lignes")
            for (col, ou, v), n in sorted(fautes.items(), key=lambda x: -len(x[1])):
                print(f"       {col:30s} = {v!r:48s} x{len(n):<3d} inconnu de {ou}")
            for col, t in sorted(manquantes):
                print(f"       {col:30s} -> table {t} absente du kit (non verifiable)")
        else:
            print(f"  {nom:44s} {len(donnees):4d} lignes, rien a signaler")

    print(f"\n{lignes_vues} lignes verifiees, {fautes_total} cellules a corriger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
