#!/usr/bin/env python3
"""
props_wh1_vers_layers.py - les objets (props) du terrain de campagne de WH1, réécrits en entités des
calques Terry (`.layer`) de notre carte WH3, pour que BOB les compile dans `global_props.bin`.

Pourquoi (21.09.2026, 21 h 45, Charles : « la carte est vide », « il manque des villes ») : WH1
habillait carte et villes de 79 756 objets ; notre terrain n'en a aucun. Tout ce qui suit a été
établi sur les données, rien n'est deviné (journal `05-journal\\2026-09-21-fidelite\\carte.md`) :

- **lecture** : `lire_props_wh1.py` (grammaire des lots BMD v21 vérifiée sur tout le fichier) ;
- **cultures** : un lot par case et par variante ; le lot de base de la case référence chaque
  variante avec un masque d'un bit ; un objet présent dans plusieurs variantes y est recopié par
  BOB. Sens des bits relevé sur le contenu des variantes (`BITS_CULTURES`) : bit 0 = habillage
  naturel de la région, visible de tous ; masque nul, bits 6 et 8 = dévastation et corruption du
  Chaos ; bit 12 = corruption vampirique ; bits 7, 9, 10, 11, 13 = petits habillages propres à un
  occupant (Bretonnie, Nains, Empire, Peaux-Vertes, Elfes sylvains) ;
- **rotation** : Terry écrit `rotation="rx ry rz"` (degrés) pour la matrice compilée
  Rx(-rx)·Ry(-ry)·Rz(-rz) (vérifié sur 12 objets inclinés des Empires, écart 1e-5) ; les matrices
  de WH1 portent l'échelle par lignes (lignes orthogonales dans 3 017 cas non uniformes sur 3 017) ;
- **décalques** : octet 0 des drapeaux = 1 (5 795 objets) -> entité `ECDecal`, comme les Empires ;
- **modèles** : toujours **le fichier de WH1** (22.09.2026, Charles : « sans équivalences de WH3 ») :
  sous son chemin s'il manque à WH3 ou y est identique, sinon déplacé sous `_wh1/`
  (`fichiers_wh1.Relocateur`, qui corrige aussi les textures citées) ; la table `SUBSTITUTS` (seconde
  passe du 21.09.2026) reste désactivée ;
- **repère** : le monde de WH3 est l'espace des hex, celui des objets de WH1 : leur z est gardé ; les rasters
  (relief...) se lisent à la ligne de z × √3/2 (`Z_VERS_RASTER`, erreur 89) ;
- **hauteur** : celle de WH1, corrigée de ce dont notre relief a bougé à cet endroit (terre basse
  relevée, `terrain_wh1_vers_terry.py`).

Appelé par `terrain_wh1_vers_terry.py` ; seul, il fait un essai à blanc et un bilan :
    python props_wh1_vers_layers.py
"""

import hashlib
import math
import os
import re
import struct
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lire_props_wh1 as L                                         # noqa: E402
from contenu_pack import chemins_du_jeu                            # noqa: E402
from modeles_wh1 import SourceWH1                                  # noqa: E402

DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
# Sens des bits, relevé sur le contenu de chaque variante dans des régions dont on connaît l'état
# (21.09.2026, 21 h 55 ; détail dans le journal). Le bit 0 porte l'habillage naturel de la région
# (pierres elfiques à la Clairière Royale, roseaux et arbres de marais à Mousillon) : présent partout,
# c'est l'état par défaut -> visible de tous (masque vide, comme les objets communs des Empires).
# Le masque nul et les bits 6 et 8 portent la dévastation et la corruption du Chaos (tumeurs, pics
# nordiques, fissures, lave : jusque dans le Chêne des Âges) ; le bit 12 la corruption vampirique
# (tombes, crânes). Les Empires masquent ces décors par les mêmes groupes de cultures.
BIT_DEFAUT = 0
CHAOS = ("wh_dlc03_bst_beastmen", "wh_main_chs_chaos", "wh3_main_dae_daemons", "wh_dlc08_nor_norsca")
VAMPIRES = ("wh_main_vmp_vampire_counts", "wh2_dlc11_cst_vampire_coast")
BITS_CULTURES = {None: CHAOS, 6: CHAOS, 8: CHAOS, 12: VAMPIRES,
                 7: ("wh_main_brt_bretonnia",), 9: ("wh_main_dwf_dwarfs",), 10: ("wh_main_emp_empire",),
                 11: ("wh_main_grn_greenskins",), 13: ("wh_dlc05_wef_wood_elves",)}
BIT_DE_VARIANTE = {0: None, 1: 0, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11, 13: 12, 14: 13}   # b -> bit
# Les objets de WH1 sont exprimés dans l'espace des hex, dont la profondeur (338,9, celle qu'annonce la
# zone jouable) vaut celle du relief (293,5) multipliée par 2/√3. Vérifié sur les 73 961 objets
# (21.09.2026, 22 h 05) : en lisant le relief à z × √3/2, l'écart médian entre la hauteur d'un objet et
# le relief tombe de 1,20 à 0,26, celui des sommets des maillages de WH1 eux-mêmes (0,263).
# Repère (22.09.2026, 23 h 10, erreur 89) : **le monde de WH3 est cet espace des hex** (positions des entités de
# Terry, caméra, zone jouable) ; Terry y étire les rasters du relief (pixels carrés) de 2/√3 en z : il montre la mer
# là où la lecture « pixels carrés » met la terre, et l'inverse (deux essais à la caméra), et aux Empires les herbes de
# CA sont sur leur sol quand on lit le relief à z × √3/2 (37 % à 0,1 près, contre 3,5 % à z tel quel). On garde donc
# le z des objets de WH1 et on ne convertit que pour lire un raster. Du 21 au 22.09.2026, les objets étaient ramenés
# à z × √3/2 : tassés de 13 % vers le sud, ils volaient ou s'enfonçaient partout dans Terry.
Z_VERS_RASTER = 3 ** 0.5 / 2
# Recalage des objets hors du sol connu de WH1 (22.09.2026, 19 h 30 ; journal `05-journal\\2026-09-22-phase-4\\
# objets-zones-de-tuiles.md`). Là (tuiles de montagne, de falaise, de rivière de WH1, 36 % de la carte), notre sol
# n'est pas celui de WH1 : un objet gardé à sa hauteur de WH1 flotte ou s'enfonce (cercle de pierres enfoui dans une
# crête du sud, vu dans Terry). Chaque objet qui ne repose sur rien y est posé sur notre sol avec l'enfoncement de son
# modèle, mesuré sur ses exemplaires du sol connu (médiane du bas de la boîte moins le sol) ; un objet posé sur un
# autre (pierre sur une colline modelée, crâne sur un tertre) suit son support. Sur le sol connu, rien ne bouge.
ENFONCEMENT_DEFAUT = -0.05             # modèle sans exemplaire sur le sol connu
# un objet repose sur un autre si le haut de celui-ci est entre 0,1 sous son bas et 0,5 au-dessus (flanc d'une
# colline), l'autre commençant plus bas ; la végétation (matériau 97 des RMV2 de WH1) ne porte rien : sinon un
# arbre voisin, dont la boîte monte haut, « portait » tout ce qui est à ses pieds (5 371 objets au premier essai)
TOLERANCE_APPUI = 0.10
HAUT_APPUI_MAX = 0.50
MATERIAUX_SANS_APPUI = (97,)
FICHIERS_WH1 = os.path.join(r"C:\TotalWar-CampaignMap", "04-projets", "saison-des-revelations",
                            "fichiers-wh1")
KIT_WD = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\working_data"
# Décor qui n'est pas de la carte de campagne (22.09.2026) : l'écran de pré-bataille du Chaos de WH1 (toile de
# fond de 19 x 19 unités pour la caméra d'avant bataille) barrait la vue dans Terry ; les calques de campagne
# des Empires n'en posent aucun.
HORS_CAMPAGNE = ("/prebattle_screens/",)

