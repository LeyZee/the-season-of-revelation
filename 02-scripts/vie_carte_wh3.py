#!/usr/bin/env python3
"""
vie_carte_wh3.py - créatures et effets de vie de WH3 sur notre carte, cohérents avec le lore (session du rendu).

Accord de Charles (23.09.2026, 18 h 50 : « Vas-y pour les créatures sûres et les cascades ») sur la liste des candidats
« très cohérents et sûrs » de la recherche `05-journal\\2026-09-23-rendu-carte\\gabarits-ca\\vie-ambiante.json` (rapport
`rapport-vie-ambiante-wh3.md`) : ressources que CA pose lui-même en campagne dans WH3, émetteurs activés, réglages relevés
sur ses poses (échelle, hauteur au-dessus du relief, lacet, espacement, masque de culture) :
- esprits d'Athel Loren (`wh_dlc05_campaign_enviro_sprites_wide`) dans les clairières profondes, loin des 21 esprits de
  WH1 (les colonies elfes les ont déjà par leurs prefabs de CA) ;
- chauves-souris (`wh3_main_campaign_enviro_bat_swarm`) aux abords des châteaux de Mousillon ;
- mouches (`wh2_main_campaign_fly_swarm`) sur les marais de Mousillon ;
- tourbillons de feuilles (`wh3_dlc20_campaign_enviro_leaves_burst`) aux lisières d'Athel Loren et dans les bois de
  Bretonnie (masque de culture de CA) ;
- chevaux blancs elfes (scènes `hr1_hef_*`) à la place des chevaux de WH1 des Salles d'Equos (accord de Charles) ;
- pégases (`pegasus1.csc`) sur les pentes des Montagnes Grises autour de Parravon, la cité des chevaliers pégases ;
- grands aigles (`bi1_fly_loop_01.csc`) au-dessus des sommets des Montagnes Grises.
Écarté : `wh_dlc05_campaign_forest_spirits_encircling` (déjà dans les prefabs de colonie elfe de CA).

Les cascades de CA aux sources de montagne viendront dans ce module (`cascades`), après la mesure du plantage de rendu par
la construction (les effets de particules y sont suspects) ; de même, `entites` n'est branché dans `ajouts_carte_wh3`
qu'avec l'accord de la construction (AJOUTS["vie"]).

Usage (module) :
    blocs, ambiance, bilan = vie_carte_wh3.creatures(r, carte, ambiance)
    python vie_carte_wh3.py      # essai à blanc sur le cache d'essai_complet (positions, lieux)
"""

import hashlib
import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ajouts_carte_wh3 import RX_POS, masque_provinces, scene, vfx  # noqa: E402

CREATURES = {
    "esprits": True, "chauves_souris": True, "mouches": True, "feuilles": True, "chevaux": True, "pegases": True,
    "aigles": True,
}
BRETONNIE = ("aquitaine", "bastonne", "bordeleaux", "brionne", "carcassonne", "gisoreux", "montfort", "parravon",
             "quenelles")
MONTAGNES_GRISES = ("grey_mountains", "grey_mountains_2")

ESPRITS = "wh_dlc05_campaign_enviro_sprites_wide"
ESPRITS_WH1 = "wh_dlc05_campaign_enviro_sprites"
N_ESPRITS, ECART_ESPRITS, LACET_ESPRITS = 5, 8.0, -60.0
CHAUVES_SOURIS = "wh3_main_campaign_enviro_bat_swarm"
CHATEAUX_MOUSILLON = ("wh_dlc05_mousillon_castle_rachard", "wh_dlc05_mousillon_mousillon", "wh_dlc05_mousillon_yremy",
                      "wh_dlc05_mousillon_martel")
