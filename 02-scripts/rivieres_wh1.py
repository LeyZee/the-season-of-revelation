#!/usr/bin/env python3
"""
rivieres_wh1.py - les rivières de Warhammer 1 dans notre carte : le sol de leurs tuiles (le lit) dans notre relief, et leur
eau en maillages drapés qui portent le matériau d'eau de la mer de WH3, comme les rivières des Empires.

Pourquoi (22.09.2026, 23 h 55 ; Charles : « attaquer l'eau »). Établi le 22.09.2026 (GUIDE § 15, n° 101) :
- **WH1** : 1 399 poses de tuiles `river*` (`tile_list.bin`), 77 tuiles. Chaque `mesh.rigid_model_v2` a deux morceaux :
  le sol de la tuile (matériau 96, sommets de 8 octets en demi-flottants, x et z de 0 à 128 × cases, lit à y −10, berges
  de 0 à 0,9) et le ruban d'eau (matériau 90, sommets de 32 octets : x, y, z, 0,5, le long, largeur, travers, le long / 12,
  **au quart de l'unité de la tuile**, bande de paires de berges).
- **Pose** : celle des montagnes (`montagnes_wh1.cadre`, quarts de tour `CHOIX`), mais **n = z / 128** (sans + H) :
  les rubans passent alors à 0,15 unité (médiane) des sons de rivière de WH1, contre 0,63 avec la règle des montagnes ;
  le drapeau 0x04 (411 poses) ne change rien. Drapé comme les montagnes : y = relief de base + BASE + S × y local.
- **WH3** : plus de tuiles de rivière ; les Empires posent des maillages `terrain/campaigns/<carte>/models/river_<id>.
  wsmodel` (RMV2 v8, matériau 68, morceau « River », sommets de 48 octets : position + 1, uv, uv, repère en octets ;
  positions relatives au centre écrit à +628 de l'en-tête du morceau) qui portent le matériau d'eau de la mer. On en
  prend un comme gabarit (`GABARIT`) : même en-tête, nos sommets et nos triangles.
- Une eau plate par tuile ne suit pas la pente (relief sous un ruban : médiane 4 cm, p90 17 cm, pour un lit de 2,6 cm) :
  d'où les maillages drapés.

Repère : calculs dans celui des rasters (pixels carrés) ; les modèles et entités sont écrits dans le monde de WH3 (espace
des hex, z × 2/√3 : erreur 89).

Usage :
    python rivieres_wh1.py            # bilan à blanc
"""

import argparse
import hashlib
import math
import os
import shutil
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tuiles_wh1 as T                                              # noqa: E402
import montagnes_wh1 as M                                           # noqa: E402

ATELIER = M.ATELIER
KIT_WD = M.KIT_WD
import carte_config                                                 # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                          # la cible (kit)
SORTIE = carte_config.dans_projet("rivieres-wh1")
DATA_WH3 = M.DATA_WH3
FAMILLES = ("river", "river_stream", "river_start", "river_crossing", "river_confluence", "river_mouth")
MAT_SOL, MAT_EAU = 96, 90
ECHELLE_RUBAN = 4.0                               # unités du ruban -> unités de la tuile
GABARIT = "terrain/campaigns/wh3_main_combi_map_1/models/river_1720864eb6a52d3.wsmodel.rigid_model_v2"
import eau_carte                                                    # noqa: E402
MATERIAU_EAU = eau_carte.materiau()               # notre matériau d'eau s'il existe (masques de notre carte)
DOSSIER_MODELES = f"terrain/campaigns/{CARTE}/models"
Z_VERS_MONDE = M.Z_VERS_MONDE
# repère des sommets de WH3 en octets (normale vers le haut, tangente x, bitangente z), relevé sur le gabarit
NORMALE_HAUT = bytes((0x7F, 0xFF, 0x7F, 0x00))
TANGENTE_X = bytes((0xFF, 0x7F, 0x7F, 0x00))
BITANGENTE_Z = bytes((0x7F, 0x7F, 0xFF, 0x00))


def ident(graine):
    return "1" + hashlib.sha1(f"{CARTE}:{graine}".encode()).hexdigest()[:14]


def poses():
    """Les poses de tuiles de rivière de WH1, dans l'ordre de `tile_list.bin`."""
    noms, recs = T.lire()
    out = []
    for k, (x, y, code, _clim, _k, idx, _e) in enumerate(recs):
        fam = T.famille(noms[idx])
        if fam not in FAMILLES:
            continue
        p = M.Pose()
        p.k, p.x, p.y, p.code, p.idx = k, x, y, code, idx
        p.nom = noms[idx].replace("\\", "/").lower()
        p.famille = fam
        p.W, p.H = T.taille(noms[idx])
        out.append(p)
    return out


def morceaux(b):
    """{matériau: [(sommets (n, 8) float64 ou (n, 3), triangles (m, 3))]} du LOD 0 d'une tuile de rivière de WH1."""
    off = struct.unpack_from("<I", b, 152)[0]
    nb = struct.unpack_from("<I", b, 140)[0]
    out = {}
    for _ in range(nb):
        mat, _u, taille, voff, vc, ioff, ic = struct.unpack_from("<HHIIIII", b, off)
        pas = (ioff - voff) // max(vc, 1)
        brut = np.frombuffer(b, np.uint8, count=vc * pas, offset=off + voff).reshape(vc, pas)
        if pas == 8:
            v = brut[:, :8].copy().view("<f2").reshape(vc, 4)[:, :3].astype(np.float64)
        elif pas == 32:
            v = brut[:, :32].copy().view("<f4").reshape(vc, 8).astype(np.float64)
        else:
            raise ValueError(f"pas de sommet {pas} inattendu (matériau {mat})")
        t = np.frombuffer(b, "<u2", count=ic - ic % 3, offset=off + ioff).reshape(-1, 3).astype(np.int64)
        out.setdefault(mat, []).append((v, t))
        off += taille
    return out


BIT_MIROIR = 0x04                                 # rivières seulement : miroir local sur x avant le quart de tour


def vers_raster(p, vx, vz):
    """Sommets locaux (unités de la tuile) -> (x, z) du repère des rasters (n = z / 128, sans + H). Le bit 0x04 (29 % des
    poses) est un miroir local sur x avant la rotation : établi le 22.09.2026 sur 1 974 bords communs de tuiles de
    rivière (`rivieres_wh1_masque.py`, première version de ce module, restaurée le 23.09.2026)."""
    u = vx / 128.0
    if p.code & BIT_MIROIR:
        u = p.W - u
    X, Y = M.cadre(u, vz / 128.0, p.W, p.H, M.CHOIX[p.code & 0xF0])
    return (p.x + X) * M.CASE, (p.y + Y) * M.CASE


