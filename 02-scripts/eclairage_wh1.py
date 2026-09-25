#!/usr/bin/env python3
"""
eclairage_wh1.py - l'éclairage par zones de Warhammer 1 (clairières d'Athel Loren, Bretonnie), converti au format
de Warhammer 3.

Pourquoi (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\eclairage-textures-wh1.md`) : notre carte prenait
l'éclairage des Empires Immortels (`woodelf.environment`, brouillard turquoise 0,29 / 0,76 / 0,75 : le voile
bleu-vert vu de loin dans Terry). WH1 avait un éclairage global (`woodelves`) et 7 sphères
(`environment_collection.xml` : Ashenhall, Nightglens, Witherhold, Winterheart, 3 x Bretonnie).

Formats : `environment_collection.xml` a la même version (2) dans les deux jeux, sphères en coordonnées du
monde (vérifié : Winterheart tombe sur le centre de notre neige). Les `.environment` ont changé (WH1 : version 5,
lumière v4 ; WH3 : version 11, lumière physique, soleil x 1000, nouveau brouillard, LUT, tone mapping), mais
WH3 garde `legacy_fog` et `legacy_hdr` au format du brouillard et du HDR de WH1.

Conversion, sur le modèle WH3 des Empires (`woodelf.environment` du kit), en ne touchant que des valeurs
d'attributs (mise en forme de CA conservée) :
- lumière : direction et couleur du soleil, diffusion sous-marine et réfraction, ombres des nuages, couleurs de
  l'eau : celles de WH1 ; intensité du soleil et du ciel x 1000 ; cube ambiant : couleurs de WH1 imposées,
  intensité au prorata (celle des Empires pour l'éclairage global de WH1, WH1 x 0,043 pour chaque zone) ;
- post-traitement : luminosité, contraste, saturation, teinte (360 -> 0), superposition de WH1, LUT neutre
  (`default`, comme WH1) ;
- brouillard : `legacy_fog` = brouillard de WH1 ; nouveau brouillard : couleur, distance dégagée et hauteur de
  WH1, densité des Empires ;
- `legacy_hdr` = HDR de WH1 ; vent (`weather`) de WH1. Ciel, nuages, SSAO, soleil affiché : ceux des Empires.

Usage :
    python eclairage_wh1.py            # contrôle : ce qui serait écrit
    python eclairage_wh1.py --apply    # écrit dans le projet (lighting\\) et dans working_data (lighting\\ et
                                       # environment_collection.xml, que la compilation suivante de BOB refait)
`terrain_wh1_vers_terry.py --apply` appelle `installer()` à chaque génération du projet et pose les 7 zones de
WH1 dans le calque `eclairage_wh1` (`entites_zones`) : c'est d'après elles que BOB écrit
`environment_collection.xml`.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
ATELIER = r"C:\TotalWar-CampaignMap"
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit)
WH1 = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns",
                   carte_config.CARTE_SOURCE)
MODELE = os.path.join(KIT, "working_data", "terrain", "campaigns", "wh3_main_combi_map_1", "lighting", "woodelf.environment")
PROJET = os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE)
COMPILE = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE)
GLOBAL_WH1 = "woodelves"                     # l'éclairage global de WH1 (environment_collection.xml)
FACTEUR_SOLEIL = 1000.0                      # WH1 sun_colour_scale 30 <-> Empires 30000
LUT = "default"
# Seconde conversion (23.09.2026, 00 h 30 ; capture de Charles en jeu : « gros problème, l'éclairage, la luminosité : dès
# qu'on zoome, ça change », voile cyan ; erreur 96). Transposer champ par champ l'éclairage de WH1 dans celui de WH3 ne
# marche pas : son brouillard bleu (0,56 / 0,60 / 1,0, pris à 15 % dans WH1 via fog_colour_blend, à 100 % dans WH3) collé
# au sol (3 unités, relatif au terrain : la caméra y entre en zoomant), ses gains de couleur (vert x 1,10, bleu x 1,14) sans
# la LUT de CA, son cube ambiant bleuté. Désormais : l'éclairage des elfes sylvains des Empires (`woodelf.environment`,
# le rendu naturel de CA dans WH3) avec **le soleil de WH1** (direction et couleur chaude), et la couleur de brouillard de
# la Bretonnie des Empires (le turquoise de `woodelf` faisait le voile bleu-vert vu de loin, 22.09.2026).
DE_WH1 = ("sun_direction_azimuth", "sun_direction_elevation")
BROUILLARD_CA = os.path.join(os.path.dirname(MODELE), "bretonnia.environment")
# Les 7 zones de WH1 (sphères) : WH3 les évalue à la position de la caméra, qui en sort en prenant de la hauteur (la
# luminosité change au zoom) ; le projet des Empires du kit n'en pose aucune (0 ECEnvironmentVolume). Désactivées en
# sphères (entités du projet, compilées par BOB).
ZONES_ACTIVES = False
# ... et remises en cylindres (23.09.2026, revue complète ; Charles : « la carte identique en tout point »). La collection
# que CA LIVRE pour les Empires (`terrain/campaigns/wh3_main_combi_map_1/environment_collection.xml` des packs, pas le
# projet du kit) a ses zones régionales en cylindres infinis (Bretonnie x 4, rayons 30-60, fondu de 10 à 15 unités ;
# Badlands, Cathay...) : une zone ne dépend plus de la hauteur de la caméra, seulement de sa position au sol, et le fondu
# est progressif. Même centre et mêmes rayons que les sphères de WH1. La collection est écrite par `build_pack.py`
# (format compilé de CA : <CYLINDER .../>), pas par BOB.
# RETIRÉES (23.09.2026, 02 h 53, essai de Charles : « de toutes les couleurs, ça fait très mal aux yeux » ; erreur 109) :
# en cylindres, les zones s'appliquent à toute hauteur de caméra, là où les sphères de WH1 ne jouaient que de près ; les
# trois zones de Bretonnie (rayons 90 à 110, un tiers de la carte) prenaient l'éclairage de CA pour la Bretonnie (soleil
# 60 000 contre 30 000, filtre de couleur `campaign_chaos_ogre_kingdoms`), les quatre clairières leurs écarts (orangé,
# désaturé, pâle, teinte froide) : la couleur et la lumière changeaient à chaque mouvement de caméra. Éclairage global
# seul (celui des elfes sylvains des Empires, soleil de WH1).
ZONES_CYLINDRES = False
# Chaque zone de WH1 : l'éclairage de CA le plus proche (elfes sylvains ; Bretonnie pour les trois zones bretonnes), avec
# le soleil de la zone et, pour les clairières, les ÉCARTS que WH1 donnait à la zone par rapport à son éclairage global
# (rapports : force du soleil et du ciel, saturation, luminosité, contraste, superposition ; teinte) : Nightglens, la
# clairière de minuit éternel, soleil x 0,33 et couleurs désaturées ; Ashenhall orangée ; Witherhold pâle ; Winterheart
# froide. Les valeurs absolues de WH1 ne se transposent pas (erreur 96) ; leurs rapports gardent le sens.
MODELES_ZONES = {"bretonnia": os.path.join(os.path.dirname(MODELE), "bretonnia.environment")}
ZONES_RELATIVES = ("ashenhall", "nightglens", "witherhold", "winterheart", "bretonnia")
# LES QUATRE CLAIRIÈRES RALLUMÉES (24.09.2026, chaîne 12 ; accord de Charles, 05 h 45 : « il faut vraiment que ça fasse
# bien, et exactement comme dans WH1 avec les screens » ; les trois zones de Bretonnie, cause de l'erreur 109, restent
# éteintes). Seules les zones de ZONES_RELATIVES sont écrites en cylindres (mêmes centres et rayons que les sphères de WH1 :
# plein effet jusqu'au rayon intérieur, fondu jusqu'au rayon extérieur), et chacune est BÂTIE SUR NOTRE GLOBAL (GRIMDARK,
# structure de CA, brouillard v2 compris) : le 23.09 elles partaient du modèle de CA non assombri, d'où un saut à chaque
# entrée de zone. Sur ce global : les rapports zone / global de WH1 (soleil, ciel, ambiant, post-traitement, voile, teinte,
# brouillard en hauteur), sauf pour le post-traitement des zones de CALAGE_ZONES, mesuré sur les images (brouillon
# `mesure_clairieres.py` : clairière d'hiver, Warhammer1_0020/25/95 s contre Warhammer3V2_0085/20 s ; nous / WH1 :
# R x 1,30, G x 1,24, B x 1,08, saturation x 0,70, teinte 30° trop verte ; d'où les facteurs inverses ci-dessous). Les
# facteurs par canal relèvent déjà à eux seuls la saturation par pixel (0,25 -> 0,33) et la teinte (166° -> 193°, WH1 196°) :
# reste une saturation x 1,10, et non x 1,40 qui compterait l'écart deux fois (0,43 ; brouillon `calage_hiver.py`).
# Une zone calée prend le soleil, le ciel et l'ambiance de notre global (la mesure porte sur l'image finale : y ajouter les
# rapports de WH1 compterait deux fois l'écart). Les forces de lumière des autres zones suivent WH1 telles quelles : WH1
# avait une exposition automatique (`hdr`, point blanc de 22 à 100) qui en rattrapait une partie, pas notre global
# (exposition fixe) ; Nightglens et Witherhold (soleil x 0,33) seront donc plus sombres que dans WH1 : à caler sur les
# images de Charles.
# ALLUMÉ le 24.09.2026 à 19 h 25 (accord de la construction, pack de ~20 h 35, présenté à Charles comme un essai) :
# `build_pack.py` écrit désormais la collection ET les fichiers d'éclairage de `produire()` et contrôle les cylindres par
# `cylindres_attendus` (correctif `brouillons-chaine12\correctif-build-pack-clairieres.md`). Pour éteindre : False, puis
# un simple pack.
ZONES_CLAIRIERES = True
# INTERRUPTEUR GÉNÉRAL DES ZONES (25.09.2026, 02 h 40 ; vidéo de Charles de 02 h 19 sur l'éclairage v3 : « comme une prise de
# LSD », Winterheart bleu nuit sur tout l'écran, Nightglens ciel et brume magenta et sol vert fluo, forêt cyan sous ciel rose,
# automne rouge-magenta). False : un seul éclairage global, aucune zone (clairières, Bretonnie, vampires) ; elles reviendront
# une à une, calées sur l'amplitude et les transitions des zones de CA aux Empires, montrées en image.
ZONES_ECLAIRAGE = True        # 25.09.2026, 02 h 50 : rallumées avec Winterheart SEULE, à la façon de CA (ZONES_REMISES)
if not ZONES_ECLAIRAGE:
    ZONES_CLAIRIERES = False
CALAGE_ZONES = {"winterheart": {"luminosite": (0.77, 0.81, 0.93), "saturation": 1.10}}
# (25.09.2026, 01 h, éclairage v3 ; audit par biome : la clairière d'hiver, même calée, restait trop claire et trop peu bleue
# face à la forêt (luminance hiver / forêt 1,66 contre 1,28 dans WH1, saturation 0,78 contre 1,03 ; teinte beige 49° contre
# 197° dans WH1). Plus sombre, plus bleue ; la saturation du global passe déjà de 1,05 à 1,22 (x 1,16) : x 1,30 voulu en tout,
# donc x 1,12 ici ; voile bleuté (superposition, facteurs sur celle du global).
CALAGE_ZONES = {"winterheart": {"luminosite": (0.62, 0.65, 0.78), "saturation": 1.16,     # x 1,30 au total (global 1,12)
                                "superposition": (0.90, 0.97, 1.08)}}
# LA BRETONNIE (25.09.2026, 01 h, éclairage v3 ; accord de Charles, risque de l'erreur 109 expliqué). WH1 éclairait ses
# trois zones de Bretonnie autrement qu'Athel Loren (soleil x 1,67, ambiance x 1,42, bleu plus saturé) ; nos plaines
# prenaient l'éclairage de la forêt, le biome le plus terne mesuré. Les trois zones reviennent en cylindres, BÂTIES SUR NOTRE
# GLOBAL comme les clairières (le 23.09, elles prenaient l'éclairage de CA pour la Bretonnie, soleil 60 000 et filtre des
# Royaumes Ogres : couleurs qui sautaient à chaque mouvement de caméra, erreur 109), et avec une PART seulement des écarts
# de WH1 (ATTENUATION_ZONES : rapports élevés à cette puissance, teinte et couleur du soleil interpolées) : entrer en
# Bretonnie doit se sentir, pas sauter. Pour éteindre : retirer "bretonnia" de ZONES_RELATIVES, puis un pack.
ATTENUATION_ZONES = {"bretonnia": 0.5,
                     # (01 h 15, vidéo de Charles, 56 s : autour de Tirsyth, TOUT rouge-orangé saturé, « l'automne au nord
                     # d'Athel Loren, trop orange ») : l'automne vient déjà des arbres d'automne de WH1 ; la lumière n'en
                     # garde qu'un tiers
                     "ashenhall": 0.33}
# LES TERRES DES VAMPIRES PLUS SOMBRES (25.09.2026, 01 h 15 ; Charles : « la Bretonnie peut rester lumineuse, mais les
# Comtes Vampires et Mousillon doivent être nettement plus grimdark »). WH1 n'avait pas de zone à Mousillon : deux zones À
# NOUS, en cylindres (fondu de 10 à 12 u), bâties sur notre global : Mousillon (province, centre de la ville) et Blackstone
# Post (capitale de Kemmler). Plus sombres, désaturées, voile froid, brume plus dense et plus sombre.
SOMBRE_VAMPIRES = {"luminosite": (0.78, 0.78, 0.82), "saturation": 0.68, "superposition": (0.93, 0.96, 1.03),
                   "brouillard_densite": 1.5, "brouillard": (0.12, 0.14, 0.14)}
ZONES_AJOUTEES = {"mousillon_sombre": {"cylindres": [(35.40, 233.33, 18.0, 30.0)], "calage": SOMBRE_VAMPIRES},
                  "blackstone_sombre": {"cylindres": [(199.06, 226.00, 10.0, 20.0)], "calage": SOMBRE_VAMPIRES}}
# ZONES REMISES UNE À UNE, « À LA MANIÈRE DE CA » (25.09.2026, 02 h 47, session du rendu ; accord de Charles via la
# construction, 02 h 45). Cause des couleurs « LSD » de la v3 (agent de mesure, `fx_hdr_to_screen` désassemblé) : la teinte de
# la Bretonnie (356,5, soit -3,5° modulo 360) interpolée de 0 à 356,5 dans l'anneau de fondu parcourait toutes les teintes ;
# le bleu nuit de Winterheart venait de son calage par canal. Les 18 zones de CA aux Empires : teinte 0, luminosité, contraste
# et saturation égaux au global, canaux égaux ; leur identité est portée par la LUT (16 sur 18 en changent), la couleur et la
# densité du brouillard, la force et la couleur du soleil, l'ambiance (jamais sous le global). Une zone de ZONES_FACON_CA est
# donc notre global tel quel, avec SEULEMENT : LUT de CA, couleur et densité du brouillard, soleil et ambiance en facteurs.
# Si elle ne se distingue pas assez en jeu, renforcer d'abord le brouillard (bornes de CA), jamais la couleur.
# Winterheart : LUT d'hiver de CA `campaign_chaos_kislev` (simulée sur la vidéo de 02 h 19 : luminance inchangée, saturation
# 0,44 -> 0,21, froid léger ; `campaign_chaos_norsca` virait au bleu), brouillard gris-bleu clair (norsca 0,36/0,41/0,49,
# kislev 0,41/0,50/0,63 ; ici en dessous), soleil x 0,85 (naggaroth_tundra x 0,83), ambiance x 1,2.
ZONES_FACON_CA = {"winterheart": {"lut": "campaign_chaos_kislev", "brouillard": (0.28, 0.32, 0.38),
                                  "brouillard_densite": 1.0, "soleil": 0.85, "ambiant": 1.2}}
# Les zones rallumées quand ZONES_ECLAIRAGE est vrai (None : toutes, comme en v3). Une zone de plus = montrée en image, puis
# essai en jeu avec captures à trois hauteurs (erreur 109).
ZONES_REMISES = ("winterheart",)
if ZONES_REMISES is not None:
    ZONES_RELATIVES = tuple(z for z in ZONES_RELATIVES if z in ZONES_REMISES)
    ZONES_AJOUTEES = {k: v for k, v in ZONES_AJOUTEES.items() if k in ZONES_REMISES}
# Brume des clairières : épaisseur au-dessus du sol de la zone (le y de la sphère de WH1) au prorata de WH1, jamais
# au-dessus de BRUME_HAUT_MAX (la caméra au plus près ne doit pas entrer dans la brume : erreur 96 ; notre global : 2 à 4,
# celui de CA).
BRUME_HAUT_MAX = 5.0
# La neige de campagne de WH3 est un post-traitement dont le matériau porte le masque de neige D'UNE carte : celui des
# Empires (`combi_campaign_snow`) lit `terrain/campaigns/wh3_main_combi_map_1/snow_mask.dds`, jamais le nôtre (la
# clairière d'hiver de WH1 restait sans neige, arbres, lisières et herbes givrés en gris sur un sol d'été). CA a un
# matériau par campagne (combi, chaos, prologue, vortex) : le nôtre, même contenu, notre masque.
NEIGE_CA = "materials/environment/snow/combi_campaign_snow.xml.material"
NEIGE_NOUS = "materials/environment/snow/wh_dlc05_wood_elves_campaign_snow.xml.material"
MASQUE_NEIGE_CA = "terrain/campaigns/wh3_main_combi_map_1/snow_mask.dds"
MASQUE_NEIGE_NOUS = f"terrain/campaigns/{CARTE}/snow_mask.dds"
SORTIE_MATERIAUX = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "eclairage-wh1")
# textures de neige de CA du matériau -> textures de neige de WH1 converties (voir `materiau_neige`)
# (04 h 40 : `snow2` de WH1, gris, la neige la plus présente de sa clairière d'hiver, au lieu de `snow0`, trop clair)
NEIGE_TEXTURES_WH1 = {
    "terrain/textures/campaign/default/snow/snow0_base_colour.dds": "terrain/textures/campaign/wh1/snow2_base_colour.dds",
    "terrain/textures/campaign/default/snow/snow0_material_map.dds": "terrain/textures/campaign/wh1/snow2_material_map.dds",
    "terrain/textures/campaign/default/snow/snow0_normal.dds": "terrain/textures/campaign/wh1/snow2_normal.dds",
}


def _attr(t, balise, nom, valeur):
    """Remplace la valeur de l'attribut `nom` dans la première balise `<balise ...>` de `t`."""
    m = re.search(rf"<{balise}\b[^>]*>", t)
    if not m:
        raise ValueError(f"balise {balise} absente du modèle")
    tag = m.group(0)
    neuf, n = re.subn(rf'(\b{nom}=")[^"]*(")', lambda k: k.group(1) + valeur + k.group(2), tag, count=1)
    if n != 1:
        raise ValueError(f"attribut {nom} absent de <{balise}>")
    return t[:m.start()] + neuf + t[m.end():]