# DÉSACTIVÉE le 21.09.2026 à 22 h 55 (décision de Charles : les vrais objets de WH1, pack privé ;
# « ce n'est pas du tout ceux de WH1 », erreur 67). Gardée comme savoir : l'équivalent WH3 de chaque
# rôle, pour une éventuelle version sans fichier de WH1.
SUBSTITUTS_ACTIFS = False
# Seconde passe (21.09.2026, 22 h 30) : les modèles de WH1 qui n'existent plus dans WH3 (297, RMV2 v7
# spéculaire contre v8 PBR) sont remplacés par le modèle de WH3 du même rôle et de la même culture,
# relevé dans les dossiers de campagne de WH3 (inventaire du 21.09.2026). Motif sur le nom de fichier
# de WH1 -> (dossier WH3, racine WH3) ; le numéro de variante de WH1 est ramené sur les variantes
# existantes (modulo). Une racine qui commence par « = » désigne un fichier précis de WH3. Le premier
# motif qui correspond l'emporte. Les objets sans rôle équivalent (plan d'eau, cascade, écran de
# pré-bataille...) restent écartés et comptés.
SUBSTITUTS = [
    # végétation : objets de WH3 préfixés par culture
    (r"^(emp_geothorn|emp_thorns|emp_bush)", "vegetation/shrubs", "emp_shrubs"),
    (r"^brt_tall_grass", "vegetation/grass", "brt_grass"),
    (r"^(brt_bush|brt_plant|brt_flowers)", "vegetation/shrubs", "brt_shrubs"),
    (r"^wef_tall_grass", "vegetation/grass", "wef_grass"),
    (r"^wef_grass_(winter|autumn)", "vegetation/grass", "wef_grass"),
    (r"^(wef_bush|wef_plant|wef_flowers|wef_fern)", "vegetation/shrubs", "wef_shrubs"),
    (r"^(vmp_tall_bush|vmp_bush|vmp_plant|vmp_mushrooms)", "vegetation/shrubs", "vmp_shrubs"),
    (r"^(mtn_bush|mtn_sticks|mtn_docleaf)", "vegetation/shrubs", "mtn_shrubs"),
    (r"^mtn_rocks", "generic_props/gen_rocks", "gen_small_rocks"),
    (r"^(marsh_mushrooms|marsh_bush|marsh_mangrove)", "vegetation/shrubs", "marsh_shrubs"),
    (r"^(grn_mushrooms|grn_geomushrooms)", "vegetation/shrubs_single", "=grn_mushroom_01"),
    (r"^(chs_plant|chs_bush|chs_spikes|chs_tumour_shrub)", "vegetation/shrubs", "chs_shrubs"),
    (r"^bst_grass", "vegetation/grass", "gen_grass"),
    (r"^wh_marsh", "vegetation/shrubs", "marsh_shrubs"),
    (r"^cauliflower", "vegetation/shrubs", "farm_cabbage"),
    (r"^brt_small_trees", "vegetation/trees", "brt_tree_oak_small"),
    (r"^brt_large_trees", "vegetation/trees", "brt_tree_oak_large"),
    (r"^(wef_small_trees|wef_small_autumn_trees)", "vegetation/trees", "wef_tree_oak_small"),
    (r"^(wef_large_trees|wef_large_autumn_trees)", "vegetation/trees", "wef_tree_oak_large"),
    (r"^(wef_large_dead_trees|wef_small_dead_trees)", "vegetation/trees", "gen_tree_dead_large"),
    (r"^(bst_small_trees|bst_medium_trees)", "vegetation/trees", "gen_tree_oak_small"),
    (r"^marsh_tree", "vegetation/trees", "mangrove_tree_evil"),
    (r"^vmp_(small|medium)_trees", "vegetation/trees", "grn_tree_evil_small"),
    (r"^vmp_large_trees", "vegetation/trees", "grn_tree_evil_large"),
    (r"^chs_(small|medium)_trees", "vegetation/trees", "chs_tree_pine_small"),
    (r"^chs_large_trees", "vegetation/trees", "chs_tree_pine_large"),
    (r"^wef_forest_edge", "vegetation/trees", "wef_tree_oak_small"),
    (r"^brt_forest_edge", "vegetation/trees", "brt_tree_oak_small"),
    # rochers, pierres dressées, glace
    (r"^grn_rock_of_tall", "generic_props/gen_rocks", "grn_sharp_rock"),
    (r"^brt_stacking_stone", "generic_props/rocks", "wef_stone"),
    (r"^brt_menhir", "generic_props/rocks", "wef_standing_stone"),
    (r"^wef_ice_shard", "generic_props/rocks", "wef_ice_shard"),
    (r"^(vamp_rock_skull)", "generic_props/skull_rocks", "standard_rock_skull"),
    (r"^(vamp_rock_jaw)", "generic_props/skull_rocks", "standard_rock_jaw"),
    (r"^marble_cliff", "resources/marble", "gen_marble"),
    (r"^rock_fall_pile", "resources/marble", "marble_rockfall"),
    # ruines
    (r"^ground_tile", "generic_props/ruins", "gen_ruin_platform"),
    (r"^(wall_|brt_ruin_wall|brt_ruin_house)", "generic_props/ruins", "gen_ruin_wall"),
    (r"^hef_ruin_arch", "generic_props/ruins", "gen_ruin_wall_arch"),
    (r"^stairs", "generic_props/ruins", "gen_ruin_stairs"),
    (r"^brt_ruin_tower", "generic_props/ruins", "gen_ruin_tower"),
    (r"^bricks_stacked", "", "=ksl_rubble_stone_01"),
    (r"^brt_ruin_wood", "", "=ksl_rubble_wood_01"),
    # pics, os, crânes, cornes (Chaos, Norsca, Hommes-bêtes)
    (r"^(norsca_spikes_single|chs_cmp_props_metalspike|chs_metal_spike|bst_metal_spike)", "", "=gen_metal_spike_01"),
    (r"^greenskin_small_spike", "settlements/greenskins", "=greenskin_spike"),
    (r"^norsca_totem", "settlements/norsca", "=nor_totem_01"),
    (r"^norsca_tusk_single", "generic_props/gen_bones", "gen_tusk_single"),
    (r"^norsca_tusk_group", "generic_props/gen_bones", "gen_tusk_group"),
    (r"^(chs_cmp_props_horn|chs_horn|chs_horns|bst_horn_)", "", "chs_horn"),
    (r"^(chs_skull_ram_horns|chs_skull_small_horns|bst_skull_(small|raml|all)_horns|bst_horns)", "generic_props/gen_bones", "gen_skull_horn"),
    (r"^(chs_skull|bst_skull|skull_)", "generic_props/gen_bones", "gen_bone_skull_cow"),
    (r"^(chs_bone|bst_bone)", "generic_props/gen_bones", "gen_bone_ribs"),
    (r"^(chs_bonecage_sway|bst_bonecage_sway)", "beastmen", "=bst_bonecage"),
    (r"^chs_pole", "beastmen", "=bst_pole"),
    (r"^chs_shield", "settlements/norsca", "shield"),
    (r"^bst_shield", "beastmen", "=bst_shield_a"),
    (r"^chs_bloodied_cloth", "beastmen", "bst_bloodied_cloth"),
    (r"^campaign_dragon_bone_body", "generic_props/gen_bones", "gen_dragon_bone_body"),
    (r"^campaign_dragon_skull", "generic_props/gen_bones", "gen_dragon_bone_skull"),
    (r"^campaign_dragon_bone_ribcage", "generic_props/gen_bones", "gen_dragon_bone_ribs"),
    # campements, habitat, ressources
    (r"^(empire_camps_braizer|stone_brazier)", "settlements/dwarfs", "dwf_brazier"),
    (r"^(woodern_shack|thacthed_shack|attachment_shack)", "settlements/norsca", "shack"),
    (r"^pile_of_wood", "resources/lumberyard", "=gen_woodpile"),
    (r"^scaffolding", "", "gen_scaffold"),
    (r"^mine_enterance", "resources/mines", "gen_mine_entrance"),
    (r"^(dlc02_prefab_as_mesh__greenskin_idol)", "settlements/greenskins", "greenskin_idol"),
    (r"^brt_lotl_statue", "", "=brt_lotl_statue"),
    (r"^(dwf_statue_big_01_rubble)", "settlements/dwarfs", "=dwf_statue_big_rubble_02"),
    (r"^00_dwf_statue", "settlements/dwarfs", "dwf_statue_big"),
    (r"^(empire_square|empire_triangle|empire_skew)", "generic_props/mountains/empire", "empire_mountain"),
    (r"^fence_", "generic_props/fences_spikes", "gen_fence"),
    (r"^(dwf_barrel|barrel)", "generic_props/barrels_crates", "gen_barrel"),
    (r"^crate", "generic_props/barrels_crates", "gen_crate"),
    (r"^ladder", "generic_props/scaffold", "=gen_ladder_01"),
    (r"^(norsca_chain|chs_rope_cylinder|bst_rope_cylinder)", "generic_props/gen_chains", "=gen_chain"),
    (r"^vmp_cobweb", "generic_props/cobwebs", "cobweb"),
    (r"^dye_vat", "resources/dye", "=gen_dye_vat_small_auburn"),
    (r"^ws_campaign_waterfall", "water_fall", "=campaign_waterfall"),
    # décalques (restent des décalques)
    (r"^leaves_0", "decals/leaves", "gen_leaves"),
    (r"^wef_decal_leaves_winter", "decals/leaves", "wef_decal_leaves_spring"),
    (r"^wef_(small_root|large_root|medium_branch_root)", "decals/roots", "wef_decal_roots"),
]


# IDENTIFIANTS UNIQUES (24.09.2026, chaîne 13 ; audit des doublons, `scratchpad\doublons13`) : la graine ne contient ni la
# rotation ni le masque ; 13 identifiants étaient portés par 23 entités de trop (4 piques vampiriques au même pied, tournées
# différemment, éclats de glace, épées, un mur nain). Une graine déjà vue dans la génération reçoit un numéro : le premier
# objet garde son identifiant, les suivants en ont un neuf. `entites_par_region` remet le compte à zéro.
_GRAINES_VUES = {}


def ident(graine):
    n = _GRAINES_VUES.get(graine, 0)
    _GRAINES_VUES[graine] = n + 1
    return "1" + hashlib.sha1((graine if n == 0 else f"{graine}#{n}").encode()).hexdigest()[:14]


def rotation_terry(matrice):
    """(rx, ry, rz) en degrés et (sx, sy, sz) pour Terry, depuis la matrice 3 x 3 de WH1."""
    M = np.array(matrice, float).reshape(3, 3)
    ech = np.linalg.norm(M, axis=1)
    R = M / np.where(ech == 0, 1, ech)[:, None]
    # R = Rx(a)·Ry(b)·Rz(c) avec a = -rx, b = -ry, c = -rz : R02 = sin b ; R12 = -sin a cos b ;
    # R22 = cos a cos b ; R01 = -cos b sin c ; R00 = cos b cos c. Deux solutions (b, pi - b) :
    # on garde celle dont les angles a et c sont les plus petits, comme les Empires (0, ry, 0).
    meilleur = None
    b0 = math.asin(max(-1.0, min(1.0, R[0, 2])))
    for b in (b0, math.pi - b0):
        cb = math.cos(b)
        if abs(cb) < 1e-6:
            a, c = math.atan2(R[2, 1], R[1, 1]), 0.0
        else:
            a = math.atan2(-R[1, 2] / cb, R[2, 2] / cb)
            c = math.atan2(-R[0, 1] / cb, R[0, 0] / cb)
        cout = abs(a) + abs(c)
        if meilleur is None or cout < meilleur[0] - 1e-9:
            meilleur = (cout, a, b, c)
    _, a, b, c = meilleur
    rx, ry, rz = (-math.degrees(t) for t in (a, b, c))
    return (rx, ry, rz), tuple(float(e) for e in ech)