N_CHAUVES_SOURIS, ECART_CHAUVES_SOURIS = 3, 15.0
CHAUVES_SOURIS_ECHELLE, CHAUVES_SOURIS_HAUT, CHAUVES_SOURIS_LACET = 0.42, 0.17, -10.0
CHAUVES_SOURIS_RECUL = 0.9          # u : à côté des murs, pas au centre de la colonie
MOUCHES = "wh2_main_campaign_fly_swarm"
N_MOUCHES, ECART_MOUCHES, MOUCHES_ECHELLE, MOUCHES_HAUT = 5, 10.0, 0.42, 0.4
MOUCHES_LACETS = (132.0, 144.0, -51.0, -157.0)
FEUILLES = "wh3_dlc20_campaign_enviro_leaves_burst"
N_FEUILLES, ECART_FEUILLES, FEUILLES_HAUT = 32, 12.0, 0.05
FEUILLES_ECHELLES = (0.4, 0.4, 0.4, 0.5, 0.6)       # proportions de CA : 0,4 le plus souvent
FEUILLES_LACETS = (-128.0, 0.0)
FEUILLES_MASQUE = "wh_dlc03_bst_beastmen,wh_main_brt_bretonnia,wh_dlc05_wef_wood_elves,wh2_main_hef_high_elves,wh3_main_cth_cathay"
LISIERE_AL = 4.0                    # u : bande intérieure d'Athel Loren le long de sa frontière
# Charles (23.09.2026, 20 h 15) : « dans les Salles d'Equos, il y a déjà des chevaux dans Warhammer 1, mais tu peux les
# remplacer avec les chevaux blancs ». Les 3 chevaux de WH1 de la région (2 au pâturage, 1 couché) deviennent les
# chevaux blancs elfes de CA de même attitude, à leurs place, orientation et échelle de WH1.
EQUOS = "wh_dlc05_cavaroc_halls_of_equos"
CHEVAUX_WH1 = "composite_scene/campaign_fauna/hr1/"
CHEVAUX_BLANCS = {"hr1_grazing/hr1_grazing_01.csc": "hef_white_horse/hr1_hef_grazing_01.csc",
                  "hr1_grazing/hr1_grazing_02.csc": "hef_white_horse/hr1_hef_grazing_02.csc",
                  "hr1_grazing/hr1_grazing_03.csc": "hef_white_horse/hr1_hef_grazing_03.csc",
                  "lying_down/hr1_lyingdown_alert_01.csc": "hef_white_horse/hr1_hef_lyingdown_alert_01.csc",
                  "lying_down/hr1_lyingdown_sleeping_01.csc": "hef_white_horse/hr1_hef_lyingdown_sleeping_01.csc",
                  "stand/hr1_stand_01.csc": "hef_white_horse/hr1_hef_stand_01.csc"}
PEGASE = "composite_scene/campaign_fauna/flying/pegasus1.csc"
PARRAVON = ("wh_dlc05_parravon_parravon", "wh_dlc05_parravon_grunere", "wh_dlc05_parravon_montlac")
N_PEGASES, ECART_PEGASES, PEGASE_ECHELLE, PEGASE_HAUT, PEGASE_RAYON = 2, 20.0, 0.3, 3.0, 14.0
AIGLE = "composite_scene/campaign_fauna/bi1/bi1_fly_loop_01.csc"
N_AIGLES, ECART_AIGLES, AIGLE_ECHELLE, AIGLE_HAUT, AIGLE_LACET = 2, 30.0, 0.1, 5.0, -162.0


def _hash01(*cles):
    """Nombre déterministe dans [0, 1) (choix reproductibles d'une chaîne à l'autre)."""
    h = hashlib.sha1(":".join(str(c) for c in cles).encode()).hexdigest()
    return int(h[:8], 16) / 2 ** 32


def _positions(ambiance, motif):
    """[(x, y, z)] des entités d'ambiance de WH1 dont le bloc contient `motif`."""
    out = []
    for blocs in ambiance.values():
        for b in blocs:
            if motif in b:
                p = RX_POS.search(b)
                if p:
                    out.append(tuple(float(c) for c in p.group(1).split()))
    return out


# Positions des colonies tirées de map_data.esf (construction, 23.09.2026, 23 h 33, ports remis à leur hex de WH1) : la
# position « affichage » de `positions_colonies.json` (session de l'extension) oubliait le décalage des colonnes impaires.
POSITIONS_COLONIES = os.path.join(r"C:\TotalWar-CampaignMap", "04-projets", "saison-des-revelations",
                                  "relief-wh1", "colonies_map_data.json")


def colonies_nommees(carte):
    """{clé de région : (x, z)} : position de chaque colonie dans map_data.esf (`relief-wh1\\colonies_map_data.json`) ; à
    défaut, centre des hex d'emplacement principal (SLOTS == 0)."""
    if os.path.exists(POSITIONS_COLONIES):
        d = json.load(open(POSITIONS_COLONIES, encoding="utf-8"))
        return {k: (float(v[0]), float(v[1])) for k, v in d["keys"].items()}
    import captage_campagne as CC
    import terrain_wh1_vers_terry as T
    from caime_layers import read_layer
    slots = np.asarray(read_layer(T.SLOTS)[1]).reshape(T.HEX_H, T.HEX_L)
    reg, _ = CC.calques()
    noms = CC.noms_regions()
    out = {}
    for k, nom in enumerate(noms):
        # SLOTS : 0 = emplacement principal de ville (-1 ailleurs)
        lig, col = np.nonzero((slots == 0) & (reg == k))
        if not len(lig):
            continue
        # centre de l'hex (8 px par hex, colonnes impaires décalées d'un demi-hex) -> pixel -> monde
        xs = col * 8 + 4
        ys = (carte.H - 1) - (lig * 8 + 4 * (col & 1) + 4)
        i, j = float(np.mean(ys)), float(np.mean(xs))
        out[nom] = carte.monde(i, j)
    return out