def _dans(t, parent, balise, valeurs):
    """Remplace les attributs de `<balise>` à l'intérieur du bloc `<parent>...</parent>`."""
    m = re.search(rf"<{parent}\b.*?</{parent}>", t, re.S)
    bloc = m.group(0)
    for nom, v in valeurs.items():
        bloc = _attr(bloc, balise, nom, v)
    return t[:m.start()] + bloc + t[m.end():]


def f6(x):
    return f"{float(x):.6f}"


# Brouillard 2D (23.09.2026, 16 h 45, session du rendu ; capture de Charles en jeu, pack de 15 h 37 : « quand je dézoome et
# je zoome, il y a une espèce de carré très moche ») : notre modèle, `woodelf.environment` des Empires, est un éclairage de
# ZONE (Athel Loren) à brouillard volumique (`fog is_3d="1"`) ; l'éclairage GLOBAL de CA l'a en 2D, aux Empires
# (`default.environment`) comme au prologue (`prologue_khorne.environment`). Un brouillard volumique se calcule dans un
# volume autour de la caméra : sa distance dégagée (40 unités) y dessine une zone claire aux bords droits, qui change avec
# le zoom. Même distance dégagée qu'avant ; seul le calcul en volume est retiré (à confirmer en jeu par Charles).
BROUILLARD_3D = False
# LA STRUCTURE DE L'ÉCLAIRAGE GLOBAL DE CA (23.09.2026, 18 h 30, session du rendu ; pack de 17 h 42, Charles : « quand on
# dézoome, il y a un carré qui se met en place », « brouillard très épais au loin » ; le brouillard 2D n'y a rien changé).
# Notre modèle `woodelf` est un éclairage de ZONE ; comparé à l'éclairage GLOBAL des Empires (`default.environment`,
# brouillon `reglages_mer.py`) : plans de nuages en grille de 2 (CA 18) à densité 1 (CA 0,25), brouillard plus dense (2 et
# 2 contre 1,5 et 1,3), ancien brouillard (`legacy_fog`) ALLUMÉ (distance 0,65, hauteur jusqu'à 1 000, relatif au terrain)
# là où CA l'éteint. Les attributs de ces balises sont repris de l'éclairage global de CA ; l'aspect de WH1 (soleil,
# couleurs, `GRIMDARK`, couleur du brouillard) reste le nôtre.
STRUCTURE_GLOBALE_CA = True
GLOBAL_CA = os.path.join(os.path.dirname(MODELE), "default.environment")
BALISES_STRUCTURE = ("fog", "legacy_fog", "volume_fog_colour", "near_cloud_plane_mesh", "far_cloud_plane_mesh")