def verifie_rotation(matrice, rot, ech):
    """Recompose la matrice depuis les angles de Terry : écart maximal."""
    def R(axe, t):
        c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
        return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
                "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
                "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axe]
    P = R("x", -rot[0]) @ R("y", -rot[1]) @ R("z", -rot[2])
    return float(np.abs(np.diag(ech) @ P - np.array(matrice).reshape(3, 3)).max())


def variante(base):
    """Numéro de variante d'un nom de modèle de WH1 : chiffres finaux, sinon lettre finale (a = 1)."""
    m = re.search(r"(\d+)[a-z]?$", base)
    if m:
        return int(m.group(1))
    m = re.search(r"_([a-z])$", base)
    return ord(m.group(1)) - ord("a") + 1 if m else int(hashlib.sha1(base.encode()).hexdigest(), 16) % 97


class Modeles:
    """Correspondance modèle de WH1 -> (chemin de WH3, mode) ; mode : même chemin, déplacé (même nom
    ailleurs), substitut (`SUBSTITUTS`) ; (None, None) si rien ne convient."""

    def __init__(self):
        from fichiers_wh1 import Relocateur
        self.jeu = chemins_du_jeu(DATA_WH3)
        self.wh1 = SourceWH1()
        self.reloc = Relocateur(self.wh1)
        self.par_nom = defaultdict(list)
        self.campagne = sorted(c for c in self.jeu if c.startswith("rigidmodels/campaign/")
                               and c.endswith((".rigid_model_v2", ".wsmodel")))
        for c in self.jeu:
            if c.startswith(("rigidmodels/campaign", "terrain/")):
                self.par_nom[c.rsplit("/", 1)[-1]].append(c)
        self.cache = {}

    def candidats(self, dossier, racine):
        pref = f"rigidmodels/campaign/{dossier}/" if dossier else "rigidmodels/campaign/"
        if racine.startswith("="):
            motif = re.compile(re.escape(racine[1:]) + r"$")
        else:
            motif = re.compile(re.escape(racine) + r"(_?\d+[a-z]?|_[a-z])?$")
        par_tige = {}
        for c in self.campagne:
            if not c.startswith(pref):
                continue
            tige = c.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if motif.fullmatch(tige):
                # un modèle de WH3 existe souvent en .rigid_model_v2 et en .wsmodel (matériaux) : on
                # prend le .wsmodel, la forme complète
                if tige not in par_tige or c.endswith(".wsmodel"):
                    par_tige[tige] = c
        return [par_tige[t] for t in sorted(par_tige)]

    def resout(self, modele):
        m = modele.lower().replace("\\", "/")
        if m in self.cache:
            return self.cache[m]
        cible, mode = None, None
        nom = m.rsplit("/", 1)[-1]
        base = nom.rsplit(".", 1)[0]
        final = self.reloc.cible(m) if m in self.wh1.ou else None
        if final is not None:
            # le vrai modèle de WH1 (livré par `modeles_wh1.py`, même Relocateur donc mêmes chemins)
            cible = final
            mode = ("fichier de WH1 (identique à WH3)" if m in self.reloc.identiques
                    else "version de CA (shader de WH1 absent de WH3)" if m in getattr(self.reloc, "par_ca", ())
                    else "fichier de WH1 déplacé (WH3 diffère)" if m in self.reloc.deplaces
                    else "fichier de WH1")
        elif m in self.jeu:
            cible, mode = modele, "fichier de WH3 (absent de WH1)"
        if cible is None and SUBSTITUTS_ACTIFS:
            for n in (nom, base + ".wsmodel", base + ".rigid_model_v2"):
                if self.par_nom.get(n):
                    cible, mode = sorted(self.par_nom[n])[0], "déplacé"
                    break
        if cible is None and SUBSTITUTS_ACTIFS:
            for motif, dossier, racine in SUBSTITUTS:
                if re.search(motif, base):
                    cands = self.candidats(dossier, racine)
                    if cands:
                        cible, mode = cands[(variante(base) - 1) % len(cands)], "substitut"
                    break
        if cible is None and SUBSTITUTS_ACTIFS:
            # même famille : la variante voisine du même modèle (…_decal_c -> …_decal_a, …small01 -> …small02)
            famille = re.sub(r"(_?\d+[a-z]?|_[a-z])$", "", base)
            if famille != base:
                cands = self.candidats("", famille)
                if cands:
                    cible, mode = cands[(variante(base) - 1) % len(cands)], "substitut"
        self.cache[m] = (cible, mode)
        return cible, mode

    def wh3(self, modele):
        return self.resout(modele)[0]


def objets_uniques():
    """Chaque objet de WH1 une seule fois, avec l'ensemble des bits (cultures) qui le voient et
    l'ensemble des bits présents dans sa case."""
    cases = defaultdict(dict)
    for court, region, a, v, blob in L.lots(L.GLOBAL_PROPS):
        if v is None or region is None:
            continue
        cases[(region, a)][BIT_DE_VARIANTE.get(v, v)] = L.objets(blob)
    out = []
    for (region, a), variantes in cases.items():
        bits_case = set(variantes)
        vus = {}
        for bit, objs in variantes.items():
            for o in objs:
                o["position"] = tuple(o["position"])        # espace des hex = monde de WH3 (Z_VERS_RASTER)
                cle = (o["modele"].lower(), tuple(round(x, 3) for x in o["position"]),
                       tuple(round(x, 3) for x in o["matrice"]))
                if cle not in vus:
                    vus[cle] = dict(o, region=region, bits=set())
                vus[cle]["bits"].add(bit)
        for o in vus.values():
            o["bits_case"] = bits_case
            out.append(o)
    return out


BIT_VAMPIRES = 12
# Les variantes de corruption (Chaos : bits 6, 8, nul ; vampires : bit 12) existent dans presque toutes les régions
# (25 624 et 8 036 objets) : WH1 les montrait selon la corruption de la région en cours de partie. Au tour 1, seule
# Mousillon est corrompue par les morts-vivants (Charles, 22.09.2026 : « la corruption vampirique, c'est normal, il y
# a Mousillon ») : son décor vampirique y est visible de tous, comme dans WH1 ; ailleurs, les variantes de corruption
# restent masquées aux cultures qui les portent (invisibles au départ, comme dans WH1).
REGIONS_VAMPIRIQUES_DEPART = {"wh_dlc05_mousillon_mousillon", "wh_dlc05_mousillon_martel",
                              "wh_dlc05_mousillon_castle_rachard", "wh_dlc05_mousillon_yremy"}
# Les régions en ruine au tour 1 (23.09.2026, 04 h ; Charles, captures WH1 / WH3 : « il manque des pics… les objets en
# forme de pic n'étaient pas là pour rien ») : les cinq régions sans propriétaire de `start_pos_regions` ; WH1 y montrait
# son décor de dévastation (masque nul : pics, tumeurs, fissures). WH3 n'a pas de masque « sans propriétaire » : ce décor
# y est visible de tous (il reste après la reprise de la région, faute de mieux).
REGIONS_DEVASTEES_DEPART = {"wh_dlc05_anmyr_tal_rond", "wh_dlc05_fyr_darric_threllock", "wh_dlc05_talsyn_tal_eth_ayr",
                            "wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_tal_jul_finel"}


def masque_culture(o):
    """(masque, garder). Seul le décor naturel (bit 0) est visible de tous, avec le décor vampirique de Mousillon
    (`REGIONS_VAMPIRIQUES_DEPART`). Sinon : les cultures des bits où l'objet apparaît (habillage d'un occupant,
    corruption du Chaos ou des Vampires). Un objet de la seule dévastation (masque nul) : visible de tous dans les
    régions en ruine au départ (`REGIONS_DEVASTEES_DEPART`), masqué au Chaos et aux Hommes-bêtes ailleurs (il était
    écarté jusqu'au 23.09.2026, 04 h). Erreur 66 : la règle « présent dans toutes les variantes de sa
    case = visible de tous » rendait permanents 5 277 décors du Chaos."""
    if BIT_DEFAUT in o["bits"]:
        return "", True
    if BIT_VAMPIRES in o["bits"] and o.get("region") in REGIONS_VAMPIRIQUES_DEPART:
        return "", True
    if None in o["bits"] and o.get("region") in REGIONS_DEVASTEES_DEPART:
        return "", True
    # Ailleurs, la dévastation (masque nul) prend le masque du Chaos et des Hommes-bêtes, comme les bits 6 et 8
    # (23.09.2026, 04 h ; Charles : « ces 52 effets et objets écartés, il faut absolument les avoir… c'est lié à la
    # corruption des hommes-bêtes ») : aux Empires, CA masque par culture ses décors de corruption (Nurgle 59 915,
    # vampires 55 016, skavens 49 069, Chaos et Hommes-bêtes 32 478...), qui paraissent là où cette corruption s'étend.
    cultures = sorted({c for b in o["bits"] for c in BITS_CULTURES.get(b, ())})
    if not cultures:
        return "", False
    return ",".join(cultures), True


# Les lacs de WH1 (22.09.2026, 22 h 15, erreur 85) : WH1 posait sur la terre des « plans d'eau » à l'altitude de chaque
# lac (`generic_props/terrain/water_plane`, un carré de 4 sommets, matériau 83 que WH3 n'a pas, textures de test
# grises). WH3 fait ses lacs en polygones d'eau (`ECPolygonMesh`, matériau d'eau de campagne : 361 aux Empires) : même
# carré, même orientation, même hauteur.
MODELE_PLAN_EAU = "generic_props/terrain/water_plane"
import eau_carte                                                    # noqa: E402
MATERIAU_EAU = eau_carte.materiau()               # notre matériau d'eau s'il existe (masques de notre carte)