class Sol:
    """Relief de base de WH1 (`relief_maillages_wh1.relief_lf`) lu en bilinéaire dans le repère des rasters."""

    def __init__(self, lf, pas):
        self.lf, self.pas = lf, pas
        self.H, self.L = lf.shape

    def sous(self, xs, zs):
        cx = np.clip(xs * self.pas - 0.5, 0, self.L - 1.001)
        cy = np.clip((self.H - 1.5) - zs * self.pas, 0, self.H - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        f = self.lf
        return (f[r0, c0] * (1 - fx) * (1 - fy) + f[r0, c0 + 1] * fx * (1 - fy)
                + f[r0 + 1, c0] * (1 - fx) * fy + f[r0 + 1, c0 + 1] * fx * fy)


def surface(lf, pas, liste=None):
    """Sol des tuiles de rivière de WH1 (morceau 96, drapé sur `lf` + BASE) rastérisé sur la grille du relief (ligne 0 au
    nord) : minimum des morceaux qui se recouvrent (le lit l'emporte) ; NaN hors des tuiles."""
    import relief_maillages_wh1 as R
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    sol = Sol(lf, pas)
    H_, L_ = lf.shape
    grille = np.full((H_, L_), np.nan)
    cache = {}
    for p in (liste if liste is not None else poses()):
        if p.nom not in cache:
            cache[p.nom] = morceaux(wh1.lire(p.nom + "mesh.rigid_model_v2"))
        for v, t in cache[p.nom].get(MAT_SOL, []):
            wx, wz = vers_raster(p, v[:, 0], v[:, 2])
            hy = sol.sous(wx, wz) + M.BASE + M.S * v[:, 1]
            neg = np.full((H_, L_), np.nan)
            R.rasteriser_px(wx * pas - 0.5, (H_ - 1.5) - wz * pas, -hy, t, neg)   # maximum de -h = minimum de h
            grille = np.fmin(grille, -neg)
    return grille


# Profondeur de l'eau (23.09.2026 ; audit de la session « IA et modding 3D » : notre eau à +0,001 au-dessus du lit, celle
# des rivières des Empires à +0,052 en médiane). Le matériau d'eau de la mer de WH3 s'estompe avec la profondeur : à 1 mm,
# une rivière est presque invisible. Le lit est creusé de PROFONDEUR sous le ruban (moitié sur un pixel autour).
# (24.09.2026, chaîne 11 ; Charles : « l'eau ne bouge pas », rivières pâles contre l'eau sombre de WH1) 5 cm -> 12 cm au cœur :
# le matériau (river_depth_max_point 0,8) règle la teinte et l'agitation de l'eau sur la profondeur ; à 5 cm (6 % de ce
# point) l'eau restait transparente et ses normales presque plates. Essai en jeu : à juger par Charles.
PROFONDEUR = 0.12


def eau_raster(lf, pas, liste=None):
    """Hauteur de l'eau des rubans (drapés comme dans `construire`) rastérisée sur la grille du relief (ligne 0 au nord,
    repère des rasters) : maximum des rubans ; NaN hors de l'eau."""
    import relief_maillages_wh1 as R
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    sol = Sol(lf, pas)
    H_, L_ = lf.shape
    grille = np.full((H_, L_), np.nan)
    cache = {}
    for p in (liste if liste is not None else poses()):
        if p.nom not in cache:
            cache[p.nom] = morceaux(wh1.lire(p.nom + "mesh.rigid_model_v2"))
        for v, t in cache[p.nom].get(MAT_EAU, []):
            wx, wz = vers_raster(p, v[:, 0] * ECHELLE_RUBAN, v[:, 2] * ECHELLE_RUBAN)
            wy = sol.sous(wx, wz) + M.BASE + M.S * v[:, 1] * ECHELLE_RUBAN
            R.rasteriser_px(wx * pas - 0.5, (H_ - 1.5) - wz * pas, wy, t, grille)
    return grille


# Rivières LISSES ET RELIÉES (23.09.2026, 05 h ; Charles sur le pack de 04 h 37 : « les rivières n'ont aucun sens, elles
# ne sont pas reliées entre elles, ça déborde » ; « il faut vraiment que ça ne soit plus pixelisé »). Mesures (brouillon
# `rivieres/diag2.py`) : (1) le ruban des `blend0.dds` de WH1 s'estompe au bord de chaque tuile : au seuil 0,5, le réseau
# se coupe en 1 516 morceaux (session d'audit : écart médian 0,3 unité, 90 % sous 1 unité) ; les ruisseaux, plus fins
# qu'un pixel du masque, n'y dépassent pas 0,2 à 0,4 ; (2) l'eau des rubans de WH1 prolongée était au-dessus de la berge la
# plus basse (13 px) de 1,5 cm en médiane, de plus de 5 cm pour 16,7 % des pixels : elle débordait ; (3) une surface en
# carrés de pixels a des bords en escalier ; (4) les rubans d'eau de WH1 sont décalés d'un pixel sur le ruban des blend0 et
# portent des « poils » : on n'en garde que la hauteur, dans le ruban. D'où : champ du réseau fermé par un disque (0,6
# unité), lissé et ramené à son maximum local (le cœur de chaque ruisseau à 1) ; eau jusqu'à la courbe de niveau
# SEUIL_MAILLAGE (marching squares, sommets interpolés : bords lisses) ; niveau des rubans prolongé dans tout le réseau,
# plafonné MARGE_BERGE sous la berge la plus basse, lissé par enveloppe basse ; lit creusé en profil doux, le sol remonté
# juste au-dessus de l'eau au bord du maillage (le bord de l'eau passe sous la berge, comme chez CA).
RAYON_FERMETURE = 7                               # px (0,58 unité) : coupures du réseau aux jonctions de tuiles
FLOU_CHAMP = 1.0                                  # px
FENETRE_MAX_LOCAL = 9                             # px : cœur de chaque cours d'eau ramené à 1
MAX_LOCAL_MIN = 0.1                               # en dessous : pas de cours d'eau (bruit des blend0)
SURFACE_MIN = 30                                  # px : taches isolées écartées
SEUIL_MAILLAGE = 0.25                             # bord du maillage d'eau (sous la berge)
SEUIL_RIVE = 0.45                                 # bord de l'eau visible (berges basses)
SEUIL_LIT = 0.75                                  # au-delà : fond du lit
MARGE_BERGE = 0.01                                # l'eau 1 cm sous la berge la plus basse
FENETRE_BERGE = 21                                # px
REBORD = 0.02                                     # le sol au bord du maillage, au-dessus de l'eau
PROLONGE_EAU = 96                                 # px de proche en proche depuis les rubans de WH1
TUILE_EAU = 128                                   # px de raster par maillage d'eau (index sur 16 bits)
ECHELLE_UV_EAU = 0.1


def flou(a, sigma):
    """Flou gaussien séparable, bords répétés."""
    r = max(1, int(round(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.asarray(a, np.float64)
    p = np.pad(a, ((r, r), (0, 0)), mode="edge")
    a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode="edge")
    return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))


def _filtre(a, k, op, vide):
    """Minimum ou maximum sur une fenêtre carrée k x k (séparable, en place)."""
    r = k // 2
    p = np.pad(a, ((r, r), (0, 0)), constant_values=vide)
    out = p[0:a.shape[0]].copy()
    for i in range(1, k):
        op(out, p[i:i + a.shape[0]], out=out)
    p = np.pad(out, ((0, 0), (r, r)), constant_values=vide)
    out = p[:, 0:a.shape[1]].copy()
    for i in range(1, k):
        op(out, p[:, i:i + a.shape[1]], out=out)
    return out


def dilater(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        out = m.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                out |= p[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]]
        m = out
    return m


def composantes(m):
    """Étiquettes 8-connexes de `m` (-1 hors de `m`), par propagation du minimum et saut de pointeurs."""
    H_, L_ = m.shape
    lab = np.where(m, np.arange(H_ * L_).reshape(H_, L_), -1).astype(np.int64)
    grand = H_ * L_ + 1
    while True:
        p = np.pad(np.where(m, lab, grand), 1, constant_values=grand)
        mn = p[1:1 + H_, 1:1 + L_].copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                np.minimum(mn, p[1 + dy:1 + dy + H_, 1 + dx:1 + dx + L_], out=mn)
        plat = np.where(m, mn, -1).ravel()
        dedans = plat >= 0
        for _ in range(6):
            plat[dedans] = plat[plat[dedans]]
        neuf = plat.reshape(H_, L_)
        if np.array_equal(neuf, lab):
            return lab
        lab = neuf


POIDS_RUBANS = 0.8                                # rubans d'eau de WH1 dans le champ (le ruban des blend0 vaut 1)
DECALAGE_RUBANS = 1                               # lignes vers le sud : recouvrement des deux mesuré au mieux à +1


def champ_reseau(masque, rubans, mer):
    """(champ, écartées, gardées) : champ 0..1 du réseau de rivières de WH1 sur la grille du relief : ruban des blend0
    (`rivieres_wh1_masque`) et rubans d'eau (`eau_raster`, recalés de DECALAGE_RUBANS), fermé, lissé, cœur de chaque cours
    d'eau à 1, taches isolées écartées, nul sur la mer. Les deux sources recousent les ruisseaux (171 morceaux d'eau
    visible avec le seul ruban des blend0, 62 avec les deux ; le réseau principal d'un seul tenant)."""
    import masques_eau_carte as ME
    couverture = np.roll(np.isfinite(rubans), DECALAGE_RUBANS, 0).astype(np.float32)
    f = np.maximum(np.asarray(masque, np.float32), POIDS_RUBANS * couverture)
    f = flou(ME.fermer(f, RAYON_FERMETURE), FLOU_CHAMP)
    mx = _filtre(f, FENETRE_MAX_LOCAL, np.maximum, 0.0)
    f = np.where(mx >= MAX_LOCAL_MIN, np.clip(f / np.maximum(mx, 1e-6), 0, 1), 0.0)
    f = np.where(mer, 0.0, f)
    lab = composantes(f >= SEUIL_MAILLAGE)
    ids, n = np.unique(lab[lab >= 0], return_counts=True)
    petits = np.isin(lab, ids[n < SURFACE_MIN])
    f = np.where(dilater(petits, 2), 0.0, f)
    return f.astype(np.float32), int((n < SURFACE_MIN).sum()), int((n >= SURFACE_MIN).sum())


# LES SOURCES (23.09.2026, 18 h, session du rendu ; Charles : « rends plus jolies les sources des rivières, qui coulent
# depuis les montagnes, plus cohérentes »). Relevé (brouillon `sources_nous.py`, planche) : aux 30 tuiles `river_start` de
# WH1, notre ruban d'eau commençait par une coupe franche, de toute sa largeur, souvent au pied d'une montagne. Aux 24
# petites sources (tuiles 2 x 2 et 4 x 6 ; les 6 grandes, 8 x 12 et 9 x 12, sont des lacs de source et ne changent pas), le
# champ du réseau est effilé depuis le bout amont de l'eau : x SOURCE_CHAMP_BOUT au bout, puis jusqu'à 1 sur
# SOURCE_LONGUEUR (fondu doux) ; le maillage (champ >= SEUIL_MAILLAGE), l'eau visible (SEUIL_RIVE) et le lit
# (`creuser_doux`) s'amincissent ensemble jusqu'à une pointe. Le bout amont : le point de l'eau de la tuile le plus loin, le
# long de l'eau, du bord d'une fenêtre de SOURCE_FENETRE autour d'elle (là où la rivière s'en va) ; une tuile traversée de
# part en part (pas de bout dans la fenêtre) n'est pas touchée.
SOURCE_LONGUEUR = 2.0                             # unités le long de l'eau (1,2 : effilement à peine visible, essai)
SOURCE_CHAMP_BOUT = 0.15                          # sous SEUIL_MAILLAGE : le bout même n'a plus d'eau
SOURCE_FENETRE = 2.5                              # unités autour de la tuile
SOURCE_FAMILLES_EFFILEES = ("2x2", "4x6")


def effiler_sources(champ, pas):
    """(champ, bilan) : le champ du réseau effilé aux petites sources de WH1 (voir SOURCE_*)."""
    champ = np.array(champ, np.float64, copy=True)
    H_, L_ = champ.shape
    bilan = {"sources effilées": 0, "sources sans bout amont dans la fenêtre": 0, "lacs de source gardés": 0}
    lt = SOURCE_LONGUEUR * pas
    n_fen = int(SOURCE_FENETRE * pas)
    for p in poses():
        if p.famille != "river_start":
            continue
        taille = p.nom.rstrip("/").rsplit("/", 1)[-1].split("_", 1)[0]
        if taille not in SOURCE_FAMILLES_EFFILEES:
            bilan["lacs de source gardés"] += 1
            continue
        W, Ht = (p.H, p.W) if p.code & 0xF0 in (0x20, 0x80) else (p.W, p.H)
        # emprise de la tuile en px (cases de 4 px, lignes comptées depuis le sud)
        c0, c1 = p.x * 4, (p.x + W) * 4
        r0, r1 = (T.HAUTEUR - (p.y + Ht)) * 4, (T.HAUTEUR - p.y) * 4
        ci, cj = (r0 + r1) // 2, (c0 + c1) // 2
        R0, R1, C0, C1 = max(ci - n_fen, 0), min(ci + n_fen, H_), max(cj - n_fen, 0), min(cj + n_fen, L_)
        f = champ[R0:R1, C0:C1]
        eau = f >= SEUIL_MAILLAGE
        tuile = np.zeros_like(eau)
        tuile[max(r0 - R0, 0):max(r1 - R0, 0), max(c0 - C0, 0):max(c1 - C0, 0)] = True
        if not (eau & tuile).any():
            bilan["sources sans bout amont dans la fenêtre"] += 1
            continue
        # l'eau reliée à celle de la tuile, puis la distance le long de l'eau depuis le bord de la fenêtre
        lab = composantes(eau)
        ids = np.unique(lab[eau & tuile])
        zone = np.isin(lab, ids[ids >= 0])
        bord = np.zeros_like(zone)
        bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
        d = _distance_dans(zone, zone & bord)
        dt = np.where(zone & tuile & np.isfinite(d), d, -1.0)
        if dt.max() < 0.3 * n_fen:
            bilan["sources sans bout amont dans la fenêtre"] += 1
            continue
        i, j = np.unravel_index(int(np.argmax(dt)), dt.shape)
        # effilement depuis le bout amont, le long de l'eau
        pt = np.zeros_like(zone)
        pt[i, j] = True
        g = _distance_dans(zone, pt)
        t = np.clip(g / lt, 0, 1)
        m = SOURCE_CHAMP_BOUT + (1 - SOURCE_CHAMP_BOUT) * t * t * (3 - 2 * t)
        f[:] = np.where(zone & np.isfinite(g), f * m, f)
        bilan["sources effilées"] += 1
    return champ.astype(np.float32), bilan


# LES RIVIÈRES DE LA LARGEUR DE WH1 (24.09.2026, 00 h 45, session du rendu ; Charles, 00 h 20 : « pour les rivières, tu as ma
# permission de les rétrécir… il faut vraiment que ça soit comme dans WH1 »). Mesure (brouillon `colonies_riviere_wh1.py`) :
# notre eau couvrait 149 568 px, 3,8 fois les rubans d'eau de WH1 (39 041 px) ; le lit sableux peint de WH1 (105 329 px)
# restait sous notre eau. Dans WH1, un filet d'eau fin court sur un lit de sable plus large. Le champ du réseau est plafonné
# partout par un champ étroit : 1 sur les rubans de WH1, nul à LARGEUR_WH1_PX ; là où WH1 n'a pas de ruban (coutures entre
# ses tuiles), le squelette de notre réseau, aussi fin (LARGEUR_FIL_PX), garde la rivière d'un seul tenant de la source à
# la mer, prolongé jusqu'aux rubans (TROU_RUBAN_PX). Essai à blanc : brouillon `essai_largeur_wh1.py`.
# Réglage (24.09.2026, 01 h 50 ; planche `planche_riv_19_19_1.png`) : eau visible 120 760 -> 94 844 px, 96 % des rubans de
# WH1 couverts, formes de WH1 gardées (bras multiples, méandres) ; trou de 3 px : 404 morceaux ; squelette seul : 62 045 px
# mais une largeur uniforme et 55 % des rubans seulement. Avec 1,9 px, le premier pixel hors du ruban est à peine sous
# l'eau : la rivière dessinée n'a guère que la largeur du ruban.
LARGEUR_WH1 = True
LARGEUR_WH1_PX = 1.9                              # px : demi-largeur du champ étroit autour des rubans de WH1
LARGEUR_FIL_PX = 1.9                              # px : autour du squelette, dans les trous des rubans
TROU_RUBAN_PX = 1                                 # px : le squelette ne sert qu'à plus de cette distance d'un ruban


def _distance_px(m, n):
    """Distance (px, dilatations 8-connexes) au masque, jusqu'à n ; n + 1 au-delà."""
    d = np.full(m.shape, n + 1.0)
    d[m] = 0.0
    cur = m
    for k in range(1, n + 1):
        nxt = dilater(cur, 1)
        d[nxt & ~cur] = k
        cur = nxt
    return d


def largeur_wh1(champ, rubans):
    """(champ, bilan) : le champ du réseau plafonné par le champ étroit des rubans de WH1 et du squelette (LARGEUR_WH1)."""
    zone = champ >= SEUIL_MAILLAGE
    ruban = np.roll(np.isfinite(rubans), DECALAGE_RUBANS, 0) & dilater(zone, 1)
    d_r = _distance_px(ruban, max(int(np.ceil(LARGEUR_WH1_PX)) + 1, TROU_RUBAN_PX + 1))
    etroit = np.clip(1.0 - d_r / LARGEUR_WH1_PX, 0.0, 1.0)
    sq = amincir(zone)
    fil = sq & dilater(sq & (d_r > TROU_RUBAN_PX), TROU_RUBAN_PX + 1)
    d_f = _distance_px(fil, int(np.ceil(LARGEUR_FIL_PX)) + 1)
    etroit = np.maximum(etroit, np.clip(1.0 - d_f / LARGEUR_FIL_PX, 0.0, 1.0))
    neuf = np.minimum(champ, etroit).astype(np.float32)
    bilan = {"eau visible avant (px)": int((champ >= SEUIL_RIVE).sum()), "après (px)": int((neuf >= SEUIL_RIVE).sum()),
             "rubans de WH1 (px)": int(ruban.sum()), "squelette dans les trous des rubans (px)": int(fil.sum())}
    return neuf, bilan


# LES RIVIÈRES SUR L'AXE, À LA LARGEUR LOCALE DE WH1 (24.09.2026, chaîne 13, session du rendu ; Charles : « les rivières
# parfaites… comme dans Warhammer 1 à l'identique », puis « prépare les méthodes des rivières pour la chaîne 13, il faut
# vraiment qu'elles rentrent bien »). Avec `largeur_wh1` à 1,9 px, l'eau fait 4,98 px de large (0,415 u), 2,2 fois les
# rubans de WH1 (2,31 px, 0,192 u) ; ramenée à 1,2 px, elle a la bonne largeur mais se coupe en 953 morceaux (brouillon
# `essai_largeur_rivieres.py`) : le squelette n'était pris que loin des rubans, et les rubans de WH1 ont des trous à chaque
# couture de tuile. Ici, deux champs étroits, sans largeur fixe :
# - le ruban de WH1 tel quel : bord de l'eau visible (SEUIL_RIVE) au bord du ruban, bras multiples et méandres gardés ;
# - l'AXE du réseau (squelette de la zone d'eau, d'un seul tenant), partout : bord visible à la demi-largeur LOCALE des rubans
#   de WH1 (surface des rubans / longueur de l'axe dans une fenêtre de AXE_FENETRE px), prolongée le long de l'axe dans les
#   trous, jamais sous AXE_DEMI_MIN : chaque pixel de l'axe est dans l'eau, la rivière reste d'un seul tenant.
# Distance euclidienne (centres des pixels) : le bord interpolé du maillage tombe là où il faut, sans escalier de pixels.
# ALLUMÉ (25.09.2026, 01 h, chaîne 14 ; Charles : « le rendu des rivières n'est pas top non plus ») : essai du 24.09 sur le
# champ en cache, eau visible 51 720 px (WH1 38 255, méthode 1,9 px : 94 902), morceaux 327 avant l'écart des bouts de
# ruban isolés ; contrôle à l'essai à blanc de la chaîne 14 (`essai_chaine14.py`).
AXE_WH1 = True
AXE_FENETRE = 7                                   # px : mesure de la largeur des rubans de WH1 autour de l'axe
AXE_DEMI_MIN = 0.7                                # px : demi-largeur visible minimale (ruisseaux, trous des rubans)
AXE_DEMI_MAX = 6.0                                # px
AXE_PORTEE = 8                                    # px : portée du champ autour de l'axe (au-delà de 1,36 x AXE_DEMI_MAX)


def _somme_boite(a, k):
    """Somme de `a` sur une fenêtre carrée k x k (k impair) centrée, bords à zéro."""
    r = k // 2
    c = np.cumsum(np.cumsum(np.pad(np.asarray(a, np.float64), ((r + 1, r), (r + 1, r))), 0), 1)
    return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]


