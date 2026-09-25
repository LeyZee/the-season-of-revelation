#!/usr/bin/env python3
"""
deltas_wh1.py - les deltas de Warhammer 1, repris tels quels (session du rendu, chaîne 12).

Pourquoi (24.09.2026, 18 h 50 ; Charles, capture en jeu du pack 9.0 : « il faut toujours travailler sur les embouchures,
comment les rivières se jettent dans la mer avec leur joli delta comme sur Warhammer 1 » ; 18 h 55 : « fais exactement
comme dans Warhammer 1, ne te prends pas la tête à réinventer la roue, il faut juste l'adapter dans Warhammer 3 »).
Relevé (brouillons `estuaire_wh1.py`, `inventaire_deltas.py`, planche `inventaire_deltas.png`) : WH1 a trois deltas, ses
tuiles d'embouchure (`river_mouth`, 419 cases) : l'estuaire près d'Yremy (50, 250), l'anse au nord de Bordeleaux
(28, 189), la baie au sud de Brionne (17, 129), en patte d'oie. Chacun : un éventail de maillages de mer dont le fond
monte au-dessus de 0 (bancs de sable, jusqu'à +0,11), des îlots de terre, et les rubans d'eau de la rivière à leur
hauteur (+0,12 à +0,15) qui s'étalent en 5 à 8 bras sur l'éventail et au-dessus de la mer. La chaîne 11 les avait
effacés (bancs rendus à la terre par `rivage_naturel`, rivières abaissées au niveau de la mer et plongées dessous).

Ce que fait ce module, dans la zone des tuiles d'embouchure (élargie de DILATATION_PX) :
- `bancs` : le fond de WH1 au-dessus de BANC_MIN hors de ses maillages de terre devient de la terre, à la hauteur de ce
  fond (ses bancs de sable) ; le reste de l'éventail reste de la mer, au fond de WH1 (ni approfondi, ni adouci) ;
- `eau` : l'eau de la rivière y est celle des rubans de WH1, à leur hauteur, sans creusement (l'eau de WH1 passe 2 à
  4 cm au-dessus de ses bancs) ; la chaîne ne l'abaisse pas vers la mer et ne la plonge pas dessous (comme WH1).

Usage (module, `terrain_wh1_vers_terry.rasters`) :
    zone = deltas_wh1.zone(H, L)
    banc = deltas_wh1.bancs(zone, fond_w, terre_w)
    niveau, champ = deltas_wh1.eau(zone, rubans)
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ACTIF = True
FAMILLE = "river_mouth"
DILATATION_PX = 2              # la zone : les tuiles d'embouchure de WH1 et 2 px autour
BANC_MIN = 0.0                 # fond de WH1 au-dessus duquel l'éventail est un banc de sable (terre)
FLOU_BORD = 0.7                # px : bord du maillage d'eau adouci (les rubans de WH1 font 1 à 3 px)
PROLONGE_PX = 2                # la hauteur de l'eau prolongée sous le bord adouci du maillage
# LES DELTAS SANS MARCHES (25.09.2026, 01 h, chaîne 14 ; Charles, capture du pack de 00 h 28 au delta d'Yremy : « les deltas
# et les contacts entre la mer et les rivières, comme elles se jettent dans la mer, c'est pas encore ça », escalier de cases
# autour du delta, bancs bruns rectangulaires, nappe claire des bras posée sur la mer). Figés au pixel de WH1 (chaîne 13),
# les deltas gardaient les marches de ses cases de 0,33 u, que le jeu montre de loin comme la côte (erreur 223) ; les bancs
# suivaient les bords droits de ses tuiles ; l'eau de ses rubans (+0,11 à +0,15) restait une nappe au-dessus de la mer.
# Désormais : bancs lissés (LISSE_BANCS_PX, seuil à mi-hauteur : les formes de WH1 arrondies, pas déplacées) ; eau des bras
# gardée sur les bancs et la terre seulement (sur la mer, c'est la mer qui se voit, EAU_SUR_MER = False), descendue vers le
# niveau de la mer à PENTE_VERS_MER par unité le long de l'eau (plus de marche de 11 cm au bord de l'eau). Le trait de côte
# autour du delta est lissé à part, plus doucement que la côte (`cotes_wh1.LISSAGE_DELTAS_PX`).
LISSE_BANCS_PX = 1.5
# (25.09.2026, chaîne 15, C4) les bancs au moins à cette hauteur (ceux de WH1 : +0,8 à +3,3 cm en médiane, bordés d'écume par
# le matériau de la mer de WH3 ; enquête `scratchpad\enquete_rivieres\e10_delta.json`)
BANC_HAUT_MIN = 0.05
EAU_SUR_MER = False
PENTE_VERS_MER = 0.10


def _dilater(m, n):
    for _ in range(n):
        p = np.pad(m, 1)
        out = m.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                out |= p[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]]
        m = out
    return m


def zone(H, L):
    """Pixels des tuiles d'embouchure de WH1, élargis de DILATATION_PX (grille du relief, ligne 0 au nord)."""
    import tuiles_wh1
    fam = tuiles_wh1.familles_par_case(ordre=[FAMILLE])
    k = H // fam.shape[0]
    z = np.repeat(np.repeat(fam == FAMILLE, k, 0), k, 1)[:H, :L]
    if z.shape != (H, L):
        z = np.pad(z, ((0, H - z.shape[0]), (0, L - z.shape[1])))
    return _dilater(z, DILATATION_PX)


