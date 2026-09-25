#!/usr/bin/env python3
"""
champs_bretons.py - de vrais ensembles de champs autour des villages de Bretonnie (session du rendu, chaîne 12).

Pourquoi (24.09.2026, 04 h 20 - 05 h ; Charles, relevé de la construction sur la vidéo V2, 41 s et 136 s : à Fort
Solstice et à Montlac, « deux ou trois champs, chacun un seul rectangle plat collé au bord de la ville… des plaques
isolées », l'un « flotte » au-dessus de la pente) : ces rectangles sont le décalque de champ de CA
(`rigidmodels/campaign/decals/farm/farm.rigid_model_v2`) inclus dans les préfabs des villages bretonniens
(`prefabs/campaign/bretonnia_minor_level_1..4.bmd`, rayon p90 de leurs pièces 2,3 u, maximum 2,8), posés à plat sur notre
relief de WH1 (brouillons `prefabs_brt*.py`, `prefab_emprise.py`). Charles veut « de vrais ensembles de champs
bretonniens comme sur les cartes de CA : plusieurs parcelles de tailles et de teintes variées, orientées selon la route ou
la rivière, posées sur le sol, un peu écartées de la ville et jamais sur l'eau ».

Relevé des Empires (brouillon `champs_ie.py`) : 463 décalques de champ, dont 396 en `ECDecal apply_to_terrain="True"`
(projetés sur le sol : ils suivent le relief, jamais en dalle), échelle x 0,46 à 1,17, z 0,56 à 1,42 (le modèle est un cube
de 1 u : l'échelle est la taille de la parcelle), groupes de 2 à 4 ; rangs de cultures `farm_crop_01/02` à 0,36-0,42 ;
labours : décalque de boue `gen_mud_1/2` (2 630 poses).

Méthode (par village de Bretonnie, hors Mousillon) : un axe, celui de la route la plus proche (direction principale de ses
pixels à moins de AXE_PORTEE u), sinon tangent à la ville ; des blocs de parcelles (N_LONG x N_TRAVERS, tailles tirées dans
PARCELLE_LONG et PARCELLE_TRAVERS, séparées de SILLON) essayés à ANNEAU u du centre, tous les PAS_ANGLE degrés ; une
parcelle n'est posée que sur un sol constructible (pas d'eau, de mer, de route, de forêt, de montagne, ni l'emprise du
préfab R_PREFAB ; pente sous PENTE_MAX ; écart de hauteur sous ECART_MAX) et loin des objets de WH1 ; le meilleur bloc
(le plus de parcelles), puis un second si la place le permet. Parcelle : champ (décalque de champ), labour (décalque de
boue) ou rangs de cultures, selon une graine ; clôture le long du bord extérieur du bloc.

Usage (module) : blocs, bilan = champs_bretons.entites(r, carte, objets, ambiance)
"""

import json
import math
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ATELIER = r"C:\TotalWar-CampaignMap"
POSITIONS = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1", "colonies_map_data.json")
BRETONNIE = ("aquitaine", "bastonne", "bordeleaux", "brionne", "carcassonne", "gisoreux", "montfort", "parravon",
             "quenelles")
DECAL_CHAMP = "rigidmodels/campaign/decals/farm/farm.rigid_model_v2"
DECALS_LABOUR = ("rigidmodels/campaign/decals/gen/gen_mud_1.rigid_model_v2",
                 "rigidmodels/campaign/decals/gen/gen_mud_2.rigid_model_v2")
CULTURE = "rigidmodels/campaign/vegetation/shrubs/farm_crop_0{}.wsmodel"
CLOTURE = "rigidmodels/campaign/generic_props/fences_spikes/gen_fence_0{}.rigid_model_v2"
R_PREFAB = 2.5                       # u : emprise du préfab de la ville (p90 2,3, maximum 2,8)
ANNEAU = (2.9, 3.4, 3.9, 4.4, 4.9)      # u : distance du centre d'un bloc à la ville
PAS_ANGLE = 15
N_LONG, N_TRAVERS = 3, 2
PARCELLE_LONG = (0.60, 0.95)         # u, le long de l'axe
PARCELLE_TRAVERS = (0.45, 0.75)      # u, en travers
SILLON = 0.07                        # u entre deux parcelles
PROFONDEUR_DECAL = 0.6               # u : hauteur de la boîte de projection (échelle y du cube de 1 u)
CULTURE_ECHELLE, CULTURE_RANG = 0.38, 0.33
CLOTURE_PAS = 0.55
PENTE_MAX, ECART_MAX = 0.28, 0.14
DEGAGE_OBJETS = 0.3
AXE_PORTEE = 5.0
PARCELLES_MIN = 2
BLOCS_MAX = 2
PARTS = (("champ", 0.45), ("labour", 0.30), ("cultures", 0.25))


def _h(*cles):
    return zlib.crc32(":".join(str(c) for c in cles).encode()) / 2.0 ** 32