def structure_globale(t, ca):
    """Les attributs des balises BALISES_STRUCTURE de `t` remplacés par ceux de l'éclairage global de CA `ca` (les
    enfants, dont la couleur du brouillard, ne changent pas)."""
    for balise in BALISES_STRUCTURE:
        m = re.search(rf"<{balise}\b[^>]*>", ca)
        if not m:
            raise ValueError(f"balise {balise} absente de l'éclairage global de CA")
        for nom, v in re.findall(r'(\w+)="([^"]*)"', m.group(0)):
            if nom != "serialise_version":
                t = _attr(t, balise, nom, v)
    return t


def convertir(xml_wh1, modele, couleur_brouillard):
    """Éclairage de WH3 : le modèle de CA, avec le soleil de WH1, la couleur de brouillard `couleur_brouillard`
    ({r, g, b}) et notre matériau de neige (seconde conversion, 23.09.2026, erreur 96)."""
    w = ET.fromstring(xml_wh1)
    t = modele
    L = w.find("lighting")
    for nom in DE_WH1:
        t = _attr(t, "lighting", nom, f6(L.get(nom)))
    e = L.find("sun_colour")
    t = _dans(t, "lighting", "sun_colour", {c: f6(e.get(c)) for c in "rgb"})
    t = _dans(t, "fog", "colour", couleur_brouillard)
    if not BROUILLARD_3D:
        t = _attr(t, "fog", "is_3d", f6(0.0))
    if NEIGE_CA not in t:
        raise ValueError("modèle d'éclairage sans le matériau de neige des Empires")
    return t.replace(NEIGE_CA, NEIGE_NOUS)


