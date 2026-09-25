#!/usr/bin/env python3
"""
declare_campaign.py - porte les huit tables `start_pos_*` d'une mini-campagne de Warhammer 1 dans
la base de l'Assembly Kit de Warhammer 3, en traduisant les clés par `correspondances.json`.

Ces tables sont ce que `build_starpos` (RPFM) consomme pour produire le `startpos.esf` d'une
campagne. Elles se tiennent par des identifiants numériques : une faction porte un numéro, une
région cite ce numéro, une colonie cite la région, un personnage cite la faction, une unité cite
le personnage. Le script suit ce graphe depuis les factions de la campagne demandée.

Traductions appliquées, toutes lues dans `correspondances.json` (produit par
`build_correspondances.py`) :

- clés de faction (`wh_dlc05_wef_mini_argwylon` -> `wh_dlc05_wef_argwylon`) ;
- sous-types de personnage (`dlc05_wef_orion` -> `wh_dlc05_wef_orion`) ;
- bâtiments de colonie (`wef_settlement_major_1` -> `wef_settlement_major_main_1`) ;
- gabarits de slots, par gabarit (`gabarits_de_slots`) ou, pour une région qui existe aussi dans
  l'Empire Immortel, par région (`gabarits_de_slots_par_region`, prioritaire). Une ligne dont le
  gabarit serait marqué « à ignorer » est écartée ; il n'y en a plus depuis le 21.09.2026 : les
  écarter laissait les 18 régions d'Athel Loren **sans emplacement**, et le jeu plantait au
  chargement de la campagne (il exige un emplacement `primary` par colonie).

Colonnes : le script écrit dans l'ordre du schéma de Warhammer 3. Une colonne que Warhammer 1
avait et que Warhammer 3 n'a plus est abandonnée ; une colonne nouvelle reçoit la valeur par
défaut indiquée dans DEFAULTS, choisie d'après ce que contiennent les lignes livrées par CA.

Les identifiants numériques de Warhammer 1 sont conservés tels quels : aucun n'entre en collision
avec ceux de Warhammer 3 (vérifié table par table le 20.09.2026).

Usage :
    python declare_campaign.py --campaign wh_dlc05_wood_elves
        --correspondances 04-projets/saison-des-revelations/correspondances.json
        --asskit "<kit WH3>" [--asskit-wh1 "<kit WH1>"] [--tables t1,t2] [--apply] [--undo]

`--tables` limite l'écriture à ces tables : les autres ont pu être corrigées depuis par d'autres
scripts, et une ligne retirée exprès y serait sinon remise.

Sans --apply : essai à blanc, rien n'est écrit. Avant toute écriture, chaque XML touché est copié
dans `05-journal\\db-backups\\<date>`.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from declare_map import Table, plain, approved                      # noqa: E402
from groupes_ia import Choix                                         # noqa: E402

WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit"
WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
ATELIER = r"C:\TotalWar-CampaignMap"

# Colonnes que Warhammer 3 ajoute, avec la valeur que portent ses propres lignes.
DEFAULTS = {
    "start_pos_factions": {"faction_potential": "minor"},
    "start_pos_settlements": {"settlement_type": "", "primary_display_building": ""},
    "start_pos_starting_general_options": {"exclude_other_options": "0"},
}

TABLES = ["start_pos_factions", "start_pos_regions", "start_pos_settlements",
          "start_pos_characters", "start_pos_land_units", "start_pos_region_slot_templates",
          "start_pos_calendars", "start_pos_starting_general_options",
          # Ajoutée le 20.09.2026 : le vidage mémoire du jeu montre qu'il ouvre
          # `db\start_pos_diplomacy` pendant la génération du startpos, et la mini-campagne en a
          # quatre lignes dans Warhammer 1 (trois états de guerre et un pacte de non-agression)
          # que nous n'avions jamais portées. Ce n'est pas la cause du plantage — le prologue de
          # CA n'a aucune ligne de diplomatie et fonctionne — mais c'est de la fidélité rendue.
          "start_pos_diplomacy"]


def rows(kit, table):
    path = os.path.join(kit, "raw_data", "db", table + ".xml")
    if not os.path.exists(path):
        return []
    out = []
    for r in ET.parse(path).getroot():
        if r.tag == "edit_uuid":
            continue
        d = {"_key": r.get("record_key", "")}
        for c in r:
            d[c.tag] = (c.text or "").strip()
        out.append(d)
    return out


def schema(kit, table):
    """Colonnes de la table, dans l'ordre du schéma, et celles qui sont du texte localisé."""
    path = os.path.join(kit, "raw_data", "db", "TWaD_" + table + ".xml")
    text = open(path, encoding="utf-8-sig", errors="replace").read()
    cols, localised = [], set()
    for m in re.finditer(r"<field>(.*?)</field>", text, re.S):
        block = m.group(1)
        name = re.search(r"<name>(.*?)</name>", block).group(1)
        cols.append(name)
        if "<is_localised>1</is_localised>" in block or "<field_type>loc" in block:
            localised.add(name)
    return cols, localised


