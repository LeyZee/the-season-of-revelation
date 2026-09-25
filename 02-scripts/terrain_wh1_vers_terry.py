#!/usr/bin/env python3
"""
terrain_wh1_vers_terry.py - fabriquer le projet Terry « de campagne » de la carte
`wh_dlc05_wood_elves_map_1` a partir du terrain compile de Warhammer 1.

Pourquoi (21.09.2026, journal `05-journal\\2026-09-21-phase-3-terrain\\terrain.md`). Le terrain
compile a change de format entre les deux jeux (WH1 : 72 maillages + carte de hauteur 16 bits ;
WH3 : carte de hauteur pleine BC6H, plan logique compresse). On ne peut donc pas le recopier : il
faut un projet Terry que BOB compile, comme ChaosRobie l'a fait pour les Empires Immortels. Toutes
les conventions ci-dessous ont ete relevees sur son projet (installe dans le kit) et verifiees
contre le terrain compile de CA :

- tailles : 8 px par hex (+4 lignes) pour les grands rasters, 4 pour `HeightShroud`, 2 pour
  les masques et `tile_map.png` ; ici 3200 x 3524, 1600 x 1762, 800 x 881 ;
- orientation : rasters et `tile_map.png` du nord vers le sud (ligne 0 = haut) ; la couche d'hex
  de CAIME a sa ligne 0 en bas ; les colonnes impaires sont decalees d'un demi-hex vers le haut ;
- hauteurs en unites du monde, plan d'eau a 0 (le brouillard compile vaut hauteur + 1, et 1 en
  mer) ;
- **la mer est declaree par `tile_map.png`** (couleur (83, 141, 213), type de tuile `sea`), pas
  par la hauteur : dans les Empires, la moitie des hex de mer ont une hauteur positive ;
- `blend.tif` porte directement le numero de texture de WH3 (0 a 143, ordre de
  `_tile_database\\_settings.bin`) : il est identique a 99,66 % au `global_blend.dds` compile.

Le terrain de WH1, relu et etalonne :

- `lf_height_map.dds` : 3200 x 3524, 16 bits, **du nord vers le sud** (la mer y est au minimum) ;
  hauteur = 0,0002185272 x v - 0,753375, etalonnee par moindres carres sur les 614 484 sommets des
  72 maillages (ecart moyen 0,38 : le detail des tuiles de WH1) ;
- `global_map\\global_blend.dds` : 3200 x 3524, un octet, **du sud vers le nord** (les marais
  tombent sur la texture `marsh` dans 74 % des hex de marais), numeros des 19 textures de
  `texture_arrays.xml` ; traduits vers celles de WH3 par couleur moyenne et usage (table TEXTURES).

Version minimale (phase 3) : relief, mer, textures, sans arbres, sans objets, sans rivieres.

Phase 6 (21.09.2026, 21 h, captures de Charles : « la carte est vide ») :
- **arbres** : `trees.png` de WH1 (800 x 881, 2 px par hex, nord en haut, comme `tree.tif`) ; chaque
  couleur y est une famille d'essences (`campaign_tree_ids` du kit WH1), traduite vers la famille
  de WH3 (`FAMILLES_ARBRES`) puis vers l'index de palette de `tree.tif`, dont la palette **est** la
  table `campaign_tree_ids` de WH3 (verifie sur les Empires : 51 index, 51 couleurs de la table).
  L'apparence suit la culture qui possede la region (`campaign_tree_type_cultures`) ;
- **neige** : la clairiere d'hiver de la Saison des Revelations (sud d'Athel Loren : textures de neige
  6 a 9 et arbres d'hiver de WH1 au meme endroit). Les textures de neige de WH3 y faisaient des taches
  blanches aux bords en escalier ; comme dans les Empires, la neige est faite par le masque
  `SnowMask` (`neige`) sur des eboulis, et les arbres d'hiver sont des essences enneigees. (A 21 h 05
  j'avais d'abord supprime cette neige, la prenant pour un defaut : erreur 65.)
- **cote** : 1,2 % de la terre (bande de la cote ouest) etait sous le plan d'eau (hauteur < 0) et
  donc noyee ; la terre basse est relevee en douceur au-dessus de 0 (`PLANCHER_TERRE`) ;
- **routes** : couche `Roads` de CAIME -> chaque hex de route peint en entier (bloc 2 x 2), couleur
  `roads` de `_settings.bin`, comme les routes des Empires dans leur `tile_map.png` (`routes`).

Sorties :
- `<kit>\\raw_data\\terrain\\campaigns\\wh_dlc05_wood_elves_map_1\\` : le projet (`.terry`, 9 tif,
  `tile_map.png`, 61 `.layer`, `rules.bob`, `lighting\\`) ; un projet existant est d'abord
  sauvegarde dans `05-journal\\terrain-backups\\` ;
- `04-projets\\saison-des-revelations\\terrain-controle\\` : images de controle.

Usage :
    python terrain_wh1_vers_terry.py              # essai a blanc : controles seulement
    python terrain_wh1_vers_terry.py --apply
"""

import argparse
import hashlib
import itertools
import os
import re
import shutil
import struct
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from caime_layers import read_layer                                 # noqa: E402
import props_wh1_vers_layers                                         # noqa: E402
from arbres_wh1 import ArbresWH1, SORTIE_LISTE as SORTIE_LISTE_ARBRES  # noqa: E402
import eclairage_wh1                                                 # noqa: E402
import tuiles_wh1                                                    # noqa: E402
import montagnes_wh1                                                 # noqa: E402
import rivieres_wh1                                                  # noqa: E402
import etangs_wh1                                                    # noqa: E402
import eau_carte                                                     # noqa: E402
import cotes_wh1                                                     # noqa: E402

Image.MAX_IMAGE_PIXELS = None

ATELIER = r"C:\TotalWar-CampaignMap"
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
# (25.09.2026, Saison Expanded, phase 1) la SOURCE (WH1, toujours la même) et la CIBLE (la carte écrite dans le kit, choisie
# par `carte_config` / SAISON_CARTE) sont deux constantes ; pour la bêta, les deux valent wh_dlc05_wood_elves_map_1
import carte_config                                                  # noqa: E402
CARTE_SOURCE = carte_config.CARTE_SOURCE
CARTE = carte_config.CARTE
REFS = os.path.join(ATELIER, "03-references", "saison-des-revelations")
WH1 = os.path.join(REFS, "terrain-wh1", "terrain", "campaigns", CARTE_SOURCE)
SOLS = os.path.join(REFS, CARTE_SOURCE, "couches-wh1-binaire", "layer_ground_types.hex_layer")
IE = os.path.join(KIT, "raw_data", "terrain", "campaigns", "wh3_main_combi_map_1")
PROJET = os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE)
CIBLE_ECLAIRAGE = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE, "lighting")
RELIEF_MAILLAGES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1", "relief_maillages.npy")
# positions des colonies tirées de map_data.esf (construction, 23.09.2026, 23 h 33 : ports à leur hex de WH1)
COLONIES_MAP_DATA = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1", "colonies_map_data.json")
CONTROLE = carte_config.dans_projet("terrain-controle")
REGIONS_KIT = os.path.join(KIT, "raw_data", "db", "campaign_map_regions.xml")

HEX_L, HEX_H = 400, 440
L, H = HEX_L * 8, HEX_H * 8 + 4                   # 3200 x 3524
LARGEUR_MONDE = "266.53"                          # maxx de la zone jouable, comme WH1

A_HAUTEUR, B_HAUTEUR = 0.0002185272, -0.753375    # etalonnage sur les maillages de WH1
# mer visuelle : sea_coast et sea_ocean (index CAIME), la mer de WH1 à 99,9 % et 100 %. Les 85 hex `sea_lake` (14)
# sont de la TERRE dans WH1 (maillages de terrain à 92 %) : ses lacs étaient des plans d'eau posés en objets à leur
# altitude (`props_wh1_vers_layers` en fait des polygones d'eau de WH3). Déclarés en mer, ils devenaient des puits
# jusqu'au niveau de la mer, statue et pierres du lac flottant 4 unités plus haut (22.09.2026, 22 h 15, erreur 85).
SOLS_MER = (13, 15)
SOL_MONTAGNE = 8

# texture de WH1 (index dans son texture_arrays.xml) -> texture de WH3 (index de groupe)
TEXTURES = {
    0: 126,   # sand_b3      sol de foret sombre      -> underlay_forest0
    1: 54,    # grass_a0     herbe olive              -> grass_wet0
    2: 56,    # grass_a2     herbe olive, cailloux    -> grass_wet2
    3: 73,    # mud_a0       boue grise               -> mud_dry0
    4: 99,    # sand_a0      sable clair              -> sand_tropical1
    5: 56,    # grass_a3     herbe olive              -> grass_wet2
    6: 111,   # snow3        roche et neige sale      -> scree_mountain1
    # 7 et 9 : `snow3` et `snow0` de WH3 sortaient en taches d'un blanc eclatant, bords en escalier,
    # dans les collines du sud d'Athel Loren (captures de Charles, 21.09.2026) : eboulis gris
    7: 110,   # snow1        neige                    -> scree_mountain0
    8: 110,   # snow2        roche grise et neige     -> scree_mountain0
    9: 111,   # snow0        neige                    -> scree_mountain1
    10: 127,  # sand_b1      sol olive sombre         -> underlay_forest1
    11: 86,   # sand_b0      sol brun sombre          -> mud_wet2
    12: 66,   # marsh        marais                   -> marsh1
    13: 57,   # grass_a1     herbe olive              -> grass_wet3
    14: 96,   # grass_b0     herbe seche a brindilles -> sand_rocky2
    15: 53,   # grass_dead3  herbe morte              -> grass_tundra3
    16: 53,   # grass_dead2                           -> grass_tundra3
    17: 97,   # grass_dead1                           -> sand_rocky3
    18: 114,  # grass_dead0                           -> scree_sandy0
}
# dans les hex de montagne, les deux textures d'herbe et de sol de foret de WH1 deviennent des
# eboulis : WH1 laissait la roche aux tuiles de falaise, que nous n'avons pas
MONTAGNE = {2: 112, 0: 113}                       # -> scree_mountain2, scree_mountain3
TEXTURE_MER = 98                                  # sand_tropical0, le fond de mer des Empires

COULEUR_TERRE = (223, 180, 145, 255)              # type de tuile `generic`
COULEUR_MER = (83, 141, 213, 255)                 # type de tuile `sea`
MER_COTE, MER_LARGE, TERRE_SOUS_MER = -0.3, -1.4, -0.91   # profil de `sea_height` des Empires
FONDU_COTE = 24                                   # px (3 hex) de la cote au large
OVERLAY = (115, 117, 115, 255)                    # teinte neutre de `color_overlay` des Empires
OVERLAY_MER = (25, 32, 41, 255)                   # eau profonde de `color_overlay_sea`
PAS_D_ARBRE = 255                                 # index de `tree.tif` sans arbre (Empires)
# Masque de corruption (23.09.2026, 04 h 40 ; GUIDE n° 122) : 21 est la valeur la plus fréquente des Empires, mais CA
# peint ses décors de corruption sur des valeurs hautes (médiane 68 à 71) et le jeu ne bascule décors et arbres qu'au-delà
# d'une intensité de 50 : à 21 partout, nos décors du Chaos (cornes, épines, obsidienne de WH1) ne paraîtraient jamais.
# Uniforme, comme WH1 qui basculait une région entière selon sa corruption.
CORRUPTION = 128

# Terre basse (phase 6) : sous ce seuil, la hauteur de la terre est ramenee en douceur dans
# [PLANCHER_TERRE, SEUIL_TERRE_BASSE] ; le plan d'eau est a 0.
PLANCHER_TERRE, SEUIL_TERRE_BASSE = 0.03, 0.35    # (SEUIL_TERRE_BASSE n'est plus employé : erreur 86)
SOUS_MONTAGNE = 0.02                              # le sol passe 2 cm sous le maillage d'une montagne de WH1
FOND_PENTE, FOND_DECALAGE = 1.0058, 340.3         # lf_sea_height_map -> échelle de lf_height_map (moindres carrés, terre)
CULTURE_APERCU = "wh_dlc05_wef_wood_elves"        # culture de l'aperçu de Terry (arbres, décors) : Orion

ARBRES_WH1 = os.path.join(REFS, CARTE_SOURCE, "trees.png")
DB_WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
DB_WH3 = os.path.join(KIT, "raw_data", "db")
# famille d'essences de WH1 -> famille de WH3. WH3 n'a ni essences de saison (automne, hiver : les
# `wef_aut_*`, `wef_win_*` de la mini-campagne), ni `brt_trees_large`, `tree_med`, `marsh_shrubs` :
# on prend la famille generique de meme taille ; c'est la culture de la region qui habille l'arbre
# (elfes sylvains -> chenes `wef_tree_oak_*`, Bretonnie -> arbres bretonniens).
FAMILLES_ARBRES = {
    "brt_trees_large": "tree_large", "tree_large": "tree_large", "tree_med": "tree_large",
    "tree_small": "tree_small", "grass": "grass", "shrubs_grass": "shrubs",
    "wef_wild_grass": "grass", "wef_wild_shrubs_grass": "shrubs",
    "wef_aut_tree_large": "tree_large", "wef_aut_tree_medium": "tree_large", "wef_aut_tree_small": "tree_small",
    # la clairière d'hiver de la Saison des Révélations (erreur 65) : arbres enneigés de WH3
    "wef_win_tree_large": "tree_large_snow", "wef_win_tree_medium": "tree_large_snow",
    "wef_win_tree_small": "tree_small_snow",
    "marsh": "shrubs_marsh", "marsh_shrubs": "shrubs_marsh",
}
ECART_COULEUR_MAX = 16         # couleurs lissees de `trees.png` (5 couleurs, 44 px) : la plus proche
                               # (ecart L1 ; la plus eloignee, (54, 197, 78), est a 11 de (60, 200, 80))

# La clairière d'hiver (erreur 65) : WH1 n'avait pas de masque de neige (le sien est vide) ; sa neige
# était faite de textures (6 à 9 de son texture_arrays.xml) et d'arbres d'hiver, au même endroit. WH3
# fait sa neige par le masque `SnowMask` (Empires : 255 au coeur, 240 à 254 sur les bords, aucune
# texture de neige dessous) : on le peint là où WH1 avait ses textures de neige et ses arbres d'hiver.
TEXTURES_NEIGE_WH1 = (6, 7, 8, 9)
COULEURS_HIVER_WH1 = ((50, 90, 20), (30, 50, 10))      # wef_win_tree_small, wef_win_tree_large/medium
BORD_NEIGE = 3                                           # px (1,5 hex) de fondu au bord de la neige
# (24.09.2026, 04 h 10 ; vidéos WH1 / WH3 de Charles : la clairière d'hiver « bleu pâle, arbres épars givrés » dans WH3,
# « forêt sombre dense, neige turquoise scintillante » dans WH1 ; mesure : WH3 plus clair et deux fois moins saturé) : le
# post-traitement de neige de WH3 blanchit le sol et givre les arbres ; intensité ramenée de 110 à 70.
NEIGE_COEUR = 70                                         # intensité du masque au cœur de la neige (givre ; 255 = CA)

ROUTES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "couches", "layer_roads.hex_layer")
SLOTS = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "couches-slots", "layer_town_slots.hex_layer")
COULEUR_ROUTE = (93, 66, 24, 255)                 # type de tuile `roads` (_settings.bin)

# La côte (22.09.2026, 19 h, Charles : « les côtes sont en pixels, en carrés ») : les Empires bordent toute leur mer
# d'une bande d'un hex (2 px de tile_map, côté terre) de types de côte, que BOB change en falaises et rivages :
# `cliff_gen` (253, 3, 1) et `sea_coast` (255, 255, 0) (_settings.bin ; 88 500 et 19 852 px aux Empires). Sans elle,
# la limite terre / mer reste un escalier d'hex. On la peint là où WH1 avait sa côte (`tuiles_wh1`) : rivage où il
# avait ses tuiles `sea_coast` (et ses embouchures), falaise où il avait ses falaises (`cliff_*`).
COULEUR_FALAISE = (253, 3, 1, 255)
COULEUR_RIVAGE = (255, 255, 0, 255)
LARGEUR_COTE = 2                                  # px de tile_map (un hex), comme les Empires
FAMILLES_RIVAGE_WH1 = ("sea_coast", "river_mouth")
# Les rivières de WH1 (`rivieres_wh1.py` : lit dans le relief, eau en maillages drapés au matériau d'eau de la mer, comme
# les rivières des Empires). Vérifiées dans Terry le 23.09.2026 à 00 h 16 (ruisseau continu, drapé, eau de WH3).
RIVIERES_WH1 = True
# tuiles de WH1 dont le sol n'est pas reconstitué chez nous (leurs propres maillages : rivières, falaises, côte)
FAMILLES_SOL_INCONNU_WH1 = ["river", "river_stream", "river_start", "river_crossing", "river_confluence", "river_mouth",
                            "cliff_base", "cliff_custom", "cliff_inland_custom", "cliff_inland_custom_passable",
                            "cliff_end_anchors", "sea", "sea_coast"]