def positions_colonies():
    if not os.path.exists(POSITIONS):
        return {}
    return {k: (float(v[0]), float(v[1])) for k, v in json.load(open(POSITIONS, encoding="utf-8"))["keys"].items()}


def villages_bretons(col):
    out = {}
    for cle, p in col.items():
        parts = cle.split("_")
        if len(parts) > 2 and parts[2] in BRETONNIE:
            out[cle] = p
    return out


def axe_route(carte, cx, cz, route=None):
    """Angle (radians, 0 = est, sens trigonométrique vers le nord) de la route la plus proche : direction principale des
    pixels de route à moins de AXE_PORTEE u ; None s'il n'y en a pas assez."""
    route = carte.route if route is None else route
    i0, j0 = carte.px(cx, cz)
    n = int(AXE_PORTEE * carte.pas) + 1
    a0, a1 = max(i0 - n, 0), min(i0 + n + 1, carte.H)
    b0, b1 = max(j0 - n, 0), min(j0 + n + 1, carte.L)
    ii, jj = np.nonzero(route[a0:a1, b0:b1])
    if len(ii) < 12:
        return None
    x = (jj + b0 + 0.5) / carte.pas
    z = ((carte.H - 1.5) - (ii + a0)) / carte.pas / (3 ** 0.5 / 2)
    d = np.hypot(x - cx, z - cz)
    garde = (d > R_PREFAB * 0.6) & (d < AXE_PORTEE)
    if garde.sum() < 12:
        return None
    x, z = x[garde] - x[garde].mean(), z[garde] - z[garde].mean()
    c = np.cov(np.vstack([x, z]))
    w, v = np.linalg.eigh(c)
    e = v[:, int(np.argmax(w))]
    return math.atan2(e[1], e[0])


def _parcelles(cle, k_bloc):
    """[(du, dv, long, travers, genre)] d'un bloc, en repère local (u le long de l'axe, v en travers), centré."""
    longs = [PARCELLE_LONG[0] + (PARCELLE_LONG[1] - PARCELLE_LONG[0]) * _h(cle, k_bloc, "l", a) for a in range(N_LONG)]
    travs = [PARCELLE_TRAVERS[0] + (PARCELLE_TRAVERS[1] - PARCELLE_TRAVERS[0]) * _h(cle, k_bloc, "t", b)
             for b in range(N_TRAVERS)]
    tot_u = sum(longs) + SILLON * (N_LONG - 1)
    tot_v = sum(travs) + SILLON * (N_TRAVERS - 1)
    out = []
    u = -tot_u / 2
    for a, lo in enumerate(longs):
        v = -tot_v / 2
        for b, tr in enumerate(travs):
            t = _h(cle, k_bloc, "genre", a, b)
            genre, cumul = PARTS[-1][0], 0.0
            for g, p in PARTS:
                cumul += p
                if t < cumul:
                    genre = g
                    break
            out.append((u + lo / 2, v + tr / 2, lo, tr, genre))
            v += tr + SILLON
        u += lo + SILLON
    return out, tot_u, tot_v


