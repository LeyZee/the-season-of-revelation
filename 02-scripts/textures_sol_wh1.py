#!/usr/bin/env python3
"""
textures_sol_wh1.py - les 19 textures de sol de Warhammer 1, en jeu, à la place de nos équivalents de WH3.

Pourquoi (22.09.2026, Charles : « identique à la map dans Warhammer 1 » ; journal
`05-journal\\2026-09-22-phase-4\\eclairage-textures-wh1.md`) : `terrain_wh1_vers_terry.py` traduit les 19 textures
de sol de WH1 vers des textures de WH3 (table TEXTURES). WH3 n'a pas de registre de groupes de textures que
nous puissions étendre (la liste compilée de BOB, 144 groupes, ne vient ni de `_settings.bin`, 138 groupes, ni
d'un parcours des fichiers) ; mais chaque carte a sa liste compilée, `global_map\\texture_arrays.xml`, qui donne
le chemin des textures de chaque case des tableaux. Terry ne la lit pas (essai du 22.09.2026, 17 h 40) : le
jeu, si.

Donc, après BOB :
- 19 groupes de la liste compilée que notre carte n'emploie pas, **de même nature** que la texture de WH1
  (herbe -> herbe, sable -> sable...), au cas où le jeu tirerait un type de sol du nom du groupe, reçoivent les
  chemins des textures de WH1 converties (`DONNEURS`) ;
- `global_blend.dds` compilé est réécrit depuis celui de WH1 (rangé du sud au nord, retourné), chaque texture de
  WH1 renvoyant à son groupe donneur ; les hex de montagne gardent l'éboulis que BOB y a mis (les maillages de
  montagne de WH1, avec leur roche, ne sont pas encore reconstitués).
Terry continue de montrer notre traduction WH3 ; le jeu montre les textures de WH1.

Conversion au format exact des 144 textures de CA :
- `_base_colour` : le `_diffuse` de WH1 (DXT5 2048²) ramené à 1024², BC7 sRGB, 11 niveaux (`bc7.py`) ;
- `_material_map` : R = 0 (non métallique), G = 255 - brillance du `_spec_gloss` de WH1, B = 0, A = 255 ; BC7,
  1024², 11 niveaux ;
- `_normal` : la normal map de WH1 (DXT5, même disposition des canaux que chez CA), niveaux 1024 à 2 (10
  niveaux, comme CA), sans réencodage, sous l'en-tête d'une normale de CA.
Fichiers sous `terrain/textures/campaign/wh1/` (chemin absent de WH3), dans le projet
(`04-projets\\saison-des-revelations\\textures-sol-wh1\\`, embarqué par `build_pack.py`) et dans `working_data`.

Usage :
    python textures_sol_wh1.py --convertir      # fabrique les 57 textures (une fois ; ~3 min)
    python textures_sol_wh1.py --apply          # après BOB : réécrit texture_arrays.xml et global_blend.dds
    python textures_sol_wh1.py --apply --refaire  # déjà appliqué : refait depuis la sortie de BOB sauvegardée
    python textures_sol_wh1.py                  # contrôle à blanc
Les textures que WH1 posait par ses tuiles (fond de mer et plages en mud_a0, lits de rivière en sand_a0) passent par
`textures_tuiles_wh1.corriger` avant la réécriture.
"""

import argparse
import glob
import io
import os
import re
import shutil
import struct
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc7                                                           # noqa: E402
from terrain_wh1_vers_terry import MONTAGNE, TEXTURE_MER, TEXTURES   # noqa: E402

TRADUITS = set(TEXTURES.values())                                    # notre traduction WH3, remplacée en jeu

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
ATELIER = r"C:\TotalWar-CampaignMap"
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit)
WH1 = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns",
                   carte_config.CARTE_SOURCE)
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "textures-sol-wh1")
COMPILE = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE, "global_map")
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "terrain-backups")
DOSSIER = "terrain/textures/campaign/wh1"
NORMALE_CA = "terrain/textures/campaign/default/grass_wet/grass_wet0_normal.dds"

# texture de WH1 -> groupe de WH3 de même nature, absent de notre carte (vérifié par `controle`)
DONNEURS = {
    "grass_a0": "grass_flowers0", "grass_a1": "grass_flowers1", "grass_a2": "grass_flowers2",
    "grass_a3": "grass_flowers3", "grass_b0": "grass_wet1",
    "grass_dead0": "grass_dry0", "grass_dead1": "grass_dry1", "grass_dead2": "grass_dry2", "grass_dead3": "grass_dry3",
    "sand_a0": "sand_rocky0", "sand_b0": "sand_rocky1", "sand_b1": "sand_tropical2", "sand_b3": "sand_tropical3",
    "mud_a0": "mud_dry0", "marsh": "marsh0",
    "snow0": "ice0", "snow1": "ice1", "snow2": "ice2", "snow3": "ice3",
}