def _foret(r, carte):
    """(foret, densite) sur la grille des rasters : cases d'arbre de WH1, et part d'arbres dans ~1,2 u."""
    a = np.asarray(r["arbres"]) != 255
    f = np.repeat(np.repeat(a, 4, 0), 4, 1)[:carte.H, :carte.L]
    from terrain_wh1_vers_terry import moyenne_boite
    rayon = int(1.2 * carte.pas)
    k = 2 * rayon + 1
    d = moyenne_boite(f.astype(np.float64), rayon) / (k * k)
    return f, d


def _choisir(candidats, score, carte, n, ecart, deja=(), graine="", sous_pas=6):
    """Jusqu'à `n` points (x, z) choisis par score décroissant parmi les pixels `candidats`, à `ecart` u au moins les uns
    des autres et des points `deja` ; sous-échantillonnage de `sous_pas` px pour la vitesse, ex aequo départagés par un
    bruit déterministe."""
    m = candidats[::sous_pas, ::sous_pas]
    ii, jj = np.nonzero(m)
    if not len(ii):
        return []
    s = score[::sous_pas, ::sous_pas][ii, jj] + np.array([_hash01(graine, a, b) * 1e-3 for a, b in zip(ii, jj)])
    ordre = np.argsort(-s)
    pris = [tuple(p[:2]) if len(p) == 2 else (p[0], p[2]) for p in deja]
    out = []
    for o in ordre:
        x, z = (float(v) for v in carte.monde(ii[o] * sous_pas, jj[o] * sous_pas))
        if all(math.hypot(x - a, z - b) >= ecart for a, b in pris):
            out.append((x, z))
            pris.append((x, z))
            if len(out) >= n:
                break
    return out


def chevaux_blancs(ambiance, dans_al=None):
    """(ambiance, liste) : dans la région des Salles d'Equos, et (24.09.2026, Charles, vidéo V2 : « un cheval de l'Empire en
    Athel Loren ; des chevaux elfiques blancs en Athel Loren, ceux de l'Empire et de Bretonnie hors de la forêt ») partout
    où `dans_al(x, z)` est vrai, chaque scène de cheval de WH1 prend le cheval blanc elfe de CA de même attitude (même
    entité : identifiant, place, orientation et échelle gardés)."""
    neuve, changes = {}, []
    for region, blocs in ambiance.items():
        garde = []
        for b in blocs:
            m = re.search(r'<ECCompositeScene path="' + re.escape(CHEVAUX_WH1) + r'([^"]+)"', b)
            en_al = False
            if m and dans_al is not None:
                p = RX_POS.search(b)
                if p:
                    x_, _, z_ = (float(v) for v in p.group(1).split())
                    en_al = dans_al(x_, z_)
            if (region == EQUOS or en_al) and m and m.group(1) in CHEVAUX_BLANCS:
                b = b.replace(CHEVAUX_WH1 + m.group(1), CHEVAUX_WH1 + CHEVAUX_BLANCS[m.group(1)])
                p = RX_POS.search(b)
                changes.append((m.group(1).rsplit("/", 1)[-1], tuple(round(float(v), 1) for v in p.group(1).split()[::2])))
            garde.append(b)
        neuve[region] = garde
    return neuve, changes


