#!/usr/bin/env python3
"""
seigneurs_drycha_kemmler_grom.py - Drycha, Heinrich Kemmler et Grom la Panse dans la carte de la Saison des Révélations :
les lignes `start_pos_*` du kit (sauvegardées avant écriture dans `05-journal\\db-backups\\`).

Pourquoi (23.09.2026, 13 h ; décision de Charles du 23.09 à 06 h 20, réponses par défaut à 13 h) : spécification de la
session d'audit `05-journal\\2026-09-22-gameplay-wh3\\spec-drycha-kemmler-grom.md`. Trois seigneurs jouables :
- Drycha REMPLACE la clairière de Cythral (ligne de faction 2120137221 : la faction devient `wh2_dlc16_wef_drycha`) ; son
  chef en garnison (2140783871) devient Drycha, en armée à côté de Tyr Vanna, avec l'armée de CA ;
- Grom REMPLACE les Teef Snatchaz (ligne 2120137146 -> `wh2_dlc15_grn_broken_axe`, Massif Orcal et Orquemont) ; leur chef
  (2140783823) devient Grom, en armée à côté du Massif Orcal ;
- Kemmler, faction NEUVE (`wh2_dlc11_vmp_the_barrow_legion`), prend le Poste de la Pierre Noire à Karak Ziflin (capitale,
  culture et bâtiments vampiriques), en armée à côté ; guerre contre Karak Ziflin et Quenelles.
Colonnes de faction, personnages, armées, trait et suiveur : ceux des Empires (campagne `wh3_main_combi`). Positions :
cases franchissables hors colonies, dans la région de la capitale (relevé des couches CAIME, 23.09.2026, 13 h 10).

Après lui : `synchroniser_pack_startpos.py` pour chaque table (`--maj --supprimer`), `ajouter_seigneurs_jouables.py
--apply` (fiches et options), puis génération du startpos (commande du témoin).

Usage :
    python seigneurs_drycha_kemmler_grom.py            # essai à blanc : ce qui changerait, table par table
    python seigneurs_drycha_kemmler_grom.py --apply
"""

import argparse
import io
import os
import re
import shutil
import sys
import time
import uuid
from xml.sax.saxutils import escape

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
CAMPAGNE = "wh_dlc05_wood_elves"

# faction de notre campagne (ID de ligne) -> ligne des Empires dont on reprend les colonnes
SUBSTITUTIONS = {"2120137221": "1443225988",        # Cythral -> Drycha
                 "2120137146": "1277704031"}        # Teef Snatchaz -> Grom
KEMMLER_FACTION, KEMMLER_IE = "2120137700", "1738448985"
COLONNES_FACTION = ("faction", "playable", "treasury", "is_major", "ai_manager", "honour", "cai_starting_personality",
                    "cdir_military_generator_config", "cai_personality_group", "faction_potential")
# personnage de notre campagne -> (personnage des Empires, case de départ)
CONVERSIONS = {"2140783871": ("1214807884", (301, 55)),     # Drycha, à 5 cases de Tyr Vanna
               "2140783823": ("160498396", (121, 267))}      # Grom, à 6 cases du Massif Orcal
KEMMLER, KEMMLER_PERSO_IE, KEMMLER_CASE = "2140784200", "1487310411", (297, 303)
COLONNES_PERSO = ("Name", "Surname", "Type", "ministerial_position", "portrait_id", "model", "immortal",
                  "override_general_unit", "is_in_generals_pool", "is_male", "loyalty", "clan_name", "other_name",
                  "death_type", "turns_died_before_start", "legacy_override", "subtype")
# le Poste de la Pierre Noire
POSTE_REGION, POSTE_COLONIE = "2130429363", "2145381258"
REGION_POSTE = {"owning_faction": KEMMLER_FACTION, "faction_capital": "1", "cultural_originator":
                "wh_main_sc_vmp_vampire_counts", "rebel_faction": "wh2_dlc11_vmp_the_barrow_legion", "rebel_faction_name": ""}
COLONIE_POSTE = {"primary_building": "wh_main_vmp_settlement_minor_1", "building1": ""}   # plus de ferme naine
GUERRES_KEMMLER = ("2120137573", "2120137125")      # Karak Ziflin, Quenelles
PREMIER_ID_UNITE, PREMIER_ID_TRAIT, PREMIER_ID_OBJET, PREMIER_ID_DIPLO = 20000, 1000, 1000, 1000