# LE JEU N'AFFICHE PAS LES TEXTURES DE WH1 (23.09.2026, 03 h 45 ; captures de Charles face à WH1, erreur 114) : il montre,
# pour chaque groupe, SA texture de CA, quel que soit le chemin écrit dans `texture_arrays.xml` (le sol de forêt brun
# sombre de WH1, `sand_b3`, 45 % de la carte, sortait en sable tropical beige de CA ; `grass_a2` en herbe fleurie ; la
# neige en glace sombre). Faute de pouvoir charger celles de WH1 sans toucher aux textures de CA des autres campagnes,
# chaque texture de WH1 prend le groupe de CA le plus proche en couleur (moyenne Lab, grain) ET en nature (sol de forêt,
# herbe, neige ; jamais de sol du Chaos) : même règle que pour la lave.
EQUIVALENTS_CA = {
    "sand_b3": "underlay_forest0",      # sol de forêt de WH1 (45 %) -> sous-bois de forêt de CA (75/68/48)
    "grass_a2": "underlay_forest1",     # (36 %) -> sous-bois herbeux (72/72/31)
    "grass_a0": "grass_wet0", "grass_a1": "grass_wet3", "grass_a3": "grass_wet2",
    "grass_b0": "sand_rocky2",
    "grass_dead0": "scree_sandy0", "grass_dead1": "sand_rocky3", "grass_dead2": "grass_tundra3",
    "grass_dead3": "grass_tundra2",
    "sand_a0": "sand_tropical1",        # lits de rivière (et routes de WH1, qui restent des tuiles de WH3)
    "sand_b0": "grass_tundra3", "sand_b1": "mud_wet2",
    "mud_a0": "scree_sandy1",           # fond de mer et plages
    "marsh": "marsh2",
    "snow0": "snow2", "snow1": "snow1", "snow2": "ice2", "snow3": "ice0",
}
# La neige et la glace de WH1 TELLES QUELLES (23.09.2026, 04 h 15 ; Charles : « vraiment la texture de Warhammer 1 pour la
# glace et la neige ») : `ice0` et `ice2` sont deux des 23 groupes qu'aucune campagne de CA n'emploie (mélanges des
# Empires, des Royaumes du Chaos et du prologue relevés : 0 pixel ; seul `warscape_asset_variation_db` cite leurs
# fichiers). Leurs fichiers de CA sont remplacés dans notre pack par les textures converties de WH1 : ailleurs, rien ne
# change à l'écran. Les deux neiges de WH1 les plus présentes y vont (snow3 43 575 px, snow2 40 634 px) ; snow0 et snow1
# (12 168 px) prennent la neige de CA la plus proche. Les groupes de corruption (`creep_*`), de brouillard de guerre
# (`shroud_*`) et de route, libres eux aussi, sont lus par d'autres effets : on n'y touche pas.
GLACE_WH1 = {"ice0": "snow3", "ice2": "snow2"}
# DANS NOS GROUPES (24.09.2026, chaîne 13 ; audit du pack, `rapport-pack-textures.md` : les six fichiers de CA remplacés
# changent la glace `ice0` / `ice2` de TOUTES les campagnes tant que le mod est actif, contre la règle « les campagnes
# coexistent, jamais remplacer un fichier de CA »). Depuis le registre de variantes à nous (BASE_VARIANTES_WH1, chaîne 9),
# snow2 et snow3 vont dans des groupes `wh1_snow2`, `wh1_snow3` comme les autres textures de WH1 : plus aucun fichier de CA
# remplacé (`remplacements_glace` rend une liste vide ; les six anciens fichiers sont à retirer du pack rouvert).
GLACE_WH1 = {}
# LES PIÉMONTS (23.09.2026, session du rendu ; relevé des Empires, `05-journal\\2026-09-23-essais-auto\\releve-visuel-ie.md`
# § 3 ; demande de Charles relayée par la construction : « une texture rocheuse au pied des montagnes, pas de texture de
# sous-bois »). Les pentes à découvert au pied des montagnes de WH1 (4 260 u² entre 0,5 et 1, 389 u² au-delà) portaient à
# 93 % le sous-bois de CA (`underlay_forest0/1`, équivalents du sol de forêt de WH1), aucune roche ; CA met de l'éboulis sur
# ses pentes (`scree_mountain3`, 15 % des pentes > 1 aux Montagnes Grises). Sur les pentes, le sous-bois devient l'éboulis de
# CA le plus proche de la couleur des montagnes de WH1 (textures de base de leurs maillages : 88/84/75 en moyenne, mesure
# du brouillon `couleurs_roches.py`) : `scree_flowers0` (87/81/72, éboulis herbeux) au pied des montagnes (à moins de
# DISTANCE_PIEMONT de leurs maillages, `relief-wh1\\montagnes_wh1.npy` écrit par le générateur) au-delà de PENTE_PIEMONT,
# `scree_mountain0` (80/75/67) partout au-delà de PENTE_ROCHE ; bords naturels (`terrain_wh1_vers_terry.contour_naturel`).
# (Premier essai à blanc sans la restriction au pied des montagnes : 3,3 millions de pixels, tous les coteaux de forêt.)
PIEMONTS = True
PENTE_PIEMONT, PENTE_ROCHE = 0.5, 1.0            # hauteur par unité du monde
DISTANCE_PIEMONT = 2.5                           # unités autour des maillages de montagne de WH1
SOUS_BOIS = ("underlay_forest0", "underlay_forest1")
ROCHE_PIEMONT, ROCHE_PENTE = "scree_flowers0", "scree_mountain0"
EMPRISE_MONTAGNES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1", "montagnes_wh1.npy")
# SOUS LES MONTAGNES (23.09.2026, 17 h 45 ; Charles : « des montagnes vertes, très vallonnées »). Aux distances de la
# caméra, le jeu dessinait les niveaux de détail grossiers des montagnes de WH1, sous lesquels notre sol (2 cm sous le plus
# fin) perçait sur 11 à 29 % de leur surface, avec le sous-bois vert de WH1 traduit. `montagnes_wh1.lod_fin_partout` garde le
# plus fin ; par sécurité (bords, lointain), le sol sous leur emprise prend la roche de CA la plus proche de la leur.
ROCHE_SOUS_MONTAGNE = "scree_mountain0"