# L'aspect « grimdark » de WH1 (23.09.2026, 03 h 50 ; Charles, captures WH1 / WH3 côte à côte : « un aspect plus grim dark
# dans Warhammer 1 que j'aimerais bien retrouver ») : WH1 est plus sombre, moins saturé, plus froid, sous une brume
# gris-bleu. Appliqué à l'éclairage global seulement, en facteurs sur les valeurs de CA (jamais les valeurs absolues de
# WH1, erreur 96). À régler d'après les captures en jeu.
# 04 h 40 : « un peu mieux, même s'il pourrait être un peu plus grimdark » (Charles, face à sa capture de WH1) : plus
# sombre et plus terne encore.
# 23.09.2026, 19 h 45 (session du rendu ; Charles, pack de 19 h 02 : « une ambiance un peu plus grimdark avec la
# luminosité... là, ça fait trop lumineux ») : exposition fixe partout (`auto_exposure="false"`) ; ce qui éclaire notre
# scène (brouillon `luminosite_globale.py`, contre l'éclairage global des Empires) : la lumière ambiante du modèle
# `woodelf` (`ambient_fudge_factor` 3 contre 1, couleurs du cube d'ambiance deux fois plus claires) et la lumière du ciel
# (21 600 contre 0) ; et depuis la chaîne 3, l'ancien brouillard (voile sombre au loin) est éteint comme chez CA. On
# assombrit par l'ambiance (des ombres plus profondes), le ciel, puis la luminosité, la saturation et la teinte du
# post-traitement ; brouillard plus sombre.
# ÉCLAIRAGE V2 (24.09.2026, 03 h 45, session du rendu ; vidéos WH1 / WH3 de Charles, cinq plans appariés mesurés par le
# brouillon `videos\mesure_couleurs.py`) : notre WH3 était deux fois moins saturé que WH1 (0,16-0,26 contre 0,32-0,47),
# 15 à 40 % plus clair, moins contrasté, 15 à 25° plus bleu et noyé dans une brume gris-bleu (17 % de pixels « brume » en
# forêt contre 1 %). Ancien réglage : saturation 0,66, luminosité 0,80, contraste 1,12, voile (0,90 ; 0,93 ; 0,98),
# brouillard (0,30 ; 0,35 ; 0,41), densité 1,5, brume en hauteur 1,3, dégagé 40 u, fondu 60 u.
# ÉCLAIRAGE V3 (25.09.2026, 01 h, session du rendu ; audit par biome `scratchpad\eclairage_biomes\`, accord de Charles
# « vas-y ») : la forêt d'Athel Loren restait terne et plate face à WH1 (luminance égale, saturation -20 %, écart ombres /
# lumières -25 %, dérive cyan au loin), les plaines de Bretonnie plus ternes encore (-22 % sur la forêt). Saturation 1,05 ->
# 1,22, contraste 1,20 -> 1,28, brouillard gris sarcelle (0,20 ; 0,26 ; 0,26) -> gris-bleu sombre (0,17 ; 0,20 ; 0,24),
# proche de la couleur du global de CA assombrie. Luminosité, soleil, ciel, ambiance inchangés (pas plus sombre ni plus
# clair). Les clairières, bâties sur ce global, en héritent.
# (01 h 15, vidéo de Charles de 00 h 58 : l'objectif est GRIMDARK ; touffes vert-jaune vif et automne rouge-orangé déjà
# trop saturés à 1,05) : saturation 1,12 au lieu de 1,22, le contraste seul relève la forêt.
GRIMDARK = {"soleil": 0.72, "ciel": 0.62, "saturation": 1.12, "luminosite": 0.72, "contraste": 1.28,
            "superposition": (0.96, 1.00, 0.97), "brouillard": (0.17, 0.20, 0.24), "ambiant": 0.65}
BROUILLARD_V2 = {"density": "0.900000", "height_density": "0.800000", "clear_distance": "60.000000",
                 "clear_distance_fade_out": "100.000000"}


