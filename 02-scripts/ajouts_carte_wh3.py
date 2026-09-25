#!/usr/bin/env python3
"""
ajouts_carte_wh3.py - ce que la carte de WH1 n'avait pas, ou que WH3 fait autrement, repris des Empires de CA : le son et
le scintillement des braseros, l'habillage des étangs, les rochers et herbes de montagne, la vie paysanne de Bretonnie.

Pourquoi (23.09.2026, session du rendu). Relevé des Empires (`05-journal\\2026-09-23-essais-auto\\releve-visuel-ie.md`) :
nos feux de brasero de WH1 n'ont ni son ni scintillement ; nos montagnes portent 6 objets par 100 u² contre 43 chez CA,
sans aucun rocher ni herbe de montagne (familles `rocks_small`, `rocks_large`, `grass_mtn` de la carte des arbres) ; nos
lacs n'ont ni roseaux ni berges de boue ; la Bretonnie n'a ni moulin ni fumée de cheminée ; peu de libellules, aucun nuage
de crête. Principe de Charles : la carte est celle de WH1 à 100 %, de WH3 seulement ce qui manque et reste cohérent ; le
23.09.2026 (« attaque tout ça ») il a demandé les corrections (braseros) et les ajouts (étangs, rochers, moulins, vie).
Chaque ajout a son drapeau (`AJOUTS`) : on le retire sans toucher au reste.

Gabarits relevés sur les calques des Empires (recherches de la session du rendu, rapports gardés dans
`05-journal\\2026-09-23-rendu-carte\\`) :
- torchère de route de CA : feu + scintillement `wh3_main_campaign_torch_flicker_light` (au pied, échelle 0,5) + son
  `Sound_Environment_Fire_Small_Torch` (point, 4,7 cm au-dessus du feu), SANS lumière ponctuelle : le scintillement est une
  source de lumière (`wh3_main_lib_lightsource`). Brasero de colonie de CA : lumière + feu, jamais de scintillement. Nos
  braseros de WH1 (lumière fixe dans WH1 aussi : 441 sur 441) prennent la recette de la torchère : le scintillement
  REMPLACE leur lumière fixe (sinon deux éclairages par feu, les « taches orange » du 23.09.2026) ;
- étang de CA : 3 roseaux `marsh_reeds_01` (0,5 ; 0,29 u dans l'eau ; eau + 0,04), 4 berges `gen_mudbank` (0,8 ; sur le
  bord ; eau - 0,29), 4 `dragon_stone_parts03-05` (sur le bord ; eau - 0,14), roches `gen_rock` (juste dehors), un son
  `Sound_Environment_Lake_Moderate` près du centre ; pour un étang de 8,4 u de tour, proportionnel au tour ailleurs ;
- rochers et herbes de montagne : familles de CA de la liste des arbres (`rocks_small_01-03`, `rocks_large_01-03` : les 04
  et 05 montrent `gen_spacer_01`, presque rien ; `grass_mtn_01-04`), par taches de 1 à 3 u² (1,8 objet par u² de tache),
  sur les replats, 3,3 + 1,5 + 3,0 par 100 u² ; enregistrement : x, y (au sol), z, puis octets 1, 0..5, 255 ; un
  propriétaire bretonnien ou elfe sylvain voit les modèles BASE ; aucune ligne de base (identifiants déjà dans db.pack) ;
- moulin à vent de CA : scène `gen_windmill.csc` (les ailes, 0,67, moyeu 0,857 au-dessus du sol) + 38 pièces de CA
  (cabanes, échafaudages, ponton...) du moulin de Grunburg, en repère local ; à 1,2 u au moins d'une route, sur un
  replat, près des champs ;
- roue à eau : scène `gen_watermill_wheel.csc` (0,838 ; axe x local perpendiculaire au courant ; axe 0,135 au-dessus de
  l'eau), son `Sound_Environment_Building_Rotating_Wheel`, deux éclaboussures, deux pans de cabane sur l'axe, une cabane ;
- fumée : `wh_main_campaign_chimney_smoke` (0,776) au sommet d'une cheminée (jamais sur un toit nu) ;
- libellules `wh_main_campaign_enviro_dragonflies` (0,5, au sol, près de l'eau) ; nuages de crête
  `wh3_main_campaign_enviro_mountain_clouds_thin` (1,77 au-dessus du sol, replats hauts, 10 u d'écart, lacet 107°) ;
- pont de pierre de CA (86 des 87 `bridge_stone` des Empires sont sur une route) : échelle 0,15 (2,1 u de long), axe long
  (x local) le long de la route, y = relief moyen des deux têtes - 0,307, un dallage `gen_tiles` à chaque tête. Charles
  (23.09.2026, 17 h 30) : en Athel Loren, les ponts de WH1 exactement (« respectable par rapport aux elfes sylvains ») ;
  ailleurs, la pierre ; « s'il doit y avoir un pont, il faut que ce soit bien intégré ». D'où le plan des traversées
  (`plan_ponts`, partagé avec `ponts_wh1`) : hors d'Athel Loren, le pont de pierre remplace la passerelle de WH1.

Interface (appelé par `terrain_wh1_vers_terry.ecrire_projet`) :
    entites(r, ambiance, objets) -> ([blocs XML <entity>] du calque `ajouts_wh3`, ambiance sans les lumières remplacées,
                                     bilan)
    arbres(liste, r) -> (octets de la liste d'arbres augmentée, bilan)
    IDS_ARBRES_CA : identifiants d'arbres de CA ajoutés à la liste (garde de `build_pack.py`)

Repère : monde des entités = espace des hex (x est, y haut, z nord) ; un raster se lit à la ligne z × √3/2 (erreur 89) ;
lacet t (degrés) : l'axe x local pointe vers l'angle monde -t ; X = X0 + xl cos t + zl sin t, Z = Z0 - xl sin t + zl cos t.

Usage :
    python ajouts_carte_wh3.py      # rappel des drapeaux et des identifiants d'arbres de CA
"""

import hashlib
import math
import os
import re
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit), sert aux identifiants
R3 = 3 ** 0.5 / 2
LARGEUR_MONDE = 266.53
AJOUTS = {
    "braseros": True,          # correction : son et scintillement des feux de brasero de WH1
    "etangs": True,            # habillage des étangs : roseaux, berges de boue, pierres, son de lac
    "rochers": True,           # rochers et herbes de montagne (liste des arbres)
    "moulins": True,           # moulins à vent et roues à eau de Bretonnie
    "fumees": True,            # fumées sur les cheminées de WH1
    "libellules": True,        # libellules près des étangs et des rivières
    "nuages": True,            # nuages de crête sur les montagnes
    # (22 h 40) plus de pont de pierre : partout les ponts de WH1, recalés sur les traversées comme en Athel Loren
    "ponts_ca": False,         # pont de pierre de CA où une route traverse une rivière sans pont de WH1 (Charles, 23.09)
    "plan_ponts": True,        # plan des traversées : ponts de WH1 recalés (et recopiés là où WH1 n'en avait pas)
    "vie": True,               # créatures de WH3 et chevaux blancs d'Equos (`vie_carte_wh3`) ; allumées à la demande de
                               # Charles (23.09.2026, 20 h 50 : « en attendant, allume les créatures et les cascades »)
    "cascades": True,          # cascades de CA aux sources de montagne (`vie_carte_wh3.cascades`), idem
    # nappes d'eau de CA aux cascades de WH1 (`vie_carte_wh3.cascades_wh1`, 24.09.2026 ; vidéo de Charles : la gorge sous la
    # Clairière Royale vide dans WH3, chutes blanches dans WH1 : ses cascades sont des effets de particules, que WH3 ne
    # dessine que de près)
    "cascades_wh1": True,
    # décors de WH3 bien ancrés (`decors_carte_wh3` : cerfs, ours, corbeaux, papillons, épaves, pavillons, champs et
    # clôtures, masures ; Charles, 23.09.2026, 23 h 15 : « attaque tes 10 suggestions… bien ancré dans la map »)
    "decors": True,
    # (24.09.2026, chaîne 12 ; Charles : « de vrais ensembles de champs bretonniens comme sur les cartes de CA ») parcelles de
    # champ, de labour et de cultures en damier autour des villages de Bretonnie (`champs_bretons`) ; elles remplacent les
    # trois rangs de cultures de `decors_carte_wh3` (DECORS["champs"] éteint)
    "champs_bretons": True,
}
FAMILLES_ROCHERS = {"rocks_small": ("rocks_small_01", "rocks_small_02", "rocks_small_03"),
                    "rocks_large": ("rocks_large_01", "rocks_large_02", "rocks_large_03"),
                    "grass_mtn": ("grass_mtn_01", "grass_mtn_02", "grass_mtn_03", "grass_mtn_04")}