PORTEE_COTE_WH1 = 4                               # cases : la côte de WH1 est décalée d'une case vers la mer
# La côte de WH1 (23.09.2026, 01 h 30 ; Charles, dans Terry : « les bords autour de la mer… pixelisés… ça fait des
# carrés… il n'y a pas moyen de rendre ça beaucoup plus naturel et joli ? »). Relevé ce soir-là : dans WH1, les plages
# (`sea_coast`, 95 poses) et les tuiles de mer sont fondues dans ses maillages de terre et de mer (0 % de leur emprise
# hors de ces maillages) ; sa côte est la frontière entre les deux, au pixel (bords de case et diagonales des tuiles
# `*_tri`), avec par-dessus ses 233 falaises sculptées (`cliff_custom`, `montagnes_wh1`). Chez nous, la mer était faite
# d'hex entiers (`mer_de_wh1`), le relief sautait du sol de la terre (>= 0,03) au fond (<= -0,3) à chaque bord de case,
# et la bande de côte de WH3 (`cotes`) y posait ses tuiles de falaise et de rivage : des marches et des carrés de sable.
# Avec COTE_WH1 : mer visuelle = pixels des maillages de mer de WH1, fond = ces maillages (dans `sea_height` ; `height`
# porte la surface de l'eau en mer depuis le 23.09.2026, 03 h 40, erreur 113), une case de tile_map est de la mer dès qu'un de ses
# pixels l'est, plus de bande de côte de WH3, et sous l'eau la texture de WH1 (son `global_blend`) au lieu du sable
# tropical de WH3. La mer logique (hex de la carte CAIME) ne change pas.
COTE_WH1 = True
# Niveau de l'eau de mer (la valeur de `height` sur la mer chez CA : 0,000 en médiane aux Empires) et écart minimal de
# `sea_height` sous la terre (au moins 1,025 chez CA). Voir `rasters`, erreur 113.
# 04 h 40 : 1,0 était au ras du minimum de CA (1,025) ; un « rectangle vert » translucide suivait la caméra au dézoom
# (Charles) : on prend l'écart médian de CA sous la terre.
NIVEAU_EAU, SOUS_TERRE_MER = 0.0, 3.0
# La mer visible (23.09.2026, 16 h 50, session du rendu ; capture de Charles en jeu, Bordeleaux, pack de 15 h 37 : « il n'y
# a pas d'eau… il manque l'eau de la mer… des problèmes avec les bords »). Mesures (brouillon `mer_ca_nous.py`) : chez CA
# (Empires, mer de tile_map), le fond est à -0,40 à moins d'une demi-unité de la côte, -0,6 à 1-2 u, -0,88 à 2-4 u, -0,92 à
# -0,99 au large (p10 -1,4) ; chez nous, le fond de WH1, plat à -0,5 (-0,18 près des côtes) : l'eau de campagne de WH3
# s'estompe avec la profondeur, notre mer presque transparente montrait le fond (vert). Et la terre des cases de mer avait son
# fond 3 unités sous elle : seules taches d'eau profonde, sombres, en escalier le long de la côte.
# MER_PROFONDE : fond = min(fond de WH1, profil de CA selon la distance à la terre), sauf les hauts-fonds et bancs de WH1
# (fond au-dessus de HAUT_FOND à plus d'une demi-unité de la côte), gardés ; CASES_DE_MER : la terre d'une case de mer a pour
# fond la terre elle-même.
MER_PROFONDE, CASES_DE_MER = True, True
# La couleur de la mer (`color_overlay_sea`) : celle de WH1 (`entites_wh1.couleur_mer_wh1`), 13 / 25 / 30 en moyenne, le
# tiers de celle des Empires (40 / 70 / 76, projet du kit) : une mer profonde en serait presque noire. Nuances de WH1 gardées,
# luminosité de CA (erreur 96 : un réglage de rendu de WH1 ne se transpose pas en valeurs).
COULEUR_MER_CA = (40.0, 70.0, 76.0)
# LA MER JOUABLE (23.09.2026, 18 h 45, session du rendu ; pack de 17 h 42 avec la mer approfondie, Charles : « très
# moche » : toujours pas d'eau, un sol plat texturé, des bandes bleues en escalier au rivage, le carré au dézoom). Mesures
# refaites sur le projet des Empires (brouillons `height_mer_ie2.py`, `height0_ie.py`, `cote_ie.py`) : `height` n'y vaut 0
# que sur 14,7 % de la mer, à 79 % dans la bande des 5 % du bord de la carte (les marges hors jeu) ; sur la mer jouable il
# est positif et continu avec la terre (0,64 de part et d'autre de la côte, 1,0 au large), et la profondeur
# height - sea_height y va de 1,05 à la côte à 1,9 au large. Notre mer entière avait height = 0 : codée comme une marge
# morte (la mesure de l'erreur 113, « 0,000 en médiane », venait de ces marges). Et la terre voisine de la mer gardait un
# sea_height 3 unités sous elle (les bandes d'eau sombre en escalier : le jeu la traite par cases, voire par hex).
HAUTEUR_SUR_MER = 0.02         # jamais 0 ; à peine au-dessus du niveau de l'eau (nos côtes basses, 0,02 à 0,27, au-dessus)
PROF_COTE, PROF_LARGE, ECHELLE_PROF = 1.05, 1.9, 2.5    # profondeur height - sea_height des Empires, d en unités
TERRE_PRES_DE_LA_MER = 8       # px (deux cases) : cette terre a sea_height = height (aucune eau cachée dessous)
# LE FOND SOUS L'EAU PARTOUT (23.09.2026, 19 h 40, session du rendu ; Charles, pack de 19 h 02 : « toujours pas d'eau »).
# Mesures (brouillons `bc6h.py`, décodeur du relief compilé ; `poses_tuiles.py`, `tuiles_mer_bornes.py`,
# `mer_references.py`) : `tile_list.bin` donne à chaque pose de tuile ses hauteurs mini et maxi, que BOB calcule sur
# `sea_height` (emprise de la tuile et une case de bord, écart médian 1 cm). Tuiles de mer au maxi au-dessus de 0 :
# Empires 0,3 %, The Old World (ChaosRobie) 0 %, nous 73,8 % : CASES_DE_MER et TERRE_PRES_DE_LA_MER mettaient le fond de la
# terre côtière à la hauteur de la terre, et le jeu dessinait ces tuiles en sol plat, sans eau. Sur les quatre cartes où
# l'eau se dessine (Empires, prologue, Chaos, The Old World), `sea_height` reste sous 0 partout, même sous la terre
# (Empires -0,91, Chaos -0,5, The Old World -1 ou 0). Donc : fond au plus à FOND_MAX partout ; la terre d'une case de mer
# (la côte de WH1 passe au pixel, la case entière est de la mer) a pour fond FOND_MAX : un rivage noyé de quelques
# centimètres, que le jeu dessine en eau peu profonde ; profil de la mer en valeurs absolues sous le niveau de l'eau (0),
# comme aux Empires (-0,40 à moins d'une demi-unité de la côte, -0,95 au large), un peu moins raide au rivage.
FOND_SOUS_ZERO = True
FOND_MAX = -0.1
PROF_ABS_COTE, PROF_ABS_LARGE, ECHELLE_PROF_ABS = 0.15, 0.97, 2.2
HAUT_FOND = -0.2
# LA CÔTE DOUCE (23.09.2026, 21 h 55, session du rendu ; Charles, pack de 21 h 43 où l'eau est enfin là : « les bords sont
# tout pixelisés, je veux que ce soit très joli » ; la construction, capture de Mousillon : « la terre finit en marches
# d'escalier carrées, à angles droits, avec un petit bord vertical sombre au-dessus de l'eau »). FOND_SOUS_ZERO mettait à
# FOND_MAX la terre des cases de mer, et à la terre - SOUS_TERRE_MER le fond de la terre voisine. Or le jeu dessine
# `sea_height` sur les cases de mer (4 x 4 px), et aussi sur la terre proche (chaîne 2, pack de 17 h 42 : « bandes bleues
# en escalier au rivage », disparues avec TERRE_PRES_DE_LA_MER à la chaîne 3). D'où une côte qui suit la grille des cases,
# et un mur entre la terre et le fond. La supposition de 19 h 40 (une tuile de mer au maximum au-dessus de 0 ne dessine pas
# d'eau) n'a jamais été vérifiée seule : l'eau manquait faute de plans d'eau (MER_PLANS). Désormais : toute la terre à
# moins de TERRE_COTE_PX px de la mer, cases de mer comprises, a pour fond la terre elle-même, et le plan d'eau à y = 0
# coupe la côte au pixel, sur le tracé de WH1. La mer descend en pente douce depuis le bord de l'eau (PROF_DOUCE_BORD sous
# 0, jusqu'à PROF_ABS_LARGE, échelle ECHELLE_PROF_DOUCE), au moins EAU_MIN_MER sous l'eau.
COTE_DOUCE = True
# LES CASES DE CÔTE EN TERRE (23.09.2026, 22 h 55, session du rendu ; pack de 22 h 47 : côte en courbes à l'estuaire de
# Mousillon, mais « une grande nappe plate, pâle et opaque, à bords droits » au sud-ouest, et une eau laiteuse). Mesures
# (brouillon `diag_nappe_pale.py`) : la mer n'y est pas peu profonde (96 cm en médiane). Mais 502 poses de tuiles de mer sur
# 664 avaient un maximum > 0 (0 à la chaîne 5), par leur case de bord, de la terre à sea_height = height : le jeu les dessine
# alors en sol plat (height = HAUTEUR_SUR_MER), comme le « sol plat texturé » de la chaîne 3. La supposition de 19 h 40
# était donc juste. Désormais : une case n'est de la mer que si ses 16 pixels le sont ; une case mixte est de la TERRE,
# dessinée depuis `height`, qui vaut le fond (sous 0) sur ses pixels de mer, et le plan d'eau coupe la côte au pixel ; sous
# les cases de mer et leur case de bord, `sea_height` reste sous 0 (maximum des tuiles de mer <= 0).
COTE_CASES_DE_TERRE = True
# LA LISIÈRE DES CASES (25.09.2026, 00 h, chaîne 13 bis ; fichiers compilés de la chaîne 13 décodés, brouillons
# `scratchpad\compile13\`). Le jeu tesselle le sol depuis `full_height_map` (R = height, G = sea_height), et le shader du
# sol jette chaque pixel dont la case de `tile_mask` et ses 8 voisines à `g_clip_threshold` ne sont pas de la terre : autour
# des cases de terre, le sol est donc dessiné aussi sur les cases de mer pleines, où height valait HAUTEUR_SUR_MER (+0,02) :
# une lisière au-dessus de l'eau qui suit les cases de 0,33 u (golfe du Bidouze : 78 u² en chaîne 12, 64 en chaîne 13 ; toute
# la carte 182 u²), l'escalier vu de loin. Sur les cases de mer pleines à moins de PRES_DES_TERRES_PX d'une case de terre,
# height prend le fond (sous l'eau), comme sur la mer des cases mixtes : la ligne d'eau devient celle du relief.
MER_SOUS_L_EAU_PRES_DES_TERRES = True
ARBRES_CENTRE_COLONIE = 0.5                        # u : pas d'arbre de WH1 si près du centre d'une colonie (chaîne 14)
# rayon de découpe du moteur inconnu : au moins 0,5 u (sans quoi les cases de route, tile_mask 0, seraient des trous ;
# brouillon `compile13\rayon_routes.py`) ; on prend 2 u, quatre fois cette borne. Distance en croix (`distance_a`) : 24 px en
# ligne droite, 17 px (1,4 u) en diagonale.
# (25.09.2026, 02 h 30) essayé à 12 px (1 u) contre la nappe gris-blanc de la mer sous le brouillard de guerre (vidéo de
# Charles de 00 h 58 : là où height passe sous l'eau, le jeu y montre le plan d'eau pâle ; enquête
# `scratchpad\peaufinage_mer_brouillard\`) ; revenu à 2 u à 03 h avant la chaîne 15 (la construction : le contrôle validé
# de la 13 bis est « 0 px au-dessus de 0 à moins de 2 u », rien ne prouve une découpe à moins d'1 u) ; la nappe est d'abord
# attaquée par le matériau de la mer (C4, session IA : sea_depth_max_point 0,6, foam_falloff 20). Une seule affectation
# (erreur 240).
# (25.09.2026, 15 h, chaîne 17, construction ; vidéo de Charles de 14 h 46 : le long de TOUTES les côtes, une bande de mer
# noire, lisse, sans vagues ni reflet, coupée net du large, où le reflet du soleil s'arrête ; sous le brouillard, la même
# bande pâle qu'à 00 h 58). La bande a la largeur de ce réglage : le sol passé sous l'eau y est dessiné avec l'eau du sol,
# le large par la mer. Ramené à 12 px (1 u), trois fois la borne mesurée de la découpe (0,5 u, routes). CONTRÔLE ANNONCÉ
# (erreur 240) : sur le compilé, 0 px de sol au-dessus de 0 à moins d'1 u d'une case de terre, et en jeu pas d'escalier
# de loin sur les côtes (golfe du Bidouze, Mousillon, Bordeleaux) ; sinon retour à 24.
PRES_DES_TERRES_PX = 12                            # px (1 u)
TERRE_COTE_PX = 12                                 # px (3 cases, 1 u) : la terre dont le fond est la terre elle-même
PROF_DOUCE_BORD, ECHELLE_PROF_DOUCE = 0.02, 1.2    # fond au bord de l'eau ; échelle de la pente (unités)
EAU_MIN_MER = 0.01                                 # un pixel de mer reste au moins 1 cm sous l'eau
# Le rivage naturel (23.09.2026, 01 h 35 ; vu dans Terry après la côte de WH1) : la frontière des maillages de WH1 suit
# les bords de ses tuiles (cases de 0,33 unité, angles droits) et le relief y saute de la terre (0,05 à 0,3) au fond
# (-0,2 à -0,5) en un ou deux pixels : dans WH3, une berge verticale en marches, texture d'herbe étirée. On adoucit le
# relief sur une bande étroite de part et d'autre de la côte (fondu progressif sur RIVAGE_BANDE px) : la ligne d'eau
# devient une courbe qui suit le tracé de WH1 à l'échelle de l'hex, et la berge une pente. Flou : trois moyennes de
# rayon RIVAGE_RAYON (écart-type ≈ 2,8 px). Les objets gardent le sol de WH1 comme référence (`hauteur_wh1`) et sont
# reposés sur le sol adouci par les règles habituelles.
RIVAGE_BANDE, RIVAGE_RAYON = 10, 2
# LE RIVAGE PARTOUT AU RELIEF ADOUCI (23.09.2026, 23 h 10, session du rendu ; Charles, captures de 22 h 56 : « peaufine les
# côtes, qu'elles soient plus naturelles »). `rivage_naturel` noyait la terre que l'adoucissement passe sous l'eau, mais
# gardait en mer le fond qu'il sort de l'eau : là, le rivage restait le bord des maillages de WH1 (cases de 0,33 u, angles
# droits). Désormais ce fond sorti de l'eau devient de la terre : partout, le rivage est la courbe où le relief adouci passe
# sous l'eau.
RIVAGE_EMERGES = True
# LA TERRE DE WH1 AU BORD DE L'EAU (24.09.2026, chaîne 12 ; Charles, 18 h 55 : « fais exactement comme dans Warhammer 1 au
# niveau du découpage de la côte »). Avec le découpage de WH1 (`cotes_wh1.LISSAGE = False`), l'adoucissement ne touche plus
# que le fond de la mer (qui remonte en pente douce vers la côte, sous l'eau) : la terre garde son relief de WH1 et le trait
# de côte ne bouge plus (ni terre noyée ni fond sorti de l'eau, qui refermait les bras de mer et effaçait les bancs de
# sable des deltas : 1 944 px de mer perdus à la chaîne 11, dont l'estuaire près d'Yremy et la baie au sud de Brionne).
# RETIRÉ (24.09.2026, 22 h 50, chaîne 13 ; capture de Charles, 22 h 40, golfe nord du Bidouze : côte en escalier à gros crans,
# murs sombres). La terre de WH1 finit à +0,14 (p10 +0,04) au-dessus d'un fond à -0,30 (brouillon `cote_profil_wh1.py`) :
# ce mur d'un pixel, WH1 le dessine avec les arêtes de ses tuiles, WH3 le simplifie de loin (LOD de BOB) en crans de plusieurs
# hex. La berge redevient une pente (terre et fond adoucis ensemble, ligne d'eau sur la courbe 0), comme à la chaîne 11 ;
# les deltas de WH1 restent tels quels (`rivage_naturel(fige=...)`, `cotes_wh1.GARDER_DELTAS`).
RIVAGE_TERRE_WH1 = False