def pentes_projet():
    """Pente (hauteur par unité du monde) du relief `height` du projet Terry (ligne 0 au nord), lissé sur 3 x 3 px ; en z,
    un pixel du raster vaut 2/√3 d'unité du monde divisé par le pas (erreur 89)."""
    import terrain_wh1_vers_terry as TT
    f = glob.glob(os.path.join(TT.PROJET, f"{CARTE}.height.*.tif"))
    if len(f) != 1:
        raise SystemExit(f"relief du projet introuvable ou ambigu : {f}")
    h = np.asarray(Image.open(f[0]), np.float64)
    pas = h.shape[1] / float(TT.LARGEUR_MONDE)
    p = np.pad(h, 1, mode="edge")
    hs = sum(p[1 + dy:1 + dy + h.shape[0], 1 + dx:1 + dx + h.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    gy, gx = np.gradient(hs)
    return np.hypot(gx * pas, gy * pas * 3 ** 0.5 / 2)


def piemonts(melange, idx):
    """(mélange, bilan) : le sous-bois des pentes au pied des montagnes devient éboulis (`PIEMONTS`) ; bilan compté hors
    des maillages de montagne (sous eux, le sol ne se voit pas)."""
    import terrain_wh1_vers_terry as TT
    pente = pentes_projet()
    if pente.shape != melange.shape:
        raise SystemExit(f"relief du projet {pente.shape} et mélange {melange.shape} de tailles différentes")
    if not os.path.exists(EMPRISE_MONTAGNES):
        raise SystemExit(f"{EMPRISE_MONTAGNES} absent : lancer terrain_wh1_vers_terry.py --apply")
    montagnes = np.load(EMPRISE_MONTAGNES)
    pas = melange.shape[1] / float(TT.LARGEUR_MONDE)
    pied = TT.distance_a(montagnes, int(DISTANCE_PIEMONT * pas) + 1) <= DISTANCE_PIEMONT * pas
    sous_bois = np.isin(melange, [idx[g] for g in SOUS_BOIS])
    piemont = TT.contour_naturel(pied & (pente > PENTE_PIEMONT), rayon=3, amplitude=0.2, echelle=12, graine=11)
    roche = TT.contour_naturel(pente > PENTE_ROCHE, rayon=3, amplitude=0.2, echelle=12, graine=13)
    out = np.array(melange, copy=True)
    out[sous_bois & piemont] = idx[ROCHE_PIEMONT]
    out[sous_bois & roche] = idx[ROCHE_PENTE]
    out[montagnes] = idx[ROCHE_SOUS_MONTAGNE]
    vu = ~montagnes
    bilan = {f"{ROCHE_SOUS_MONTAGNE} sous les maillages de montagne": int(montagnes.sum()),
             f"{ROCHE_PIEMONT} (hors maillages)": int((sous_bois & piemont & ~roche & vu).sum()),
             f"{ROCHE_PENTE} (hors maillages)": int((sous_bois & roche & vu).sum()),
             "sous-bois restant, pentes > 0,5 au pied des montagnes (hors maillages)":
                 int((np.isin(out, [idx[g] for g in SOUS_BOIS]) & pied & (pente > PENTE_PIEMONT) & vu).sum())}
    return out, bilan


def remplacements_glace():
    """[(chemin du pack, fichier local)] : les fichiers de CA des groupes de `GLACE_WH1`, remplacés par ceux de WH1."""
    out = []
    for groupe, wh1 in GLACE_WH1.items():
        for suffixe in ("_base_colour", "_material_map", "_normal"):
            local = os.path.join(SORTIE, *DOSSIER.split("/"), wh1 + suffixe + ".dds")
            if not os.path.exists(local):
                raise SystemExit(f"texture de WH1 absente : {local} (lancer --convertir)")
            out.append((f"terrain/textures/campaign/default/ice/{groupe}{suffixe}.dds", local))
    return out


def liste_wh1():
    """[(groupe, diffuse, normal, spec)] dans l'ordre de l'index de WH1 (texture_arrays.xml v1)."""
    t = open(os.path.join(WH1, "global_map", "texture_arrays.xml"), encoding="utf-8").read()
    g = re.findall(r"<group>([^<]+)</group>", t)
    tab = {n: re.findall(r"<texture>([^<]+)</texture>", re.search(rf"<{n}>(.*?)</{n}>", t, re.S).group(1))
           for n in ("diffuse_array", "normal_array", "spec_array")}
    return list(zip(g, tab["diffuse_array"], tab["normal_array"], tab["spec_array"]))


def niveaux_dxt5(dds):
    """Tranches des niveaux d'un DDS DXT5 (en-tête de 128 octets)."""
    h, w = struct.unpack_from("<II", dds, 12)
    mips = struct.unpack_from("<I", dds, 28)[0]
    o, out = 128, []
    for k in range(mips):
        hh, ww = max(1, h >> k), max(1, w >> k)
        n = max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * 16
        out.append(dds[o:o + n])
        o += n
    return out


def convertir():
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import contenu_pack as C
    src = C.SourcePacks(os.path.join(os.path.dirname(KIT), "data"))
    tete_normale = src.lire(NORMALE_CA)[:128]
    if (struct.unpack_from("<III", tete_normale, 12) != (1024, 1024, 1048576) or tete_normale[84:88] != b"DXT5"
            or struct.unpack_from("<I", tete_normale, 28)[0] != 10):
        raise SystemExit("en-tête de normale de CA inattendu")
    dest = os.path.join(SORTIE, *DOSSIER.split("/"))
    os.makedirs(dest, exist_ok=True)
    for groupe, diff, norm, spec in liste_wh1():
        t0 = time.time()
        img = np.array(Image.open(io.BytesIO(wh1.lire(diff.lower()))).convert("RGBA"))
        while img.shape[0] > 1024:
            img = bc7.reduire(img)
        img[..., 3] = 255
        base = bc7.dds_bc7(bc7.chaine(img), srgb=True)
        sg = np.array(Image.open(io.BytesIO(wh1.lire(spec.lower()))).convert("RGBA"))
        while sg.shape[0] > 1024:
            sg = bc7.reduire(sg)
        mat = np.zeros_like(sg)
        mat[..., 1] = 255 - sg[..., 3]
        mat[..., 3] = 255
        matiere = bc7.dds_bc7(bc7.chaine(mat), srgb=False)
        nb = wh1.lire(norm.lower())
        h, w = struct.unpack_from("<II", nb, 12)
        if nb[84:88] != b"DXT5" or (h, w) != (2048, 2048):
            raise SystemExit(f"{norm} : attendu DXT5 2048², trouvé {nb[84:88]!r} {w}x{h}")
        normale = tete_normale + b"".join(niveaux_dxt5(nb)[1:11])
        for suffixe, octets in (("_base_colour", base), ("_material_map", matiere), ("_normal", normale)):
            with open(os.path.join(dest, groupe + suffixe + ".dds"), "wb") as f:
                f.write(octets)
        print(f"  {groupe:12} -> {DONNEURS[groupe]:15} ({time.time() - t0:.1f} s)")
    # aussi dans working_data (Terry et BOB lisent le kit ; sans effet sur eux, mais le jeu de fichiers reste complet)
    wd = os.path.join(KIT, "working_data", *DOSSIER.split("/"))
    if os.path.exists(wd):
        shutil.rmtree(wd)
    shutil.copytree(dest, wd)
    print(f"textures écrites : {dest} (et {wd})")


def sauvegarde_bob():
    """(liste, mélange) de la dernière sauvegarde de BOB faite par `appliquer`, soit la sortie de la compilation en
    place quand la liste compilée cite déjà les textures de WH1 (contrôlé par l'appelant)."""
    listes = sorted(glob.glob(os.path.join(SAUVEGARDES, "texture_arrays-bob-*.xml")))
    if not listes:
        raise SystemExit("aucune sauvegarde de BOB dans " + SAUVEGARDES)
    stamp = os.path.basename(listes[-1])[len("texture_arrays-bob-"):-len(".xml")]
    melange = os.path.join(SAUVEGARDES, f"global_blend-bob-{stamp}.dds")
    if not os.path.exists(melange):
        raise SystemExit(f"sauvegarde de BOB incomplète : {melange} absent")
    print(f"  --refaire : repart de la sortie de BOB sauvegardée le {stamp}")
    with open(listes[-1], encoding="utf-8", newline="") as f:
        return f.read(), bytearray(open(melange, "rb").read())


CHEMINS_WH1 = False   # réécrire texture_arrays.xml vers les textures de WH1 : sans effet en jeu (erreur 114)
MARQUE = "saison_textures_wh1.txt"   # posée après la réécriture du mélange ; BOB la rend plus ancienne que lui
# LES TEXTURES DE WH1 EN GROUPES NEUFS (23.09.2026, 20 h 40, session du rendu ; Charles, 19 h 55 : « au lieu de créer des
# équivalents, convertis les textures de Warhammer 1 » ; 20 h 37 : « tu peux lancer l'essai des textures de WH1 en jeu »).
# Le jeu prend la texture de chaque groupe de la liste compilée dans `warscape_asset_variation_db/
# terrain_textures_campaign.assetdb` (espaces campaign_base_colour, campaign_material, campaign_normal ; clé = nom du
# groupe), commune à toutes les campagnes : d'où l'erreur 114. Essai : des groupes À NOUS (`wh1_<texture>`) ajoutés après
# les 144 de CA dans notre liste compilée (le mélange a 256 indices), déclarés dans une copie de cette base où les 440
# entrées de CA restent identiques à l'octet (`base_variantes_ca`), et le mélange de ces textures de WH1 renvoyé à eux
# (seulement là où il porte encore leur équivalent de CA : piémonts, roche sous les montagnes, mer et lits de rivière
# gardent leurs retouches). Hors de l'essai, pour ne pas le mêler à celui de l'eau : `mud_a0` (fond de mer) et `sand_a0`
# (lits de rivière) ; la neige de WH1 est déjà en jeu par `GLACE_WH1`. La copie de la base passe devant celle de CA quand
# le mod est actif : à REFAIRE depuis celle de CA après chaque mise à jour du jeu (9.0 le 24.09.2026).
GROUPES_WH1 = ("sand_b3", "grass_a2", "sand_b1", "grass_a3", "grass_a0", "sand_b0", "marsh", "grass_a1", "grass_dead3",
               "grass_dead2", "grass_dead0", "grass_dead1", "grass_b0", "mud_a0", "sand_a0", "snow0", "snow1", "snow2", "snow3")
# 20 h 45, Charles : « il faudrait vraiment que les textures de Warhammer 1 couvrent 100 % de la carte, pas 62 % ». TOUT le
# mélange reprend donc celui de WH1 (textures de ses tuiles de mer, de plage et de lit de rivière comprises, voir
# `textures_tuiles_wh1`) : plus d'éboulis de CA sous et au pied des montagnes (PIEMONTS, ROCHE_SOUS_MONTAGNE), ni de pixels
# gardés de BOB ; les deux neiges de WH1 déjà en jeu par GLACE_WH1 (snow3, snow2 sur ice0, ice2) y restent ; les rares
# pixels sans texture de WH1 (255) prennent celle du voisin le plus proche.
PARTOUT_WH1 = True
PREFIXE_GROUPE = "wh1_"
BASE_VARIANTES = "warscape_asset_variation_db/terrain_textures_campaign.assetdb"
# la copie HORS du dossier embarqué en bloc par build_pack (`textures-sol-wh1`, dont le garde-fou refuse tout chemin de
# WH3) : build_pack l'ajoute par son exception, `remplacements_base_variantes`, comme GLACE_WH1
SORTIE_BASE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "base-variantes-sol")
# La clé du plan d'eau de NOTRE carte, comme CA en déclare une pour chacune de ses trois cartes (espace
# `campaign_texture_terrain/campaigns/<carte>`, clé `water_plane_material`) ; notre carte n'en avait pas. Demande de la
# session « IA et modding 3D » (23.09.2026, 23 h 45 : « le lien qui manquait sans doute au jeu » vers son matériau,
# `masques_eau_carte.MATERIAU`). Même entrée que celle des Empires, chemin changé.
ESPACE_EAU = f"campaign_texture_terrain/campaigns/{CARTE}"
ESPACE_EAU_CA = "campaign_texture_terrain/campaigns/wh3_main_combi_map_1"
CLE_EAU = "water_plane_material"
EAU_CARTE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "eau-carte")
# Essai en deux temps : 1) groupes neufs dans notre liste seulement (si le jeu prend le chemin écrit quand la base ne
# connaît pas le groupe, aucun fichier de CA n'est remplacé) ; 2) seulement si 1) échoue, la copie de la base de CA avec nos
# clés (exception au garde-fou de build_pack à demander à la construction, comme GLACE_WH1).
# Le temps 1 a échoué (pack du 23.09.2026, 22 h 41 ; Charles, 23 h 35 : « j'ai vraiment l'impression que c'était les terres
# désolées du Chaos ») : le jeu n'a pas chargé nos groupes et a pris, pour les index 144 à 160, la dernière texture de son
# tableau (`wasteland_chaos3`, cendre 96/89/77). Preuve que la base est le registre : ses trois espaces de texture ont
# exactement les 144 clés de la liste de BOB, dans le même ordre (brouillon `base_variantes_registre.py`). Temps 2 : nos
# 17 clés déclarées à la suite, dans le même ordre que la liste (index 144 + k).
BASE_VARIANTES_WH1 = True
COULEUR_EDITEUR = (3, 3)              # rouge, vert des couleurs d'éditeur de nos groupes (le bleu les numérote)


