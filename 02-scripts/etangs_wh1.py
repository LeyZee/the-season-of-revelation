#!/usr/bin/env python3
"""
etangs_wh1.py - les lacs de WH1 en vrais étangs : contour naturel, cuvette et berge dans le relief, niveau accordé aux
rivières qui les traversent.

Pourquoi (23.09.2026, session du rendu ; Charles : « les lacs ne sont pas assez bien reliés aux rivières, ce n'est pas
cohérent » ; « attaque tout ça »). Relevé des Empires (`05-journal\\2026-09-23-essais-auto\\releve-visuel-ie.md` § 1) :
nos 26 lacs sont les plans d'eau de WH1 (`generic_props/terrain/water_plane`, carrés de 1,1 à 4,7 unités) devenus des
polygones d'eau carrés (`props_wh1_vers_layers.entite_eau`) ; 18 ont plus d'un quart du bord au-dessus du sol (arête
droite qui flotte, jusqu'à 1 unité) ; plusieurs sont des élargissements de rivière 20 à 40 cm au-dessus de l'eau de la
rivière. Chez CA, un étang en altitude est un polygone irrégulier dont le bord est enterré (47 à 100 % du contour sous le
sol), et une rivière y finit 1 à 4 cm sous l'étang, en le chevauchant. Planche du 23.09.2026 (brouillon de la session du
rendu, `lacs_planche.png`) : la plupart des lacs de WH1 sont de petites cuvettes, plus petites que leur carré ; quatre
groupes sont des bassins étagés sur une rivière, avec les cascades de WH1 entre eux.

Méthode, lac par lac (les plans d'eau qui se touchent forment un groupe partagé en cellules : chaque bassin reste dans
la sienne, une berge sépare deux niveaux, là où WH1 a ses cascades) :
1. forme : la cuvette de notre sol sous le niveau du lac, dans l'ellipse inscrite au carré de WH1 (une ellipse réduite
   si la cuvette manque), lissée, rendue étoilée depuis son centre (N_POINTS rayons) ;
2. niveau : celui de WH1 ; si une rivière traverse le bassin, celui de son eau à la sortie (p10 dans le bassin) +
   DESSUS_RIVIERE, jamais au-dessus de WH1 ; si la berge à relever dépasse RELEVE_MAX, le niveau descend d'autant ;
3. rivières (`rivieres_vers_etangs`, avant le creusement de leur lit) : dans le bassin, leur eau passe DESSOUS_ETANG sous
   l'étang ; en amont, elle descend vers lui (PENTE_ETANG le long de l'eau) ;
4. relief (`creuser`, après le lit des rivières) : cuvette (PROF_BORD au rivage, PROF_CENTRE au-delà de TALUS_PX), berge
   à niveau + REBORD sur BERGE_PX, fondue dans le sol sur FONDU_PX, jamais sur le lit d'une rivière ni dans un autre
   bassin ;
5. eau (`entite`) : le contour élargi de MARGE_EAU_PX, son bord sous la berge ; polygone de N_POINTS points, rotation
   nulle.

Repère : rasters à pixels carrés (ligne 0 au nord) ; le monde des entités est l'espace des hex, z × 2/√3 (erreur 89) ;
les formes sont calculées dans le monde, testées au centre des pixels.

Usage (module, appelé par `terrain_wh1_vers_terry.rasters`) ; seul : bilan à blanc sur le relief du projet en place.
    python etangs_wh1.py
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ACTIF = True
R3 = 3 ** 0.5 / 2
LARGEUR_MONDE = 266.53
N_POINTS = 32
ELLIPSE = 0.9                 # ellipse inscrite au carré de WH1 (fraction des demi-côtés)
ELLIPSE_REPLI = 0.6           # sans cuvette : ellipse réduite
AIRE_MIN = 0.3                # cuvette plus petite que cette part de l'ellipse : ellipse réduite
TOLERANCE_CUVETTE = 0.02      # le sol jusqu'à 2 cm au-dessus du niveau compte dans la cuvette (il sera creusé)
ECART_CELLULE = 0.15          # entre deux carrés d'un groupe (distance normalisée) : la berge qui les sépare
RAYON_MIN = 0.25              # unités
RIVIERE_MIN_PX = 15           # pixels d'eau de rivière dans le bassin pour y accorder le niveau
DESSUS_RIVIERE = 0.02         # l'étang 2 cm au-dessus de l'eau de la rivière à sa sortie
DESSOUS_ETANG = 0.02          # l'eau des rivières dans l'étang : 2 cm dessous (CA : 1 à 4 cm)
PENTE_ETANG = 0.15            # l'eau des rivières en amont descend vers l'étang (hauteur par unité le long de l'eau)
RELEVE_MAX = 0.15             # berge relevée au plus de tant (p75 du tour) ; au-delà, le niveau de l'étang descend
# LE NIVEAU DE WH1 QUAND LA CUVETTE LE TIENT (24.09.2026, 05 h 20, chaîne 11 ; Charles, pack de 04 h 50 : « la mare du début,
# en face de l'arbre, est vide » et « un gros trou derrière la cascade » ; WH1 : mare turquoise pleine). Les deux étangs de
# WH1 au sud de la Clairière Royale (niveau de WH1 2,819) étaient abaissés au niveau de la rivière qui les traverse (2,40
# et 2,50) : 35 % de leur carré sous l'eau, la cuvette vide derrière la chute de la gorge. La règle « rivière » visait les
# élargissements de rivière de WH1 posés 20 à 40 cm au-dessus de leur rivière, sans cuvette pour les tenir (eau plate qui
# flotte) ; ici, la cuvette de WH1 tient son eau. Désormais le niveau de WH1 est gardé, rivière dessous
# (`rivieres_vers_etangs`), si la berge à relever à ce niveau ne dépasse pas RELEVE_MAX ; sinon, règle de la rivière.
NIVEAU_WH1_SI_CUVETTE = True
# LA MARE DE LA CLAIRIÈRE ROYALE ET LA CASCADE DE LA GORGE (24.09.2026, 22 h 40, chaîne 13 ; Charles, pack de 22 h 20 : « des
# trous noirs entre les nappes », la sortie de la mare mal reliée à la cascade). Mesures (brouillons `mare_cascade_*.py`,
# cache de la chaîne 12) : (1) l'étang de WH1 au bord de la chute (194,20 ; 51,84, niveau 2,129) n'était visible dans WH1 que
# sur 12,8 % de son carré (33 px, sol de WH1 2,92 au centre) : faute de cuvette, une « ellipse réduite » creusée 0,8 u dans le
# plateau ; (2) son niveau tirait la rivière amont vers le bas (PENTE_ETANG) sur plus de 2 u : tranchée de 0,45 à 0,6 u ;
# (3) l'étang du fond de la gorge (0,818) tirait de même le bassin intermédiaire (1,9 dans WH1) à 1,0 ; (4) sous les étangs
# gardés au niveau de WH1, la rivière restait 16 à 40 cm plus bas (rubans de WH1) : son lit et sa tranchée se voyaient à
# travers la mare, et la sortie était 14 cm sous elle. Désormais : (1) un plan d'eau de WH1 visible sur moins de
# VISIBLE_WH1_MIN de son carré n'est pas un étang ; (2, 3) la descente vers un étang s'arrête au premier pixel qu'elle
# abaisserait de plus de ABAISSE_MAX (c'est une chute : la rivière garde son niveau) ; (4) dans un étang « rivière dessous »,
# l'eau de la rivière est à DESSOUS_ETANG sous lui, et autour elle remonte vers lui de RELEVE_RIVIERE_MAX au plus.
VISIBLE_WH1_MIN = 0.2
ABAISSE_MAX = 0.20
RELEVE_RIVIERE_MAX = 0.20
# fond : CA pose le sien 0,36 sous l'eau (médiane de 212 étangs, relevé de la session du rendu) ; l'eau de campagne
# s'estompe avec la profondeur (à quelques centimètres, presque rien)
PROF_BORD, PROF_CENTRE = 0.01, 0.30
TALUS_PX = 8
# LES PETITS ÉTANGS BIEN REMPLIS (23.09.2026, 22 h 50, session du rendu ; Charles : « vérifie que chaque étang a bien de
# l'eau à l'intérieur »). Relevé (brouillon `diag_etangs.py`, chaîne 6) : les 26 étangs ont de l'eau visible (55 à 82 % de
# leur contour d'eau), mais les petits (rayon de 5 à 6 px) n'atteignaient jamais PROF_CENTRE : talus de 8 px et 1 cm au bord,
# une eau à peine teintée. Talus ramené à la moitié du rayon moyen (au moins TALUS_MIN_PX), et PROF_BORD_PETITS au bord.
TALUS_MIN_PX = 3
PROF_BORD_PETITS = 0.03
REBORD = 0.03
BERGE_PX, FONDU_PX = 3, 8
MARGE_EAU_PX = 2
MARGE_FENETRE_PX = BERGE_PX + FONDU_PX + 6


def lacs_wh1():
    """[dict] des plans d'eau de WH1 visibles : cle (`props_wh1_vers_layers.cle_eau`), x, y, z (WH1, monde), hx, hz,
    ry (degrés), region, masque (culture)."""
    import props_wh1_vers_layers as PL
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    out = []
    for o in PL.objets_uniques():
        if PL.MODELE_PLAN_EAU not in o["modele"].replace("\\", "/").lower():
            continue
        masque, garder = PL.masque_culture(o)
        if not garder:
            continue
        hx, hz, ry = PL.carre_eau(o, wh1)
        x, y, z = (float(c) for c in o["position"])
        out.append(dict(cle=PL.cle_eau(o), x=x, y=y, z=z, hx=hx, hz=hz, ry=ry, region=o["region"], masque=masque))
    return sorted(out, key=lambda e: (e["x"], e["z"]))


def groupes(lacs):
    """Listes d'indices des lacs dont les carrés se touchent (distance des centres < somme des demi-diagonales)."""
    n = len(lacs)
    parent = list(range(n))

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            a, b = lacs[i], lacs[j]
            if math.hypot(a["x"] - b["x"], a["z"] - b["z"]) < math.hypot(a["hx"], a["hz"]) + math.hypot(b["hx"], b["hz"]):
                parent[racine(i)] = racine(j)
    g = {}
    for i in range(n):
        g.setdefault(racine(i), []).append(i)
    return list(g.values())