def creatures(r, carte, ambiance, colonies=None):
    """(blocs d'entités, ambiance, bilan) : les créatures et effets de vie de CREATURES (les chevaux de WH1 d'Equos
    changés en place dans l'ambiance)."""
    blocs, bilan = [], {}
    H, L = carte.H, carte.L
    colonies = colonies if colonies is not None else colonies_nommees(carte)
    al = masque_provinces(H, L, set(__import__("ponts_wh1").ATHEL_LOREN))
    mousillon = masque_provinces(H, L, {"mousillon"})
    bretonnie = masque_provinces(H, L, set(BRETONNIE))
    grises = masque_provinces(H, L, set(MONTAGNES_GRISES))
    foret, densite = _foret(r, carte)
    import ajouts_carte_wh3 as A
    villes = A.colonies(r, carte, 2.0)
    sec = ~carte.eau & ~carte.route & ~villes
    plat = carte.pente < 0.5
    hauteur = np.asarray(r["hauteur"], np.float64)
    montagnes = np.asarray(r["montagnes"], bool)

    def y_sol(x, z):
        return carte.y(x, z)

    if CREATURES["esprits"]:
        dist_hors_al = carte.distance(~al, 8.0)
        cand = al & ~foret & sec & plat & (densite >= 0.55) & (dist_hors_al >= 4.0)
        deja = _positions(ambiance, f'vfx="{ESPRITS_WH1}"')
        pts = _choisir(cand, densite, carte, N_ESPRITS, ECART_ESPRITS, deja, "esprits")
        for x, z in pts:
            blocs.append(vfx(f"vie:esprits:{x:.2f}:{z:.2f}", ESPRITS, (x, y_sol(x, z), z), (0.0, LACET_ESPRITS, 0.0), 1.0))
        bilan["esprits d'Athel Loren (clairières profondes)"] = [(round(x, 1), round(z, 1)) for x, z in pts]

    if CREATURES["chauves_souris"]:
        pts = []
        for cle in CHATEAUX_MOUSILLON:
            if cle not in colonies or len(pts) >= N_CHAUVES_SOURIS:
                continue
            cx, cz = colonies[cle]
            ang = math.radians(135.0 + 90.0 * _hash01("chauves", cle))       # côté nord-ouest à sud-ouest
            x, z = cx + CHAUVES_SOURIS_RECUL * math.cos(ang), cz + CHAUVES_SOURIS_RECUL * math.sin(ang)
            if all(math.hypot(x - a, z - b) >= ECART_CHAUVES_SOURIS for a, b in pts):
                pts.append((x, z))
        for x, z in pts:
            blocs.append(vfx(f"vie:chauves_souris:{x:.2f}:{z:.2f}", CHAUVES_SOURIS,
                             (x, y_sol(x, z) + CHAUVES_SOURIS_HAUT, z), (0.0, CHAUVES_SOURIS_LACET, 0.0),
                             CHAUVES_SOURIS_ECHELLE))
        bilan["chauves-souris (châteaux de Mousillon)"] = [(round(x, 1), round(z, 1)) for x, z in pts]

    if CREATURES["mouches"]:
        melange = np.asarray(r["melange"])
        marais = np.isin(melange, _indices_groupes(("marsh0", "marsh1", "marsh2", "marsh3")))
        cand = mousillon & marais & ~villes & ~carte.route
        score = A_boite(marais.astype(np.float64), int(1.0 * carte.pas))
        pts = _choisir(cand, score, carte, N_MOUCHES, ECART_MOUCHES, (), "mouches", sous_pas=4)
        for k, (x, z) in enumerate(pts):
            blocs.append(vfx(f"vie:mouches:{x:.2f}:{z:.2f}", MOUCHES, (x, y_sol(x, z) + MOUCHES_HAUT, z),
                             (0.0, MOUCHES_LACETS[k % len(MOUCHES_LACETS)], 0.0), MOUCHES_ECHELLE))
        bilan["mouches (marais de Mousillon)"] = [(round(x, 1), round(z, 1)) for x, z in pts]

    if CREATURES["feuilles"]:
        dist_hors_al = carte.distance(~al, LISIERE_AL + 1)
        lisiere = al & (dist_hors_al <= LISIERE_AL)
        cand = foret & (densite >= 0.5) & (lisiere | (bretonnie & ~mousillon)) & sec & ~montagnes & (carte.pente < 0.8)
        pts = _choisir(cand, densite, carte, N_FEUILLES, ECART_FEUILLES, (), "feuilles")
        for x, z in pts:
            e = FEUILLES_ECHELLES[int(_hash01("feuilles:echelle", round(x, 2), round(z, 2)) * len(FEUILLES_ECHELLES))]
            lacet = FEUILLES_LACETS[int(_hash01("feuilles:lacet", round(x, 2), round(z, 2)) * len(FEUILLES_LACETS))]
            blocs.append(vfx(f"vie:feuilles:{x:.2f}:{z:.2f}", FEUILLES, (x, y_sol(x, z) + FEUILLES_HAUT, z),
                             (0.0, lacet, 0.0), e, FEUILLES_MASQUE))
        bilan["tourbillons de feuilles (lisières d'Athel Loren, bois de Bretonnie)"] = len(pts)

    if CREATURES["chevaux"]:
        ambiance, changes = chevaux_blancs(ambiance, lambda x, z: bool(al[carte.px(x, z)]))
        bilan["chevaux de WH1 d'Athel Loren (Salles d'Equos comprises) devenus chevaux blancs elfes"] = changes

    if CREATURES["pegases"]:
        centres = [colonies[c] for c in PARRAVON if c in colonies]
        ii, jj = np.mgrid[0:H, 0:L]
        pres = np.zeros((H, L), bool)
        for cx, cz in centres:
            xs, zs = (jj + 0.5) / carte.pas, ((H - 1.5) - ii) / carte.pas / (3 ** 0.5 / 2)
            pres |= np.hypot(xs - cx, zs - cz) <= PEGASE_RAYON
        cand = pres & (montagnes | (carte.pente > 1.0)) & ~villes
        deja = _positions(ambiance, "pegasus1.csc")
        pts = _choisir(cand, hauteur, carte, N_PEGASES, ECART_PEGASES, deja, "pegases")
        for x, z in pts:
            lacet = -180.0 + 360.0 * _hash01("pegase", round(x, 2))
            blocs.append(scene(f"vie:pegase:{x:.2f}:{z:.2f}", PEGASE, (x, y_sol(x, z) + PEGASE_HAUT, z), (0.0, lacet, 0.0),
                               PEGASE_ECHELLE))
        bilan["pégases (pentes autour de Parravon)"] = [(round(x, 1), round(z, 1)) for x, z in pts]

    if CREATURES["aigles"]:
        cand = grises & (montagnes | (carte.pente > 1.0))
        deja = _positions(ambiance, "bi1_fly_loop")
        pts = _choisir(cand, hauteur, carte, N_AIGLES, ECART_AIGLES, deja, "aigles")
        for x, z in pts:
            blocs.append(scene(f"vie:aigle:{x:.2f}:{z:.2f}", AIGLE, (x, y_sol(x, z) + AIGLE_HAUT, z),
                               (0.0, AIGLE_LACET, 0.0), AIGLE_ECHELLE))
        bilan["grands aigles (sommets des Montagnes Grises)"] = [(round(x, 1), round(z, 1)) for x, z in pts]
    return blocs, ambiance, bilan