def carre_eau(o, wh1):
    """(hx, hz, ry) du plan d'eau de WH1 `o` : demi-côtés du rectangle de ses sommets (à l'échelle de sa matrice) et
    rotation autour de y (degrés), comme `entite_eau` (23.09.2026, pour `etangs_wh1`)."""
    import struct as _s
    b = wh1.lire(o["modele"].replace("\\", "/").lower())
    off = _s.unpack_from("<I", b, 152)[0]
    _, _, _, voff, vc, ioff, _ = _s.unpack_from("<HHIIIII", b, off)
    pas_v = (ioff - voff) // vc
    if pas_v in (8, 12, 16):
        v = np.array([np.frombuffer(b, np.float16, count=3, offset=off + voff + pas_v * k).astype(np.float64)
                      for k in range(vc)])
    else:
        v = np.array([_s.unpack_from("<3f", b, off + voff + pas_v * k) for k in range(vc)])
    if float(np.abs(v[:, [0, 2]]).max()) < 0.05:
        raise ValueError(f"{o['modele']} : plan d'eau de {np.abs(v).max():.4f} unité, sommets mal lus")
    rot, ech = rotation_terry(o["matrice"])
    return float(np.abs(v[:, 0]).max()) * ech[0], float(np.abs(v[:, 2]).max()) * ech[2], rot[1]


def cle_eau(o):
    """Clé d'un plan d'eau de WH1 (région, position arrondie) : lien avec les étangs de `etangs_wh1`."""
    return (o["region"], tuple(round(float(c), 3) for c in o["position"]))


def entite_eau(o, wh1, position, masque):
    """Entité `ECPolygonMesh` d'eau pour le plan d'eau de WH1 `o` : rectangle des sommets du modèle (à l'échelle de sa
    matrice), rotation autour de y de sa matrice, à `position`."""
    import struct as _s
    b = wh1.lire(o["modele"].replace("\\", "/").lower())
    off = _s.unpack_from("<I", b, 152)[0]
    _, _, _, voff, vc, ioff, _ = _s.unpack_from("<HHIIIII", b, off)
    pas_v = (ioff - voff) // vc
    # sommets en DEMI-flottants (x, y, z, w puis uv : pas de 12 octets ; ±1,711 pour `water_plane`) : lus en flottants
    # 32 bits jusqu'au 23.09.2026, 04 h 35, ils donnaient des plans d'eau de 0,01 unité (lacs vides en jeu, erreur 118)
    if pas_v in (8, 12, 16):
        v = np.array([np.frombuffer(b, np.float16, count=3, offset=off + voff + pas_v * k).astype(np.float64)
                      for k in range(vc)])
    else:
        v = np.array([_s.unpack_from("<3f", b, off + voff + pas_v * k) for k in range(vc)])
    if float(np.abs(v[:, [0, 2]]).max()) < 0.05:
        raise ValueError(f"{o['modele']} : plan d'eau de {np.abs(v).max():.4f} unité, sommets mal lus")
    rot, ech = rotation_terry(o["matrice"])
    hx = float(np.abs(v[:, 0]).max()) * ech[0]
    hz = float(np.abs(v[:, 2]).max()) * ech[2]
    points = "".join(f'\t\t\t\t\t<point x="{px:.5f}" y="{pz:.5f}"/>\n'
                     for px, pz in ((hx, hz), (-hx, hz), (-hx, -hz), (hx, -hz)))
    pos = " ".join(f"{c:.5f}" for c in position)
    graine = f"eau:{o['region']}:{position}"
    return (f'\t\t<entity id="{ident(graine)}">\n'
            f'\t\t\t<ECPolygonMesh material="{MATERIAU_EAU}" affects_mesh_optimization="false"/>'
            '<ECVisibilitySettingsCampaign visible_in_tactical_view="False" visible_in_tactical_view_only="False"/>\n'
            f'\t\t\t<ECCampaignProperties visible_in_shroud="False" no_culling="true" culture_mask="{masque}"/>\n'
            f'\t\t\t<ECTransform position="{pos}" rotation="0. {rot[1]:.5f} 0." scale="1. 1. 1." pivot="0 0 0"/>\n'
            '\t\t\t<ECPolyline>\n\t\t\t\t<polyline closed="true">\n' + points +
            '\t\t\t\t</polyline>\n\t\t\t</ECPolyline>\n\t\t</entity>\n')


# Collines modelées de WH1 (23.09.2026, revue complète) : 82 objets (`wef_climate_hill_01` à `_04`, `climate_hill`),
# matériau 86 et textures factices (`test_gray`, `flatnormal`...), faits pour prendre l'aspect du sol dans WH1 (25 dans
# la clairière d'hiver de Tal Amere). Dans WH3, le matériau 86 affiche ses propres textures : bosses grises ou sombres.
# Ils sont fondus dans le relief (`terrain_wh1_vers_terry.rasters`), qui porte les textures de WH1, et ne sont plus posés.
def est_colline_de_relief(b):
    """RMV2 dont tous les morceaux du LOD 0 sont au matériau 86 avec la couleur factice `test_gray`."""
    if not b or b[:4] != b"RMV2":
        return False
    nb = struct.unpack_from("<I", b, 140)[0]
    off = struct.unpack_from("<I", b, 152)[0]
    mats = []
    for _ in range(nb):
        if off + 16 > len(b):
            break
        mat, _u, taille, voff = struct.unpack_from("<HHII", b, off)
        mats.append(mat == 86 and bool(re.search(rb"test_gray\.dds", b[off:off + voff], re.I)))
        if taille == 0:
            break
        off += taille
    return bool(mats) and all(mats)


_COLLINES = {}


def modele_colline(modele):
    """(sommets, triangles) du modèle de WH1 s'il est une colline modelée, sinon None (mis en cache)."""
    m = modele.replace("\\", "/").lower()
    if m not in _COLLINES:
        import sommets_rmv2
        from modeles_wh1 import SourceWH1
        wh1 = _COLLINES.setdefault("__source__", SourceWH1())
        b = wh1.lire(m)
        if b and m.endswith(".wsmodel"):
            g = re.search(rb"<geometry>([^<]+)</geometry>", b)
            b = wh1.lire(g.group(1).decode().replace("\\", "/").lower()) if g else None
        _COLLINES[m] = sommets_rmv2.maillage(b) if est_colline_de_relief(b) else None
    return _COLLINES[m]


def collines_de_relief():
    """[(sommets placés dans le monde de WH1 (espace des hex), triangles)] des collines modelées de WH1."""
    out = []
    for o in objets_uniques():
        g = modele_colline(o["modele"])
        if g is not None:
            v, t = g
            out.append((v @ np.array(o["matrice"], np.float64).reshape(3, 3) + np.array(o["position"], np.float64), t))
    return out


def est_decalque(o, modele):
    """Décalque si WH1 le marquait ainsi (octet 0) ou si son substitut de WH3 est un décalque."""
    return o["drapeaux"][0] == 1 or "/decals/" in modele.lower()


def entite(o, modele, rot, ech, position, masque):
    pos = " ".join(f"{v:.5f}" for v in position)
    r = " ".join(f"{v:.5f}" for v in rot)
    s = " ".join(f"{v:.5f}" for v in ech)
    commun = ('\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="False" visible_in_tactical_view_only="False"/>\n'
              '\t\t\t<ECPropHeightPatch apply_height_patch="False" for_camera_height_map_only="false"/>\n'
              '\t\t\t<ECCampaignProperties visible_inside_snow_region="True" visible_outside_snow_region="True" '
              'visible_inside_destruction_region="True" visible_outside_destruction_region="True" '
              f'visible_in_shroud="False" visible_in_shroud_only="False" no_culling="False" culture_mask="{masque}"/>\n'
              f'\t\t\t<ECTransform position="{pos}" rotation="{r}" scale="{s}" pivot="0 0 0"/>\n')
    if est_decalque(o, modele):
        corps = (f'\t\t\t<ECDecal model_path="{modele}" parallax_scale="0" tiling="0" normal_mode="DNM_BLEND" '
                 'apply_to_terrain="True" apply_to_objects="False" render_above_snow="False"/>\n')
    else:
        corps = ('\t\t\t<ECPropMesh/>\n'
                 f'\t\t\t<ECMesh model_path="{modele}" opacity="1"/>\n'
                 '\t\t\t<ECMeshRenderSettings receive_decals="True"/>\n')
    graine = f"prop:{o['region']}:{o['modele']}:{position}"
    return f'\t\t<entity id="{ident(graine)}">\n{corps}{commun}\t\t</entity>\n'


class Boites:
    """Boîte englobante (min, max) d'un modèle placé : celle du premier maillage du RMV2 (octet 24 de son en-tête,
    comme les maillages de terrain de WH1), un `.wsmodel` renvoyant à sa géométrie. Fichier cherché dans nos fichiers
    de WH1, puis dans `working_data`, puis dans les packs de WH3."""

    def __init__(self):
        self.cache = {}
        self.packs = None

    def _octets(self, chemin):
        for racine in (FICHIERS_WH1, KIT_WD):
            p = os.path.join(racine, *chemin.split("/"))
            if os.path.exists(p):
                return open(p, "rb").read()
        if self.packs is None:
            from contenu_pack import SourcePacks
            self.packs = SourcePacks(DATA_WH3)
        return self.packs.lire(chemin)

    def boite(self, chemin):
        chemin = chemin.replace("\\", "/").lower()
        if chemin not in self.cache:
            b, res = self._octets(chemin), None
            if b and chemin.endswith(".wsmodel"):
                m = re.search(rb"<geometry>([^<]+)</geometry>", b)
                res = self.boite(m.group(1).decode()) if m else None
            elif b and b[:4] == b"RMV2":
                first = int.from_bytes(b[152:156], "little")
                v = np.frombuffer(b, "<f4", count=6, offset=first + 24).astype(np.float64)
                res = (v[:3], v[3:], int.from_bytes(b[first:first + 2], "little"))
            self.cache[chemin] = res
        return self.cache[chemin]


def emprise(matrice, boite, position):
    """(bas, haut, xmin, xmax, zmin, zmax) de la boîte d'un objet posé (matrice de WH1 : lignes = axes X, Y, Z,
    échelle comprise ; z de la matrice déjà dans le repère du monde à l'échelle √3/2 près, négligeable ici)."""
    M = np.array(matrice, np.float64).reshape(3, 3)
    lo, hi = boite[0], boite[1]
    coins = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
    w = coins @ M + np.asarray(position, np.float64)
    return w[:, 1].min(), w[:, 1].max(), w[:, 0].min(), w[:, 0].max(), w[:, 2].min(), w[:, 2].max()


