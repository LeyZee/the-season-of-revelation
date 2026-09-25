#!/usr/bin/env python3
"""
eau_carte.py - le matériau d'eau de notre carte (mer, rivières, lacs).

Pourquoi (23.09.2026, 04 h 45 ; session « IA et modding 3D ») : le matériau d'eau de CA est PROPRE À CHAQUE CARTE.
Celui des Empires (`wh3_main_combi_campaign_water_plane`) lit `Sea/combi_A_mask.dds` (alpha = leur mer, bleu = leur réseau
de rivières, en coordonnées du monde) et leur masque de flux. Nous l'employions : notre eau suivait la mer et les rivières
des Empires projetées sur notre carte (mer vide, rivières en morceaux là où elles croisent celles des Empires, nappe
d'eau sur la terre). Notre matériau (même shader, nos masques) est fabriqué par la session d'audit dans
`04-projets\\saison-des-revelations\\eau-carte\\` (embarqué par build_pack) ; tant qu'il n'y est pas, on garde celui des
Empires.

Usage (module) :
    eau_carte.materiau()    # chemin du matériau d'eau à citer (rivières, lacs, `water_plane_material` du projet Terry)
"""

import os

ATELIER = r"C:\TotalWar-CampaignMap"
DOSSIER = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "eau-carte")
MATERIAU_CA = "materials/environment/campaign_sea/wh3_main_combi_campaign_water_plane.xml.material"
MATERIAU_NOUS = "materials/environment/campaign_sea/wh_dlc05_wood_elves_campaign_water_plane.xml.material"


def materiau():
    """Notre matériau d'eau s'il est dans le projet, sinon celui des Empires."""
    return MATERIAU_NOUS if os.path.exists(os.path.join(DOSSIER, *MATERIAU_NOUS.split("/"))) else MATERIAU_CA