# ------------------------------------------------------------------ cascades de CA aux sources de montagne
# Recherche `gabarits-ca\sources.json` (sources de rivière des Empires, 5 exemples, entités relevées dans le repère de la
# source : le long de l'axe vers l'aval, en travers à gauche, hauteur par rapport à l'eau et au sol, lacet relatif) :
# l'exemple 48 (« pied de montagne, cascade complète », Massif Orcal) est la recette de CA pour une petite source au pied
# d'une montagne : nappe d'eau + écume (mêmes transformations), effet de chute, éclaboussures, son, rochers et falaises
# derrière. On en reprend la chute principale (entités à moins de CASCADE_RAYON de la source ; la seconde chute, latérale, à
# 1,4 u, est laissée) et on la transplante sur nos petites sources de WH1 au pied d'une montagne de WH1.
SOURCES_CA = os.path.join(r"C:\TotalWar-CampaignMap", "05-journal", "2026-09-23-rendu-carte",
                          "gabarits-ca", "sources.json")
CASCADE_EXEMPLE, CASCADE_RAYON = 48, 1.3
CASCADE_MONTAGNE_MAX = 1.0          # u : maillage de montagne de WH1 à moins de cette distance du bout de la source
CASCADE_PENTE_MIN = 0.15            # sol à 1 u en amont moins l'eau (CA, exemple 48 : 0,17)
CASCADE_WH1_MIN = 1.5               # u : pas de cascade de CA près d'une cascade de WH1
CASCADE_ECART = 6.0                 # u entre deux de nos cascades (le même assemblage répété de près ferait artificiel)
# La nappe de CA (exemple 48, échelle 0,42) monte 1,44 u au-dessus de l'eau ; CA l'adosse à une falaise. Nos pentes sont
# plus douces : la chute de la cascade (nappe, écume, effets de chute et d'éclaboussures, hauteur et échelle) est ramenée à
# la chute réelle du sol (sol à CASCADE_RECUL en amont de la nappe moins l'eau), jamais au-delà de celle de CA ; en deçà de
# CASCADE_CHUTE_MIN, pas de cascade.
CASCADE_HAUT_CA = 1.44
CASCADE_RECUL = 0.3
CASCADE_CHUTE_MIN = 0.4
EAU_GENRES = ("vfx", "son")         # posés par rapport à l'eau ; nappe et écume aussi (maillages water_fall)


def _gabarit_cascade():
    d = json.load(open(SOURCES_CA, encoding="utf-8"))
    ex = next(e for e in d["exemples"] if e["numero"] == CASCADE_EXEMPLE)
    return [e for e in ex["entites_a_1_5u"] if e["distance"] <= CASCADE_RAYON]


