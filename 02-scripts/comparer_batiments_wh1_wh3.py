#!/usr/bin/env python3
"""
comparer_batiments_wh1_wh3.py - compare, région par région, les bâtiments qu'une colonie peut
construire dans la mini-campagne de Warhammer 1 et dans notre portage pour Warhammer 3.

Pourquoi (21.09.2026, erreur 60) : le jeu chargeait la campagne alors que 14 régions d'Athel Loren
n'offraient aux elfes que des avant-postes. Un gabarit d'emplacement se valide par ce qu'il permet,
pas par le fait que le jeu charge.

Ce qui est comparé : pour chaque région, l'union des chaînes permises par tous ses emplacements.
- WH1 : `start_pos_region_slot_templates` -> `slot_template_to_building_superchain_junctions` ->
  `building_chains.building_superchain` ;
- WH3 (kit, donc nos lignes comprises) : `start_pos_region_slot_templates` ->
  `slot_template_permitted_building_chains` (jeu de chaînes, chaîne ou superchaîne) ->
  `building_chain_sets` (parent) et `building_chain_set_items` (ajouts et retraits).
Seules comptent les chaînes connues des deux jeux et qui ont au moins un niveau dans WH3 ; les
chaînes mortes de WH3 sont listées à part.

Règles de WH3 (décision de Charles, 21.09.2026) : les chaînes se classent en trois familles.
- **abandonnées par CA** : aucun gabarit de WH3 ne les permet (ruines de WH1, avant-postes de
  Norsca...) ; listées pour information ;
- **monuments** : chaînes que WH3 ne range que dans des jeux `*landmark*` ; WH3 les attache à une
  région ; le rapport dit où chacune se construit sur notre carte, et lesquelles nulle part ;
- **bâtiments de base** : tout le reste. Une région qui en perd un est une erreur.

Code de sortie 1 si une région perd un bâtiment de base que WH1 lui permettait.

Usage :
    python comparer_batiments_wh1_wh3.py [--campagne wh_dlc05_wood_elves] [--detail] [--region <clé>]
"""

import argparse
import os
import re
import sys
from collections import defaultdict

WH1_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
WH3_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"


def lignes(db, table):
    with open(os.path.join(db, table + ".xml"), encoding="utf-8") as f:
        t = f.read()
    return [dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
            for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S)]


def vrai(v):
    return (v or "").strip().lower() in ("1", "true")


def permis_wh1():
    sc = defaultdict(set)
    for r in lignes(WH1_DB, "building_chains"):
        sc[r.get("building_superchain", "")].add(r["key"])
    perm = defaultdict(set)
    for r in lignes(WH1_DB, "slot_template_to_building_superchain_junctions"):
        perm[r["slot_template"]] |= sc.get(r["building_superchain"], set())
    return perm, {r["key"] for r in lignes(WH1_DB, "building_chains")}


