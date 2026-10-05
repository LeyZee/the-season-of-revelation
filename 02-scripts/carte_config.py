#!/usr/bin/env python3
"""
carte_config.py - la carte sur laquelle travaille la chaîne (la Saison de la bêta, ou Saison Expanded).

Pourquoi (25.09.2026, chantier « Expanded », demande de Charles) : la chaîne était écrite pour UNE carte ; une même
constante `CARTE` y désignait à la fois la SOURCE WH1 et la CIBLE dans le kit, et la taille (400 × 440 hex, 266,53 u)
était écrite en dur dans une trentaine de modules (inventaire : `04-projets\\saison-expanded\\PLAN.md`). Ce module porte
tout ce qui dépend de la carte ; les modules de la chaîne le lisent au lieu de leurs constantes.

Choix de la carte : variable d'environnement `SAISON_CARTE` (`saison` par défaut, `expanded`). La carte par défaut garde
EXACTEMENT les valeurs d'avant (contrôle : `04-projets\\saison-expanded\\outils\\releve_constantes.py --comparer`).

Repère d'Expanded (Atlas de la session « Extension », `travail\\geo_extension.py:34-35`, `carte_papier_v2.py:11-12`) : hex
logiques de 560 × 905 depuis le 03.10.2026 : le cadre de l'Atlas (carte de WH1 en x + 120 : pair, la parité des colonnes
décalées est gardée), les Voûtes (80 rangées) et le Bois Rêveur (250 rangées au sud) ; carte de WH1 en y + 330 (voir le
profil « expanded » ci-dessous). Avant le 03.10 : 560 × 825 et y + 250.
"""

import os

ATELIER = r"C:\TotalWar-CampaignMap"

# La source : la mini-campagne de WH1, toujours la même (données extraites dans 03-references)
CARTE_SOURCE = "wh_dlc05_wood_elves_map_1"
CAMPAGNE_SOURCE = "wh_dlc05_wood_elves"
HEX_L_SOURCE, HEX_H_SOURCE = 400, 440
LARGEUR_MONDE_SOURCE = 266.53                  # u, largeur de la carte de WH1 (world_width)
PROFONDEUR_MONDE_SOURCE = 338.9                # u, espace des hex (293,5 dans le repère des rasters, × √3/2)

PROFILS = {
    "saison": {
        "CARTE": "wh_dlc05_wood_elves_map_1",
        "CAMPAGNE": "wh_dlc05_wood_elves",
        "HEX_L": 400, "HEX_H": 440,
        "DECALAGE_HEX": (0, 0),                  # place de la carte de WH1 dans la carte (colonnes, rangées)
        "PROJET_ATELIER": os.path.join(ATELIER, "04-projets", "saison-des-revelations"),
        "PACK": "saison_des_revelations.pack",
        "SOURCE_MONDE": None,                    # la Saison : les données de WH1 telles quelles
    },
    # (25.09.2026, 16 h 15, décision de Charles sur conseil) la place du Bois des Rêves (reflet d'Athel Loren EN MIROIR,
    # sud de la forêt contre un voile infranchissable d'environ 26 rangées) est réservée dès la grille : 250 rangées au
    # sud (proposition de la session « Extension », `bois-des-reves.md` § 4 : « de 440 à ~690 rangées ») ; la carte de
    # WH1 monte donc de 250 rangées. Hors jeu (brume) tant que le Bois n'est pas dessiné.
    # (3.10.2026, Charles : « repousser le miroir… côté jeu ») les Voûtes prennent 80 rangées entre la carte de WH1 et le
    # voile (Atlas, geo_extension.VOUTES_SUD) : 560 × 905, WH1 en (x + 120, y + 330), le Bois Rêveur garde ses 250 rangées
    # du bas. Constantes dérivées (reflet, rasters) : 04-projets\saison-expanded\outils\cadre_expanded.py
    "expanded": {
        "CARTE": "saison_expanded_map",
        "CAMPAGNE": "saison_expanded",
        "HEX_L": 560, "HEX_H": 905,
        "DECALAGE_HEX": (120, 330),
        "PROJET_ATELIER": os.path.join(ATELIER, "04-projets", "saison-expanded"),
        "PACK": "saison_expanded.pack",
        # (3.10.2026, crochets proposés par la session « Expanded map integration et polish », appliqués par la
        # construction) données de WH1 posées dans le monde agrandi par projet_expanded.py, pour la chaîne d'après BOB
        "SOURCE_MONDE": {
            "BLEND_WH1": os.path.join(ATELIER, "04-projets", "saison-expanded", "terrain-wh1", "wh1_blend_monde.npy"),
            "MONTAGNES_WH1": os.path.join(ATELIER, "04-projets", "saison-expanded", "terrain-wh1",
                                          "montagnes_wh1_monde.npy"),
            # matériau d'eau d'Expanded (outils\eau_materiau_expanded.py, dans 04-projets\saison-expanded\eau-carte\)
            "MATERIAU_EAU": "materials/environment/campaign_sea/saison_expanded_campaign_water_plane.xml.material",
        },
    },
}

NOM = os.environ.get("SAISON_CARTE", "saison")
if NOM not in PROFILS:
    raise SystemExit(f"SAISON_CARTE={NOM!r} inconnue ; attendu : {sorted(PROFILS)}")
_P = PROFILS[NOM]
CARTE = _P["CARTE"]
CAMPAGNE = _P["CAMPAGNE"]
HEX_L, HEX_H = _P["HEX_L"], _P["HEX_H"]
DECALAGE_HEX = _P["DECALAGE_HEX"]
PROJET_ATELIER = _P["PROJET_ATELIER"]
PACK = _P["PACK"]
SOURCE_MONDE = _P.get("SOURCE_MONDE")          # None pour la Saison
# le monde grandit avec la grille, à l'échelle de WH1 (même taille d'hex)
LARGEUR_MONDE = LARGEUR_MONDE_SOURCE * HEX_L / HEX_L_SOURCE
PROFONDEUR_MONDE = PROFONDEUR_MONDE_SOURCE * HEX_H / HEX_H_SOURCE
EST_SOURCE = NOM == "saison"                   # la carte de la bêta : tout reste comme avant


def dans_projet(*parties):
    """Chemin dans le dossier d'atelier de la carte (sorties de la chaîne)."""
    return os.path.join(PROJET_ATELIER, *parties)