def groupes_neufs(t, neuf, wh1_blend, garde, idx, n_ca):
    """(liste compilée, mélange, bilan) : les groupes `wh1_*` ajoutés aux cinq tableaux de la liste, et les pixels de
    chaque texture de WH1 de GROUPES_WH1 qui portent encore son équivalent de CA renvoyés à son groupe."""
    noms_wh1 = [g for g, *_ in liste_wh1()]
    neufs = []
    for nom in GROUPES_WH1:
        chemins = {k: f"{DOSSIER}/{nom}_{k}.dds" for k in ("base_colour", "material_map", "normal")}
        absents = [c for c in chemins.values() if not os.path.exists(os.path.join(SORTIE, *c.split("/")))]
        if absents:
            raise SystemExit(f"textures converties absentes : {absents[:3]} (lancer --convertir)")
        neufs.append((PREFIXE_GROUPE + nom, chemins))
    if n_ca + len(neufs) > 256:
        raise SystemExit("plus de 256 groupes : le mélange est sur un octet")

    def allonger(texte, tableau, balise, valeurs):
        m = re.search(rf"(<{tableau}>)(.*?)(\s*</{tableau}>)", texte, re.S)
        ajout = "".join(f"\n\t\t<{balise}>{v}</{balise}>" if v is not None else f"\n\t\t<{balise}/>" for v in valeurs)
        return texte[:m.end(2)] + ajout + texte[m.end(2):]
    t = allonger(t, "group_array", "group", [g for g, _ in neufs])
    t = allonger(t, "base_colour_array", "texture", [c["base_colour"] for _, c in neufs])
    t = allonger(t, "material_map_array", "texture", [c["material_map"] for _, c in neufs])
    t = allonger(t, "normal_roughness_occlusion_array", "normal_roughness_occlusion", [c["normal"] for _, c in neufs])
    t = allonger(t, "climate_array", "climate", [None] * len(neufs))
    for tableau, balise in (("group_array", "group"), ("base_colour_array", "texture"), ("material_map_array", "texture"),
                            ("normal_roughness_occlusion_array", "normal_roughness_occlusion"),
                            ("climate_array", "climate")):
        m = re.search(rf"<{tableau}>(.*?)</{tableau}>", t, re.S)
        if len(re.findall(rf"<{balise}\b", m.group(1))) != n_ca + len(neufs):
            raise SystemExit(f"{tableau} : longueur inattendue après ajout")
    neuf = neuf.copy()
    bilan = {}
    if PARTOUT_WH1:
        # tout le mélange de WH1 : chaque pixel prend son groupe neuf, ou le groupe de glace qui porte déjà sa neige de
        # WH1 ; les pixels sans texture de WH1 prennent celle du voisin le plus proche
        src = remplir_vides(wh1_blend, len(noms_wh1))
        table = np.full(256, 255, np.int32)
        for j, (g, _) in enumerate(neufs):
            table[noms_wh1.index(g[len(PREFIXE_GROUPE):])] = n_ca + j
        for glace, neige in GLACE_WH1.items():
            table[noms_wh1.index(neige)] = idx[glace]
        if (table[np.unique(src)] == 255).any():
            raise SystemExit(f"textures de WH1 sans groupe : {[noms_wh1[k] for k in np.unique(src) if table[k] == 255]}")
        neuf = table[src].astype(np.uint8)
        for j, (g, _) in enumerate(neufs):
            bilan[g] = int((neuf == n_ca + j).sum())
        for glace, neige in GLACE_WH1.items():
            bilan[f"{neige} (fichiers de WH1 sur {glace})"] = int((neuf == idx[glace]).sum())
        return t, neuf, neufs, bilan
    for j, (g, _) in enumerate(neufs):
        nom = g[len(PREFIXE_GROUPE):]
        zone = (wh1_blend == noms_wh1.index(nom)) & (neuf == idx[EQUIVALENTS_CA[nom]]) & ~garde
        neuf[zone] = n_ca + j
        bilan[g] = int(zone.sum())
    return t, neuf, neufs, bilan


