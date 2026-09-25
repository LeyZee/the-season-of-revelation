#!/usr/bin/env python3
"""
captage_campagne.py - peint les 3 cartes de captage des batailles de notre campagne (choix de la carte de bataille et
de siège selon le lieu), aux couleurs des zones de WH3 (`battle_catchment_override_areas`).

Pourquoi (23.09.2026) : notre terrain de bataille n'avait pas ses cartes de captage (9 fichiers sur les 12 de CA) et
aucune ligne `battle_catchment_override_battle_mappings` ne visait notre chemin de bataille. Relevé :
- le jeu lit la couleur du pixel de la bataille (« find_catchment_override: pixel colour is », empireutility), cherche
  la zone de cette couleur, puis la ligne (zone, type de bataille, cultures, chemin de bataille) -> groupe de cartes ;
- UNE image par famille : `blm_catchment_override%s%s.png` -> générale, `_settlement_standard`,
  `_settlement_unfortified` ; compilées par BOB en `.compressed_map` (« FASTBIN0 », pixels de 32 bits, RLE_CARD32) ;
- WH1 avait une seule carte pour notre carte (`blm_catchment_override_map.dds`, 800 x 881, 28 zones de WH1 dont les
  clairières d'hiver, de nuit, flétries, de cendres) ; WH3 ne connaît plus ces zones.
Orientation : le nord en haut ; pixel (x, y) -> hex (x // 2, 439 - y // 2) (vérifié : 99,9 % des pixels colorés de
WH1 sur la terre, 96,4 % de ses forêts sur nos forêts, 98,3 % de sa côte sur la terre).

Zones (celles de WH3 pour la même géographie aux Empires) :
- générale : Athel Loren -> forêt elfe ; Mousillon -> terres ou forêts vampiriques ; Montagnes grises, Massif
  Orcal, montagnes et cols -> montagnes du Vieux Monde ; en Bretonnie : côte (côte de WH1 ou 2 hex de la mer), forêts,
  collines, sinon prairies ; mer -> noir (zone « Gatekeeper », batailles navales) ;
- colonies (standard et non fortifiée) : la zone de colonie de la culture de la province (elfes, vampires, nains,
  peaux-vertes, Bretonnie du sud et du nord).

Usage :
    python captage_campagne.py [--sortie <dossier>]      # défaut : 04-projets\\saison-des-revelations\\captage
"""

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caime_layers as CL                                                     # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
CAIME = ATELIER + r"\01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe"
CARTE = "wh_dlc05_wood_elves_map_1"
MAP_HEX = os.path.join(KIT, "raw_data", "EmpireDesignData", "campaign_maps", CARTE, "map.hex")
SPEC = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "map_spec.json")
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "captage")
L, H = 800, 881                         # taille de la carte de tuiles (celle de WH1 pour sa carte de captage)
HL, HH = 400, 440                       # grille des hex

ATHEL_LOREN = {"anmyr", "argwylon", "arranoc", "atylwyth", "cavaroc", "cythral", "fyr_darric", "modryn",
               "oak_of_ages", "talsyn", "tirsyth", "torgovann", "wydrioth"}
MONTAGNES = {"grey_mountains", "grey_mountains_2", "massif_orcal"}
BRETONNIE_SUD = {"aquitaine", "bordeleaux", "brionne", "carcassonne"}
# sols (index des listes de CAIME : 15 terrestres, puis les maritimes)
SOL_FORET = {1, 5, 7}                   # dense_forest, hilly_light_forest, light_forest
SOL_COLLINES = {4}
SOL_MONTAGNE = {9}
SOL_MARAIS = {8, 12}
SOL_MER_OUVERTE = {15, 18}              # sea_coast, sea_ocean (pas les lacs ni les rivières)

# Zones de WH1 (couleurs de sa carte de captage, lues en RVB ; noms de sa table battle_catchment_override_areas),
# guide principal : ses concepteurs avaient peint la Bretonnie surtout en plaines avec des bosquets, là où nos types
# de sol disent « forêt » presque partout. Hors d'Athel Loren -> zone de WH3 de la même nature ; dans Athel Loren,
# toutes (clairières d'hiver, de nuit, flétries, de cendres, Chêne compris) -> forêt elfe de WH3, qui n'a pas de
# variantes de saison.
WH1_VERS_WH3 = {
    (209, 149, 112): "plaine",        # wh_dlc05_mini_wef_plains_areas
    (0, 152, 255): "plaine",          # wh_dlc05_mini_wef_river_areas
    (0, 112, 255): "plaine",          # wh_dlc05_mini_wef_lake_areas
    (167, 197, 82): "foret",          # wh_dlc05_mini_wef_forest_areas
    (103, 155, 82): "collines",       # wh_dlc05_mini_wef_hilly_areas
    (255, 206, 158): "cote",          # wh_dlc05_mini_wef_coastal_areas
    (255, 255, 82): "col",            # wh_dlc05_mini_wef_mtn_pass_areas
    (158, 206, 255): "col",           # wh_main_mountain_pass_areas
}