class Grille:
    """Passage monde (espace des hex) <-> raster (ligne 0 au nord, pixels carrés) pour un raster H x L."""

    def __init__(self, H, L):
        self.H, self.L = H, L
        self.pas = L / LARGEUR_MONDE

    def fenetre(self, x, z, rayon):
        """(r0, r1, c0, c1, X, Z) : fenêtre de raster autour du point du monde (x, z), rayon en unités du monde, avec les
        coordonnées du monde des centres de ses pixels."""
        c = x * self.pas - 0.5
        r = (self.H - 1.5) - z * R3 * self.pas
        dc = rayon * self.pas + MARGE_FENETRE_PX
        dr = rayon * R3 * self.pas + MARGE_FENETRE_PX
        r0, r1 = max(int(r - dr), 0), min(int(r + dr) + 2, self.H)
        c0, c1 = max(int(c - dc), 0), min(int(c + dc) + 2, self.L)
        cols, rows = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
        X = (cols + 0.5) / self.pas
        Z = ((self.H - 1.5) - rows) / self.pas / R3
        return r0, r1, c0, c1, X, Z


def local(lac, X, Z):
    """(u, v) dans le repère du carré de WH1 (convention de `masques_eau_carte.lacs`)."""
    a = math.radians(lac["ry"])
    dx, dz = X - lac["x"], Z - lac["z"]
    return dx * math.cos(a) - dz * math.sin(a), dx * math.sin(a) + dz * math.cos(a)


