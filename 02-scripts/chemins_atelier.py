#!/usr/bin/env python3
"""
chemins_atelier.py - les chemins de la machine (atelier, Warhammer III, Warhammer I, kits), en un seul endroit.

Pourquoi (25.09.2026, demande de Charles : « ouvrir » l'atelier aux autres moddeurs) : 74 scripts sur 106 de 02-scripts
écrivaient ces chemins en dur (`ATELIER = r"C:\\Users\\you\\..."` dans 41 d'entre eux, le dossier du jeu dans 74) ; sur
un autre PC, rien ne marchait sans les retoucher un par un. Les scripts lisent désormais ce module (migration par
étapes, après la bêta pour la chaîne de construction).

Réglage, du plus fort au plus faible :
1. variables d'environnement : SAISON_ATELIER, SAISON_WH3, SAISON_WH1 ;
2. fichier `atelier_local.json` à la racine de l'atelier (jamais partagé : propre à chaque machine), par exemple
   {"WH3": "D:/SteamLibrary/steamapps/common/Total War WARHAMMER III"} ;
3. valeurs par défaut : celles de la machine de Charles, EXACTEMENT celles d'avant (aucun script ne change de
   comportement chez lui).

Usage :
    from chemins_atelier import ATELIER, WH3, KIT, KIT_DB, DATA_WH3
    python chemins_atelier.py            # affiche les chemins retenus et ceux qui manquent
"""

import json
import os
import sys

_DEFAUTS = {
    "ATELIER": r"C:\TotalWar-CampaignMap",
    "WH3": r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III",
    "WH1": r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER",
}
_ENV = {"ATELIER": "SAISON_ATELIER", "WH3": "SAISON_WH3", "WH1": "SAISON_WH1"}


def _local():
    """Réglages de la machine (atelier_local.json à la racine de l'atelier), s'il existe."""
    racine = os.environ.get(_ENV["ATELIER"]) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chemin = os.path.join(racine, "atelier_local.json")
    if not os.path.isfile(chemin):
        return {}
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _choisir():
    local = _local()
    return {cle: os.path.normpath(os.environ.get(_ENV[cle]) or local.get(cle) or defaut)
            for cle, defaut in _DEFAUTS.items()}


_C = _choisir()
ATELIER = _C["ATELIER"]
WH3 = _C["WH3"]                                     # dossier du jeu Warhammer III
WH1 = _C["WH1"]                                     # dossier du jeu Warhammer I (source de la carte)

DATA_WH3 = os.path.join(WH3, "data")
KIT = os.path.join(WH3, "assembly_kit")
KIT_DB = os.path.join(KIT, "raw_data", "db")
KIT_WD = os.path.join(KIT, "working_data")
DATA_WH1 = os.path.join(WH1, "data")
KIT_WH1 = os.path.join(WH1, "assembly_kit")
KIT_DB_WH1 = os.path.join(KIT_WH1, "raw_data", "db")

SCRIPTS = os.path.join(ATELIER, "02-scripts")
JOURNAL = os.path.join(ATELIER, "05-journal")
PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
SAUVEGARDES_DB = os.path.join(JOURNAL, "db-backups")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for nom in ("ATELIER", "WH3", "WH1", "DATA_WH3", "KIT", "KIT_DB", "KIT_WD", "DATA_WH1", "KIT_WH1", "KIT_DB_WH1",
                "PROJET", "SAUVEGARDES_DB"):
        chemin = globals()[nom]
        print(f"{nom:15s} {'ok ' if os.path.exists(chemin) else 'ABSENT'} {chemin}")


if __name__ == "__main__":
    main()
