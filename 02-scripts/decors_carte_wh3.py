#!/usr/bin/env python3
"""
decors_carte_wh3.py - ajouts de WH3 qui rendent la carte plus vivante, bien ancrés dans le terrain (session du rendu).

Accord de Charles (23.09.2026, 23 h 15 : « attaque tes 10 suggestions ; il faut que tout soit bien ancré dans la map, un truc
très joli » ; 22 h 40 : « pour les ajouts, je veux bien rajouter du WH3 si ça rend plus joli, mais tout ce qui est de base
doit être 100 % WH1 »). Ressources vérifiées dans les packs de WH3 et réglages relevés chez CA (rapport
`05-journal\\2026-09-23-rendu-carte\\gabarits-ca\\rapport-vie-ambiante-wh3.md`, brouillon `poses_ca_objets.py`) :
- cerfs (`st1/deer_idle_0N.csc`, échelle des loups de CA 0,57) dans les clairières d'Athel Loren et des bois de Bretonnie ;
- ours (`be01_kislev_bear_beige_idle_01.csc`, échelle de CA 0,36) au fond d'Athel Loren ;
- corbeaux en cercle (`cam_fauna_bird_medium_1.csc`, 0,25) au-dessus des châteaux de Mousillon ;
- papillons (`wh2_main_campaign_butterfly_swarm`, 0,5, +0,13 comme CA) dans les prés et les clairières ;
- épave de galion bretonnien (`brt_galleon_wreck`, modèle de campagne de 3,5 u de long, posé à 0,3) échouée sur le fond au
  large de Mousillon et de Bordeleaux, inclinée ;
- pavillons de chevaliers (`bret_tent_1..3`, modèles de campagne de 0,55 à 0,8 u, posés à 0,42) en arc face à Parravon, au
  château de Carcassonne et au château de Bastonne ;
- champs (`farm_crop_01/02.wsmodel`, échelle de CA 0,38, rangs à 0,33 u comme ses 165 poses) et leurs clôtures
  (`gen_fence_01..05`, échelle 1, pas de 0,5 u) autour de villages bretons ;
- masures de paysans (`vampire_peasant_house_1/2`, modèles des Comtes Vampires, à 0,5) en hameaux autour de Mousillon.
Les esprits des colonies elfes (tournoyants et au sol) sont déjà dans les prefabs de colonie elfe de CA : pas de doublon.

Ancrage : hauteur du sol (bilinéaire) sous chaque pièce ; terrain plat (pente et écart de hauteur sous l'emprise bornés),
hors de l'eau, des routes, des emplacements de ville et de la forêt de WH1 pour les constructions ; à distance des objets
de WH1 (grille de proximité). Choix déterministes (graines).

Usage (module) : blocs, bilan = decors_carte_wh3.entites(r, carte, objets, ambiance)
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ajouts_carte_wh3 import RX_POS, maillage, masque_provinces, scene, vfx  # noqa: E402
from ajouts_carte_wh3 import colonies as zones_villes  # noqa: E402
from vie_carte_wh3 import BRETONNIE, _choisir, _foret, _hash01  # noqa: E402

# (24.09.2026, chaîne 12) "champs" éteint : les ensembles de champs de `champs_bretons` les remplacent
# "pre_de_ceren" : validé par Charles (24.09.2026, 20 h 05, sur les vues de contrôle, « si tu es satisfait »)
DECORS = {"cerfs": True, "ours": True, "corbeaux": True, "papillons": True, "epaves": True, "pavillons": True,
          "champs": False, "masures": True, "pre_de_ceren": True}
# LE PRÉ DE CEREN (24.09.2026, chaîne 12 ; feu vert de Charles relayé par la session de l'extension, décor pur, aucune
# table) : en Aquitanie, la tour de marbre du Duc sur la colline qui domine le Pré, et sur le pré la chapelle du Graal de
# Galand, figurée par la statue de la Dame du Lac. Les sources ne situent ni la colline ni le pré : zone du Pré de la session
# IA (ellipse centrée en hex (110 ; 226), rayons 10 x 7 hex, soit (73,48 ; 174,32), 6,7 x 5,4 u) ; tour sur le sommet le plus
# proche qui domine le pré (+0,92 u, à 7,8 u du centre) : CHOIX DE PLACEMENT ; statue sur le point plat du pré le plus proche
# du centre (brouillon `pre_de_ceren.py`, vues `pre_de_ceren_dessus.png` et `_profil.png`). Échelles de CA pour ces modèles
# posés en décor aux Empires (tour fine 0,607 ; statue 0,6 à 1,0).
PRE_DE_CEREN = [("rigidmodels/campaign/settlements/bretonnia/bretonnia_tower_thin.rigid_model_v2", (79.33, 169.22), 0.607,
                 0.0, "tour de marbre du Duc (choix de placement)"),
                ("rigidmodels/campaign/settlements/bretonnia/brt_lotl_statue.rigid_model_v2", (71.05, 173.17), 0.6,
                 115.0, "chapelle du Graal de Galand (Dame du Lac)")]
# (25.09.2026, chaîne 14 ; vue dans Terry à 00 h 21 : la tour a le pied pris dans les sapins de WH1) aucun arbre de WH1 à
# moins de PRE_DE_CEREN_DEGAGE u de chaque décor (`sans_arbres`, lu par le générateur avec l'eau des étangs)
PRE_DE_CEREN_DEGAGE = (0.9, 0.6)


def sans_arbres(H, L, pas):
    """Raster (ligne 0 au nord) : True autour des décors du Pré de Ceren (pas d'arbre de WH1), False ailleurs."""
    import numpy as np
    out = np.zeros((H, L), bool)
    if not DECORS.get("pre_de_ceren"):
        return out
    r3 = 3 ** 0.5 / 2
    for (_, (x, z), _, _, _), rayon in zip(PRE_DE_CEREN, PRE_DE_CEREN_DEGAGE):
        ci, cj = (H - 1.5) - z * r3 * pas, x * pas - 0.5
        n = int(rayon * pas) + 2
        i0, i1, j0, j1 = max(int(ci) - n, 0), min(int(ci) + n + 1, H), max(int(cj) - n, 0), min(int(cj) + n + 1, L)
        ii, jj = np.mgrid[i0:i1, j0:j1]
        out[i0:i1, j0:j1] |= np.hypot((ii - ci) / (r3 * pas), (jj - cj) / pas) <= rayon
    return out


# (reprise, 20 h 08) statue déplacée de (72,00 ; 177,78), au milieu de 29 décors de dévastation du Chaos (crevasses, lave),
# vers un point du pré à 1,3 u du premier décor, peu boisé (24 %), tournée vers la tour (brouillon `pre_de_ceren_site.py`)
# positions exactes des colonies (map_data.esf, REGION_KEYS ; construction, 23.09.2026, 23 h 05 : identiques à WH1 au
# millième pour les 54 de l'intérieur ; `positions_colonies.json` oubliait le décalage des colonnes impaires)
POSITIONS = os.path.join(r"C:\TotalWar-CampaignMap", "04-projets", "saison-des-revelations",
                         "relief-wh1", "colonies_map_data.json")

CERF = "composite_scene/campaign_fauna/st1/deer_idle_0{}.csc"
# (24.09.2026, Charles, vidéo V2 : « la forêt manque d'animaux ; WH1 en avait peu, mais ajoutes-en par-ci par-là, d'espèces
# qui existent dans WH3 et cohérentes avec Athel Loren ») : plus de cerfs en Athel Loren (6 -> 14, écart 12 -> 8 u), un ours
# de plus, et des vols d'oiseaux au-dessus de la canopée d'Athel Loren (OISEAUX_AL)
# (24.09.2026, chaîne 11 ; vidéo V2, 127 s : le cerf « aussi haut que les arbres ») CA ne pose pas de cerf aux Empires :
# l'échelle de ses loups (0,57) était trop grande pour cette scène ; celle de ses chevaux et de ses ours (0,36 à 0,39)
N_CERFS_AL, N_CERFS_BRT, ECART_CERFS, CERF_ECHELLE = 14, 3, 8.0, 0.38
OURS = "composite_scene/campaign_fauna/bear01/be01_kislev_bear_beige_idle_01.csc"
N_OURS, ECART_OURS, OURS_ECHELLE = 3, 25.0, 0.36
N_OISEAUX_AL, ECART_OISEAUX_AL, OISEAUX_AL_HAUT, OISEAUX_AL_ECHELLE = 6, 18.0, 4.0, 0.2
CORBEAUX = "composite_scene/campaign_fauna/birds/cam_fauna_bird_01/cam_fauna_bird_medium_1.csc"
CORBEAUX_COLONIES = ("wh_dlc05_mousillon_mousillon", "wh_dlc05_mousillon_castle_rachard", "wh_dlc05_mousillon_yremy")
CORBEAUX_ECHELLE, CORBEAUX_HAUT, CORBEAUX_ECART_WH1 = 0.25, 9.0, 6.0
PAPILLONS = "wh2_main_campaign_butterfly_swarm"
N_PAPILLONS, ECART_PAPILLONS, PAPILLONS_ECHELLE, PAPILLONS_HAUT, PAPILLONS_PAIRE = 3, 25.0, 0.5, 0.13, 2.5
EPAVE = "rigidmodels/campaign/generic_props/ship_props/brt_galleon_wreck.rigid_model_v2"
EPAVES_COLONIES = ("wh_dlc05_mousillon_mousillon", "wh_dlc05_bordeleaux_bordeleaux")
EPAVE_ECHELLE, EPAVE_PROF, EPAVE_TERRE = 0.3, (0.2, 0.6), (0.4, 1.6)       # profondeur, distance à la terre (u)
EPAVE_ANNEAU = (2.5, 8.0)                                                   # u autour de la colonie
PAVILLON = "rigidmodels/campaign/encampments/bretonnia/bret_tent_{}.rigid_model_v2"
PAVILLONS_CHATEAUX = ("wh_dlc05_parravon_parravon", "wh_dlc05_carcassonne_castle_carcassonne",
                      "wh_dlc05_bastonne_castle_bastonne")
# pavillons (modèle carré de 0,85 u, entrée supposée sur +z) : 4 en arc léger, les bouts vers le château (z local vers lui)
PAVILLON_ECHELLE, PAVILLONS_ARC = 0.42, ((-0.75, 0.12), (-0.25, 0.0), (0.25, 0.0), (0.75, 0.12))
CHAMP = "rigidmodels/campaign/vegetation/shrubs/farm_crop_0{}.wsmodel"
CLOTURE = "rigidmodels/campaign/generic_props/fences_spikes/gen_fence_0{}.rigid_model_v2"
CHAMPS_VILLAGES = ("wh_dlc05_aquitaine_gien", "wh_dlc05_aquitaine_derrevin_libre", "wh_dlc05_quenelles_brusse",
                   "wh_dlc05_quenelles_laguiller", "wh_dlc05_brionne_muret", "wh_dlc05_carcassonne_st_jacques",
                   "wh_dlc05_montfort_poussenc", "wh_dlc05_bastonne_soude")
CHAMP_ECHELLE, CHAMP_RANG, CHAMP_DY = 0.38, 0.33, 0.03
CLOTURE_PAS, CLOTURE_RECUL = 0.5, 0.55
MASURE = "rigidmodels/campaign/settlements/vampire_counts/vampire_peasant_house_{}.rigid_model_v2"
MASURES_COLONIES = ("wh_dlc05_mousillon_mousillon", "wh_dlc05_mousillon_martel", "wh_dlc05_mousillon_castle_rachard",
                    "wh_dlc05_mousillon_yremy")
MASURE_ECHELLE, MASURES_HAMEAU = 0.5, ((-0.22, 0.0), (0.22, 0.12), (0.0, -0.3))
ANNEAU_COLONIE = (1.7, 3.2)            # u : autour d'une colonie, hors de son emplacement (disque de 1,4 u)
PENTE_MAX, ECART_SOL_MAX = 0.25, 0.06  # sous une construction
DEGAGE_OBJETS = 0.35                   # u : aucun objet de WH1 plus près


def positions_colonies():
    """{clé de région : (x, z)} des colonies (map_data.esf) ; {} si le fichier manque."""
    if not os.path.exists(POSITIONS):
        return {}
    return {k: (float(v[0]), float(v[1])) for k, v in json.load(open(POSITIONS, encoding="utf-8"))["keys"].items()}


class Voisins:
    """Grille de proximité de points (x, z)."""

    def __init__(self, pts=(), cellule=0.5):
        self.c, self.g = cellule, {}
        for x, z in pts:
            self.ajouter(x, z)

    def ajouter(self, x, z):
        self.g.setdefault((int(x // self.c), int(z // self.c)), []).append((x, z))

    def libre(self, x, z, r):
        n = int(math.ceil(r / self.c))
        i0, j0 = int(x // self.c), int(z // self.c)
        for a in range(i0 - n, i0 + n + 1):
            for b in range(j0 - n, j0 + n + 1):
                for u, v in self.g.get((a, b), ()):
                    if (u - x) ** 2 + (v - z) ** 2 < r * r:
                        return False
        return True


def _positions_objets(objets, ambiance):
    pts = []
    for blocs in list((objets or {}).values()) + list((ambiance or {}).values()):
        for b in blocs:
            p = RX_POS.search(b)
            if p:
                x, _, z = (float(v) for v in p.group(1).split())
                pts.append((x, z))
    return pts


def _terrain_ok(carte, masques, pts, dy_max=ECART_SOL_MAX, pente_max=PENTE_MAX):
    """Tous les points (x, z) sur un terrain constructible : pas d'eau, de route, de ville, de forêt ; plat."""
    ys = []
    for x, z in pts:
        i, j = carte.px(x, z)
        if masques["interdit"][i, j] or carte.pente[i, j] > pente_max:
            return False
        ys.append(float(carte.y_bilineaire(x, z)))
    return max(ys) - min(ys) <= dy_max


def _site(carte, masques, voisins, centre, motif, graine, anneau=ANNEAU_COLONIE, face=True):
    """Premier site (angle, rayon) autour de `centre` où toutes les pièces de `motif` (décalages locaux (x, z), l'axe z
    pointant vers la colonie si `face`) tiennent sur un terrain constructible, loin des objets de WH1 ; rend
    [(x, z, lacet)] ou []."""
    cx, cz = centre
    depart = _hash01(graine) * 360.0
    for dr in np.arange(anneau[0], anneau[1] + 1e-6, 0.2):
        for da in range(0, 360, 12):
            a = math.radians(depart + da)
            x0, z0 = cx + dr * math.cos(a), cz + dr * math.sin(a)
            vers = math.atan2(cz - z0, cx - x0) if face else a
            lacet = 90.0 - math.degrees(vers)               # l'axe z local vers la colonie (convention des Empires)
            t = math.radians(lacet)
            pts = [(x0 + xl * math.cos(t) + zl * math.sin(t), z0 - xl * math.sin(t) + zl * math.cos(t)) for xl, zl in motif]
            if not _terrain_ok(carte, masques, pts):
                continue
            if not all(voisins.libre(x, z, DEGAGE_OBJETS) for x, z in pts):
                continue
            return [(x, z, lacet) for x, z in pts]
    return []


def entites(r, carte, objets=None, ambiance=None):
    """(blocs XML du calque des ajouts, bilan) des décors de DECORS."""
    blocs, bilan = [], {}
    H, L = carte.H, carte.L
    col = positions_colonies()
    import ponts_wh1
    al = masque_provinces(H, L, set(ponts_wh1.ATHEL_LOREN))
    bretonnie = masque_provinces(H, L, set(BRETONNIE))
    foret, densite = _foret(r, carte)
    villes = zones_villes(r, carte, 1.4)
    montagnes = np.asarray(r["montagnes"], bool)
    sec = ~carte.eau & ~carte.route & ~villes
    masques = {"interdit": carte.eau | carte.route | villes | foret | montagnes}
    voisins = Voisins(_positions_objets(objets, ambiance))

    def y(x, z, dy=0.0):
        return float(carte.y_bilineaire(x, z)) + dy

    animaux = []                           # cerfs posés : les ours se tiennent à l'écart (24.09.2026 : ours sur des cerfs)
    if DECORS["cerfs"]:
        loin_villes = carte.distance(villes, 3.0) >= 3.0
        clairiere = ~foret & (densite >= 0.4) & sec & (carte.pente < 0.3) & ~montagnes & loin_villes
        pts_al = _choisir(al & clairiere, densite, carte, N_CERFS_AL, ECART_CERFS, (), "cerfs:al")
        pts_brt = _choisir(bretonnie & ~al & clairiere, densite, carte, N_CERFS_BRT, ECART_CERFS, pts_al, "cerfs:brt")
        for k, (x, z) in enumerate(pts_al + pts_brt):
            n = 1 + int(_hash01("cerf", k) * 3)
            blocs.append(scene(f"decor:cerfs:{x:.2f}:{z:.2f}", CERF.format(n), (x, y(x, z), z),
                               (0.0, _hash01("cerf:lacet", k) * 360.0 - 180.0, 0.0), CERF_ECHELLE))
            voisins.ajouter(x, z)
        bilan["cerfs (clairières d'Athel Loren, bois de Bretonnie)"] = [(round(x, 1), round(z, 1)) for x, z in pts_al + pts_brt]
        animaux = pts_al + pts_brt

    if DECORS["ours"]:
        fond_al = al & ~foret & (densite >= 0.7) & sec & (carte.pente < 0.4) & ~montagnes
        pts = _choisir(fond_al, densite, carte, N_OURS, ECART_OURS, animaux, "ours")
        for k, (x, z) in enumerate(pts):
            blocs.append(scene(f"decor:ours:{x:.2f}:{z:.2f}", OURS, (x, y(x, z), z),
                               (0.0, _hash01("ours:lacet", k) * 360.0 - 180.0, 0.0), OURS_ECHELLE))
            voisins.ajouter(x, z)
        bilan["ours (profondeurs d'Athel Loren)"] = [(round(x, 1), round(z, 1)) for x, z in pts]

    if DECORS["corbeaux"]:
        deja = []
        for bl in (ambiance or {}).values():
            for b in bl:
                if "cam_fauna_bird" in b:
                    p = RX_POS.search(b)
                    if p:
                        v = [float(c) for c in p.group(1).split()]
                        deja.append((v[0], v[2]))
        pts = []
        for cle in CORBEAUX_COLONIES:
            if cle not in col:
                continue
            cx, cz = col[cle]
            if all(math.hypot(cx - a, cz - b) >= CORBEAUX_ECART_WH1 for a, b in deja):
                pts.append((cx, cz))
        for k, (x, z) in enumerate(pts):
            blocs.append(scene(f"decor:corbeaux:{x:.2f}:{z:.2f}", CORBEAUX, (x, y(x, z, CORBEAUX_HAUT), z),
                               (0.0, _hash01("corbeaux", k) * 360.0 - 180.0, 0.0), CORBEAUX_ECHELLE))
        bilan["corbeaux en cercle (châteaux de Mousillon)"] = [(round(x, 1), round(z, 1)) for x, z in pts]
        # vols d'oiseaux au-dessus de la canopée d'Athel Loren (même scène d'oiseaux de CA, plus bas et plus petits)
        canopee = al & foret & ~villes & ~montagnes
        pts_o = _choisir(canopee, densite, carte, N_OISEAUX_AL, ECART_OISEAUX_AL, deja, "oiseaux:al")
        for k, (x, z) in enumerate(pts_o):
            blocs.append(scene(f"decor:oiseaux_al:{x:.2f}:{z:.2f}", CORBEAUX, (x, y(x, z, OISEAUX_AL_HAUT), z),
                               (0.0, _hash01("oiseaux:al", k) * 360.0 - 180.0, 0.0), OISEAUX_AL_ECHELLE))
        bilan["vols d'oiseaux (canopée d'Athel Loren)"] = [(round(x, 1), round(z, 1)) for x, z in pts_o]

    if DECORS["papillons"]:
        pre = ~foret & (densite >= 0.15) & (densite <= 0.5) & sec & (carte.pente < 0.25) & ~montagnes & (al | bretonnie)
        pts = _choisir(pre, 1.0 - np.abs(densite - 0.3), carte, N_PAPILLONS, ECART_PAPILLONS, (), "papillons")
        n = 0
        for k, (x, z) in enumerate(pts):
            a = math.radians(_hash01("papillons", k) * 360.0)
            for m, (px_, pz_) in enumerate(((x, z), (x + PAPILLONS_PAIRE * math.cos(a), z + PAPILLONS_PAIRE * math.sin(a)))):
                i, j = carte.px(px_, pz_)
                if carte.eau[i, j] or carte.route[i, j]:
                    continue
                blocs.append(vfx(f"decor:papillons:{px_:.2f}:{pz_:.2f}", PAPILLONS, (px_, y(px_, pz_, PAPILLONS_HAUT), pz_),
                                 (0.0, _hash01("papillons:lacet", k, m) * 360.0 - 180.0, 0.0), PAPILLONS_ECHELLE))
                n += 1
        bilan["papillons (prés et clairières)"] = n

    if DECORS["epaves"]:
        mer = np.asarray(r["mer"], bool)
        prof = -np.asarray(r["hauteur_mer"], np.float64)
        d_terre = carte.distance(~mer, EPAVE_TERRE[1] + 0.5)
        riv = np.isfinite(np.asarray(r["eau_rivieres"], np.float64))
        loin_riv = carte.distance(riv, 1.5) >= 1.0
        ok = mer & (prof >= EPAVE_PROF[0]) & (prof <= EPAVE_PROF[1]) & (d_terre >= EPAVE_TERRE[0]) & \
            (d_terre <= EPAVE_TERRE[1]) & loin_riv
        pts = []
        for cle in EPAVES_COLONIES:
            if cle not in col:
                continue
            cx, cz = col[cle]
            i0, j0 = carte.px(cx, cz)
            rr = int(EPAVE_ANNEAU[1] * carte.pas) + 2
            ii, jj = np.mgrid[max(i0 - rr, 0):min(i0 + rr, H):3, max(j0 - rr, 0):min(j0 + rr, L):3]
            xs, zs = (jj + 0.5) / carte.pas, ((H - 1.5) - ii) / carte.pas / (3 ** 0.5 / 2)
            dist = np.hypot(xs - cx, zs - cz)
            c = ok[ii, jj] & (dist >= EPAVE_ANNEAU[0]) & (dist <= EPAVE_ANNEAU[1])
            if not c.any():
                continue
            # le plus près de la colonie, départagé par une graine (calculée sur les seuls candidats)
            ci, cj = np.nonzero(c)
            score = dist[ci, cj] + 0.3 * np.array([_hash01("epave", cle, a, b) for a, b in zip(ci, cj)])
            k = int(np.argmin(score))
            x, z = float(xs[ci[k], cj[k]]), float(zs[ci[k], cj[k]])
            i, j = carte.px(x, z)
            fond = -prof[i, j]
            lacet = _hash01("epave:lacet", cle) * 360.0 - 180.0
            blocs.append(maillage(f"decor:epave:{cle}", EPAVE, (x, fond + 0.04, z), (7.0, lacet, 17.0), EPAVE_ECHELLE))
            pts.append((round(x, 1), round(z, 1), round(float(fond), 2)))
        bilan["épaves de galion (échouées sur le fond)"] = pts

    if DECORS["pavillons"]:
        motif = list(PAVILLONS_ARC)
        sites = {}
        for cle in PAVILLONS_CHATEAUX:
            if cle not in col:
                continue
            s = _site(carte, masques, voisins, col[cle], motif, f"pavillons:{cle}", (1.8, 3.0))
            for k, (x, z, lacet) in enumerate(s):
                n = 1 + (k + int(_hash01("pavillon", cle) * 3)) % 3
                blocs.append(maillage(f"decor:pavillon:{cle}:{k}", PAVILLON.format(n), (x, y(x, z), z),
                                      (0.0, lacet, 0.0), PAVILLON_ECHELLE))
                voisins.ajouter(x, z)
            sites[cle.split("_", 2)[-1]] = [(round(x, 1), round(z, 1)) for x, z, _ in s]
        bilan["pavillons de chevaliers (face aux châteaux)"] = sites

    if DECORS["champs"]:
        # un champ : 3 rangs de cultures côte à côte, et une clôture de 3 pièces le long d'un côté
        rangs = [(-CHAMP_RANG, 0.0), (0.0, 0.0), (CHAMP_RANG, 0.0)]
        cloture = [(-CLOTURE_PAS, CLOTURE_RECUL), (0.0, CLOTURE_RECUL), (CLOTURE_PAS, CLOTURE_RECUL)]
        sites = {}
        for cle in CHAMPS_VILLAGES:
            if cle not in col:
                continue
            s = _site(carte, masques, voisins, col[cle], rangs + cloture, f"champs:{cle}", face=False)
            if not s:
                continue
            for k, (x, z, lacet) in enumerate(s):
                if k < len(rangs):
                    blocs.append(maillage(f"decor:champ:{cle}:{k}", CHAMP.format(1 + k % 2), (x, y(x, z, CHAMP_DY), z),
                                          (0.0, lacet, 0.0), CHAMP_ECHELLE))
                else:
                    n = 1 + int(_hash01("cloture", cle, k) * 5)
                    blocs.append(maillage(f"decor:cloture:{cle}:{k}", CLOTURE.format(n), (x, y(x, z), z),
                                          (0.0, lacet, 0.0), 1.0))   # long côté des clôtures : x local
                voisins.ajouter(x, z)
            sites[cle.split("_", 2)[-1]] = (round(s[1][0], 1), round(s[1][1], 1))
        bilan["champs et clôtures (villages bretons)"] = sites

    if DECORS["masures"]:
        sites = {}
        for cle in MASURES_COLONIES:
            if cle not in col:
                continue
            s = _site(carte, masques, voisins, col[cle], list(MASURES_HAMEAU), f"masures:{cle}", face=False)
            for k, (x, z, lacet) in enumerate(s):
                blocs.append(maillage(f"decor:masure:{cle}:{k}", MASURE.format(1 + k % 2), (x, y(x, z), z),
                                      (0.0, lacet + _hash01("masure", cle, k) * 60.0 - 30.0, 0.0), MASURE_ECHELLE))
                voisins.ajouter(x, z)
            if s:
                sites[cle.split("_", 2)[-1]] = (round(s[0][0], 1), round(s[0][1], 1))
        bilan["masures (hameaux de Mousillon)"] = sites

    if DECORS.get("pre_de_ceren"):
        poses = []
        for k, (modele, (x, z), ech, lacet, sens) in enumerate(PRE_DE_CEREN):
            blocs.append(maillage(f"decor:pre_de_ceren:{k}", modele, (x, y(x, z), z), (0.0, lacet, 0.0), ech))
            voisins.ajouter(x, z)
            poses.append((sens, round(x, 2), round(z, 2), round(y(x, z), 3)))
        bilan["Pré de Ceren (tour du Duc, chapelle de Galand)"] = poses
    return blocs, bilan