def norme_carre(lac, X, Z):
    u, v = local(lac, X, Z)
    return np.maximum(np.abs(u) / lac["hx"], np.abs(v) / lac["hz"])


def _lisser_masque(m, rayon=2, sigma=1.5):
    import rivieres_wh1 as RW
    if not m.any():
        return m
    m = RW.dilater(m, rayon)
    m = ~RW.dilater(~m, rayon)                    # fermeture
    return RW.flou(m.astype(np.float64), sigma) > 0.5


def centre_interieur(masque, X, Z):
    """Point du masque le plus loin de son bord (dernière érosion non vide), le plus proche du barycentre : le barycentre
    d'une cuvette en croissant tombe hors d'elle (rayons nuls, essai à blanc du 23.09.2026)."""
    import rivieres_wh1 as RW
    m, dernier = masque.copy(), masque
    while m.any():
        dernier = m
        m = ~RW.dilater(~m, 1)
    w = masque.astype(np.float64)
    bx, bz = float((X * w).sum() / w.sum()), float((Z * w).sum() / w.sum())
    ii, jj = np.nonzero(dernier)
    k = int(np.argmin((X[ii, jj] - bx) ** 2 + (Z[ii, jj] - bz) ** 2))
    return float(X[ii[k], jj[k]]), float(Z[ii[k], jj[k]])


