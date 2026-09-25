#!/usr/bin/env python3
"""
replats_colonies.py - le sol adouci sous les colonies, pour les préfabs plats de WH3 (session du rendu, chaîne 12).

Pourquoi (24.09.2026 ; Charles, relevé de la construction sur la vidéo V2, 41 s : à Fort Solstice, un champ du préfab
« semble posé au-dessus de la pente, on voit son épaisseur », des maisons à cheval sur la pente) : les préfabs de colonie
de CA sont plats et larges (bretonniens mineurs : pièces jusqu'à 2,3 u du centre au p90, 2,8 au maximum ; brouillon
`prefab_emprise.py`) ; CA pose ses villes sur du plat. Notre relief de WH1, fait pour ses colonies plus petites, penche
sous certaines : écart de hauteur p5-p95 dans 2,3 u de 0,3 à 1,2 u (Fort Solstice 0,31, Montfort Poussenc 1,17 ;
brouillon `colonies_eau.py`).

Méthode (`replats`), le relief de WH1 gardé autant que possible :
- seulement sous les colonies dont le sol penche vraiment (écart p5-p95 sous le préfab d'au moins ECART_MIN) et qui ne sont
  pas des forts de montagne (plus de MONTAGNE_MAX de montagne de WH1 sous le préfab) ;
- PARTIEL : le sol se rapproche de PART de son écart à la hauteur du cœur (médiane dans R_COEUR), jusqu'à R1, puis le
  raccord revient au relief de WH1 en douceur (smoothstep) jusqu'à R2. Un disque tout à fait plat reporte la dénivelée
  sur la couronne de raccord (premier essai, R1 2 et R2 3 : pente multipliée par 4, anneaux visibles) ; à moitié et sur
  3 u de raccord, environ x 1,5 ;
- le déplacement le plus grand, raccord compris (au pied d'une colline voisine, l'écart au cœur grandit avec la distance),
  reste sous DMAX : la part est RÉDUITE (jamais écrêtée : un écrêtage dessine une marche là où il commence) ;
- rien sur la mer, les montagnes de WH1, le lit des rivières (creusé ensuite) : le déplacement s'y éteint en douceur sur
  FONDU_GARDE (pas de marche au bord de l'eau).
Seul `hauteur` change, pas `hauteur_wh1` : les objets de WH1 (arbres, décors, ambiance), recalés de l'écart entre notre
sol et celui de WH1, suivent le sol.

Usage (module, `terrain_wh1_vers_terry.rasters`, après le lit des rivières de WH1, avant le niveau de leur eau) :
    hauteur, bilan = replats_colonies.replats(hauteur, positions, pas, garde, montagnes)
"""

import numpy as np

ACTIF = True
R_COEUR, R1, R2 = 1.0, 2.3, 5.3        # unités (espace des hex) : cœur, emprise du préfab, fin du raccord
PART = 0.5                             # part de l'écart au plat retirée sous le préfab
ECART_MIN = 0.10                       # u : écart p5-p95 sous le préfab en deçà duquel on ne touche à rien
DMAX = 0.25                            # u : déplacement maximal sous le préfab (la part est réduite d'autant)
FONDU_GARDE = 1.0                      # u : extinction du déplacement à l'approche de la mer, de l'eau, des montagnes
MONTAGNE_MAX = 0.3
R3 = 3 ** 0.5 / 2


def _lisse(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _distance(masque, portee):
    """Distance (px, plafonnée à `portee`) de chaque pixel à `masque`, par dilatations 8-connexes successives."""
    d = np.full(masque.shape, float(portee), np.float64)
    front = masque.copy()
    d[front] = 0.0
    for k in range(1, portee):
        p = np.pad(front, 1)
        v = front.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                v |= p[1 + dy:1 + dy + front.shape[0], 1 + dx:1 + dx + front.shape[1]]
        d[v & ~front] = k
        front = v
    return d


def replats(h, positions, pas, garde, montagnes=None):
    """(sol, bilan) : `h` (raster ligne 0 au nord, `pas` px par unité) adouci sous chaque colonie de `positions`
    ({clé : (x, z)} monde) ; `garde` : pixels à ne pas toucher (mer, lit des rivières) ; `montagnes` : emprise des
    montagnes de WH1 (gardée elle aussi)."""
    h = np.array(h, np.float64, copy=True)
    H, L = h.shape
    bilan = {"colonies adoucies": 0, "déjà planes": 0, "laissées (montagne)": [], "déplacement p50 / max (u)": None,
             "écart sous le préfab p50 avant -> après (u)": None}
    deplacements, avant, apres = [], [], []
    fondu_px = max(int(round(FONDU_GARDE * pas)), 1)
    for cle, (x, z) in sorted(positions.items()):
        ci, cj = (H - 1.5) - z * R3 * pas, x * pas - 0.5
        n = int(R2 * pas) + fondu_px + 2
        a0, a1, b0, b1 = max(int(ci) - n, 0), min(int(ci) + n + 1, H), max(int(cj) - n, 0), min(int(cj) + n + 1, L)
        if a0 >= a1 or b0 >= b1:
            continue
        ii, jj = np.mgrid[a0:a1, b0:b1]
        d = np.hypot((jj - cj) / pas, (ii - ci) / (R3 * pas))
        s = h[a0:a1, b0:b1]
        g = np.asarray(garde[a0:a1, b0:b1], bool)
        if montagnes is not None:
            mont = np.asarray(montagnes[a0:a1, b0:b1], bool)
            if (d <= R1).any() and mont[d <= R1].mean() > MONTAGNE_MAX:
                bilan["laissées (montagne)"].append(cle.split("_", 2)[-1])
                continue
            g = g | mont
        coeur = (d <= R_COEUR) & ~g
        pied = (d <= R1) & ~g
        if coeur.sum() < 10 or pied.sum() < 20:
            continue
        h0 = float(np.median(s[coeur]))
        e0 = float(np.percentile(s[pied], 95) - np.percentile(s[pied], 5))
        if e0 < ECART_MIN:
            bilan["déjà planes"] += 1
            continue
        w = 1.0 - _lisse((d - R1) / (R2 - R1))
        fg = _lisse(_distance(g, fondu_px + 1) / fondu_px)
        brut = w * fg * (h0 - s)
        amax = float(np.abs(brut).max())               # sur tout le raccord : une colline voisine n'est pas rabotée
        part = min(PART, DMAX / amax) if amax > 0 else 0.0
        delta = part * brut
        neuf = np.where(g, s, s + delta)
        deplacements.append(np.abs(neuf - s)[d <= R2])
        avant.append(e0)
        apres.append(float(np.percentile(neuf[pied], 95) - np.percentile(neuf[pied], 5)))
        h[a0:a1, b0:b1] = neuf
        bilan["colonies adoucies"] += 1
    if deplacements:
        tout = np.concatenate(deplacements)
        bilan["déplacement p50 / max (u)"] = (round(float(np.median(tout)), 3), round(float(tout.max()), 3))
        bilan["écart sous le préfab p50 avant -> après (u)"] = (round(float(np.median(avant)), 3),
                                                               round(float(np.median(apres)), 3))
    return h.astype(np.float32), bilan
