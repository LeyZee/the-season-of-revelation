#!/usr/bin/env python3
"""
textures_tuiles_wh1.py - les textures que WH1 posait par ses tuiles, absentes de son mélange global.

Pourquoi (23.09.2026, décodage des `blend0.dds` des tuiles, `scratchpad\\tuiles_blend\\rapport.md` de la revue ; GUIDE
§ 15, n° 114) : `global_map\\global_blend.dds` de WH1 ne porte que la texture du « climat » (herbe `grass_a2` à 98,8 %
sous ses tuiles de mer, à 77,6 % sous ses routes) ; la texture propre de chaque tuile vient de son `blend0.dds` et de sa
fiche (`terrain/tiles/campaign/_tile_database/tiles/<famille>_<tuile>.bin`). Relevé :
- tuiles de mer (`sea`) : un seul emplacement, `mud_a0` ; plages (`sea_coast`, 95 poses) : `mud_a0` dans les deux
  emplacements, uniforme (le fond de mer en mud_a0 est une lecture des fiches, pas encore vue en jeu) ;
- rivières (1 399 poses) : `sand_a0` pour 1 362 d'entre elles (lit et berges) ;
- routes (2 023 poses) : `sand_a0` / `sand_a1`, bandes de 0,03 à 0,08 unité (moins d'un pixel à notre grille) : non
  traitées ici.
Or `textures_sol_wh1.appliquer` réécrit le mélange compilé d'après `global_blend.dds` de WH1 : sans cette correction, le
fond de la mer et les lits de rivière avaient en jeu l'herbe du climat.

Usage (module) :
    corrige, bilan = corriger(melange_wh1)   # indices de texture de WH1 (ligne 0 au nord), corrigés
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tuiles_wh1 as T                                              # noqa: E402

INDEX_MUD_A0, INDEX_SAND_A0 = 3, 4               # rangs de `texture_arrays.xml` de WH1 (19 groupes)
SEUIL_RUBAN = 0.5                                 # poids du ruban de rivière (`rivieres_wh1_masque`) : lit de sable
# LE FOND SOMBRE SOUS L'EAU (24.09.2026, 04 h, session du rendu ; vidéos WH1 / WH3 de Charles et relevé de la construction :
# « rivières et lacs blancs, opaques », « bande d'eau pâle et plate le long du rivage »). Dans WH1, l'eau des rivières était
# un ruban sombre qui cachait le lit de sable de ses tuiles ; dans WH3, l'eau de la carte (matériau de la mer, reflets de
# fond forts pour les rivières) est presque transparente sur 5 cm (la profondeur des rivières de CA aussi) : le sable le
# plus clair de WH1 (`sand_a0`, 164 / 133 / 101) sous l'eau faisait des rivières blanches, et la boue claire du fond de mer
# (`mud_a0`, 101 / 90 / 74) la bande pâle des côtes. Désormais : sous l'eau des rivières (`relief-wh1\eau_rivieres.npy` de
# la chaîne), le marais de WH1 (65 / 58 / 42) ; le sable de WH1 reste sur les berges hors de l'eau. Sous la mer finale
# (`mer_finale.npy`, côte naturelle comprise), le sable sombre `sand_b3` (73 / 60 / 43) ; la terre que la côte naturelle
# gagne sur les tuiles de mer de WH1 garde la texture de son climat (pas de traînée de boue sur la côte).
FOND_SOMBRE = True
INDEX_MARSH, INDEX_SAND_B3 = 12, 0
# LE RIVAGE (24.09.2026, 05 h 30, chaîne 11 ; Charles : « les côtes sont toujours aussi catastrophiques », relevé de la
# construction : pas de transition entre la terre et l'eau). Sans les falaises de côte de WH1 (retirées de la côte naturelle,
# `montagnes_wh1.FALAISES_DE_COTE`), l'herbe du climat allait jusqu'à l'eau. Une bande de la boue des plages de WH1
# (`mud_a0`, la texture de ses tuiles `sea_coast`) borde la mer finale sur RIVAGE_PX pixels, largeur modulée par un bruit
# lisse (RIVAGE_BRUIT_PX), hors des lits de rivière (qui gardent leurs textures).
# RETIRÉE (24.09.2026, chaîne 12 ; Charles, 18 h 55 : « fais exactement comme dans Warhammer 1 au niveau du découpage de
# la côte, ne te prends pas la tête à réinventer la roue ») : avec le découpage de WH1, le bord de l'eau reprend les textures
# de WH1 (ses plages `sea_coast` en mud_a0, le climat ailleurs).
# REMISE (24.09.2026, 22 h 50, chaîne 13) avec la côte lisse (`cotes_wh1.LISSAGE`) : le trait bouge jusqu'à ~1 u, les
# plages de WH1 ne tombent plus au bord de l'eau.
RIVAGE_BOUE = True
RIVAGE_PX, RIVAGE_BRUIT_PX = 3, 2
# LES BANCS DE SABLE DES DELTAS DE WH1 (24.09.2026, chaîne 12, `deltas_wh1`) : l'éventail ocre de ses tuiles d'embouchure,
# devenu terre à la hauteur de son fond (`relief-wh1\delta_bancs.npy` de la chaîne), en sable de WH1 (sand_a0) hors de
# l'eau ; sous l'eau de ses bras, le marais, comme sous les autres rivières.
BANCS_DELTAS = True
# RETIRÉ (25.09.2026, 04 h 40, chaîne 16 ; Charles, capture de 04 h 05 : bancs orangés au delta du Grismerie ; enquête
# `scratchpad\enquete_deltas\`) : WH1 porte l'herbe du climat sur ses bancs (grass_a2 / a0, 85 à 95 %), le sable seulement en
# liseré le long des bras (sa tuile d'embouchure, déjà reprise par la règle des lits `river_mouth` ci-dessous) ; sand_a0 sur
# tout le banc faisait l'éventail ocre. Et pas de bande de boue dans les deltas (WH1 n'y a pas de plage) : DELTAS_SANS_BOUE.
BANCS_DELTAS = False
DELTAS_SANS_BOUE = True
# LES TACHES DES CARREFOURS (24.09.2026, chaîne 12 ; Charles, capture de 19 h 49 en Athel Loren : « une grande tache
# orange-beige informe, bien plus large que les chemins », puis « vérifie partout sur toute la carte ») : le mélange global de
# WH1 ne porte son sable clair (`sand_a0`) qu'en 5 taches, toutes sous ses carrefours de route (919 px, 97 % sous ses
# tuiles `roads` ; brouillon `taches_routes.py`) ; dans WH1, ses tuiles de route les recouvraient. Chez nous ce mélange est
# le sol : la tache se voyait sous les chemins de WH3. Remplacée par la texture voisine (propagation depuis son bord),
# avant les règles ci-dessous (qui posent elles-mêmes sand_a0 sur les berges et les bancs des deltas).
TACHES_ROUTES = True


def _sans_taches_de_route(a):
    """(indices, n) : le sand_a0 du mélange global de WH1 remplacé de proche en proche par la texture voisine."""
    out = np.array(a, copy=True)
    tache = out == INDEX_SAND_A0
    n = int(tache.sum())
    for _ in range(60):
        if not tache.any():
            break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            prend = tache & ~np.roll(tache, (dy, dx), (0, 1))
            out[prend] = np.roll(out, (dy, dx), (0, 1))[prend]
            tache &= ~prend
    return out, n
RELIEF = os.path.join(r"C:\TotalWar-CampaignMap", "04-projets", "saison-des-revelations", "relief-wh1")


def corriger(melange_wh1):
    """(indices corrigés, bilan) : emprise des tuiles de mer et de plage en mud_a0, lit des rivières en sand_a0.

    Emprise des tuiles et non maillages de mer : 94,5 % des maillages de mer portent une tuile `sea` ; le reste
    (17 916 px, pieds de falaise, sables) garde la texture de son climat, comme dans WH1."""
    H, L = melange_wh1.shape
    out = np.array(melange_wh1, np.uint8, copy=True)
    n_taches = 0
    if TACHES_ROUTES:
        out, n_taches = _sans_taches_de_route(out)
    fam = T.familles_par_case()
    if fam.shape[0] * 4 < H or fam.shape[1] * 4 < L:
        raise SystemExit(f"tuiles de WH1 {fam.shape} trop petites pour un mélange de {(H, L)}")
    a_la_grille = lambda m: np.repeat(np.repeat(m, 4, 0), 4, 1)[:H, :L]  # noqa: E731 - 4 px par case
    mer, plage = a_la_grille(fam == "sea"), a_la_grille(fam == "sea_coast")
    import rivieres_wh1_masque
    lit = rivieres_wh1_masque.Rivieres().masque(4)[:H, :L] > SEUIL_RUBAN
    if not FOND_SOMBRE:
        out[mer | plage] = INDEX_MUD_A0
        lit &= ~(mer | plage)
        out[lit] = INDEX_SAND_A0
        bilan = {"tuiles de mer (mud_a0)": int(mer.sum()), "plages (mud_a0)": int(plage.sum()),
                 "lits de rivière (sand_a0)": int(lit.sum())}
        return out, bilan
    mer_finale = np.load(os.path.join(RELIEF, "mer_finale.npy"))[:H, :L]
    eau_riv = np.isfinite(np.load(os.path.join(RELIEF, "eau_rivieres.npy"), mmap_mode="r"))[:H, :L]
    plage &= ~mer_finale
    out[plage] = INDEX_MUD_A0
    out[mer_finale] = INDEX_SAND_B3
    lit &= ~(mer_finale | plage)
    berge = lit & ~eau_riv
    out[berge] = INDEX_SAND_A0
    bancs = np.zeros((H, L), bool)
    chemin_bancs = os.path.join(RELIEF, "delta_bancs.npy")
    if BANCS_DELTAS and os.path.exists(chemin_bancs):
        bancs = np.load(chemin_bancs)[:H, :L] & ~mer_finale & ~eau_riv
        out[bancs] = INDEX_SAND_A0
    sous_eau = eau_riv & ~mer_finale
    out[sous_eau] = INDEX_MARSH
    rivage = np.zeros((H, L), bool)
    if RIVAGE_BOUE:
        # distance à la mer finale (px, dilatations 8-connexes) et largeur de bande modulée par un bruit lisse
        d = np.full((H, L), RIVAGE_PX + RIVAGE_BRUIT_PX + 1, np.int16)
        front = mer_finale.copy()
        for k in range(1, RIVAGE_PX + RIVAGE_BRUIT_PX + 1):
            p = np.pad(front, 1)
            v = front.copy()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    v |= p[1 + dy:1 + dy + H, 1 + dx:1 + dx + L]
            d[v & ~front] = k
            front = v
        from cotes_wh1 import _bruit_lisse
        largeur = RIVAGE_PX + np.round(RIVAGE_BRUIT_PX * _bruit_lisse((H, L), 16, 24))
        rivage = ~mer_finale & (d <= largeur) & ~lit & ~eau_riv & ~bancs         # les bancs des deltas gardent leur sable
        if DELTAS_SANS_BOUE:
            import deltas_wh1
            import rivieres_wh1
            rivage &= ~rivieres_wh1.dilater(deltas_wh1.zone(H, L), 6)
        out[rivage] = INDEX_MUD_A0
    bilan = {"mer finale (sand_b3)": int(mer_finale.sum()), "plages à terre (mud_a0)": int(plage.sum()),
             "berges des rivières (sand_a0)": int(berge.sum()), "sous l'eau des rivières (marsh)": int(sous_eau.sum()),
             "terre gagnée sur les tuiles de mer (climat gardé)": int((mer & ~mer_finale & ~plage).sum()),
             "rivage de boue (mud_a0)": int(rivage.sum()), "bancs des deltas (sand_a0)": int(bancs.sum()),
             "taches de sable des carrefours de WH1 effacées": n_taches}
    return out, bilan


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import terrain_wh1_vers_terry as TT
    b = TT.dds(os.path.join(TT.WH1, "global_map", "global_blend.dds"), np.uint8, (TT.H, TT.L))[::-1]
    c, bilan = corriger(b)
    print(bilan, "; pixels changés :", int((c != b).sum()))