def rayons(masque, X, Z, cx, cz):
    """Rayons (unités du monde) de la forme étoilée depuis (cx, cz) : pour chacun des N_POINTS angles, la distance de la
    première sortie du masque (pas de 0,02 unité)."""
    pas_r = 0.02
    etendue = float(np.hypot(X - cx, Z - cz)[masque].max()) + 0.1 if masque.any() else RAYON_MIN
    ts = np.arange(0.0, etendue + pas_r, pas_r)
    x0, z0 = float(X[0, 0]), float(Z[0, 0])
    dxp = float(X[0, 1] - X[0, 0]) if X.shape[1] > 1 else 1.0
    dzp = float(Z[1, 0] - Z[0, 0]) if Z.shape[0] > 1 else -1.0
    out = np.empty(N_POINTS)
    for k in range(N_POINTS):
        th = 2 * math.pi * k / N_POINTS
        px_ = cx + ts * math.cos(th)
        pz_ = cz + ts * math.sin(th)
        jj = np.rint((px_ - x0) / dxp).astype(int)
        ii = np.rint((pz_ - z0) / dzp).astype(int)
        dedans = (ii >= 0) & (ii < masque.shape[0]) & (jj >= 0) & (jj < masque.shape[1])
        m = np.zeros(len(ts), bool)
        m[dedans] = masque[ii[dedans], jj[dedans]]
        sortie = np.nonzero(~m)[0]
        out[k] = ts[sortie[0] - 1] if len(sortie) and sortie[0] > 0 else (ts[-1] if not len(sortie) else 0.0)
    for _ in range(2):                            # lissage circulaire
        out = 0.25 * np.roll(out, 1) + 0.5 * out + 0.25 * np.roll(out, -1)
    return np.maximum(out, RAYON_MIN)


def rayon_a(rs, X, Z, cx, cz):
    """(distance au centre, rayon de la forme dans la direction) pour chaque point, interpolé entre les N_POINTS."""
    th = np.mod(np.arctan2(Z - cz, X - cx), 2 * math.pi) / (2 * math.pi) * N_POINTS
    k0 = np.floor(th).astype(int) % N_POINTS
    f = th - np.floor(th)
    return np.hypot(X - cx, Z - cz), rs[k0] * (1 - f) + rs[(k0 + 1) % N_POINTS] * f