def sources_de_montagne(r, carte, objets_wh1_xz=()):
    """[(x, z, y_eau, angle_axe_deg, bilan)] : petites sources de WH1 (tuiles river_start effilées) dont le bout amont est
    à moins de CASCADE_MONTAGNE_MAX d'un maillage de montagne, avec une pente derrière, loin des cascades de WH1."""
    import rivieres_wh1 as RW
    import tuiles_wh1 as T                     # grille des tuiles de WH1 : 800 x 881 cases, lignes depuis le sud
    eau = np.asarray(r["eau_rivieres"], np.float64)
    zone_eau = np.nan_to_num(eau, nan=-1e9) > np.asarray(r["hauteur"], np.float64)   # l'eau VISIBLE (pas le ruban enterré)
    montagnes = np.asarray(r["montagnes"], bool)
    d_mont = carte.distance(montagnes, CASCADE_MONTAGNE_MAX + 1.0)
    n_fen = int(RW.SOURCE_FENETRE * carte.pas)
    out, rejets = [], collections_counter()
    for p in RW.poses():
        if p.famille != "river_start":
            continue
        taille = p.nom.rstrip("/").rsplit("/", 1)[-1].split("_", 1)[0]
        if taille not in RW.SOURCE_FAMILLES_EFFILEES:
            rejets["lac de source"] += 1
            continue
        W, Ht = (p.H, p.W) if p.code & 0xF0 in (0x20, 0x80) else (p.W, p.H)
        c0, c1 = p.x * 4, (p.x + W) * 4
        r0, r1 = (T.HAUTEUR - (p.y + Ht)) * 4, (T.HAUTEUR - p.y) * 4
        ci, cj = (r0 + r1) // 2, (c0 + c1) // 2
        R0, R1, C0, C1 = max(ci - n_fen, 0), min(ci + n_fen, carte.H), max(cj - n_fen, 0), min(cj + n_fen, carte.L)
        z = zone_eau[R0:R1, C0:C1]
        if not z.any():
            rejets["pas d'eau visible près de la tuile"] += 1
            continue
        # la composante d'eau visible la plus proche du centre de la tuile (le ruban naît sous la berge et n'affleure
        # qu'un peu en aval) ; son bout amont = le pixel le plus loin du bord de la fenêtre, le long de l'eau
        lab = RW.composantes(z)
        ii_, jj_ = np.nonzero(z)
        k_ = int(np.argmin((ii_ - (ci - R0)) ** 2 + (jj_ - (cj - C0)) ** 2))
        zone = lab == lab[ii_[k_], jj_[k_]]
        bord = np.zeros_like(zone)
        bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
        dd = RW._distance_dans(zone, zone & bord)
        dt = np.where(zone & np.isfinite(dd), dd, -1.0)
        if dt.max() < 0.3 * n_fen:
            rejets["pas de bout amont"] += 1
            continue
        i, j = np.unravel_index(int(np.argmax(dt)), dt.shape)
        pt = np.zeros_like(zone)
        pt[i, j] = True
        g = RW._distance_dans(zone, pt) / carte.pas
        aval = zone & (g >= 0.8) & (g <= 1.2)
        if not aval.any():
            rejets["axe introuvable"] += 1
            continue
        ia, ja = np.nonzero(aval)
        I, J = R0 + i, C0 + j
        x0, z0 = (float(v) for v in carte.monde(I, J))
        xa, za = carte.monde(R0 + float(ia.mean()), C0 + float(ja.mean()))
        dx, dz = xa - x0, za - z0
        n = math.hypot(dx, dz)
        dx, dz = dx / n, dz / n
        y_eau = float(eau[I, J])
        if d_mont[I, J] > CASCADE_MONTAGNE_MAX:
            rejets["loin des montagnes"] += 1
            continue
        pente = carte.y(x0 - dx, z0 - dz) - y_eau
        if pente < CASCADE_PENTE_MIN:
            rejets["pas de pente derrière"] += 1
            continue
        if any(math.hypot(x0 - a, z0 - b) < CASCADE_WH1_MIN for a, b in objets_wh1_xz):
            rejets["cascade de WH1 à côté"] += 1
            continue
        out.append((x0, z0, y_eau, math.degrees(math.atan2(dz, dx)),
                    {"montagne": round(float(d_mont[I, J]), 2), "pente_1u": round(pente, 2)}))
    # la plus pentue d'abord ; une autre à moins de CASCADE_ECART est laissée
    garde = []
    for s in sorted(out, key=lambda s: -s[4]["pente_1u"]):
        if all(math.hypot(s[0] - g[0], s[1] - g[1]) >= CASCADE_ECART for g in garde):
            garde.append(s)
        else:
            rejets["trop près d'une autre cascade"] += 1
    return garde, dict(rejets)


def collections_counter():
    import collections
    return collections.Counter()


