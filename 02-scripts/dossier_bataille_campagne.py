#!/usr/bin/env python3
"""
dossier_bataille_campagne.py - fabriquer le projet de terrain de BATAILLE d'une carte de campagne, comme CA.

Pourquoi (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\plantage-fin-de-tour.md`) : l'essai du
21.09.2026 à 22 h 15 a planté à la fin du tour 1 (`Warhammer3.exe+0x1497949`, lecture d'un masque 16 bits
nul) : le jeu préparait une bataille terrestre de l'IA et cherchait la **carte des lieux de bataille** de la
campagne dans `terrain/battles/<dossier>/` (colonne `terrain_folder` de `campaign_map_playable_areas`).
Toutes les campagnes de CA livrent ce dossier (12 fichiers) ; nous ne l'avions pas.

Ce que CA y met, relevé dans les packs (prologue, Royaumes du Chaos, Empires Immortels) et chez WH1 :
un terrain de bataille « porteur » de la taille de la carte de tuiles de la campagne, couvert d'**une seule
tuile factice** `terrain\\tiles\\battle\\dummy_set_bca_gen\\dummy_4_x_4` et d'**un seul climat**
(`default` pour les Empires, `hef` ailleurs), et **plat** : le `lf_normal.dds` de bataille des trois campagnes
n'a qu'un seul bloc distinct (normale verticale), la carte logique de bataille des Empires est à 0. Le relief
de bataille (lf_normal et carte logique à 4 × la carte de tuiles) n'est donc qu'un support. BOB le compile par
sa branche « bataille » (action « Heights & Normals », créée seulement pour un dossier `terrain/battles`), et,
si la règle `save_meta_data_map` est vraie, écrit la carte des lieux de bataille (`battle_locations_map.*`,
`blm_primary_mask.dds`, `blm_secondary_mask.dds`) ; la demi-rangée du bord (carte de hauteur impaire) reste
sans tuile, comme chez CA.

Le script crée `raw_data\\terrain\\battles\\<carte>\\` :
    tile_map.png      carte de tuiles (taille de celle de la campagne), tout en couleur de la tuile factice
                      (255, 120, 200) ; lue dans `raw_data\\terrain\\tiles\\battle\\_tile_database\\_settings.xml`
    climate_map.png   même taille, tout en climat `default` (0, 0, 0), comme les Empires
    <carte>.terry     projet `QTU::ProjectTileMap` (modèle : `assembly_kit_example_tile_map` du kit), cartes
                      Height et HeightSea à la taille du relief de campagne (4 × la carte de tuiles)
    <carte>.height.<id>.tif, <carte>.sea_height.<id>.tif   reliefs plats (0,0), flottants 32 bits
    rules.bob         PrefabRoot (une section [Terrain] locale remplace celle du dossier parent : sans elle,
                      « Generate Tile Map BMD » échoue), save_meta_data_map = true, save_final_tile_map = true

Puis : `compiler_terrain_bob.py --carte <carte> --bataille --apply`, et `build_pack.py` embarque la sortie
dans `terrain/battles/<carte>/`.

Cartes de captage (23.09.2026) : `--captage <dossier>` copie aussi les trois calques peints qui choisissent la carte
de bataille ou de siège selon le lieu, `blm_catchment_override%s%s.png` (motif de `empireutility.modder.x64.dll` ;
chez CA, compilés en `blm_catchment_override[_settlement_standard|_settlement_unfortified].compressed_map` du dossier
de bataille, et BOB refuse un calque dont la taille n'est pas celle de la carte des lieux : « Catchment override
layer '%s' dimensions do not match layer '%s' »). Contrôles : taille de `tile_map.png`, RGB, chaque couleur déclarée
dans `battle_catchment_override_areas` (noir = `Gatekeeper`). `--captage-seul` ne fait que cette copie.

Usage :
    python dossier_bataille_campagne.py --carte wh_dlc05_wood_elves_map_1            # vérifications
    python dossier_bataille_campagne.py --carte wh_dlc05_wood_elves_map_1 --apply    # écriture
    python dossier_bataille_campagne.py --carte wh_dlc05_wood_elves_map_1 --captage <dossier> --captage-seul --apply
"""

import argparse
import os
import re
import secrets
import shutil
import sys
import time

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
TUILES_BATAILLE = os.path.join(KIT, "raw_data", "terrain", "tiles", "battle", "_tile_database", "_settings.xml")
ATELIER = r"C:\TotalWar-CampaignMap"
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "terrain-backups")