def former(lacs, sol, eau_riv, grille):
    """[étang] : forme, niveau et fenêtre de chaque lac (voir l'en-tête, points 1 et 2). `sol` : notre sol avant les
    rivières (ligne 0 au nord) ; `eau_riv` : niveau de l'eau des rivières (NaN hors de l'eau)."""
    etangs = []
    former.ignores = []                           # (chaîne 13) plans d'eau de WH1 écartés (VISIBLE_WH1_MIN) et part visible
    for g in groupes(lacs):
        for i in g:
            lac = lacs[i]
            rayon = math.hypot(lac["hx"], lac["hz"])
            r0, r1, c0, c1, X, Z = grille.fenetre(lac["x"], lac["z"], rayon)
            s = sol[r0:r1, c0:c1]
            e = eau_riv[r0:r1, c0:c1]
            u, v = local(lac, X, Z)
            # (chaîne 13) un plan d'eau de WH1 presque entièrement sous son sol n'était pas visible dans WH1 : pas d'étang
            carre = (np.abs(u) <= lac["hx"]) & (np.abs(v) <= lac["hz"])
            if VISIBLE_WH1_MIN and carre.any() and float(np.mean(s[carre] < lac["y_base"])) < VISIBLE_WH1_MIN:
                former.ignores.append(((round(lac["x"], 2), round(lac["z"], 2)), round(float(np.mean(s[carre] < lac["y_base"])), 3)))
                continue
            ellipse = (u / (ELLIPSE * lac["hx"])) ** 2 + (v / (ELLIPSE * lac["hz"])) ** 2 <= 1
            cellule = np.ones(ellipse.shape, bool)
            n_moi = norme_carre(lac, X, Z)
            for j in g:
                if j != i:
                    cellule &= n_moi + ECART_CELLULE < norme_carre(lacs[j], X, Z)
            niveau = lac["y_base"]
            for passe in range(3):
                cuvette = ellipse & cellule & (s < niveau + TOLERANCE_CUVETTE)
                if cuvette.sum() < AIRE_MIN * max((ellipse & cellule).sum(), 1):
                    repli = (u / (ELLIPSE_REPLI * lac["hx"])) ** 2 + (v / (ELLIPSE_REPLI * lac["hz"])) ** 2 <= 1
                    cuvette = repli & cellule
                    forme_de = "ellipse réduite"
                else:
                    forme_de = "cuvette"
                cuvette = _lisser_masque(cuvette) & cellule
                if not cuvette.any():
                    cuvette = ellipse & cellule
                    forme_de = "ellipse"
                cx, cz = centre_interieur(cuvette, X, Z)
                rs = rayons(cuvette, X, Z, cx, cz)
                rho, rr = rayon_a(rs, X, Z, cx, cz)
                dedans = rho <= rr
                # niveau : la rivière qui traverse le bassin
                riv = dedans & np.isfinite(e)
                cause = "WH1"
                neuf = lac["y_base"]
                d_out = (rho - rr) * grille.pas
                tour = (d_out > 0) & (d_out <= BERGE_PX) & ~np.isfinite(e)
                if riv.sum() >= RIVIERE_MIN_PX:
                    # (NIVEAU_WH1_SI_CUVETTE) la cuvette tient l'eau au niveau de WH1 : on le garde, la rivière passe dessous
                    tient = NIVEAU_WH1_SI_CUVETTE and tour.any() and \
                        float(np.percentile(neuf + REBORD - s[tour], 75)) <= RELEVE_MAX
                    if tient:
                        cause = "WH1 (rivière dessous)"
                    else:
                        neuf = min(neuf, float(np.percentile(e[riv], 10)) + DESSUS_RIVIERE)
                        cause = "rivière"
                # la berge à relever
                if tour.any():
                    releve = float(np.percentile(neuf + REBORD - s[tour], PERCENTILE_BERGE))
                    if releve > RELEVE_MAX:
                        neuf -= releve - RELEVE_MAX
                        cause += " ; berge (abaissé)"
                if abs(neuf - niveau) < 0.005 and passe > 0:
                    break
                niveau = neuf
            etangs.append(dict(lac=lac, niveau=niveau, cause=cause, forme=forme_de, centre=(cx, cz), rayons=rs,
                               fenetre=(r0, r1, c0, c1), groupe=tuple(lacs[j]["cle"] for j in g)))
    return etangs


def rivieres_vers_etangs(eau_riv, etangs, grille):
    """(eau_riv, n) : dans chaque étang (et sa marge), l'eau des rivières passe DESSOUS_ETANG sous lui ; en amont, elle
    descend vers lui (plafond niveau - DESSOUS_ETANG + PENTE_ETANG × distance le long de l'eau)."""
    import rivieres_wh1 as RW
    eau_riv = np.array(eau_riv, copy=True)
    n = 0
    for et in etangs:
        r0, r1, c0, c1 = et["fenetre"]
        # fenêtre élargie : la descente amont porte jusqu'à ~2 unités
        m = int(2.0 * grille.pas) + 2
        R0, R1, C0, C1 = max(r0 - m, 0), min(r1 + m, grille.H), max(c0 - m, 0), min(c1 + m, grille.L)
        cols, rows = np.meshgrid(np.arange(C0, C1), np.arange(R0, R1))
        X = (cols + 0.5) / grille.pas
        Z = ((grille.H - 1.5) - rows) / grille.pas / R3
        rho, rr = rayon_a(et["rayons"], X, Z, *et["centre"])
        e = eau_riv[R0:R1, C0:C1]
        eau = np.isfinite(e)
        dans = eau & (rho <= rr + (MARGE_EAU_PX + 2) / grille.pas)
        if not dans.any():
            continue
        haut = et["niveau"] - DESSOUS_ETANG
        dessous = "rivière dessous" in et["cause"]
        if ABAISSE_MAX is None:
            d = np.full(e.shape, np.inf)
            d[dans] = 0.0
            atteint = dans.copy()
            for k in range(1, m + 1):
                v = RW.dilater(atteint, 1) & eau & ~atteint
                if not v.any():
                    break
                d[v] = k
                atteint |= v
            plafond = haut + PENTE_ETANG * d / grille.pas
            bas = eau & (e > plafond)
            e = np.where(bas, plafond, e)
            eau_riv[R0:R1, C0:C1] = e
            n += int(bas.sum())
            continue
        # (chaîne 13) dans l'étang : la rivière DESSOUS_ETANG sous lui (« rivière dessous » : relevée aussi) ; autour, de
        # proche en proche, abaissée vers lui (PENTE_ETANG) ou relevée vers lui (« rivière dessous »), mais jamais de plus de
        # ABAISSE_MAX / RELEVE_RIVIERE_MAX : au-delà c'est une chute, la rivière garde son niveau et la descente s'arrête
        neuf = e.copy()
        neuf[dans] = haut if dessous else np.minimum(e[dans], haut)
        atteint = dans.copy()
        for k in range(1, m + 1):
            v = RW.dilater(atteint, 1) & eau & ~atteint
            if not v.any():
                break
            plafond = haut + PENTE_ETANG * k / grille.pas
            plancher = haut - PENTE_ETANG * k / grille.pas
            bloque = v & (((e - plafond) > ABAISSE_MAX) | (dessous & ((plancher - e) > RELEVE_RIVIERE_MAX)))
            ok = v & ~bloque
            neuf[ok] = np.minimum(e[ok], plafond)
            if dessous:
                neuf[ok] = np.maximum(neuf[ok], plancher)
            atteint |= ok
        n += int((np.abs(neuf - e) > 1e-4)[eau].sum())
        eau_riv[R0:R1, C0:C1] = neuf
    return eau_riv, n