IDS_ARBRES_CA = tuple(i for v in FAMILLES_ROCHERS.values() for i in v)
# LE FOND DE LA CARTE 100 % WH1 (23.09.2026, 22 h 40, Charles : « tout ce qui est de base sur la map doit être 100 %
# Warhammer 1… pour les ajouts, je veux bien rajouter du Warhammer 3 si ça rend plus joli, comme les créatures ») : plus
# de rochers de CA dans la liste des arbres ; au pied des montagnes, l'herbe de WH1 (`wh1_grass_*`, octet 12 à 0 comme
# les arbres de WH1) au lieu de l'herbe de montagne de CA ; autour des étangs, plus de roseaux, berges, pierres ni roches
# de CA (le son de lac, un ajout, reste) ; plus de pont de pierre (`ponts_ca`).
ROCHERS_CA = False
HERBE_MONTAGNE_WH1 = ("wh1_grass_1", "wh1_grass_2", "wh1_grass_3", "wh1_grass_4")
ETANGS_MAILLAGES_CA = False


def ident(graine):
    """Identifiant Terry stable, propre à ce calque."""
    return "1" + hashlib.sha1(f"{CARTE}:ajout:{graine}".encode()).hexdigest()[:14]


def _f(v):
    return f"{v:.5f}"


def _transform(position, rotation=(0.0, 0.0, 0.0), echelle=(1.0, 1.0, 1.0)):
    return (f'\t\t\t<ECTransform position="{" ".join(_f(c) for c in position)}" '
            f'rotation="{" ".join(_f(c) for c in rotation)}" scale="{" ".join(_f(c) for c in echelle)}" pivot="0 0 0"/>\n')


def _ech(e):
    return e if isinstance(e, (tuple, list)) else (e, e, e)


VIS_MAILLAGE = ('\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="False" '
                'visible_in_tactical_view_only="False"/>\n')
VIS_EFFET = ('\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="false" '
             'visible_in_tactical_view_only="false"/>\n')


def vfx(graine, nom, position, rotation=(0.0, 0.0, 0.0), echelle=1.0, masque=""):
    """Entité ECVFX, dans l'ordre et avec les réglages des effets des Empires."""
    return (f'\t\t<entity id="{ident(graine)}">\n' + VIS_EFFET +
            f'\t\t\t<ECVFX vfx="{nom}" autoplay="true" scale="1" instance_name=""/>\n'
            f'\t\t\t<ECCampaignProperties visible_in_shroud="False" visible_in_shroud_only="False" culture_mask="{masque}"/>\n'
            + _transform(position, rotation, _ech(echelle)) + '\t\t</entity>\n')


def son(graine, cle, position, masque=""):
    """Entité ECSoundMarker ponctuelle (forme des sons ponctuels des Empires)."""
    return (f'\t\t<entity id="{ident(graine)}">\n'
            f'\t\t\t<ECSoundMarker key="{cle}" />\n'
            + _transform(position) +
            f'\t\t\t<ECCampaignProperties culture_mask="{masque}"/>\n\t\t</entity>\n')


def maillage(graine, modele, position, rotation=(0.0, 0.0, 0.0), echelle=1.0, masque="", decalque=False):
    """Entité d'objet (ECMesh) ou de décalque (ECDecal), réglages des Empires."""
    commun = (VIS_MAILLAGE +
              '\t\t\t<ECPropHeightPatch apply_height_patch="False" for_camera_height_map_only="false"/>\n'
              '\t\t\t<ECCampaignProperties visible_inside_snow_region="True" visible_outside_snow_region="True" '
              'visible_inside_destruction_region="True" visible_outside_destruction_region="True" '
              f'visible_in_shroud="False" visible_in_shroud_only="False" no_culling="False" culture_mask="{masque}"/>\n'
              + _transform(position, rotation, _ech(echelle)))
    if decalque:
        corps = (f'\t\t\t<ECDecal model_path="{modele}" parallax_scale="0" tiling="0" normal_mode="DNM_BLEND" '
                 'apply_to_terrain="True" apply_to_objects="False" render_above_snow="False"/>\n')
    else:
        corps = ('\t\t\t<ECPropMesh/>\n'
                 f'\t\t\t<ECMesh model_path="{modele}" opacity="1"/>\n'
                 '\t\t\t<ECMeshRenderSettings receive_decals="True"/>\n')
    return f'\t\t<entity id="{ident(graine)}">\n{corps}{commun}\t\t</entity>\n'


def scene(graine, chemin, position, rotation=(0.0, 0.0, 0.0), echelle=1.0, masque=""):
    """Entité ECCompositeScene (moulins, roues), ordre des scènes des Empires."""
    return (f'\t\t<entity id="{ident(graine)}">\n'
            f'\t\t\t<ECCompositeScene path="{chemin}" script_id="" autoplay="true"/>\n' + VIS_EFFET
            + _transform(position, rotation, _ech(echelle)) +
            f'\t\t\t<ECCampaignProperties visible_in_shroud="False" visible_in_shroud_only="False" no_culling="False" '
            f'culture_mask="{masque}"/>\n\t\t</entity>\n')


def local_vers_monde(x0, z0, lacet, xl, zl):
    """Décalage local (xl, zl) d'un parent de lacet `lacet` (degrés) -> monde (convention des Empires)."""
    t = math.radians(lacet)
    return x0 + xl * math.cos(t) + zl * math.sin(t), z0 - xl * math.sin(t) + zl * math.cos(t)