TUILE_FACTICE = "dummy_set_bca_gen"
CLIMAT = "default"
REGLES = ("[Terrain]\n\tPrefabRoot = art/prefabs/battle\n\tsave_meta_data_map = true\n"
          "\tsave_final_tile_map = true\n")
HAUTEUR = 0.0                  # relief du support, comme les Empires (carte logique de bataille à 0)
CAPTAGE = ("blm_catchment_override.png", "blm_catchment_override_settlement_standard.png",
           "blm_catchment_override_settlement_unfortified.png")
ZONES_CAPTAGE = os.path.join(KIT, "raw_data", "db", "battle_catchment_override_areas.xml")


def couleurs_captage():
    """{(r, g, b): zone} de `battle_catchment_override_areas` (kit)."""
    t = open(ZONES_CAPTAGE, encoding="utf-8").read()
    out = {}
    for bloc in re.findall(r"<battle_catchment_override_areas\b.*?</battle_catchment_override_areas>", t, re.S):
        rgb = tuple(int(re.search(rf"<{c}>(\d+)</{c}>", bloc).group(1)) for c in ("red", "green", "blue"))
        out[rgb] = re.search(r"<area>([^<]*)</area>", bloc).group(1)
    return out


def copier_captage(source, cible, taille, ecrire):
    """Contrôle les trois calques de captage de `source` (taille de la carte de tuiles, RGB, couleurs des zones
    déclarées) et les copie dans le dossier de bataille `cible`."""
    zones = couleurs_captage()
    for n in CAPTAGE:
        p = os.path.join(source, n)
        if not os.path.isfile(p):
            sys.exit(f"calque de captage absent : {p}")
        im = Image.open(p)
        if im.mode != "RGB" or im.size != taille:
            sys.exit(f"{n} : {im.mode} {im.size}, attendu RGB {taille} (taille de la carte de tuiles)")
        couleurs, nombres = np.unique(np.asarray(im).reshape(-1, 3), axis=0, return_counts=True)
        inconnues = [tuple(c) for c in couleurs.tolist() if tuple(c) not in zones]
        if inconnues:
            sys.exit(f"{n} : couleurs absentes de battle_catchment_override_areas : {inconnues[:5]}")
        detail = ", ".join(f"{zones[tuple(c)]} {m}" for c, m in
                           sorted(zip(couleurs.tolist(), nombres.tolist()), key=lambda cm: -cm[1])[:3])
        print(f"captage {n} : {len(couleurs)} zones ({detail}...)")
        if ecrire:
            shutil.copy2(p, os.path.join(cible, n))


def couleur(xml, balise, nom):
    m = re.search(rf"<{balise}\b[^>]*\bname='{re.escape(nom)}'[^>]*>", xml)
    if not m:
        sys.exit(f"{balise} {nom} absent de {TUILES_BATAILLE}")
    return tuple(int(re.search(rf"\b{c}='(\d+)'", m.group(0)).group(1)) for c in ("red", "green", "blue"))


def identifiant():
    """Identifiant de Terry : 15 chiffres hexadécimaux commençant par 1 (comme `184ff1b99563adb`)."""
    return "1" + secrets.token_hex(7)


def cartes_relief(terry_campagne, dossier_campagne, carte):
    """(taille, fichier tif) du relief et du relief marin de la campagne, lus dans son projet Terry."""
    t = open(terry_campagne, encoding="utf-8").read()
    out = {}
    for type_, prefixe in (("Height", "height"), ("HeightSea", "sea_height")):
        m = re.search(rf'<data type="{type_}" size="(\d+)x(\d+)" id="\w+"/>\s*<pc type="QTU::TerrainMapLayer">\s*'
                      rf'<data id="(\w+)"', t)
        if not m:
            sys.exit(f"carte {type_} absente de {terry_campagne}")
        tif = os.path.join(dossier_campagne, f"{carte}.{prefixe}.{m.group(3)}.tif")
        if not os.path.isfile(tif):
            sys.exit(f"relief introuvable : {tif}")
        out[type_] = ((int(m.group(1)), int(m.group(2))), tif, prefixe)
    return out