def creuser(sol, etangs, lit_riviere, grille):
    """(sol, bilan) : berges relevées (toutes, d'abord), puis cuvettes (point 4 de l'en-tête)."""
    sol = np.array(sol, np.float64, copy=True)
    bilan = {"px relevés (berge)": 0, "px creusés (cuvette)": 0}
    geo = []
    for et in etangs:
        r0, r1, c0, c1 = et["fenetre"]
        cols, rows = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
        X = (cols + 0.5) / grille.pas
        Z = ((grille.H - 1.5) - rows) / grille.pas / R3
        rho, rr = rayon_a(et["rayons"], X, Z, *et["centre"])
        geo.append((rho - rr) * grille.pas)                   # distance au rivage en px (> 0 dehors)
    dans_un_bassin = np.zeros(sol.shape, bool)
    for et, d in zip(etangs, geo):
        r0, r1, c0, c1 = et["fenetre"]
        dans_un_bassin[r0:r1, c0:c1] |= d <= 0
    for et, d in zip(etangs, geo):
        r0, r1, c0, c1 = et["fenetre"]
        s = sol[r0:r1, c0:c1]
        t = np.clip((d - BERGE_PX) / FONDU_PX, 0, 1)
        w = 1 - t * t * (3 - 2 * t)
        cible = et["niveau"] + REBORD
        berge = (d > 0) & (w > 0) & (s < cible) & ~lit_riviere[r0:r1, c0:c1] & ~dans_un_bassin[r0:r1, c0:c1]
        s[berge] = s[berge] + np.minimum(cible - s[berge], BERGE_RELEVE_MAX) * w[berge]
        bilan["px relevés (berge)"] += int(berge.sum())
    for et, d in zip(etangs, geo):
        r0, r1, c0, c1 = et["fenetre"]
        s = sol[r0:r1, c0:c1]
        rayon_px = float(np.mean(et["rayons"])) * grille.pas
        talus = min(TALUS_PX, max(TALUS_MIN_PX, 0.5 * rayon_px))
        bord = PROF_BORD if talus >= TALUS_PX else PROF_BORD_PETITS
        t = np.clip(-d / talus, 0, 1)
        prof = bord + (PROF_CENTRE - bord) * t * t * (3 - 2 * t)
        cuvette = (d <= 0) & (s > et["niveau"] - prof)
        if ILOT_MIN is not None:
            # (chaîne 15) les îlots de WH1 dans l'étang restent : à plus de 2 px du rivage, le sol au-dessus de l'eau
            cuvette &= ~((d <= -2) & (s >= et["niveau"] + ILOT_MIN))
        s[cuvette] = et["niveau"] - prof[cuvette]
        bilan["px creusés (cuvette)"] += int(cuvette.sum())
    return sol.astype(np.float32), bilan


