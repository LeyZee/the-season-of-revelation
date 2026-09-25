#!/usr/bin/env python3
"""
seigneur_soeurs.py - les Sœurs du Crépuscule (Naestra et Arahan), dixième seigneur jouable de la Saison des Révélations :
les lignes `start_pos_*` du kit (sauvegardées avant écriture dans `05-journal\\db-backups\\`).

Pourquoi (24.09.2026, 00 h 10 ; décision de Charles du 23.09 à 23 h 40 et du 24.09 à 00 h 15) : spécification de la
session « IA et modding 3D », `05-journal\\2026-09-22-gameplay-wh3\\spec-soeurs-du-crepuscule.md`. Faction NEUVE
(`wh2_dlc16_wef_sisters_of_twilight`, ligne des Empires 202058440), SANS région : elle commence en armée près de la
Grande Salle tombée de Tal Jul Finel (`wh_dlc05_wydrioth_tal_jul_finel`, colonie en (316, 132), ruine sans propriétaire
qu'elle relèvera en première quête) ; personnage et armée des Empires (2109289604), héroïne spellsinger_beasts des
Empires (835029364) ; paix et accès militaire avec Wydrioth (Findol). Cases : franchissables, hors emplacement et
étalement de la colonie, dans sa région (relevé des couches CAIME du 23.09.2026, 23 h 33 ; script du brouillon
`case_soeurs.py`).

Même mécanique que `seigneurs_drycha_kemmler_grom.py` (dont il reprend la classe Table).

Usage :
    python seigneur_soeurs.py            # essai à blanc
    python seigneur_soeurs.py --apply
"""

import argparse
import sys

from seigneurs_drycha_kemmler_grom import Table, CAMPAGNE, COLONNES_FACTION, COLONNES_PERSO

FACTION, FACTION_IE = "2120137701", "202058440"
SOEURS, SOEURS_IE, SOEURS_CASE = "2140784201", "2109289604", (316, 135)
HEROINE, HEROINE_IE, HEROINE_CASE = "2140784202", "835029364", (318, 135)
WYDRIOTH = "2120137239"
PREMIER_ID_UNITE, PREMIER_ID_TRAIT, PREMIER_ID_OBJET, PREMIER_ID_DIPLO = 20000, 1000, 1000, 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    F = Table("start_pos_factions")
    P = Table("start_pos_characters")
    U = Table("start_pos_land_units")
    TR = Table("start_pos_character_traits")
    AN = Table("start_pos_character_ancillaries")
    D = Table("start_pos_diplomacy")

    # 1. faction neuve, colonnes de celle des Empires
    if not F.trouve(ID=FACTION):
        (j,) = F.trouve(ID=FACTION_IE)
        ligne = {c: F.lignes[j][c] for c in COLONNES_FACTION}
        ligne.update({"ID": FACTION, "campaign": CAMPAGNE, "starting_order": F.lignes[j]["starting_order"]})
        (modele,) = F.trouve(ID="2120137230")                    # Orion : une ligne de notre campagne pour modèle
        F.ajouter(ligne, modele)
        print(f"faction {FACTION} : {ligne['faction']} (neuve, sans région)")

    # 2. personnages : les Sœurs (chef, en armée) et l'héroïne, colonnes de ceux des Empires
    for nous, ie, (x, y) in ((SOEURS, SOEURS_IE, SOEURS_CASE), (HEROINE, HEROINE_IE, HEROINE_CASE)):
        if P.trouve(ID=nous):
            continue
        (j,) = P.trouve(ID=ie)
        valeurs = {c: P.lignes[j][c] for c in COLONNES_PERSO}
        valeurs.update({"ID": nous, "faction": FACTION, "startx": str(x), "starty": str(y), "unique": "0"})
        (modele,) = P.trouve(ID="2140783885")
        P.ajouter(valeurs, modele)
        print(f"personnage {nous} : {valeurs['subtype']} ({valeurs['Type']}) en ({x}, {y})")

    # 3. armée des Empires
    if not U.trouve(general=SOEURS):
        modele = U.trouve(general="2140783885")[0]               # une unité d'Orion pour modèle
        for m in U.trouve(general=SOEURS_IE):
            U.ajouter({"id": str(U.libre("id", PREMIER_ID_UNITE)), "unit_type": U.lignes[m]["unit_type"],
                       "general": SOEURS, "soldiers": U.lignes[m]["soldiers"], "unique": "0"}, modele)
        print(f"armée des Sœurs : {len(U.trouve(general=SOEURS_IE))} unités de CA")

    # 4. traits et suiveurs des Empires
    for nous, ie in ((SOEURS, SOEURS_IE), (HEROINE, HEROINE_IE)):
        for T_, col, depart in ((TR, "trait_level", PREMIER_ID_TRAIT), (AN, "ancillary", PREMIER_ID_OBJET)):
            if T_.trouve(character_id=nous):
                continue
            for m in T_.trouve(character_id=ie):
                T_.ajouter({"id": str(T_.libre("id", depart)), "character_id": nous, col: T_.lignes[m][col],
                            "unique": "0"}, m)
                print(f"{T_.nom} de {nous} : {T_.lignes[m][col]}")

    # 5. paix et accès militaire avec Wydrioth
    if not (D.trouve(faction1=FACTION, faction2=WYDRIOTH) or D.trouve(faction1=WYDRIOTH, faction2=FACTION)):
        (modele,) = D.trouve(key="577")
        D.ajouter({"key": str(D.libre("key", PREMIER_ID_DIPLO)), "faction1": FACTION, "faction2": WYDRIOTH,
                   "stance": "neutral", "grants_military_access": "1", "grants_trade_agreement": "0",
                   "relations_modifier": "0", "non_aggression_pact": "0", "unique": "0"}, modele)
        print(f"diplomatie : {FACTION} et {WYDRIOTH} (Wydrioth) en paix, accès militaire")

    print()
    for t in (F, P, U, TR, AN, D):
        print(t.bilan())
    if not a.apply:
        print("essai à blanc : relancer avec --apply")
        return 0
    for t in (F, P, U, TR, AN, D):
        dest = t.ecrire()
        if dest:
            print(f"  {t.nom} écrite (sauvegarde {dest})")
    print("Ensuite : synchroniser_pack_startpos.py pour chaque table (--maj --apply), fiche et option de général "
          "(ajouter_seigneurs_jouables.py), génération du startpos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