# (type Terry, nom de fichier, taille, mode) ; PatchVisibilityMask n'a pas de calque chez CA
CARTES = [("Height", "height", (L, H)), ("HeightSea", "sea_height", (L, H)),
          ("HeightShroud", "height_shroud", (L // 2, H // 2)), ("BlendCampaign", "blend", (L, H)),
          ("ColorOverlay", "color_overlay", (L, H)), ("ColorOverlaySea", "color_overlay_sea", (L, H)),
          ("CampaignTree", "tree", (L // 4, (H + 3) // 4)),
          ("CorruptionMask", "corruption_mask", (L // 4, (H + 3) // 4)),
          ("SnowMask", "snow_mask", (L // 4, (H + 3) // 4))]
OPACITE = {"ColorOverlay": "0.5"}


def ident(graine):
    """Identifiant Terry (15 chiffres hexadecimaux, commence par 1), stable d'une generation a
    l'autre : les noms des fichiers en dependent."""
    return "1" + hashlib.sha1(f"{CARTE}:{graine}".encode()).hexdigest()[:14]


def dds(chemin, dtype, forme, entete=128):
    brut = open(chemin, "rb").read()
    return np.frombuffer(brut, dtype=dtype, count=forme[0] * forme[1], offset=entete).reshape(forme)


def hex_de_pixel(largeur, hauteur, pas):
    """Pour chaque pixel d'un raster (ligne 0 = nord) a `pas` px par hex : colonne et ligne de
    l'hex CAIME (ligne 0 = sud, colonnes impaires decalees d'un demi-hex)."""
    y, x = np.mgrid[0:hauteur, 0:largeur]
    col = np.clip(x // pas, 0, HEX_L - 1)
    depuis_bas = (hauteur - 1) - y
    lig = (depuis_bas - (pas // 2) * (col & 1)) // pas
    return col, np.clip(lig, 0, HEX_H - 1)


def distance_a(masque, portee):
    """Distance (en px, jusqu'a `portee`) de chaque pixel a `masque`, par dilatations successives."""
    d = np.full(masque.shape, portee, np.float32)
    front = masque.copy()
    d[front] = 0
    for k in range(1, portee):
        voisin = front.copy()
        voisin[1:, :] |= front[:-1, :]
        voisin[:-1, :] |= front[1:, :]
        voisin[:, 1:] |= front[:, :-1]
        voisin[:, :-1] |= front[:, 1:]
        neufs = voisin & ~front
        d[neufs] = k
        front = voisin
    return d


def lignes_db(db, table):
    xml = open(os.path.join(db, table + ".xml"), encoding="utf-8").read()
    return [dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
            for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", xml, re.S)]


def famille(tree_id):
    return re.sub(r"_\d+$", "", tree_id)


def arbres(mer2):
    """`tree.tif` depuis `trees.png` de WH1 : index de palette de la famille de WH3, 255 ailleurs."""
    couleur_wh1 = {}
    for r in lignes_db(DB_WH1, "campaign_tree_ids"):
        couleur_wh1.setdefault((int(r["colour_r"]), int(r["colour_g"]), int(r["colour_b"])), set()).add(famille(r["tree_id"]))
    couleur_wh3 = {}
    for r in lignes_db(DB_WH3, "campaign_tree_ids"):
        couleur_wh3.setdefault(famille(r["tree_id"]), (int(r["colour_r"]), int(r["colour_g"]), int(r["colour_b"])))
    pal = palette_de(next(n for n in os.listdir(IE) if ".tree." in n))
    index_de = {}
    for k in range(len(pal) // 3):
        index_de.setdefault(tuple(pal[3 * k:3 * k + 3]), k)

    img = np.array(Image.open(ARBRES_WH1).convert("RGBA"))
    assert img.shape[:2] == mer2.shape, (img.shape, mer2.shape)
    plein = img[..., 3] > 0
    # orientation : `trees.png` et `tree.tif` ont le nord en haut ; controle par la mer, ou WH1 ne
    # plante rien (a l'envers, les arbres tomberaient dans l'estuaire de la cote ouest)
    dans_mer, dans_mer_inverse = (plein & mer2).mean() / plein.mean(), (plein[::-1] & mer2).mean() / plein.mean()
    if dans_mer > dans_mer_inverse:
        raise SystemExit(f"trees.png semble a l'envers : {dans_mer:.1%} des arbres en mer, {dans_mer_inverse:.1%} retourne")
    sortie = np.full(mer2.shape, PAS_D_ARBRE, np.uint8)
    connues = np.array(sorted(couleur_wh1))
    bilan = {}
    for rgba in np.unique(img[plein].reshape(-1, 4), axis=0):
        rgb = tuple(int(x) for x in rgba[:3])
        proche = connues[np.abs(connues - rgb).sum(1).argmin()]
        if np.abs(proche - rgb).sum() > ECART_COULEUR_MAX:
            raise SystemExit(f"trees.png : couleur {rgb} absente de campaign_tree_ids de WH1")
        familles1 = couleur_wh1[tuple(int(x) for x in proche)]
        # 22.09.2026, 22 h : le jeu reçoit la liste des arbres de WH1 elle-même (positions, essences, modèles :
        # `arbres_wh1.liste_wh1`, embarquée par build_pack.py) ; tree.tif ne sert plus qu'à BOB et à l'aperçu de
        # Terry : familles de WH3 de même nature (chênes, petits arbres, herbes), que la base du kit sait dessiner
        # (les familles « porteuses » n'y ont aucune variante : Terry n'affichait aucun arbre)
        cibles = {FAMILLES_ARBRES.get(f) for f in familles1}
        if None in cibles or len(cibles) != 1:
            raise SystemExit(f"trees.png : familles {sorted(familles1)} sans correspondance unique ({cibles})")
        cible = cibles.pop()
        index = index_de.get(couleur_wh3.get(cible))
        if index is None:
            raise SystemExit(f"famille {cible} : couleur absente de la palette de tree.tif")
        m = plein & (img[..., :3] == rgba[:3]).all(-1)
        sortie[m & ~mer2] = index
        bilan[cible] = bilan.get(cible, 0) + int((m & ~mer2).sum())
    print(f"  arbres : {int((sortie != PAS_D_ARBRE).sum())} px ({(sortie != PAS_D_ARBRE).mean():.1%}) ; "
          f"en mer dans WH1 : {dans_mer:.2%} (retourne : {dans_mer_inverse:.2%}) ; {bilan}")
    return sortie


def neige(melange_wh1, mer2, eau=None):
    """`SnowMask` (800 x 881) : 255 sous les textures de neige et les arbres d'hiver de WH1, fondu de
    BORD_NEIGE px (255 - 5 par px, comme les bords des Empires), 0 ailleurs, en mer et sur l'eau `eau` (raster du relief :
    étangs et rivières visibles ; 23.09.2026, 18 h 50, Charles : « le lac dans la partie enneigée, il n'y a pas d'eau
    dedans » : le givre de la neige de WH3, un post-traitement, recouvrait l'eau des deux étangs de la clairière d'hiver)."""
    tex = np.isin(melange_wh1, TEXTURES_NEIGE_WH1)
    h2, w2 = mer2.shape
    tex = tex[:h2 * 4, :w2 * 4].reshape(h2, 4, w2, 4).any(axis=(1, 3))
    a = np.array(Image.open(ARBRES_WH1).convert("RGBA"))[..., :3]
    hiver = np.zeros(mer2.shape, bool)
    for c in COULEURS_HIVER_WH1:
        hiver |= (a == c).all(-1)
    coeur = (tex | hiver) & ~mer2
    d = distance_a(coeur, BORD_NEIGE + 1)
    m = np.where(coeur, 255, np.where(d <= BORD_NEIGE, 255 - 5 * d, 0)).astype(np.float64)
    # WH1 n'avait pas de neige plaquée sur le terrain (aucun post-traitement dans ses éclairages) : sa neige était la
    # texture du sol (gris-brun) et les arbres d'hiver. À 255, celle de WH3 couvrait tout d'un blanc-cyan uniforme
    # (Charles, 23.09.2026, 04 h 30 : « pas du tout comme WH1 ») : elle ne fait plus que givrer (`NEIGE_COEUR`).
    m = np.round(m * NEIGE_COEUR / 255.0).astype(np.uint8)
    m[mer2] = 0
    if eau is not None:
        e2 = eau[:h2 * 4, :w2 * 4].reshape(h2, 4, w2, 4).any(axis=(1, 3))
        print(f"  neige : {int((e2 & (m > 0)).sum())} cases d'eau (étangs, rivières) sans givre")
        m[e2] = 0
    print(f"  neige : {int(coeur.sum())} px au coeur (textures {int(tex.sum())}, arbres d'hiver {int(hiver.sum())}), "
          f"{int((m > 0).sum())} px avec le fondu")
    return m


# LA CORRUPTION À LA MANIÈRE DE CA (25.09.2026, 04 h 45, chaîne 16 ; Charles : dans les terres des morts-vivants « les mêmes
# effets que sur les autres cartes de Warhammer 3 » ; enquête `scratchpad\enquete_corruption\`). Le sol corrompu (paliers
# `vampire_creep0` à 3), les arbres et décors de corruption sont posés par le moteur d'après la corruption de la région
# ET ce masque, fixe et commun à toutes les corruptions. Le nôtre valait 128 partout : Mousillon uniformément sombre, bord
# net à la frontière. Celui de CA (dds du jeu) est un dégradé autour de chaque colonie : CORRUPTION_PROFIL (médianes des
# Empires selon la distance en unités), étiré de CORRUPTION_ETIREMENT (nos colonies sont moins serrées : 0,75 contre 1,35 pour
# 1 000 u² de terre), bruit lisse de ~8 u (écart-type CORRUPTION_BRUIT, graine fixe), CORRUPTION_MER en mer.
CORRUPTION_PROFIL = ((0.5, 198), (1.5, 187), (2.5, 169), (3.5, 148), (4.5, 127), (5.5, 113), (6.5, 103), (7.5, 97),
                     (9.0, 91), (11.0, 82), (13.0, 75), (15.0, 68), (17.0, 63), (19.0, 60), (22.5, 57), (27.5, 53),
                     (35.0, 49), (50.0, 48), (70.0, 48))
CORRUPTION_ETIREMENT = 1.3
CORRUPTION_BRUIT = 11.6
CORRUPTION_MER = 34
CORRUPTION_CA = True


def masque_corruption(mer):
    """`CorruptionMask` (L // 4 x (H + 3) // 4, ligne 0 au nord) au profil de CA autour de nos colonies ; CORRUPTION
    uniforme si CORRUPTION_CA est faux ou les colonies inconnues."""
    h2, w2 = (H + 3) // 4, L // 4
    if not CORRUPTION_CA or not os.path.exists(COLONIES_MAP_DATA):
        return np.full((h2, w2), CORRUPTION, np.uint8)
    import json
    pos = list(json.load(open(COLONIES_MAP_DATA, encoding="utf-8"))["keys"].values())
    pas = L / float(LARGEUR_MONDE)
    r3 = 3 ** 0.5 / 2
    gi, gj = np.mgrid[0:h2, 0:w2].astype(np.float32)
    d = np.full((h2, w2), np.inf, np.float32)
    for x, z in pos:
        i, j = ((H - 1.5) - z * r3 * pas) / 4.0, (x * pas - 0.5) / 4.0
        d = np.minimum(d, np.hypot(gi - i, gj - j))
    du = d / (pas / 4.0) / CORRUPTION_ETIREMENT
    px_, py_ = np.array(CORRUPTION_PROFIL, np.float64).T
    m = np.interp(du, px_, py_)
    rng = np.random.default_rng(1225)
    ech = 24                                                   # px du masque (3 px par unité : 8 u)
    g = rng.normal(0, 1, (h2 // ech + 3, w2 // ech + 3)).astype(np.float32)
    b = np.asarray(Image.fromarray(g, "F").resize(((w2 // ech + 3) * ech, (h2 // ech + 3) * ech), Image.BICUBIC))[:h2, :w2]
    m = m + b / (b.std() + 1e-6) * CORRUPTION_BRUIT
    mer2 = mer[:h2 * 4, :w2 * 4].reshape(h2, 4, w2, 4).mean(axis=(1, 3)) > 0.5
    m = np.where(mer2, CORRUPTION_MER, m)
    m = np.clip(np.round(m), 0, 255).astype(np.uint8)
    print(f"  corruption à la manière de CA : {len(pos)} colonies, terre moyenne {m[~mer2].mean():.1f}, "
          f">= 50 : {(m[~mer2] >= 50).mean():.1%}")
    return m


def routes(mer2, col2, lig2):
    """Les hex de route de CAIME, **peints en entier** (hors mer).

    Grammaire relevee sur les Empires (21.09.2026, 21 h 30) : 30 283 hex de route sur 30 400 y sont
    un bloc 2 x 2 plein ; les segments horizontaux et verticaux ont des longueurs paires. Un premier
    trace aminci a un pixel (squelette) laissait 2 872 trous que BOB ne savait couvrir d'aucune tuile
    (« area painted in tile map likely doesn't match the tile shape »)."""
    _, val = read_layer(ROUTES)
    route_hex = (np.asarray(val).reshape(HEX_H, HEX_L) > 0)
    # un hex de route reste entier : il n'en porte plus dès qu'une de ses cases est de la mer (COTE_WH1 : la mer est
    # tracée à la case, et un demi-hex de route n'a pas de tuile dans BOB)
    mer_h = np.zeros((HEX_H, HEX_L), bool)
    mer_h[lig2[mer2], col2[mer2]] = True
    masque = route_hex[lig2, col2] & ~mer_h[lig2, col2]
    print(f"  routes : {int(route_hex.sum())} hex -> {int(masque.sum())} px")
    return masque


def voisins_hex(masque_hex):
    """Hex (grille CAIME, ligne 0 au sud, colonnes impaires décalées d'un demi-hex vers le haut) dont au moins un des
    six voisins est dans `masque_hex`."""
    m = masque_hex
    v = np.zeros_like(m)
    v[1:, :] |= m[:-1, :]
    v[:-1, :] |= m[1:, :]
    impaires = (np.arange(m.shape[1]) & 1).astype(bool)
    for dc in (-1, 1):
        dec = np.zeros_like(m)                         # colonne voisine, même ligne
        if dc == 1:
            dec[:, :-1] = m[:, 1:]
        else:
            dec[:, 1:] = m[:, :-1]
        v |= dec
        # colonne impaire (haute) : voisins aux lignes r et r + 1 ; colonne paire (basse) : r - 1 et r
        haut = np.zeros_like(m)
        haut[:-1, :] = dec[1:, :]
        bas = np.zeros_like(m)
        bas[1:, :] = dec[:-1, :]
        v |= np.where(impaires[None, :], haut, bas)
    return v


def cotes(mer_hex, col2, lig2):
    """(falaise, rivage) : masques de tile_map (800 x 881) de la bande de côte, à la manière des Empires : les hex de
    terre voisins d'un hex de mer, peints en entier (2 x 2 px), comme leur mer (une bande tracée en pixels donnait 148
    « Failed to find tile » dans BOB, 22.09.2026, 19 h 17). Chaque hex prend le type de côte de WH1 le plus proche
    (majorité de ses pixels) ; hors de portée d'une côte de WH1 (lacs, bords), rien n'est peint."""
    bande_hex = ~mer_hex & voisins_hex(mer_hex)
    mer2 = mer_hex[lig2, col2]
    bande = bande_hex[lig2, col2]
    fam = tuiles_wh1.familles_par_case(ordre=["cliff_base", "cliff_custom", "sea_coast", "river_mouth"])
    if fam.shape != mer2.shape:
        raise SystemExit(f"grille des tuiles de WH1 {fam.shape} et tile_map {mer2.shape} différentes")
    rivage_wh1 = np.isin(fam, FAMILLES_RIVAGE_WH1)
    falaise_wh1 = np.array([[f.startswith("cliff") for f in ligne] for ligne in fam])
    d_riv = distance_a(rivage_wh1, PORTEE_COTE_WH1 + 1)
    d_fal = distance_a(falaise_wh1, PORTEE_COTE_WH1 + 1)
    # vote par hex : pixels plus près d'un rivage de WH1, d'une falaise, ou d'aucune côte à portée
    ident_hex = (lig2 * HEX_L + col2)[bande]
    n = HEX_L * HEX_H
    vote_riv = np.bincount(ident_hex, weights=((d_riv < d_fal) & (d_riv <= PORTEE_COTE_WH1))[bande], minlength=n)
    vote_fal = np.bincount(ident_hex, weights=((d_fal <= d_riv) & (d_fal <= PORTEE_COTE_WH1))[bande], minlength=n)
    vote_rien = np.bincount(ident_hex, weights=(np.minimum(d_riv, d_fal) > PORTEE_COTE_WH1)[bande], minlength=n)
    type_hex = np.where((vote_rien >= vote_riv) & (vote_rien >= vote_fal), 0, np.where(vote_riv > vote_fal, 2, 1))
    t = type_hex[lig2 * HEX_L + col2]
    falaise = bande & (t == 1)
    rivage = bande & (t == 2)
    print(f"  côte : {int(bande_hex.sum())} hex de bande ({int(bande.sum())} px) ; falaise {int(falaise.sum())} px, "
          f"rivage {int(rivage.sum())} px, sans côte de WH1 à portée {int((bande & (t == 0)).sum())} px")
    return falaise, rivage


def regions_de_la_carte():
    xml = open(REGIONS_KIT, encoding="utf-8").read()
    cles = []
    for bloc in re.findall(r"<campaign_map_regions\b.*?</campaign_map_regions>", xml, re.S):
        if f"<campaign_map>{CARTE}</campaign_map>" in bloc:
            cles.append(re.search(r"<region>([^<]+)</region>", bloc).group(1))
    return sorted(set(cles))


def mer_de_wh1(col8, lig8):
    """Hex de mer du visuel : ceux dont plus de la moitié des pixels sont de la mer dans WH1 (ses maillages de mer, hors de
    ses maillages de terrain). La mer logique (hex `sea_coast` / `sea_ocean`) s'arrêtait un hex trop tôt tout le long
    de la côte : cette bande, de l'eau dans WH1, devenait chez nous de la terre sous le niveau de l'eau, relevée en
    plateau avec toute la plaine côtière ; vue de Terry, des plaques de sol plates qui flottent au bord de l'eau
    (22.09.2026, 22 h 30, erreur 86)."""
    terre = np.load(RELIEF_MAILLAGES)
    merw = np.load(os.path.join(os.path.dirname(RELIEF_MAILLAGES), "mer_maillages.npy"))
    eau = np.isfinite(merw) & ~np.isfinite(terre)
    idx = (lig8 * HEX_L + col8).ravel()
    n = np.bincount(idx, minlength=HEX_H * HEX_L)
    m = np.bincount(idx, weights=eau.ravel().astype(np.float64), minlength=HEX_H * HEX_L)
    mer = (m >= 0.5 * np.maximum(n, 1)).reshape(HEX_H, HEX_L)
    # jamais d'eau sur l'emplacement principal d'une ville (valeur 0 de la couche des emplacements) ; les hex de port
    # (valeur 1) restent en mer, là où WH1 avait l'eau du port
    slots = np.asarray(read_layer(SLOTS)[1]).reshape(HEX_H, HEX_L)
    mer &= ~((slots == 0) & ~np.isin(np.asarray(read_layer(SOLS)[1]).reshape(HEX_H, HEX_L), SOLS_MER))
    part = (m / np.maximum(n, 1)).reshape(HEX_H, HEX_L)
    mer, noyes, rendus, cout = regulariser_cote(mer, part, slots >= 0)
    reste = defauts_de_cote(mer)
    print(f"  côte régularisée pour les tuiles de WH3 : {noyes} hex de terre noyés, {rendus} hex de mer rendus à la "
          f"terre (écart à la part d'eau de WH1 : {cout:.2f} hex) ; défauts restants : {len(reste)}")
    if reste:
        raise SystemExit(f"bande de côte sans tuile possible en {reste[:10]} : BOB les refuserait (« Failed to find tile »)")
    return mer


def voisins_de(r, c):
    """Les six voisins d'un hex de la grille CAIME (ligne 0 au sud, colonnes impaires hautes), dans l'ordre N, NE, SE,
    S, SO, NO."""
    if c & 1:
        return ((r + 1, c), (r + 1, c + 1), (r, c + 1), (r - 1, c), (r, c - 1), (r + 1, c - 1))
    return ((r + 1, c), (r, c + 1), (r - 1, c + 1), (r - 1, c), (r - 1, c - 1), (r, c - 1))


def defaut_de_cote(mer, r, c):
    """Hex de terre du bord de mer qu'aucune tuile de côte de WH3 ne couvre : plus de trois voisins de mer, ou deux bras
    de mer séparés. Relevé le 22.09.2026 (23 h) : les 431 hex de bande de la mer logique de WH1 ont tous une seule
    série de un à trois voisins de mer (0 échec de BOB) ; la mer visuelle de WH1 en donnait 27 autres (quatre ou cinq
    voisins de mer : pointes de terre d'un hex), et BOB 28 « Failed to find tile » autour d'eux (erreur 87). Hors de la
    carte compte comme mer."""
    if mer[r, c]:
        return False
    m = [bool(mer[a, b]) if 0 <= a < HEX_H and 0 <= b < HEX_L else True for a, b in voisins_de(r, c)]
    n = sum(m)
    return n > 3 or (n > 0 and sum(1 for k in range(6) if m[k] and not m[k - 1]) > 1)


def defauts_de_cote(mer):
    return [(int(r), int(c)) for r, c in zip(*np.nonzero(~mer & voisins_hex(mer))) if defaut_de_cote(mer, r, c)]


def regulariser_cote(mer, part, fige):
    """Retouche la mer hex par hex jusqu'à ce que toute la bande de côte soit couvrable (`defaut_de_cote`), en
    s'écartant le moins possible de WH1. Pour chaque défaut, on essaie de retourner (terre <-> mer) toute partie de
    l'hex et de ses six voisins ; parmi les retouches qui règlent l'hex et font baisser les défauts alentour, la moins
    chère, le coût d'un hex retourné étant son écart à la part d'eau de WH1 (|2 part - 1|). Mesuré le 22.09.2026 :
    26 hex d'écart, 6 hex d'eau pleine rendus à la terre ; ne proposer que « noyer l'hex ou rendre ses voisins de mer à
    la terre », en préférant la retouche qui règle le plus de défauts, coûtait 32,75 hex et 19 hex d'eau pleine. Les
    emplacements de ville (`fige`) ne bougent jamais. Renvoie (mer, noyés, rendus, coût)."""
    initiale = mer
    mer = mer.copy()

    def dedans(a, b):
        return 0 <= a < HEX_H and 0 <= b < HEX_L

    def defauts_autour(hexes):
        zone = set()
        for r, c in hexes:
            for a, b in ((r, c),) + voisins_de(r, c):
                zone.add((a, b))
                zone.update(voisins_de(a, b))
        return sum(1 for a, b in zone if dedans(a, b) and defaut_de_cote(mer, a, b))

    for _ in range(50):
        defauts = defauts_de_cote(mer)
        if not defauts:
            break
        for r, c in defauts:
            if not defaut_de_cote(mer, r, c):
                continue                                   # réglé par une retouche voisine
            libres = [(a, b) for a, b in ((r, c),) + voisins_de(r, c) if dedans(a, b) and not fige[a, b]]
            meilleure = None
            for k in range(1, len(libres) + 1):
                for opt in itertools.combinations(libres, k):
                    avant = defauts_autour(opt)
                    for a, b in opt:
                        mer[a, b] = not mer[a, b]
                    regle = not defaut_de_cote(mer, r, c)
                    apres = defauts_autour(opt)
                    for a, b in opt:
                        mer[a, b] = not mer[a, b]
                    prix = sum(abs(2 * float(part[a, b]) - 1) for a, b in opt)
                    cle = (0, prix, 0) if apres < avant else (1, apres - avant, prix)
                    if regle and (meilleure is None or cle < meilleure[0]):
                        meilleure = (cle, opt)
            if meilleure is not None:
                for a, b in meilleure[1]:
                    mer[a, b] = not mer[a, b]
    change = mer != initiale
    return (mer, int((change & mer).sum()), int((change & initiale).sum()),
            float(np.abs(2 * part[change] - 1).sum()))


def rasters():
    sols = np.asarray(read_layer(SOLS)[1]).reshape(HEX_H, HEX_L)
    col8, lig8 = hex_de_pixel(L, H, 8)
    mer_logique = np.isin(sols, SOLS_MER)
    if COTE_WH1:
        # la mer de WH1 au pixel : ses maillages de mer, hors de ses maillages de terre
        terre_w = np.load(RELIEF_MAILLAGES)
        fond_w = np.load(os.path.join(os.path.dirname(RELIEF_MAILLAGES), "mer_maillages.npy")).astype(np.float32)
        mer = np.isfinite(fond_w) & ~np.isfinite(terre_w)
        mer_hex = None
        slots = np.asarray(read_layer(SLOTS)[1]).reshape(HEX_H, HEX_L)
        ville = (slots == 0)[lig8, col8]
        print(f"  mer de WH1 au pixel : {int(mer.sum())} px ({mer.mean():.1%}) ; pixels d'eau sur l'emplacement principal "
              f"d'une ville : {int((mer & ville).sum())} (comme dans WH1)")
        # LA CÔTE NATURELLE (24.09.2026, session du rendu ; Charles : « les côtes, c'est un peu n'importe quoi », Bordeleaux
        # « très dans l'eau ») : le tracé de WH1 sans ses marches de cases, les ports au sec comme aux Empires
        # (`cotes_wh1`) ; tout ce qui suit (rivières, fond, rivage, plan d'eau, tuiles) part de cette mer. Un pixel de terre
        # de WH1 devenu mer reçoit un fond provisoire sous l'eau, approfondi ensuite (`approfondir_mer`).
        if cotes_wh1.COTE_NATURELLE:
            mer, bilan_cote = cotes_wh1.cote_naturelle(mer, L / float(LARGEUR_MONDE))
            fond_w = np.where(mer & ~np.isfinite(fond_w), np.float32(cotes_wh1.FOND_NOUVELLE_MER), fond_w).astype(np.float32)
            print(f"  côte naturelle : {bilan_cote}")
    else:
        mer_hex = mer_de_wh1(col8, lig8)
        print(f"  mer : {int(mer_hex.sum())} hex (mer de WH1) contre {int(mer_logique.sum())} hex de mer logique ; "
              f"en plus : {int((mer_hex & ~mer_logique).sum())}, en moins : {int((mer_logique & ~mer_hex).sum())}")
        mer = mer_hex[lig8, col8]

    v = dds(os.path.join(WH1, "lf_height_map.dds"), "<u2", (H, L)).astype(np.float32)
    lf = (A_HAUTEUR * v + B_HAUTEUR).astype(np.float64)
    hauteur, connu = sol_wh1(lf.astype(np.float32))
    # Les montagnes de WH1 (22.09.2026, 22 h, `montagnes_wh1.py`) : posées en objets, drapées sur lf + BASE, leur anneau
    # de base à y local 0 rejoint les maillages de terrain de WH1. Le sol suit donc, hors des maillages de terrain,
    # lf + BASE (et non plus l'écart prolongé de `sol_wh1`) et, sous chaque montagne, sa surface 2 cm plus bas : sans
    # cela, leur jupe sortait du sol en murs verts (Terry, 21 h 35).
    # (24.09.2026, chaîne 11) sans les falaises de côte de WH1 (`montagnes_wh1.FALAISES_DE_COTE`) : ni objet, ni sol sous elles
    surf = montagnes_wh1.surface(lf, L / float(LARGEUR_MONDE), liste=montagnes_wh1.poses_retenues())
    emprise_montagnes = np.isfinite(surf)              # pour les piémonts de `textures_sol_wh1` (relief-wh1)
    # (les falaises de côte descendent jusqu'au fond : sous leur face côté mer, le sol reste le fond de WH1)
    montagne_wh1 = np.isfinite(surf) & ~connu & ~(mer if COTE_WH1 else False)
    lfv = lf + montagnes_wh1.BASE
    if MOUSSE_MONTAGNES:
        sous_montagne, bilan_mousse = sol_sous_montagnes(surf, montagne_wh1, L / float(LARGEUR_MONDE))
        print(f"  mousse des montagnes : {bilan_mousse}")
    else:
        sous_montagne = surf - SOUS_MONTAGNE
    hauteur = np.where(connu, hauteur, np.where(montagne_wh1, sous_montagne, lfv)).astype(np.float32)
    hauteur_wh1 = np.where(connu, hauteur, np.where(montagne_wh1, surf, lfv)).astype(np.float32)   # objets de WH1
    connu = connu | montagne_wh1
    print(f"  montagnes de WH1 : {int(montagne_wh1.sum())} px sous leurs maillages ({montagne_wh1.mean():.1%})")
    # Les routes de WH1 (22.09.2026, 23 h 30) : leurs tuiles n'ont pas de maillage de terrain, mais leur sol est le relief
    # de base + BASE, celui que nous posons (la végétation de WH1 y est à +0,005 de notre sol : audit, lot 4). Sol connu :
    # les objets y gardent leur hauteur de WH1 ; recalés comme sur un sol inconnu, 323 pieux, fissures et tertres
    # plantés par WH1 étaient remontés (erreur 94). Les rivières et falaises passent devant (familles suivantes de l'ordre).
    fam = tuiles_wh1.familles_par_case(ordre=["roads"] + FAMILLES_SOL_INCONNU_WH1)
    route_wh1 = np.repeat(np.repeat(fam == "roads", 4, 0), 4, 1)[:H, :L] & ~connu
    connu = connu | route_wh1
    print(f"  routes de WH1 : {int(route_wh1.sum())} px de sol connu en plus ({route_wh1.mean():.1%})")
    # LES DELTAS DE WH1 (24.09.2026, chaîne 12, `deltas_wh1` ; Charles : « leur joli delta comme sur Warhammer 1 ») : dans
    # ses tuiles d'embouchure, les bancs de sable (fond de WH1 au-dessus de 0) sont de la terre à la hauteur de ce fond, le
    # reste de l'éventail reste de la mer au fond de WH1 ; l'eau y sera celle des rubans de WH1 (plus bas, après la mer)
    import deltas_wh1
    zone_delta = np.zeros((H, L), bool)
    banc_delta = np.zeros((H, L), bool)
    if deltas_wh1.ACTIF and COTE_WH1:
        zone_delta = deltas_wh1.zone(H, L)
        banc_delta = deltas_wh1.bancs(zone_delta, fond_w, terre_w) & mer
        mer = mer & ~banc_delta
        # (chaîne 15, C4) bancs au moins deltas_wh1.BANC_HAUT_MIN au-dessus de l'eau : au ras de l'eau, le matériau de la
        # mer les bordait d'écume (enquête `scratchpad\enquete_rivieres\`, e10_delta)
        hauteur = np.where(banc_delta, np.maximum(fond_w, np.float32(deltas_wh1.BANC_HAUT_MIN)), hauteur).astype(np.float32)
        hauteur_wh1 = np.where(banc_delta, fond_w, hauteur_wh1).astype(np.float32)
        connu = connu | banc_delta
        print(f"  deltas de WH1 : zone {int(zone_delta.sum())} px, bancs de sable {int(banc_delta.sum())} px, mer de "
              f"l'éventail {int((zone_delta & mer).sum())} px")
    # Le sol des tuiles de rivière de WH1 (23.09.2026, `rivieres_wh1.py`) : leur lit (y local -10, 2,6 cm sous le relief de
    # base) sous les rubans d'eau drapés ; c'est le sol de WH1 à cet endroit, donc du sol connu pour les objets.
    if RIVIERES_WH1:
        surf_riv = rivieres_wh1.surface(lf, L / float(LARGEUR_MONDE))
        riviere = np.isfinite(surf_riv) & ~connu
        hauteur = np.where(riviere, surf_riv, hauteur).astype(np.float32)
        hauteur_wh1 = np.where(riviere, surf_riv, hauteur_wh1).astype(np.float32)
        connu = connu | riviere
        print(f"  rivières de WH1 : {int(riviere.sum())} px de lit et de berges ({riviere.mean():.1%})")
        # LES REPLATS SOUS LES COLONIES (24.09.2026, chaîne 12, session du rendu, `replats_colonies` ; Fort Solstice : un
        # champ du préfab « posé au-dessus de la pente ») : le sol à moitié adouci sous les préfabs plats de WH3, raccord de
        # 3 u, ni la mer, ni le lit des rivières de WH1, ni les montagnes ; `hauteur` seul (les objets de WH1 suivent)
        import replats_colonies
        if replats_colonies.ACTIF and os.path.exists(COLONIES_MAP_DATA):
            import json
            cles = json.load(open(COLONIES_MAP_DATA, encoding="utf-8"))["keys"]
            hauteur, bilan_replats = replats_colonies.replats(
                hauteur, {k: (float(v[0]), float(v[1])) for k, v in cles.items()}, L / float(LARGEUR_MONDE),
                mer | np.isfinite(surf_riv), emprise_montagnes)
            print(f"  replats sous les colonies : {bilan_replats}")
        # l'eau des rivières LISSE ET RELIÉE (23.09.2026, 05 h 30, `rivieres_wh1.champ_reseau`) : champ du réseau de WH1
        # (ruban des `blend0.dds` et rubans d'eau), niveau des rubans plafonné sous les berges, lit en profil doux
        rubans_wh1 = rivieres_wh1.eau_raster(lf, L / float(LARGEUR_MONDE))
        # (24.09.2026, chaîne 12) hors des deltas de WH1 : leur eau est celle de ses rubans, posée telle quelle plus bas
        rubans = np.where(zone_delta, np.nan, rubans_wh1).astype(rubans_wh1.dtype)
        import rivieres_wh1_masque
        champ_riv, n_ecartees, n_gardees = rivieres_wh1.champ_reseau(
            np.where(zone_delta, 0.0, rivieres_wh1_masque.Rivieres().masque(4)[:H, :L]), rubans, mer)
        # les sources effilées (23.09.2026, 18 h, session du rendu) : plus de coupe franche au départ des petites sources
        champ_riv, bilan_sources = rivieres_wh1.effiler_sources(champ_riv, L / float(LARGEUR_MONDE))
        print(f"  sources : {bilan_sources}")
        # les rivières de la largeur de WH1 (24.09.2026, session du rendu ; Charles : « comme dans WH1 »)
        if rivieres_wh1.AXE_WH1:
            # (chaîne 14) sur l'axe continu, à la largeur locale des rubans de WH1 (`rivieres_wh1.largeur_axe`)
            champ_riv, bilan_largeur = rivieres_wh1.largeur_axe(champ_riv, rubans)
            print(f"  rivières sur l'axe, largeur de WH1 : {bilan_largeur}")
        elif rivieres_wh1.LARGEUR_WH1:
            champ_riv, bilan_largeur = rivieres_wh1.largeur_wh1(champ_riv, rubans)
            print(f"  rivières de la largeur de WH1 : {bilan_largeur}")
        # les colonies au bord de l'eau, comme dans WH1 (24.09.2026, session du rendu ; Fort Solstice, Château de Desfleuves)
        if rivieres_wh1.COLONIES_AU_SEC and os.path.exists(COLONIES_MAP_DATA):
            import json
            positions = [tuple(v) for v in json.load(open(COLONIES_MAP_DATA, encoding="utf-8"))["keys"].values()]
            champ_riv, bilan_sec = rivieres_wh1.colonies_au_sec(champ_riv, rubans, positions, L / float(LARGEUR_MONDE))
            print(f"  colonies au bord de l'eau (filet de WH1) : {bilan_sec}")
        eau_riv, n_sec = rivieres_wh1.niveau_eau(rubans, champ_riv, hauteur.astype(np.float64), mer)
        print(f"  réseau des rivières : {n_gardees} morceaux ({n_ecartees} taches écartées) ; eau sur "
              f"{int(np.isfinite(eau_riv).sum())} px ({n_sec} px loin de tout ruban de WH1)")
        if rivieres_wh1.EAU_SOUS_SOL_MAX is not None:
            # (chaîne 14) jamais plus de EAU_SOUS_SOL_MAX sous le sol de WH1 (plus de tranchée de 0,8 à 1,08 u)
            plancher_eau = hauteur.astype(np.float64) - rivieres_wh1.EAU_SOUS_SOL_MAX
            releve = np.isfinite(eau_riv) & ~mer & (eau_riv < plancher_eau)
            eau_riv = np.where(releve, plancher_eau, eau_riv).astype(eau_riv.dtype)
            print(f"  eau des rivières relevée à {rivieres_wh1.EAU_SOUS_SOL_MAX} u sous le sol de WH1 au plus : "
                  f"{int(releve.sum())} px")
        # les embouchures (23.09.2026, session du rendu) : l'eau descend jusqu'au niveau de la mer à la côte
        # (23 h 10) l'eau descend au niveau de la mer au bord du PLAN D'EAU de la mer (EMBOUCHURES_SOUS_LE_PLAN)
        # (chaîne 12) pas de descente vers la mer des deltas de WH1 : la rivière y arrive à la hauteur de ses rubans
        pres_delta = rivieres_wh1.dilater(zone_delta, 6) if zone_delta.any() else zone_delta
        eau_riv, n_desc, _ = rivieres_wh1.descente_vers_la_mer(
            eau_riv, (emprise_plan_mer(mer) if MER_PLANS and EMBOUCHURES_SOUS_LE_PLAN else mer) & ~pres_delta,
            L / float(LARGEUR_MONDE))
        print(f"  embouchures : eau abaissée vers la mer sur {n_desc} px (plafond {rivieres_wh1.NIVEAU_MER} + "
              f"{rivieres_wh1.PENTE_EMBOUCHURE} par unité le long de l'eau)")
        # les lacs de WH1 en vrais étangs (23.09.2026, session du rendu, `etangs_wh1`) : forme et niveau, puis l'eau des
        # rivières qui les traversent passe sous eux et descend vers eux (avant le creusement de leur lit)
        if etangs_wh1.ACTIF:
            grille = etangs_wh1.Grille(H, L)
            lacs = etangs_wh1.lacs_wh1()
            for lac in lacs:
                c_ = int(min(max(lac["x"] * grille.pas - 0.5, 0), L - 1))
                l_ = int(min(max((H - 1.5) - lac["z"] * props_wh1_vers_layers.Z_VERS_RASTER * grille.pas, 0), H - 1))
                lac["y_base"] = lac["y"] + float(hauteur[l_, c_] - hauteur_wh1[l_, c_])
            etangs = etangs_wh1.former(lacs, hauteur.astype(np.float64), eau_riv, grille)
            eau_riv, n_et = etangs_wh1.rivieres_vers_etangs(eau_riv, etangs, grille)
            causes = {}
            for et in etangs:
                causes[et["cause"]] = causes.get(et["cause"], 0) + 1
            print(f"  étangs : {len(etangs)} ({causes}) ; eau des rivières accordée à eux sur {n_et} px ; plans d'eau de WH1 "
                  f"invisibles dans WH1, écartés : {getattr(etangs_wh1.former, 'ignores', [])}")
        hauteur, n_eau, n_releves = rivieres_wh1.creuser_doux(hauteur.astype(np.float64), eau_riv, champ_riv)
        print(f"  lit des rivières en profil doux ({rivieres_wh1.PROFONDEUR} au cœur) : {n_eau} px sous le maillage, "
              f"{n_releves} px de berge relevés pour cacher son bord")
    # Les collines modelées de WH1 (23.09.2026, `props_wh1_vers_layers.collines_de_relief`) : 82 objets au matériau 86 à
    # textures factices, qui prenaient l'aspect du sol dans WH1 ; fondus dans le relief (dessus de leur maillage, lu à
    # z × √3/2 comme tout raster), ils portent les textures de WH1 et ne sont plus posés en objets
    import relief_maillages_wh1
    collines = np.full((H, L), np.nan)
    pas_px = L / float(LARGEUR_MONDE)
    liste_collines = props_wh1_vers_layers.collines_de_relief()
    for w, t in liste_collines:
        relief_maillages_wh1.rasteriser_px(w[:, 0] * pas_px - 0.5,
                                           (H - 1.5) - w[:, 2] * props_wh1_vers_layers.Z_VERS_RASTER * pas_px,
                                           w[:, 1], t, collines)
    dessus = np.isfinite(collines) & (collines > hauteur)
    leve = float(np.max(np.where(dessus, collines - hauteur, 0.0))) if dessus.any() else 0.0
    hauteur = np.where(dessus, collines, hauteur).astype(np.float32)
    hauteur_wh1 = np.where(np.isfinite(collines) & (collines > hauteur_wh1), collines, hauteur_wh1).astype(np.float32)
    print(f"  collines modelées de WH1 fondues dans le relief : {len(liste_collines)} ; {int(dessus.sum())} px relevés "
          f"(jusqu'à {leve:.2f})")
    # terre sous le niveau de l'eau (22.09.2026, 22 h 30) : avec la mer de WH1, la terre de WH1 est au-dessus de 0
    # presque partout ; les rares pixels dessous sont seulement remontés à PLANCHER_TERRE. L'ancienne « terre basse
    # relevée » (phase 6) remodelait toute la plaine côtière sous 0,35 en plateau : erreur 86.
    # (23.09.2026, session du rendu) sauf le lit des rivières, creusé sous leur eau : relevé à PLANCHER_TERRE près de la côte,
    # il passait au-dessus de l'eau qui descend vers la mer
    lit_riviere = np.isfinite(eau_riv) if RIVIERES_WH1 else np.zeros((H, L), bool)
    basse = ~mer & (hauteur < PLANCHER_TERRE) & ~lit_riviere
    if basse.any():
        print(f"  terre sous l'eau remontée à {PLANCHER_TERRE} : {int(basse.sum())} px (min {float(hauteur[basse].min()):.3f})")
        hauteur = np.where(basse, np.float32(PLANCHER_TERRE), hauteur).astype(np.float32)
    # les étangs dans le relief (23.09.2026, session du rendu) : berges puis cuvettes, après le lit des rivières
    eau_etangs = np.zeros((H, L), bool)
    if RIVIERES_WH1 and etangs_wh1.ACTIF:
        hauteur, bilan_et = etangs_wh1.creuser(hauteur, etangs, lit_riviere, grille)
        # au bord d'une chute, le contour de l'eau ne dépasse pas au-dessus du vide (`etangs_wh1.marges_sures`)
        bilan_et["directions de contour réduites (bord d'une chute)"] = etangs_wh1.marges_sures(etangs, hauteur, grille)
        eau_etangs = etangs_wh1.masque_eau(etangs, grille)
        enterre = [etangs_wh1.bord_enterre(et, hauteur, grille) for et in etangs]
        print(f"  étangs dans le relief : {bilan_et} ; bord de l'eau enterré : médiane {np.median(enterre):.0%}, "
              f"min {min(enterre):.0%}")
    # le fil de l'eau (23.09.2026, 22 h, session du rendu ; Charles : « des trous entre deux morceaux de rivière ») : après
    # les collines et les étangs, une eau visible d'un seul tenant de la source à la mer (`rivieres_wh1.fil_de_l_eau`)
    if RIVIERES_WH1 and rivieres_wh1.FIL_DE_L_EAU:
        hauteur, bilan_fil = rivieres_wh1.fil_de_l_eau(hauteur, eau_riv, mer, garde=rivieres_wh1.dilater(eau_etangs, 4))
        print(f"  fil de l'eau : {bilan_fil}")
    # (25.09.2026, chaîne 15) les berges basses pour le sol vu de loin (`rivieres_wh1.BERGES_BASSES`) : ni les étangs, ni
    # les deltas, ni le pied des colonies
    if RIVIERES_WH1 and rivieres_wh1.BERGES_BASSES:
        garde_bb = rivieres_wh1.dilater(eau_etangs, 4) | (rivieres_wh1.dilater(zone_delta, 6) if zone_delta.any()
                                                          else zone_delta)
        if os.path.exists(COLONIES_MAP_DATA):
            import json
            r3 = 3 ** 0.5 / 2
            ii, jj = np.mgrid[0:H, 0:L]
            for x, z in json.load(open(COLONIES_MAP_DATA, encoding="utf-8"))["keys"].values():
                i, j = (H - 1.5) - z * r3 * pas_px, x * pas_px - 0.5
                r_px = int(rivieres_wh1.COLONIE_R_SEC * pas_px) + 2
                i0, i1, j0, j1 = max(int(i) - r_px, 0), min(int(i) + r_px + 1, H), max(int(j) - r_px, 0), min(int(j) + r_px + 1, L)
                if i0 < i1 and j0 < j1:
                    garde_bb[i0:i1, j0:j1] |= np.hypot((ii[i0:i1, j0:j1] - i) / (r3 * pas_px),
                                                       (jj[i0:i1, j0:j1] - j) / pas_px) <= rivieres_wh1.COLONIE_R_SEC
            del ii, jj
        hauteur, bilan_bb = rivieres_wh1.berges_basses(hauteur, eau_riv, mer, garde=garde_bb, plancher=PLANCHER_TERRE)
        print(f"  berges basses (sol vu de loin) : {bilan_bb}")

    # le fond de la mer de WH1 (22.09.2026, 22 h ; Charles : « plein d'objets flottants dans la mer, avant
    # l'embouchure ») : `lf_sea_height_map.dds` (même grille et même sens que le relief, lf ≈ 1,0058 x fond + 340 sur
    # la terre ; en mer vers -0,75, -0,59 près des côtes). Notre profil inventé (-0,3 à -1,4) laissait les rochers
    # et récifs de WH1 au-dessus du fond.
    noyee = np.zeros((H, L), bool)                  # terre des cases de mer, dessinée en eau (FOND_SOUS_ZERO)
    if COTE_WH1:
        # la surface de WH1 (ses maillages de mer en mer, notre sol ailleurs), adoucie au rivage : c'est le FOND ; la
        # côte est la ligne où elle passe sous l'eau, comme dans WH1
        fond = np.where(mer, fond_w, hauteur).astype(np.float32)
        hauteur_wh1 = np.where(mer, fond_w, hauteur_wh1).astype(np.float32)
        fond, mer = rivage_naturel(fond, mer, garde=(lit_riviere | eau_etangs) & ~mer,
                                   # (chaîne 14) seuls les bancs des deltas restent figés ; le reste du delta prend la
                                   # berge en pente comme la côte (plus de mur au pixel de WH1)
                                   fige=rivieres_wh1.dilater(banc_delta, 1) if banc_delta.any() else None)
        # (chaîne 12) la mer des deltas de WH1 garde le fond de WH1 (ni adoucie ni approfondie)
        # (chaîne 14) seulement là où WH1 a un fond : la berge en pente noie aussi de la terre de WH1 dans le delta (244 px
        # sans fond, hauteur non définie, à l'essai à blanc) ; ceux-là gardent le fond adouci
        mer_delta = zone_delta & mer & np.isfinite(fond_w)
        fond = np.where(mer_delta, np.minimum(fond_w, np.float32(-EAU_MIN_MER)), fond).astype(np.float32)
        if not np.isfinite(fond[mer]).all():
            raise SystemExit(f"fond de la mer non défini sur {int((~np.isfinite(fond) & mer).sum())} px")
        fond_wh1 = fond
        if MER_PROFONDE:
            fond, bilan_mer = approfondir_mer(fond, mer, garde=mer_delta)
            print(f"  mer approfondie comme chez CA : {bilan_mer}")
        if RIVIERES_WH1:
            # la fin des rivières sous la mer (23.09.2026, session du rendu) : sous le fond, ruban prolongé et effilé
            # (23 h 10) sous tout le plan d'eau de la mer, pas seulement sur la mer : plus de double eau à l'embouchure
            eau_riv, champ_riv, bilan_pl = rivieres_wh1.plongee(
                eau_riv, champ_riv, (emprise_plan_mer(mer) if MER_PLANS and EMBOUCHURES_SOUS_LE_PLAN else mer) & ~pres_delta,
                fond)
            print(f"  rivières sous la mer : {bilan_pl}")
            # (chaîne 12) l'eau des deltas de WH1 : ses rubans, à leur hauteur, sur les bancs et au-dessus de la mer
            if zone_delta.any():
                # (chaîne 14) rien sur la mer, l'eau des bras descendue vers elle (`deltas_wh1.EAU_SUR_MER`)
                niv_d, champ_d = deltas_wh1.eau(zone_delta, rubans_wh1, mer=mer, pas=L / float(LARGEUR_MONDE))
                eau_riv = np.where(zone_delta, niv_d, eau_riv).astype(eau_riv.dtype)
                champ_riv = np.where(zone_delta, champ_d, champ_riv).astype(champ_riv.dtype)
                # sur les bancs, le sol 3 cm sous l'eau des rubans (essai à blanc, 20 h 42 : au sud de Brionne, l'eau passait
                # sous les bancs, jusqu'à +0,19, et la rivière s'arrêtait à la pointe de l'éventail)
                sous = zone_delta & ~mer & np.isfinite(niv_d)
                fond = np.where(sous, np.minimum(fond, niv_d - 0.03), fond).astype(np.float32)
                print(f"  eau des deltas de WH1 : {int(np.isfinite(niv_d).sum())} px, hauteur p10/p50/p90 "
                      f"{np.round(np.nanpercentile(niv_d, [10, 50, 90]), 3).tolist() if np.isfinite(niv_d).any() else '-'}")
        # Convention de CA (23.09.2026, 03 h 40 ; Charles en jeu : « sur le côté de la mer il n'y a pas d'eau, que le
        # fond de sable » ; erreur 113) : dans la mer, `height` est la SURFACE DE L'EAU (aux Empires : 0,000 en médiane)
        # et `sea_height` le fond (-0,9 près des côtes) ; sous la terre, `sea_height` reste au moins 1 plus bas. La même
        # surface écrite dans les deux faisait une eau de profondeur nulle : le jeu n'en dessinait rien.
        # (16 h 50, session du rendu : la mesure refaite sur la mer de tile_map des Empires donne `height` 0,9 en médiane
        # sur la mer, sans lien avec le fond : ce que le jeu dessine sur une case de mer est `sea_height`, l'eau restant au
        # niveau de la mer ; voir CASES_DE_MER.)
        # (18 h 45 : la mer jouable des Empires a height > 0, jamais 0 ; voir HAUTEUR_SUR_MER)
        hauteur = np.where(mer, np.float32(HAUTEUR_SUR_MER), fond).astype(np.float32)
        hauteur_mer = np.where(mer, fond, hauteur - SOUS_TERRE_MER).astype(np.float32)
        if FOND_SOUS_ZERO:
            # (19 h 40) le fond sous FOND_MAX partout : aucune tuile de mer au-dessus de l'eau (voir FOND_SOUS_ZERO) ; la
            # terre d'une case de mer est un rivage noyé à FOND_MAX (ni 3 unités dessous, ni la terre elle-même)
            assert (H % 4, L % 4) == (0, 0), (H, L)
            case_mer = np.repeat(np.repeat(mer.reshape(H // 4, 4, L // 4, 4).any((1, 3)), 4, 0), 4, 1)
            noyee = case_mer & ~mer
            if COTE_DOUCE and COTE_CASES_DE_TERRE:
                # (22 h 55) cases de mer = cases entièrement de mer ; une case mixte est de la terre (COTE_CASES_DE_TERRE)
                pleine_c = mer.reshape(H // 4, 4, L // 4, 4).all((1, 3))
                p_ = np.pad(pleine_c, 1)
                bord_c = np.zeros_like(pleine_c)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        bord_c |= p_[1 + dy:1 + dy + pleine_c.shape[0], 1 + dx:1 + dx + pleine_c.shape[1]]
                pleine = np.repeat(np.repeat(pleine_c, 4, 0), 4, 1)
                bord = np.repeat(np.repeat(bord_c, 4, 0), 4, 1)      # cases de mer et leurs 8 voisines
                fond_mer = np.minimum(hauteur_mer, np.float32(-EAU_MIN_MER))
                # height : sur la mer des cases de terre (mixtes), le fond, sous le plan d'eau
                hauteur = np.where(mer & ~pleine, fond_mer, hauteur).astype(np.float32)
                if MER_SOUS_L_EAU_PRES_DES_TERRES:
                    # (chaîne 13 bis) aussi sur les cases de mer pleines près d'une case de terre (voir le drapeau)
                    pres_terre = distance_a(~pleine, PRES_DES_TERRES_PX + 1) <= PRES_DES_TERRES_PX
                    hauteur = np.where(mer & pleine & pres_terre, fond_mer, hauteur).astype(np.float32)
                    print(f"  mer sous l'eau près des cases de terre : {int((mer & pleine & pres_terre).sum())} px")
                # sea_height : la mer au fond ; la terre des cases de bord ramenée sous 0 (tuiles de mer au maximum <= 0) ;
                # l'autre terre proche = la terre (si le jeu la dessinait depuis sea_height) ; la terre lointaine sous elle-même
                pres = distance_a(mer, TERRE_COTE_PX + 1) <= TERRE_COTE_PX
                hauteur_mer = np.where(mer, fond_mer,
                                       np.where(bord, np.minimum(hauteur, np.float32(-EAU_MIN_MER)),
                                                np.where(pres, hauteur, np.minimum(hauteur_mer, np.float32(FOND_MAX))))
                                       ).astype(np.float32)
                noyee = np.zeros((H, L), bool)
                print(f"  côte en cases de terre : {int(pleine_c.sum())} cases de mer pleines, "
                      f"{int((mer.reshape(H // 4, 4, L // 4, 4).any((1, 3)) & ~pleine_c).sum())} cases mixtes passées en terre ; "
                      f"sea_height max sur les cases de mer et leur bord {float(hauteur_mer[bord].max()):.3f}")
            elif COTE_DOUCE:
                # (21 h 55) la terre proche de la mer, cases de mer comprises, garde sa hauteur : le plan d'eau coupe la côte
                # au pixel ; la mer au moins EAU_MIN_MER sous l'eau ; la terre lointaine reste loin sous elle-même
                # (`noyee` reste la terre des cases de mer : les objets qui y sont posés suivent `hauteur_mer`, ici la terre)
                pres = distance_a(mer, TERRE_COTE_PX + 1) <= TERRE_COTE_PX
                terre_cote = (pres | case_mer) & ~mer
                hauteur_mer = np.where(terre_cote, hauteur,
                                       np.where(mer, np.minimum(hauteur_mer, np.float32(-EAU_MIN_MER)),
                                                np.minimum(hauteur_mer, np.float32(FOND_MAX)))).astype(np.float32)
                print(f"  côte douce : terre à moins de {TERRE_COTE_PX} px de la mer au fond = la terre ({int(terre_cote.sum())} "
                      f"px, dont {int(noyee.sum())} dans des cases de mer) ; mer au moins {EAU_MIN_MER} sous l'eau ; fond de "
                      f"mer max {float(hauteur_mer[mer].max()):.3f}")
            else:
                hauteur_mer = np.where(noyee, np.float32(FOND_MAX),
                                       np.minimum(hauteur_mer, np.float32(FOND_MAX))).astype(np.float32)
                print(f"  fond sous {FOND_MAX} partout : rivage noyé (terre des cases de mer) {int(noyee.sum())} px ; fond "
                      f"max {float(hauteur_mer.max()):.3f}")
        elif CASES_DE_MER:
            # la terre d'une case de mer (la côte de WH1 passe au pixel, la case entière est de la mer) : son fond est
            # la terre elle-même, pas 3 unités dessous (des trous d'eau profonde sombres, en escalier le long de la côte) ;
            # 18 h 45 : toute la terre à moins de TERRE_PRES_DE_LA_MER px de la mer (le jeu traite la côte par cases, voire
            # par hex : les bandes sombres restaient)
            assert (H % 4, L % 4) == (0, 0), (H, L)
            case_mer = np.repeat(np.repeat(mer.reshape(H // 4, 4, L // 4, 4).any((1, 3)), 4, 0), 4, 1)
            # (distance_a plafonne à sa portée : portée + 1, sinon tout pixel serait « à moins de » la portée)
            pres = distance_a(mer, TERRE_PRES_DE_LA_MER + 1) <= TERRE_PRES_DE_LA_MER
            terre_en_mer = (case_mer | pres) & ~mer
            hauteur_mer = np.where(terre_en_mer, hauteur, hauteur_mer).astype(np.float32)
            print(f"  terre au bord de la mer : {int(terre_en_mer.sum())} px, fond = la terre (plus de trou de 3 unités)")
        # les objets posés en mer suivent le fond approfondi (leur sol de WH1 reste le fond de WH1)
        hauteur_wh1 = np.where(mer, fond_wh1, hauteur_wh1).astype(np.float32)
        print(f"  fond de WH1 (maillages de mer) : p5/p50/p95 "
              f"{np.round(np.percentile(fond[mer], [5, 50, 95]), 3).tolist()} sous une eau au niveau {NIVEAU_EAU} ; "
              f"au-dessus de l'eau : {int((fond[mer] > NIVEAU_EAU).sum())} px (écueils et bancs de WH1)")
    else:
        v_mer = dds(os.path.join(WH1, "lf_sea_height_map.dds"), "<u2", (H, L)).astype(np.float64)
        fond = A_HAUTEUR * (FOND_PENTE * v_mer + FOND_DECALAGE) + B_HAUTEUR
        hauteur_mer = np.where(mer, np.minimum(fond, MER_COTE), TERRE_SOUS_MER).astype(np.float32)

    melange_wh1 = dds(os.path.join(WH1, "global_map", "global_blend.dds"), np.uint8, (H, L))[::-1]
    table = np.full(256, TEXTURES[2], np.uint8)
    for k, v3 in TEXTURES.items():
        table[k] = v3
    melange = table[melange_wh1]
    # plus d'éboulis de WH3 sous les montagnes (22.09.2026, 22 h) : elles sont désormais les maillages de WH1 ; au pied,
    # le sol a les textures de WH1, comme dans WH1. Sous la mer, WH1 garde son `global_blend` (herbe à cailloux
    # `grass_a2` à 99 %, vue à travers son eau teintée) : avec COTE_WH1, plus de sable tropical de WH3
    if not COTE_WH1:
        melange[mer] = TEXTURE_MER

    col2, lig2 = hex_de_pixel(L // 4, (H + 3) // 4, 2)
    if COTE_WH1:
        # une case est de la mer dès qu'un de ses 4 x 4 pixels l'est : toute l'eau de WH1 est sur des cases de mer
        assert (H % 4, L % 4) == (0, 0), (H, L)
        mer2 = mer.reshape(H // 4, 4, L // 4, 4).any((1, 3))
        if FOND_SOUS_ZERO and COTE_DOUCE and COTE_CASES_DE_TERRE:
            mer2 = mer.reshape(H // 4, 4, L // 4, 4).all((1, 3))      # (22 h 55) cases mixtes en terre
    else:
        mer2 = mer_hex[lig2, col2]
    tuiles = np.empty(mer2.shape + (4,), np.uint8)
    tuiles[:] = COULEUR_TERRE
    tuiles[mer2] = COULEUR_MER
    route = routes(mer2, col2, lig2)
    tuiles[route] = COULEUR_ROUTE
    # la côte passe sur les routes : aux Empires, une route s'arrête à la bande de côte (638 contacts), jamais dedans
    if not COTE_WH1:
        falaise, rivage = cotes(mer_hex, col2, lig2)
        tuiles[falaise] = COULEUR_FALAISE
        tuiles[rivage] = COULEUR_RIVAGE
    # sol visible pour les objets : le fond de la mer en mer (celui de WH1), le relief ailleurs
    return {"hauteur": hauteur, "hauteur_mer": hauteur_mer, "melange": melange, "tuiles": tuiles,
            "eau_rivieres": eau_riv if RIVIERES_WH1 else None, "champ_rivieres": champ_riv if RIVIERES_WH1 else None,
            "mer": mer, "sols": sols, "arbres": arbres(mer2), "route": route, "hauteur_wh1": hauteur_wh1,
            "neige": neige(melange_wh1, mer2, eau_etangs | (np.nan_to_num(eau_riv, nan=-1e9) > hauteur
                                                          if RIVIERES_WH1 else False)),
            "sol_connu": connu | mer,
            # le sol que le jeu dessine : le fond sur les cases de mer (rivage noyé compris), le relief ailleurs
            "sol_objets": np.where(mer | noyee, hauteur_mer, hauteur).astype(np.float32),
            "sol_objets_wh1": np.where(mer, hauteur_mer, hauteur_wh1).astype(np.float32),
            # (24.09.2026, chaîne 13) sous les maillages de montagne de WH1, hors maillages de terrain et mer : objets
            "montagnes_wh1": montagne_wh1 & ~mer,
            "montagnes": emprise_montagnes, "eau_etangs": eau_etangs, "delta_bancs": banc_delta & ~mer,
            "zone_delta": zone_delta,
            "etangs": etangs if (RIVIERES_WH1 and etangs_wh1.ACTIF) else [],
            "grille": grille if (RIVIERES_WH1 and etangs_wh1.ACTIF) else None}


# LA MOUSSE DES MONTAGNES (24.09.2026, 04 h 05, session du rendu ; vidéos WH1 / WH3 de Charles : « montagnes nues, grises, à
# traînées blanches » contre la roche moussue de WH1). Les textures de roche de WH1 sont gris-brun (moyennes 86-107) : le
# vert venait du moteur de WH1, qui peignait les textures du sol sur les faces peu pentues de ses maillages de terrain
# personnalisé (matériau 49). Posées en objets dans WH3, nos montagnes n'ont que la roche. Sous chaque montagne, le sol
# (qui suivait la surface 2 cm plus bas, SOUS_MONTAGNE) passe désormais MOUSSE_DESSUS AU-DESSUS de la roche sur les
# replats (pente < MOUSSE_PENTE_0) : l'herbe de WH1 du mélange y affleure comme de la mousse ; sur les pentes raides
# (> MOUSSE_PENTE_1), il passe SOUS le point le plus bas du maillage dans le pixel et ses voisins (minimum 3 x 3) moins
# SOUS_RAIDE : le sol ne perce plus les parois (les traînées claires, relief au maximum par pixel sous une face raide).
MOUSSE_MONTAGNES = True
MOUSSE_DESSUS, SOUS_RAIDE = 0.03, 0.03
MOUSSE_PENTE_0, MOUSSE_PENTE_1 = 0.45, 0.75     # pente (u par u) : replat en dessous, paroi au-dessus, fondu entre


def sol_sous_montagnes(surf, masque, pas):
    """(sol, bilan) : le sol sous les montagnes de WH1 (voir MOUSSE_MONTAGNES) ; `surf` = dessus des maillages (NaN
    ailleurs), `masque` = pixels concernés, `pas` px par unité."""
    s = np.where(np.isfinite(surf), surf, np.nan).astype(np.float64)
    plein = np.where(np.isfinite(s), s, np.nanmin(s[np.isfinite(s)]) if np.isfinite(s).any() else 0.0)
    gy, gx = np.gradient(plein)
    pente = np.hypot(gx, gy) * pas                       # u par u (pixels carrés, `pas` px par unité)
    pente = moyenne_boite(pente, 2) / 25.0               # plaques de mousse d'un seul tenant, pas de taches d'un pixel
    bas = np.where(np.isfinite(s), s, np.inf)
    p = np.pad(bas, 1, mode="edge")
    mini = bas.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            mini = np.minimum(mini, p[1 + dy:1 + dy + s.shape[0], 1 + dx:1 + dx + s.shape[1]])
    mini = np.where(np.isfinite(mini), mini, s)
    t = np.clip((pente - MOUSSE_PENTE_0) / (MOUSSE_PENTE_1 - MOUSSE_PENTE_0), 0.0, 1.0)
    t = t * t * (3 - 2 * t)
    sol = (1 - t) * (s + MOUSSE_DESSUS) + t * (mini - SOUS_RAIDE)
    m = masque & np.isfinite(s)
    bilan = {"replats moussus (px)": int((m & (t < 0.5)).sum()), "parois (px)": int((m & (t >= 0.5)).sum()),
             "part moussue": f"{float((m & (t < 0.5)).sum()) / max(int(m.sum()), 1):.0%}",
             "haut des parois abaissé p50 (u)": round(float(np.median((s - sol)[m & (t >= 0.5)])), 3) if (m & (t >= 0.5)).any()
             else 0.0}
    return sol.astype(np.float32), bilan


def rivage_naturel(h, mer, garde=None, fige=None):
    """(relief, mer) : le relief adouci de part et d'autre de la côte de WH1 (`RIVAGE_BANDE`, `RIVAGE_RAYON`), et la
    mer étendue aux pixels que ce relief adouci met sous l'eau (ils doivent tomber sur des cases de mer de tile_map).
    `garde` (23.09.2026, session du rendu) : pixels de terre qui ne sont ni relevés par l'adoucissement ni noyés : le lit
    des rivières, creusé sous leur eau qui descend vers la mer (noyé, il faisait de l'embouchure une anse dont le bord,
    à l'intérieur des terres, laissait l'eau de la rivière quelques centimètres au-dessus de la mer).
    `fige` (24.09.2026, chaîne 13) : pixels laissés tels quels, relief et côté (les deltas de WH1)."""
    frontiere = np.zeros(mer.shape, bool)
    frontiere[1:, :] |= mer[1:, :] != mer[:-1, :]
    frontiere[:-1, :] |= mer[1:, :] != mer[:-1, :]
    frontiere[:, 1:] |= mer[:, 1:] != mer[:, :-1]
    frontiere[:, :-1] |= mer[:, 1:] != mer[:, :-1]
    d = distance_a(frontiere, RIVAGE_BANDE + 1)
    bande = d <= RIVAGE_BANDE
    k = 2 * RIVAGE_RAYON + 1
    flou = h.astype(np.float64)
    for _ in range(3):
        flou = moyenne_boite(flou, RIVAGE_RAYON) / (k * k)
    t = np.clip(1.0 - d / float(RIVAGE_BANDE), 0.0, 1.0)
    w = t * t * (3 - 2 * t)
    neuf = (w * flou + (1 - w) * h).astype(np.float32)
    if garde is not None:
        neuf = np.where(garde, np.minimum(neuf, h), neuf).astype(np.float32)
    if fige is not None:
        neuf = np.where(fige, h, neuf).astype(np.float32)
        bande = bande & ~fige
    if RIVAGE_TERRE_WH1:
        # la terre de WH1 telle quelle ; sous l'eau, le fond adouci reste sous le niveau de l'eau ; tracé inchangé
        neuf = np.where(mer, np.minimum(neuf, np.float32(-EAU_MIN_MER)), h).astype(np.float32)
        print(f"  rivage de WH1 : fond de la mer adouci sur {int((bande & mer).sum())} px (bande de {RIVAGE_BANDE} px), "
              f"terre et tracé de WH1 inchangés")
        return neuf, mer
    noyes = ~mer & bande & (neuf < 0) & (~garde if garde is not None else True)
    emerges = mer & bande & (neuf >= 0)
    print(f"  rivage naturel : {int(bande.sum())} px adoucis (bande de {RIVAGE_BANDE} px) ; terre passée sous l'eau "
          f"{int(noyes.sum())} px, fond sorti de l'eau {int(emerges.sum())} px"
          f"{' (devenu terre)' if RIVAGE_EMERGES else ''} ; écart max {float(np.abs(neuf - h)[bande].max()):.3f}")
    if RIVAGE_EMERGES:
        return neuf, (mer | noyes) & ~emerges
    return neuf, mer | noyes


def couleur_mer(mer):
    """(H, L, 4) uint8 : la couleur de la mer de WH1, ramenée canal par canal à la moyenne de CA sur notre mer
    (`COULEUR_MER_CA`)."""
    import entites_wh1
    c = entites_wh1.couleur_mer_wh1().astype(np.float64)
    if COULEUR_MER_CA is None:
        return c.astype(np.uint8)
    f = np.array(COULEUR_MER_CA) / np.maximum(c[mer][:, :3].mean(0), 1.0)
    c[..., :3] = np.clip(c[..., :3] * f, 0, 255)
    if COULEUR_MER_PLAFOND:
        # (25.09.2026, chaîne 16) WH1 peint ses hauts-fonds deux fois plus clair que le large ; x ~3 en plus, l'éventail des
        # deltas (79, 133, 131) et le bord des côtes (74, 125, 123) sortaient en nappe et liseré pâles (enquête
        # `scratchpad\enquete_deltas\`) : jamais au-dessus de la moyenne de CA, canal par canal
        c[..., :3] = np.minimum(c[..., :3], np.array(COULEUR_MER_CA, np.float64))
    print(f"  couleur de la mer : nuances de WH1 x {np.round(f, 2).tolist()} (moyenne de CA {COULEUR_MER_CA}"
          f"{', plafond' if COULEUR_MER_PLAFOND else ''})")
    return np.rint(c).astype(np.uint8)


# LE TON DES RIVIÈRES (25.09.2026, 03 h, chaîne 15, C2 ; enquête `scratchpad\enquete_rivieres\`) : le matériau d'eau teinte
# les rivières par `color_overlay_sea` ; la nôtre y portait la couleur de la mer (28, 55, 58) sur toute la terre ; chez CA,
# sous ses rivières, une couleur deux fois plus sombre (médiane (16, 28, 25)). WH1 : (33, 49, 57) sur ses captures.
COULEUR_SOUS_RIVIERES = (16, 28, 25, 255)
MARGE_SOUS_RIVIERES_PX = 2
# (25.09.2026, chaîne 16 ; enquête des deltas) la couleur de mer plafonnée à la moyenne de CA (voir `couleur_mer`) ; et le
# ton sombre des rivières sur toute la zone des deltas, mer de l'éventail comprise (WH1 : delta sombre, bras sombres)
COULEUR_MER_PLAFOND = True
# (25.09.2026, 15 h, chaîne 17 ; vidéo de Charles de 14 h 46) le ton sombre sur toute la zone des deltas faisait des taches
# d'encre aux embouchures (Bordeleaux) : coupé ; le lit sombre reste sous l'eau des rivières (C2).
DELTAS_SOMBRES = False


def couleur_sous_rivieres(c, mer, eau_rivieres, zone_delta=None):
    """`c` (H, L, 4) avec COULEUR_SOUS_RIVIERES sous l'eau des rivières (+ MARGE_SOUS_RIVIERES_PX), hors mer ; avec
    DELTAS_SOMBRES, sur toute `zone_delta` aussi."""
    if COULEUR_SOUS_RIVIERES is None or eau_rivieres is None:
        return c
    zone = rivieres_wh1.dilater(np.isfinite(eau_rivieres), MARGE_SOUS_RIVIERES_PX) & ~mer
    if DELTAS_SOMBRES and zone_delta is not None and zone_delta.any():
        zone |= zone_delta
    c = c.copy()
    c[zone] = np.array(COULEUR_SOUS_RIVIERES, c.dtype)
    print(f"  ton des rivières (color_overlay_sea) : {int(zone.sum())} px à {COULEUR_SOUS_RIVIERES[:3]}")
    return c


# LE MATÉRIAU DES LACS (25.09.2026, 04 h 50, chaîne 16 ; Charles, vidéo de 04 h 10 : « petits problèmes pour les lacs » ;
# accord à 04 h 42 ; enquête `scratchpad\enquete_eau_mouvement\`) : nos 26 lacs partageaient le matériau des rivières ; avec
# river_depth_max_point à 0,2 (rivières sombres), leurs 0,2 à 0,3 u d'eau passaient en « eau profonde » : aplat turquoise.
# Comme CA (`cwb_cmapaign_lake`), un matériau de lac à nous (session IA, `masques_eau_carte.py` : copie avec 0,8), écrit à
# l'étape « masques eau » de la chaîne, APRÈS ce générateur : cité dès que notre matériau d'eau existe.
MATERIAU_LACS = "materials/environment/campaign_sea/wh_dlc05_wood_elves_campaign_lake_plane.xml.material"


def materiau_lacs():
    import eau_carte
    return MATERIAU_LACS if MATERIAU_LACS and eau_carte.materiau() == eau_carte.MATERIAU_NOUS else \
        props_wh1_vers_layers.MATERIAU_EAU


# LA SURFACE DE LA MER (23.09.2026, 20 h 55, session du rendu ; Charles en jeu, pack de 20 h 42 : « toujours pas d'eau »,
# après le fond sous 0 de FOND_SOUS_ZERO). Relevé du projet des Empires (brouillon `polygones_eau_ie.py`) : leur mer est
# COUVERTE de polygones d'eau (`ECPolygonMesh` au matériau d'eau de la carte, y = 0, jusqu'à 35 000 u² chacun, 30 points
# environ ; visibles sous le linceul, jamais écartés), le relief traçant la côte (la terre au-dessus de 0 cache le plan) ;
# notre projet n'en avait que pour les 26 étangs : aucune surface d'eau sur la mer. Chaque mer de WH1 (composante de la mer au
# pixel, élargie de MER_PLAN_MARGE sous la côte) reçoit son polygone, simplifié à MER_PLAN_TOLERANCE (moins que la marge :
# il couvre toujours toute l'eau), sans ses trous (les îles sont au-dessus de l'eau). Contrôle : aucune terre sous 0 dans
# l'emprise hors des lits de rivière qui descendent à la mer.
MER_PLANS = True
MER_PLAN_Y = 0.0
MER_PLAN_MARGE, MER_PLAN_TOLERANCE = 0.6, 0.2     # unités du monde
# (24.09.2026, chaîne 12 ; capture de Charles, 18 h 30 : éclats pâles en escalier le long des côtes) la marge de 0,6 u, à
# angles vifs, dépassait de la côte lissée ; vue de loin, le jeu simplifie le relief et la terre basse du bord (2,5 cm en
# médiane dans le premier dixième d'unité) découvrait le plan. Avec le découpage de WH1 (`cotes_wh1.LISSAGE = False`), le
# plan suit la côte à la case près : une marge juste assez large pour glisser sous le bord de la terre.
MER_PLAN_MARGE, MER_PLAN_TOLERANCE = 0.15, 0.05
# LE PLAN SUR LA CÔTE, PLUS SUR LES CASES (24.09.2026, 22 h 50, chaîne 13, avec la côte lisse remise) : le contour des cases
# de 4 x 4 px (0,33 u) suivait l'escalier de WH1 ; sous une côte lisse, ses angles passaient sous la terre basse du bord et
# ressortaient de loin (éclats pâles en escalier de la capture de 18 h 30). Désormais le plan suit la mer finale au pixel
# (contour d'OpenCV), élargie de MER_PLAN_MARGE : une courbe parallèle à la côte, glissée sous le bord de la terre.
MER_PLAN_CONTOUR = True
MER_PLAN_AIRE_MIN = 0.5                          # u² : les flaques de mer plus petites sont laissées
# LE PIVOT DANS LA CARTE (23.09.2026, 21 h 25, chaîne 5) : pivot au premier point du contour (x = -0,6, marge hors de la
# carte), BOB a écarté le plan (« Failed to find valid quadtree node for Polygon Mesh entity… Check object
# position/bounds » ; global_props.bin : 26 plans d'eau, ceux des étangs, pour 27 dans les calques). Les 997 plans d'eau
# des Empires ont tous leur pivot dans la carte (x >= 5,7 ; z >= 8), dans la boîte du polygone pour 991, alors que les
# points de 11 d'entre eux en sortent (jusqu'à -3,8) (brouillon `bornes_polygones_ie.py`). Pivot : un point intérieur du
# polygone, ramené à MER_PLAN_BORD_PIVOT des bords de la carte.
MER_PLAN_BORD_PIVOT = 0.5


# LES EMBOUCHURES SOUS LE PLAN D'EAU (23.09.2026, 23 h 10, session du rendu ; Charles, captures de 22 h 56 : « le rendu des
# rivières qui plongent dans l'eau de mer, c'est très moche »). Le plan d'eau de la mer déborde de MER_PLAN_MARGE sous la
# côte ; sur ces derniers 0,6 u, le ruban de la rivière (entre 0 et +5 cm) et le plan (0) se superposaient presque au même
# niveau : double eau, couture et scintillement. Désormais la rivière descend au niveau de la mer au bord du plan
# (`descente_vers_la_mer`), puis passe dessous (`plongee`), son lit sous 0 : c'est la mer qui remplit l'estuaire. L'emprise
# est celle du plan à coup sûr (marge moins la tolérance de simplification) : une emprise trop large laisserait un lit sec.
EMBOUCHURES_SOUS_LE_PLAN = True


def emprise_plan_mer(mer):
    """Pixels sûrement sous le plan d'eau de la mer : cases de 4 x 4 px portant de la mer, élargies (Tchebychev) de
    MER_PLAN_MARGE - MER_PLAN_TOLERANCE, en lignes de raster (le z du monde y est x √3/2)."""
    Hh, Ll = mer.shape
    n = int((MER_PLAN_MARGE - MER_PLAN_TOLERANCE) * Ll / float(LARGEUR_MONDE) * 3 ** 0.5 / 2)
    if MER_PLAN_CONTOUR:
        return rivieres_wh1.dilater(mer, n) if n > 0 else mer.copy()
    cases = np.repeat(np.repeat(mer.reshape(Hh // 4, 4, Ll // 4, 4).any((1, 3)), 4, 0), 4, 1)
    return rivieres_wh1.dilater(cases, n)


def _polygones_contour(mer, pas):
    """Polygones (shapely, monde : x vers l'est, z vers le nord) de la mer au pixel élargie de MER_PLAN_MARGE : contours
    extérieurs d'OpenCV sur le masque élargi (les îles restent des trous, ignorés comme avant)."""
    import cv2
    from shapely.geometry import Polygon
    Hh, Ll = mer.shape
    r3 = 3 ** 0.5 / 2
    n = max(int(round(MER_PLAN_MARGE * pas)), 1)
    large = rivieres_wh1.dilater(mer, n).astype(np.uint8)
    contours, _ = cv2.findContours(large, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    for c in contours:
        c = c[:, 0, :].astype(np.float64)             # (colonne, ligne) des centres des pixels du bord
        if len(c) < 3:
            continue
        # le bord du masque élargi passe à un demi-pixel au-delà des centres : on pousse d'un demi-pixel vers l'extérieur
        # par un tampon, après conversion au monde
        x = (c[:, 0] + 0.5) / pas
        z = ((Hh - 1.5) - c[:, 1]) / pas / r3
        p = Polygon(np.c_[x, z])
        if not p.is_valid:
            p = p.buffer(0)
        p = p.buffer(0.5 / pas, join_style=2)
        polys.extend(list(p.geoms) if hasattr(p, "geoms") else [p])
    return polys


def polygones_mer(r):
    """[blocs XML] des plans d'eau de la mer (un par mer de WH1) et bilan."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    mer = np.asarray(r["mer"], bool)
    Hh, Ll = mer.shape
    pas = Ll / float(LARGEUR_MONDE)
    r3 = 3 ** 0.5 / 2
    if MER_PLAN_CONTOUR:
        polys = _polygones_contour(mer, pas)
    else:
        # cases de 4 x 4 px (0,33 u) portant de la mer : boîtes en coordonnées du monde (x vers l'est, z vers le nord)
        cases = mer.reshape(Hh // 4, 4, Ll // 4, 4).any((1, 3))
        boites = []
        for ci, cj in zip(*np.nonzero(cases)):
            x0, x1 = cj * 4 / pas, (cj + 1) * 4 / pas
            # le pixel de ligne i est centré en z = ((H - 1,5) - i) / pas / r3 : bords nord et sud de la case
            z_haut = ((Hh - 1) - ci * 4) / pas / r3
            z_bas = ((Hh - 1) - (ci + 1) * 4) / pas / r3
            boites.append(box(x0, z_bas, x1, z_haut))
        union = unary_union(boites).buffer(MER_PLAN_MARGE, join_style=2)
        polys = list(union.geoms) if hasattr(union, "geoms") else [union]
    profondeur = (Hh - 1) / pas / r3
    blocs, bilan = [], {"plans": 0, "aire (u²)": 0.0, "points": [], "aire de la mer (u²)": round(mer.sum() / pas ** 2 / r3, 1),
                        "pivots": []}
    for k, p in enumerate(sorted(polys, key=lambda p: -p.area)):
        if p.area < MER_PLAN_AIRE_MIN:
            continue
        ext = type(p)(p.exterior).simplify(MER_PLAN_TOLERANCE, preserve_topology=True)
        pts = list(ext.exterior.coords)[:-1]
        c = ext.representative_point()
        X0 = min(max(c.x, MER_PLAN_BORD_PIVOT), float(LARGEUR_MONDE) - MER_PLAN_BORD_PIVOT)
        Z0 = min(max(c.y, MER_PLAN_BORD_PIVOT), profondeur - MER_PLAN_BORD_PIVOT)
        bilan["pivots"].append((round(X0, 2), round(Z0, 2)))
        points = "".join(f'\t\t\t\t\t<point x="{x - X0:.5f}" y="{z - Z0:.5f}"/>\n' for x, z in pts)
        blocs.append(f'\t\t<entity id="{ident(f"mer:plan:{k}")}">\n'
                     f'\t\t\t<ECPolygonMesh material="{eau_carte.materiau()}" affects_mesh_optimization="false"/>'
                     '<ECVisibilitySettingsCampaign visible_in_tactical_view="True" visible_in_tactical_view_only="False"/>\n'
                     '\t\t\t<ECCampaignProperties visible_in_shroud="True" no_culling="true" culture_mask=""/>\n'
                     f'\t\t\t<ECTransform position="{X0:.5f} {MER_PLAN_Y:.5f} {Z0:.5f}" rotation="0. 0. 0." scale="1. 1. 1." '
                     'pivot="0 0 0"/>\n'
                     '\t\t\t<ECPolyline>\n\t\t\t\t<polyline closed="true">\n' + points +
                     '\t\t\t\t</polyline>\n\t\t\t</ECPolyline>\n\t\t</entity>\n')
        bilan["plans"] += 1
        bilan["aire (u²)"] = round(bilan["aire (u²)"] + ext.area, 1)
        bilan["points"].append(len(pts))
    return blocs, bilan


def approfondir_mer(fond, mer, garde=None):
    """(fond, bilan) : sur la mer, le fond au plus haut au profil de CA (`PROF_COTE`, `PROF_LARGE`, `ECHELLE_PROF`) selon
    la distance à la terre, sauf les hauts-fonds de WH1 au large (au-dessus de HAUT_FOND à plus d'une demi-unité de la
    côte) et `garde` (24.09.2026 : la mer des deltas de WH1, au fond de WH1)."""
    pas = L / float(LARGEUR_MONDE)
    portee = int(12 * pas)
    d = distance_a(~mer, portee) / pas                      # unités (4-connexe, au plus 12 u)
    if FOND_SOUS_ZERO and COTE_DOUCE:
        # (21 h 55) pente douce depuis le bord de l'eau : -0,11 au premier pixel, -0,25 à une case, -0,34 à une demi-unité
        profil = -(PROF_DOUCE_BORD + (PROF_ABS_LARGE - PROF_DOUCE_BORD) * (1.0 - np.exp(-d / ECHELLE_PROF_DOUCE)))
    elif FOND_SOUS_ZERO:
        # (19 h 40) fond absolu sous le niveau de l'eau (0), comme aux Empires : -0,40 à la côte, -0,95 au large
        profil = -(PROF_ABS_COTE + (PROF_ABS_LARGE - PROF_ABS_COTE) * (1.0 - np.exp(-d / ECHELLE_PROF_ABS)))
    else:
        # profondeur height - sea_height des Empires sous notre height de mer (HAUTEUR_SUR_MER)
        profil = HAUTEUR_SUR_MER - (PROF_COTE + (PROF_LARGE - PROF_COTE) * (1.0 - np.exp(-d / ECHELLE_PROF)))
    haut_fond = (fond > HAUT_FOND) & (d > 0.5)
    if garde is not None:
        haut_fond = haut_fond | garde
    neuf = np.where(mer & ~haut_fond, np.minimum(fond, profil), fond).astype(np.float32)
    avant, apres = fond[mer], neuf[mer]
    bilan = {"fond de WH1 p50": round(float(np.median(avant)), 3), "après p10/p50/p90":
             np.round(np.percentile(apres, [10, 50, 90]), 3).tolist(), "abaissés (px)": int((apres < avant - 1e-4).sum()),
             "hauts-fonds de WH1 gardés (px)": int((mer & haut_fond).sum())}
    return neuf, bilan


def contour_naturel(masque, rayon=8, amplitude=0.22, echelle=24, graine=7):
    """Masque au bord naturel : moyenne sur une fenêtre de 2 x `rayon` + 1 px, plus un bruit lisse déterministe
    (± `amplitude`, grain de `echelle` px), seuillée à 0,5. Remplace les blocs d'hex (22.09.2026, 21 h 10 ; Charles :
    « des carrés de différentes couleurs » : les éboulis des hex de montagne formaient des plaques à bords d'hex)."""
    h, w = masque.shape
    k = 2 * rayon + 1
    f = moyenne_boite(masque.astype(np.float64), rayon) / (k * k)
    rng = np.random.default_rng(graine)
    gh, gw = h // echelle + 2, w // echelle + 2
    g = rng.uniform(-amplitude, amplitude, (gh, gw))
    yy, xx = np.mgrid[0:h, 0:w] / echelle
    y0, x0 = yy.astype(int), xx.astype(int)
    ty, tx = yy - y0, xx - x0
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    bruit = (g[y0, x0] * (1 - tx) * (1 - ty) + g[y0, x0 + 1] * tx * (1 - ty)
             + g[y0 + 1, x0] * (1 - tx) * ty + g[y0 + 1, x0 + 1] * tx * ty)
    return (f + bruit) > 0.5


def moyenne_boite(a, r):
    """Somme de `a` sur une fenêtre carrée de côté 2r + 1 (images intégrales), bords compris."""
    p = np.pad(a, r + 1, mode="constant")
    s = p.cumsum(0).cumsum(1)
    n, m = a.shape
    k = 2 * r + 1
    return s[k:k + n, k:k + m] - s[:n, k:k + m] - s[k:k + n, :m] + s[:n, :m]


def sol_wh1(lf):
    """Le vrai sol de WH1 (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\relief-tuiles-wh1.md`) : ses
    maillages de terrain (`relief_maillages_wh1.py`), là où ils existent (64 % de la carte) ; ses objets y sont
    posés au centimètre (médiane 0,03), contre 0,26 au-dessus de `lf_height_map`. Ailleurs (tuiles de montagne,
    de falaise, de rivière, que WH1 dessine par leurs propres maillages), le relief de base plus l'écart
    maillages - base prolongé en douceur (moyennes de voisinage de plus en plus larges) : pas de marche au bord.
    Rend (hauteur, masque des pixels où le sol de WH1 est connu exactement)."""
    if not os.path.exists(RELIEF_MAILLAGES):
        raise SystemExit(f"{RELIEF_MAILLAGES} absent : lancer relief_maillages_wh1.py --apply")
    m = np.load(RELIEF_MAILLAGES).astype(np.float64)
    if m.shape != lf.shape:
        raise SystemExit(f"relief des maillages {m.shape} au lieu de {lf.shape}")
    connu = np.isfinite(m)
    d = np.where(connu, m - lf, 0.0)
    rempli = np.full(lf.shape, np.nan)
    for r in (24, 96, 384):
        poids = moyenne_boite(connu.astype(np.float64), r)
        somme = moyenne_boite(d, r)
        neuf = np.isnan(rempli) & (poids > 0)
        rempli[neuf] = somme[neuf] / poids[neuf]
    rempli[np.isnan(rempli)] = float(np.median(d[connu]))
    ecart = np.where(connu, d, rempli)
    print(f"  sol de WH1 (maillages) : {connu.mean():.1%} des pixels ; écart au relief de base "
          f"p5/p50/p95 {np.round(np.percentile(d[connu], [5, 50, 95]), 3).tolist()}")
    return (lf + ecart).astype(np.float32), connu


def grille_parcelles(lt, ht):
    """Grille des parcelles de terrain pour une carte de tuiles de lt x ht px : la parcelle fait
    p = plafond(plus grand cote / 128) px, la grille (lt // p) x (ht // p). Empires 2880 x 1941 :
    p = 23, 125 x 84 ; prologue 1600 x 1201 : p = 13, 123 x 92 ; notre carte 800 x 881 : p = 7,
    114 x 125 (tailles des `patch_mask.dds` compiles, les trois verifiees le 22.09.2026)."""
    p = -(-max(lt, ht) // 128)
    return lt // p, ht // p


def taille_pvm():
    """Une case par parcelle, comme le `patch_mask.dds` que BOB compile. L'ancienne regle (une case
    par 7,68 unites du monde, tiree des seuls Empires) donnait 34 x 38 : Terry ne dessinait alors
    le sol que dans les 34 x 38 premieres parcelles, le ciel au travers ailleurs (erreur 70)."""
    return grille_parcelles(L // 4, (H + 3) // 4)


def controle_pvm():
    """Garde de l'erreur 70 : la regle redonne la grille des Empires (125 x 84, leur `.terry`) et,
    si BOB a deja compile notre terrain, celle de notre `patch_mask.dds`."""
    assert grille_parcelles(2880, 1941) == (125, 84), grille_parcelles(2880, 1941)
    compile_ = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE, "patch_mask.dds")
    if os.path.exists(compile_):
        with open(compile_, "rb") as f:
            h, w = struct.unpack_from("<II", f.read(20), 12)
        if (w, h) != taille_pvm():
            raise SystemExit(f"patch_mask.dds compile par BOB : {w} x {h} ; regle : {taille_pvm()} : a revoir")
    print(f"PatchVisibilityMask : {taille_pvm()[0]} x {taille_pvm()[1]} (une case par parcelle)")


def palette_de(nom_ie):
    return Image.open(os.path.join(IE, nom_ie)).getpalette()


def ecrire_tif(chemin, img):
    """Meme organisation que les tif du projet des Empires (ecrits par Terry) : LZW, une ligne
    par bande pour les grandes cartes, cinq pour les masques, et l'etiquette SampleFormat sur les
    images 8 bits. Avec les bandes de 5 a 81 lignes que Pillow fait par defaut, Terry plantait a
    l'ouverture du projet (21.09.2026)."""
    lignes = 1 if img.size[0] >= 1600 else 5
    octets = {"F": 4, "RGBA": 4, "L": 1, "P": 1}[img.mode] * img.size[0]
    # une seule valeur : libtiff l'etend a chaque couche ; (1, 1, 1, 1) donnait un fichier illisible.
    # SamplesPerPixel (277) ecrit explicitement pour les images a une couche, comme chez CA :
    # Pillow l'omet (c'est la valeur par defaut de la norme).
    info = {} if img.mode == "F" else {339: 1}
    if len(img.getbands()) == 1:
        info[277] = 1
    img.save(chemin, compression="tiff_lzw", strip_size=lignes * octets, tiffinfo=info)


def controles(r):
    os.makedirs(CONTROLE, exist_ok=True)
    h = r["hauteur"][::4, ::4]
    gy, gx = np.gradient(h)
    ombre = np.clip(0.55 + 3.0 * (gx - gy), 0, 1)                 # relief ombre, lumiere nord-ouest
    teinte = np.clip(h / 12, 0, 1)
    rgb = np.stack([90 + 150 * teinte, 130 + 90 * teinte, 70 + 150 * teinte], -1) * ombre[..., None]
    rgb[r["mer"][::4, ::4]] = (40, 70, 140)
    Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).save(os.path.join(CONTROLE, "relief.png"))
    pal = np.array(palette_de(next(n for n in os.listdir(IE) if ".blend." in n))[:768]).reshape(256, 3)
    Image.fromarray(pal[r["melange"][::4, ::4]].astype(np.uint8)).save(os.path.join(CONTROLE, "textures.png"))
    Image.fromarray(r["tuiles"]).save(os.path.join(CONTROLE, "tile_map.png"))
    # arbres (couleur de leur famille de WH3) sur le relief ombre, routes en brun
    pal_arbres = np.array(palette_de(next(n for n in os.listdir(IE) if ".tree." in n))[:768]).reshape(256, 3)
    fond = rgb.clip(0, 255).astype(np.uint8)          # relief au quart : 800 x 881, comme tree.tif
    assert fond.shape[:2] == r["arbres"].shape, (fond.shape, r["arbres"].shape)
    a = r["arbres"] != PAS_D_ARBRE
    fond[a] = pal_arbres[r["arbres"][a]]
    fond[r["route"]] = COULEUR_ROUTE[:3]
    Image.fromarray(fond).save(os.path.join(CONTROLE, "arbres_routes.png"))
    print(f"  controles : {CONTROLE} (relief.png, textures.png, tile_map.png, arbres_routes.png)")


def ecrire_terry_user(ids_cartes):
    """Réglages d'aperçu du projet pour Terry (`<carte>.terry.user`, 22.09.2026, 22 h ; Charles : « pourquoi l'eau et
    les arbres ne s'affichent pas ? »). Le projet des Empires en a un (plan d'eau, végétation, culture de l'aperçu...) ;
    le nôtre n'en avait pas (le dossier est recréé à chaque génération). Même contenu que celui des Empires, sauf :
    plan d'eau affiché, culture de l'aperçu = elfes sylvains (les arbres et les décors propres à une culture suivent
    ce choix), identifiants de nos cartes, caméra au-dessus de notre carte."""
    t = open(os.path.join(IE, "wh3_main_combi_map_1.terry.user"), encoding="utf-8").read()
    t = re.sub(r'excluded_components="[^"]*"', 'excluded_components=""', t)
    t = re.sub(r'<water_plane value="\w+"/>', '<water_plane value="true"/>', t)
    t = re.sub(r'<show_vegetation value="\w+"/>', '<show_vegetation value="true"/>', t)
    t = re.sub(r'<culture value="[^"]*"/>', f'<culture value="{CULTURE_APERCU}"/>', t)
    cartes = "".join(f'    <terrain_map id="{i}">\n      <frozen_layers></frozen_layers>\n    </terrain_map>\n'
                     for i in ids_cartes)
    t = re.sub(r"  <terrain>\n.*?  </terrain>\n", "  <terrain>\n" + cartes + "  </terrain>\n", t, flags=re.S)
    t = re.sub(r'(<ECTransform position=")[^"]*(" rotation=")[^"]*(")',
               r'\g<1>133.0 70.0 40.0\g<2>50.0 0.0 0.0\g<3>', t, count=1)
    t = re.sub(r'<target_distance value="[^"]*"/>', '<target_distance value="120.0"/>', t)
    if f'<culture value="{CULTURE_APERCU}"/>' not in t or '<water_plane value="true"/>' not in t:
        raise SystemExit("réglages d'aperçu de Terry : modèle des Empires inattendu")
    with open(os.path.join(PROJET, f"{CARTE}.terry.user"), "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


def ecrire_projet(r, regions):
    # Les objets de WH1 sont calcules AVANT de toucher au projet existant : le 21.09.2026 (21 h 46),
    # un controle qui echouait apres la suppression laissait le projet Terry a moitie ecrit.
    # les étangs (23.09.2026, session du rendu, `etangs_wh1`) remplacent les carrés d'eau des plans d'eau de WH1
    etangs_xml = None
    if r.get("etangs"):
        etangs_xml = {et["lac"]["cle"]: etangs_wh1.entite(et, r["grille"], materiau_lacs())
                      for et in r["etangs"]}
    objets, bilan, absents = props_wh1_vers_layers.entites_par_region(
        float(LARGEUR_MONDE), r["sol_objets"], r["sol_objets_wh1"], set(regions), sol_connu=r["sol_connu"],
        etangs=etangs_xml, montagnes=r.get("montagnes_wh1"))
    # les arbres de WH1 à leurs positions de WH1 (22.09.2026, 22 h) : liste écrite pour build_pack.py ; aucun dans l'eau
    # des étangs
    # (chaîne 14) ni dans l'eau des étangs, ni au pied des décors du Pré de Ceren (`decors_carte_wh3.sans_arbres`)
    import decors_carte_wh3
    hors_arbres = decors_carte_wh3.sans_arbres(H, L, L / float(LARGEUR_MONDE))
    if r.get("eau_etangs") is not None:
        hors_arbres = hors_arbres | np.asarray(r["eau_etangs"], bool)
    # (chaîne 14 ; audit de toute la carte : 29 grands arbres dans la mer au sud-ouest de Brionne, 140 dans l'eau des
    # rivières, un arbre à 0,13 u du centre de Tal Esth) ni dans la mer, ni dans l'eau visible des rivières, ni à moins de
    # ARBRES_CENTRE_COLONIE u du centre d'une colonie
    eau_r = np.asarray(r["eau_rivieres"], np.float64)
    hors_arbres = hors_arbres | np.asarray(r["mer"], bool) | (np.nan_to_num(eau_r, nan=-9.0) > np.asarray(r["hauteur"]) + 0.005)
    if os.path.exists(COLONIES_MAP_DATA):
        import json
        pas_c = L / float(LARGEUR_MONDE)
        for v in json.load(open(COLONIES_MAP_DATA, encoding="utf-8"))["keys"].values():
            ci, cj = (H - 1.5) - float(v[1]) * 3 ** 0.5 / 2 * pas_c, float(v[0]) * pas_c - 0.5
            n = int(ARBRES_CENTRE_COLONIE * pas_c) + 2
            i0, i1, j0, j1 = max(int(ci) - n, 0), min(int(ci) + n + 1, H), max(int(cj) - n, 0), min(int(cj) + n + 1, L)
            ii, jj = np.mgrid[i0:i1, j0:j1]
            hors_arbres[i0:i1, j0:j1] |= np.hypot((ii - ci) / (3 ** 0.5 / 2 * pas_c), (jj - cj) / pas_c) <= ARBRES_CENTRE_COLONIE
    liste, comptes = ArbresWH1().liste_wh1(r["hauteur"], r["hauteur_wh1"], L / float(LARGEUR_MONDE),
                                           hors=hors_arbres)
    # rochers et herbes de montagne de CA (23.09.2026, session du rendu, `ajouts_carte_wh3`)
    import ajouts_carte_wh3
    liste, bilan_rochers = ajouts_carte_wh3.arbres(liste, r)
    print(f"  rochers et herbes de montagne de CA : {bilan_rochers}")
    # la liste est écrite après les ponts (plus bas) : aucun arbre sur un pont
    if objets.get(None):
        raise SystemExit(f"{len(objets[None])} objets dans une region absente du projet : a ranger")
    # Lumières, sons, effets et scènes de faune de WH1 (22.09.2026, 23 h 50 ; `entites_wh1.py`, session d'audit) :
    # positions de WH1 (monde, espace hex), hauteur recalée de ce dont notre sol diffère de celui de WH1 à cet endroit
    import entites_wh1
    # (24.09.2026, chaîne 13) sur les montagnes de WH1, le sol affiché ; près d'un objet déplacé par les règles des
    # montagnes (brasero posé au contact), son déplacement (`props_wh1_vers_layers.suivre_les_objets`)
    sol_nous = props_wh1_vers_layers.sol_des_objets(r["sol_objets"], r["sol_objets_wh1"], r.get("montagnes_wh1"))
    sol_eux = r["sol_objets_wh1"]
    pas_px = L / float(LARGEUR_MONDE)

    def recaler_y(x, y, z):
        c = int(min(max(x * pas_px, 0), L - 1))
        lig = int(min(max((H - 1) - z * props_wh1_vers_layers.Z_VERS_RASTER * pas_px, 0), H - 1))
        return y + float(sol_nous[lig, c] - sol_eux[lig, c]) + props_wh1_vers_layers.suivre_les_objets(x, z)
    bilan_ambiance = {}
    ambiance = entites_wh1.entites_ambiance(recaler_y=recaler_y, bilan=bilan_ambiance)
    print(f"  ambiance de WH1 : {sum(len(v) for v in ambiance.values())} entités ; {bilan_ambiance}")
    # les ponts de WH1 (23.09.2026, session du rendu, `ponts_wh1`) : objets des tuiles `river_crossing` ; plan des
    # traversées (`ajouts_carte_wh3.plan_ponts`) : en Athel Loren les ponts de WH1 (recopiés là où WH1 n'en avait pas),
    # ailleurs le pont de pierre de CA remplaçait la passerelle (Charles, 23.09.2026, 17 h 30) ; depuis 22 h 40 (« tout ce
    # qui est de base doit être 100 % WH1 »), partout les ponts de WH1 recalés (`AJOUTS["plan_ponts"]`, `ponts_ca` éteint)
    import ponts_wh1
    ponts, bilan_ponts = [], {}
    if ponts_wh1.ACTIF:
        plan = (ajouts_carte_wh3.plan_ponts(r) if ajouts_carte_wh3.AJOUTS.get("ponts_ca")
                or ajouts_carte_wh3.AJOUTS.get("plan_ponts") else [])
        remplacees = {p["pose_wh1"]: (p["x"], p["z"], p["lacet"]) for p in plan
                      if p["genre"] == "pierre" and p["pose_wh1"] is not None}
        nouveaux = [(p["x"], p["z"], p["angle"]) for p in plan if p["genre"] == "wh1" and p["pose_wh1"] is None]
        traversees = {p["pose_wh1"]: (p["x"], p["z"], p["angle"]) for p in plan
                      if p["genre"] == "wh1" and p["pose_wh1"] is not None}
        ponts = ponts_wh1.entites(r["hauteur"], r["eau_rivieres"], pas_px, bilan_ponts, remplacees, nouveaux, traversees)
        print(f"  ponts de WH1 : {len(ponts)} objets ; {bilan_ponts}")
    # ce que WH3 ajoute (23.09.2026, session du rendu, `ajouts_carte_wh3`) : son et scintillement des braseros (leur
    # lumière fixe remplacée), habillage des étangs, moulins, fumées, libellules, nuages
    ajouts, ambiance, bilan_ajouts = ajouts_carte_wh3.entites(r, ambiance, objets)
    print(f"  ajouts de WH3 : {len(ajouts)} entités ; {bilan_ajouts}")
    # la liste des arbres, sans arbre sur un pont (passerelle, pont de pierre, dallage)
    liste, n_ponts = ajouts_carte_wh3.degager_arbres(liste, ponts + ajouts)
    os.makedirs(os.path.dirname(SORTIE_LISTE_ARBRES), exist_ok=True)
    with open(SORTIE_LISTE_ARBRES, "wb") as f:
        f.write(liste)
    print(f"  arbres de WH1 à leurs positions : {sum(comptes.values())} en {len(comptes)} essences, {n_ponts} retirés des "
          f"ponts -> {SORTIE_LISTE_ARBRES}")
    # les montagnes de WH1 (22.09.2026, `montagnes_wh1.py`) : maillages drapés et textures écrits dans le dossier du
    # projet de l'atelier et dans `working_data` ; un calque d'objets `montagnes_wh1`
    # (24.09.2026) seules les falaises de côte qui touchent encore la côte naturelle (`cotes_wh1`) sont posées
    montagnes, _ = montagnes_wh1.construire(ecrire=True, mer=r["mer"])
    # eau lisse et reliée sur tout le réseau de WH1 (23.09.2026, 05 h 30 : courbe de niveau du champ, plus de carrés)
    # (18 h 55 : coordonnées de texture le long du courant, comme les rubans des Empires : `rivieres_wh1.UV_LE_LONG`)
    rivieres = (rivieres_wh1.construire_lisse(r["eau_rivieres"], r["champ_rivieres"], L / float(LARGEUR_MONDE),
                                              ecrire=True, mer=r["mer"])[0] if RIVIERES_WH1 else [])
    if os.path.exists(PROJET):
        dest = os.path.join(ATELIER, "05-journal", "terrain-backups", f"{CARTE}-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.copytree(PROJET, dest)
        shutil.rmtree(PROJET)
        print(f"  projet existant sauvegarde : {dest}")
    os.makedirs(PROJET)
    ids = {nom: (ident(f"carte:{nom}"), ident(f"calque:{nom}")) for _, nom, _ in CARTES}

    b = Image.fromarray(r["melange"], "P")
    b.putpalette(palette_de(next(n for n in os.listdir(IE) if ".blend." in n)))
    arbres = Image.fromarray(r["arbres"], "P")
    arbres.putpalette(palette_de(next(n for n in os.listdir(IE) if ".tree." in n)))
    contenu = {
        "height": Image.fromarray(r["hauteur"], "F"),
        "sea_height": Image.fromarray(r["hauteur_mer"], "F"),
        "height_shroud": Image.fromarray(np.ones((H // 2, L // 2), np.float32), "F"),
        "blend": b,
        "color_overlay": Image.new("RGBA", (L, H), OVERLAY),
        # la couleur de la mer de WH1, case par case (`entites_wh1.couleur_mer_wh1`, 22.09.2026, 23 h 50 ; audit, lot 3 :
        # notre mer uniforme (24, 32, 41) était plus claire et moins verte que la sienne), à la luminosité de CA
        "color_overlay_sea": Image.fromarray(couleur_sous_rivieres(couleur_mer(r["mer"]), r["mer"], r["eau_rivieres"],
                                                                   r.get("zone_delta")), "RGBA"),
        "tree": arbres,
        "corruption_mask": Image.fromarray(masque_corruption(r["mer"]), "L"),
        "snow_mask": Image.fromarray(r["neige"], "L"),
    }
    for _, nom, taille in CARTES:
        img = contenu[nom]
        assert img.size == taille, (nom, img.size, taille)
        ecrire_tif(os.path.join(PROJET, f"{CARTE}.{nom}.{ids[nom][1]}.tif"), img)
    # Le masque de visibilite des zones n'a pas de calque dans le `.terry` des Empires, mais son
    # fichier est dans le dossier (tout a 255) : Terry le cherche par son nom. Sans lui, Terry
    # plantait en ouvrant le projet (21.09.2026, pointeur nul dans `warscape`, pres de
    # `TERRAIN_RENDER_SETUP::apply_mask_map`).
    ecrire_tif(os.path.join(PROJET, f"{CARTE}.patch_visibility_mask.{ident('calque:patch_visibility_mask')}.tif"),
               Image.new("L", taille_pvm(), 255))
    Image.fromarray(r["tuiles"], "RGBA").save(os.path.join(PROJET, "tile_map.png"))

    entites = "".join(
        f'      <entity id="{ident("region:" + k)}" name="{k}">\n'
        f'        <ECFileLayer export="true" bmd_export_type=""/>\n'
        f'      </entity>\n' for k in regions)
    # les zones d'eclairage de WH1 (22.09.2026, 18 h) : BOB ecrit `environment_collection.xml` d'apres les
    # entites `ECEnvironmentVolume` du projet et efface toute autre version (`eclairage_wh1.zones`)
    global_eclairage, _ = eclairage_wh1.zones()
    entites += (f'      <entity id="{ident("calque:eclairage_wh1")}" name="eclairage_wh1">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
    entites += (f'      <entity id="{ident("calque:montagnes_wh1")}" name="montagnes_wh1">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
    entites += (f'      <entity id="{ident("calque:ambiance_wh1")}" name="ambiance_wh1">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
    if rivieres:
        entites += (f'      <entity id="{ident("calque:rivieres_wh1")}" name="rivieres_wh1">\n'
                    '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
        with open(os.path.join(PROJET, f"{CARTE}.{ident('calque:rivieres_wh1')}.layer"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- rivieres_wh1 -->\n<layer version="41">\n\t<entities>\n'
                    + "".join(rivieres) + '\t</entities>\n'
                    "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    with open(os.path.join(PROJET, f"{CARTE}.{ident('calque:ambiance_wh1')}.layer"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- ambiance_wh1 -->\n<layer version="41">\n\t<entities>\n'
                + "".join(e for k in sorted(ambiance, key=str) for e in ambiance[k]) + '\t</entities>\n'
                "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")

    # calques de la session du rendu (23.09.2026) : ponts de WH1, ajouts repris des Empires
    def calque(nom, blocs):
        with open(os.path.join(PROJET, f"{CARTE}.{ident('calque:' + nom)}.layer"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<!-- {nom} -->\n<layer version="41">\n\t<entities>\n'
                    + "".join(blocs) + '\t</entities>\n'
                    "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
        return (f'      <entity id="{ident("calque:" + nom)}" name="{nom}">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
    if ponts:
        entites += calque("ponts_wh1", ponts)
    if ajouts:
        entites += calque("ajouts_wh3", ajouts)
    # la surface de la mer (MER_PLANS, 23.09.2026, 20 h 55) : des plans d'eau comme les Empires
    if MER_PLANS:
        plans_mer, bilan_mer = polygones_mer(r)
        print(f"  surface de la mer : {bilan_mer}")
        if plans_mer:
            entites += calque("mer_wh1", plans_mer)
    with open(os.path.join(PROJET, f"{CARTE}.{ident('calque:montagnes_wh1')}.layer"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- montagnes_wh1 -->\n<layer version="41">\n\t<entities>\n'
                + "".join(montagnes) + '\t</entities>\n'
                "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    with open(os.path.join(PROJET, f"{CARTE}.{ident('calque:eclairage_wh1')}.layer"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- eclairage_wh1 -->\n<layer version="41">\n\t<entities>\n'
                + eclairage_wh1.entites_zones(ident) + '\t</entities>\n'
                "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    # les objets de WH1 (phase 6, 21.09.2026) : un calque par region, comme les Empires
    for k, v in bilan.items():
        print(f"     objets de WH1 : {k} : {v}")
    for k in regions:
        with open(os.path.join(PROJET, f"{CARTE}.{ident('region:' + k)}.layer"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    f"<!-- {k} -->\n"
                    '<layer version="41">\n\t<entities>\n' + "".join(objets.get(k, [])) + '\t</entities>\n'
                    "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    cartes = ""
    for type_, nom, (w, h) in CARTES:
        cartes += ('    <pc type="QTU::TerrainMap">\n'
                   f'      <data type="{type_}" size="{w}x{h}" id="{ids[nom][0]}"/>\n'
                   '      <pc type="QTU::TerrainMapLayer">\n'
                   f'        <data id="{ids[nom][1]}" name="base" visible="1" serializable="1" '
                   f'opacity="{OPACITE.get(type_, "1")}"/>\n'
                   "      </pc>\n    </pc>\n")
    pvm = ident("carte:patch_visibility_mask")
    w_pvm, h_pvm = taille_pvm()
    cartes += ('    <pc type="QTU::TerrainMap">\n'
               f'      <data type="PatchVisibilityMask" size="{w_pvm}x{h_pvm}" id="{pvm}"/>\n'
               "    </pc>\n")
    terry = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<project version="27" id="{ident("projet")}">\n'
             '  <pc type="QTU::ProjectTileMap">\n'
             f'    <data terrain_setup="terrain/campaigns/{CARTE}/" world_width="{LARGEUR_MONDE}" '
             f'global_lighting="{global_eclairage}" '
             f'ambient_light_environments="" water_plane_material="{eau_carte.materiau()}" '
             'extend_tile_blend_ranges_to_maximum="0"/>\n'
             "  </pc>\n"
             '  <pc type="QTU::Scene">\n    <data version="41">\n' + entites +
             "    </data>\n  </pc>\n"
             '  <pc type="QTU::Terrain">\n' + cartes + "  </pc>\n"
             '  <pc type="QTU::ProjectClimateMapFile"/>\n</project>\n')
    with open(os.path.join(PROJET, f"{CARTE}.terry"), "w", encoding="utf-8", newline="\n") as f:
        f.write(terry)
    ecrire_terry_user([ids[nom][0] for _, nom, _ in CARTES] + [pvm])
    regles = open(os.path.join(IE, "rules.bob"), encoding="utf-8").read().replace("wh3_main_combi_map_1", CARTE)
    with open(os.path.join(PROJET, "rules.bob"), "w", encoding="utf-8", newline="\n") as f:
        f.write(regles)
    # eclairage (22.09.2026) : celui de WH1, global et 7 zones, converti au format de WH3 (`eclairage_wh1.py`),
    # par-dessus ceux des Empires. Terry le lit sous le chemin de jeu `terrain/campaigns/<carte>/lighting/`,
    # c'est-a-dire dans le dossier CIBLE de `working_data` (celui que BOB remplit), pas dans le projet : sans
    # lui, Terry plantait a l'ouverture (21.09.2026). On l'installe aux deux endroits, avec
    # `environment_collection.xml` (les zones) dans `working_data`.
    eclairage_wh1.installer()
    print(f"  projet ecrit : {PROJET}")
    print(f"     {len(regions)} regions, {len(CARTES)} rasters, tile_map.png, rules.bob, lighting\\")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    controle_pvm()
    regions = regions_de_la_carte()
    print(f"{len(regions)} regions pour {CARTE}")
    r = rasters()
    # la mer finale et l'eau des rivières (grille des rasters, ligne 0 au nord), pour les masques de notre matériau d'eau
    # (session « IA et modding 3D », 23.09.2026 : le matériau d'eau de CA est propre à chaque carte)
    # (23.09.2026, session du rendu) seulement avec --apply : un essai à blanc ne change plus les entrées des masques d'eau
    dossier_relief = os.path.dirname(RELIEF_MAILLAGES)
    if a.apply:
        np.save(os.path.join(dossier_relief, "mer_finale.npy"), r["mer"])
        # les bancs de sable des deltas de WH1, pour leur texture (`textures_tuiles_wh1`, 24.09.2026, chaîne 12)
        np.save(os.path.join(dossier_relief, "delta_bancs.npy"), r["delta_bancs"])
        # l'emprise des maillages de montagne de WH1, pour les piémonts de `textures_sol_wh1` (23.09.2026, session du rendu)
        np.save(os.path.join(dossier_relief, "montagnes_wh1.npy"), r["montagnes"])
    if r.get("eau_rivieres") is not None and a.apply:
        np.save(os.path.join(dossier_relief, "eau_rivieres.npy"), r["eau_rivieres"])
        # le sens du courant, pour le masque de flux du matériau d'eau (23.09.2026, 06 h 05, `rivieres_wh1.flux_reseau`)
        flux, n_emb = rivieres_wh1.flux_reseau(r["eau_rivieres"], r["mer"])
        # (24.09.2026, chaîne 11) le courant sur les étangs et prolongé dans la mer à l'embouchure
        flux, bilan_flux = rivieres_wh1.flux_etangs_et_panaches(flux, r.get("eau_etangs"), r["mer"],
                                                                 L / float(LARGEUR_MONDE))
        print(f"courant des étangs et panaches d'embouchure : {bilan_flux}")
        np.save(os.path.join(dossier_relief, "flux_rivieres.npy"), flux)
        print(f"sens du courant des rivières : {int(np.isfinite(flux[..., 0]).sum())} px, {n_emb} pixels d'embouchure")
    h = r["hauteur"]
    print(f"hauteur : {h.min():.3f} a {h.max():.3f} ; terre p5/p50/p95 "
          f"{np.percentile(h[~r['mer']], [5, 50, 95]).round(3)} ; mer {np.percentile(h[r['mer']], [5, 50, 95]).round(3)}")
    print(f"mer : {r['mer'].mean():.1%} des pixels ; textures utilisees : "
          f"{sorted(np.unique(r['melange']).tolist())}")
    controles(r)
    if not a.apply:
        print("essai a blanc : relancer avec --apply pour ecrire le projet dans le kit")
        return 0
    ecrire_projet(r, regions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