def assombrir(t, reglage=GRIMDARK):
    """L'éclairage global en plus sombre, désaturé, froid et brumeux (facteurs sur les valeurs de CA)."""
    for nom, cle in (("sun_colour_scale", "soleil"), ("sky_colour_scale", "ciel")):
        t = _attr(t, "lighting", nom, f6(_valeur(t, "lighting", nom) * reglage[cle]))
    if "ambiant" in reglage:
        t = _attr(t, "lighting", "ambient_fudge_factor",
                  f6(_valeur(t, "lighting", "ambient_fudge_factor") * reglage["ambiant"]))
    for nom, cle in (("saturation", "saturation"), ("brightness", "luminosite"), ("contrast", "contraste")):
        for c in "rgb":
            t = _attr(t, "post_processing", f"{nom}_{c}", f6(_valeur(t, "post_processing", f"{nom}_{c}") * reglage[cle]))
    m = re.search(r"<post_processing\b.*?<overlay\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
    t = _dans(t, "post_processing", "overlay", {c: f6(float(v) * f) for c, v, f in zip("rgb", m.groups(),
                                                                                     reglage["superposition"])})
    return _dans(t, "fog", "colour", {c: f6(v) for c, v in zip("rgb", reglage["brouillard"])})


def _valeur(t, balise, nom):
    m = re.search(rf"<{balise}\b[^>]*\b{nom}=\"([^\"]+)\"", t)
    if not m:
        raise ValueError(f"attribut {nom} absent de <{balise}>")
    return float(m.group(1))


def convertir_zone(xml_zone, xml_global, modele, couleur_brouillard):
    """Éclairage d'une clairière de WH1 : `convertir` (modèle de CA, soleil de la zone), puis les rapports zone / global
    de WH1 appliqués aux valeurs de CA (voir `ZONES_RELATIVES`)."""
    t = convertir(xml_zone, modele, couleur_brouillard)
    z, g = ET.fromstring(xml_zone), ET.fromstring(xml_global)
    Lz, Lg, Pz, Pg = z.find("lighting"), g.find("lighting"), z.find("post_processing"), g.find("post_processing")

    def rapport(a, b, nom):
        vb = float(b.get(nom))
        return float(a.get(nom)) / vb if vb else 1.0
    for nom in ("sun_colour_scale", "sky_colour_scale"):
        t = _attr(t, "lighting", nom, f6(_valeur(t, "lighting", nom) * rapport(Lz, Lg, nom)))
    for nom in ("saturation_r", "saturation_g", "saturation_b", "brightness_r", "brightness_g", "brightness_b",
                "contrast_r", "contrast_g", "contrast_b"):
        t = _attr(t, "post_processing", nom, f6(_valeur(t, "post_processing", nom) * rapport(Pz, Pg, nom)))
    oz, og = Pz.find("overlay"), Pg.find("overlay")
    m = re.search(r"<post_processing\b.*?<overlay\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
    t = _dans(t, "post_processing", "overlay", {c: f6(float(v) * float(oz.get(c)) / float(og.get(c)))
                                                 for c, v in zip("rgb", m.groups())})
    teinte = (float(Pz.get("hue")) - float(Pg.get("hue"))) % 360.0
    t = _attr(t, "post_processing", "hue", f6(_valeur(t, "post_processing", "hue") + teinte))
    return t


def zone_sur_global(nom, xml_zone, xml_global_wh1, global_nous, sol):
    """Éclairage d'une clairière (`ZONES_CLAIRIERES`) : notre éclairage global `global_nous` (texte final : GRIMDARK,
    structure de CA, brouillard v2), avec les écarts de la zone de WH1 à son global, ou le calage mesuré sur les images
    (`CALAGE_ZONES`) ; brume : épaisseur au-dessus de `sol` (y de la sphère de WH1) au prorata de WH1. Direction du soleil,
    couleur et distances du brouillard, ciel, nuages : ceux du global (les ombres ne tournent pas en entrant dans la zone ;
    WH1 : 327,1 à 327,6° d'azimut partout)."""
    t = global_nous
    z, g = ET.fromstring(xml_zone), ET.fromstring(xml_global_wh1)
    Lz, Lg, Pz, Pg, Fz, Fg = (e.find(b) for b in ("lighting", "post_processing", "fog") for e in (z, g))

    a_ = ATTENUATION_ZONES.get(nom, 1.0)               # (v3) part des écarts de WH1 (Bretonnie : la moitié)

    def rapport(a, b, n):
        vb = float(b.get(n))
        return (float(a.get(n)) / vb) ** a_ if vb else 1.0
    calage = CALAGE_ZONES.get(nom)
    if calage is None:
        m_sol = re.search(r"<lighting\b.*?<sun_colour\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
        t = _dans(t, "lighting", "sun_colour", {c: f6(float(v) + (float(Lz.find("sun_colour").get(c)) - float(v)) * a_)
                                                for c, v in zip("rgb", m_sol.groups())})
        for n_wh1, n_nous in (("sun_colour_scale", "sun_colour_scale"), ("sky_colour_scale", "sky_colour_scale"),
                              ("ambient_cube_hdr_scaler", "ambient_fudge_factor")):
            t = _attr(t, "lighting", n_nous, f6(_valeur(t, "lighting", n_nous) * rapport(Lz, Lg, n_wh1)))
        for n in ("saturation_r", "saturation_g", "saturation_b", "brightness_r", "brightness_g", "brightness_b",
                  "contrast_r", "contrast_g", "contrast_b"):
            t = _attr(t, "post_processing", n, f6(_valeur(t, "post_processing", n) * rapport(Pz, Pg, n)))
        oz, og = Pz.find("overlay"), Pg.find("overlay")
        m = re.search(r"<post_processing\b.*?<overlay\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
        t = _dans(t, "post_processing", "overlay", {c: f6(float(v) * (float(oz.get(c)) / float(og.get(c))) ** a_)
                                                     for c, v in zip("rgb", m.groups())})
        teinte = ((float(Pz.get("hue")) - float(Pg.get("hue")) + 180.0) % 360.0 - 180.0) * a_
        t = _attr(t, "post_processing", "hue", f6((_valeur(t, "post_processing", "hue") + teinte) % 360.0))
    else:
        for c, f in zip("rgb", calage["luminosite"]):
            t = _attr(t, "post_processing", f"brightness_{c}", f6(_valeur(t, "post_processing", f"brightness_{c}") * f))
        for c in "rgb":
            t = _attr(t, "post_processing", f"saturation_{c}",
                      f6(_valeur(t, "post_processing", f"saturation_{c}") * calage["saturation"]))
        if "superposition" in calage:                  # (v3) voile de couleur de la zone
            m = re.search(r"<post_processing\b.*?<overlay\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
            t = _dans(t, "post_processing", "overlay", {c: f6(float(v) * f) for c, v, f in
                                                         zip("rgb", m.groups(), calage["superposition"])})
    haut, bas = _valeur(t, "fog", "height_top"), _valeur(t, "fog", "height_bottom")
    neuf = sol + max(0.0, haut - sol) * rapport(Fz, Fg, "fog_height_top")
    t = _attr(t, "fog", "height_top", f6(min(max(neuf, bas + 0.5), BRUME_HAUT_MAX)))
    return _attr(t, "fog", "height_density",
                 f6(_valeur(t, "fog", "height_density") * rapport(Fz, Fg, "fog_height_strength")))


def zone_calee(global_nous, calage):
    """Éclairage d'une zone À NOUS (`ZONES_AJOUTEES`) : notre global, post-traitement calé (luminosité par canal,
    saturation, voile), brume plus dense et d'une autre couleur."""
    t = global_nous
    for c, f in zip("rgb", calage["luminosite"]):
        t = _attr(t, "post_processing", f"brightness_{c}", f6(_valeur(t, "post_processing", f"brightness_{c}") * f))
    for c in "rgb":
        t = _attr(t, "post_processing", f"saturation_{c}",
                  f6(_valeur(t, "post_processing", f"saturation_{c}") * calage["saturation"]))
    m = re.search(r"<post_processing\b.*?<overlay\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
    t = _dans(t, "post_processing", "overlay", {c: f6(float(v) * f) for c, v, f in
                                                 zip("rgb", m.groups(), calage["superposition"])})
    t = _attr(t, "fog", "density", f6(_valeur(t, "fog", "density") * calage["brouillard_densite"]))
    return _dans(t, "fog", "colour", {c: f6(v) for c, v in zip("rgb", calage["brouillard"])})


def zone_facon_ca(global_nous, reglage):
    """Éclairage d'une zone de `ZONES_FACON_CA` : notre global, post-traitement inchangé (teinte 0), sauf la LUT de CA ;
    brouillard (couleur, densité), force du soleil et ambiance en facteurs sur le global."""
    t = global_nous
    for n in ("lut_texture_file", "lut_texture_file_2"):
        t = _attr(t, "post_processing", n, reglage["lut"])
    t = _attr(t, "lighting", "sun_colour_scale", f6(_valeur(t, "lighting", "sun_colour_scale") * reglage["soleil"]))
    t = _attr(t, "lighting", "ambient_fudge_factor",
              f6(_valeur(t, "lighting", "ambient_fudge_factor") * reglage["ambiant"]))
    t = _attr(t, "fog", "density", f6(_valeur(t, "fog", "density") * reglage["brouillard_densite"]))
    return _dans(t, "fog", "colour", {c: f6(v) for c, v in zip("rgb", reglage["brouillard"])})


def cylindres_attendus():
    """Les fichiers d'éclairage (noms de base) que la collection doit citer en cylindres, dans l'ordre de WH1 : les quatre
    clairières (`ZONES_CLAIRIERES`), les 7 zones de WH1 (`ZONES_CYLINDRES`) ou aucun. Pour le contrôle de `build_pack.py`.
    (v3) Puis les zones à nous (`ZONES_AJOUTEES`)."""
    if ZONES_CLAIRIERES:
        return [os.path.basename(s[0]) for s in _spheres_wh1()
                if os.path.basename(s[0])[:-len(".environment")] in ZONES_RELATIVES] + \
            [f"{nom}.environment" for nom, d in ZONES_AJOUTEES.items() for _ in d["cylindres"]]
    if ZONES_CYLINDRES:
        return [os.path.basename(s[0]) for s in _spheres_wh1()]
    return []


def collection_cylindres(coll_wh1, garder=None):
    """La collection de WH1 (sphères) au format compilé de CA, ses zones en cylindres (même centre, mêmes rayons) ; avec
    `garder`, seulement les zones dont le fichier d'éclairage (sans `.environment`) y figure."""
    racine = ET.fromstring(coll_wh1)
    retenues = [s for s in racine.find("ENVIRONMENT_SPHERES")
                if garder is None or os.path.basename(s.get("lighting"))[:-len(".environment")] in garder]
    cyl = "".join(
        f"\t\t<CYLINDER serialise_version='1' lighting='{s.get('lighting')}' x='{float(s.get('x')):.6f}' "
        f"y='{float(s.get('y')):.6f}' z='{float(s.get('z')):.6f}' inner_radius='{float(s.get('inner_radius')):.6f}' "
        f"outer_radius='{float(s.get('outer_radius')):.6f}'/>\n" for s in retenues)
    return (f"<ENVIRONMENT_COLLECTION serialise_version='2' global_lighting='{racine.get('global_lighting')}'>\n"
            f"\t<ENVIRONMENT_SPHERES/>\n\t<ENVIRONMENT_CYLINDERS>\n{cyl}\t</ENVIRONMENT_CYLINDERS>\n"
            f"</ENVIRONMENT_COLLECTION>\n")


def convertir_champ_par_champ(xml_wh1, modele, facteur_ambiant):
    """Première conversion (22.09.2026), gardée pour mémoire : voile cyan et luminosité qui change au zoom (erreur 96)."""
    w = ET.fromstring(xml_wh1)
    t = modele
    L = w.find("lighting")
    for nom in ("sea_bed_light_scatter_red", "sea_bed_light_scatter_green", "sea_bed_light_scatter_blue",
                "refraction_light_scatter", "sun_direction_azimuth", "sun_direction_elevation",
                "cloud_shadow_scroll_speed", "cloud_shadow_uv_scale", "cloud_shadow_lerp"):
        t = _attr(t, "lighting", nom, f6(L.get(nom)))
    t = _attr(t, "lighting", "sun_colour_scale", f6(float(L.get("sun_colour_scale")) * FACTEUR_SOLEIL))
    t = _attr(t, "lighting", "sky_colour_scale", f6(float(L.get("sky_colour_scale")) * 30000.0))
    t = _attr(t, "lighting", "use_custom_ambient_cube_colours", L.get("use_custom_ambient_cube_colours"))
    amb = f6(float(L.get("ambient_cube_hdr_scaler")) * facteur_ambiant)
    t = _attr(t, "lighting", "ambient_cube_hdr_scaler", amb)
    t = _attr(t, "lighting", "ambient_scale", amb)
    for sous in ("sun_colour", "deep_water_colour", "shallow_water_colour", "ambient_cube_left", "ambient_cube_right",
                 "ambient_cube_top", "ambient_cube_bottom", "ambient_cube_front", "ambient_cube_back"):
        e = L.find(sous)
        t = _dans(t, "lighting", sous, {c: f6(e.get(c)) for c in "rgb"})
    P = w.find("post_processing")
    t = _attr(t, "post_processing", "lut_texture_file", LUT)
    t = _attr(t, "post_processing", "lut_texture_file_2", LUT)
    for nom in ("brightness_r", "brightness_g", "brightness_b", "contrast_r", "contrast_g", "contrast_b",
                "saturation_r", "saturation_g", "saturation_b", "sharpening_strength"):
        t = _attr(t, "post_processing", nom, f6(P.get(nom)))
    teinte = float(P.get("hue"))
    t = _attr(t, "post_processing", "hue", f6(0.0 if abs(teinte - 360.0) < 1e-3 else teinte))
    t = _dans(t, "post_processing", "overlay", {c: f6(P.find("overlay").get(c)) for c in "rgb"})
    F = w.find("fog")
    for nom in ("fog_distance_start", "fog_distance_strength", "fog_distance_scale", "fog_height_top",
                "fog_height_strength", "fog_clear_distance", "fog_colour_blend", "fog_precipitation_intensity",
                "fog_precipitation_distance_modifier"):
        t = _attr(t, "legacy_fog", nom, f6(F.get(nom)))
    t = _attr(t, "legacy_fog", "terrain_relative_height_fog", F.get("terrain_relative_height_fog"))
    vf = F.find("volume_fog_colour")
    t = _dans(t, "legacy_fog", "volume_fog_colour", {c: f6(vf.get(c)) for c in "rgba"})
    t = _dans(t, "fog", "colour", {c: f6(min(1.0, float(vf.get(c)))) for c in "rgb"})
    t = _attr(t, "fog", "clear_distance", f6(F.get("fog_clear_distance")))
    t = _attr(t, "fog", "height_top", f6(F.get("fog_height_top")))
    t = _attr(t, "fog", "terrain_relative_height_fog", F.get("terrain_relative_height_fog"))
    Hd = w.find("hdr")
    for nom in ("absolute_black_point", "max_black_point", "min_white_point", "absolute_white_point",
                "exposure_sensitivity", "auto_exposure_speed_down", "auto_exposure_speed_up", "low_tones_bias_red",
                "high_tones_bias_red", "low_tones_bias_green", "high_tones_bias_green", "low_tones_bias_blue",
                "high_tones_bias_blue", "bloom_point_above_white_point", "whiteout_start", "whiteout_end",
                "bloom_strength"):
        t = _attr(t, "legacy_hdr", nom, f6(Hd.get(nom)))
    t = _attr(t, "legacy_hdr", "lock_rgb_relative_tones", Hd.get("lock_rgb_relative_tones"))
    W = w.find("weather")
    t = _attr(t, "weather", "wind_dir_random", W.get("wind_dir_random"))
    t = _attr(t, "weather", "wind_dir_degrees", f6(W.get("wind_dir_degrees")))
    t = _attr(t, "weather", "definition_name", W.get("definition_name"))
    t = _attr(t, "weather", "snowing_intensity", f6(W.get("snowing_intensity")))
    t = _attr(t, "weather", "creep_intensity", f6(W.get("creep_intensity")))
    return t


def lire(chemin):
    return open(chemin, encoding="utf-8").read()


def produire():
    """{nom de fichier : contenu} : les .environment convertis, default.environment, environment_collection.xml."""
    modele = lire(MODELE)
    wh1_dir = os.path.join(WH1, "lighting")
    brouillard = re.search(r"<fog\b.*?<colour\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", lire(BROUILLARD_CA), re.S)
    couleur = dict(zip("rgb", brouillard.groups()))
    facteur = 1.0
    out = {}
    glob_wh1 = lire(os.path.join(wh1_dir, GLOBAL_WH1 + ".environment"))
    for n in sorted(os.listdir(wh1_dir)):
        if n.endswith(".environment") and not n.endswith("_test.environment"):
            nom = n[:-len(".environment")]
            xml = lire(os.path.join(wh1_dir, n))
            if ZONES_CYLINDRES and nom in ZONES_RELATIVES:
                out["lighting/" + n] = convertir_zone(xml, glob_wh1, modele, couleur)
            elif ZONES_CYLINDRES and nom in MODELES_ZONES:
                out["lighting/" + n] = convertir(xml, lire(MODELES_ZONES[nom]), couleur)
            else:
                out["lighting/" + n] = convertir(xml, modele, couleur)
    out[f"lighting/{GLOBAL_WH1}.environment"] = assombrir(out[f"lighting/{GLOBAL_WH1}.environment"])
    if STRUCTURE_GLOBALE_CA:
        out[f"lighting/{GLOBAL_WH1}.environment"] = structure_globale(out[f"lighting/{GLOBAL_WH1}.environment"],
                                                                      lire(GLOBAL_CA))
    for nom, v in BROUILLARD_V2.items():               # (24.09.2026) brouillard moins dense, plus loin (voir GRIMDARK)
        out[f"lighting/{GLOBAL_WH1}.environment"] = _attr(out[f"lighting/{GLOBAL_WH1}.environment"], "fog", nom, v)
    out["lighting/default.environment"] = out[f"lighting/{GLOBAL_WH1}.environment"]
    if ZONES_CLAIRIERES:                               # (24.09.2026) les quatre clairières, sur notre global
        sols = {os.path.basename(s[0])[:-len(".environment")]: s[2] for s in _spheres_wh1()}
        for nom in ZONES_RELATIVES:
            if nom in ZONES_FACON_CA:                  # (25.09.2026) à la manière de CA
                out[f"lighting/{nom}.environment"] = zone_facon_ca(out[f"lighting/{GLOBAL_WH1}.environment"],
                                                                   ZONES_FACON_CA[nom])
                continue
            out[f"lighting/{nom}.environment"] = zone_sur_global(
                nom, lire(os.path.join(wh1_dir, nom + ".environment")), glob_wh1,
                out[f"lighting/{GLOBAL_WH1}.environment"], sols[nom])
    coll = lire(os.path.join(WH1, "environment_collection.xml"))
    for m in re.findall(r"lighting/([a-z0-9_]+)\.environment", coll):
        if f"lighting/{m}.environment" not in out:
            raise SystemExit(f"environment_collection.xml cite {m}.environment, absent")
    if ZONES_CLAIRIERES:
        coll = collection_cylindres(coll, garder=ZONES_RELATIVES)
        # (v3) les zones à nous, en cylindres après celles de WH1 (même format)
        ajout = "".join(
            f"\t\t<CYLINDER serialise_version='1' lighting='terrain/campaigns/{CARTE}/lighting/{nom}.environment' "
            f"x='{x:.6f}' y='0.000000' z='{z:.6f}' inner_radius='{ri:.6f}' outer_radius='{ro:.6f}'/>\n"
            for nom, d in ZONES_AJOUTEES.items() for x, z, ri, ro in d["cylindres"])
        coll = coll.replace("\t</ENVIRONMENT_CYLINDERS>", ajout + "\t</ENVIRONMENT_CYLINDERS>")
        for nom, d in ZONES_AJOUTEES.items():
            out[f"lighting/{nom}.environment"] = zone_calee(out[f"lighting/{GLOBAL_WH1}.environment"], d["calage"])
    elif ZONES_CYLINDRES:
        coll = collection_cylindres(coll)
    elif not ZONES_ACTIVES:
        coll = re.sub(r"<ENVIRONMENT_SPHERES>.*?</ENVIRONMENT_SPHERES>", "<ENVIRONMENT_SPHERES/>", coll, flags=re.S)
    out["environment_collection.xml"] = coll
    return out, facteur


def materiau_neige():
    """Notre matériau de neige de campagne : celui des Empires, avec notre masque (voir `NEIGE_NOUS`)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from contenu_pack import SourcePacks
    b = SourcePacks(os.path.join(os.path.dirname(KIT), "data")).lire(NEIGE_CA)
    if b is None:
        raise SystemExit(f"{NEIGE_CA} absent des packs de WH3")
    t = b.decode("utf-8")
    # (24.09.2026, 21 h 08, chaîne 12) en 9.0, le matériau de CA ne cite plus aucun masque de carte (le jeu lie lui-même le
    # snow_mask.dds de la campagne) : rien à remplacer ; en 8.1, il citait celui des Empires une fois
    n_masque = t.count(MASQUE_NEIGE_CA)
    if n_masque > 1 or re.search(r"terrain/campaigns/[^\"<]*snow_mask\.dds", t.replace(MASQUE_NEIGE_CA, "")):
        raise SystemExit(f"{NEIGE_CA} : masque de neige inattendu (cité {n_masque} fois)")
    t = t.replace(MASQUE_NEIGE_CA, MASQUE_NEIGE_NOUS).replace("combi_campaign_snow.xml",
                                                              os.path.basename(NEIGE_NOUS)[:-len(".material")])
    # La neige de WH1 (23.09.2026, 04 h 10 ; Charles : « vraiment la texture de Warhammer 1 pour la glace et la neige ») :
    # le matériau est à nous seuls, ses textures peuvent donc être celles de WH1 (converties au format de CA par
    # `textures_sol_wh1.py --convertir`, embarquées sous `terrain/textures/campaign/wh1/`) sans toucher à la neige des
    # autres campagnes. Neige principale : `snow0` de WH1 ; les trois normales de détail : `snow1` à `snow3`.
    for ca, wh1 in NEIGE_TEXTURES_WH1.items():
        if ca not in t:
            raise SystemExit(f"{NEIGE_CA} : texture {ca} absente du matériau des Empires")
        t = t.replace(ca, wh1)
    return t


def zones():
    """(éclairage global, [(fichier d'éclairage, x, y, z, rayon intérieur, rayon extérieur)]) : les sphères de
    `environment_collection.xml` de WH1 (aucun cylindre chez lui).

    BOB **écrit lui-même** `environment_collection.xml` (sortie « <working>/terrain/campaigns/<carte>/
    environment_collection.xml » de sa configuration) d'après les entités du projet qui portent un
    `ECEnvironmentVolume` (propriété « Lighting File » -> attribut `lighting_file`) et une forme
    (`ECDoubleSphere` -> SPHERE ; `ECInfiniteDoubleCylinder` -> CYLINDER), et efface toute autre version :
    22.09.2026, 18 h, la collection posée par `installer()` avait disparu après BOB. Relevé dans
    `bob_terrain.modder.x64.dll` et `qttoolutility.modder.x64.dll` (chaînes `ENVIRONMENT_SPHERES`,
    `?lighting_file@ECEnvironmentVolume`, « Lighting File »)."""
    racine = ET.fromstring(lire(os.path.join(WH1, "environment_collection.xml")))
    return racine.get("global_lighting"), (_spheres_wh1() if ZONES_ACTIVES else [])


def _spheres_wh1():
    """[(fichier d'éclairage, x, y, z, rayon intérieur, rayon extérieur)] : les sphères de la collection de WH1."""
    racine = ET.fromstring(lire(os.path.join(WH1, "environment_collection.xml")))
    if racine.find("ENVIRONMENT_CYLINDERS") is not None and len(racine.find("ENVIRONMENT_CYLINDERS")):
        raise SystemExit("environment_collection.xml de WH1 : des cylindres, non prévus")
    return [(s.get("lighting"), *(float(s.get(k)) for k in ("x", "y", "z", "inner_radius", "outer_radius")))
            for s in racine.find("ENVIRONMENT_SPHERES")]


def entites_zones(ident):
    """Entités de calque Terry des zones de WH1 (`ident(texte)` -> identifiant d'entité du générateur)."""
    _, sph = zones()
    return "".join(
        f'\t\t<entity id="{ident(f"eclairage:{k}:{os.path.basename(f)}")}">\n'
        f'\t\t\t<ECEnvironmentVolume lighting_file="{f}"/>\n'
        f'\t\t\t<ECTransform position="{x:.6f} {y:.6f} {z:.6f}" rotation="0. 0. 0." scale="1. 1. 1." pivot="0 0 0"/>\n'
        f'\t\t\t<ECDoubleSphere inner_radius="{ri:.6f}" outer_radius="{ro:.6f}"/>\n'
        "\t\t</entity>\n" for k, (f, x, y, z, ri, ro) in enumerate(sph))


def installer(avec_collection=False, verbeux=True):
    """Écrit l'éclairage dans le projet (lighting\\) et dans working_data (lighting\\ ; environment_collection.xml
    si `avec_collection` : inutile avant BOB, qui l'écrit d'après les zones du projet, voir `zones`).
    Base : les éclairages des Empires (le jeu peut en chercher par leur nom, ceux de pré-bataille par exemple),
    puis ceux de WH1 par-dessus (`default.environment` compris)."""
    out, facteur = produire()
    base = os.path.join(os.path.dirname(MODELE))
    for racine in (PROJET, COMPILE):
        dossier = os.path.join(racine, "lighting")
        if os.path.isdir(dossier):
            for n in os.listdir(dossier):
                os.remove(os.path.join(dossier, n))
        os.makedirs(dossier, exist_ok=True)
        for n in os.listdir(base):
            with open(os.path.join(base, n), "rb") as fs, open(os.path.join(dossier, n), "wb") as fd:
                fd.write(fs.read())
        for chemin, texte in out.items():
            if chemin == "environment_collection.xml" and (racine == PROJET or not avec_collection):
                continue
            with open(os.path.join(racine, *chemin.split("/")), "w", encoding="utf-8", newline="\r\n") as f:
                f.write(texte)
    # notre matériau de neige : dans le dossier embarqué par build_pack.py, et dans working_data pour Terry
    neige = materiau_neige()
    for racine in (SORTIE_MATERIAUX, os.path.join(KIT, "working_data")):
        chemin = os.path.join(racine, *NEIGE_NOUS.split("/"))
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8", newline="\n") as f:
            f.write(neige)
    if verbeux:
        print(f"  éclairage : {len([c for c in out if c.startswith('lighting/')])} fichiers (base des Empires, soleil de "
              f"WH1), zones {'actives' if ZONES_ACTIVES else 'désactivées'}"
              f"{' ; clairières en cylindres : ' + ', '.join(cylindres_attendus()) if ZONES_CLAIRIERES else ''} ; "
              f"neige : {NEIGE_NOUS}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out, facteur = produire()
    for c, t in out.items():
        m = re.search(r'sun_colour_scale="([^"]+)".*?ambient_cube_hdr_scaler="([^"]+)"', t, re.S)
        fog = re.search(r"<fog\b.*?<colour\s+r=\"([^\"]+)\"\s+g=\"([^\"]+)\"\s+b=\"([^\"]+)\"", t, re.S)
        print(f"  {c:40} " + (f"soleil {m.group(1)} ambiant {m.group(2)} brouillard {fog.groups()}" if m and fog else f"{len(t)} octets"))
    glob, sph = zones()
    print(f"  zones de WH1 : {len(sph)} sphères ; éclairage global {glob}")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply")
        return 0
    installer(avec_collection=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