class Carte:
    """Lecture des rasters du générateur (ligne 0 au nord) aux points du monde, et masques utiles."""

    def __init__(self, r):
        self.r = r
        self.sol = np.asarray(r["sol_objets"], np.float64)
        self.H, self.L = self.sol.shape
        self.pas = self.L / LARGEUR_MONDE
        gy, gx = np.gradient(np.asarray(r["hauteur"], np.float64))
        self.pente = np.hypot(gx * self.pas, gy * self.pas * R3)
        eau = np.isfinite(r["eau_rivieres"]) | r["mer"] | r["eau_etangs"]
        self.eau = eau
        route2 = np.asarray(r["route"], bool)                     # grille de tile_map (2 px par hex)
        self.route = np.repeat(np.repeat(route2, 4, 0), 4, 1)[:self.H, :self.L]
        self.montagnes = np.asarray(r["montagnes"], bool)

    def px(self, x, z):
        return (int(min(max(round((self.H - 1.5) - z * R3 * self.pas), 0), self.H - 1)),
                int(min(max(round(x * self.pas - 0.5), 0), self.L - 1)))

    def monde(self, i, j):
        return (j + 0.5) / self.pas, ((self.H - 1.5) - i) / self.pas / R3

    def y(self, x, z):
        return float(self.sol[self.px(x, z)])

    def y_bilineaire(self, xs, zs):
        cx = np.clip(np.asarray(xs) * self.pas - 0.5, 0, self.L - 1.001)
        cy = np.clip((self.H - 1.5) - np.asarray(zs) * R3 * self.pas, 0, self.H - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        f = self.sol
        return (f[r0, c0] * (1 - fx) * (1 - fy) + f[r0, c0 + 1] * fx * (1 - fy)
                + f[r0 + 1, c0] * (1 - fx) * fy + f[r0 + 1, c0 + 1] * fx * fy)

    def distance(self, masque, portee_u):
        """Distance approchée (unités) au masque, jusqu'à `portee_u` (dilatations 4-connexes, bornées)."""
        import terrain_wh1_vers_terry as T
        n = int(portee_u * self.pas) + 1
        return T.distance_a(masque, n) / self.pas


def masque_provinces(H, L, provinces):
    """Raster (H x L, ligne 0 au nord) : True dans les provinces données (clés sans préfixe, `donnees_campagne`)."""
    import captage_campagne as CC
    import donnees_campagne as DC
    from terrain_wh1_vers_terry import hex_de_pixel
    reg, _ = CC.calques()
    noms = CC.noms_regions()
    prov = DC.nos_regions()
    dans = np.array([prov.get(n, "").replace("wh_dlc05_", "") in provinces for n in noms] + [False])
    idx = np.where((reg >= 0) & (reg < len(noms)), reg, len(noms))
    col8, lig8 = hex_de_pixel(L, H, 8)
    return dans[idx][lig8, col8]


RX_ENTITE = re.compile(r"<entity\b.*?</entity>", re.S)
RX_POS = re.compile(r'<ECTransform position="([^"]+)" rotation="([^"]+)" scale="([^"]+)"')


def objets_de(blocs, motif):
    """[(modèle, (x, y, z), (rx, ry, rz), (sx, sy, sz), masque)] des blocs dont le modèle contient `motif`."""
    out = []
    for b in blocs:
        m = re.search(r'model_path="([^"]+)"', b)
        if not m or not re.search(motif, m.group(1), re.I):
            continue
        p = RX_POS.search(b)
        c = re.search(r'culture_mask="([^"]*)"', b)
        out.append((m.group(1), tuple(float(v) for v in p.group(1).split()), tuple(float(v) for v in p.group(2).split()),
                    tuple(float(v) for v in p.group(3).split()), c.group(1) if c else ""))
    return out


# ------------------------------------------------------------------ braseros (correction)
FEU = "wh_main_campaign_brazier_fire"
SCINTILLEMENT = "wh3_main_campaign_torch_flicker_light"
SCINTILLEMENT_ECHELLE = 0.5
FEU_AU_DESSUS_DU_PIED = 0.3133            # nos braseros : le feu 0,31 au-dessus du pied (médiane du relevé)
SON_FEU = "Sound_Environment_Fire_Small_Torch"
SON_AU_DESSUS_DU_FEU = 0.047
SCINTILLEMENT_REMPLACE_LUMIERE = True
DISTANCE_LUMIERE = 0.3                         # la lumière d'un brasero est à 1 cm de son feu (relevé) ; pas celles d'à côté
REGLAGE_LUMIERE_BRASERO = 'colour_scale="630000.0"'   # réglage de CA des lumières de brasero (`entites_wh1`)
RX_VFX = re.compile(r'<ECVFX vfx="([^"]+)".*?culture_mask="([^"]*)".*?<ECTransform position="([^"]+)" rotation="([^"]+)"',
                    re.S)


def braseros(ambiance, bilan):
    """(blocs ajoutés, ambiance) : scintillement et son sur chaque feu de brasero ; la lumière fixe voisine retirée."""
    out, feux = [], []
    for region in sorted(ambiance, key=str):
        for bloc in ambiance[region]:
            m = RX_VFX.search(bloc)
            if not m or m.group(1) != FEU:
                continue
            x, y, z = (float(c) for c in m.group(3).split())
            lacet = float(m.group(4).split()[1])
            masque = m.group(2)
            feux.append((x, z))
            graine = f"brasero:{x:.3f}:{y:.3f}:{z:.3f}"
            out.append(vfx(graine + ":scintillement", SCINTILLEMENT, (x, y - FEU_AU_DESSUS_DU_PIED, z), (0.0, lacet, 0.0),
                           SCINTILLEMENT_ECHELLE, masque))
            out.append(son(graine + ":son", SON_FEU, (x, y + SON_AU_DESSUS_DU_FEU, z), masque))
    bilan["braseros : feux avec scintillement et son"] = len(feux)
    if not (SCINTILLEMENT_REMPLACE_LUMIERE and feux):
        return out, ambiance
    F = np.array(feux)
    neuve, retirees = {}, 0
    for region, blocs in ambiance.items():
        garde = []
        for bloc in blocs:
            if "<ECPointLight " in bloc and REGLAGE_LUMIERE_BRASERO in bloc:
                p = RX_POS.search(bloc)
                x, _, z = (float(c) for c in p.group(1).split())
                if np.hypot(F[:, 0] - x, F[:, 1] - z).min() < DISTANCE_LUMIERE:
                    retirees += 1
                    continue
            garde.append(bloc)
        neuve[region] = garde
    bilan["braseros : lumières fixes remplacées par le scintillement"] = retirees
    return out, neuve


# ------------------------------------------------------------------ habillage des étangs
ROSEAU = "RigidModels/campaign/vegetation/shrubs_single/marsh_reeds_01.wsmodel"
BERGES = ("rigidmodels/campaign/generic_props/mudbanks/gen_mudbank_02.rigid_model_v2",
          "rigidmodels/campaign/generic_props/mudbanks/gen_mudbank_06.rigid_model_v2",
          "rigidmodels/campaign/generic_props/mudbanks/gen_mudbank_02.rigid_model_v2",
          "rigidmodels/campaign/generic_props/mudbanks/gen_mudbank_07.rigid_model_v2")
PIERRES = (("rigidmodels/campaign/generic_props/rocks/dragon_stone_parts03.rigid_model_v2", 0.42),
           ("rigidmodels/campaign/generic_props/rocks/dragon_stone_parts04.rigid_model_v2", 0.40),
           ("rigidmodels/campaign/generic_props/rocks/dragon_stone_parts05.rigid_model_v2", 0.23))
ROCHES = ("rigidmodels/campaign/generic_props/gen_rocks/gen_rock_01.rigid_model_v2",
          "rigidmodels/campaign/generic_props/gen_rocks/gen_rock_02.rigid_model_v2",
          "rigidmodels/campaign/generic_props/gen_rocks/gen_rock_03.rigid_model_v2")
SON_LAC = "Sound_Environment_Lake_Moderate"
# (24.09.2026, chaîne 13 ; audit de fluidité, doublons de sons) WH1 posait déjà ce son sur 14 de ses étangs (`ambiance_wh1`,
# `entites_wh1`) : 18 de nos 26 sons de lac tombaient à 0,3 à 1,1 u d'un son de lac de WH1, deux boucles du même son sur
# le même étang. Drapeau allumé : pas de son de lac ajouté là où WH1 en a un (même masque ou visible de tous) à moins de
# DISTANCE_SON_LAC_WH1 du centre de l'étang ; l'image ne change pas.
SANS_DOUBLE_SON_DE_LAC = True
DISTANCE_SON_LAC_WH1 = 1.5
RX_SON = re.compile(r'<ECSoundMarker key="([^"]+)"')


def sons_de(ambiance, cle):
    """[(x, z, masque)] des sons `cle` de l'ambiance de WH1."""
    out = []
    for blocs in (ambiance or {}).values():
        for b in blocs:
            m = RX_SON.search(b)
            if m and m.group(1) == cle:
                p = RX_POS.search(b)
                c = re.search(r'culture_mask="([^"]*)"', b)
                x, _, z = (float(v) for v in p.group(1).split())
                out.append((x, z, c.group(1) if c else ""))
    return out


TOUR_CA = 8.4                                  # tour de l'étang médian de CA (rayon 1,34 u)
PAR_TOUR = {"roseaux": 3, "berges": 4, "pierres": 4, "roches": 3}
RIVE_WH1 = r"reed|marsh|rock|stone"


def habillage_etangs(r, carte, objets, bilan, ambiance=None):
    import etangs_wh1 as ET
    out = []
    lacs_wh1 = sons_de(ambiance, SON_LAC) if SANS_DOUBLE_SON_DE_LAC else []
    g = r.get("grille")
    rives_wh1 = [o[1] for blocs in objets.values() for o in objets_de(blocs, RIVE_WH1)]
    P = np.array([(p[0], p[2]) for p in rives_wh1]) if rives_wh1 else np.zeros((0, 2))
    for et in r.get("etangs", []):
        lac = et["lac"]
        cx, cz = et["centre"]
        rs = et["rayons"]
        niveau = et["niveau"]
        masque = lac["masque"]
        rng = np.random.default_rng(int(hashlib.sha1(repr(lac["cle"]).encode()).hexdigest()[:8], 16))
        tour = float(np.sum(rs) * 2 * math.pi / len(rs))
        k = tour / TOUR_CA
        deja = int((np.hypot(P[:, 0] - cx, P[:, 1] - cz) < rs.max() + 0.6).sum()) if len(P) else 0
        graine = f"etang:{lac['cle']!r}"

        def point(angle, ecart):
            """Point du monde à `ecart` (unités, > 0 dehors) du rivage, dans la direction `angle`."""
            f = angle / (2 * math.pi) * ET.N_POINTS
            k0 = int(math.floor(f)) % ET.N_POINTS
            t = f - math.floor(f)
            rr = rs[k0] * (1 - t) + rs[(k0 + 1) % ET.N_POINTS] * t
            d = max(rr + ecart, 0.05)
            return cx + d * math.cos(angle), cz + d * math.sin(angle)

        def sur_riviere(x, z):
            return bool(np.isfinite(r["eau_rivieres"][carte.px(x, z)]))

        n_vus = {}

        def poser(role, n, ecart, dy, fabrique):
            angles = (rng.uniform(0, 2 * math.pi) + np.arange(n) * 2 * math.pi / max(n, 1)
                      + rng.uniform(-0.3, 0.3, n)) if n else []
            for i, a in enumerate(angles):
                x, z = point(a, ecart if not callable(ecart) else ecart())
                if sur_riviere(x, z):
                    continue
                y = niveau + dy if dy is not None else carte.y(x, z)
                out.append(fabrique(f"{graine}:{role}:{i}", (x, y, z), float(rng.uniform(-180, 180))))
                n_vus[role] = n_vus.get(role, 0) + 1
        reduc = max(0.0, 1.0 - deja / 8.0)          # la rive de WH1 déjà habillée : moins d'ajouts
        n = {role: int(round(v * k * reduc)) for role, v in PAR_TOUR.items()}
        n["roseaux"] = max(n["roseaux"], 2)
        if not ETANGS_MAILLAGES_CA:                 # (22 h 40) le fond de la carte 100 % WH1 : pas de maillage de CA
            n = {role: 0 for role in n}
        poser("roseaux", n["roseaux"], -min(0.29, 0.5 * float(rs.min())), 0.04,
              lambda gr, p, a: maillage(gr, ROSEAU, p, (0.0, a, 0.0), 0.5, masque))
        poser("berges", n["berges"], -0.07, -0.29,
              lambda gr, p, a: maillage(gr, BERGES[int(rng.integers(len(BERGES)))], p, (0.0, a, 0.0), 0.8, masque))

        def pierre(gr, p, a):
            m, e = PIERRES[int(rng.integers(len(PIERRES)))]
            return maillage(gr, m, p, (0.0, a, 0.0), e, masque)
        poser("pierres", n["pierres"], -0.11, -0.14, pierre)
        poser("roches", n["roches"], 0.26, 0.11,
              lambda gr, p, a: maillage(gr, ROCHES[int(rng.integers(len(ROCHES)))], p,
                                        (float(rng.uniform(-15, 15)), a, float(rng.uniform(-15, 15))), 1.0, masque))
        for role, v in n_vus.items():
            bilan[f"étangs : {role}"] = bilan.get(f"étangs : {role}", 0) + v
        if any(math.hypot(x - cx, z - cz) < DISTANCE_SON_LAC_WH1 and m in ("", masque) for x, z, m in lacs_wh1):
            bilan["étangs : sons de lac déjà dans WH1"] = bilan.get("étangs : sons de lac déjà dans WH1", 0) + 1
            continue
        out.append(son(f"{graine}:son", SON_LAC, (cx, niveau + 0.06, cz), masque))
        bilan["étangs : sons de lac"] = bilan.get("étangs : sons de lac", 0) + 1
    return out


# ------------------------------------------------------------------ rochers et herbes de montagne (liste des arbres)
DENSITE_100U2 = {"rocks_small": 3.3, "rocks_large": 1.5, "grass_mtn": 3.0}
OBJETS_PAR_U2_TACHE = 1.8
TACHE_U2 = (1.0, 3.0)
ESPACEMENT = 0.45
PENTE_MAX_ROCHERS = 0.6                        # replats (CA : 90 % sous 0,4 ; notre relief est plus raide)
DISTANCE_PIED = 2.5                            # piémonts : jusqu'à 2,5 u des maillages de montagne
SOUS_MONTAGNE = 0.02                           # = terrain_wh1_vers_terry.SOUS_MONTAGNE (le maillage 2 cm au-dessus)


def arbres(liste, r, carte=None):
    """(octets, bilan) : la liste d'arbres (`arbres_wh1.liste_wh1`) augmentée des rochers et herbes de montagne de CA."""
    from arbres_wh1 import lire_liste
    if not AJOUTS["rochers"]:
        return liste, {}
    carte = carte or Carte(r)
    tete, groupes = lire_liste(liste)
    rng = np.random.default_rng(20260923)
    zone_pied = carte.distance(carte.montagnes, DISTANCE_PIED) <= DISTANCE_PIED
    zone = (carte.montagnes | zone_pied) & (carte.pente < PENTE_MAX_ROCHERS) & ~carte.eau & ~carte.route
    # loin des colonies et de leurs abords (emplacements de ville : couche des emplacements, valeur 0)
    zone &= ~colonies(r, carte, 1.2)
    aire = float(zone.sum()) / (carte.pas * carte.pas * R3)      # u² (pixel = 1/pas x 1/(pas √3/2) en espace des hex)
    # arbres existants (toutes familles) : espacement minimal
    existants = np.concatenate([g[:, :12].copy().view("<f4").reshape(-1, 3)[:, [0, 2]] for _, g in groupes]).astype(np.float64)
    grille = {}
    cellule = ESPACEMENT

    def cle(x, z):
        return int(x // cellule), int(z // cellule)
    for x, z in existants:
        grille.setdefault(cle(x, z), []).append((x, z))

    def libre(x, z):
        i, j = cle(x, z)
        for a in (i - 1, i, i + 1):
            for b in (j - 1, j, j + 1):
                for (u, v) in grille.get((a, b), ()):
                    if (u - x) ** 2 + (v - z) ** 2 < ESPACEMENT ** 2:
                        return False
        return True
    ii, jj = np.nonzero(zone)
    nouveaux = {}
    bilan = {"zone des rochers (u²)": round(aire)}
    herbe_haute = np.percentile(carte.sol[zone], 40) if zone.any() else 0.0
    for fam, dens in DENSITE_100U2.items():
        if fam != "grass_mtn" and not ROCHERS_CA:
            continue                                  # (22 h 40) plus de rochers de CA
        voulu = int(round(dens * aire / 100.0))
        poses = 0
        essais = 0
        while poses < voulu and essais < voulu * 20 and len(ii):
            essais += 1
            k = int(rng.integers(len(ii)))
            x0, z0 = carte.monde(ii[k], jj[k])
            if fam == "grass_mtn" and carte.sol[ii[k], jj[k]] < herbe_haute:
                continue                                  # CA : herbes de montagne en hauteur seulement
            tache = rng.uniform(*TACHE_U2)
            n = max(1, int(round(tache * OBJETS_PAR_U2_TACHE)))
            rayon = math.sqrt(tache / math.pi)
            for _ in range(n * 3):
                if n <= 0:
                    break
                a, d = rng.uniform(0, 2 * math.pi), rayon * math.sqrt(rng.uniform(0, 1))
                x, z = x0 + d * math.cos(a), z0 + d * math.sin(a)
                i, j = carte.px(x, z)
                if not zone[i, j] or not libre(x, z):
                    continue
                y = float(carte.y_bilineaire(x, z)) + (SOUS_MONTAGNE if carte.montagnes[i, j] else 0.0)
                ids = HERBE_MONTAGNE_WH1 if fam == "grass_mtn" and HERBE_MONTAGNE_WH1 else FAMILLES_ROCHERS[fam]
                ident_ = ids[int(rng.integers(len(ids)))]
                rec = np.zeros(15, np.uint8)
                rec[:12] = np.array([x, y, z], "<f4").view(np.uint8)
                # octet 12 : 1 comme BOB et CA, pour les arbres de WH1 aussi (`arbres_wh1.OCTET_12_COMME_BOB`, 24.09.2026)
                rec[12], rec[13], rec[14] = 1, int(rng.integers(6)), 255
                nouveaux.setdefault(ident_, []).append(rec)
                grille.setdefault(cle(x, z), []).append((x, z))
                poses += 1
                n -= 1
        bilan[fam] = poses
    # un identifiant déjà dans la liste (herbe de WH1) : ses nouveaux arbres rejoignent son groupe (jamais deux groupes
    # du même nom)
    noms_existants = {nom for nom, _ in groupes}
    out = bytearray(tete) + struct.pack("<I", len(groupes) + len(set(nouveaux) - noms_existants))
    for nom, recs in groupes:
        if nom in nouveaux:
            recs = np.concatenate([recs, np.stack(nouveaux[nom])])
        out += struct.pack("<H", len(nom)) + nom.encode("ascii") + struct.pack("<I", len(recs)) + recs.tobytes()
    for nom in sorted(set(nouveaux) - noms_existants):
        recs = np.stack(nouveaux[nom])
        out += struct.pack("<H", len(nom)) + nom.encode("ascii") + struct.pack("<I", len(recs)) + recs.tobytes()
    return bytes(out), bilan


def colonies(r, carte, rayon_u):
    """Masque (grille des rasters) des emplacements principaux de ville élargis de `rayon_u`."""
    import terrain_wh1_vers_terry as T
    from caime_layers import read_layer
    slots = np.asarray(read_layer(T.SLOTS)[1]).reshape(T.HEX_H, T.HEX_L)
    col8, lig8 = T.hex_de_pixel(carte.L, carte.H, 8)
    ville = (slots == 0)[lig8, col8]
    return carte.distance(ville, rayon_u) <= rayon_u


# ------------------------------------------------------------------ moulins
MOULIN_SCENE = "composite_scene/campaign_animated_props/gen_props/gen_windmill.csc"
MOULIN_ECHELLE = 0.67
MOULIN_MOYEU = 0.857
MOULIN_ROTATION_XZ = (6.70932, 25.07455)       # rotation des ailes de l'exemple de Grunburg (variété d'animation)
ROUE_SCENE = "composite_scene/campaign_animated_props/gen_props/gen_watermill_wheel.csc"
ROUE_ECHELLE = 0.838
ROUE_AXE_SUR_EAU = 0.135
N_MOULINS, N_ROUES = 8, 5
ECART_MOULINS = 8.0
PROVINCES_MOULINS = {"aquitaine", "bastonne", "bordeleaux", "brionne", "carcassonne", "gisoreux", "montfort", "parravon",
                     "quenelles"}                # la Bretonnie, sans Mousillon (terre maudite)
GABARITS_CA = os.path.join(r"C:\TotalWar-CampaignMap", "05-journal", "2026-09-23-rendu-carte",
                           "gabarits-ca", "gabarits.json")


def _gabarit(nom):
    import json
    return json.load(open(GABARITS_CA, encoding="utf-8"))[nom]


def _pieces(gab):
    """[(xml, décalage local (x, dy, z), lacet relatif, rotation x/z de l'exemple, échelle)] des pièces d'un gabarit."""
    out = []
    for c in gab["composants"][1:]:
        if "decalage_local_exemple" not in c:
            continue
        rot = c.get("rotation_exemple", [0.0, 0.0, 0.0])
        out.append((c["xml"], c["decalage_local_exemple"], c.get("lacet_relatif_exemple", 0.0), (rot[0], rot[2]),
                    c.get("echelle_exemple", [1.0, 1.0, 1.0])))
    return out


def _depuis_gabarit(xml, graine, position, rotation, echelle, masque=""):
    """Bloc <entity> d'un gabarit de CA (jokers {ID} {X}... du relevé), à nos indentations."""
    t = (xml.replace("{ID}", ident(graine))
         .replace("{X} {Y} {Z}", " ".join(_f(c) for c in position))
         .replace("{RX} {RY} {RZ}", " ".join(_f(c) for c in rotation))
         .replace("{SX} {SY} {SZ}", " ".join(_f(c) for c in echelle))
         .replace('culture_mask=""', f'culture_mask="{masque}"'))
    # gabarit : <entity> sans retrait, composants à un retrait ; nos calques : deux et trois
    return "".join("\t\t" + ln + "\n" for ln in t.strip().split("\n"))


def moulins(r, carte, objets, bilan):
    out = []
    bret = masque_provinces(carte.H, carte.L, PROVINCES_MOULINS)
    rng = np.random.default_rng(1519)
    ville = colonies(r, carte, 1.5)
    d_route = carte.distance(carte.route, 4.0)
    champs = [o[1] for blocs in objets.values() for o in objets_de(blocs, r"/farm\.rigid_model_v2")]
    # voisinage libre d'objets de WH1 (0,8 u)
    occupes = np.array([(o[1][0], o[1][2]) for blocs in objets.values() for o in objets_de(blocs, r".")])
    # 1. moulins à vent : près des champs de WH1, sur un replat, à 1,2 à 4 u d'une route, hors des villes
    site = bret & ~carte.eau & ~ville & (carte.pente < 0.3) & (d_route >= 1.2) & (d_route <= 4.0) & ~carte.montagnes
    cands = []
    for (x, y, z) in champs:
        for _ in range(24):
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0.8, 4.0)
            xx, zz = x + d * math.cos(a), z + d * math.sin(a)
            i, j = carte.px(xx, zz)
            if site[i, j]:
                cands.append((xx, zz))
    rng.shuffle(cands)
    places = []
    gab = _gabarit("moulin_a_vent")
    pieces = _pieces(gab)
    for x, z in cands:
        if len(places) >= N_MOULINS:
            break
        if any(math.hypot(x - a, z - b) < ECART_MOULINS for a, b in places):
            continue
        if len(occupes) and np.hypot(occupes[:, 0] - x, occupes[:, 1] - z).min() < 0.8:
            continue
        # le disque de 0,6 u sous le moulin : plat et libre d'eau
        ok = True
        for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
            i, j = carte.px(x + 0.6 * math.cos(a), z + 0.6 * math.sin(a))
            ok &= bool(site[i, j])
        if not ok:
            continue
        places.append((x, z))
        lacet = float(rng.uniform(-180, 180))
        y0 = carte.y(x, z) + MOULIN_MOYEU
        gr = f"moulin:{x:.2f}:{z:.2f}"
        out.append(scene(gr, MOULIN_SCENE, (x, y0, z), (MOULIN_ROTATION_XZ[0], lacet, MOULIN_ROTATION_XZ[1]), MOULIN_ECHELLE))
        for k, (xml, (xl, dy, zl), lacet_rel, (rx, rz), ech) in enumerate(pieces):
            px_, pz_ = local_vers_monde(x, z, lacet, xl, zl)
            py_ = carte.y(px_, pz_) + (dy + MOULIN_MOYEU)
            out.append(_depuis_gabarit(xml, f"{gr}:{k}", (px_, py_, pz_), (rx, lacet + lacet_rel, rz), ech))
    bilan["moulins à vent"] = len(places)
    # 2. roues à eau : au bord d'une rivière de Bretonnie, près d'un village (1,5 à 4 u d'un emplacement de ville)
    import rivieres_wh1
    eau = r["eau_rivieres"]
    riv = np.isfinite(eau) & ~r["mer"] & bret
    pres_ville = carte.distance(colonies(r, carte, 0.0), 4.0)
    # le bord de l'eau (CA : roue à 0,02 à 0,10 u de la surface, son bas 0,16 à 0,35 sous l'eau) : eau touchant la terre
    bord = riv & rivieres_wh1.dilater(~riv & ~carte.eau, 1)
    ii, jj = np.nonzero(bord & (pres_ville >= 1.5) & (pres_ville <= 4.0) & (carte.pente < 0.35))
    ordre = rng.permutation(len(ii))
    gab_r = _gabarit("roue_a_eau")
    pieces_r = _pieces(gab_r)
    roues = []
    for k in ordre:
        if len(roues) >= N_ROUES:
            break
        i, j = ii[k], jj[k]
        x, z = carte.monde(i, j)
        if any(math.hypot(x - a, z - b) < ECART_MOULINS for a, b in roues + places):
            continue
        # direction du courant : le long de l'eau voisine (plus grand axe des pixels d'eau à 6 px)
        fen = riv[max(i - 6, 0):i + 7, max(j - 6, 0):j + 7]
        yy, xx = np.nonzero(fen)
        if len(yy) < 8:
            continue
        pts = np.c_[xx - xx.mean(), -(yy - yy.mean()) / R3]
        _, _, vt = np.linalg.svd(pts, full_matrices=False)
        dx, dz = vt[0]
        angle_courant = math.degrees(math.atan2(dz, dx))
        # l'axe x local de la roue perpendiculaire au courant : axe à l'angle monde courant + 90 = -lacet
        lacet = -(angle_courant + 90.0)
        niveau = float(np.nanmedian(np.where(np.isfinite(eau[max(i - 3, 0):i + 4, max(j - 3, 0):j + 4]),
                                             eau[max(i - 3, 0):i + 4, max(j - 3, 0):j + 4], np.nan)))
        if not np.isfinite(niveau):
            continue
        roues.append((x, z))
        gr = f"roue:{x:.2f}:{z:.2f}"
        y0 = niveau + ROUE_AXE_SUR_EAU
        out.append(scene(gr, ROUE_SCENE, (x, y0, z), (0.0, lacet, 0.0), ROUE_ECHELLE))
        for n_, (xml, (xl, dy, zl), lacet_rel, (rx, rz), ech) in enumerate(pieces_r):
            px_, pz_ = local_vers_monde(x, z, lacet, xl, zl)
            if "ECSoundMarker" in xml:
                out.append(_depuis_gabarit(xml, f"{gr}:{n_}", (px_, y0 + dy, pz_), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))
            else:
                out.append(_depuis_gabarit(xml, f"{gr}:{n_}", (px_, y0 + dy, pz_), (rx, lacet + lacet_rel, rz), ech))
    bilan["roues à eau"] = len(roues)
    return out


# ------------------------------------------------------------------ fumées de cheminée
FUMEE = "wh_main_campaign_chimney_smoke"
FUMEE_ECHELLE = 0.776
FUMEE_AU_DESSUS = 0.05
CHEMINEES_WH1 = r"emipre_wall_chimney"


def fumees(r, carte, objets, ambiance, bilan):
    import props_wh1_vers_layers as PL
    out = []
    boites = PL.Boites()
    fumees_wh1 = []
    for blocs in ambiance.values():
        for b in blocs:
            m = RX_VFX.search(b)
            if m and "smoke" in m.group(1):
                x, _, z = (float(c) for c in m.group(3).split())
                fumees_wh1.append((x, z))
    for blocs in objets.values():
        for modele, (x, y, z), rot, ech, masque in objets_de(blocs, CHEMINEES_WH1):
            bilan["cheminées de WH1"] = bilan.get("cheminées de WH1", 0) + 1
            if any(math.hypot(x - a, z - b) < 0.5 for a, b in fumees_wh1):
                bilan["cheminées de WH1 qui fument déjà"] = bilan.get("cheminées de WH1 qui fument déjà", 0) + 1
                continue
            bo = boites.boite(modele) if hasattr(boites, "boite") else None
            haut = (bo[1][1] if bo is not None else 0.5) * ech[1]
            out.append(vfx(f"fumee:{x:.3f}:{z:.3f}", FUMEE, (x, y + haut + FUMEE_AU_DESSUS, z), (0.0, rot[1], 0.0),
                           FUMEE_ECHELLE, masque))
    bilan["fumées sur les cheminées de WH1"] = len(out)
    return out


# ------------------------------------------------------------------ libellules
LIBELLULES = "wh_main_campaign_enviro_dragonflies"
LIBELLULES_ECHELLE = 0.5
ECART_LIBELLULES = 12.0


def libellules(r, carte, bilan):
    out = []
    rng = np.random.default_rng(77)
    places = []
    # une par étang, sur la rive, à 0,6 à 1,5 u de l'eau
    for et in r.get("etangs", []):
        cx, cz = et["centre"]
        for _ in range(20):
            a = rng.uniform(0, 2 * math.pi)
            d = float(et["rayons"].max()) + rng.uniform(0.6, 1.5)
            x, z = cx + d * math.cos(a), cz + d * math.sin(a)
            i, j = carte.px(x, z)
            if not carte.eau[i, j] and carte.pente[i, j] < 0.5:
                places.append((x, z))
                break
    # le long des rivières des plaines (sous 3 u d'altitude), à 12 u d'écart
    eau = r["eau_rivieres"]
    import rivieres_wh1
    riv = np.isfinite(eau) & ~r["mer"]
    rive = rivieres_wh1.dilater(riv, 8) & ~rivieres_wh1.dilater(riv, 4) & ~carte.eau & (carte.sol < 3.0) & ~carte.montagnes
    ii, jj = np.nonzero(rive)
    for k in rng.permutation(len(ii))[:20000]:
        x, z = carte.monde(ii[k], jj[k])
        if all(math.hypot(x - a, z - b) >= ECART_LIBELLULES for a, b in places):
            places.append((x, z))
    for x, z in places:
        out.append(vfx(f"libellules:{x:.2f}:{z:.2f}", LIBELLULES, (x, carte.y(x, z) + 0.02, z),
                       (0.0, float(rng.uniform(-180, 180)), 0.0), LIBELLULES_ECHELLE))
    bilan["libellules"] = len(out)
    return out


# ------------------------------------------------------------------ nuages de crête
NUAGE = "wh3_main_campaign_enviro_mountain_clouds_thin"
NUAGE_AU_DESSUS = 1.77
NUAGE_LACET = 107.0
ECART_NUAGES = 10.0
N_NUAGES = 40


def nuages(r, carte, bilan):
    out = []
    rng = np.random.default_rng(107)
    haut = carte.montagnes & (carte.pente < 0.45)
    if not haut.any():
        return out
    seuil = np.percentile(carte.sol[carte.montagnes], 60)
    ii, jj = np.nonzero(haut & (carte.sol > seuil))
    places = []
    for k in rng.permutation(len(ii)):
        if len(places) >= N_NUAGES:
            break
        x, z = carte.monde(ii[k], jj[k])
        if all(math.hypot(x - a, z - b) >= ECART_NUAGES for a, b in places):
            places.append((x, z))
    for x, z in places:
        out.append(vfx(f"nuage:{x:.2f}:{z:.2f}", NUAGE, (x, carte.y(x, z) + NUAGE_AU_DESSUS, z), (0.0, NUAGE_LACET, 0.0),
                       float(rng.uniform(0.3, 0.6))))
    bilan["nuages de crête"] = len(out)
    return out


# ------------------------------------------------------------------ pont de pierre de CA
PONT_CA = "rigidmodels/campaign/generic_props/bridges/bridge_stone.rigid_model_v2"
PONT_CA_ECHELLE = 0.15
PONT_CA_ECHELLE_MAX = 0.2                      # CA : 0,1293 à 0,15 ; un peu plus pour une rivière large
PONT_DEMI_LONGUEUR = 0.975                     # têtes du pont : x local ±6,5 x 0,15
PONT_BOUT = 7.0                                # bout du modèle (x local) : 1,05 u à 0,15
PONT_DESSUS = 5.286                            # dessus du modèle (y local)
PONT_SOUS_TETES = 0.307                        # CA : y = relief moyen des têtes - 0,307 (médiane des 87 ponts)
PONT_MARGE_TETE = 0.35                         # les derniers 0,35 u de chaque tête sur la terre
# dallages de CA aux têtes (85 ponts sur 87) : ici dans l'axe de la route, juste après chaque bout (l'exemple de CA,
# décalé de 0,5 u sur le côté, suivait sa route à lui) ; (modèle, dessus du modèle, demi-côté)
PONT_DALLAGES = (("rigidmodels/campaign/generic_props/gen_tiles/gen_tiles_01.rigid_model_v2", 0.111, 0.43),
                 ("rigidmodels/campaign/generic_props/gen_tiles/gen_tiles_05.rigid_model_v2", 0.151, 0.44))
PONT_DALLAGE_APRES_BOUT = 0.3                  # centre du dallage à 0,3 u après le bout du pont
PONT_WH1_PROCHE = 1.5                          # un pont de WH1 à moins de 1,5 u : c'est sa traversée
# les objets de WH1 ne bougent pas (la carte est celle de WH1) : le pont de pierre s'adapte. Un objet de WH1 (hors
# décalque) dans son emprise : pont plus court (0,1293, l'autre échelle de CA) ou décalé le long de la route ; sinon la
# passerelle de WH1 reste. Un dallage qui gênerait un objet n'est pas posé ; un arbre sur un pont est retiré.
PONT_DEMI_LARGEUR = 0.55                       # 3,2 x 0,15 + marge
PONT_ECHELLE_COURTE = 0.1293
PONT_DECALAGES = (0.0, 0.15, -0.15, 0.3, -0.3)


def _objets_wh1_xz(r):
    """(n, 2) : x, z des objets de WH1 hors décalques (gardé dans `r`)."""
    if "_objets_wh1_xz" not in r:
        import props_wh1_vers_layers as PL
        xz = [(o["position"][0], o["position"][2]) for o in PL.objets_uniques() if o["drapeaux"][0] != 1]
        r["_objets_wh1_xz"] = np.array(xz, np.float64).reshape(-1, 2)
    return r["_objets_wh1_xz"]


def _libre(O, x, z, lacet, demi_l, demi_w):
    """Aucun point de O dans le rectangle de centre (x, z), d'axe x local vers l'angle monde -lacet."""
    if not len(O):
        return True
    t = math.radians(lacet)
    dx, dz = O[:, 0] - x, O[:, 1] - z
    a = dx * math.cos(t) - dz * math.sin(t)
    b = dx * math.sin(t) + dz * math.cos(t)
    return not ((np.abs(a) <= demi_l) & (np.abs(b) <= demi_w)).any()


def _composantes(masque):
    """Composantes 8-connexes d'un petit masque : [(lignes, colonnes)]."""
    from collections import deque
    vu = np.zeros_like(masque, bool)
    out = []
    H, L = masque.shape
    for i0, j0 in zip(*np.nonzero(masque)):
        if vu[i0, j0]:
            continue
        q, pts = deque([(i0, j0)]), []
        vu[i0, j0] = True
        while q:
            i, j = q.popleft()
            pts.append((i, j))
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    a, b = i + di, j + dj
                    if 0 <= a < H and 0 <= b < L and masque[a, b] and not vu[a, b]:
                        vu[a, b] = True
                        q.append((a, b))
        p = np.array(pts)
        out.append((p[:, 0], p[:, 1]))
    return out


def plan_ponts(r, carte=None):
    """Les traversées route / rivière de la carte, calculées une fois (gardées dans `r`) : [dict(x, z, angle, lacet,
    pose_wh1, athel_loren, genre, ...)]. `genre` : « wh1 » en Athel Loren (le pont de WH1, ou son lot recopié là où WH1
    n'avait pas de croisement), « pierre » ailleurs (pont de pierre de CA, drapeau `ponts_ca`)."""
    if "plan_ponts" in r:
        return r["plan_ponts"]
    import ponts_wh1
    import rivieres_wh1
    carte = carte or Carte(r)
    # l'eau visible (le ruban glisse sous les berges : ses pixels sous le sol ne comptent pas)
    riv = (np.nan_to_num(r["eau_rivieres"], nan=-1e9) > np.asarray(r["hauteur"])) & ~r["mer"]
    wh1 = [(o["pose"], o["x"], o["z"]) for o in ponts_wh1.objets_ponts() if o["role"] == "passerelle"]
    athel_loren = masque_provinces(carte.H, carte.L, set(ponts_wh1.ATHEL_LOREN))
    contact = carte.route & rivieres_wh1.dilater(riv, 2)
    plan, bilan = [], {}

    def eau_en(x, z):
        return bool(riv[carte.px(x, z)])

    def route_en(x, z):
        return bool(carte.route[carte.px(x, z)])
    def sans_traversee(raison):
        bilan[f"contacts sans traversée ({raison})"] = bilan.get(f"contacts sans traversée ({raison})", 0) + 1

    def pixels(masque, x, z, rayon):
        """Coordonnées du monde des pixels du masque à moins de `rayon` u de (x, z)."""
        i0, j0 = carte.px(x, z)
        n = int(rayon * carte.pas) + 1
        i1, j1 = max(i0 - n, 0), max(j0 - n, 0)
        yy, xx = np.nonzero(masque[i1:i0 + n + 1, j1:j0 + n + 1])
        p = np.c_[(xx + j1 + 0.5) / carte.pas, ((carte.H - 1.5) - (yy + i1)) / carte.pas / R3]
        return p[np.hypot(p[:, 0] - x, p[:, 1] - z) <= rayon]
    for ii, jj in _composantes(contact):
        x, z = carte.monde(float(ii.mean()), float(jj.mean()))
        # 1. axe grossier : plus grand axe des pixels de route à moins de 1,5 u (repère du monde)
        pts = pixels(carte.route, x, z, 1.5)
        if len(pts) < 10:
            sans_traversee("peu de route")
            continue
        _, _, vt = np.linalg.svd(pts - pts.mean(0), full_matrices=False)
        dx, dz = vt[0]
        # 2. axe fin : de la route d'une rive à la route de l'autre (centres des pixels de route à 0,5-1,8 u de chaque
        # côté, à moins d'1 u de l'axe grossier) : le pont relie les deux bouts de route
        pts = pixels(carte.route, x, z, 1.8)
        s_ = (pts[:, 0] - x) * dx + (pts[:, 1] - z) * dz
        c_ = -(pts[:, 0] - x) * dz + (pts[:, 1] - z) * dx
        a_, b_ = pts[(s_ < -0.5) & (np.abs(c_) < 1.0)], pts[(s_ > 0.5) & (np.abs(c_) < 1.0)]
        if len(a_) < 5 or len(b_) < 5:
            sans_traversee("route d'un seul côté")
            continue
        ca, cb = a_.mean(0), b_.mean(0)
        d = float(np.hypot(*(cb - ca)))
        dx, dz = (cb - ca) / d
        s = np.arange(0.0, d + 1e-6, 0.03)
        w = np.array([eau_en(ca[0] + t * dx, ca[1] + t * dz) for t in s])
        if not w.any():
            sans_traversee("pas d'eau entre les deux bouts de route")
            continue
        # la plage d'eau la plus proche du milieu des deux bouts ; le pont se centre sur elle
        idx = np.nonzero(w)[0]
        k0 = idx[np.argmin(np.abs(s[idx] - d / 2))]
        k1 = k0
        while k0 > 0 and w[k0 - 1]:
            k0 -= 1
        while k1 < len(s) - 1 and w[k1 + 1]:
            k1 += 1
        milieu, largeur = (s[k0] + s[k1]) / 2, s[k1] - s[k0]
        x, z = ca[0] + milieu * dx, ca[1] + milieu * dz
        # 3. la rivière coupe la route (plus de 45°) : une route qui longe la rive n'est pas une traversée
        eau_p = pixels(riv, x, z, 0.8)
        if len(eau_p) >= 8:
            _, _, vr = np.linalg.svd(eau_p - eau_p.mean(0), full_matrices=False)
            if abs(vr[0][0] * dx + vr[0][1] * dz) > math.cos(math.radians(45)):
                sans_traversee("route le long de la rivière")
                continue
        proche = min(wh1, key=lambda p: math.hypot(p[1] - x, p[2] - z)) if wh1 else None
        pose = proche[0] if proche and math.hypot(proche[1] - x, proche[2] - z) < PONT_WH1_PROCHE else None
        if any((pose is not None and p["pose_wh1"] == pose) or math.hypot(p["x"] - x, p["z"] - z) < PONT_WH1_PROCHE
               for p in plan):
            bilan["contacts d'une même traversée"] = bilan.get("contacts d'une même traversée", 0) + 1
            continue
        al = bool(athel_loren[carte.px(x, z)])
        genre = "wh1" if al or not AJOUTS["ponts_ca"] else "pierre"
        echelle = PONT_CA_ECHELLE
        lacet = -math.degrees(math.atan2(dz, dx))
        if genre == "pierre":
            # l'eau tient sous le pont et ses têtes reposent sur la terre (PONT_MARGE_TETE) ; sinon un pont un peu plus
            # grand, jusqu'à PONT_CA_ECHELLE_MAX ; au-delà, la passerelle de WH1 reste
            echelle = PONT_CA_ECHELLE * max(1.0, (largeur / 2 + PONT_MARGE_TETE) / PONT_DEMI_LONGUEUR)
            if echelle > PONT_CA_ECHELLE_MAX:
                genre, echelle = "wh1", PONT_CA_ECHELLE
                bilan["rivière trop large pour le pont de pierre"] = bilan.get("rivière trop large pour le pont de pierre",
                                                                               0) + 1
        if genre == "pierre":
            # les objets de WH1 dans l'emprise : pont plus court ou décalé le long de la route, sinon la passerelle reste
            O = _objets_wh1_xz(r)
            choix = None
            for e_ in (echelle, PONT_ECHELLE_COURTE):
                for dec in PONT_DECALAGES:
                    if largeur / 2 + abs(dec) + PONT_MARGE_TETE > PONT_DEMI_LONGUEUR * e_ / PONT_CA_ECHELLE:
                        continue
                    if _libre(O, x + dec * dx, z + dec * dz, lacet, PONT_BOUT * e_ + 0.1, PONT_DEMI_LARGEUR):
                        choix = (e_, dec)
                        break
                if choix:
                    break
            if choix is None:
                genre = "wh1"
                bilan["pont de pierre gêné par un objet de WH1 (passerelle gardée)"] = \
                    bilan.get("pont de pierre gêné par un objet de WH1 (passerelle gardée)", 0) + 1
            else:
                if choix != (echelle, 0.0):
                    bilan["ponts de pierre décalés ou raccourcis (objet de WH1)"] = \
                        bilan.get("ponts de pierre décalés ou raccourcis (objet de WH1)", 0) + 1
                echelle, dec = choix
                x, z = x + dec * dx, z + dec * dz
        plan.append(dict(x=x, z=z, angle=math.degrees(math.atan2(dz, dx)), lacet=-math.degrees(math.atan2(dz, dx)),
                         largeur=float(largeur), echelle=float(echelle), pose_wh1=pose, athel_loren=al, genre=genre))
    poses_vues = {p["pose_wh1"] for p in plan}
    bilan["ponts de WH1 sans traversée repérée (gardés)"] = sum(1 for k, _, _ in wh1 if k not in poses_vues)
    bilan["traversées"] = {f"{g} ({'Athel Loren' if a else 'hors Athel Loren'}, {'pont de WH1' if k else 'sans pont de WH1'})":
                           sum(1 for p in plan if p["genre"] == g and p["athel_loren"] == a and (p["pose_wh1"] is not None) == k)
                           for g in ("wh1", "pierre") for a in (True, False) for k in (True, False)}
    bilan["traversées"] = {k: v for k, v in bilan["traversées"].items() if v}
    r["plan_ponts"], r["bilan_plan_ponts"] = plan, bilan
    return plan


def ponts_ca(r, carte, bilan):
    """Pont de pierre de CA sur chaque traversée « pierre » du plan (hors d'Athel Loren)."""
    out = []
    plan = plan_ponts(r, carte)
    bilan.update({f"plan des ponts : {k}": v for k, v in r.get("bilan_plan_ponts", {}).items()})
    for p in plan:
        if p["genre"] != "pierre":
            continue
        x, z, lacet, e = p["x"], p["z"], p["lacet"], p["echelle"]
        k_e = e / PONT_CA_ECHELLE
        dx, dz = math.cos(math.radians(p["angle"])), math.sin(math.radians(p["angle"]))
        demi = PONT_DEMI_LONGUEUR * k_e
        tetes = carte.y_bilineaire([x - demi * dx, x + demi * dx], [z - demi * dz, z + demi * dz])
        y = float(np.mean(tetes)) - PONT_SOUS_TETES * k_e
        niveau = np.nanmax([r["eau_rivieres"][carte.px(x + t * dx, z + t * dz)] for t in np.linspace(-0.5, 0.5, 11)])
        gr = f"pont_ca:{x:.2f}:{z:.2f}"
        out.append(maillage(gr, PONT_CA, (x, y, z), (0.0, lacet, 0.0), e))
        for k, (modele, dessus, cote) in enumerate(PONT_DALLAGES):
            signe = -1 if k == 0 else 1
            xl = signe * (PONT_BOUT * e + PONT_DALLAGE_APRES_BOUT)
            px_, pz_ = local_vers_monde(x, z, lacet, xl, 0.0)
            if not _libre(_objets_wh1_xz(r), px_, pz_, lacet, cote + 0.05, cote + 0.05):
                bilan["dallages non posés (objet de WH1)"] = bilan.get("dallages non posés (objet de WH1)", 0) + 1
                continue
            # le dessus du dallage au ras du sol (1 cm) au point le plus bas sous lui : jamais en l'air sur une pente
            coins = [local_vers_monde(x, z, lacet, xl + a * cote, b * cote) for a in (-1, 0, 1) for b in (-1, 0, 1)]
            bas = float(np.min(carte.y_bilineaire([c[0] for c in coins], [c[1] for c in coins])))
            out.append(maillage(f"{gr}:dallage:{k}", modele, (px_, bas - dessus + 0.01, pz_), (0.0, lacet, 0.0), 1.0))
        bilan.setdefault("ponts de CA", []).append({"x": round(x, 2), "z": round(z, 2), "lacet": round(lacet, 1),
                                                    "échelle": round(e, 4), "eau (largeur)": round(p["largeur"], 2),
                                                    "y": round(y, 3), "niveau": round(float(niveau), 3),
                                                    "dessus - eau": round(y + PONT_DESSUS * e - float(niveau), 3),
                                                    "têtes - eau": [round(float(t) - float(niveau), 3) for t in tetes]})
    return out


# emprises (demi-longueur, demi-largeur) en unités du modèle : pont de pierre (boîte x ±7, z -2,9..3,5), passerelle
# (x -1,25..1,33, garde-corps compris) ; dallage en unités du monde
EMPRISES_PONTS = {"bridge_stone": (PONT_BOUT + 0.7, 3.7), "gen_tiles": (0.47, 0.47), "jetty": (1.4, 0.8)}


def degager_arbres(liste, blocs):
    """(octets, n) : la liste d'arbres sans les arbres posés sur un pont (pierre, dallage ou passerelle) des `blocs`.
    Emprises en unités du modèle (x, z locaux) multipliées par l'échelle de l'entité (un dallage : unités du monde)."""
    from arbres_wh1 import lire_liste
    rects = []
    for b in blocs:
        m = re.search(r'model_path="([^"]+)"', b)
        t = RX_POS.search(b)
        if not (m and t):
            continue
        for motif, (dl, dw) in EMPRISES_PONTS.items():
            if motif in m.group(1):
                x, _, z = (float(v) for v in t.group(1).split())
                sx, _, sz = (float(v) for v in t.group(3).split())
                if motif == "gen_tiles":
                    sx = sz = 1.0
                rects.append((x, z, float(t.group(2).split()[1]), dl * sx, dw * sz))
    if not rects:
        return liste, 0
    tete, groupes = lire_liste(liste)
    R = np.array(rects)
    out = bytearray(tete) + struct.pack("<I", len(groupes))
    retires = 0
    for nom, recs in groupes:
        xyz = recs[:, :12].copy().view("<f4").reshape(-1, 3).astype(np.float64)
        garde = np.ones(len(recs), bool)
        for x, z, lacet, dl, dw in R:
            proche = np.abs(xyz[:, 0] - x) + np.abs(xyz[:, 2] - z) < dl + dw + 0.1
            if not proche.any():
                continue
            t = math.radians(lacet)
            dx, dz = xyz[:, 0] - x, xyz[:, 2] - z
            dedans = proche & (np.abs(dx * math.cos(t) - dz * math.sin(t)) <= dl) & \
                (np.abs(dx * math.sin(t) + dz * math.cos(t)) <= dw)
            garde &= ~dedans
        retires += int((~garde).sum())
        recs = recs[garde]
        out += struct.pack("<H", len(nom)) + nom.encode("ascii") + struct.pack("<I", len(recs)) + recs.tobytes()
    return bytes(out), retires


def entites(r, ambiance, objets):
    """([blocs XML] du calque `ajouts_wh3`, ambiance (lumières fixes des braseros retirées), bilan)."""
    bilan = {}
    out = []
    carte = Carte(r)
    if AJOUTS["braseros"]:
        blocs, ambiance = braseros(ambiance, bilan)
        out += blocs
    if AJOUTS["etangs"]:
        out += habillage_etangs(r, carte, objets, bilan, ambiance)
    if AJOUTS["moulins"]:
        out += moulins(r, carte, objets, bilan)
    if AJOUTS["fumees"]:
        out += fumees(r, carte, objets, ambiance, bilan)
    if AJOUTS["libellules"]:
        out += libellules(r, carte, bilan)
    if AJOUTS["nuages"]:
        out += nuages(r, carte, bilan)
    if AJOUTS["ponts_ca"]:
        out += ponts_ca(r, carte, bilan)
    # créatures de WH3 et cascades de CA aux sources de montagne (accord de Charles, 23.09.2026, 18 h 50 ; chevaux blancs
    # d'Equos, 20 h 15) : `vie_carte_wh3` ; éteint tant que la construction mesure le plantage de rendu (effets de
    # particules suspects)
    if AJOUTS.get("vie") or AJOUTS.get("cascades") or AJOUTS.get("cascades_wh1"):
        import vie_carte_wh3
        if AJOUTS.get("vie"):
            blocs, ambiance, bilan_vie = vie_carte_wh3.creatures(r, carte, ambiance)
            out += blocs
            bilan["vie de WH3"] = bilan_vie
        if AJOUTS.get("cascades"):
            blocs, bilan_c = vie_carte_wh3.cascades(r, carte, ambiance, objets)
            out += blocs
            bilan["cascades de CA"] = bilan_c
        if AJOUTS.get("cascades_wh1"):
            blocs, bilan_w = vie_carte_wh3.cascades_wh1(r, carte, ambiance, objets)
            out += blocs
            bilan["nappes de CA aux cascades de WH1"] = bilan_w
    if AJOUTS.get("decors"):
        import decors_carte_wh3
        blocs, bilan_d = decors_carte_wh3.entites(r, carte, objets, ambiance)
        out += blocs
        bilan["décors de WH3"] = bilan_d
    if AJOUTS.get("champs_bretons"):
        import champs_bretons
        blocs, bilan_c = champs_bretons.entites(r, carte, objets, ambiance)
        out += blocs
        bilan["ensembles de champs de Bretonnie"] = bilan_c
    return out, ambiance, bilan


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("ajouts :", AJOUTS)
    print("identifiants d'arbres de CA ajoutés à la liste :", IDS_ARBRES_CA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