def couleurs_wh3():
    """{zone: (r, v, b)} de battle_catchment_override_areas du kit de WH3."""
    t = open(os.path.join(KIT, "raw_data", "db", "battle_catchment_override_areas.xml"), encoding="utf-8").read()
    out = {}
    for b in re.findall(r"<battle_catchment_override_areas(?: [^>]*)?>(.*?)</battle_catchment_override_areas>", t, re.S):
        v = {k: x for k, x in re.findall(r"<([a-z_]+)>([^<]*)</\1>", b)}
        out[v["area"]] = (int(v["red"]), int(v["green"]), int(v["blue"]))
    return out


def noms_regions():
    """Liste des régions terrestres de la carte (ordre de CAIME : l'indice du calque Regions)."""
    sortie = subprocess.run([CAIME, "info", "--map", MAP_HEX, "--names"], capture_output=True, text=True).stdout
    bloc = sortie.split("Land regions", 1)[1].split("Sea regions", 1)[0]
    return re.findall(r"\[\d+\] (\S+)", bloc)


def calques():
    """(régions, sols) en grille hex, ligne 0 = sud, exportés par CAIME (lecture seule de la carte)."""
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([CAIME, "export-layer", "--map", MAP_HEX, "--out", d, "--layer", "Regions", "--layer",
                        "GroundTypes", "--format", "binary"], capture_output=True, text=True, check=True)
        _, reg = CL.read_layer(os.path.join(d, "layer_regions.hex_layer"))
        _, sol = CL.read_layer(os.path.join(d, "layer_ground_types.hex_layer"))
    return reg.reshape(HH, HL), sol.reshape(HH, HL)


def carte_wh1():
    """La carte de captage de WH1 pour notre carte (RVB, 881 x 800), lue dans ses packs ; None si absente."""
    try:
        from modeles_wh1 import SourceWH1
    except Exception:                                                        # noqa: BLE001
        return None
    b = SourceWH1().lire(f"terrain/battles/{CARTE}/blm_catchment_override_map.dds")
    if not b:
        return None
    h, w = struct.unpack_from("<II", b, 12)
    px = np.frombuffer(b, np.uint8, count=w * h * 4, offset=128).reshape(h, w, 4)
    return px[:, :, [2, 1, 0]]                                               # BGRA -> RVB