def recaler_hors_sol_connu(poses, boites, bilan):
    """`poses` : liste de dict (cible, matrice, x, y, z, sol, connu, decal) ; y modifié en place hors du sol connu."""
    famille = lambda c: re.sub(r"_?\d+$", "", c.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    for p in poses:
        b = None if p["decal"] else boites.boite(p["cible"])
        p["porteur"] = b is not None and b[2] not in MATERIAUX_SANS_APPUI
        if b is None:
            p["bas"] = p["haut"] = p["y"]
            p["xz"] = (p["x"], p["x"], p["z"], p["z"])
        else:
            bas, haut, x0, x1, z0, z1 = emprise(p["matrice"], b, (p["x"], p["y"], p["z"]))
            p["bas"], p["haut"], p["xz"] = bas, haut, (x0, x1, z0, z1)
    # enfoncement de chaque modèle (puis de sa famille) sur le sol connu
    par_modele, par_famille = defaultdict(list), defaultdict(list)
    for p in poses:
        if p["connu"] and not p["decal"]:
            par_modele[p["cible"]].append(p["bas"] - p["sol"])
            par_famille[famille(p["cible"])].append(p["bas"] - p["sol"])
    enf_m = {k: float(np.median(v)) for k, v in par_modele.items()}
    enf_f = {k: float(np.median(v)) for k, v in par_famille.items()}
    # grille des emprises (0,5 unité) pour chercher les supports
    grille = defaultdict(list)
    for i, p in enumerate(poses):
        if p["decal"]:
            continue
        x0, x1, z0, z1 = p["xz"]
        for gx in range(int(x0 // 0.5), int(x1 // 0.5) + 1):
            for gz in range(int(z0 // 0.5), int(z1 // 0.5) + 1):
                grille[(gx, gz)].append(i)
    decal = [0.0] * len(poses)
    fait = [p["connu"] for p in poses]
    for i in sorted((i for i, p in enumerate(poses) if not p["connu"]), key=lambda i: poses[i]["bas"]):
        p = poses[i]
        if p["decal"]:
            decal[i] = p["sol"] - p["y"]
            bilan["hors sol connu : décalques posés au sol"] += 1
            fait[i] = True
            continue
        cx, cz = (p["xz"][0] + p["xz"][1]) / 2, (p["xz"][2] + p["xz"][3]) / 2
        appui = None
        for j in grille[(int(cx // 0.5), int(cz // 0.5))]:
            q = poses[j]
            if j == i or not fait[j] or not q["porteur"] or q["bas"] >= p["bas"]:
                continue
            if (q["xz"][0] <= cx <= q["xz"][1] and q["xz"][2] <= cz <= q["xz"][3]
                    and p["bas"] - TOLERANCE_APPUI <= q["haut"] <= p["bas"] + HAUT_APPUI_MAX):
                if appui is None or q["haut"] > poses[appui]["haut"]:
                    appui = j
        if appui is not None:
            decal[i] = decal[appui]
            bilan["hors sol connu : portés par un autre objet"] += 1
        else:
            enf = enf_m.get(p["cible"], enf_f.get(famille(p["cible"]), ENFONCEMENT_DEFAUT))
            decal[i] = (p["sol"] + enf) - p["bas"]
            bilan["hors sol connu : posés au sol (enfoncement de leur modèle)"] += 1
        fait[i] = True
    ecarts = [abs(decal[i]) for i, p in enumerate(poses) if not p["connu"]]
    if ecarts:
        bilan["hors sol connu : déplacement médian (unités)"] = round(float(np.median(ecarts)), 3)
    for p, d in zip(poses, decal):
        p["y"] += d


TOLERANCE_VOL = 0.03                   # point le plus bas plus haut que le sol de plus de 0,03 : l'objet vole
CONTACT_SOL = 0.01                     # objet qui vole sur le sol de WH1 : point le plus bas 1 cm sous le sol
ENFONCEMENT_BORNES = (-0.5, 0.0)
# Appui (22.09.2026, 21 h ; Charles : « énormément d'objets volants » dans Terry). Relevé dans le repère de WH1, où
# les arrangements sont justes : un objet repose sur un autre si la surface réelle de celui-ci (ses triangles, pas sa
# boîte) passe sous son point le plus bas, entre 0,05 au-dessous et 0,30 au-dessus (objet un peu enfoncé dans son
# support). La première version jugeait sur la boîte englobante : une fissure, une colline, une tour « portaient »
# tout ce qui passait à leur hauteur, 3 345 objets restaient en l'air (erreur 80).
APPUI_SOUS, APPUI_DANS = 0.05, 0.30
# Un objet qui ne repose sur aucune surface et qui, dans WH1, ne touchait pas le sol (plus de 0,05 au-dessus) est
# accroché à ce qu'il touche (boîtes qui se recoupent, à 0,02 près) : chaîne à sa tour, crâne à son pieu, toile.
CONTACT = 0.02
HORS_SOL_WH1 = 0.05
# Un objet qui ne touche rien et sous lequel passe le tronc d'un arbre de WH1 y pend (toiles d'araignée du Massif d'Orcal,
# 0,5 au-dessus du sol, un arbre à moins de 0,05 : audit du 22.09.2026, 23 h)
PRES_TRONC = 0.10
HAUT_ARBRE = 3.0
# ce qui pend est haut ; un tertre ou une touffe à 0,1 - 0,2 du sol près d'un tronc flottait dans WH1 (audit de 23 h 27)
HAUT_PENDU = 0.25
# Objets qui épousent le sol (fissures, mares, dalles, collines modelées) : dans WH1, au moins la moitié des cellules
# de 0,1 de leur dessous sont à moins de 0,12 du sol (mesuré sur le sol connu), et ils font plus de 0,5 de large. Là
# où notre sol n'est pas celui de WH1, poser leur seul point le plus bas en laissait flotter le reste (fissure de 4
# unités en l'air dans les Montagnes Grises) : on les pose de façon que 99 % de leur dessous soit au sol ou dessous
# (à 90 %, le dixième restant d'une grande fissure flottait encore de plusieurs unités).
CELLULE = 0.1
CONFORME_PART, CONFORME_ECART, CONFORME_LARGEUR = 0.5, 0.12, 0.5
QUANTILE_CONFORME = 99
# LES MONTAGNES DE WH1 NE SONT PAS LE SOL QUE WH1 MONTRAIT (24.09.2026, chaîne 13 ; audit `rapport-objets-wh1-textures.md`,
# D2 et D3 ; brouillons `scratchpad\objets13`). Sous une montagne de WH1, `sol_wh1` est notre drapé de son maillage
# (lf + BASE + S x y local) et `sol` le relief de la mousse (`MOUSSE_MONTAGNES` : 0,03 au-dessus du maillage sur les replats,
# sous son point bas sur les parois, 0,15 dessous en médiane). Les objets de WH1 posés dessus disent que le sol que WH1
# montrait en différait localement : les 89 dalles de la ruine naine à l'est de Blackstone Post sont plates à 14,720
# (± 0,006) quand le drapé passe 0,05 à 1,76 au-dessus (médiane 0,64 ; aucune pose ni base du drapé ne les met à plat) ;
# les 53 de Karak Tzor, à 10,06, sont 0,05 à 0,52 au-dessus ; braseros de Grom, minerai du col de Gragrut, mur nain de
# Karak Tzor, tour d'Axe Bite, 0,32 à 1,00 au-dessus. La montagne comptant comme sol connu (`terrain_wh1_vers_terry.rasters`,
# 22.09.2026), l'arrangement de WH1 y était gardé tel quel, plus l'écart de la mousse (-0,19 à -0,29 sous la ruine), et la
# règle des pièces d'assemblage (HAUT_PENDU au-dessus de ce faux sol de WH1) gardait en l'air ces objets posés seuls.
# 1. SOL_VISIBLE_DES_MONTAGNES : sur une montagne, le sol des objets est le sol affiché, le plus haut du relief et du
#    maillage, et non plus le relief caché sous les parois (qui enfonçait tout objet de 0,15 en médiane dans la roche).
# 2. ASSEMBLAGES_HORS_MONTAGNES : la règle des pièces d'assemblage ne vaut plus sur une montagne ;
#    un objet sans appui qui y vole est posé au contact (CONTACT_SOL), comme partout sur le sol connu.
# 3. RUINES_SUR_LEURS_DALLES : sur une montagne, un objet entouré d'au moins DALLES_MIN dalles de WH1 (MOTIF_DALLES) à moins
#    de RAYON_DALLES prend pour sol de WH1 le bas médian de ces dalles : il est posé sur notre sol affiché à la hauteur où il
#    était au-dessus de ce dallage dans WH1 (dalles au ras du sol ; statue, tours, porte et murs empilés gardent leur place).
# Les feux, sons et lumières de WH1 à moins de DISTANCE_SUIVI d'un objet ainsi déplacé le suivent (`suivre_les_objets`).
# 25.09.2026, 13 h 55 (Charles, « couper les règles ») : ESSAI DU PLANTAGE +0x1AC7576 (erreur 265) : les trois règles,
# arrivées à la chaîne 14 juste avant le premier plantage, sont coupées pour la chaîne 16 (objets comme à la 13 bis) ; le
# vidage montre nos falaises de WH1 (cliff_inland_custom_passable) au moment du plantage. À remettre une à une si le
# plantage disparaît. Sauvegarde : 05-journal\scripts-backups\props_wh1_vers_layers-avant-essai-plantage-20260925-1355.py
SOL_VISIBLE_DES_MONTAGNES = False
ASSEMBLAGES_HORS_MONTAGNES = False
RUINES_SUR_LEURS_DALLES = False
MOTIF_DALLES = re.compile(r"/ground_tile_\d+\.")
RAYON_DALLES, DALLES_MIN = 1.0, 5
DISTANCE_SUIVI = 0.35
SUIVIS = defaultdict(list)             # maille de DISTANCE_SUIVI -> [(x, z, déplacement)] ; vidé par `entites_par_region`


def sol_des_objets(sol, sol_wh1, montagnes):
    """(chaîne 13) Le sol affiché pour les objets : sur les montagnes de WH1 (`montagnes`, masque), le plus haut du relief
    (`sol`) et du dessus de leur maillage (`sol_wh1`) ; ailleurs `sol` (SOL_VISIBLE_DES_MONTAGNES)."""
    if not SOL_VISIBLE_DES_MONTAGNES or montagnes is None or sol is None:
        return sol
    return np.where(montagnes, np.maximum(sol, sol_wh1), sol).astype(np.float32)


def suivre_les_objets(x, z):
    """(chaîne 13) Déplacement de l'objet déplacé par les règles des montagnes le plus proche de (x, z), à moins de
    DISTANCE_SUIVI ; 0 sinon : feu, scintillement et son d'un brasero de WH1 restent sur lui."""
    gx, gz = int(x // DISTANCE_SUIVI), int(z // DISTANCE_SUIVI)
    meilleur, d2 = 0.0, DISTANCE_SUIVI ** 2
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for sx, sz, dy in SUIVIS.get((gx + i, gz + j), ()):
                e = (sx - x) ** 2 + (sz - z) ** 2
                if e <= d2:
                    meilleur, d2 = dy, e
    return meilleur


def poser_sur_les_dalles(poses, pixel, sol, bilan):
    """(chaîne 13, RUINES_SUR_LEURS_DALLES) Sur une montagne de WH1, le sol de WH1 d'un objet entouré de dalles de WH1 est
    le bas médian de ces dalles. `sol` : sol affiché (raster, ligne 0 au nord) ; `pixel(x, z)` -> (ligne, colonne).
    `y`, `delta` et `sol` des poses modifiés en place ; `sol_dalles` retenu pour `poser_sur_le_sol`."""
    boites = Boites()
    grille = defaultdict(list)
    for p in poses:
        if p.get("montagne") and not p["decal"] and MOTIF_DALLES.search("/" + p["cible"].replace("\\", "/").lower()):
            b = boites.boite(p["cible"])
            if b is not None:
                bas = emprise(p["matrice"], b, p["o"]["position"])[0]
                grille[(int(p["x"] // RAYON_DALLES), int(p["z"] // RAYON_DALLES))].append((p["x"], p["z"], bas))
    for p in poses:
        if not p.get("montagne") or p["decal"]:
            continue
        gx, gz = int(p["x"] // RAYON_DALLES), int(p["z"] // RAYON_DALLES)
        bas = [b for i in (-1, 0, 1) for j in (-1, 0, 1) for x, z, b in grille.get((gx + i, gz + j), ())
               if (x - p["x"]) ** 2 + (z - p["z"]) ** 2 <= RAYON_DALLES ** 2]
        if len(bas) < DALLES_MIN:
            continue
        lc = pixel(p["x"], p["z"])
        p["sol_dalles"] = float(np.median(bas))
        p["sol"] = float(sol[lc])
        p["delta"] = p["sol"] - p["sol_dalles"]
        p["y"] = float(p["o"]["position"][1]) + p["delta"]
        p["ch13"] = True
        bilan["sol : sur une montagne, posés sur le dallage de leur ruine de WH1"] += 1


def cultures(masque):
    return set(masque.split(",")) if masque else None       # None : toutes


def visible_avec(support, objet):
    """Le support est-il visible chaque fois que l'objet l'est ?"""
    cs, co = cultures(support), cultures(objet)
    return cs is None or (co is not None and co <= cs)


def poser_sur_le_sol(poses, sol, pas, boites, bilan, sol_wh1=None, arbres=None):
    """Pose chaque objet (hors décalques) sur le sol affiché (`sol` : raster ligne 0 au nord, `pas` px par unité), au
    sommet près, sans qu'aucun ne flotte (22.09.2026 ; Charles : « je ne veux plus d'objets qui volent »).

    1. Dans le repère de WH1 (hauteur d'origine), chaque objet cherche son **appui** : l'objet dont la surface passe
       sous son point le plus bas (`APPUI_*`), sinon, s'il ne touchait pas le sol de WH1 (`sol_wh1`), l'objet que sa
       surface touche vraiment (`sommets_rmv2.se_touchent` ; des boîtes qui se recoupent ne suffisent plus : erreur 94),
       sinon un arbre de WH1 dont le tronc passe dans son emprise (`arbres` : liste des arbres de WH1, présents en jeu ;
       toiles et lanternes y pendent) ; l'appui doit commencer plus bas que lui et être visible chaque fois qu'il l'est.
    2. Du plus bas au plus haut. Un objet porté reçoit le même déplacement total depuis WH1 que son appui (les
       assemblages de WH1 restent entiers), **si la surface de l'appui sous lui reste au-dessus de notre sol** ; sinon
       (appui enfoncé là) il est traité comme un objet posé au sol. Un objet au sol qui vole est posé à l'enfoncement
       propre à son modèle (médiane de ses exemplaires du sol connu de WH1). Sur le sol connu (celui de WH1), rien
       d'autre ne bouge : l'arrangement de WH1 y est juste. Ailleurs, un objet entièrement enfoui est remonté, et s'il
       épouse le sol (`CONFORME_*`), c'est 99 % de son dessous qui est ramené au sol ou dessous.
    `poses` : dicts (o, cible, matrice, x, y, z, masque, decal, connu) ; y modifié en place. Positions dans le monde
    (espace des hex) ; les rasters se lisent à z × Z_VERS_RASTER."""
    import sommets_rmv2
    H, L = sol.shape
    famille = lambda c: re.sub(r"_?\d+$", "", c.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    geo = {}

    def geometrie(cible):
        if cible not in geo:
            b = boites._octets(cible.replace("\\", "/").lower())
            if b and cible.lower().endswith(".wsmodel"):
                m = re.search(rb"<geometry>([^<]+)</geometry>", b)
                b = boites._octets(m.group(1).decode().replace("\\", "/").lower()) if m else None
            r = sommets_rmv2.maillage(b) if b else None
            geo[cible] = r if r is not None and len(r[0]) else None
        return geo[cible]

    def sous(raster, xs, zs):
        cx = np.clip(xs * pas - 0.5, 0, L - 1.001)
        cy = np.clip((H - 1.5) - zs * Z_VERS_RASTER * pas, 0, H - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        return (raster[r0, c0] * (1 - fx) * (1 - fy) + raster[r0, c0 + 1] * fx * (1 - fy)
                + raster[r0 + 1, c0] * (1 - fx) * fy + raster[r0 + 1, c0 + 1] * fx * fy)

    def placer(p, y):
        v, t = geometrie(p["cible"])
        return v @ np.array(p["matrice"], np.float64).reshape(3, 3) + np.array([p["x"], y, p["z"]]), t

    def dessous(w):
        """Le sommet le plus bas de chaque cellule de 0,1 (vue de dessus)."""
        cle = np.floor(w[:, [0, 2]] / CELLULE).astype(np.int64)
        ordre = np.lexsort((w[:, 1], cle[:, 1], cle[:, 0]))
        cs = cle[ordre]
        prem = np.ones(len(cs), bool)
        prem[1:] = (cs[1:] != cs[:-1]).any(1)
        return w[ordre][prem]

    # 1. mesures : dans le repère de WH1 (y1) et sur notre sol (y courant)
    for p in poses:
        p["gmin"] = None
        p["appui"] = None
        p["classe"] = None
        if p["decal"] or geometrie(p["cible"]) is None:
            continue
        p["y1"] = float(p["o"]["position"][1])
        w1, _ = placer(p, p["y1"])
        k = int(np.argmin(w1[:, 1]))
        p["bas1"] = (float(w1[k, 0]), float(w1[k, 1]), float(w1[k, 2]))
        p["boite1"] = (w1.min(0), w1.max(0))
        d1 = w1[:, 1] - sous(sol_wh1, w1[:, 0], w1[:, 2]) if sol_wh1 is not None else None
        p["hors_sol_wh1"] = d1 is not None and float(d1.min()) > HORS_SOL_WH1
        p["haut_sol_wh1"] = float(d1.min()) if d1 is not None else None
        # entièrement sous le sol de WH1 : invisible dans WH1 (fissures à 4 unités sous terre au Massif d'Orcal) ;
        # un tel objet reste enfoui, on ne le remonte jamais (erreur 82)
        p["enfoui_wh1"] = d1 is not None and float(d1.max()) < 0
        if p.get("sol_dalles") is not None:
            # (chaîne 13) sur le dallage d'une ruine de WH1, son sol de WH1 est le dallage (RUINES_SUR_LEURS_DALLES)
            p["haut_sol_wh1"] = p["bas1"][1] - p["sol_dalles"]
            p["hors_sol_wh1"] = p["haut_sol_wh1"] > HORS_SOL_WH1
            p["enfoui_wh1"] = float(w1[:, 1].max()) < p["sol_dalles"]
        w, _ = placer(p, p["y"])
        d = w[:, 1] - sous(sol, w[:, 0], w[:, 2])
        p["gmin"], p["gmax"] = float(d.min()), float(d.max())
        b = boites.boite(p["cible"])
        p["porteur"] = b is not None and len(b) > 2 and b[2] not in MATERIAUX_SANS_APPUI
    mesures = [i for i, p in enumerate(poses) if p["gmin"] is not None]
    # arbres de WH1 (monde, hauteurs de WH1), mailles de 1
    grille_a = defaultdict(list)
    for k, (ax, ay, az) in enumerate(arbres if arbres is not None else ()):
        grille_a[(int(ax // 1.0), int(az // 1.0))].append((ax, ay, az))

    def pendu_a_un_arbre(p):
        """Un tronc d'arbre de WH1 passe dans l'emprise de l'objet (à PRES_TRONC près), sous son point le plus bas et à
        moins de HAUT_ARBRE de lui : l'objet (toile, lanterne) y pend en jeu, où la liste des arbres de WH1 est
        embarquée ; Terry, qui dessine ses propres forêts, le montre en l'air."""
        if p.get("haut_sol_wh1") is None or p["haut_sol_wh1"] < HAUT_PENDU:
            return False
        lo_p, hi_p = p["boite1"]
        for gx in range(int((lo_p[0] - PRES_TRONC) // 1.0), int((hi_p[0] + PRES_TRONC) // 1.0) + 1):
            for gz in range(int((lo_p[2] - PRES_TRONC) // 1.0), int((hi_p[2] + PRES_TRONC) // 1.0) + 1):
                for ax, ay, az in grille_a.get((gx, gz), ()):
                    if (lo_p[0] - PRES_TRONC <= ax <= hi_p[0] + PRES_TRONC and lo_p[2] - PRES_TRONC <= az <= hi_p[2]
                            + PRES_TRONC and ay < lo_p[1] < ay + HAUT_ARBRE):
                        return True
        return False

    # grille des boîtes (repère de WH1), mailles de 0,5
    grille = defaultdict(list)
    for i in mesures:
        lo, hi = poses[i]["boite1"]
        for gx in range(int(lo[0] // 0.5), int(hi[0] // 0.5) + 1):
            for gz in range(int(lo[2] // 0.5), int(hi[2] // 0.5) + 1):
                grille[(gx, gz)].append(i)
    # 2. appuis, dans le repère de WH1
    for i in mesures:
        p = poses[i]
        bx, by, bz = p["bas1"]
        meilleur, s_max = None, None
        for j in grille[(int(bx // 0.5), int(bz // 0.5))]:
            q = poses[j]
            if j == i or not q["porteur"] or q["bas1"][1] >= by or not visible_avec(q["masque"], p["masque"]):
                continue
            lo, hi = q["boite1"]
            if not (lo[0] <= bx <= hi[0] and lo[2] <= bz <= hi[2]) or hi[1] < by - APPUI_SOUS:
                continue
            w, t = placer(q, q["y1"])
            s = sommets_rmv2.surface_sous(w, t, bx, bz)
            if s is not None and by - APPUI_SOUS <= s <= by + APPUI_DANS and (s_max is None or s > s_max):
                meilleur, s_max = j, s
        if meilleur is not None:
            p["appui"], p["classe"] = meilleur, "porté"
            continue
        if not p["hors_sol_wh1"]:
            continue
        lo_p, hi_p = p["boite1"]
        wp, tp = placer(p, p["y1"])
        vus, recouvre = set(), None
        for gx in range(int(lo_p[0] // 0.5), int(hi_p[0] // 0.5) + 1):
            for gz in range(int(lo_p[2] // 0.5), int(hi_p[2] // 0.5) + 1):
                for j in grille[(gx, gz)]:
                    if j == i or j in vus:
                        continue
                    vus.add(j)
                    q = poses[j]
                    if q["bas1"][1] >= by or not visible_avec(q["masque"], p["masque"]):
                        continue
                    lo, hi = q["boite1"]
                    inter = np.minimum(hi, hi_p) - np.maximum(lo, lo_p) + CONTACT
                    if (inter > 0).all():
                        vol = float(np.prod(inter))
                        if recouvre is not None and vol <= recouvre[0]:
                            continue
                        wq, tq = placer(q, q["y1"])
                        if sommets_rmv2.se_touchent(wp, tp, wq, tq):
                            recouvre = (vol, j)
        if recouvre is not None:
            p["appui"], p["classe"] = recouvre[1], "accroché"
        elif pendu_a_un_arbre(p):
            p["classe"] = "arbre"
    # enfoncement et conformité de chaque modèle, mesurés sur le sol connu (objets sans appui, hauteur de WH1)
    par_m, par_f, conf, quant = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for i in mesures:
        p = poses[i]
        if not p["connu"] or p["appui"] is not None:
            continue
        w, _ = placer(p, p["y"])
        dd = dessous(w)
        ecart = dd[:, 1] - sous(sol, dd[:, 0], dd[:, 2])
        if -0.5 <= p["gmin"] <= TOLERANCE_VOL and p["gmax"] > 0:
            par_m[p["cible"]].append(p["gmin"])
            par_f[famille(p["cible"])].append(p["gmin"])
        large = max(np.ptp(w[:, 0]), np.ptp(w[:, 2])) > CONFORME_LARGEUR
        conf[p["cible"]].append(float(np.mean(np.abs(ecart) < CONFORME_ECART)) if large else 0.0)
        quant[p["cible"]].append(float(np.percentile(ecart, QUANTILE_CONFORME)))
    enf_m = {k: float(np.clip(np.median(v), *ENFONCEMENT_BORNES)) for k, v in par_m.items()}
    enf_f = {k: float(np.clip(np.median(v), *ENFONCEMENT_BORNES)) for k, v in par_f.items()}
    # la végétation (matériau 97 : herbes, buissons) n'épouse pas le sol au sens de cette règle : ses « dessous » sont
    # des brins et des feuilles hauts ; tirer 99 % de ses cellules au sol l'enterrait presque entière (audit du
    # 22.09.2026, 23 h : 3 050 plantes descendues de 0,41 en médiane, pivot de WH1 pourtant sur notre sol)
    vegetation = {poses[i]["cible"] for i in mesures if not poses[i]["porteur"]}
    conformes = {k: float(np.clip(np.median(quant[k]), -0.3, TOLERANCE_VOL))
                 for k, v in conf.items() if np.median(v) >= CONFORME_PART and k not in vegetation}
    bilan["sol : modèles qui épousent le sol"] = len(conformes)

    # 3. déplacements : total depuis WH1 (y final - y1), du plus bas au plus haut
    total = {}
    for i in sorted(mesures, key=lambda i: poses[i]["bas1"][1]):
        p = poses[i]
        j = p["appui"]
        if j is not None and j in total:
            q = poses[j]
            bx, _, bz = p["bas1"]
            w, t = placer(q, q["y1"] + total[j])
            s = sommets_rmv2.surface_sous(w, t, bx, bz)
            g = float(sous(sol, np.array([bx]), np.array([bz]))[0])
            if p["classe"] == "accroché" or (s is not None and s >= g - TOLERANCE_VOL):
                total[i] = total[j]
                bilan["sol : portés par un objet (surface)" if p["classe"] == "porté" else "sol : accrochés à ce qu'ils touchent"] += 1
                continue
            bilan["sol : appui enfoncé sous eux, posés au sol"] += 1
        p["appui"] = None
        t0 = p["y"] - p["y1"]
        if p["classe"] == "arbre":
            total[i] = p.get("delta", t0)             # pend à son arbre de WH1, qui suit notre sol
            bilan["sol : pendus à un arbre de WH1"] += 1
            continue
        assemblage = (p.get("haut_sol_wh1") is not None and p["haut_sol_wh1"] >= HAUT_PENDU
                      and p["gmin"] > TOLERANCE_VOL)
        if assemblage and ASSEMBLAGES_HORS_MONTAGNES and p.get("montagne"):
            # (chaîne 13) sur une montagne, « plus de 0,25 au-dessus de son sol dans WH1 » ne mesure que l'écart de notre
            # drapé au sol de WH1 : braseros, minerai, mur nain posés seuls y restaient en l'air (+0,31 à +0,99) ; près
            # d'un dallage, deux tours de la terrasse haute de Blackstone (0,8 au-dessus des dalles dans WH1) aussi
            assemblage = False
            p["ch13"] = True
            bilan["sol : sur une montagne, volaient sans appui (plus « pièces d'assemblage »), posés au contact"] += 1
        if assemblage:
            # Pièce d'assemblage de WH1 (23.09.2026, revue) : à plus de 0,25 au-dessus de son sol dans WH1, sans appui
            # trouvé, l'objet tient à une structure dont le contact est trop fin pour `se_touchent` (cornes et crânes
            # des totems du Chaos, lanternes, attaches de cabanes, chaînes, cheminées, pierres de dragon empilées :
            # 65 objets posés au sol à tort, jusqu'à 1 unité plus bas). Il garde sa hauteur de WH1 (au décalage de
            # notre sol près), comme ce qui pend aux arbres de WH1.
            total[i] = p.get("delta", t0)
            p["classe"] = "assemblage"
            bilan["sol : pièces d'assemblage de WH1 (plus de 0,25 au-dessus de son sol), gardées en place"] += 1
            continue
        w, _ = placer(p, p["y"])
        # sur le sol connu de WH1 (ses maillages de terrain), notre sol est le sien à 0,005 près (audit du 22.09.2026) :
        # l'arrangement de WH1 y est juste par construction, la règle ne sert qu'ailleurs (tuiles de WH1)
        if p["cible"] in conformes and not p["connu"]:
            dd = dessous(w)
            ecart = dd[:, 1] - sous(sol, dd[:, 0], dd[:, 2])
            q90 = float(np.percentile(ecart, QUANTILE_CONFORME))
            if q90 > TOLERANCE_VOL or (p["gmax"] < 0 and not p["enfoui_wh1"]):
                t0 += conformes[p["cible"]] - q90
                p["classe"] = "épouse le sol"
                bilan["sol : épousent le sol, posés à 99 %"] += 1
                total[i] = t0
                continue
        enf = enf_m.get(p["cible"], enf_f.get(famille(p["cible"]), ENFONCEMENT_DEFAUT))
        if p["gmin"] > TOLERANCE_VOL:
            # Sur le sol connu (celui de WH1), un objet qui vole flottait déjà dans WH1 (0,03 à 0,3 au-dessus de ses
            # maillages : assemblages de décor recopiés par les artistes sur un sol inégal) : on le descend juste au
            # contact, son point le plus bas CONTACT_SOL sous le sol. L'enfoncement type de son modèle le descendait
            # bien plus bas que WH1 : tertres de crânes enterrés en entier, rochers à moitié (audit du 23.09.2026 :
            # 961 objets descendus de 0,117 en médiane pour 0,061 de vol, jusqu'à 0,39 ; erreur 101). Ailleurs, la
            # hauteur de WH1 ne dit rien de notre sol : l'enfoncement du modèle reste la meilleure estimation.
            t0 += (-CONTACT_SOL if p["connu"] else enf) - p["gmin"]
            p["classe"] = "posé"
            bilan["sol : volaient, descendus au contact (sol de WH1)" if p["connu"] else
                  "sol : volaient, posés à l'enfoncement de leur modèle (sol inconnu)"] += 1
        elif p["connu"]:
            # sur le sol de WH1, un objet qui ne vole pas garde sa hauteur de WH1 (pieux plantés, fissures en creux) :
            # 709 remontés à tort avant le 22.09.2026, 23 h 30 (audit, lot 4)
            p["classe"] = "déjà"
            bilan["sol : déjà posés"] += 1
        elif p["gmax"] < 0 and p["enfoui_wh1"]:
            t0 = p.get("delta", t0)                 # sans le recalage hors sol connu, qui l'aurait remonté
            p["classe"] = "enfoui dans WH1"
            bilan["sol : enfouis dans WH1 aussi, laissés sous terre"] += 1
        elif p["gmax"] < 0:
            t0 += enf - p["gmin"]
            p["classe"] = "remonté"
            bilan["sol : enfouis, remontés"] += 1
        else:
            p["classe"] = "déjà"
            bilan["sol : déjà posés"] += 1
        total[i] = t0
    deplaces = []
    for i, t0 in total.items():
        p = poses[i]
        neuf = p["y1"] + t0
        if abs(neuf - p["y"]) > 1e-6:
            deplaces.append(abs(neuf - p["y"]))
        p["y"] = neuf
    if deplaces:
        bilan["sol : déplacement médian des objets déplacés"] = round(float(np.median(deplaces)), 3)


def entites_par_region(largeur_monde, hauteur_nous=None, hauteur_wh1=None, regions_connues=None, sol_connu=None,
                       poses_out=None, etangs=None, montagnes=None):
    """{région: [entités XML]}, et un bilan. `hauteur_*` : rasters (ligne 0 = nord) pour recaler la
    hauteur ; sans eux, la hauteur de WH1 est gardée telle quelle. `sol_connu` (22.09.2026) : masque des
    pixels où notre sol est celui de WH1 ; ailleurs (tuiles de montagne et de falaise de WH1, pas encore
    reconstituées), un objet qui flotterait au-dessus de notre sol y est reposé (capture de Charles dans
    Terry : « plein de trucs flottants »). `etangs` (23.09.2026, session du rendu) : {`cle_eau` : entité XML} des
    étangs de `etangs_wh1`, qui remplacent les carrés d'eau des plans d'eau de WH1. `montagnes` (24.09.2026, chaîne 13) :
    masque des pixels sous les maillages de montagne de WH1 (SOL_VISIBLE_DES_MONTAGNES et suivantes)."""
    _GRAINES_VUES.clear()
    SUIVIS.clear()
    modeles = Modeles()
    objs = objets_uniques()
    bilan = Counter()
    absents = Counter()
    ecart_rot = 0.0
    orient = None
    if hauteur_nous is not None:
        h, w = hauteur_nous.shape
        pas = w / largeur_monde

        def pixel(x, z, nord_en_haut):
            col = int(min(max(x * pas, 0), w - 1))
            zr = z * Z_VERS_RASTER                   # monde (espace des hex) -> ligne du raster
            lig = int(min(max((h - 1) - zr * pas if nord_en_haut else zr * pas, 0), h - 1))
            return lig, col
        # orientation nord-sud : la hauteur des objets suit-elle le terrain ?
        echant = objs[::max(1, len(objs) // 4000)]
        ecarts = {}
        for sens in (True, False):
            d = [abs(o["position"][1] - hauteur_wh1[pixel(o["position"][0], o["position"][2], sens)]) for o in echant]
            ecarts[sens] = float(np.median(d))
        orient = min(ecarts, key=ecarts.get)
        bilan["orientation_nord_en_haut"] = int(orient)
        print(f"  objets : écart médian hauteur objet / terrain de WH1 : z vers le nord {ecarts[True]:.3f}, "
              f"z vers le sud {ecarts[False]:.3f} -> {'nord' if orient else 'sud'}")
        if ecarts[orient] * 3 > ecarts[not orient]:
            raise SystemExit("orientation des objets ambiguë : rien n'est écrit")
    out = defaultdict(list)
    poses = []
    visible = sol_des_objets(hauteur_nous, hauteur_wh1, montagnes)          # (chaîne 13)
    for o in objs:
        if any(motif in o["modele"].replace("\\", "/").lower() for motif in HORS_CAMPAGNE):
            bilan["écartés : écran de pré-bataille"] += 1
            continue
        masque, garder = masque_culture(o)
        if not garder:
            bilan["écartés : culture hors campagne"] += 1
            continue
        if modele_colline(o["modele"]) is not None:
            bilan["collines modelées de WH1 fondues dans le relief (non posées)"] += 1
            continue
        if MODELE_PLAN_EAU in o["modele"].replace("\\", "/").lower():
            # plan d'eau de WH1 (lac en altitude) -> polygone d'eau de WH3, à sa hauteur (jamais « posé au sol »)
            region = o["region"] if (regions_connues is None or o["region"] in regions_connues) else None
            if etangs is not None and cle_eau(o) in etangs:
                out[region].append(etangs[cle_eau(o)])
                bilan["plans d'eau de WH1 -> étangs à contour naturel (etangs_wh1)"] += 1
                continue
            x, y, z = o["position"]
            if hauteur_nous is not None:
                y += float(hauteur_nous[pixel(x, z, orient)] - hauteur_wh1[pixel(x, z, orient)])
            out[region].append(entite_eau(o, modeles.wh1, (x, y, z), masque))
            bilan["plans d'eau de WH1 -> polygones d'eau de WH3"] += 1
            continue
        cible, mode = modeles.resout(o["modele"])
        if cible is None:
            absents[o["modele"].lower()] += 1
            bilan["écartés : modèle sans équivalent dans WH3"] += 1
            continue
        bilan[f"modèle : {mode}"] += 1
        rot, ech = rotation_terry(o["matrice"])
        ecart_rot = max(ecart_rot, verifie_rotation(o["matrice"], rot, ech))
        x, y, z = o["position"]
        p = dict(o=o, cible=cible, rot=rot, ech=ech, masque=masque, matrice=o["matrice"], x=x, y=y, z=z,
                 connu=True, sol=0.0, decal=est_decalque(o, cible))
        if hauteur_nous is not None:
            lc = pixel(x, z, orient)
            p["delta"] = float(hauteur_nous[lc] - hauteur_wh1[lc])
            p["y"] += p["delta"]
            p["sol"] = float(hauteur_nous[lc])
            p["connu"] = sol_connu is None or bool(sol_connu[lc])
            # (chaîne 13) sur une montagne de WH1, le sol affiché (SOL_VISIBLE_DES_MONTAGNES)
            p["montagne"] = montagnes is not None and bool(montagnes[lc])
            if p["montagne"]:
                p["delta"] = float(visible[lc] - hauteur_wh1[lc])
                p["y"], p["sol"] = float(o["position"][1]) + p["delta"], float(visible[lc])
            p["y_base"] = p["y"]
        poses.append(p)
    if RUINES_SUR_LEURS_DALLES and hauteur_nous is not None and montagnes is not None:
        poser_sur_les_dalles(poses, lambda x, z: pixel(x, z, orient), visible, bilan)
    if sol_connu is not None:
        boites = Boites()
        recaler_hors_sol_connu(poses, boites, bilan)
        # les arbres de WH1 (liste embarquée telle quelle dans le pack) : toiles et lanternes y pendent
        from arbres_wh1 import LISTE_WH1, lire_liste
        _, groupes = lire_liste(modeles.wh1.lire(LISTE_WH1))
        arbres = np.concatenate([recs[:, :12].copy().view("<f4").reshape(-1, 3) for _, recs in groupes]).astype(np.float64)
        # dernière passe, sur tous les objets et au sommet près : plus aucun objet en l'air (22.09.2026, 21 h)
        poser_sur_le_sol(poses, visible, hauteur_nous.shape[1] / largeur_monde, boites, bilan, sol_wh1=hauteur_wh1,
                         arbres=arbres)
        # (chaîne 13) feux, sons, lumières de WH1 : ils suivent les objets que les règles des montagnes ont déplacés
        for p in poses:
            if p.get("ch13") and abs(p["y"] - p["y_base"]) > 1e-3:
                SUIVIS[(int(p["x"] // DISTANCE_SUIVI), int(p["z"] // DISTANCE_SUIVI))].append(
                    (p["x"], p["z"], p["y"] - p["y_base"]))
        bilan["sol : objets déplacés par les règles des montagnes (chaîne 13), suivis par leurs feux"] = sum(
            len(v) for v in SUIVIS.values())
    for p in poses:
        o = p["o"]
        region = o["region"] if (regions_connues is None or o["region"] in regions_connues) else None
        out[region].append(entite(o, p["cible"], p["rot"], p["ech"], (p["x"], p["y"], p["z"]), p["masque"]))
        bilan["décalques" if p["decal"] else "objets"] += 1
        bilan["masque de culture" if p["masque"] else "visibles de toutes les cultures"] += 1
    bilan["écart de recomposition des rotations (max)"] = round(ecart_rot, 6)
    if poses_out is not None:                        # diagnostic : les poses et la décision prise pour chacune
        poses_out.extend(poses)
    return out, bilan, absents


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out, bilan, absents = entites_par_region(266.53)
    for k, v in bilan.items():
        print(f"  {k} : {v}")
    print(f"  régions : {len(out)} ; modèles absents : {len(absents)} "
          f"(les plus fréquents : {absents.most_common(5)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