def bancs(z, fond_w, terre_w):
    """Bancs de sable de WH1 : dans la zone, fond de ses maillages de mer au-dessus de BANC_MIN, hors de ses maillages de
    terre."""
    b = z & np.isfinite(fond_w) & ~np.isfinite(terre_w) & (np.nan_to_num(fond_w, nan=-9.0) >= BANC_MIN)
    if LISSE_BANCS_PX:
        import rivieres_wh1 as RW
        b = (RW.flou(b.astype(np.float64), LISSE_BANCS_PX) >= 0.5) & z & np.isfinite(fond_w) & ~np.isfinite(terre_w)
    return b


def eau(z, rubans, mer=None, pas=None):
    """(niveau, champ) dans la zone : hauteur des rubans d'eau de WH1 (prolongée de PROLONGE_PX sous le bord adouci),
    champ 0..1 de leur emprise au bord adouci (FLOU_BORD) ; NaN et 0 hors des rubans et hors de la zone. Avec `mer` (et
    EAU_SUR_MER faux) : rien sur la mer, et l'eau descend vers elle (PENTE_VERS_MER par unité le long de l'eau, `pas` px
    par unité)."""
    import rivieres_wh1 as RW
    r = np.where(z, np.asarray(rubans, np.float64), np.nan)
    dedans = np.isfinite(r)
    champ = RW.flou(dedans.astype(np.float64), FLOU_BORD) if FLOU_BORD > 0 else dedans.astype(np.float64)
    champ = np.where(z, np.clip(champ / max(float(champ[dedans].max()) if dedans.any() else 1.0, 1e-6), 0, 1), 0.0)
    autour = _dilater(dedans, PROLONGE_PX) & z
    niveau = RW._prolonger(r, autour, PROLONGE_PX)
    niveau = np.where(autour, niveau, np.nan)
    if mer is not None and not EAU_SUR_MER:
        niveau = np.where(mer, np.nan, niveau)
        eau_ = np.isfinite(niveau)
        if eau_.any() and pas:
            # distance le long de l'eau depuis le bord de la mer (px, pas de proche en proche), plafond qui monte avec elle
            d = np.full(niveau.shape, np.inf)
            front = eau_ & _dilater(mer, 1)
            d[front] = 1.0
            atteint = front.copy()
            for k in range(2, int(2.0 * pas) + 2):
                v = _dilater(atteint, 1) & eau_ & ~atteint
                if not v.any():
                    break
                d[v] = k
                atteint |= v
            plafond = RW.NIVEAU_MER + 0.005 + PENTE_VERS_MER * d / pas
            niveau = np.where(eau_, np.minimum(niveau, plafond), np.nan)
    return niveau, np.where(np.isfinite(niveau), champ, 0.0)