def entites(r, carte, objets=None, ambiance=None, masques_interdits=None):
    """(blocs XML, bilan) des ensembles de champs autour des villages de Bretonnie."""
    from ajouts_carte_wh3 import maillage
    from decors_carte_wh3 import Voisins, _positions_objets
    from vie_carte_wh3 import _foret
    col = positions_colonies()
    villages = villages_bretons(col)
    foret, _ = _foret(r, carte)
    montagnes = np.asarray(r["montagnes"], bool)
    mer = np.asarray(r["mer"], bool)
    # la route elle-même (tuiles `roads` de WH1, cases de 0,33 u, un pixel de marge), pas les bandes d'hex des tuiles de
    # route de WH3 (`carte.route`, 1 u de large), qui couvraient presque tout le tour des villages (essai du 24.09, 17 h 17)
    import tuiles_wh1
    fam = tuiles_wh1.familles_par_case(ordre=["roads"])
    route = np.repeat(np.repeat(fam == "roads", 4, 0), 4, 1)[:carte.H, :carte.L]
    route = route | np.roll(route, 1, 0) | np.roll(route, -1, 0) | np.roll(route, 1, 1) | np.roll(route, -1, 1)
    interdit = carte.eau | route | foret | montagnes | mer
    if masques_interdits is not None:
        interdit = interdit | masques_interdits
    voisins = Voisins(_positions_objets(objets, ambiance))
    toutes_villes = list(col.values())
    blocs, bilan = [], {"villages": 0, "parcelles": 0, "champs": 0, "labours": 0, "cultures": 0, "clôtures": 0,
                        "sans place": []}

    def libre_sol(x, z):
        i, j = carte.px(x, z)
        if not (0 <= i < carte.H and 0 <= j < carte.L) or interdit[i, j] or carte.pente[i, j] > PENTE_MAX:
            return False
        return all(math.hypot(x - a, z - b) >= R_PREFAB for a, b in toutes_villes)

    for cle, (cx, cz) in sorted(villages.items()):
        axe0 = axe_route(carte, cx, cz, route)
        poses = []
        occupe = []
        for k_bloc in range(BLOCS_MAX):
            parc, tot_u, tot_v = _parcelles(cle, k_bloc)
            meilleur = None
            depart = _h(cle, "angle", k_bloc) * 360.0
            for rayon in ANNEAU:
                for da in range(0, 360, PAS_ANGLE):
                    a = math.radians(depart + da)
                    bx, bz = cx + rayon * math.cos(a), cz + rayon * math.sin(a)
                    if any(math.hypot(bx - ox, bz - oz) < max(tot_u, tot_v) for ox, oz in occupe):
                        continue
                    th = axe0 if axe0 is not None else a + math.pi / 2
                    cu, su = math.cos(th), math.sin(th)
                    bonnes = []
                    for du, dv, lo, tr, genre in parc:
                        px_, pz_ = bx + du * cu - dv * su, bz + du * su + dv * cu
                        coins = [(px_ + eu * lo / 2 * cu - ev * tr / 2 * su, pz_ + eu * lo / 2 * su + ev * tr / 2 * cu)
                                 for eu in (-1, 0, 1) for ev in (-1, 0, 1)]
                        if not all(libre_sol(x, z) for x, z in coins):
                            continue
                        ys = [float(carte.y_bilineaire(x, z)) for x, z in coins]
                        if max(ys) - min(ys) > ECART_MAX:
                            continue
                        if not all(voisins.libre(x, z, DEGAGE_OBJETS) for x, z in coins[::2]):
                            continue
                        bonnes.append((px_, pz_, lo, tr, genre, float(np.mean(ys))))
                    score = len(bonnes) - 0.05 * rayon
                    if len(bonnes) >= PARCELLES_MIN and (meilleur is None or score > meilleur[0]):
                        meilleur = (score, bonnes, th, (bx, bz))
            if meilleur is None:
                break
            _, bonnes, th, centre = meilleur
            occupe.append(centre)
            lacet = 90.0 - math.degrees(th)            # axe z local vers l'axe du bloc (convention des Empires)
            for n, (x, z, lo, tr, genre, y) in enumerate(bonnes):
                graine = f"champ:{cle}:{k_bloc}:{n}"
                if genre == "champ":
                    blocs.append(maillage(graine, DECAL_CHAMP, (x, y, z), (0.0, lacet + 90.0, 0.0),
                                          (lo, PROFONDEUR_DECAL, tr), decalque=True))
                    bilan["champs"] += 1
                elif genre == "labour":
                    modele = DECALS_LABOUR[int(_h(graine) * len(DECALS_LABOUR))]
                    blocs.append(maillage(graine, modele, (x, y, z), (0.0, lacet + 90.0, 0.0),
                                          (lo, PROFONDEUR_DECAL, tr), decalque=True))
                    bilan["labours"] += 1
                else:
                    # rangs de cultures en travers de la parcelle (un rang de CA : 0,32 x 0,86 u à l'échelle 0,38)
                    nr = max(1, int(tr / CULTURE_RANG))
                    for q in range(nr):
                        dv = -tr / 2 + CULTURE_RANG * (q + 0.5)
                        rx, rz = x - dv * math.sin(th), z + dv * math.cos(th)
                        blocs.append(maillage(f"{graine}:{q}", CULTURE.format(1 + (q % 2)),
                                              (rx, float(carte.y_bilineaire(rx, rz)) + 0.03, rz),
                                              (0.0, lacet, 0.0), CULTURE_ECHELLE))
                    bilan["cultures"] += 1
                voisins.ajouter(x, z)
                bilan["parcelles"] += 1
            # clôture le long du bord extérieur du bloc (côté opposé à la ville)
            bx, bz = centre
            nx, nz = -math.sin(th), math.cos(th)
            if (bx - cx) * nx + (bz - cz) * nz < 0:
                nx, nz = -nx, -nz
            n_cl = int(tot_u / CLOTURE_PAS)
            for q in range(n_cl):
                du = -tot_u / 2 + CLOTURE_PAS * (q + 0.5)
                fx, fz = bx + du * math.cos(th) + nx * (tot_v / 2 + 0.08), bz + du * math.sin(th) + nz * (tot_v / 2 + 0.08)
                if not libre_sol(fx, fz):
                    continue
                blocs.append(maillage(f"cloture:{cle}:{k_bloc}:{q}", CLOTURE.format(1 + int(_h(cle, k_bloc, q) * 5)),
                                      (fx, float(carte.y_bilineaire(fx, fz)), fz), (0.0, lacet + 90.0, 0.0), 1.0))
                bilan["clôtures"] += 1
        if occupe:
            bilan["villages"] += 1
        else:
            bilan["sans place"].append(cle.split("_", 2)[-1])
    return blocs, bilan