def voisinage(masque, rayon):
    """Dilatation carrée d'un masque booléen de `rayon` cases."""
    out = masque.copy()
    for dy in range(-rayon, rayon + 1):
        for dx in range(-rayon, rayon + 1):
            out |= np.roll(np.roll(masque, dy, 0), dx, 1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sortie", default=SORTIE)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    zones = couleurs_wh3()
    regions = noms_regions()
    province = {r["key"]: r.get("province", "").replace("wh_dlc05_", "")
                for r in json.load(open(SPEC, encoding="utf-8"))["regions"]}      # mers et terres sauvages : sans
    reg, sol = calques()
    wh1 = carte_wh1()

    # pixel -> hex (nord en haut)
    ys, xs = np.mgrid[0:H, 0:L]
    hy = np.clip(HH - 1 - ys // 2, 0, HH - 1)
    hx = np.clip(xs // 2, 0, HL - 1)
    p_reg, p_sol = reg[hy, hx], sol[hy, hx]
    terre = (p_sol < 15) & (p_reg >= 0) & (p_reg < len(regions))
    mer_ouverte_hex = np.isin(sol, list(SOL_MER_OUVERTE))
    cote = voisinage(mer_ouverte_hex, 2)[hy, hx] & terre

    prov = np.array([province.get(r, "") for r in regions] + [""])
    p_prov = prov[np.where(terre, p_reg, len(regions))]
    nom_reg = np.array(regions + [""])[np.where(terre, p_reg, len(regions))]

    generale = np.full((H, L), "", object)
    colonies = np.full((H, L), "", object)
    al = np.isin(p_prov, list(ATHEL_LOREN))
    mous = p_prov == "mousillon"
    mont = np.isin(p_prov, list(MONTAGNES))
    sud = np.isin(p_prov, list(BRETONNIE_SUD))

    # nature du lieu : la zone de WH1 si elle en a une, sinon le type de sol (terre laissée en noir par WH1)
    nature = np.full((H, L), "plaine", object)
    nature[np.isin(p_sol, list(SOL_FORET))] = "foret"
    nature[np.isin(p_sol, list(SOL_COLLINES))] = "collines"
    nature[np.isin(p_sol, list(SOL_MONTAGNE))] = "col"
    nature[cote] = "cote"
    col_wh1 = np.zeros((H, L), bool)          # les cols que WH1 a dessinés (zones « mtn_pass »), seuls vrais défilés
    if wh1 is not None and wh1.shape[:2] == (H, L):
        for c, n in WH1_VERS_WH3.items():
            masque = np.all(wh1 == c, axis=2)
            nature[masque] = n
            if n == "col":
                col_wh1 |= masque
    # Revue des cartes de bataille (25.09.2026, I-1 et I-2 ; erreur 271) : `*_chokepoint` impose une bataille de passage
    # (land_bridge). Les collines de Bretonnie prennent les prairies (mêmes cartes de collines, 12 variantes, sans
    # changement de type) ; les provinces de montagne, la montagne ordinaire des Empires (17 variantes) ; le défilé nain
    # ne reste que sur les cols de WH1.
    VERS_BRETONNIE = {"plaine": "wh3_main_macro_brt_grasslands", "foret": "wh3_main_macro_brt_forest",
                      "collines": "wh3_main_macro_brt_grasslands", "cote": "wh3_main_macro_brt_coast",
                      "col": "wh3_main_macro_old_world_mountains"}
    for n, z in VERS_BRETONNIE.items():
        generale[terre & (nature == n)] = z
    generale[terre & mont] = "wh3_main_macro_old_world_mountains"
    # (mesure du 25.09.2026 : l'essentiel des défilés, ~198 000 px, venait du sol de montagne DES PROVINCES BRETONNES,
    # pas des provinces de montagne, 3 462 px de cols de WH1 seulement)
    generale[terre & col_wh1] = "wh3_main_macro_old_world_mountains_dwf_chokepoint"
    defile = generale == "wh3_main_macro_old_world_mountains_dwf_chokepoint"
    print(f"défilés : {int((defile & mont).sum())} px dans les provinces de montagne (cols de WH1 : "
          f"{int((terre & mont & col_wh1).sum())} px sur {int((terre & mont).sum())}), {int((defile & ~mont).sum())} px "
          f"ailleurs (sol de montagne : {int((defile & ~mont & (p_sol == 9)).sum())} px, cols de WH1 : "
          f"{int((defile & ~mont & col_wh1).sum())} px)")
    generale[mous] = "wh3_main_macro_vmp_grasslands"
    generale[mous & ((nature == "foret") | np.isin(p_sol, list(SOL_MARAIS)))] = "wh3_main_macro_vmp_forest"
    generale[al] = "wh3_main_macro_wef_forest"

    colonies[terre] = "wh3_main_brt_settlement_2"
    colonies[terre & sud] = "wh3_dlc20_brt_settlement_1"
    colonies[al] = "wh3_main_wef_settlement"
    colonies[mous] = "wh3_main_vmp_settlement_1"
    colonies[mont] = "wh3_main_grn_settlement_1"
    colonies[p_prov == "massif_orcal"] = "wh3_main_grn_settlement_2"
    colonies[np.isin(nom_reg, ["wh_dlc05_grey_mountains_2_karak_ziflin", "wh_dlc05_grey_mountains_2_karak_tzor"])] = \
        "wh3_main_dwf_settlement_1"
    colonies[nom_reg == "wh_dlc05_grey_mountains_2_blackstone_post"] = "wh3_main_dwf_settlement_2"

    os.makedirs(a.sortie, exist_ok=True)
    bilan = {}
    for nom, grille in (("blm_catchment_override.png", generale),
                        ("blm_catchment_override_settlement_standard.png", colonies),
                        ("blm_catchment_override_settlement_unfortified.png", colonies)):
        img = np.zeros((H, L, 3), np.uint8)
        comptes = {}
        for z in sorted(set(grille.ravel()) - {""}):
            if z not in zones:
                raise KeyError(f"zone inconnue de battle_catchment_override_areas : {z}")
            m = grille == z
            img[m] = zones[z]
            comptes[z] = int(m.sum())
        Image.fromarray(img, "RGB").save(os.path.join(a.sortie, nom))
        bilan[nom] = comptes
        print(f"{nom} : {H} x {L} ; " + ", ".join(f"{z} {n}" for z, n in sorted(comptes.items(), key=lambda kv: -kv[1])))
    json.dump({"zones": sorted({z for c in bilan.values() for z in c}), "pixels": bilan,
               "orientation": "nord en haut ; pixel (x, y) -> hex (x // 2, 439 - y // 2)"},
              open(os.path.join(a.sortie, "zones.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("terre peinte :", int(terre.sum()), "pixels ; mer (noir) :", int((~terre).sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