# AU BORD D'UNE CHUTE (23.09.2026, 18 h, session du rendu ; Charles : « les lacs et les rivières mal reliés »). Profil de
# l'étang perché au-dessus de la cascade de WH1 au nord-ouest de Tyr Vanna (brouillon `profil_cascade.py`) : le sol tombe
# de 1,97 à 0,57 entre 0,64 et 0,72 u du centre ; la marge de MARGE_EAU_PX du polygone d'eau passait au-dessus du vide
# (eau plate en l'air, au-dessus de la rivière). La marge est donc réglée direction par direction : jamais au-delà du point
# où le sol tombe de plus de CHUTE sous le niveau de l'étang.
CHUTE = 0.05
# LES BORDS D'ÉTANG ENTERRÉS (25.09.2026, 01 h 40, chaîne 15 ; audit de toute la carte : 17 étangs sur 18 avec un bord d'eau
# qui flotte au-dessus du sol, sur 5 à 56 % du tour et jusqu'à 0,68 u ; étang au sud-est de Gien : berge relevée de 0,63 u,
# une digue ; défilé Gragrut : 40 % du bord flotte ; accord de Charles, 01 h 35 : « attaque tout ça »). Trois causes : le
# niveau n'était abaissé que si la berge à relever dépassait RELEVE_MAX aux trois quarts du tour (le dernier quart restait
# une digue ou un bord en l'air) ; la berge relevée sans limite ; la marge du contour d'eau gardée tant que le sol ne tombe
# pas de plus de 5 cm. Désormais : niveau réglé sur PERCENTILE_BERGE du tour, berge relevée de BERGE_RELEVE_MAX au plus,
# marge coupée dès que le sol passe sous le niveau de 2 cm (comme les étangs de CA : bord enterré).
CHUTE = 0.02
PERCENTILE_BERGE = 95
# LES ÎLOTS DES ÉTANGS (25.09.2026, 02 h, chaîne 15 ; contrôle des objets dans l'eau, `scratchpad\correctifs15\`) : les deux
# statues de la Dame du Lac (sud de Laguiller, sud-est de Gasconnie) se dressent dans WH1 sur un îlot à +0,35 u au-dessus
# de l'étang, avec cascade, éclaboussures et son de lac autour ; la cuvette le creusait sous l'eau (notre sol -0,016 contre
# 0,632 dans WH1). Le sol d'un étang à plus d'ILOT_MIN au-dessus de l'eau, loin du rivage, n'est plus creusé.
ILOT_MIN = 0.05
BERGE_RELEVE_MAX = 0.18


def marges_sures(etangs, sol, grille):
    """Pour chaque étang, `marges` (N_POINTS, px) : la marge du contour d'eau, réduite là où le sol tombe sous l'eau au-delà
    du rivage (bord d'une chute) ; rend le nombre de directions réduites."""
    n = 0
    for et in etangs:
        cx, cz = et["centre"]
        m = np.full(N_POINTS, float(MARGE_EAU_PX))
        for k in range(N_POINTS):
            a = 2 * math.pi * k / N_POINTS
            # (chaîne 15) la marge se mesure à partir de la berge (1 px au-delà du rivage) : au rivage même, le fond de la
            # cuvette est 1 à 3 cm sous l'eau (PROF_BORD, PROF_BORD_PETITS), sous CHUTE = 0,02 ; chaîne 14 : marge coupée au
            # rivage sur 479 directions, bord de l'eau enterré à 38 % (73 % à la chaîne 13)
            for d in np.arange(1.0, MARGE_EAU_PX + 1e-9, 0.25):
                rr = et["rayons"][k] + d / grille.pas
                x, z = cx + rr * math.cos(a), cz + rr * math.sin(a)
                col = int(np.clip(round(x * grille.pas - 0.5), 0, grille.L - 1))
                row = int(np.clip(round((grille.H - 1.5) - z * R3 * grille.pas), 0, grille.H - 1))
                if sol[row, col] < et["niveau"] - CHUTE:
                    m[k] = max(d - 0.5, 0.0)
                    n += 1
                    break
        et["marges"] = m
    return n


def masque_eau(etangs, grille):
    """Raster (H x L) : True sous l'eau des étangs (contour élargi de sa marge, MARGE_EAU_PX ou `marges`)."""
    m = np.zeros((grille.H, grille.L), bool)
    for et in etangs:
        r0, r1, c0, c1 = et["fenetre"]
        cols, rows = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
        X = (cols + 0.5) / grille.pas
        Z = ((grille.H - 1.5) - rows) / grille.pas / R3
        marges = et.get("marges")
        rs = et["rayons"] + (marges if marges is not None else MARGE_EAU_PX) / grille.pas
        rho, rr = rayon_a(rs, X, Z, *et["centre"])
        m[r0:r1, c0:c1] |= rho <= rr
    return m