def _plus_proche(graines, valeurs, portee):
    """(distance, valeur) : distance euclidienne (px) au pixel de `graines` le plus proche, jusqu'à `portee` (inf au-delà),
    et la valeur de ce pixel."""
    H_, L_ = graines.shape
    d = np.full((H_, L_), np.inf, np.float32)
    v = np.zeros((H_, L_), np.float32)
    pg = np.pad(graines, portee)
    pv = np.pad(np.where(graines, valeurs, 0.0).astype(np.float32), portee)
    decal = sorted(((dy * dy + dx * dx) ** 0.5, dy, dx) for dy in range(-portee, portee + 1)
                   for dx in range(-portee, portee + 1) if dy * dy + dx * dx <= portee * portee)
    for dd, dy, dx in decal:                      # du plus proche au plus loin : le premier trouvé est le plus proche
        s = pg[portee + dy:portee + dy + H_, portee + dx:portee + dx + L_]
        neuf = s & ~np.isfinite(d)
        if neuf.any():
            d[neuf] = dd
            v[neuf] = pv[portee + dy:portee + dy + H_, portee + dx:portee + dx + L_][neuf]
    return d, v


def largeur_axe(champ, rubans):
    """(champ, bilan) : le champ du réseau plafonné par le champ étroit des rubans de WH1 et de l'axe à la largeur locale
    de WH1 (AXE_WH1, voir plus haut)."""
    zone = champ >= SEUIL_MAILLAGE
    ruban = np.roll(np.isfinite(rubans), DECALAGE_RUBANS, 0) & dilater(zone, 1)
    axe = amincir(zone)
    k = AXE_FENETRE
    n_r = _somme_boite(ruban & dilater(axe, k // 2), k)
    # longueur de l'axe : un pas droit vaut 1, un pas en diagonale √2 (moitié à chacun de ses deux pixels)
    pa = np.pad(axe, 1)
    lon = np.zeros(axe.shape)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lon += pa[1 + dy:1 + dy + axe.shape[0], 1 + dx:1 + dx + axe.shape[1]] * (0.5 * (2 ** 0.5 if dy and dx else 1.0))
    lon = np.where(axe, np.maximum(lon, 1.0), 0.0)
    n_a = _somme_boite(lon, k)
    demi = np.where(axe & (n_r > 0), n_r / np.maximum(n_a, 1.0) / 2.0, np.nan)
    mesure = int(np.isfinite(demi).sum())
    demi = _prolonger(demi, axe, 400)
    demi = np.clip(np.where(axe, np.nan_to_num(demi, nan=AXE_DEMI_MIN), 0.0), AXE_DEMI_MIN, AXE_DEMI_MAX)
    d_a, h = _plus_proche(axe, demi, AXE_PORTEE)
    etroit_axe = np.clip(1.0 - d_a / np.maximum(h, 1e-3) * (1.0 - SEUIL_RIVE), 0.0, 1.0)
    # le ruban : 1 dedans ; bord visible à 0,55 px du centre du dernier pixel du ruban (son bord), maillage à 0,75 px
    d_r, _ = _plus_proche(ruban, np.ones(ruban.shape, np.float32), 2)
    etroit_ruban = np.clip(1.0 - d_r * (1.0 - SEUIL_RIVE) / 0.55, 0.0, 1.0)
    neuf = np.minimum(champ, np.maximum(etroit_axe, etroit_ruban)).astype(np.float32)
    # (essai de 23 h 05 : 327 morceaux) les bouts de ruban de WH1 qui ne touchent pas l'axe (poils, rubans décalés) restent
    # à sec : seule compte l'eau d'un seul tenant avec l'axe
    eau = neuf >= SEUIL_MAILLAGE
    lab = composantes(eau)
    garde = np.unique(lab[axe & eau])
    isoles = eau & ~np.isin(lab, garde)
    neuf = np.where(isoles, np.minimum(neuf, SEUIL_MAILLAGE * 0.8), neuf).astype(np.float32)
    p = np.percentile(demi[axe], [10, 50, 90]) if axe.any() else [0, 0, 0]
    bilan = {"eau visible avant (px)": int((champ >= SEUIL_RIVE).sum()), "après (px)": int((neuf >= SEUIL_RIVE).sum()),
             "rubans de WH1 (px)": int(ruban.sum()), "axe (px)": int(axe.sum()),
             "axe mesuré sur les rubans (px)": mesure, "bouts de ruban isolés laissés à sec (px)": int(isoles.sum()),
             "demi-largeur sur l'axe p10/p50/p90 (px)": [round(float(x), 2) for x in p]}
    return neuf, bilan


# LES COLONIES AU BORD DE L'EAU, COMME DANS WH1 (24.09.2026, 00 h 15, session du rendu ; Charles, 23.09.2026, 23 h 30 :
# Fort Solstice « est sur une rivière ; elle doit être juste à côté »). Mesure (brouillon `colonies_riviere_wh1.py`) : notre
# eau couvre 3,8 fois les rubans d'eau de WH1 (le lit sableux peint de WH1 est entre les deux) ; à Fort Solstice, le filet
# de WH1 longe la ville (2 % de l'emplacement de 1,4 u, à 0,96 u du centre) quand notre rivière en couvrait 9 % ; au Château
# de Desfleuves, 2 % contre 26 %. Autour de chaque colonie, le champ du réseau (largeur de l'eau, du maillage et du lit) est
# plafonné par un champ étroit tiré des rubans de WH1 : 1 sur le ruban, nul à COLONIE_LARGEUR_PX ; plafond plein jusqu'à
# COLONIE_R_SEC, effacé en fondu à COLONIE_R_FONDU, où la rivière reprend sa largeur.
COLONIES_AU_SEC = True
COLONIE_R_SEC, COLONIE_R_FONDU = 1.6, 3.0         # unités autour de la position de la colonie (map_data.esf)
COLONIE_LARGEUR_PX = 3.0                          # px : demi-largeur du champ étroit autour du ruban de WH1


def colonies_au_sec(champ, rubans, positions, pas):
    """(champ, bilan) : autour de chaque colonie (x, z), le champ plafonné par le champ étroit des rubans de WH1
    (voir COLONIE_*) ; calculé par fenêtre autour de chaque colonie."""
    champ = np.array(champ, np.float64, copy=True)
    H_, L_ = champ.shape
    r3 = 3 ** 0.5 / 2
    rr = int(COLONIE_R_FONDU * pas) + 2
    n_dil = int(np.ceil(COLONIE_LARGEUR_PX))
    bilan = {"colonies dont la rivière est rétrécie": 0, "px d'eau visible retirés": 0}
    for x, z in positions:
        i, j = (H_ - 1.5) - z * r3 * pas, x * pas - 0.5
        i0, i1 = max(int(i) - rr, DECALAGE_RUBANS), min(int(i) + rr + 1, H_)
        j0, j1 = max(int(j) - rr, 0), min(int(j) + rr + 1, L_)
        if i0 >= i1 or j0 >= j1:
            continue
        f = champ[i0:i1, j0:j1]
        if not (f >= SEUIL_MAILLAGE).any():
            continue
        # le ruban de WH1 recalé comme dans `champ_reseau` (DECALAGE_RUBANS lignes vers le sud)
        ruban = np.isfinite(rubans[i0 - DECALAGE_RUBANS:i1 - DECALAGE_RUBANS, j0:j1])
        d = np.where(ruban, 0.0, np.inf)
        m = ruban
        for k in range(1, n_dil + 1):
            m2 = dilater(m, 1)
            d[m2 & ~m] = k
            m = m2
        etroit = np.clip(1.0 - d / COLONIE_LARGEUR_PX, 0.0, 1.0)
        ii, jj = np.mgrid[i0:i1, j0:j1]
        dist = np.hypot((ii - i) / (r3 * pas), (jj - j) / pas)
        w = np.clip((COLONIE_R_FONDU - dist) / (COLONIE_R_FONDU - COLONIE_R_SEC), 0.0, 1.0)
        w = w * w * (3 - 2 * w)
        neuf = np.minimum(f, etroit * w + (1.0 - w))
        retires = int(((f >= SEUIL_RIVE) & (neuf < SEUIL_RIVE)).sum())
        if retires:
            bilan["colonies dont la rivière est rétrécie"] += 1
            bilan["px d'eau visible retirés"] += retires
        champ[i0:i1, j0:j1] = neuf
    return champ.astype(np.float32), bilan


def _distance_dans(zone, depart):
    """Distance (px, 8-connexe, pas de 1 ou √2) le long de `zone` depuis `depart` ; inf ailleurs."""
    import heapq
    H_, L_ = zone.shape
    d = np.full(zone.shape, np.inf)
    tas = [(0.0, int(i), int(j)) for i, j in zip(*np.nonzero(depart & zone))]
    for _, i, j in tas:
        d[i, j] = 0.0
    heapq.heapify(tas)
    pas8 = [(dy, dx, (dy * dy + dx * dx) ** 0.5) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    while tas:
        dd, i, j = heapq.heappop(tas)
        if dd > d[i, j]:
            continue
        for dy, dx, w in pas8:
            a, b = i + dy, j + dx
            if 0 <= a < H_ and 0 <= b < L_ and zone[a, b] and dd + w < d[a, b]:
                d[a, b] = dd + w
                heapq.heappush(tas, (dd + w, a, b))
    return d


def _prolonger(w, zone, n):
    """Valeurs finies de `w` prolongées de proche en proche dans `zone` (moyenne des voisins connus), `n` pas au plus."""
    w = np.where(zone, w, np.nan).astype(np.float64)
    for _ in range(n):
        manque = zone & ~np.isfinite(w)
        if not manque.any():
            break
        p = np.pad(w, 1, constant_values=np.nan)
        s, c = np.zeros(w.shape), np.zeros(w.shape)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    v = p[1 + dy:1 + dy + w.shape[0], 1 + dx:1 + dx + w.shape[1]]
                    ok = np.isfinite(v)
                    s += np.where(ok, v, 0.0)
                    c += ok
        remplir = manque & (c > 0)
        w[remplir] = s[remplir] / c[remplir]
    return w


# LES BERGES AU BORD D'UN À-PIC (24.09.2026, chaîne 13 ; Charles, pack de 22 h 20 : de la mare de la Clairière Royale à la
# cascade de la gorge, « des trous noirs entre les nappes »). Le plafond de l'eau (MARGE_BERGE sous la berge la plus basse
# dans FENETRE_BERGE px, 0,83 u de part et d'autre) voyait le fond de la gorge le long du rebord : la rivière passait 0,5 à
# 1,0 u sous ses rubans de WH1 et son lit devenait une tranchée (brouillon `mare_cascade_etapes.py`). Quand la fenêtre voit
# une berge plus basse de CHUTE_BERGE que les berges immédiates (FENETRE_BERGE_PROCHE px), ce sont celles-ci qui comptent.
BERGE_PROCHE_AUX_CHUTES = True
# L'EAU PRÈS DU SOL DE WH1 (25.09.2026, 01 h 15, chaîne 14 ; audit de toute la carte, `scratchpad\audit_carte\` : lits
# creusés 0,8 à 1,08 u sous le relief de WH1, gorges à 76-83° là où WH1 avait 24-42°, arbres et objets de WH1 dans l'eau,
# gorges de Tyr Vanna, Tal Jul-Finel, Palais des Chutes). Les rubans de WH1 suivent son sol ; notre eau, plafonnée par les
# berges et tirée vers les étangs, passait loin dessous, et le lit (creusement doux, fil de l'eau) la suivait. L'eau des
# rivières n'est jamais plus de EAU_SOUS_SOL_MAX sous le sol de WH1 (avant creusement) ; les descentes vers la mer et vers
# les étangs, bornées, passent après.
EAU_SOUS_SOL_MAX = 0.15
FENETRE_BERGE_PROCHE = 7                          # px
CHUTE_BERGE = 0.30


def niveau_eau(rubans, champ, sol, mer):
    """(niveau, n) : hauteur de l'eau sur la zone du maillage (champ >= SEUIL_MAILLAGE, hors mer), NaN ailleurs ; `n`
    pixels loin de tout ruban de WH1 (mis au sol avant le plafond)."""
    zone = (champ >= SEUIL_MAILLAGE) & ~mer
    w = np.where(zone & (champ >= 0.5) & np.isfinite(rubans), rubans, np.nan)
    w = _prolonger(w, zone, PROLONGE_EAU)
    reste = zone & ~np.isfinite(w)
    w[reste] = sol[reste]
    berge = ~dilater(zone, 2) & ~mer
    bmin = _filtre(np.where(berge, sol, np.inf).astype(np.float64), FENETRE_BERGE, np.minimum, np.inf)
    if BERGE_PROCHE_AUX_CHUTES:
        # (chaîne 13) au bord d'un à-pic, la fenêtre de FENETRE_BERGE px voit le pied de la paroi : les berges immédiates
        b_proche = _filtre(np.where(berge, sol, np.inf).astype(np.float64), FENETRE_BERGE_PROCHE, np.minimum, np.inf)
        bmin = np.where(np.isfinite(b_proche) & (bmin < b_proche - CHUTE_BERGE), b_proche, bmin)
    w = np.minimum(w, np.where(np.isfinite(bmin), bmin - MARGE_BERGE, np.inf))
    c = flou(zone.astype(np.float64), 1.5)
    for _ in range(6):                            # enveloppe basse lissée : jamais au-dessus du plafond
        s = flou(np.where(zone, w, 0.0), 1.5)
        w = np.where(zone, np.minimum(w, s / np.maximum(c, 1e-6)), np.nan)
    return np.where(zone, w, np.nan).astype(np.float32), int(reste.sum())


def creuser_doux(sol, niveau, champ):
    """(sol, n eau, n relevés) : lit en profil doux sous l'eau. Profil : REBORD au-dessus de l'eau au bord du maillage
    (SEUIL_MAILLAGE : le bord de l'eau passe sous la berge), l'eau affleure à SEUIL_RIVE, fond PROFONDEUR plus bas au
    cœur (SEUIL_LIT). Le sol d'origine reste là où il est plus haut que ce profil (berges hautes), fondu vers le fond."""
    def lisse(a, b):
        s = np.clip((champ - a) / (b - a), 0, 1)
        return s * s * (3 - 2 * s)
    eau = np.isfinite(niveau)
    n = np.where(eau, niveau, 0.0).astype(np.float64)
    u, v = lisse(SEUIL_MAILLAGE, SEUIL_RIVE), lisse(SEUIL_RIVE, SEUIL_LIT)
    profil = n + REBORD * (1 - u) - PROFONDEUR * v
    lit = sol * (1 - v) + np.minimum(sol, n - PROFONDEUR) * v
    out = np.where(eau, np.maximum(lit, profil), sol)
    return out.astype(np.float32), int(eau.sum()), int((eau & (profil > sol)).sum())


# LE FIL DE L'EAU (23.09.2026, 22 h, session du rendu ; Charles : « de temps en temps, des trous entre deux morceaux de
# rivière… que tout s'enchaîne bien, de la source à la mer »). Mesures (brouillons `diag_trous_rivieres.py`,
# `diag_coupures_visibles.py`, `diag_rivieres_champ.py`, chaîne 5) : le réseau est d'un seul tenant (aucune rivière de WH1
# coupée, 80 px d'eau de WH1 sans la nôtre), mais l'eau VISIBLE ne couvre que 71 % du maillage, en 74 morceaux : le lit
# n'est creusé sous l'eau qu'en proportion du champ (`creuser_doux`, de SEUIL_RIVE à SEUIL_LIT), et là où le champ faiblit
# (jonctions des tuiles de WH1, ruisseaux fins) la berge d'origine passe au-dessus de l'eau (champ >= 0,6 : 97,5 % visible ;
# de 0,45 à 0,6 : l'eau affleure mal). Le fil de l'eau : le squelette de la zone d'eau (amincissement de Zhang et Suen, une
# ligne d'un pixel au milieu de chaque cours d'eau, d'un seul tenant de la source à la mer), élargi de FIL_RAYON px ; le sol
# y est au plus FIL_PROFONDEUR sous l'eau. Appliqué après les collines et les étangs, qui relevaient aussi le sol ici et là.
FIL_DE_L_EAU = True
FIL_RAYON = 1                                     # px de part et d'autre du squelette (ruban de 3 px, 0,25 u)
FIL_PROFONDEUR = 0.04                             # le sol du fil sous l'eau (l'eau de WH3 s'estompe avec la profondeur)
# Les flancs (même heure) : là où la berge dominait l'eau de 0,4 à 1 u (sources de montagne, 416 px abaissés de plus de
# 0,3 sur 63 700), le ruban seul faisait une fente à parois verticales ; sur FIL_BERGE px de part et d'autre, le sol est au
# plus à l'eau - FIL_PROFONDEUR + FIL_PENTE x la distance au ruban : une petite gorge en V, toujours au-dessus de l'eau
# hors du ruban (+ 0,08 au premier pixel), jamais dans la mer ni près d'un étang (`garde`).
FIL_PENTE = 0.12                                  # u par px (environ 55°)
FIL_BERGE = 5                                     # px
FIL_FLOU = 1.2                                    # px : flancs lissés (pas de terrasses aux pas d'un pixel)


def amincir(m, iter_max=400):
    """Squelette 8-connexe de `m` (Zhang et Suen, vectorisé sur la boîte englobante) : une ligne d'un pixel au milieu de
    chaque forme, d'un seul tenant quand la forme l'est."""
    out = np.zeros(m.shape, bool)
    if not m.any():
        return out
    rr, cc = np.nonzero(m)
    r0, r1, c0, c1 = rr.min(), rr.max() + 1, cc.min(), cc.max() + 1
    img = np.pad(m[r0:r1, c0:c1], 1).astype(np.uint8)
    for _ in range(iter_max):
        change = False
        for etape in (0, 1):
            p2, p3, p4, p5 = img[:-2, 1:-1], img[:-2, 2:], img[1:-1, 2:], img[2:, 2:]
            p6, p7, p8, p9 = img[2:, 1:-1], img[2:, :-2], img[1:-1, :-2], img[:-2, :-2]
            c = img[1:-1, 1:-1]
            b = p2.astype(np.int16) + p3 + p4 + p5 + p6 + p7 + p8 + p9
            suite = (p2, p3, p4, p5, p6, p7, p8, p9, p2)
            a = sum(((suite[k] == 0) & (suite[k + 1] == 1)).astype(np.int16) for k in range(8))
            if etape == 0:
                cond = ((p2 & p4 & p6) == 0) & ((p4 & p6 & p8) == 0)
            else:
                cond = ((p2 & p4 & p8) == 0) & ((p2 & p6 & p8) == 0)
            enlever = (c == 1) & (b >= 2) & (b <= 6) & (a == 1) & cond
            if enlever.any():
                c[enlever] = 0
                change = True
        if not change:
            break
    out[r0:r1, c0:c1] = img[1:-1, 1:-1].astype(bool)
    return out


def fil_de_l_eau(sol, niveau, mer, garde=None):
    """(sol, bilan) : sous le fil de l'eau (squelette de la zone d'eau hors mer, élargi de FIL_RAYON px), le sol au plus
    FIL_PROFONDEUR sous l'eau ; sur FIL_BERGE px autour, au plus l'eau du ruban voisin - FIL_PROFONDEUR + FIL_PENTE x la
    distance (hors mer et hors `garde`) ; ailleurs inchangé."""
    zone = np.isfinite(niveau) & ~mer
    squelette = amincir(zone)
    fil = dilater(squelette, FIL_RAYON) & zone
    niv = np.where(fil, np.asarray(niveau, np.float64), np.nan)
    cible = np.where(fil, niv - FIL_PROFONDEUR, np.inf)
    interdit = mer | (garde if garde is not None else np.zeros_like(mer))
    anneau = fil.copy()
    for k in range(1, FIL_BERGE + 1):
        neuf = dilater(anneau, 1) & ~anneau & ~interdit
        niv = _prolonger(niv, anneau | neuf, 1)
        cible = np.where(neuf & np.isfinite(niv), niv - FIL_PROFONDEUR + FIL_PENTE * k, cible)
        anneau |= neuf
    # flancs lissés (les pas d'un pixel des anneaux faisaient des terrasses) ; hors de la zone d'eau, jamais sous
    # l'eau + REBORD (pas de bord de maillage à l'air)
    flanc = anneau & ~fil & np.isfinite(cible)
    c = flou(np.isfinite(cible).astype(np.float64), FIL_FLOU)
    lisse = flou(np.where(np.isfinite(cible), cible, 0.0), FIL_FLOU) / np.maximum(c, 1e-6)
    plancher = np.where(zone, niv - FIL_PROFONDEUR, niv + REBORD)
    cible = np.where(flanc, np.maximum(lisse, plancher), cible)
    bas = sol > cible
    d = np.where(bas, sol - cible, 0.0)
    bilan = {"squelette (px)": int(squelette.sum()), "fil (px)": int(fil.sum()),
             "sol abaissé : ruban (px)": int((bas & fil).sum()), "flancs (px)": int((bas & ~fil).sum()),
             "abaissement p50 / max": (round(float(np.median(d[bas])), 3), round(float(d.max()), 3)) if bas.any()
             else (0.0, 0.0)}
    return np.where(bas, cible, sol).astype(np.float32), bilan


# LES BERGES BASSES (25.09.2026, 03 h, chaîne 15, session du rendu ; Charles, vidéo de 02 h 19 : rivières en chapelet de
# taches blanches, festons ; accord de Charles, 03 h ; enquête `scratchpad\enquete_rivieres\`). De loin, le jeu tesselle le
# sol grossièrement (au plus un sommet tous les 14 px, 1,17 u ; nuanceur de coque du sol désassemblé) : notre lit étroit
# (0,17 u) était comblé et la berge passait au-dessus de l'eau, 49 % de l'eau visible à 7 px, 28 % à 14 px, en centaines de
# morceaux. Chez CA, la terre autour des rubans est souvent sous l'eau (34 % à 0-3 px, 0,6 % chez nous). Sur BERGE_BASSE_PX
# autour de l'eau, le sol est au plus l'eau voisine - BERGE_BASSE_MARGE ; puis il rejoint le sol d'origine sur
# BERGE_BASSE_RETOUR_PX en courbe douce ; abaissement plafonné (BERGE_BASSE_PLAFOND) et adouci (flou gaussien, pas de
# terrasse ; variante retenue sur planche, `e12_c3_douce.py` : eau visible 99,6 % à 7 px, 97,3 % à 14 px) ; jamais sur la
# mer ni `garde` (étangs, deltas, colonies) ; la terre ne descend pas sous `plancher`.
BERGES_BASSES = True
BERGE_BASSE_PX = 8
BERGE_BASSE_RETOUR_PX = 12
BERGE_BASSE_MARGE = 0.04
BERGE_BASSE_PLAFOND = 0.20
BERGE_BASSE_FLOU = 3.0


def berges_basses(sol, niveau, mer, garde=None, plancher=None):
    """(sol, bilan) : voir BERGES_BASSES."""
    import cv2
    sol = np.asarray(sol, np.float32)
    eau = np.isfinite(niveau) & ~mer
    if not eau.any():
        return sol, {}
    d_out, lab = cv2.distanceTransformWithLabels((~eau).astype(np.uint8), cv2.DIST_L2, 5,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
    idx = np.zeros(int(lab.max()) + 1, np.int64)
    er, ec = np.nonzero(eau)
    idx[lab[er, ec]] = er * sol.shape[1] + ec
    wn = np.asarray(niveau, np.float32).ravel()[idx[lab]]
    del lab, idx
    t = np.clip((d_out - BERGE_BASSE_PX) / BERGE_BASSE_RETOUR_PX, 0, 1)
    w = t * t * (3 - 2 * t)
    baisse = (np.clip(sol - (wn - BERGE_BASSE_MARGE), 0, BERGE_BASSE_PLAFOND) * (1 - w)).astype(np.float32)
    interdit = mer | (garde if garde is not None else False)
    baisse[interdit] = 0
    if BERGE_BASSE_FLOU:
        lisse = cv2.GaussianBlur(baisse, (0, 0), BERGE_BASSE_FLOU)
        baisse = np.where(d_out <= 2, baisse, np.maximum(lisse, baisse * (d_out <= BERGE_BASSE_PX)))
        baisse[interdit] = 0
    neuf = np.where(eau, sol, sol - baisse)
    if plancher is not None:
        neuf = np.where(eau, neuf, np.maximum(neuf, np.minimum(sol, np.float32(plancher))))
    # sous l'eau : le lit au plus l'eau - BERGE_BASSE_MARGE (plafonné aussi)
    neuf = np.where(eau & ~interdit, np.minimum(neuf, np.maximum(np.asarray(niveau, np.float32) - BERGE_BASSE_MARGE,
                                                                 sol - BERGE_BASSE_PLAFOND)), neuf)
    d = sol - neuf
    b = d > 0.01
    bilan = {"u² abaissés de plus d'1 cm": round(float(b.sum()) / 144.0, 1),
             "abaissement p50 / p90 / max": [round(float(x), 3) for x in np.percentile(d[b], [50, 90, 100])] if b.any()
             else [0, 0, 0]}
    return neuf.astype(np.float32), bilan


# LES EMBOUCHURES (23.09.2026, 15 h 30, session du rendu ; relevé des Empires, `05-journal\\2026-09-23-essais-auto\\
# releve-visuel-ie.md` § 1) : chez CA, le ruban d'une rivière qui rejoint la mer PLONGE sous la surface (sommets posés sur
# l'eau : médiane +0,011, p10 -0,55, jusqu'à -1,37) ; sa fin est cachée sous le plan d'eau, sans couture. Les nôtres
# finissaient au-dessus : sommets posés sur la mer à +0,048 en médiane (76 % au-dessus de 0, jusqu'à +0,16), eau à +0,11 à
# moins d'une unité de la côte (mesure du 23.09.2026 sur la chaîne de 06 h 12). D'où deux temps :
# 1. à terre, l'eau descend vers la mer (`descente_vers_la_mer`) : plafond NIVEAU_MER + PENTE_EMBOUCHURE × distance à la mer
#    LE LONG DE L'EAU (une rivière qui longe la côte sans s'y jeter n'est pas abaissée) ; le lit suit (`creuser_doux`) et le
#    générateur ne le relève pas au plancher de la terre ni ne le noie au rivage adouci ;
# 2. la côte finale connue, l'eau posée sur la mer passe SOUS LE FOND et le ruban se prolonge sous la mer en s'effilant
#    (`plongee`) : son bord n'affleure jamais.
NIVEAU_MER = 0.0                                  # = terrain_wh1_vers_terry.NIVEAU_EAU
PENTE_EMBOUCHURE = 0.10                           # hauteur par unité de distance à la mer (10 cm par unité)
HAUTEUR_MAX_DESCENTE = 0.6                        # au-delà, le plafond ne joue plus (portée du calcul : 6 unités)
SOUS_LE_FOND = 0.02                               # l'eau posée sur la mer : 2 cm sous le fond, cachée
PROLONGE_MER = 0.85                               # décroissance du champ par pixel sous la mer (seuil en ~8 px, 0,7 u)
PROLONGE_MER_PX = 12
CHAMP_MIN_PROLONGE = 0.05                         # en dessous : hors de l'eau prolongée


def descente_vers_la_mer(niveau, mer, pas):
    """(niveau, n abaissés, distance) : à terre, l'eau ne dépasse pas NIVEAU_MER + PENTE_EMBOUCHURE × d, d = distance (px,
    8-connexe, le long de l'eau) à l'eau qui touche la mer, / `pas` px par unité ; au-delà de HAUTEUR_MAX_DESCENTE, rien."""
    eau = np.isfinite(niveau)
    portee = int(np.ceil(HAUTEUR_MAX_DESCENTE / PENTE_EMBOUCHURE * pas))
    atteint = eau & dilater(mer, 1)
    d = np.full(niveau.shape, np.inf)
    d[atteint] = 0.5                              # l'eau au contact de la mer : 4 mm au-dessus
    for k in range(1, portee + 1):
        v = dilater(atteint, 1) & eau & ~atteint
        if not v.any():
            break
        d[v] = k + 0.5
        atteint |= v
    plafond = NIVEAU_MER + PENTE_EMBOUCHURE * d / pas
    bas = eau & (niveau > plafond)
    return np.where(bas, plafond, niveau).astype(np.float32), int(bas.sum()), d


def plongee(niveau, champ, mer, fond):
    """(niveau, champ, bilan) sur la côte finale : l'eau des rivières posée sur la mer passe SOUS_LE_FOND sous le fond (et
    sous le niveau de la mer) ; le champ se prolonge sous la mer depuis l'eau (× PROLONGE_MER par pixel, sur
    PROLONGE_MER_PX au plus), à la même hauteur sous le fond : le bord du maillage n'est jamais à la surface."""
    eau = np.isfinite(niveau)
    f = np.where(eau, champ, 0.0).astype(np.float64)
    for _ in range(PROLONGE_MER_PX):
        g = _filtre(f, 3, np.maximum, 0.0) * PROLONGE_MER
        neuf = mer & ~eau & (g > f) & (g >= CHAMP_MIN_PROLONGE)
        if not neuf.any():
            break
        f = np.where(neuf, g, f)
    prolonge = mer & ~eau & (f >= CHAMP_MIN_PROLONGE)
    sous = np.minimum(NIVEAU_MER, np.asarray(fond, np.float64)) - SOUS_LE_FOND
    sur_mer = mer & (eau | prolonge)
    n = np.where(eau, niveau, np.nan).astype(np.float64)
    n = np.where(sur_mer, np.minimum(np.where(np.isfinite(n), n, np.inf), sous), n)
    bilan = {"eau posée sur la mer": int((mer & eau).sum()), "prolongée sous la mer": int(prolonge.sum()),
             "dont dans le maillage": int((prolonge & (f >= SEUIL_MAILLAGE)).sum())}
    return n.astype(np.float32), np.where(eau | prolonge, f, 0.0).astype(np.float32), bilan


# Le SENS DU COURANT (23.09.2026, 06 h 05 ; Charles : « l'eau rend bien mieux mais elle n'a pas l'air de bouger ») : le
# matériau d'eau fait couler l'eau selon son masque de flux, neutre sur nos rivières. La coordonnée « le long » des rubans
# de WH1 ne donne pas le sens : il dépend de l'orientation de chaque tuile (52 % des pixels vers l'aval, 48 % vers
# l'amont ; brouillon `rivieres/essai_flux.py`). Le sens vient donc du réseau : chaque cours d'eau coule vers son
# embouchure (la mer, sinon le point le plus bas de son morceau), les affluents vers la rivière qu'ils rejoignent :
# distance le long de l'eau jusqu'à l'embouchure, le courant descend cette distance.
FLOU_FLUX = 2.0                                   # px : lissage du champ de directions


def flux_reseau(niveau, mer, avec_distance=False):
    """(H, L, 2) float32 : direction unitaire du courant (x vers l'est, z vers le nord, repère des rasters) sur l'eau des
    rivières (`niveau` fini), NaN ailleurs ; et le nombre d'embouchures ; avec `avec_distance`, aussi la distance (px, le
    long de l'eau) à l'embouchure, NaN hors de l'eau."""
    import heapq
    eau = np.isfinite(niveau)
    H_, L_ = eau.shape
    rs, cs = np.nonzero(eau)
    n = len(rs)
    ident = np.full((H_ + 2, L_ + 2), -1, np.int64)
    ident[rs + 1, cs + 1] = np.arange(n)
    voisins = [(dy, dx, (dy * dy + dx * dx) ** 0.5) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    vois = np.stack([ident[rs + 1 + dy, cs + 1 + dx] for dy, dx, _ in voisins], 1)          # (n, 8), -1 : pas d'eau
    poids = np.array([w for _, _, w in voisins])
    # embouchures : l'eau qui touche la mer ; pour un morceau sans mer, son point le plus bas
    merp = np.pad(mer, 1)
    touche_mer = np.zeros(n, bool)
    for dy, dx, _ in voisins:
        touche_mer |= merp[rs + 1 + dy, cs + 1 + dx]
    lab = composantes(eau)[rs, cs]
    sources = set(np.nonzero(touche_mer)[0].tolist())
    niv = niveau[rs, cs]
    for l in np.unique(lab):
        membres = np.nonzero(lab == l)[0]
        if not touche_mer[membres].any():
            sources.add(int(membres[np.argmin(niv[membres])]))
    # distance le long de l'eau (Dijkstra, pas de 1 ou √2)
    dist = np.full(n, np.inf)
    tas = [(0.0, s) for s in sources]
    for _, s in tas:
        dist[s] = 0.0
    heapq.heapify(tas)
    while tas:
        d, i = heapq.heappop(tas)
        if d > dist[i]:
            continue
        for k in range(8):
            j = vois[i, k]
            if j >= 0 and d + poids[k] < dist[j]:
                dist[j] = d + poids[k]
                heapq.heappush(tas, (dist[j], j))
    D = np.full((H_, L_), np.nan)
    D[rs, cs] = dist
    # le courant descend la distance : somme des pas vers les voisins plus proches de l'embouchure
    fx, fz = np.zeros(n), np.zeros(n)
    for k, (dy, dx, w) in enumerate(voisins):
        j = vois[:, k]
        ok = j >= 0
        gain = np.where(ok, dist - np.where(ok, dist[np.maximum(j, 0)], np.inf), 0.0)
        gain = np.where(np.isfinite(gain) & (gain > 0), gain / w, 0.0)
        fx += gain * dx / w
        fz += gain * (-dy) / w                                  # une ligne vers le haut = vers le nord
    FX, FZ = np.zeros((H_, L_)), np.zeros((H_, L_))
    FX[rs, cs], FZ[rs, cs] = fx, fz
    c = flou(eau.astype(np.float64), FLOU_FLUX)
    FX, FZ = flou(FX, FLOU_FLUX) / np.maximum(c, 1e-6), flou(FZ, FLOU_FLUX) / np.maximum(c, 1e-6)
    nrm = np.hypot(FX, FZ)
    FX, FZ = np.where(eau & (nrm > 1e-9), FX / np.maximum(nrm, 1e-9), np.nan), \
        np.where(eau & (nrm > 1e-9), FZ / np.maximum(nrm, 1e-9), np.nan)
    if avec_distance:
        return np.dstack([FX, FZ]).astype(np.float32), len(sources), D
    return np.dstack([FX, FZ]).astype(np.float32), len(sources)


# LE COURANT DES ÉTANGS ET DES EMBOUCHURES (24.09.2026, 05 h, chaîne 11 ; Charles : « l'eau ne bouge pas », les lacs de WH1
# ondulent ; accord de la session IA, qui a écrit sa part dans `masques_eau_carte`). Le masque de flux du matériau d'eau ne
# recevait de direction que sur les rivières : les étangs avaient un flux nul (normales immobiles) et la mer reprenait son
# courant vers l'est dès l'embouchure, à contre-sens des rivières qui coulent vers l'ouest. `flux_etangs_et_panaches`
# complète `flux_reseau` : chaque étang prend le courant moyen des rivières qui le touchent (à ETANG_VOISINAGE_PX près),
# sinon une dérive vers l'est tournée d'au plus ETANG_ECART degrés (graine par étang) ; dans la mer, la direction de chaque
# rivière est prolongée sur PANACHE_UNITES depuis son embouchure (de proche en proche, moyenne des voisins déjà posés).
# `masques_eau_carte` pondère : norme des lacs FLUX_LAC_NORME, panache fondu de 1 à la côte à 0 à FLUX_PANACHE_UNITES.
ETANG_VOISINAGE_PX = 3
ETANG_ECART = 25.0                                # degrés
PANACHE_UNITES = 4.0
PANACHE_FENETRE = 256                             # px : fenêtres de calcul autour des embouchures


def _prolonger_directions(e, n, pose, zone, k_max):
    """Directions (e, n) posées sur `pose`, prolongées de proche en proche dans `zone` sur k_max pixels (moyenne des
    voisins déjà posés, 8-connexe) ; rend le masque des pixels ajoutés."""
    ajout = np.zeros(pose.shape, bool)
    for _ in range(k_max):
        pe, pn, pp = np.pad(e, 1), np.pad(n, 1), np.pad(pose, 1)
        h, w = pose.shape
        se, sn, cpt = np.zeros((h, w)), np.zeros((h, w)), np.zeros((h, w))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    p = pp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
                    se += np.where(p, pe[1 + dy:1 + dy + h, 1 + dx:1 + dx + w], 0.0)
                    sn += np.where(p, pn[1 + dy:1 + dy + h, 1 + dx:1 + dx + w], 0.0)
                    cpt += p
        l = np.hypot(se, sn)
        ok = zone & ~pose & (cpt > 0) & (l > 1e-6)
        if not ok.any():
            break
        e = np.where(ok, se / np.where(ok, l, 1.0), e)
        n = np.where(ok, sn / np.where(ok, l, 1.0), n)
        pose = pose | ok
        ajout |= ok
    return e, n, ajout


def flux_etangs_et_panaches(flux, eau_etangs, mer, pas):
    """(flux, bilan) : `flux` (H, L, 2) de `flux_reseau` (x vers l'est, z vers le nord, NaN hors de l'eau) complété sur
    les étangs (`eau_etangs`) et prolongé dans la mer (`mer`) depuis les embouchures ; `pas` px par unité."""
    import zlib
    out = np.array(flux, np.float32, copy=True)
    valide = np.isfinite(out[..., 0]) & np.isfinite(out[..., 1])
    H_, L_ = valide.shape
    bilan = {"étangs": 0, "orientés par une rivière": 0, "dérive vers l'est": 0, "px d'étang": 0, "px de panache": 0}
    etangs = np.asarray(eau_etangs, bool) if eau_etangs is not None else np.zeros((H_, L_), bool)
    if etangs.any():
        lab = composantes(etangs)
        for l in np.unique(lab[lab >= 0]):
            rr, cc = np.nonzero(lab == l)
            v = ETANG_VOISINAGE_PX
            r0, r1 = max(rr.min() - v, 0), min(rr.max() + v + 1, H_)
            c0, c1 = max(cc.min() - v, 0), min(cc.max() + v + 1, L_)
            m = lab[r0:r1, c0:c1] == l
            proche = dilater(m, v) & valide[r0:r1, c0:c1]
            vec = out[r0:r1, c0:c1][proche].astype(np.float64)
            moy = vec.mean(0) if len(vec) else np.zeros(2)
            if np.hypot(*moy) > 0.2:
                d = moy / np.hypot(*moy)
                bilan["orientés par une rivière"] += 1
            else:
                t = zlib.crc32(f"etang:{int(rr[0])}:{int(cc[0])}".encode()) / 2.0 ** 32
                a = np.radians(ETANG_ECART * (2.0 * t - 1.0))
                d = np.array([np.cos(a), np.sin(a)])
                bilan["dérive vers l'est"] += 1
            pose = m & ~valide[r0:r1, c0:c1]
            bloc = out[r0:r1, c0:c1]
            bloc[pose] = d.astype(np.float32)
            bilan["étangs"] += 1
            bilan["px d'étang"] += int(pose.sum())
    mer = np.asarray(mer, bool)
    k_max = int(round(PANACHE_UNITES * pas))
    depart = valide & dilater(mer, 1)
    fait = np.zeros((H_, L_), bool)
    F = PANACHE_FENETRE
    for i0 in range(0, H_, F):
        for j0 in range(0, L_, F):
            if not depart[i0:i0 + F, j0:j0 + F].any():
                continue
            a0, a1 = max(i0 - k_max - 1, 0), min(i0 + F + k_max + 1, H_)
            b0, b1 = max(j0 - k_max - 1, 0), min(j0 + F + k_max + 1, L_)
            dep = np.zeros((a1 - a0, b1 - b0), bool)
            dep[i0 - a0:i0 - a0 + F, j0 - b0:j0 - b0 + F] = depart[i0:i0 + F, j0:j0 + F]
            e = np.where(dep, out[a0:a1, b0:b1, 0], 0.0).astype(np.float64)
            n = np.where(dep, out[a0:a1, b0:b1, 1], 0.0).astype(np.float64)
            zone = mer[a0:a1, b0:b1] & ~valide[a0:a1, b0:b1] & ~fait[a0:a1, b0:b1]
            e, n, ajout = _prolonger_directions(e, n, dep, zone, k_max)
            out[a0:a1, b0:b1, 0] = np.where(ajout, e, out[a0:a1, b0:b1, 0])
            out[a0:a1, b0:b1, 1] = np.where(ajout, n, out[a0:a1, b0:b1, 1])
            fait[a0:a1, b0:b1] |= ajout
    bilan["px de panache"] = int(fait.sum())
    return out, bilan


# marching squares : coins du carré (a = (i, j), b = (i, j+1), c = (i+1, j+1), d = (i+1, j)) et arêtes, dans l'ordre du
# tour ; chaque cas donne un polygone convexe (points sur le bord du carré, dans l'ordre), triangulé en éventail. Les deux
# cas « en selle » relient les coins d'eau (l'eau reste d'un seul tenant).
_TOUR = (("n", 0, 0, 1), ("h", 0, 0, (1, 2)), ("n", 0, 1, 2), ("v", 0, 1, (2, 4)),
         ("n", 1, 1, 4), ("h", 1, 0, (4, 8)), ("n", 1, 0, 8), ("v", 0, 0, (8, 1)))


def _polygones():
    out = {}
    for cas in range(1, 16):
        pts = []
        for genre, di, dj, bits in _TOUR:
            if genre == "n":
                if cas & bits:
                    pts.append((genre, di, dj))
            elif bool(cas & bits[0]) != bool(cas & bits[1]):
                pts.append((genre, di, dj))
        out[cas] = pts
    return out


# LE LONG DE LA RIVIÈRE (23.09.2026, 18 h 55, session du rendu ; Charles : « les rivières n'ont pas l'air de bouger »).
# Relevé des rubans d'eau des Empires (`05-journal\\2026-09-23-rendu-carte\\gabarits-ca\\rapport-sources-rivieres.md`) :
# v = 0,1 x l'abscisse le long de la rivière, croissante vers l'aval (159 rubans sur 178), u = ±largeur x 0,05 (presque
# constant d'une rive à l'autre). Les nôtres étaient projetés à plat (u = 0,1 x, v = 0,1 z) : leur « aval » pointait au
# nord partout, parfois à contre-courant. Désormais v = -0,1 x la distance à l'embouchure le long de l'eau (celle de
# `flux_reseau`), u = UV_TRAVERS x (1 - champ), et le repère de chaque sommet suit le courant (tangente vers la droite du
# courant, bitangente vers l'aval : le repère des Empires pour un courant vers le nord).
UV_LE_LONG = True
UV_TRAVERS = 0.02


def _octets_dir(c):
    """Composante d'un vecteur unitaire -> octet du repère des sommets (0x7F = 0, 0xFF = +1, 0x00 = -1)."""
    return np.clip(np.rint((np.asarray(c) + 1.0) * 127.5), 0, 255).astype(np.uint8)


def construire_lisse(niveau, champ, pas, ecrire=False, mer=None):
    """(entités, fichiers) : l'eau des rivières jusqu'à la courbe de niveau SEUIL_MAILLAGE du champ (marching squares sur
    les centres des pixels, sommets des arêtes interpolés), à la hauteur `niveau` ; maillages de TUILE_EAU px. Avec `mer`
    (et UV_LE_LONG), coordonnées de texture et repères le long du courant."""
    from contenu_pack import SourcePacks, chemins_du_jeu
    gabarit = SourcePacks(DATA_WH3).lire(GABARIT)
    if gabarit is None or struct.unpack_from("<I", gabarit, 4)[0] != 8:
        raise SystemExit(f"gabarit {GABARIT} illisible")
    jeu = chemins_du_jeu(DATA_WH3)
    H_, L_ = niveau.shape
    eau = np.isfinite(niveau)
    f = np.where(eau, champ, 0.0).astype(np.float64)          # hors de l'eau : dehors, quel que soit le champ
    le_long = UV_LE_LONG and mer is not None
    if le_long:
        flux, _, dist = flux_reseau(niveau, mer, avec_distance=True)
        fx = np.nan_to_num(flux[..., 0], nan=0.0)
        fz = np.nan_to_num(flux[..., 1], nan=1.0) * Z_VERS_MONDE          # repère des rasters -> monde (z x 2/√3)
        nrm = np.maximum(np.hypot(fx, fz), 1e-9)
        fx, fz = fx / nrm, fz / nrm
        dist = np.where(np.isfinite(dist), dist, 0.0)
    y = _prolonger(niveau, dilater(eau, 1), 2)                # hauteur aussi aux voisins, pour les arêtes
    y = np.where(np.isfinite(y), y, 0.0)
    dedans = f >= SEUIL_MAILLAGE
    cas = (dedans[:-1, :-1] * 1 + dedans[:-1, 1:] * 2 + dedans[1:, 1:] * 4 + dedans[1:, :-1] * 8).astype(np.int8)
    polys = _polygones()
    NN = H_ * L_
    decalage = {"n": 0, "h": NN, "v": 2 * NN}

    def position(ids, avec_pixel=False):
        genre, reste = ids // NN, ids % NN
        ii, jj = reste // L_, reste % L_
        i, j = ii.astype(np.float64), jj.astype(np.float64)
        hy = y[ii, jj].copy()
        pi, pj = ii.copy(), jj.copy()                           # le pixel d'eau (dedans) du sommet
        for g, di, dj in ((1, 0, 1), (2, 1, 0)):              # arête horizontale (i, j)-(i, j+1), verticale (i, j)-(i+1, j)
            sel = genre == g
            a, b = f[ii[sel], jj[sel]], f[ii[sel] + di, jj[sel] + dj]
            t = np.clip((SEUIL_MAILLAGE - a) / np.where(b != a, b - a, 1.0), 0, 1)
            i[sel] += t * di
            j[sel] += t * dj
            hy[sel] = y[ii[sel], jj[sel]] * (1 - t) + y[ii[sel] + di, jj[sel] + dj] * t
            autre = b > a
            pi[np.nonzero(sel)[0][autre]] += di
            pj[np.nonzero(sel)[0][autre]] += dj
        x = (j + 0.5) / pas                                     # centres des pixels, comme `Sol.sous`
        zr = (H_ - 1.5 - i) / pas
        p = np.c_[x, hy, zr * Z_VERS_MONDE]
        return (p, pi, pj) if avec_pixel else p

    fichiers, entites = {}, []
    ntri = 0
    for r0 in range(0, H_ - 1, TUILE_EAU):
        for c0 in range(0, L_ - 1, TUILE_EAU):
            bloc = cas[r0:r0 + TUILE_EAU, c0:c0 + TUILE_EAU]
            if not bloc.any():
                continue
            tris = []
            for k, pts in polys.items():
                ri, ci = np.nonzero(bloc == k)
                if not len(ri):
                    continue
                ri, ci = ri + r0, ci + c0
                ids = np.stack([decalage[g] + (ri + di) * L_ + (ci + dj) for g, di, dj in pts], 1)
                for m in range(1, len(pts) - 1):
                    tris.append(np.c_[ids[:, 0], ids[:, m], ids[:, m + 1]])
            tris = np.concatenate(tris)
            uniq, inv = np.unique(tris, return_inverse=True)
            t = inv.reshape(-1, 3)
            pos, pi, pj = position(uniq, avec_pixel=True)
            pa, pb, pc = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
            ny = (pb[:, 2] - pa[:, 2]) * (pc[:, 0] - pa[:, 0]) - (pb[:, 0] - pa[:, 0]) * (pc[:, 2] - pa[:, 2])
            t = np.where((ny < 0)[:, None], t[:, [0, 2, 1]], t)
            if len(pos) > 65535:
                raise SystemExit(f"maillage d'eau {r0},{c0} : {len(pos)} sommets (index sur 16 bits)")
            ntri += len(t)
            centre = (pos.min(0) + pos.max(0)) / 2
            nom = f"river_wh1_c{r0 // TUILE_EAU:02d}_{c0 // TUILE_EAU:02d}"
            geometrie = f"{DOSSIER_MODELES}/{nom}.wsmodel.rigid_model_v2"
            modele = f"{DOSSIER_MODELES}/{nom}.wsmodel"
            if geometrie in jeu or modele in jeu:
                raise SystemExit(f"{modele} existe dans WH3")
            if le_long:
                dx, dz = fx[pi, pj], fz[pi, pj]
                u = UV_TRAVERS * (1.0 - np.clip(f[pi, pj], 0, 1))
                v = -ECHELLE_UV_EAU * dist[pi, pj] / pas
                # tangente vers la droite du courant (dz, 0, -dx), bitangente vers l'aval (dx, 0, dz)
                reperes = (np.c_[_octets_dir(dz), np.full(len(dz), 0x7F, np.uint8), _octets_dir(-dx)],
                           np.c_[_octets_dir(dx), np.full(len(dz), 0x7F, np.uint8), _octets_dir(dz)])
                fichiers[geometrie] = rmv2(gabarit, pos - centre, u, v, t, reperes)
            else:
                fichiers[geometrie] = rmv2(gabarit, pos - centre, pos[:, 0] * ECHELLE_UV_EAU, pos[:, 2] * ECHELLE_UV_EAU, t)
            fichiers[modele] = wsmodel(geometrie).encode("utf-8")
            entites.append(entite(ident(f"riviere_lisse:{nom}"), modele, tuple(centre)))
    print(f"rivières de WH1 (eau lisse) : {len(entites)} maillages, {ntri} triangles, {int(eau.sum())} px d'eau ; "
          f"{sum(len(v) for v in fichiers.values()) / 1e6:.1f} Mo")
    if ecrire:
        if os.path.isdir(SORTIE):                # sortie générée, embarquée par build_pack : refaite à chaque fois
            shutil.rmtree(SORTIE)
        for racine in (SORTIE, KIT_WD):
            for c, octets in fichiers.items():
                chemin = os.path.join(racine, *c.split("/"))
                os.makedirs(os.path.dirname(chemin), exist_ok=True)
                with open(chemin, "wb") as fo:
                    fo.write(octets)
        print(f"écrits dans {SORTIE} et {KIT_WD}")
    return entites, fichiers


def sommets_wh3(pos, u, v, reperes=None):
    """Sommets de 48 octets du gabarit : position (x, y, z, 1), uv (u, v), uv (0, 0), normale, tangente, bitangente, 0.
    `reperes` : (tangentes, bitangentes) en octets (n, 3) par sommet ; sinon le repère plan du gabarit (x, z)."""
    n = len(pos)
    out = np.zeros((n, 48), np.uint8)
    f = np.zeros((n, 8), "<f4")
    f[:, :3] = pos
    f[:, 3] = 1.0
    f[:, 4], f[:, 5] = u, v
    out[:, :32] = f.view(np.uint8).reshape(n, 32)
    out[:, 32:36] = np.frombuffer(NORMALE_HAUT, np.uint8)
    if reperes is None:
        out[:, 36:40] = np.frombuffer(TANGENTE_X, np.uint8)
        out[:, 40:44] = np.frombuffer(BITANGENTE_Z, np.uint8)
    else:
        tg, bt = reperes
        out[:, 36:39], out[:, 40:43] = tg, bt
        out[:, 39] = TANGENTE_X[3]
        out[:, 43] = BITANGENTE_Z[3]
    return out.tobytes()


def rmv2(gabarit, pos, u, v, t, reperes=None):
    """RMV2 v8 d'un morceau « River » au format du gabarit des Empires : positions centrées sur leur boîte (centre écrit à
    +628, comme chez CA), un LOD. `pos` dans le repère du modèle."""
    off = struct.unpack_from("<I", gabarit, 152)[0]
    _mat, _u, _taille, voff, _vc, _ioff, _ic = struct.unpack_from("<HHIIIII", gabarit, off)
    lo, hi = pos.min(0), pos.max(0)
    centre = (lo + hi) / 2
    tete_f = bytearray(gabarit[:off])
    tete_m = bytearray(gabarit[off:off + voff])
    nvc, nic = len(pos), t.size
    taille = voff + nvc * 48 + nic * 2
    struct.pack_into("<IIIII", tete_m, 4, taille, voff, nvc, voff + nvc * 48, nic)
    struct.pack_into("<6f", tete_m, 24, *(lo - centre), *(hi - centre))
    struct.pack_into("<I", tete_m, 68, taille)
    struct.pack_into("<3f", tete_m, 628, *centre)
    struct.pack_into("<II", tete_f, 144, nvc * 48, nic * 2)
    return bytes(tete_f) + bytes(tete_m) + sommets_wh3(pos - centre, u, v, reperes) + t.astype("<u2").tobytes()


def wsmodel(geometrie):
    return ('<model version="1">\n\n  <geometry>' + geometrie + '</geometry>\n\n  <materials>\n\n'
            f'    <material lod_index="0" part_index="0">{MATERIAU_EAU}</material>\n\n  </materials>\n\n</model>\n')


def entite(ident_, modele, position):
    """Entité d'objet de rivière, réglée comme les rivières des Empires (`river_*.wsmodel` posés en ECMesh)."""
    x, y, z = position
    return (f'\t\t<entity id="{ident_}">\n'
            '\t\t\t<ECPropMesh/>\n'
            f'\t\t\t<ECMesh model_path="{modele}" opacity="1"/>\n'
            '\t\t\t<ECMeshRenderSettings receive_decals="False"/>\n'
            '\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="False" visible_in_tactical_view_only="False"/>\n'
            '\t\t\t<ECPropHeightPatch apply_height_patch="False" for_camera_height_map_only="false"/>\n'
            '\t\t\t<ECCampaignProperties visible_inside_snow_region="True" visible_outside_snow_region="True" '
            'visible_inside_destruction_region="True" visible_outside_destruction_region="True" '
            # comme 200 des 206 rivières des Empires (audit de la session « IA et modding 3D », 23.09.2026)
            'visible_in_shroud="True" visible_in_shroud_only="False" no_culling="True" culture_mask=""/>\n'
            f'\t\t\t<ECTransform position="{x:.5f} {y:.5f} {z:.5f}" rotation="0. 0. 0." scale="1. 1. 1." pivot="0 0 0"/>\n'
            '\t\t</entity>\n')


def construire(ecrire=False, liste=None):
    """(entités, fichiers {chemin: octets}) des rubans d'eau de WH1, drapés sur le relief de base."""
    import relief_maillages_wh1 as R
    from modeles_wh1 import SourceWH1
    from contenu_pack import SourcePacks, chemins_du_jeu
    wh1 = SourceWH1()
    gabarit = SourcePacks(DATA_WH3).lire(GABARIT)
    if gabarit is None or struct.unpack_from("<I", gabarit, 4)[0] != 8:
        raise SystemExit(f"gabarit {GABARIT} illisible")
    jeu = chemins_du_jeu(DATA_WH3)
    lf = R.relief_lf().astype(np.float64)
    sol = Sol(lf, R.PAS)
    cache, fichiers, entites = {}, {}, []
    sans = 0
    for p in (liste if liste is not None else poses()):
        if p.nom not in cache:
            cache[p.nom] = morceaux(wh1.lire(p.nom + "mesh.rigid_model_v2"))
        eaux = cache[p.nom].get(MAT_EAU, [])
        if not eaux:
            sans += 1
            continue
        pos, us, vs, tris, base = [], [], [], [], 0
        for v, t in eaux:
            vx, vy, vz = (v[:, 0] * ECHELLE_RUBAN, v[:, 1] * ECHELLE_RUBAN, v[:, 2] * ECHELLE_RUBAN)
            wx, wz = vers_raster(p, vx, vz)
            wy = sol.sous(wx, wz) + M.BASE + M.S * vy
            pos.append(np.c_[wx, wy, wz * Z_VERS_MONDE])
            us.append((v[:, 6] - 0.5) * 0.1)             # travers : ±0,05, comme le gabarit
            vs.append(v[:, 7])                           # le long
            tris.append(t + base)
            base += len(v)
        pos = np.concatenate(pos)
        t = np.concatenate(tris)
        # le quart de tour de la pose peut retourner les triangles : on les garde tournés vers le haut
        a, b_, c = pos[t[:, 0]], pos[t[:, 1]], pos[t[:, 2]]
        ny = (b_[:, 2] - a[:, 2]) * (c[:, 0] - a[:, 0]) - (b_[:, 0] - a[:, 0]) * (c[:, 2] - a[:, 2])
        t = np.where((ny < 0)[:, None], t[:, [0, 2, 1]], t)
        centre = (pos.min(0) + pos.max(0)) / 2
        nom = f"river_wh1_{p.k}"
        geometrie = f"{DOSSIER_MODELES}/{nom}.wsmodel.rigid_model_v2"
        modele = f"{DOSSIER_MODELES}/{nom}.wsmodel"
        if geometrie in jeu or modele in jeu:
            raise SystemExit(f"{modele} existe dans WH3")
        fichiers[geometrie] = rmv2(gabarit, pos - centre, np.concatenate(us), np.concatenate(vs), t)
        fichiers[modele] = wsmodel(geometrie).encode("utf-8")
        entites.append(entite(ident(f"riviere:{p.k}"), modele, tuple(centre)))
    print(f"rivières de WH1 : {len(entites)} rubans d'eau ({sans} poses sans eau) ; {len(fichiers)} fichiers, "
          f"{sum(len(v) for v in fichiers.values()) / 1e6:.1f} Mo")
    if ecrire:
        if liste is None and os.path.isdir(SORTIE):
            shutil.rmtree(SORTIE)
        for racine in (SORTIE, KIT_WD):
            for c, octets in fichiers.items():
                chemin = os.path.join(racine, *c.split("/"))
                os.makedirs(os.path.dirname(chemin), exist_ok=True)
                with open(chemin, "wb") as f:
                    f.write(octets)
        print(f"écrits dans {SORTIE} et {KIT_WD}")
    return entites, fichiers


def essai(x, z, rayon):
    """Essai dans Terry : les rubans des poses à moins de `rayon` du point (x, z) du monde, écrits dans working_data
    seulement (jamais dans le dossier embarqué par build_pack), et un calque `rivieres_wh1_essai` ajouté au projet
    (sauvegardé d'abord)."""
    import time
    toutes = poses()
    choisies = []
    for p in toutes:
        cx, cz = vers_raster(p, np.array([64.0 * p.W]), np.array([64.0 * p.H]))
        if math.hypot(cx[0] - x, cz[0] * Z_VERS_MONDE - z) < rayon:
            choisies.append(p)
    entites, fichiers = construire(ecrire=False, liste=choisies)
    for c, octets in fichiers.items():
        chemin = os.path.join(KIT_WD, *c.split("/"))
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "wb") as f:
            f.write(octets)
    projet = M.PROJET
    terry = os.path.join(projet, f"{CARTE}.terry")
    dest = os.path.join(ATELIER, "05-journal", "terrain-backups", "terry-avant-rivieres-" + time.strftime("%Y%m%d-%H%M%S") + ".terry")
    shutil.copy(terry, dest)
    id_calque = ident("calque:rivieres_wh1_essai")
    with open(os.path.join(projet, f"{CARTE}.{id_calque}.layer"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- rivieres_wh1_essai -->\n<layer version="41">\n\t<entities>\n'
                + "".join(entites) + "\t</entities>\n\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    t = open(terry, encoding="utf-8").read()
    if id_calque not in t:
        bloc = (f'      <entity id="{id_calque}" name="rivieres_wh1_essai">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
        t = t.replace("    </data>\n  </pc>\n  <pc type=\"QTU::Terrain\">", bloc + "    </data>\n  </pc>\n  <pc type=\"QTU::Terrain\">", 1)
        if id_calque not in t:
            raise SystemExit("point d'insertion du calque introuvable dans le .terry")
        with open(terry, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
    print(f"essai : {len(choisies)} poses autour de ({x}, {z}) ; .terry sauvegardé dans {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", help="x,z,rayon : quelques rubans dans un calque d'essai du projet Terry")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.essai:
        x, z, r = (float(v) for v in a.essai.split(","))
        essai(x, z, r)
    else:
        construire()
    return 0


if __name__ == "__main__":
    sys.exit(main())
