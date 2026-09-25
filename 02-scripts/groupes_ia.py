#!/usr/bin/env python3
"""
groupes_ia.py - le groupe de personnalités d'IA (`start_pos_factions.cai_personality_group`) de chaque
faction de la campagne, choisi comme CA le choisit.

Pourquoi (21.09.2026, 20 h 15) : le jeu plantait au chargement de la campagne
(`Warhammer3.exe+0x27A863F`, lecture de `[0+0x200]`) parce que la faction
`wh_dlc03_bst_beastmen_brayherd` avait le groupe `wh3_combi_personality_group_beastmen_brayherd`,
qui existe dans `cai_personality_groups` mais **ne contient aucune personnalité** (0 ligne dans
`cai_personality_group_junctions`) : le jeu prend la personnalité choisie ou, à défaut, la première
candidate, et il n'y en avait aucune. La traduction des groupes de Warhammer 1
(`declare_campaign.py`, GROUPES_IA) donnait en outre `default` à 20 factions : la personnalité la
plus pauvre, loin des factions « mises au niveau de Warhammer 3 » que Charles demande.

Règle, dans cet ordre :
1. la faction existe dans l'Empire Immortel (`wh3_main_combi`) : son groupe là-bas ;
2. sinon, le groupe « mineur » de sa culture chez CA (REPLI_PAR_CULTURE) ;
3. sinon, le groupe traduit de Warhammer 1.
Le groupe retenu doit contenir au moins une personnalité, sinon c'est une erreur.
"""

import os
import re
from collections import Counter

KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"

# Groupes « mineurs » de CA par culture (clé de culture dans la clé de faction). Relevés dans les
# lignes de l'Empire Immortel le 21.09.2026 : c'est ce que CA donne aux factions mineures.
REPLI_PAR_CULTURE = {
    "brt": "wh3_combi_personality_group_bretonnia_minor",
    "wef": "wh3_combi_personality_group_woodelf_minor",
    "bst": "wh3_combi_personality_group_beastmen_minor",
    "grn": "wh3_combi_personality_group_greenskin_minor",
    "dwf": "wh3_combi_personality_group_dwarf_minor",
    "vmp": "wh3_combi_personality_group_vampire_minor",
}
# Les hordes « waaagh » des tribus orques n'existent pas dans l'Empire Immortel ; CA garde pour elles
# le groupe de Warhammer 2, qui a sa personnalité propre.
GROUPE_WAAAGH = "wh2_group_greenskins_waaagh"


def _lignes(table):
    with open(os.path.join(KIT_DB, table + ".xml"), encoding="utf-8") as f:
        t = f.read()
    for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S):
        yield dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))


class Choix:
    def __init__(self):
        self.jonctions = Counter(l["group_key"] for l in _lignes("cai_personality_group_junctions"))
        self.ie = {l["faction"]: l.get("cai_personality_group", "")
                   for l in _lignes("start_pos_factions") if l.get("campaign") == "wh3_main_combi"}

    def groupe(self, faction, traduit=""):
        """Rend (groupe, raison). Lève ValueError si aucun groupe utilisable."""
        candidats = []
        if faction in self.ie:
            candidats.append((self.ie[faction], "groupe de la faction dans l'Empire Immortel"))
        if faction.endswith("_waaagh"):
            candidats.append((GROUPE_WAAAGH, "horde waaagh : groupe de Warhammer 2 gardé par CA"))
        for culture, g in REPLI_PAR_CULTURE.items():
            if f"_{culture}_" in f"_{faction}_":
                candidats.append((g, f"groupe mineur de la culture {culture}"))
        if traduit:
            candidats.append((traduit, "groupe traduit de Warhammer 1"))
        for g, raison in candidats:
            if self.jonctions.get(g, 0) > 0:
                return g, raison
        raise ValueError(f"{faction} : aucun groupe d'IA avec des personnalités parmi {candidats}")