# Sens de l'axe « y » des points d'une polyligne d'entité (repère local, rotation nulle) : +1 si y local = +z du monde.
# Convention de `masques_eau_carte.lacs` (monde x = X + a cos r + c sin r, z = Z - a sin r + c cos r ; r = 0 : z = Z + c),
# confirmée sur les étangs des Empires (23.09.2026 : avec elle, leurs trous de terrain à rotation nulle recouvrent 74,5 %
# de leur eau, contre 57 à 66 % pour les sept autres conventions).
SENS_Y_POLYLIGNE = 1


def contour(et, grille, marge_px=MARGE_EAU_PX):
    """[(a, c)] : les N_POINTS points du contour de l'eau, relatifs au centre (monde), dans l'ordre des angles ; la marge
    est celle de `marges_sures` quand elle a été calculée."""
    marges = et.get("marges")
    rs = et["rayons"] + (np.minimum(marges, marge_px) if marges is not None else marge_px) / grille.pas
    return [(float(r * math.cos(2 * math.pi * k / N_POINTS)), float(SENS_Y_POLYLIGNE * r * math.sin(2 * math.pi * k / N_POINTS)))
            for k, r in enumerate(rs)]


def entite(et, grille, materiau):
    """Bloc `<entity>` ECPolygonMesh de l'eau de l'étang (même réglage que `props_wh1_vers_layers.entite_eau`)."""
    import props_wh1_vers_layers as PL
    cx, cz = et["centre"]
    pts = "".join(f'\t\t\t\t\t<point x="{a:.5f}" y="{c:.5f}"/>\n' for a, c in contour(et, grille))
    lac = et["lac"]
    return (f'\t\t<entity id="{PL.ident("etang:" + repr(lac["cle"]))}">\n'
            f'\t\t\t<ECPolygonMesh material="{materiau}" affects_mesh_optimization="false"/>'
            '<ECVisibilitySettingsCampaign visible_in_tactical_view="False" visible_in_tactical_view_only="False"/>\n'
            f'\t\t\t<ECCampaignProperties visible_in_shroud="False" no_culling="true" culture_mask="{lac["masque"]}"/>\n'
            f'\t\t\t<ECTransform position="{cx:.5f} {et["niveau"]:.5f} {cz:.5f}" rotation="0. 0. 0." scale="1. 1. 1." '
            'pivot="0 0 0"/>\n'
            '\t\t\t<ECPolyline>\n\t\t\t\t<polyline closed="true">\n' + pts +
            '\t\t\t\t</polyline>\n\t\t\t</ECPolyline>\n\t\t</entity>\n')


def bord_enterre(et, sol, grille, marge_px=MARGE_EAU_PX):
    """Part du contour de l'eau où le sol est au-dessus de l'eau (bord enterré, comme chez CA)."""
    cx, cz = et["centre"]
    ok = 0
    pts = contour(et, grille, marge_px)
    for a, c in pts:
        x, z = cx + a, cz + SENS_Y_POLYLIGNE * c
        col = int(np.clip(round(x * grille.pas - 0.5), 0, grille.L - 1))
        row = int(np.clip(round((grille.H - 1.5) - z * R3 * grille.pas), 0, grille.H - 1))
        ok += sol[row, col] > et["niveau"]
    return ok / len(pts)


def main():
    import glob
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    sys.stdout.reconfigure(encoding="utf-8")
    import terrain_wh1_vers_terry as T
    h = np.asarray(Image.open(glob.glob(os.path.join(T.PROJET, f"{T.CARTE}.height.*.tif"))[0]), np.float64)
    eau = np.load(os.path.join(os.path.dirname(T.RELIEF_MAILLAGES), "eau_rivieres.npy"))
    grille = Grille(*h.shape)
    lacs = lacs_wh1()
    for lac in lacs:
        lac["y_base"] = lac["y"]
    etangs = former(lacs, h, eau, grille)
    for et in etangs:
        lac = et["lac"]
        print(f"({lac['x']:6.1f};{lac['z']:6.1f}) WH1 {lac['y']:5.2f} -> {et['niveau']:5.2f} ({et['cause']}, {et['forme']}) "
              f"rayons {et['rayons'].min():.2f}..{et['rayons'].max():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