def cascades(r, carte, ambiance, objets=None):
    """(blocs, bilan) : la chute principale de l'exemple 48 de CA transplantée à chaque source de montagne."""
    gab = _gabarit_cascade()
    chutes_wh1 = [(x, z) for x, _, z in _positions(ambiance, "waterfall")]
    if objets:
        for blocs in objets.values():
            for b in blocs:
                if "waterfall" in b:
                    p = RX_POS.search(b)
                    if p:
                        x, _, z = (float(v) for v in p.group(1).split())
                        chutes_wh1.append((x, z))
    sources, rejets = sources_de_montagne(r, carte, chutes_wh1)
    blocs, bilan = [], {"sources de montagne retenues": len(sources), "écartées": rejets, "positions": []}
    import ajouts_carte_wh3 as A
    nappe = next(e for e in gab if "vfx_campaign_waterfall_test" in e["modele"])
    retenues = 0
    for k, (x0, z0, y_eau, angle, info) in enumerate(sources):
        t = -angle
        tr = math.radians(t)

        def monde(le_long, travers):
            return (x0 + le_long * math.cos(tr) + travers * math.sin(tr),
                    z0 - le_long * math.sin(tr) + travers * math.cos(tr))
        # chute réelle derrière la nappe (en amont, le long de l'axe)
        xn, zn = monde(nappe["le_long"] - CASCADE_RECUL, nappe["travers"])
        chute = carte.y(xn, zn) - y_eau
        if chute < CASCADE_CHUTE_MIN:
            bilan["écartées"]["chute trop faible"] = bilan["écartées"].get("chute trop faible", 0) + 1
            continue
        f = min(1.0, chute / CASCADE_HAUT_CA)
        for n, e in enumerate(gab):
            X, Z = monde(e["le_long"], e["travers"])
            chute_ = "water_fall" in e["modele"].lower() or "waterfall" in e["modele"] or "waterplashes" in e["modele"]
            eau_ = e["genre"] in EAU_GENRES or chute_
            dy = e["dy_eau"] * (f if chute_ else 1.0)
            Y = y_eau + dy if eau_ else carte.y(X, Z) + e["dy_sol"]
            rot = (e["rotation"][0], t + e["lacet_relatif"], e["rotation"][2])
            ech = tuple(v * f for v in e["echelle"]) if chute_ else tuple(e["echelle"])
            graine = f"cascade:{k}:{n}:{x0:.2f}:{z0:.2f}"
            if e["genre"] == "vfx":
                blocs.append(A.vfx(graine, e["modele"], (X, Y, Z), rot, ech))
            elif e["genre"] == "son":
                blocs.append(A.son(graine, e["modele"], (X, Y, Z)))
            elif e["genre"] in ("mesh", "decal"):
                blocs.append(A.maillage(graine, e["modele"], (X, Y, Z), rot, ech, decalque=e["genre"] == "decal"))
        retenues += 1
        bilan["positions"].append((round(x0, 1), round(z0, 1), dict(info, chute=round(chute, 2), echelle=round(f, 2))))
    bilan["sources de montagne retenues"] = retenues
    return blocs, bilan


# LES CASCADES DE WH1 VISIBLES DE LOIN (24.09.2026, 04 h 10, session du rendu ; vidéo de Charles et relevé de la construction :
# sous la Clairière Royale, « trois ou quatre chutes blanches tombent d'une falaise » dans WH1, la gorge est vide dans WH3).
# Les cascades de WH1 sont des effets de particules (`wh_main_campaign_enviro_waterfall`, 22 poses, et leurs éclaboussures),
# bien posés et présents dans WH3, mais que WH3 ne dessine que de près. À chaque groupe de ces effets (à moins de
# CASCADE_WH1_GROUPE), la chute d'eau de CA de l'exemple 48 (nappe, écume, effets de chute et d'éclaboussures, son ; pas ses
# rochers : les falaises sont celles de WH1) est posée au pied de la paroi, dans l'axe de la plus forte pente, à la hauteur
# de la chute réelle du sol (jamais au-delà de celle de CA).
CASCADE_WH1_GROUPE = 1.5
CASCADE_WH1_CHUTE_MIN = 0.3