def sauvegarde(fichier, nom):
    dest = os.path.join(ATELIER, "05-journal", "db-backups", f"{nom}-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(fichier, dest)
    return dest


class Table:
    """Une table XML du kit : blocs d'origine, valeurs, modifications, ajouts et retraits ; `ecrire()` réécrit le fichier."""

    def __init__(self, nom):
        self.nom = nom
        self.chemin = os.path.join(KIT_DB, nom + ".xml")
        with io.open(self.chemin, encoding="utf-8", newline="") as f:
            self.xml = f.read()
        self.blocs = re.findall(rf"<{nom} [^>]*>.*?</{nom}>\r?\n?", self.xml, re.S)
        self.lignes = [dict(re.findall(r"<(\w+)>([^<]*)</\1>", b)) for b in self.blocs]
        self.changes, self.ajouts, self.retraits = {}, [], []

    def trouve(self, **cond):
        return [i for i, d in enumerate(self.lignes) if all(d.get(k) == v for k, v in cond.items())]

    def ids(self, col):
        return {int(d[col]) for d in self.lignes if d.get(col, "").lstrip("-").isdigit()}

    def libre(self, col, depart):
        pris = self.ids(col) | {int(d[col]) for d in self.ajouts}
        while depart in pris:
            depart += 1
        return depart

    def changer(self, i, valeurs):
        diff = {k: v for k, v in valeurs.items() if self.lignes[i].get(k) != v}
        if diff:
            self.changes.setdefault(i, {}).update(diff)
        return diff

    def ajouter(self, valeurs, modele_i):
        """Nouvelle ligne : copie du bloc `modele_i`, valeurs remplacées (toutes les colonnes du modèle)."""
        d = dict(self.lignes[modele_i])
        manquantes = [k for k in valeurs if k not in d]
        if manquantes:
            raise SystemExit(f"{self.nom} : colonnes inconnues {manquantes}")
        d.update(valeurs)
        self.ajouts.append(d)

    def retirer(self, i):
        self.retraits.append(i)

    def bilan(self):
        return f"{self.nom:36s} {len(self.changes)} changée(s), {len(self.ajouts)} ajoutée(s), {len(self.retraits)} retirée(s)"

    def _bloc(self, d, modele):
        cle = next(iter(d.values()))
        neuf = re.sub(r'record_uuid="[^"]*" record_timestamp="[^"]*" record_key="[^"]*"',
                      f'record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{int(time.time() * 1000)}" record_key="{cle}"',
                      modele, count=1)
        for k, v in d.items():
            neuf, n = re.subn(rf"<{k}>[^<]*</{k}>|<{k}\s*/>", lambda _: f"<{k}>{escape(v)}</{k}>", neuf, count=1)
            if n != 1:
                raise SystemExit(f"{self.nom} : colonne {k} introuvable dans le bloc modèle")
        return neuf

    def ecrire(self):
        if not (self.changes or self.ajouts or self.retraits):
            return None
        dest = sauvegarde(self.chemin, self.nom.replace("_", "-"))
        xml = self.xml
        for i, diff in self.changes.items():
            d = dict(self.lignes[i]); d.update(diff)
            ancien = self.blocs[i]
            neuf = ancien
            for k, v in diff.items():
                neuf, n = re.subn(rf"<{k}>[^<]*</{k}>|<{k}\s*/>", lambda _: f"<{k}>{escape(v)}</{k}>", neuf, count=1)
                if n != 1:
                    raise SystemExit(f"{self.nom} : colonne {k} introuvable (ligne {i})")
            xml = xml.replace(ancien, neuf, 1)
        for i in self.retraits:
            xml = xml.replace(self.blocs[i], "", 1)
        if self.ajouts:
            modele = self.blocs[0]
            fin = xml.rindex(f"</dataroot>")
            xml = xml[:fin] + "".join(self._bloc(d, modele if modele.endswith("\n") else modele + "\r\n")
                                      for d in self.ajouts) + xml[fin:]
        with io.open(self.chemin, "w", encoding="utf-8", newline="") as f:
            f.write(xml)
        return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    F = Table("start_pos_factions")
    P = Table("start_pos_characters")
    G = Table("start_pos_character_to_settlements")
    U = Table("start_pos_land_units")
    TR = Table("start_pos_character_traits")
    AN = Table("start_pos_character_ancillaries")
    R = Table("start_pos_regions")
    S = Table("start_pos_settlements")
    D = Table("start_pos_diplomacy")

    # 1. factions : deux substitutions, une ligne neuve
    for nous, ie in SUBSTITUTIONS.items():
        (i,), (j,) = F.trouve(ID=nous, campaign=CAMPAGNE), F.trouve(ID=ie)
        diff = F.changer(i, {c: F.lignes[j][c] for c in COLONNES_FACTION})
        print(f"faction {nous} : {F.lignes[i]['faction']} -> {F.lignes[j]['faction']} ; {sorted(diff)}")
    if not F.trouve(ID=KEMMLER_FACTION):
        (j,) = F.trouve(ID=KEMMLER_IE)
        ligne = {c: F.lignes[j][c] for c in COLONNES_FACTION}
        ligne.update({"ID": KEMMLER_FACTION, "campaign": CAMPAGNE, "starting_order": F.lignes[j]["starting_order"]})
        (modele,) = F.trouve(ID="2120137230")                    # Orion : une ligne de notre campagne pour modèle
        F.ajouter(ligne, modele)
        print(f"faction {KEMMLER_FACTION} : {ligne['faction']} (neuve)")

    # 2. personnages : deux chefs convertis, Kemmler neuf ; hors garnison, sur la carte
    for nous, (ie, (x, y)) in CONVERSIONS.items():
        (i,), (j,) = P.trouve(ID=nous), P.trouve(ID=ie)
        valeurs = {c: P.lignes[j][c] for c in COLONNES_PERSO}
        valeurs.update({"startx": str(x), "starty": str(y), "ministerial_position": "faction_leader"})
        P.changer(i, valeurs)
        print(f"personnage {nous} : {P.lignes[i]['subtype']} -> {valeurs['subtype']} en ({x}, {y})")
        for k in G.trouve(character=nous):
            G.retirer(k)
    if not P.trouve(ID=KEMMLER):
        (j,) = P.trouve(ID=KEMMLER_PERSO_IE)
        valeurs = {c: P.lignes[j][c] for c in COLONNES_PERSO}
        valeurs.update({"ID": KEMMLER, "faction": KEMMLER_FACTION, "startx": str(KEMMLER_CASE[0]),
                        "starty": str(KEMMLER_CASE[1]), "unique": "0"})
        (modele,) = P.trouve(ID="2140783885")
        P.ajouter(valeurs, modele)
        print(f"personnage {KEMMLER} : {valeurs['subtype']} en {KEMMLER_CASE} (neuf)")

    # 3. armées : celles des Empires, à la place de celles des anciens chefs
    for nous, (ie, _) in list(CONVERSIONS.items()) + [(KEMMLER, (KEMMLER_PERSO_IE, None))]:
        anciennes = U.trouve(general=nous)
        if len(anciennes) and all(U.lignes[k]["unit_type"] in {U.lignes[m]["unit_type"] for m in U.trouve(general=ie)}
                                  for k in anciennes) and len(anciennes) == len(U.trouve(general=ie)):
            continue                                            # déjà fait
        for k in anciennes:
            U.retirer(k)
        (modele,) = U.trouve(id="8575")                          # une unité d'Orion pour modèle
        for m in U.trouve(general=ie):
            U.ajouter({"id": str(U.libre("id", PREMIER_ID_UNITE)), "unit_type": U.lignes[m]["unit_type"],
                       "general": nous, "soldiers": U.lignes[m]["soldiers"], "unique": "0"}, modele)
        print(f"armée de {nous} : {len(anciennes)} unité(s) retirée(s), {len(U.trouve(general=ie))} de CA")

    # 4. trait et suiveur de Kemmler
    for T_, col, depart in ((TR, "trait_level", PREMIER_ID_TRAIT), (AN, "ancillary", PREMIER_ID_OBJET)):
        if not T_.trouve(character_id=KEMMLER):
            for m in T_.trouve(character_id=KEMMLER_PERSO_IE):
                T_.ajouter({"id": str(T_.libre("id", depart)), "character_id": KEMMLER, col: T_.lignes[m][col],
                            "unique": "0"}, T_.trouve(character_id="2140783885")[0] if T_.trouve(character_id="2140783885")
                           else m)
                print(f"{T_.nom} de Kemmler : {T_.lignes[m][col]}")

    # 5. le Poste de la Pierre Noire : à Kemmler, capitale, vampirique
    (i,) = R.trouve(id=POSTE_REGION)
    print(f"région {R.lignes[i]['region']} : {sorted(R.changer(i, REGION_POSTE))}")
    (i,) = S.trouve(id=POSTE_COLONIE)
    print(f"colonie {S.lignes[i]['settlement_id']} : {sorted(S.changer(i, COLONIE_POSTE))}")

    # 6. guerres de Kemmler
    for adversaire in GUERRES_KEMMLER:
        if not (D.trouve(faction1=KEMMLER_FACTION, faction2=adversaire) or D.trouve(faction1=adversaire,
                                                                                      faction2=KEMMLER_FACTION)):
            (modele,) = D.trouve(key="577")
            D.ajouter({"key": str(D.libre("key", PREMIER_ID_DIPLO)), "faction1": KEMMLER_FACTION, "faction2": adversaire,
                       "stance": "war", "grants_military_access": "0", "grants_trade_agreement": "0",
                       "relations_modifier": "0", "non_aggression_pact": "0", "unique": "0"}, modele)
            print(f"guerre : {KEMMLER_FACTION} contre {adversaire}")

    print()
    for t in (F, P, G, U, TR, AN, R, S, D):
        print(t.bilan())
    if not a.apply:
        print("essai à blanc : relancer avec --apply")
        return 0
    for t in (F, P, G, U, TR, AN, R, S, D):
        dest = t.ecrire()
        if dest:
            print(f"  {t.nom} écrite (sauvegarde {dest})")
    print("Ensuite : synchroniser_pack_startpos.py pour chaque table (--maj --supprimer --apply), "
          "ajouter_seigneurs_jouables.py --apply, génération du startpos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