def controle_compile(dossier_global_map):
    """Pour build_pack (23.09.2026, 21 h 35) : (bon, message) sur la liste et le mélange compilés, quel que soit le réglage
    de la dernière application, lu dans la MARQUE (et non dans GROUPES_WH1, que `--sans-groupes-wh1` coupe le temps d'une
    chaîne). Marque absente ou plus ancienne que le mélange : BOB a recompilé sans réécriture. Sans groupes neufs : la liste
    ne cite aucune texture de WH1 (erreur 114). Avec N groupes neufs : les cinq tableaux ont 144 + N entrées ; les N groupes
    après ceux de CA sont `wh1_<GROUPES_WH1>` dans l'ordre ; ceux de CA ne citent rien de WH1 ; chaque texture de WH1 citée
    existe dans `textures-sol-wh1` ; le mélange n'emploie aucun indice au-delà de la liste."""
    xml = os.path.join(dossier_global_map, "texture_arrays.xml")
    blend = os.path.join(dossier_global_map, "global_blend.dds")
    marque = os.path.join(dossier_global_map, MARQUE)
    if not os.path.exists(marque) or os.path.getmtime(marque) < os.path.getmtime(blend):
        return False, "mélange du sol : pas réécrit depuis la dernière compilation de BOB (lancer `textures_sol_wh1.py --apply`)"
    t = open(xml, encoding="utf-8").read()
    m = re.search(r"; (\d+) groupes neufs wh1_\*", open(marque, encoding="utf-8").read())
    n = int(m.group(1)) if m else 0
    if n == 0:
        if DOSSIER in t:
            return False, "liste compilée : cite des textures de WH1 sans groupes neufs (erreur 114)"
        return True, "sol : groupes de CA seulement, mélange réécrit depuis BOB"
    attendus = [PREFIXE_GROUPE + g for g in GROUPES_WH1]
    groupes = re.findall(r"<group>([^<]+)</group>", t)
    n_ca = len(groupes) - n                   # 144 en 8.1, 172 en 9.0
    if n != len(attendus) or groupes[n_ca:] != attendus or any(g.startswith(PREFIXE_GROUPE) for g in groupes[:n_ca]):
        return False, (f"liste compilée : {len(groupes)} groupes (marque : {n} neufs), attendu les groupes de CA puis "
                       f"{attendus[:3]}...")
    for tableau, balise in (("base_colour_array", "texture"), ("material_map_array", "texture"),
                            ("normal_roughness_occlusion_array", "normal_roughness_occlusion"), ("climate_array", "climate")):
        bloc = re.search(rf"<{tableau}>(.*?)</{tableau}>", t, re.S).group(1)
        entrees = re.findall(rf"<{balise}(?:>([^<]*)</{balise}>|/>)", bloc)
        if len(entrees) != n_ca + n:
            return False, f"{tableau} : {len(entrees)} entrées, {n_ca + n} attendues"
        if any(DOSSIER in e for e in entrees[:n_ca]):
            return False, f"{tableau} : un groupe de CA cite une texture de WH1"
    cites = re.findall(rf"{DOSSIER}/[\w]+\.dds", t)
    absents = [c for c in cites if not os.path.exists(os.path.join(SORTIE, *c.split("/")))]
    if len(cites) != 3 * n or absents:
        return False, f"textures de WH1 citées : {len(cites)} pour {3 * n} attendues ; absentes du projet : {absents[:3]}"
    b = open(blend, "rb").read()
    h, w = struct.unpack_from("<II", b, 12)
    if int(np.frombuffer(b[len(b) - h * w:], np.uint8).max()) >= n_ca + n:
        return False, "mélange : un indice au-delà de la liste compilée"
    return True, (f"sol : {n} groupes de WH1 après les {n_ca} de CA ({n_ca + n} groupes), {len(cites)} textures de WH1 "
                  "présentes")


def remplir_vides(m, n):
    """Le mélange de WH1 où chaque pixel sans texture (indice >= n) prend la texture du voisin le plus proche
    (dilatations successives, 4 voisins)."""
    m = m.copy()
    vide = m >= n
    for _ in range(64):
        if not vide.any():
            break
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = np.roll(np.roll(m, dy, 0), dx, 1)
            ok = vide & (v < n)
            m[ok] = v[ok]
            vide &= ~ok
    if vide.any():
        raise SystemExit(f"{int(vide.sum())} pixels sans texture de WH1 à plus de 64 px d'une texture")
    return m