def cascades_wh1(r, carte, ambiance, objets=None):
    """(blocs, bilan) : les nappes de CA aux cascades de WH1 (voir CASCADE_WH1_*) ; pas là où WH1 a déjà un modèle de
    cascade (objets `waterfall` de `objets`, à moins de CASCADE_WH1_GROUPE)."""
    gab = [e for e in _gabarit_cascade()
           if e["genre"] in EAU_GENRES or "water_fall" in e["modele"].lower() or "waterfall" in e["modele"]
           or "waterplashes" in e["modele"]]
    modeles_wh1 = []
    for blocs_ in (objets or {}).values():
        for b in blocs_:
            if "waterfall" in b and "<ECMesh" in b:
                p = RX_POS.search(b)
                if p:
                    x, _, z = (float(v) for v in p.group(1).split())
                    modeles_wh1.append((x, z))
    sites = []
    for x, _, z in _positions(ambiance, "enviro_waterfall"):
        if any(math.hypot(x - a, z - b) < CASCADE_WH1_GROUPE for a, b in modeles_wh1):
            continue
        for s in sites:
            if math.hypot(s[0] / s[2] - x, s[1] / s[2] - z) < CASCADE_WH1_GROUPE:
                s[0] += x
                s[1] += z
                s[2] += 1
                break
        else:
            sites.append([x, z, 1])
    import ajouts_carte_wh3 as A
    blocs, bilan = [], {"effets de cascade de WH1 (groupes)": len(sites), "écartés (chute trop faible)": 0, "positions": []}
    for k, (sx, sz, n) in enumerate(sites):
        cx, cz = sx / n, sz / n
        e = 0.4
        gx = (carte.y(cx + e, cz) - carte.y(cx - e, cz)) / (2 * e)
        gz = (carte.y(cx, cz + e) - carte.y(cx, cz - e)) / (2 * e)
        g = math.hypot(gx, gz)
        if g < 1e-6:
            bilan["écartés (chute trop faible)"] += 1
            continue
        dx, dz = -gx / g, -gz / g                              # vers l'aval
        y_bas, s_bas = min((float(carte.y(cx + dx * s, cz + dz * s)), float(s)) for s in np.linspace(0.0, 1.5, 16))
        y_haut = max(float(carte.y(cx - dx * s, cz - dz * s)) for s in np.linspace(0.0, 1.0, 11))
        chute = y_haut - y_bas
        if chute < CASCADE_WH1_CHUTE_MIN:
            bilan["écartés (chute trop faible)"] += 1
            continue
        x0, z0 = cx + dx * s_bas, cz + dz * s_bas
        t = -math.degrees(math.atan2(dz, dx))
        tr = math.radians(t)
        f = min(1.0, chute / CASCADE_HAUT_CA)

        def monde(le_long, travers):
            return (x0 + le_long * math.cos(tr) + travers * math.sin(tr),
                    z0 - le_long * math.sin(tr) + travers * math.cos(tr))
        for m, ent in enumerate(gab):
            X, Z = monde(ent["le_long"], ent["travers"])
            chute_ = ("water_fall" in ent["modele"].lower() or "waterfall" in ent["modele"]
                      or "waterplashes" in ent["modele"])
            Y = y_bas + ent["dy_eau"] * (f if chute_ else 1.0)
            rot = (ent["rotation"][0], t + ent["lacet_relatif"], ent["rotation"][2])
            ech = tuple(v * f for v in ent["echelle"]) if chute_ else tuple(ent["echelle"])
            graine = f"cascade_wh1:{k}:{m}:{x0:.2f}:{z0:.2f}"
            if ent["genre"] == "vfx":
                blocs.append(A.vfx(graine, ent["modele"], (X, Y, Z), rot, ech))
            elif ent["genre"] == "son":
                blocs.append(A.son(graine, ent["modele"], (X, Y, Z)))
            elif ent["genre"] in ("mesh", "decal"):
                blocs.append(A.maillage(graine, ent["modele"], (X, Y, Z), rot, ech, decalque=ent["genre"] == "decal"))
        bilan["positions"].append((round(x0, 1), round(z0, 1), round(chute, 2), round(f, 2)))
    return blocs, bilan


def A_boite(champ, rayon):
    """Moyenne sur une boîte de côté 2 x rayon + 1."""
    from terrain_wh1_vers_terry import moyenne_boite
    k = 2 * rayon + 1
    return moyenne_boite(champ, rayon) / (k * k)


TEXTURE_ARRAYS = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\working_data"
                  r"\terrain\campaigns\wh_dlc05_wood_elves_map_1\global_map\texture_arrays.xml")


def _indices_groupes(noms):
    """Indices des groupes de texture de noms donnés (liste compilée de la carte, 144 groupes de CA)."""
    groupes = re.findall(r"<group>([^<]+)</group>", open(TEXTURE_ARRAYS, encoding="utf-8").read())
    return [groupes.index(n) for n in noms if n in groupes]


def main():
    import pickle
    sys.stdout.reconfigure(encoding="utf-8")
    cache = os.path.join(os.environ.get("TEMP", ""), "claude", "C--Users-USER-Downloads-TotalWar-CampaignMap",
                         "a0404878-ed8e-4f26-b1d4-9df649a8e40e", "scratchpad", "essai_r.pkl")
    if len(sys.argv) > 1:
        cache = sys.argv[1]
    r = pickle.load(open(cache, "rb"))
    import ajouts_carte_wh3 as A
    import entites_wh1
    carte = A.Carte(r)
    ambiance = entites_wh1.entites_ambiance(recaler_y=lambda x, y, z: y, bilan={})
    blocs, ambiance, bilan = creatures(r, carte, ambiance)
    print(f"{len(blocs)} entités ajoutées")
    for k, v in bilan.items():
        print(f"  {k} : {v}")
    blocs_c, bilan_c = cascades(r, carte, ambiance)
    print(f"cascades : {len(blocs_c)} entités ; {bilan_c['sources de montagne retenues']} sources ; écartées "
          f"{bilan_c['écartées']}")
    for p in bilan_c["positions"]:
        print(f"   {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
