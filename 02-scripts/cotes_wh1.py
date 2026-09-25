#!/usr/bin/env python3
"""
cotes_wh1.py - la côte naturelle : le tracé de la côte de Warhammer 1, sans ses marches.

Pourquoi (24.09.2026, 01 h 30 - 02 h 10, session du rendu ; Charles, pack de 00 h 50 : « les côtes, c'est un peu n'importe
quoi », « revenir à ce que Warhammer 1 faisait et l'adapter dans Warhammer 3 » ; Bordeleaux « très, très dans l'eau »).
Relevés (brouillons `cote_wh1_vraie.py`, `ports_eau_0135.py`, `ports_ie_eau.py`, journal du rendu § 3 decies) :
- la côte de WH1 est la frontière de ses maillages de terre et de mer, qui ne se recouvrent jamais (terre au-dessus de 0,
  mer dessous) : un escalier sur la grille des cases (marches de 0,33 à 2 u) ; son `lf_sea_height_map` est lisse mais
  flou (ligne 0 à 1-3 u dans les terres). `rivage_naturel` n'adoucissait qu'à 0,25 u près : des dents de scie ;
- aux Empires, le centre d'une ville portuaire n'est jamais dans l'eau : l'eau est à 0,70 u en médiane (p10 0,37), et un
  disque d'1 u autour du centre n'en contient que 8 % en médiane (p90 27 %) ; les autres colonies : 0 %. Chez nous, à la
  position de WH1 (hex de WH1) : Bordeleaux 52 % (centre dans l'eau), Brionne 44 %, Mousillon 18 % (eau à 0,06 u) ; WH1
  posait sa ville sur le rivage même, pas WH3.

Méthode (`cote_naturelle`) : part de terre du masque de WH1 floutée (trois moyennes de rayon RAYON_PX), plus un bruit lisse
faible (côte moins régulière), seuillée à 0,5 : la côte passe au milieu des marches. Bornes : à plus de DMAX_PX de la côte
de WH1 rien ne change ; les îles de WH1 de moins d'ILE_MAX_PX restent telles quelles ; restent aussi du côté de WH1 les
falaises de côte de WH1 (`cliff_custom`, posées sur son tracé), les objets de WH1 et les embouchures (tuiles de rivière).
Villes : terre dans R_PORT autour des ports (norme des Empires), eau à leurs hex de port (valeur 1 de la couche des
emplacements), pas de mer à moins de R_VILLE des autres colonies.

Usage (module, `terrain_wh1_vers_terry.rasters`) :
    mer, bilan = cote_naturelle(mer_wh1, pas)
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ATELIER = r"C:\TotalWar-CampaignMap"
COLONIES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1", "colonies_map_data.json")
PORTS = ("wh_dlc05_bordeleaux_bordeleaux", "wh_dlc05_brionne_brionne", "wh_dlc05_mousillon_mousillon")

COTE_NATURELLE = True
# LE DÉCOUPAGE DE WH1 (24.09.2026, 18 h 55, chaîne 12 ; Charles, capture en jeu du pack 9.0 : « fais exactement comme dans
# Warhammer 1 au niveau du découpage de la côte, ne te prends pas la tête à réinventer la roue, il faut juste l'adapter dans
# Warhammer 3 »). Le lissage (flou, bruit) arrondissait les caps, refermait les bras de mer et laissait le plan d'eau de la
# mer (en cases) dépasser de la côte lissée : les éclats pâles en escalier de la capture de 18 h 30. Sans lissage : la mer de
# WH1 à la case près ; seule adaptation à WH3, la terre autour des ports et des colonies (R_PORT, R_VILLE), comme avant.
# REMIS (24.09.2026, 22 h 50, chaîne 13 ; Charles, capture de 22 h 40 au golfe nord du Bidouze : côte « en escalier à gros
# crans » avec des murs sombres ; « voir comment WH1 fait pour que ce soit lisse en jeu alors que ses données sont
# pixelisées »). Mesure (brouillons `cote_golfe_zoom.py`, `cote_profil_wh1.py`) : notre tracé était celui de WH1 (46 455 px
# de mer contre 47 536, crans de la case), et WH1 a le même mur à sa côte (terre +0,14, fond -0,30 dès le premier pixel).
# Mais WH1 dessine ses tuiles avec leurs arêtes (diagonales des tuiles *_tri), alors que WH3 simplifie la carte de hauteur
# de loin (LOD de BOB) : un mur d'un pixel y retombe sur des mailles de plusieurs hex. Donc la FORME de WH1, lisse sous la
# case, avec une berge en pente (`terrain_wh1_vers_terry.RIVAGE_TERRE_WH1 = False`) : ce que WH1 montre en jeu.
LISSAGE = True
# les deltas de WH1 (`deltas_wh1.zone`, tuiles d'embouchure) restent au pixel de WH1 : le lissage refermait leurs bras et
# effaçait leurs bancs (chaîne 11 : 1 944 px de mer perdus, dont l'estuaire près d'Yremy et la baie au sud de Brionne)
GARDER_DELTAS = True
# (25.09.2026, chaîne 14 ; Charles, capture au delta d'Yremy : escalier de cases autour du delta) les deltas ne sont plus
# figés au pixel de WH1 mais lissés À PART, plus doucement que la côte (moyennes de rayon LISSAGE_DELTAS_PX au lieu de
# RAYON_PX : écart-type ~1,6 px contre ~13) : les marches de 0,33 u s'arrondissent, les bras et les bancs de WH1 restent.
LISSAGE_DELTAS_PX = 2
RAYON_PX = 12                  # rayon des trois moyennes : sigma ≈ 1,08 x RAYON_PX px (13 px = 1,08 u)
DMAX_PX = 14                   # déplacement maximal du trait de côte de WH1 (px ; 1,17 u)
BRUIT = 0.08                   # amplitude du bruit lisse sur la part de terre (le trait bouge de ~0,2 u)
R_PORT, R_HEX_PORT, R_VILLE = 0.75, 0.3, 1.0      # unités (espace des hex)
ILE_MAX_PX = 600               # îles de WH1 gardées telles quelles
GARDE_OBJET_PX = 2             # un objet de WH1 garde son côté (terre ou mer) dans ce rayon
# Les falaises de côte de WH1 (233 tuiles `cliff_custom` de 2 x 2 cases) sont posées AUX ANGLES de son escalier : les
# garder figeait 47 % de la bande côtière et la côte restait en dents de scie (essai du 24.09.2026, 02 h 20). On lisse
# partout ; `montagnes_wh1.construire(mer=...)` écarte les falaises qui ne touchent plus la côte (79 sur 233 à l'essai,
# toutes échouées en mer aux caps arrondis ; 154 restent au bord de l'eau).
GARDER_FALAISES = False
GARDE_FALAISE_PX = 4           # marge autour des falaises de côte de WH1 (si GARDER_FALAISES)
# Embouchures : pas de protection (GARDER_EMBOUCHURES). Les familles de rivière, puis les seules tuiles `river_mouth`,
# figeaient des baies entières en escalier (essais du 24.09.2026, 02 h 30 et 02 h 40, au sud de Brionne : la tuile
# d'embouchure de WH1 couvre toute la baie). La chaîne des rivières, qui part de cette mer, relie chaque rivière à elle
# (`descente_vers_la_mer`, `plongee` sous le plan d'eau) : un chenal d'embouchure comblé par le lissage devient le lit.
GARDER_EMBOUCHURES = False
FAMILLES_RIVIERE = ("river_mouth",)
GARDE_EMBOUCHURE_PX = 6        # les cases d'embouchure à moins d'une demi-unité de la côte gardent leur eau
FOND_NOUVELLE_MER = -0.05      # fond provisoire d'un pixel de terre de WH1 devenu mer (approfondi ensuite)
X_HEX, Z_HEX, Z_IMPAIR = 0.667995, 0.771334, 0.3857


def _moyenne_boite(a, r):
    p = np.pad(a, r + 1, mode="constant")
    s = p.cumsum(0).cumsum(1)
    n, m = a.shape
    k = 2 * r + 1
    return (s[k:k + n, k:k + m] - s[:n, k:k + m] - s[k:k + n, :m] + s[:n, :m]) / float(k * k)


def _bruit_lisse(forme, echelle, graine):
    rng = np.random.default_rng(graine)
    h, w = forme
    g = rng.uniform(-1, 1, (h // echelle + 2, w // echelle + 2))
    yy = (np.arange(h) / echelle)[:, None]
    xx = (np.arange(w) / echelle)[None, :]
    y0, x0 = yy.astype(int), xx.astype(int)
    ty, tx = yy - y0, xx - x0
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    return (g[y0, x0] * (1 - tx) * (1 - ty) + g[y0, x0 + 1] * tx * (1 - ty)
            + g[y0 + 1, x0] * (1 - tx) * ty + g[y0 + 1, x0 + 1] * tx * ty)


def _frontiere(m):
    f = np.zeros(m.shape, bool)
    f[1:] |= m[1:] != m[:-1]
    f[:-1] |= m[1:] != m[:-1]
    f[:, 1:] |= m[:, 1:] != m[:, :-1]
    f[:, :-1] |= m[:, 1:] != m[:, :-1]
    return f


def _distance(masque, portee):
    """Distance (px, dilatations 4-connexes, plafonnée à `portee`) au masque."""
    d = np.full(masque.shape, portee, np.float32)
    front = masque.copy()
    d[front] = 0
    for k in range(1, portee):
        v = front.copy()
        v[1:] |= front[:-1]
        v[:-1] |= front[1:]
        v[:, 1:] |= front[:, :-1]
        v[:, :-1] |= front[:, 1:]
        d[v & ~front] = k
        front = v
    return d


def colonies():
    """({clé : (x, z)} dans l'espace des hex, {port : [(x, z) des hex de port]})."""
    from caime_layers import read_layer
    import terrain_wh1_vers_terry as T
    pos = {k: tuple(v) for k, v in json.load(open(COLONIES, encoding="utf-8"))["keys"].items()}
    slots = np.asarray(read_layer(T.SLOTS)[1]).reshape(T.HEX_H, T.HEX_L)
    hex_port = {}
    for cle in PORTS:
        x, z = pos[cle]
        q0 = int(round(x / X_HEX))
        r0 = int(round((z - (Z_IMPAIR if q0 % 2 else 0.0)) / Z_HEX))
        hex_port[cle] = [(X_HEX * q, Z_HEX * r + (Z_IMPAIR if q % 2 else 0.0))
                         for r in range(r0 - 3, r0 + 4) for q in range(q0 - 3, q0 + 4)
                         if 0 <= r < T.HEX_H and 0 <= q < T.HEX_L and slots[r, q] == 1]
    return pos, hex_port


def gardes(forme, pas):
    """Pixels qui gardent le côté de WH1 : falaises de côte, objets de WH1, embouchures (tuiles de rivière)."""
    import tuiles_wh1
    import lire_props_wh1 as LP
    H, L = forme
    fam = tuiles_wh1.familles_par_case(ordre=list(FAMILLES_RIVIERE) + ["cliff_custom"])
    k = H // fam.shape[0]
    falaise = np.repeat(np.repeat(fam == "cliff_custom", k, 0), k, 1)[:H, :L]
    riviere = np.repeat(np.repeat(np.isin(fam, FAMILLES_RIVIERE), k, 0), k, 1)[:H, :L]
    objets = np.zeros((H, L), bool)
    for _, _, _, var, blob in LP.lots(LP.GLOBAL_PROPS):
        if var != 1:
            continue
        for o in LP.objets(blob):
            if o["drapeaux"][0] != 0:
                continue
            x, _, z = o["position"]
            i, j = int((H - 1.5) - z * pas + 0.5), int(x * pas - 0.5 + 0.5)
            if 0 <= i < H and 0 <= j < L:
                objets[i, j] = True
    return falaise, riviere, objets


def _dilater(m, n):
    for _ in range(n):
        p = np.pad(m, 1)
        out = m.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                out |= p[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]]
        m = out
    return m