# LE CATALOGUE SÉPARÉ (25.09.2026, 17 h 45, audit de compatibilité avec les autres mods de carte, accord de Charles) :
# remplacer `terrain_textures_campaign.assetdb` casse tout autre mod de carte qui livre le sien (The Old World de ChaosRobbie :
# 443 entrées, pas les nôtres ; un seul des deux vaut). CA range ses bases par usage (environment_map, terrain_textures_battle,
# terrain_textures_campaign) et l'exécutable cherche `*.assetdb` : le jeu lit sans doute TOUS les fichiers du dossier.
# ESSAI : un fichier À NOUS (`CATALOGUE_SEPARE_CHEMIN`) qui ne porte que nos ajouts (clés wh1_* des trois espaces de texture
# et clé du plan d'eau de notre carte), aucune entrée de CA ; la base de CA n'est plus remplacée. À juger EN JEU (sols de
# WH1 et mer de notre carte présents) ; si le jeu ne le lit pas, retour à la copie (False).
CATALOGUE_SEPARE = False
CATALOGUE_SEPARE_CHEMIN = "warscape_asset_variation_db/saison_des_revelations.assetdb"


def catalogue_separe(local):
    """(binaire, xml) du catalogue séparé tiré de notre copie `local` : ses ajouts seulement (contrôlés par
    `remplacements_base_variantes`), même en-tête (critères) que la base de CA."""
    import base_variantes_ca as BV
    import contenu_pack as C
    ca = C.SourcePacks(os.path.join(os.path.dirname(KIT), "data")).lire(BASE_VARIANTES)
    n_ca = len(BV.lire(ca)["entrees"])
    nous = BV.lire(open(local, "rb").read())
    nous["entrees"] = nous["entrees"][n_ca:]
    binaire = BV.ecrire(nous)
    x = open(local + ".xml", encoding="utf-8").read()
    debut, fin = x.index("<entries>") + len("<entries>"), x.rindex("</entries>")
    entrees = re.findall(r"<entry>.*?</entry>", x[debut:fin], re.S)
    garder = [e for e in entrees if re.search(rf"key='{PREFIXE_GROUPE}[^']*'", e) or f"namespace='{ESPACE_EAU}'" in e]
    xml = x[:debut] + "\n\t\t" + "\n\t\t".join(garder) + "\n\t" + x[fin:]
    if len(BV.lire(binaire)["entrees"]) != len(garder):
        raise SystemExit(f"catalogue séparé : {len(BV.lire(binaire)['entrees'])} entrées binaires, {len(garder)} en XML")
    return binaire, xml.encode("utf-8")


def remplacements_base_variantes():
    """[(chemin du pack, fichier local)] de la copie de la base de variantes de CA, pour build_pack (même rôle que
    `remplacements_glace`) ; contrôle d'abord que ses entrées de CA sont celles de la base de CA ACTUELLE du jeu, à
    l'octet, et que les ajouts sont seulement des clés `wh1_*` des trois espaces de texture, plus la clé du plan d'eau de
    notre carte vers notre matériau d'eau (présent dans `eau-carte`). [] si la copie n'existe pas."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import base_variantes_ca as BV
    import contenu_pack as C
    import masques_eau_carte
    local = os.path.join(SORTIE_BASE, *BASE_VARIANTES.split("/"))
    if not os.path.exists(local):
        return []
    ca = C.SourcePacks(os.path.join(os.path.dirname(KIT), "data")).lire(BASE_VARIANTES)
    nous = BV.lire(open(local, "rb").read())
    ref = BV.lire(ca)["entrees"]
    ajouts = nous["entrees"][len(ref):]
    if nous["entrees"][:len(ref)] != ref:
        raise SystemExit("base de variantes : nos entrées de CA diffèrent de la base de CA du jeu (mise à jour ?) : "
                         "relancer textures_sol_wh1.py --apply --refaire")

    def permis(e):
        if e["espace"] == ESPACE_EAU:
            return e["cle"] == CLE_EAU and [v["fichier"] for v in e["variantes"]] == [masques_eau_carte.MATERIAU]
        return e["cle"].startswith(PREFIXE_GROUPE) and e["espace"] in ("campaign_base_colour", "campaign_material",
                                                                       "campaign_normal")
    if not all(permis(e) for e in ajouts):
        raise SystemExit("base de variantes : un ajout hors des clés wh1_* des trois espaces de texture et de la clé du "
                         "plan d'eau de notre carte")
    if any(e["espace"] == ESPACE_EAU for e in ajouts) and \
            not os.path.exists(os.path.join(EAU_CARTE, *masques_eau_carte.MATERIAU.split("/"))):
        raise SystemExit(f"base de variantes : la clé du plan d'eau cite {masques_eau_carte.MATERIAU}, absent de {EAU_CARTE}")
    if CATALOGUE_SEPARE:
        binaire, xml = catalogue_separe(local)
        dossier = os.path.join(SORTIE_BASE + "-separe", *CATALOGUE_SEPARE_CHEMIN.split("/")[:-1])
        os.makedirs(dossier, exist_ok=True)
        sortie = os.path.join(dossier, CATALOGUE_SEPARE_CHEMIN.split("/")[-1])
        open(sortie, "wb").write(binaire)
        open(sortie + ".xml", "wb").write(xml)
        return [(CATALOGUE_SEPARE_CHEMIN, sortie), (CATALOGUE_SEPARE_CHEMIN + ".xml", sortie + ".xml")]
    return [(BASE_VARIANTES, local), (BASE_VARIANTES + ".xml", local + ".xml")]


def base_variantes(neufs):
    """{chemin : octets} : la base de variantes de CA (binaire et XML) avec nos groupes déclarés dans les trois espaces ;
    ses 440 entrées identiques à l'octet (contrôlé)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import base_variantes_ca as BV
    import contenu_pack as C
    src = C.SourcePacks(os.path.join(os.path.dirname(KIT), "data"))
    ca = src.lire(BASE_VARIANTES)
    ca_xml = src.lire(BASE_VARIANTES + ".xml")
    if ca is None or ca_xml is None or not BV.aller_retour(ca):
        raise SystemExit(f"{BASE_VARIANTES} de CA absente ou illisible à l'octet")
    base = BV.lire(ca)
    n_ca = len(base["entrees"])
    espaces = (("campaign_base_colour", "base_colour"), ("campaign_material", "material_map"), ("campaign_normal", "normal"))
    for k, (g, chemins) in enumerate(neufs):
        for espace, cle in espaces:
            BV.ajouter(base, espace, g, chemins[cle], g, COULEUR_EDITEUR + (1 + k,))
    import masques_eau_carte
    modele_eau = next(e for e in base["entrees"] if e["espace"] == ESPACE_EAU_CA and e["cle"] == CLE_EAU)
    BV.ajouter(base, ESPACE_EAU, CLE_EAU, masques_eau_carte.MATERIAU, "", (0, 0, 0), modele=modele_eau)
    binaire = BV.ecrire(base)
    relue = BV.lire(binaire)
    if relue["entrees"][:n_ca] != BV.lire(ca)["entrees"] or len(relue["entrees"]) != n_ca + 3 * len(neufs) + 1:
        raise SystemExit("base de variantes : entrées de CA modifiées ou nombre inattendu")
    # XML : nos entrées sur le modèle de la première entrée de chaque espace, avant la fin de la liste
    x = ca_xml.decode("utf-8")
    ajout = []
    for g, chemins in neufs:
        for espace, cle in espaces:
            e = next(v for v in relue["entrees"] if v["espace"] == espace and v["cle"] == g)["variantes"][0]
            modele = re.search(rf"<entry>\s*<key serialise_version='1' namespace='{espace}' key='[^']+'/>.*?</entry>", x,
                               re.S).group(0)
            modele = re.sub(r"(namespace='[^']+' key=')[^']+'", rf"\g<1>{g}'", modele, count=1)
            modele = re.sub(r"filename='[^']*'", f"filename='{chemins[cle]}'", modele, count=1)
            modele = re.sub(r"display_name='[^']*'", f"display_name='{g}'", modele, count=1)
            for c, v in zip("rgb", e["rgb"]):
                modele = re.sub(rf"display_{c}='[^']*'", f"display_{c}='{v}'", modele, count=1)
            modele = re.sub(r"uid='[^']*'", f"uid='{e['uid']}'", modele, count=1)
            ajout.append(modele)
    modele = re.search(rf"<entry>\s*<key serialise_version='1' namespace='{re.escape(ESPACE_EAU_CA)}' key='{CLE_EAU}'/>.*?"
                       r"</entry>", x, re.S).group(0)
    modele = modele.replace(f"namespace='{ESPACE_EAU_CA}'", f"namespace='{ESPACE_EAU}'", 1)
    ajout.append(re.sub(r"filename='[^']*'", f"filename='{masques_eau_carte.MATERIAU}'", modele, count=1))
    fin = x.rindex("</entries>")
    x = x[:fin] + "\t" + "\n\t\t".join(ajout) + "\n\t" + x[fin:]
    return {BASE_VARIANTES: binaire, BASE_VARIANTES + ".xml": x.encode("utf-8")}