def projet(carte, reliefs, ids):
    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              f'<project version="27" id="{ids["projet"]}">',
              '  <pc type="QTU::ProjectTileMap">',
              f'    <data terrain_setup="terrain/battles/{carte}/" world_width="0" global_lighting="" '
              'ambient_light_environments="" water_plane_material="materials/campaign_water_plane_default.xml.material" '
              'extend_tile_blend_ranges_to_maximum="0"/>',
              '  </pc>',
              '  <pc type="QTU::Scene">',
              '    <data version="41"/>',
              '  </pc>',
              '  <pc type="QTU::Terrain">']
    for type_ in ("Height", "HeightSea"):
        (w, h), _, _ = reliefs[type_]
        lignes += ['    <pc type="QTU::TerrainMap">',
                   f'      <data type="{type_}" size="{w}x{h}" id="{ids[type_ + "_carte"]}"/>',
                   '      <pc type="QTU::TerrainMapLayer">',
                   f'        <data id="{ids[type_ + "_calque"]}" name="base" visible="1" serializable="1" opacity="1"/>',
                   '      </pc>',
                   '    </pc>']
    lignes += ['  </pc>', '</project>', '']
    return "\n".join(lignes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carte", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--captage", help="dossier des trois calques de captage (blm_catchment_override*.png)")
    ap.add_argument("--captage-seul", action="store_true",
                    help="ne faire que la copie des calques de captage dans le dossier de bataille existant")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    carte = a.carte

    campagne = os.path.join(KIT, "raw_data", "terrain", "campaigns", carte)
    terry_campagne = os.path.join(campagne, f"{carte}.terry")
    cible = os.path.join(KIT, "raw_data", "terrain", "battles", carte)
    xml = open(TUILES_BATAILLE, encoding="utf-8").read()
    c_tuile, c_climat = couleur(xml, "TILE_SET", TUILE_FACTICE), couleur(xml, "CLIMATE", CLIMAT)
    tuiles = Image.open(os.path.join(campagne, "tile_map.png"))
    if a.captage_seul:
        if not a.captage or not os.path.isdir(cible):
            sys.exit("--captage-seul demande --captage <dossier> et un dossier de bataille existant : " + cible)
        copier_captage(a.captage, cible, tuiles.size, a.apply)
        print(f"{'copiés dans ' + cible if a.apply else 'contrôles faits ; relancer avec --apply'}\n"
              f"ensuite : compiler_terrain_bob.py --carte {carte} --bataille --apply")
        return
    reliefs = cartes_relief(terry_campagne, campagne, carte)
    print(f"carte de tuiles de la campagne : {tuiles.size} ; tuile factice {TUILE_FACTICE} {c_tuile} ; "
          f"climat {CLIMAT} {c_climat}")
    for type_, ((w, h), tif, _) in reliefs.items():
        im = Image.open(tif)
        if im.size != (w, h):
            sys.exit(f"{tif} fait {im.size}, le projet déclare {w}x{h}")
        print(f"relief {type_:9} {w}x{h} mode {im.mode} : {os.path.basename(tif)}")
    if reliefs["Height"][0] != (4 * tuiles.size[0], 4 * tuiles.size[1]):
        print(f"attention : relief {reliefs['Height'][0]} pas à 4 × la carte de tuiles {tuiles.size} (CA : 4 ×)")
    if a.captage:
        copier_captage(a.captage, cible, tuiles.size, False)
    if not a.apply:
        print(f"vérifications faites ; relancer avec --apply pour écrire {cible}")
        return

    if os.path.exists(cible):
        garde = os.path.join(SAUVEGARDES, f"raw-battles-{carte}-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.copytree(cible, garde)
        shutil.rmtree(cible)
        print("ancien dossier sauvegardé :", garde)
    os.makedirs(cible)
    ids = {k: identifiant() for k in ("projet", "Height_carte", "Height_calque", "HeightSea_carte", "HeightSea_calque")}
    Image.fromarray(np.full((tuiles.size[1], tuiles.size[0], 3), c_tuile, np.uint8), "RGB").save(
        os.path.join(cible, "tile_map.png"))
    Image.fromarray(np.full((tuiles.size[1], tuiles.size[0], 3), c_climat, np.uint8), "RGB").save(
        os.path.join(cible, "climate_map.png"))
    for type_, ((w, h), _, prefixe) in reliefs.items():
        Image.fromarray(np.full((h, w), HAUTEUR, np.float32), "F").save(
            os.path.join(cible, f"{carte}.{prefixe}.{ids[type_ + '_calque']}.tif"))
    with open(os.path.join(cible, f"{carte}.terry"), "w", encoding="utf-8", newline="\n") as f:
        f.write(projet(carte, reliefs, ids))
    with open(os.path.join(cible, "rules.bob"), "w", encoding="utf-8", newline="\n") as f:
        f.write(REGLES)
    if a.captage:
        copier_captage(a.captage, cible, tuiles.size, True)
    for n in sorted(os.listdir(cible)):
        print(f"   {n:70} {os.path.getsize(os.path.join(cible, n)):>12}")
    print(f"écrit : {cible}\nensuite : compiler_terrain_bob.py --carte {carte} --bataille --apply")


if __name__ == "__main__":
    main()
