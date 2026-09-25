#!/usr/bin/env python3
"""
build_correspondances.py - établit la table de correspondance des factions et des personnages de
la mini-campagne « La Saison des Révélations » entre Warhammer 1 et Warhammer 3.

Lit les tables de départ du kit WH1 (`start_pos_factions`, `start_pos_characters`) pour la
campagne demandée, puis cherche pour chaque clé son homologue dans la base du kit WH3
(`factions`, `agent_subtypes`). Trois règles, dans cet ordre :

1. la clé existe telle quelle dans WH3 ;
2. la clé sans `_mini` existe (c'est le cas des douze clairières et de la plupart des duchés) ;
3. une correspondance manuelle, listée dans EXCEPTIONS ci-dessous, avec sa raison.

Ce qui ne tombe dans aucun cas est signalé `manquant` : ce sont les seules décisions à prendre.
Rien n'est inventé en silence.

Usage :
    python build_correspondances.py --out 04-projets/saison-des-revelations/correspondances.json
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from declarer_gabarits_elfes import est_a_nous, gabarits_par_region  # noqa: E402

WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit"
WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
CAMPAIGN = "wh_dlc05_wood_elves"

# Correspondances que la règle mécanique ne trouve pas, avec la raison. Vérifiées sur pièce dans
# la base de Warhammer 3 le 20.09.2026.
EXCEPTIONS = {
    "wh_dlc05_brt_mini_gisoreux": ("wh_dlc05_brt_gisoroux", "orthographe changée dans WH3 : gisoroux"),
    "wh_dlc05_bst_mini_morghur_herd_brayherd": ("wh_dlc03_bst_beastmen_brayherd",
                                                "la variante brayherd du troupeau de Morghur n'existe pas dans WH3 ; celle des Hommes-bêtes la remplace"),
    # « Deff Grindaz Tribe » n'existe que dans la mini-campagne de WH1. Tenant-lieu : une tribu
    # orque mineure de WH3 qui n'apparaît pas ailleurs sur cette carte, donc aucun asset à créer.
    # La vraie faction (nom et couleurs d'origine) se recrée en phase 6 si Charles le veut.
    "wh_dlc05_grn_mini_deff_grindaz": ("wh_main_grn_teef_snatchaz",
                                       "tribu absente de WH3 ; tenant-lieu, à recréer en phase 6"),
    "wh_dlc05_grn_mini_deff_grindaz_waaagh": ("wh_main_grn_teef_snatchaz_waaagh",
                                              "tribu absente de WH3 ; tenant-lieu, à recréer en phase 6"),
}


# Bâtiments et gabarits de slots : Warhammer 3 a refondu les colonies. Les règles mécaniques
# ci-dessous couvrent tout ce qui se déduit du nom ; le reste est une décision, notée comme telle.
BUILDING_RULES = [
    ("_mini_", "_"),                 # wh_dlc05_wef_oak_of_ages_mini_1 -> ..._oak_of_ages_1
    ("_coast", ""),                  # wh_main_brt_settlement_major_2_coast -> ..._major_2
    ("wef_settlement_major_", "wef_settlement_major_main_"),
    ("wef_settlement_minor_", "wef_settlement_major_main_"),   # WH3 n'a plus de colonie mineure elfe
]
# Gabarits elfes de Warhammer 1 (21.09.2026, 19 h). Jusque-là ils étaient « à ignorer », sur la foi
# d'une vérification fausse (« 0 ligne pour les régions wef de WH3 ») : les 18 régions d'Athel Loren
# n'avaient alors **aucun emplacement**, et le jeu plantait au tout début du chargement de la
# campagne (Warhammer3.exe+0x27A7DFF, lecture de 0x30 : il cherche l'emplacement `primary` d'une
# colonie et n'en trouve pas). En réalité l'Empire Immortel donne un `primary` et un `secondary` à
# chacune de ses régions de forêt (start_pos_region_slot_templates, campagne wh3_main_combi) :
# - principal : le jeu de chaînes `wh3_main_primary_core_special_major_forest` (colonie elfe de
#   forêt), que portent cinq gabarits identiques ; CA emploie `wh_main_special_waterfall_palace_
#   primary` pour huit régions, dont d'autres que le Palais de la Cascade : c'est son gabarit générique ;
# - Chêne des Âges : ses deux gabarits propres, qui existent dans WH3 sans le suffixe `_mini` ;
# - secondaire : ~~les gabarits génériques `wh_main_human_major_secondary[_ressource]`~~ (erreur 60,
#   21.09.2026, 21 h : leur jeu de chaînes ne donne aux elfes que les avant-postes). Les secondaires
#   elfes majeurs de WH1 sont recréés **sous leurs propres clés** par `declarer_gabarits_elfes.py`,
#   selon la recette de forêt de WH3 (décision de Charles : bâtiments et monuments comme dans WH3) :
#   voir `est_a_nous` plus bas. Mineur -> majeur : WH3 n'a plus de colonie elfe mineure.
SLOT_ELFES = {
    "wh_dlc05_elf_major_primary": "wh_main_special_waterfall_palace_primary",
    "wh_dlc05_elf_minor_primary": "wh_main_special_waterfall_palace_primary",
    "wh_dlc05_elf_minor_secondary": "wh_dlc05_elf_major_secondary",
    "wh_dlc05_elf_major_primary_oak_of_ages_mini": "wh_dlc05_elf_major_primary_oak_of_ages",
    "wh_dlc05_elf_major_secondary_oak_of_ages_mini": "wh_dlc05_elf_major_secondary_oak_of_ages",
}
# Régions de la mini-campagne qui existent aussi dans l'Empire Immortel sous une autre clé : elles
# prennent les gabarits que CA leur donne là-bas (mêmes lieux, mêmes monuments : règle de WH3).
# Clés vérifiées dans start_pos_region_slot_templates de WH3 à chaque exécution.
# L'Enclume de Vaul n'y est plus depuis le 21.09.2026, 21 h : son gabarit de CA porte aussi l'arbre de
# Threllock, que notre carte loge dans sa région Threllock ; ses deux gabarits sont déclarés par
# `declarer_gabarits_elfes.PROPRES` et fusionnés ici par `gabarits_par_region()`.
SLOT_PAR_REGION = {
    "wh_dlc05_argwylon_waterfall_palace": ("wh3_main_combi_region_waterfall_palace",
                                           "wh_main_special_waterfall_palace_primary",
                                           "wh_main_special_waterfall_palace_secondary"),
    "wh_dlc05_wydrioth_crag_halls": ("wh3_main_combi_region_crag_halls_of_findol",
                                     "wh_main_special_crag_halls_primary",
                                     "wh_main_special_crag_halls_secondary"),
    "wh_dlc05_talsyn_yn_ecryl_koiran": ("wh3_main_combi_region_kings_glade",
                                        "wh_main_special_yn_edryl_korian_primary",
                                        "wh_main_special_yn_edryl_korian_secondary"),
}
SLOT_RULES = [
    # les plus longs d'abord : « _minor_secondary_beer » avant « _minor_secondary »
    ("wh_main_dwarf_orc_minor_secondary_beer", "wh_main_human_minor_secondary"),
    # les gemmes n'ont pas de gabarit « wh_main_ » dans WH3 ; celui de WH2 existe et sert
    ("wh_main_dwarf_orc_minor_secondary_gems", "wh2_main_human_minor_secondary_gems"),
    ("wh_main_dwarf_orc_minor_secondary_gold", "wh_main_human_minor_secondary_gold"),
    ("wh_main_dwarf_orc_major_primary", "wh_main_human_major_primary"),
    ("wh_main_dwarf_orc_minor_primary", "wh_main_human_minor_primary"),
    ("wh_main_dwarf_orc_major_secondary", "wh_main_human_major_secondary"),
    ("wh_main_dwarf_orc_minor_secondary", "wh_main_human_minor_secondary"),
    ("wh_main_human_major_primary_coast", "wh_main_human_major_primary"),
]


def apply_rules(key, rules, known):
    for old, new in rules:
        if old in key:
            candidate = key.replace(old, new, 1)
            if candidate in known:
                return candidate, f"règle « {old} » → « {new} »"
    return None, None


def rows(kit, table):
    path = os.path.join(kit, "raw_data", "db", table + ".xml")
    return [r for r in ET.parse(path).getroot() if r.tag != "edit_uuid"]


def rowdict(r):
    d = {"_key": r.get("record_key", "")}
    for c in r:
        d[c.tag] = (c.text or "").strip()
    return d


CULTURES = ("wef", "brt", "bst", "grn", "dwf", "vmp", "emp", "chs", "nor")


def resolve(key, known, strip="_mini"):
    if key in known:
        return key, "identique"
    if key in EXCEPTIONS:
        target, why = EXCEPTIONS[key]
        return (target, "exception : " + why) if target in known else (None, "exception invalide : " + target)
    if strip and strip in key:
        plain = key.replace(strip, "", 1)
        if plain in known:
            return plain, "sans « mini »"
    # Le préfixe de jeu change d'un opus à l'autre (wh_dlc05_brt_mini_bastonne dans WH1 est
    # wh_main_brt_bastonne dans WH3) : on apparie sur la culture et sur la fin de la clé.
    parts = key.split("_")
    culture = next((p for p in parts if p in CULTURES), None)
    if culture and f"{culture}_" in key:
        tail = key.split(f"{culture}_", 1)[1].replace("mini_", "", 1)
        candidates = sorted(k for k in known if k.endswith(f"_{culture}_{tail}"))
        if len(candidates) == 1:
            return candidates[0], "préfixe de jeu différent"
        if len(candidates) > 1:
            return None, "ambigu : " + ", ".join(candidates[:4])
    return None, "manquant"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wh1", default=WH1)
    ap.add_argument("--wh3", default=WH3)
    ap.add_argument("--campaign", default=CAMPAIGN)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    factions3 = {rowdict(r)["key"] for r in rows(a.wh3, "factions")}
    subtypes3 = {rowdict(r)["_key"] for r in rows(a.wh3, "agent_subtypes")}

    spf = [rowdict(r) for r in rows(a.wh1, "start_pos_factions") if rowdict(r).get("campaign") == a.campaign]
    by_id = {f["_key"]: f["faction"] for f in spf}

    factions = {}
    for f in sorted({f["faction"] for f in spf}):
        target, how = resolve(f, factions3)
        factions[f] = {"wh3": target, "règle": how,
                       "jouable": any(x.get("playable") == "1" for x in spf if x["faction"] == f),
                       "bataille_de_quete": "_qb" in f}

    chars = [rowdict(r) for r in rows(a.wh1, "start_pos_characters") if rowdict(r).get("faction") in by_id]
    subtypes = {}
    for s in sorted({c.get("subtype", "") for c in chars if c.get("subtype")}):
        if s == "default":
            subtypes[s] = {"wh3": None, "règle": "sans objet : personnage sans sous-type"}
            continue
        target, how = resolve(s, subtypes3, strip=None)
        subtypes[s] = {"wh3": target, "règle": how,
                       "nombre": sum(1 for c in chars if c.get("subtype") == s)}

    # --- bâtiments de colonie et gabarits de slots --------------------------------------------
    buildings3 = {rowdict(r)["_key"] for r in rows(a.wh3, "building_levels")}
    slots3 = {rowdict(r)["_key"] for r in rows(a.wh3, "slot_templates")}
    regions_wh1 = {rowdict(r)["region"] for r in rows(a.wh1, "start_pos_regions")
                   if rowdict(r).get("campaign") == a.campaign}
    reg_ids = {rowdict(r).get("id") for r in rows(a.wh1, "start_pos_regions")
               if rowdict(r).get("campaign") == a.campaign}

    used_buildings = set()
    for r in rows(a.wh1, "start_pos_settlements"):
        d = rowdict(r)
        if d.get("region") not in reg_ids:
            continue
        for k, v in d.items():
            if v and (k.startswith("building") or k in ("primary_building", "port_building")):
                used_buildings.add(v)
    batiments = {}
    for b in sorted(used_buildings):
        if b in buildings3:
            batiments[b] = {"wh3": b, "règle": "identique"}
            continue
        target, how = apply_rules(b, BUILDING_RULES, buildings3)
        batiments[b] = {"wh3": target, "règle": how or "manquant"}

    used_slots = {rowdict(r)["slot_template"] for r in rows(a.wh1, "start_pos_region_slot_templates")
                  if rowdict(r).get("campaign") == a.campaign}
    gabarits = {}
    for s in sorted(used_slots):
        if s in SLOT_ELFES:
            cible = SLOT_ELFES[s]
            regle = ("gabarit elfe : majeur recréé par declarer_gabarits_elfes.py (WH3 n'a plus de "
                     "colonie elfe mineure)" if est_a_nous(cible) else "gabarit elfe : équivalent de l'Empire Immortel")
            gabarits[s] = ({"wh3": cible, "règle": regle}
                           if cible in slots3 else {"wh3": None, "règle": "manquant : " + cible})
            continue
        if est_a_nous(s):
            gabarits[s] = ({"wh3": s, "règle": "gabarit de WH1 recréé par declarer_gabarits_elfes.py"}
                           if s in slots3 else
                           {"wh3": None, "règle": "manquant : lancer declarer_gabarits_elfes.py --apply"})
            continue
        if s in slots3:
            gabarits[s] = {"wh3": s, "règle": "identique"}
            continue
        target, how = apply_rules(s, SLOT_RULES, slots3)
        gabarits[s] = {"wh3": target, "règle": how or "manquant"}

    # gabarits imposés par région (priment sur la table par gabarit)
    ie = {(d["region"], d["slot_type"]): d["slot_template"]
          for d in (rowdict(r) for r in rows(a.wh3, "start_pos_region_slot_templates"))
          if d.get("campaign") == "wh3_main_combi"}
    par_region = {}
    for reg, (reg_ie, prim, sec) in sorted(SLOT_PAR_REGION.items()):
        if reg not in regions_wh1:
            continue
        ok = (ie.get((reg_ie, "primary")) == prim and ie.get((reg_ie, "secondary")) == sec
              and prim in slots3 and sec in slots3)
        par_region[reg] = {"primary": prim if ok else None, "secondary": sec if ok else None, "valide": ok,
                           "règle": (f"gabarits de {reg_ie} dans l'Empire Immortel" if ok
                                     else f"invalide : {reg_ie} n'a plus ces gabarits dans WH3")}
    # gabarits secondaires propres à une région (declarer_gabarits_elfes.PROPRES) ; le principal suit
    # la table par gabarit (`primary` à None : declare_campaign.py retombe alors sur `gabarits_de_slots`)
    for reg, sec in sorted(gabarits_par_region().items()):
        if reg not in regions_wh1:
            continue
        ok = sec in slots3
        par_region[reg] = {"primary": None, "secondary": sec if ok else None, "valide": ok,
                           "règle": ("gabarit propre, declarer_gabarits_elfes.py" if ok
                                     else "manquant : lancer declarer_gabarits_elfes.py --apply")}

    out = {
        "_commentaire": f"Correspondances WH1 -> WH3 pour la campagne {a.campaign}, établies par build_correspondances.py.",
        "batiments_de_colonie": batiments,
        "gabarits_de_slots": gabarits,
        "gabarits_de_slots_par_region": par_region,
        "campagne": {"wh1": a.campaign, "wh3": a.campaign},
        "carte": {"wh1": "wh_dlc05_wood_elves_map_1", "wh3": "wh_dlc05_wood_elves_map_1"},
        "factions": factions,
        "sous_types_de_personnages": subtypes,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    real = {k: v for k, v in factions.items() if not v["bataille_de_quete"]}
    missing_f = [k for k, v in real.items() if v["wh3"] is None]
    missing_s = [k for k, v in subtypes.items() if v["wh3"] is None and k != "default"]
    print(f"écrit {a.out}")
    print(f"  factions : {len(factions)} ({len(real)} réelles, {len(factions) - len(real)} de bataille de quête)")
    for how in ("identique", "sans « mini »", "préfixe de jeu différent", "exception", "ambigu", "manquant"):
        n = sum(1 for v in real.values() if v["règle"].startswith(how))
        if n:
            print(f"     {how:26s} {n}")
    print(f"  sous-types de personnages : {len(subtypes)} ; sans homologue : {len(missing_s)}")
    mb = [k for k, v in batiments.items() if v["wh3"] is None]
    mg = [k for k, v in gabarits.items() if v["wh3"] is None]
    mr = [k for k, v in par_region.items() if not v["valide"]]
    print(f"  bâtiments de colonie : {len(batiments)} ; sans homologue : {len(mb)} {mb[:4]}")
    print(f"  gabarits de slots : {len(gabarits)} ; sans homologue : {len(mg)} {mg[:4]}")
    print(f"  gabarits imposés par région : {len(par_region)} ; invalides : {len(mr)} {mr[:4]}")
    if missing_f:
        print("  FACTIONS SANS HOMOLOGUE (décision à prendre) :", ", ".join(missing_f))
    if missing_s:
        print("  SOUS-TYPES SANS HOMOLOGUE :", ", ".join(missing_s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