def appliquer(ecrire, refaire=False):
    xml = os.path.join(COMPILE, "texture_arrays.xml")
    blend = os.path.join(COMPILE, "global_blend.dds")
    marque = os.path.join(COMPILE, MARQUE)
    with open(xml, encoding="utf-8", newline="") as f:
        t = f.read()
    en_place = None
    if DOSSIER in t or (os.path.exists(marque) and os.path.getmtime(marque) >= os.path.getmtime(blend)):
        if not refaire:
            print("  déjà appliqué depuis la dernière compilation de BOB (texture_arrays.xml cite les textures de WH1 ;"
                  " --refaire repart de la sortie de BOB sauvegardée)")
            return
        en_place = t, open(blend, "rb").read()
        t, b = sauvegarde_bob()
    else:
        b = bytearray(open(blend, "rb").read())
    groupes = re.findall(r"<group>([^<]+)</group>", t)
    # 144 groupes de CA en 8.1, 172 en 9.0 (24.09.2026, 22 h 10 : 28 neufs, cwb_*, nagash_creep*, mud_lava_ash3-4, rangés
    # par ordre alphabétique : les index décalent ; tout se fait par nom et par `n_ca = len(groupes)`)
    if not 100 <= len(groupes) or any(g.startswith(PREFIXE_GROUPE) for g in groupes):
        raise SystemExit(f"texture_arrays.xml compilé : {len(groupes)} groupes, liste de BOB inattendue")
    print(f"  liste de BOB : {len(groupes)} groupes de CA")
    h, w = struct.unpack_from("<II", b, 12)
    ent = len(b) - h * w
    bob = np.frombuffer(bytes(b[ent:]), np.uint8).reshape(h, w)
    wh1_blend = np.fromfile(os.path.join(WH1, "global_map", "global_blend.dds"), np.uint8, count=h * w, offset=128).reshape(h, w)[::-1]
    # les textures que WH1 posait par ses tuiles (fond de mer, plages, lits de rivière) et que son mélange global
    # ne porte pas (GUIDE § 15, n° 114)
    import textures_tuiles_wh1
    wh1_blend, bilan_tuiles = textures_tuiles_wh1.corriger(wh1_blend)
    print(f"  textures des tuiles de WH1 : {bilan_tuiles}")
    utilises = set(np.unique(bob).tolist())
    idx = {g: i for i, g in enumerate(groupes)}
    wh1 = liste_wh1()
    if sorted(g for g, *_ in wh1) != sorted(DONNEURS) or sorted(EQUIVALENTS_CA) != sorted(DONNEURS):
        raise SystemExit("les groupes de WH1 ne sont pas ceux de DONNEURS / EQUIVALENTS_CA")
    garde_idx = set(MONTAGNE.values()) | {TEXTURE_MER}
    if CHEMINS_WH1:
        donneurs = {idx[d] for d in DONNEURS.values()}
        if len(donneurs) != len(DONNEURS):
            raise SystemExit("deux textures de WH1 sur le même groupe donneur")
        # ce que notre carte emploie encore après réécriture (mer, éboulis) ne doit pas être un donneur ;
        # les autres groupes de notre traduction disparaissent du mélange, ils peuvent l'être
        conflits = [d for d in DONNEURS.values()
                    if idx[d] in garde_idx or (idx[d] in utilises and idx[d] not in TRADUITS)]
        if conflits:
            raise SystemExit(f"groupes donneurs employés par notre carte : {conflits}")
        cible = DONNEURS
    else:
        absents = [g for g in EQUIVALENTS_CA.values() if g not in idx]
        if absents:
            raise SystemExit(f"groupes de CA absents de la liste compilée : {absents}")
        donneurs = {idx[d] for d in EQUIVALENTS_CA.values()}
        cible = EQUIVALENTS_CA
    table = np.zeros(256, np.uint8)
    for k, (groupe, *_) in enumerate(wh1):
        table[k] = idx[cible[groupe]]
    # gardés tels que BOB les a mis : la mer (fond `sand_tropical0` sous notre eau de WH3), les éboulis des
    # hex de montagne (`MONTAGNE` de terrain_wh1_vers_terry : WH1 y avait ses tuiles de montagne, pas encore
    # reconstituées) et les rares pixels sans texture de WH1 (valeur 255)
    garde = np.isin(bob, sorted(garde_idx)) | (wh1_blend >= len(wh1))
    neuf = np.where(garde, bob, table[wh1_blend]).astype(np.uint8)
    if PIEMONTS and not CHEMINS_WH1 and not (GROUPES_WH1 and PARTOUT_WH1):
        neuf, bilan_piemonts = piemonts(neuf, idx)
        neuf = np.where(garde, bob, neuf).astype(np.uint8)
        print(f"  piémonts (sous-bois des pentes -> éboulis) : {bilan_piemonts}")
    compte = {groupe: int(((wh1_blend == k) & ~garde).sum()) for k, (groupe, *_) in enumerate(wh1)}
    if not (GROUPES_WH1 and PARTOUT_WH1):
        print(f"  global_blend : {int(garde.sum())} px gardés (mer, éboulis de montagne, sans texture) ; "
              f"textures de WH1 posées : {sorted(compte.items(), key=lambda kv: -kv[1])[:8]}")
    neufs, n_ca = [], len(groupes)
    if GROUPES_WH1 and not CHEMINS_WH1:
        t, neuf, neufs, bilan_g = groupes_neufs(t, neuf, wh1_blend, garde, idx, n_ca)
        print(f"  groupes neufs (textures de WH1 telles quelles) : {len(neufs)} ; pixels "
              f"{sum(bilan_g.values())} ({sum(bilan_g.values()) / neuf.size:.1%}) ; {bilan_g}")
    reste = sorted(set(np.unique(neuf).tolist()) - donneurs - garde_idx - set(range(n_ca, n_ca + len(neufs))))
    if reste:
        print(f"  (index de WH3 restants, pixels hors texture de WH1 : {[groupes[i] for i in reste]})")
    for groupe, donneur in (DONNEURS.items() if CHEMINS_WH1 else ()):
        i = idx[donneur]
        for tableau, suffixe in (("base_colour_array", "_base_colour"), ("material_map_array", "_material_map"),
                                 ("normal_roughness_occlusion_array", "_normal")):
            bloc = re.search(rf"<{tableau}>(.*?)</{tableau}>", t, re.S)
            entrees = re.findall(r"<(\w+)>([^<]+)</\1>", bloc.group(1))
            balise, ancien = entrees[i]
            if f"/{donneur}_" not in ancien:
                raise SystemExit(f"{tableau}[{i}] = {ancien} : pas le groupe {donneur}")
            nouveau_bloc = bloc.group(1).replace(f"<{balise}>{ancien}</{balise}>",
                                                 f"<{balise}>{DOSSIER}/{groupe}{suffixe}.dds</{balise}>", 1)
            t = t[:bloc.start(1)] + nouveau_bloc + t[bloc.end(1):]
    manquants = [p for p in re.findall(rf"{DOSSIER}/[\w]+\.dds", t)
                 if not os.path.exists(os.path.join(SORTIE, *p.split("/")))]
    if manquants:
        raise SystemExit(f"textures converties absentes : {manquants[:3]} (lancer --convertir)")
    if en_place is not None:
        # la sauvegarde doit être la sortie de la compilation en place : même liste réécrite, mêmes pixels gardés
        t_place, b_place = en_place
        place = np.frombuffer(b_place[ent:], np.uint8).reshape(h, w) if len(b_place) == len(b) else None
        garde_bob = np.isin(bob, sorted(garde_idx))
        # (groupes neufs : la liste en place a nos groupes après les 144 de CA)
        meme_liste = (t == t_place) if CHEMINS_WH1 else \
            (re.findall(r"<group>([^<]+)</group>", t_place)[:len(groupes)] == groupes)
        if not meme_liste or place is None or bytes(b_place[:ent]) != bytes(b[:ent]) or \
                not np.array_equal(place[garde_bob], bob[garde_bob]):
            raise SystemExit("la dernière sauvegarde de BOB n'est pas la sortie de la compilation en place : relancer BOB")
        print(f"  --refaire : pixels changés par rapport au mélange en place : {int((place != neuf).sum())}")
    if not ecrire:
        print("  contrôle fait ; relancer avec --apply")
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if en_place is None:
        shutil.copy2(xml, os.path.join(SAUVEGARDES, f"texture_arrays-bob-{stamp}.xml"))
        shutil.copy2(blend, os.path.join(SAUVEGARDES, f"global_blend-bob-{stamp}.dds"))
    else:                                        # la sortie de BOB est déjà sauvegardée : garder l'état remplacé
        shutil.copy2(xml, os.path.join(SAUVEGARDES, f"texture_arrays-applique-{stamp}.xml"))
        shutil.copy2(blend, os.path.join(SAUVEGARDES, f"global_blend-applique-{stamp}.dds"))
    # la base de variantes d'abord (dans le dossier embarqué par build_pack) : sans elle, nos groupes n'auraient pas
    # de fichiers pour le jeu ; sans groupes neufs, l'ancienne copie est rangée (le jeu reprend celle de CA)
    chemin_base = os.path.join(SORTIE_BASE, *BASE_VARIANTES.split("/"))
    if neufs and BASE_VARIANTES_WH1:
        for chemin, octets in base_variantes(neufs).items():
            dest = os.path.join(SORTIE_BASE, *chemin.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(octets)
        print(f"  base de variantes de CA + {3 * len(neufs)} clés à nous : {os.path.dirname(chemin_base)}")
    elif os.path.exists(chemin_base):
        rang = os.path.join(SAUVEGARDES, f"base-variantes-rangee-{stamp}")
        shutil.move(os.path.dirname(chemin_base), rang)
        print(f"  copie de la base de variantes rangée (pas demandée) : {rang}")
    # le mélange d'abord : la liste qui cite les textures de WH1 est la marque d'une réécriture complète
    b[ent:] = neuf.tobytes()
    with open(blend, "wb") as f:
        f.write(bytes(b))
    with open(xml, "w", encoding="utf-8", newline="") as f:
        f.write(t)
    with open(marque, "w", encoding="utf-8") as f:
        f.write(f"mélange de WH1 appliqué {stamp} ({'chemins de WH1' if CHEMINS_WH1 else 'équivalents de CA'}"
                f"{f' ; {len(neufs)} groupes neufs wh1_*' if neufs else ''})\n")
    print(f"  écrit : global_blend.dds ({'19 groupes -> textures de WH1' if CHEMINS_WH1 else 'textures de WH1 -> leurs groupes wh1_*' if neufs else 'textures de WH1 -> groupes de CA les plus proches'}), "
          f"texture_arrays.xml ({'réécrite' if CHEMINS_WH1 else f'celle de BOB + {len(neufs)} groupes wh1_*' if neufs else 'celle de BOB'}) ; "
          f"sauvegardes {stamp}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--convertir", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refaire", action="store_true",
                    help="déjà appliqué : repartir de la sortie de BOB sauvegardée (après un changement de ce script)")
    ap.add_argument("--sans-groupes-wh1", action="store_true",
                    help="sans les groupes neufs wh1_* (équivalents de CA) : pour un pack fait avant l'aménagement de "
                         "build_pack")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.sans_groupes_wh1:
        global GROUPES_WH1
        GROUPES_WH1 = ()
    if a.convertir:
        convertir()
    appliquer(a.apply, a.refaire)
    return 0


if __name__ == "__main__":
    sys.exit(main())