def cote_naturelle(mer0, pas, positions=None, hex_port=None, protege=None):
    """(mer, bilan) : la mer de WH1 au pixel (`mer0`, ligne 0 au nord, `pas` px par unité) au trait de côte naturel.
    `protege` : (falaises, rivières, objets) de `gardes` ; calculés si absents."""
    import rivieres_wh1 as RW
    H, L = mer0.shape
    r3 = 3 ** 0.5 / 2
    if positions is None or hex_port is None:
        positions, hex_port = colonies()
    falaise, riviere, objets = protege if protege is not None else gardes(mer0.shape, pas)

    def ij(x, z):
        return (H - 1.5) - z * r3 * pas, x * pas - 0.5

    def disque(x, z, rayon, largeur):
        """(fenêtre, profil 0..1 valant 0,5 à `rayon`)"""
        ci, cj = ij(x, z)
        rr = int((rayon + 3 * largeur) * pas) + 3
        fen = (slice(max(int(ci) - rr, 0), min(int(ci) + rr + 1, H)), slice(max(int(cj) - rr, 0), min(int(cj) + rr + 1, L)))
        ii, jj = np.mgrid[fen[0], fen[1]]
        d = np.hypot((ii - ci) / (r3 * pas), (jj - cj) / pas)
        return fen, np.clip((rayon - d) / largeur + 0.5, 0, 1)

    f = (~mer0).astype(np.float64)
    for _ in range(3 if LISSAGE else 0):
        f = _moyenne_boite(f, RAYON_PX)
    if BRUIT and LISSAGE:
        f += BRUIT * (0.65 * _bruit_lisse((H, L), 18, 11) + 0.35 * _bruit_lisse((H, L), 7, 12))
    villes = np.zeros((H, L), bool)
    for cle, (x, z) in positions.items():
        if cle in PORTS:
            fen, p = disque(x, z, R_PORT, 0.15)
            f[fen] = np.maximum(f[fen], p)
            villes[fen] |= p > 0
            for hx, hz in hex_port.get(cle, []):
                fen2, p2 = disque(hx, hz, R_HEX_PORT, 0.12)
                f[fen2] = np.minimum(f[fen2], 1 - p2)
                villes[fen2] |= p2 > 0
        else:
            fen, p = disque(x, z, R_VILLE, 0.15)
            f[fen] = np.maximum(f[fen], p)
            villes[fen] |= p > 0
    for _ in range(2 if LISSAGE else 0):
        f = _moyenne_boite(f, 2)
    terre = f > 0.5
    d_cote = _distance(_frontiere(mer0), DMAX_PX + 2)
    tel_quel = (d_cote > DMAX_PX) & ~villes
    if GARDER_FALAISES:
        tel_quel |= _dilater(falaise, GARDE_FALAISE_PX) & ~villes
    tel_quel |= _dilater(objets, GARDE_OBJET_PX) & ~villes
    if GARDER_EMBOUCHURES:
        embouchure = riviere & (d_cote <= GARDE_EMBOUCHURE_PX)
        tel_quel |= _dilater(embouchure, 2) & mer0 & ~villes
    delta = np.zeros((H, L), bool)
    terre_delta = None
    if GARDER_DELTAS:
        import deltas_wh1
        if deltas_wh1.ACTIF:
            delta = _dilater(deltas_wh1.zone(H, L), 2) & ~villes
            if not LISSAGE_DELTAS_PX:
                tel_quel |= delta
    lab = RW.composantes(~mer0)
    tailles = np.bincount(lab[lab >= 0].ravel())
    petites = np.isin(lab, np.nonzero((tailles > 0) & (tailles <= ILE_MAX_PX))[0]) & (lab >= 0)
    if LISSAGE_DELTAS_PX:
        # (chaîne 14) deltas ET petites îles de WH1 : lissage doux au lieu du pixel de WH1 figé (l'îlot boisé du delta
        # d'Yremy restait un carré en escalier), fondu sur 8 px vers le lissage de la côte (pas de cran à la limite)
        doux = (delta | _dilater(petites, 3)) & ~villes
        fd = (~mer0).astype(np.float64)
        for _ in range(2):
            fd = _moyenne_boite(fd, LISSAGE_DELTAS_PX)
        w = np.clip(1.0 - _distance(doux, 9) / 8.0, 0.0, 1.0)
        terre = np.where(tel_quel & ~doux, terre, (w * fd + (1.0 - w) * f) > 0.5)
        tel_quel &= ~doux
        terre_delta = doux
    else:
        tel_quel |= _dilater(petites, 3)
    terre = np.where(tel_quel, ~mer0, terre)
    mer = ~terre
    # flaques de mer nées du flou, coupées du large : rendues à la terre (et les îlots de terre nés en mer, à la mer)
    lab_m = RW.composantes(mer)
    t_m = np.bincount(lab_m[lab_m >= 0].ravel())
    grande = int(np.argmax(t_m)) if len(t_m) else -1
    lab_0 = RW.composantes(mer0)
    mers_wh1 = set(np.unique(lab_m[(lab_0 >= 0) & (lab_m >= 0)]).tolist())
    flaque = (lab_m >= 0) & ~np.isin(lab_m, list(mers_wh1))
    mer &= ~flaque
    chg = mer != mer0
    bilan = {"pixels changés": int(chg.sum()), "terre -> mer": int((chg & mer).sum()), "mer -> terre": int((chg & ~mer).sum()),
             "gardés dans la bande côtière (objets, embouchures, îles" + (", falaises" if GARDER_FALAISES else "") + ")":
             int((tel_quel & (d_cote <= DMAX_PX)).sum()),
             "flaques rendues à la terre": int(flaque.sum()), "mer": f"{mer.mean():.3%} (WH1 {mer0.mean():.3%})",
             "deltas de WH1 gardés tels quels (px)": int(delta.sum()),
             "écart max du trait de côte (u)": round(float(_distance(_frontiere(mer0), DMAX_PX + 2)[_frontiere(mer)].max())
                                                     / pas, 2) if chg.any() else 0.0,
             "grande mer (px)": int(t_m[grande]) if grande >= 0 else 0}
    ports = {}
    for cle in PORTS:
        x, z = positions[cle]
        fen, p = disque(x, z, 1.0, 1e-6)
        ports[cle.split("_")[-1]] = f"{float(mer[fen][p > 0.5].mean()):.0%}"
    bilan["eau de mer dans 1 u des ports"] = ports
    return mer, bilan
