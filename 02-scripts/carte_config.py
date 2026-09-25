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
logiques de 560 × 825 : le cadre de l'Atlas (560 × 575, carte de WH1 en x + 120 : pair, la parité des colonnes décalées
est gardée) plus 250 rangées au sud pour le Bois des Rêves (carte de WH1 en y + 250).
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
    },
    # (25.09.2026, 16 h 15, décision de Charles sur conseil) la place du Bois des Rêves (reflet d'Athel Loren EN MIROIR,
    # sud de la forêt contre un voile infranchissable d'environ 26 rangées) est réservée dès la grille : 250 rangées au
    # sud (proposition de la session « Extension », `bois-des-reves.md` § 4 : « de 440 à ~690 rangées ») ; la carte de
    # WH1 monte donc de 250 rangées. Hors jeu (brume) tant que le Bois n'est pas dessiné.
    "expanded": {
        "CARTE": "saison_expanded_map",
        "CAMPAGNE": "saison_expanded",
        "HEX_L": 560, "HEX_H": 825,
        "DECALAGE_HEX": (120, 250),
        "PROJET_ATELIER": os.path.join(ATELIER, "04-projets", "saison-expanded"),
        "PACK": "saison_expanded.pack",
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
# le monde grandit avec la grille, à l'échelle de WH1 (même taille d'hex)
LARGEUR_MONDE = LARGEUR_MONDE_SOURCE * HEX_L / HEX_L_SOURCE
PROFONDEUR_MONDE = PROFONDEUR_MONDE_SOURCE * HEX_H / HEX_H_SOURCE
EST_SOURCE = NOM == "saison"                   # la carte de la bêta : tout reste comme avant


def dans_projet(*parties):
    """Chemin dans le dossier d'atelier de la carte (sorties de la chaîne)."""
    return os.path.join(PROJET_ATELIER, *parties)