def localised_fields(kit, table):
    """Repère les colonnes de texte localisé sur les lignes déjà présentes (attribut state)."""
    path = os.path.join(kit, "raw_data", "db", table + ".xml")
    found = set()
    if not os.path.exists(path):
        return found
    for r in ET.parse(path).getroot():
        if r.tag == "edit_uuid":
            continue
        for c in r:
            if c.get("state"):
                found.add(c.tag)
        if found:
            break
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--correspondances", required=True)
    ap.add_argument("--asskit", default=WH3)
    ap.add_argument("--asskit-wh1", default=WH1)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--backup-dir", default=None)
    ap.add_argument("--tables", default=None, help="n'écrire que ces tables (séparées par des virgules)")
    ap.add_argument("--maj", action="store_true",
                    help="réécrire aussi les lignes déjà présentes dont le contenu a changé (même clé)")
    ap.add_argument("--sample", type=int, default=0, help="montrer N lignes produites par table")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.tables:
        inconnues = [t for t in a.tables.split(",") if t not in TABLES]
        if inconnues:
            print("tables inconnues :", ", ".join(inconnues), "; connues :", ", ".join(TABLES))
            return 2

    corr = json.load(open(a.correspondances, encoding="utf-8"))
    fac_map = {k: v["wh3"] for k, v in corr["factions"].items()}
    sub_map = {k: v["wh3"] for k, v in corr["sous_types_de_personnages"].items()}
    bld_map = {k: v["wh3"] for k, v in corr["batiments_de_colonie"].items()}
    slot_map = {k: v["wh3"] for k, v in corr["gabarits_de_slots"].items()}
    slot_ignored = {k for k, v in corr["gabarits_de_slots"].items() if v["règle"].startswith("à ignorer")}
    slot_region = corr.get("gabarits_de_slots_par_region", {})

    # --- le graphe des lignes de Warhammer 1 --------------------------------------------------
    w1 = {t: rows(a.asskit_wh1, t) for t in TABLES}
    factions = [r for r in w1["start_pos_factions"] if r.get("campaign") == a.campaign]
    fac_ids = {r["_key"] for r in factions}
    regions = [r for r in w1["start_pos_regions"] if r.get("campaign") == a.campaign]
    reg_ids = {r.get("id", r["_key"]) for r in regions}
    settlements = [r for r in w1["start_pos_settlements"] if r.get("region") in reg_ids]
    characters = [r for r in w1["start_pos_characters"] if r.get("faction") in fac_ids]
    char_ids = {r.get("id", r["_key"]) for r in characters}
    units = [r for r in w1["start_pos_land_units"]
             if r.get("general") in char_ids or r.get("faction") in fac_ids]
    slots = [r for r in w1["start_pos_region_slot_templates"] if r.get("campaign") == a.campaign]
    calendars = [r for r in w1["start_pos_calendars"] if r.get("campaign") == a.campaign]
    generals = [r for r in w1["start_pos_starting_general_options"] if r.get("faction") in fac_ids]
    # la diplomatie n'a pas de colonne `campaign` : une ligne est à nous si ses deux factions
    # appartiennent à notre campagne
    diplomatie = [r for r in w1["start_pos_diplomacy"]
                  if r.get("faction1") in fac_ids and r.get("faction2") in fac_ids]
    source = {"start_pos_factions": factions, "start_pos_regions": regions,
              "start_pos_settlements": settlements, "start_pos_characters": characters,
              "start_pos_land_units": units, "start_pos_region_slot_templates": slots,
              "start_pos_calendars": calendars, "start_pos_starting_general_options": generals,
              "start_pos_diplomacy": diplomatie}

    # --- traduction ---------------------------------------------------------------------------
    unresolved = []

    # Warhammer 1 accepte le sous-type `default` (il est dans ses 125 `agent_subtypes`) ; Warhammer 3
    # ne le connaît pas (613 clés, pas de `default`) et exige un sous-type réel. Un personnage qui
    # garde `default` fait lire un enregistrement nul au jeu pendant la génération du startpos :
    # plantage 0xC0000005 à `Warhammer3.exe+0x234ACF8`, `mov r8d,[rax+0x24]` avec rax = 0, dans le
    # code qui écrit le bloc du chef de faction (20.09.2026, journal phase-2-startpos-temoin.md).
    # On rend donc à chaque `default` le seigneur générique de sa culture.
    # Clés vérifiées une à une dans `agent_subtypes.xml` du kit WH3 le 20.09.2026 : les sept
    # existent. (`wh_main_vmp_vampire` et `wh_main_emp_general`, essayés d'abord, n'existent pas.)
    SEIGNEUR_GENERIQUE = {"brt": "wh_main_brt_lord", "dwf": "wh_main_dwf_lord",
                          "wef": "wh_dlc05_wef_glade_lord", "grn": "wh_main_grn_orc_warboss",
                          "vmp": "wh_main_vmp_lord", "emp": "wh_main_emp_captain",
                          "bst": "wh_dlc03_bst_beastlord"}
    # id de faction Warhammer 1 -> clé de faction Warhammer 3, pour retrouver la culture
    faction_de_id = {}
    for r in factions:
        cle_wh1 = r.get("faction", "")
        faction_de_id[r["_key"]] = fac_map.get(cle_wh1) or cle_wh1

    def culture(cle_faction):
        for morceau in cle_faction.split("_"):
            if morceau in SEIGNEUR_GENERIQUE:
                return morceau
        return None

    # Les groupes de personnalite de l'IA ont tous ete renommes entre les deux jeux : Warhammer 3
    # les prefixe `wh3_combi_personality_group_`. Une valeur de Warhammer 1 fait **refuser le pack
    # entier** par le jeu, qui l'ecrit dans `crash_report\bad_mods_report.txt` :
    #     first_invalid_database_record : 2120137457
    #     first_invalid_database_table  : start_pos_factions_tables
    # (20.09.2026, 22 h 44). Correspondances verifiees une a une dans `cai_personality_groups.xml`
    # du kit WH3 (222 cles).
    GROUPES_IA = {
        "wh_dlc05_mini_group_wood_elves_rest":   "wh3_combi_personality_group_woodelf_minor",
        "wh_dlc05_mini_group_wood_elves_durthu": "wh3_combi_personality_group_woodelf_durthu",
        "wh_dlc05_mini_group_wood_elves_orion":  "wh3_combi_personality_group_woodelf_orion",
        "wh_group_greenskins_waaagh":            "wh2_group_greenskins_waaagh",
        "wh_dlc03_group_beastmen_default":       "wh3_combi_personality_group_beastmen_minor",
        "wh_dlc03_group_beastmen_waaagh":        "wh3_combi_personality_group_beastmen_brayherd",
        "wh_group_vampires_default":             "wh3_combi_personality_group_vampire_minor",
        "wh_group_dwarfs_default":               "wh3_combi_personality_group_dwarf_minor",
    }

    choix_ia = Choix()

    def translate(table, col, value, src=None):
        if col == "cai_personality_group":
            # Règle de CA (groupes_ia.py, erreur 57) : le groupe que la faction a dans l'Empire
            # Immortel, sinon le groupe mineur de sa culture ; jamais un groupe sans personnalité.
            cle = faction_de_id.get((src or {}).get("_key", ""), "")
            return choix_ia.groupe(cle, GROUPES_IA.get(value, value))[0]
        if table == "start_pos_region_slot_templates" and col == "slot_template":
            impose = slot_region.get((src or {}).get("region", ""), {}).get((src or {}).get("slot_type", ""))
            if impose:
                return impose
        if col == "subtype" and value == "default":
            cle = faction_de_id.get((src or {}).get("faction", ""), "")
            c = culture(cle)
            if c:
                return SEIGNEUR_GENERIQUE[c]
            unresolved.append((table, col, f"default (faction {cle or '?'} : culture inconnue)"))
            return value
        return _translate(table, col, value)

    def _translate(table, col, value):
        if not value:
            return value
        if value in fac_map and (col in ("faction", "rebel_faction", "alternative_rebel_faction",
                                         "owning_faction", "political_party") or table == "start_pos_factions"):
            return fac_map[value] or value
        if col == "subtype" and value in sub_map:
            return sub_map[value] or value
        if (col.startswith("building") or col in ("primary_building", "port_building")) and value in bld_map:
            return bld_map[value] or value
        if col == "slot_template" and value in slot_map:
            return slot_map[value] or value
        if value.startswith(("wh_dlc05_", "wh_dlc03_")) and value in fac_map:
            return fac_map[value] or value
        return value

    planned = {}
    for table in TABLES:
        cols, _ = schema(a.asskit, table)
        loc = localised_fields(a.asskit, table)
        defaults = DEFAULTS.get(table, {})
        out = []
        for src in source[table]:
            if table == "start_pos_region_slot_templates" and src.get("slot_template") in slot_ignored:
                continue
            fields = []
            for col in cols:
                value = src.get(col, defaults.get(col, ""))
                value = translate(table, col, value, src)
                if value and value.startswith(("wh_dlc05_brt_mini", "wh_dlc05_wef_mini", "wh_dlc05_grn_mini",
                                               "wh_dlc05_bst_mini", "wh_dlc05_dwf_mini", "dlc05_", "dlc07_")):
                    unresolved.append((table, col, value))
                fields.append(approved(col, value) if col in loc else plain(col, value))
            out.append((src["_key"], fields))
        planned[table] = out

    if unresolved:
        print("ATTENTION, des clés n'ont pas été traduites :")
        for t, c, v in unresolved[:10]:
            print(f"   {t}.{c} = {v}")
        print(f"   ({len(unresolved)} au total) — corriger correspondances.json avant d'écrire.")
        return 2

    if a.sample:
        for table in TABLES:
            if not planned[table]:
                continue
            print(f"\n=== {table} (2 premières colonnes de chaque ligne montrée)")
            for key, fields in planned[table][:a.sample]:
                shown = [f for f in fields if ">" in f and f.split(">", 1)[1].split("<", 1)[0]]
                print(f"   {key[:40]:42s} " + " ".join(s[1:s.index('>')] + "=" + s.split(">", 1)[1].split("<", 1)[0]
                                                       for s in shown[:6]))

    # --- écriture -----------------------------------------------------------------------------
    backup = a.backup_dir or os.path.join(ATELIER, "05-journal", "db-backups",
                                          datetime.now().strftime("%Y%m%d-%H%M%S"))
    total = 0
    for table in TABLES:
        if a.tables and table not in a.tables.split(","):
            continue
        t = Table(a.asskit, table)
        for key, fields in planned[table]:
            if a.undo:
                t.remove(key)
            elif a.maj and key in t.keys:
                # la clé d'une ligne de WH1 ne change pas quand sa traduction change (gabarit
                # d'emplacement, 21.09.2026) : sans --maj, la ligne corrigée serait « déjà présente »
                t.replace(key, fields)
            else:
                t.add(key, fields)
        n = len(t.removed if a.undo else t.added)
        total += n + len(t.updated)
        verb = "retiré" if a.undo else "ajouté"
        print(f"  {table:36s} {verb} {n:5d}  mis à jour {len(t.updated):5d}  déjà présent {len(t.skipped):5d}")
        for k in t.updated[:40]:
            print(f"      mis à jour : {k}")
        if a.apply and (n or t.updated):
            t.save(backup)

    if a.apply:
        print(f"\nÉcrit : {total} lignes. Sauvegardes des XML d'origine dans {backup}")
    else:
        print(f"\nEssai à blanc : {total} lignes seraient écrites. Relancer avec --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
