#!/usr/bin/env python3
"""
declarer_gabarits_elfes.py - gabarits d'emplacement secondaire des colonies elfes de la
mini-campagne, **selon les règles de Warhammer 3**.

Décision de Charles (21.09.2026, 21 h) : bâtiments, monuments et arbres fonctionnent comme dans
Warhammer 3 ; de Warhammer 1 on garde la carte et les scripts de la mini-campagne.

La règle de WH3, relevée sur ses 13 régions de forêt de l'Empire Immortel : chaque secondaire de
forêt se compose de

    wh3_main_secondary_addon_garrison_major
    wh3_main_secondary_core_generic_major_variant_wef_forest   (bâtiments elfes, avant-postes retirés)
    wh3_main_secondary_addon_res_<ressource>                   (s'il y a une ressource)
    le jeu « monument » de la région (landmark)

Ce que le script déclare :

- **Gabarits génériques** `wh_dlc05_elf_major_secondary[_ressource]` : la recette sans monument,
  un par gabarit secondaire elfe majeur de WH1 employé par la campagne (même clé, même ressource).
  WH3 n'a aucun secondaire de forêt sans monument ; les gabarits humains posés à 19 h ne donnaient
  aux elfes que les **avant-postes** (erreur 60). Les colonies mineures de WH1 prennent le générique
  sans ressource (WH3 n'a plus de colonie elfe mineure : `build_correspondances.SLOT_ELFES`).
- **Gabarits propres à une région** (`PROPRES`) : l'Enclume de Vaul et Threllock. Dans l'Empire
  Immortel, CA a mis l'arbre de Threllock (jeu à lui seul) dans le gabarit de l'Enclume de Vaul, faute
  de région Threllock sur cette carte ; la nôtre en a une : l'arbre y va, l'Enclume garde la Forge
  stellaire. Tout le reste de ces deux gabarits vient des jeux de CA.
- Les régions de l'Empire Immortel présentes sur notre carte (Palais de la Cascade, Crag Halls,
  Yn Edryl Korian, Chêne des Âges) gardent les gabarits de CA : `build_correspondances.SLOT_PAR_REGION`.

Les lignes vont dans le kit (sauvegarde dans `05-journal\\db-backups\\`) ; `build_pack.py` les
embarque (`lignes_du_mod()`) ; `build_correspondances.py` fait pointer les régions dessus
(`gabarits_par_region()`). Une clé déjà présente dans le kit n'est admise que si elle porte exactement
notre contenu (`verifie_cles_libres`). Les lignes d'une version précédente de ce script qui ne
servent plus (`OBSOLETES`) sont retirées du kit.

Usage :
    python declarer_gabarits_elfes.py [--apply]
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from declare_map import Table, plain                                 # noqa: E402

WH1_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
WH3_KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
WH3_DB = os.path.join(WH3_KIT, "raw_data", "db")
ATELIER = r"C:\TotalWar-CampaignMap"
CAMPAGNE = "wh_dlc05_wood_elves"

GARNISON = "wh3_main_secondary_addon_garrison_major"
COEUR_FORET = "wh3_main_secondary_core_generic_major_variant_wef_forest"
RESSOURCE = "wh3_main_secondary_addon_res_{}"
ARBRE_THRELLOCK = "wh3_main_secondary_addon_landmark_threllock"

# région de la campagne -> (clé du gabarit, gabarit de CA dont il part ou None, jeux retirés, jeux ajoutés)
# Sans gabarit de départ : garnison + forêt + la ressource du gabarit de WH1 de la région.
PROPRES = {
    "wh_dlc05_torgovann_vauls_anvil": ("wh_dlc05_mini_special_vauls_anvil_secondary",
                                       "wh_main_special_vauls_anvil_secondary", {ARBRE_THRELLOCK}, set()),
    "wh_dlc05_fyr_darric_threllock": ("wh_dlc05_mini_special_threllock_secondary",
                                      None, set(), {ARBRE_THRELLOCK}),
}

# Lignes écrites à 20 h 52 par la version « règles de WH1 » (les dix uniques partout, abandonnée sur
# décision de Charles) : table -> clés d'enregistrement à retirer si elles sont encore là.
_UNIQUES = "wh_dlc05_mini_secondary_addon_wef_uniques"
_UNIQUES_CHAINES = ["wh_dlc05_wef_office_starlight_forge", "wh_dlc05_wef_office_the_wild_heath",
                    "wh_dlc05_wef_office_wardancer_feast_halls", "wh_dlc05_wef_office_wildwood_waystones",
                    "wh_dlc05_wef_temple_ereth_khial", "wh_dlc05_wef_temple_kurnous",
                    "wh_dlc05_wef_tree_delliandra", "wh_dlc05_wef_tree_druthandor",
                    "wh_dlc05_wef_tree_talrennic", "wh_dlc05_wef_tree_threllock"]
_MAJEURS_WH1 = ["wh_dlc05_elf_major_secondary", "wh_dlc05_elf_major_secondary_furs",
                "wh_dlc05_elf_major_secondary_iron", "wh_dlc05_elf_major_secondary_marble",
                "wh_dlc05_elf_major_secondary_timber", "wh_dlc05_elf_major_secondary_wine"]
OBSOLETES = {
    "slot_templates": ["wh_dlc05_elf_minor_secondary"],
    "slot_template_permitted_building_chains": (
        [g + _UNIQUES for g in _MAJEURS_WH1]
        + ["wh_dlc05_elf_minor_secondary" + j for j in (GARNISON, COEUR_FORET)]),
    "building_chain_sets": [_UNIQUES],
    "building_chain_set_items": [_UNIQUES + c for c in _UNIQUES_CHAINES],
}


def lignes(db, table):
    with open(os.path.join(db, table + ".xml"), encoding="utf-8") as f:
        t = f.read()
    return [dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
            for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S)]


def est_a_nous(gabarit):
    """Gabarit secondaire elfe majeur de WH1 que ce script recrée (le Chêne des Âges a les siens)."""
    return gabarit.startswith("wh_dlc05_elf_major_secondary") and "oak_of_ages" not in gabarit


def suffixe_ressource(gabarit_wh1):
    return gabarit_wh1.split("_secondary", 1)[1].lstrip("_") if "_secondary" in gabarit_wh1 else ""


def plan():
    """Rend {gabarit: {"ressource", "jeux", "regions"}} ; lève SystemExit sur toute incohérence."""
    wh1 = [r for r in lignes(WH1_DB, "start_pos_region_slot_templates") if r.get("campaign") == CAMPAGNE]
    ressource1 = {r["key"]: r.get("resource", "") for r in lignes(WH1_DB, "slot_templates")}
    secondaire1 = {r["region"]: r["slot_template"] for r in wh1 if r["slot_type"] == "secondary"}
    ressource3 = {r["key"]: r.get("resource", "") for r in lignes(WH3_DB, "slot_templates")}
    jeux3 = {r["key"] for r in lignes(WH3_DB, "building_chain_sets")}
    jeux_de3 = defaultdict(list)
    for r in lignes(WH3_DB, "slot_template_permitted_building_chains"):
        if r.get("chain_set") and r.get("remove") not in ("1", "true"):
            jeux_de3[r["slot_template"]].append(r["chain_set"])

    def existe(j):
        if j not in jeux3:
            raise SystemExit(f"jeu de chaînes absent de WH3 : {j}")
        return j

    def recette(gabarit_wh1):
        jeux = [existe(GARNISON), existe(COEUR_FORET)]
        if suffixe_ressource(gabarit_wh1):
            jeux.append(existe(RESSOURCE.format(suffixe_ressource(gabarit_wh1))))
        return jeux

    gabarits = {}
    for g in sorted({r["slot_template"] for r in wh1 if est_a_nous(r["slot_template"])}):
        gabarits[g] = {"ressource": ressource1.get(g, ""), "jeux": recette(g), "regions": []}
    for region, (cle, depart, moins, plus) in PROPRES.items():
        if region not in secondaire1:
            raise SystemExit(f"{region} : région absente de la campagne de WH1")
        if depart:
            if depart not in jeux_de3:
                raise SystemExit(f"{region} : gabarit de CA introuvable : {depart}")
            manquent = moins - set(jeux_de3[depart])
            if manquent:
                raise SystemExit(f"{region} : {depart} ne porte pas {sorted(manquent)} (CA a changé ?)")
            jeux = [j for j in jeux_de3[depart] if j not in moins]
            res = ressource3.get(depart, "")
        else:
            jeux = recette(secondaire1[region])
            res = ressource1.get(secondaire1[region], "")
        jeux += [existe(j) for j in sorted(plus) if j not in jeux]
        gabarits[cle] = {"ressource": res, "jeux": jeux, "regions": [region]}
    verifie_cles_libres(gabarits)
    return gabarits


def gabarits_par_region():
    """Pour `build_correspondances.py` : région -> gabarit secondaire propre."""
    return {region: cle for region, (cle, *_reste) in PROPRES.items()}


def verifie_cles_libres(gabarits):
    """Une clé déjà présente dans le kit n'est admise que si elle porte exactement notre contenu
    (nos propres lignes d'une exécution précédente). Sinon c'est une clé de CA, ou une ligne
    retouchée depuis : on ne réécrit jamais un gabarit du jeu."""
    ressource3 = {r["key"]: r.get("resource", "") for r in lignes(WH3_DB, "slot_templates")}
    presents = [g for g in gabarits if g in ressource3]
    if not presents:
        return
    obsoletes = set(OBSOLETES["slot_template_permitted_building_chains"])
    jeux_kit = defaultdict(set)
    for r in lignes(WH3_DB, "slot_template_permitted_building_chains"):
        if r["slot_template"] in gabarits and r["slot_template"] + r.get("chain_set", "") not in obsoletes:
            jeux_kit[r["slot_template"]].add((r.get("chain_set", ""), r.get("chain", ""),
                                             r.get("super_chain", ""), r.get("remove", "0")))
    autres = [g for g in presents
              if ressource3.get(g, "") != gabarits[g]["ressource"]
              or not jeux_kit[g] <= {(j, "", "", "0") for j in gabarits[g]["jeux"]}]
    if autres:
        raise SystemExit(f"clés déjà présentes dans le kit avec un autre contenu (clé de CA ou ligne "
                         f"retouchée) : {autres}")


def lignes_du_mod():
    """Clés à embarquer dans le pack, par table (pour `build_pack.py`)."""
    gabarits = tuple(plan())
    return {
        "slot_templates": ("key", gabarits),
        "slot_template_permitted_building_chains": ("slot_template", gabarits),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    gabarits = plan()
    print(f"{len(gabarits)} gabarits secondaires elfes (règles de WH3) :")
    for g, d in gabarits.items():
        ou = f"  [{', '.join(d['regions'])}]" if d["regions"] else ""
        print(f"   {g:45} ressource {d['ressource'] or '-':15} {d['jeux']}{ou}")

    ecrit = {
        "slot_templates": [(g, [plain("key", g), plain("resource", d["ressource"])]) for g, d in gabarits.items()],
        "slot_template_permitted_building_chains": [
            (g + j, [plain("slot_template", g), plain("chain_set", j), plain("chain", ""),
                     plain("super_chain", ""), plain("remove", 0)])
            for g, d in gabarits.items() for j in d["jeux"]],
        "building_chain_sets": [],
        "building_chain_set_items": [],
    }
    sauvegarde = os.path.join(ATELIER, "05-journal", "db-backups",
                              datetime.now().strftime("%Y%m%d-%H%M%S") + "-gabarits-elfes")
    for table, recs in ecrit.items():
        t = Table(WH3_KIT, table)
        for cle in OBSOLETES.get(table, []):
            t.remove(cle)
        for cle, champs in recs:
            t.add(cle, champs)
        print(f"  {table:42s} ajouté {len(t.added):3d}  retiré {len(t.removed):3d}  déjà présent {len(t.skipped):3d}")
        if a.apply and (t.added or t.removed):
            t.save(sauvegarde)
    print(f"\nsauvegardes dans {sauvegarde}" if a.apply else "\nessai à blanc : relancer avec --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