def permis_wh3():
    sc = defaultdict(set)
    niveaux = defaultdict(int)
    for r in lignes(WH3_DB, "building_chains"):
        sc[r.get("building_superchain", "")].add(r["key"])
    for r in lignes(WH3_DB, "building_levels"):
        niveaux[r.get("chain", "")] += 1
    parent = {r["key"]: r.get("parent_set", "") for r in lignes(WH3_DB, "building_chain_sets")}
    items = defaultdict(list)
    for r in lignes(WH3_DB, "building_chain_set_items"):
        items[r["set"]].append(r)

    def chaines(r):
        if r.get("chain"):
            return {r["chain"]}
        if r.get("super_chain"):
            return set(sc.get(r["super_chain"], set()))
        return set()

    memo = {}

    def jeu(s, pile=()):
        if s in memo:
            return memo[s]
        if s in pile:
            raise SystemExit(f"jeu de chaînes circulaire : {' -> '.join(pile + (s,))}")
        out = set(jeu(parent[s], pile + (s,))) if parent.get(s) else set()
        for r in items.get(s, ()):
            if not vrai(r.get("remove")):
                out |= chaines(r)
        for r in items.get(s, ()):
            if vrai(r.get("remove")):
                out -= chaines(r)
        memo[s] = out
        return out

    perm = defaultdict(set)
    retraits = defaultdict(set)
    for r in lignes(WH3_DB, "slot_template_permitted_building_chains"):
        c = jeu(r["chain_set"]) if r.get("chain_set") else chaines(r)
        (retraits if vrai(r.get("remove")) else perm)[r["slot_template"]].update(c)
    for g in retraits:
        perm[g] -= retraits[g]
    # familles : une chaîne que WH3 ne range que dans des jeux « landmark » est un monument
    jeux_de = defaultdict(set)
    for s in set(items) | set(parent):
        for c in jeu(s):
            jeux_de[c].add(s)
    monuments = {c for c, js in jeux_de.items() if js and all("landmark" in j for j in js)}
    permises = set().union(*perm.values()) if perm else set()
    return perm, niveaux, monuments, permises


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campagne", default="wh_dlc05_wood_elves")
    ap.add_argument("--detail", action="store_true", help="lister aussi les chaînes ajoutées par WH3")
    ap.add_argument("--region", default=None)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    perm1, chaines1 = permis_wh1()
    perm3, niveaux3, monuments, permises3 = permis_wh3()
    reg1, reg3 = defaultdict(set), defaultdict(set)
    for r in lignes(WH1_DB, "start_pos_region_slot_templates"):
        if r.get("campaign") == a.campagne:
            reg1[r["region"]].add(r["slot_template"])
    for r in lignes(WH3_DB, "start_pos_region_slot_templates"):
        if r.get("campaign") == a.campagne:
            reg3[r["region"]].add(r["slot_template"])
    inconnus = sorted({g for gs in reg3.values() for g in gs if g not in perm3})
    if inconnus:
        print("gabarits de WH3 sans aucune chaîne permise :", inconnus)

    vivantes = {c for c, n in niveaux3.items() if n > 0}
    pertes_totales, mortes, abandonnees = 0, set(), set()
    monuments_wh1, ou_monument = set(), defaultdict(set)
    toutes = sorted(set(reg1) | set(reg3))
    for reg in toutes:
        c3 = set().union(*(perm3.get(g, set()) for g in reg3.get(reg, ()))) if reg3.get(reg) else set()
        for c in c3 & monuments:
            ou_monument[c].add(reg)
    regions = [a.region] if a.region else toutes
    for reg in regions:
        c1 = set().union(*(perm1.get(g, set()) for g in reg1.get(reg, ()))) if reg1.get(reg) else set()
        c3 = set().union(*(perm3.get(g, set()) for g in reg3.get(reg, ()))) if reg3.get(reg) else set()
        mortes |= {c for c in c1 if c not in vivantes}
        c1 = {c for c in c1 if c in vivantes}
        abandonnees |= {c for c in c1 if c not in permises3}
        monuments_wh1 |= c1 & monuments
        base1 = {c for c in c1 if c in permises3 and c not in monuments}
        perdues = sorted(base1 - c3)
        ajoutees = sorted(c for c in c3 - c1 if c in chaines1)
        pertes_totales += len(perdues)
        if perdues or (a.detail and ajoutees) or a.region:
            print(f"\n{reg}\n   WH1 {sorted(reg1.get(reg, ()))}\n   WH3 {sorted(reg3.get(reg, ()))}")
            print(f"   {len(base1)} bâtiments de base en WH1, {len(base1 & c3)} gardés")
            if perdues:
                print(f"   PERDUS ({len(perdues)}) : {perdues}")
            if ajoutees and (a.detail or a.region):
                print(f"   ajoutées par WH3, connues de WH1 ({len(ajoutees)}) : {ajoutees}")
            if a.region:
                print(f"   monuments : {sorted(c3 & monuments)}")
    print(f"\n{len(regions)} régions ; bâtiments de base perdus : {pertes_totales}")
    print(f"monuments que WH1 permettait ({len(monuments_wh1)}), selon les règles de WH3 :")
    for c in sorted(monuments_wh1):
        ou = sorted(ou_monument.get(c, ()))
        print(f"   {c:45} {'-> ' + ', '.join(ou) if ou else 'NULLE PART sur cette carte'}")
    if abandonnees:
        print(f"chaînes de WH1 qu'aucun gabarit de WH3 ne permet (abandonnées par CA) : {sorted(abandonnees)}")
    if mortes:
        print(f"chaînes de WH1 sans niveau dans WH3, non comptées : {sorted(mortes)}")
    return 1 if pertes_totales else 0


if __name__ == "__main__":
    sys.exit(main())
