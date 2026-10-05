#!/usr/bin/env python3
"""
recopier_depart_expanded.py - recopie le DÉPART de la Saison (campagne wh_dlc05_wood_elves) vers la campagne saison_expanded
dans les tables start_pos_* du kit, avec une table de correspondance des identifiants.

Pourquoi (03.10.2026 ; Charles : « attaque tout ça » pour Expanded ; répartition avec la session « Expanded map integration
et polish ») : la campagne saison_expanded n'avait aucune ligne de départ (0 faction, 0 région, 0 emplacement). La
construction recopie le départ de la Saison ; la session Expanded ajoute ensuite par-dessus, en lot à part, ses 16 factions
de l'Atlas, le départ de Kemmler à Krinal et les maîtres des régions neuves, en s'appuyant sur la correspondance écrite ici.

Les tables se renvoient les unes aux autres par identifiants : factions (ID) -> personnages (faction) -> unités, hordes,
options de départ, traits, objets, garnisons ; régions (id, owning_faction) -> colonies (region) -> garnisons (settlement) ;
diplomatie, événements passés, conditions de victoire (factions). Chaque ligne recopiée reçoit un identifiant neuf
(`donnees_campagne.ident_numerique`, graine « expanded:<table>:<ancien> »), et ses renvois sont réécrits par la
correspondance. Règles propres à Expanded : positions des personnages décalées de DECALAGE_HEX (WH1 en x + 120, y + 330) ;
Fort Solstice (`wh_dlc05_carcassonne_summersfall_fort`, absent d'Expanded) devient `saison_glanborielle_fort_solstice`
(reprise, décision du 25.09) ; toute autre région absente de la carte d'Expanded est écartée (avec ce qui en dépend).

Garde : refuse de tourner si saison_expanded a déjà des lignes de départ (pas de double recopie) ; sauvegarde des tables
dans `05-journal\\db-backups\\<date>-recopie-depart-expanded` avant écriture ; préavis du kit à donner avant `--apply`.

Usage :
    python recopier_depart_expanded.py            # à blanc : comptes par table
    python recopier_depart_expanded.py --apply    # écrit dans raw_data\\db et la correspondance
Sortie : 04-projets\\saison-expanded\\depart\\correspondance_depart.json
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carte_config                                                  # noqa: E402
from donnees_campagne import TableKit, ident_numerique               # noqa: E402

ATELIER = carte_config.ATELIER
SOURCE, CIBLE = "wh_dlc05_wood_elves", "saison_expanded"
CARTE_CIBLE = carte_config.PROFILS["expanded"]["CARTE"]
DX, DY = carte_config.PROFILS["expanded"]["DECALAGE_HEX"]
REPRISES = {"wh_dlc05_carcassonne_summersfall_fort": "saison_glanborielle_fort_solstice"}
SORTIE = os.path.join(ATELIER, "04-projets", "saison-expanded", "depart", "correspondance_depart.json")
COLONNES_ID = ("ID", "id", "key")


class Recopie:
    def __init__(self):
        self.t = {}
        self.carte = {}          # table -> {ancien id : neuf}
        self.compte = {}

    def table(self, nom):
        if nom not in self.t:
            self.t[nom] = TableKit(nom)
        return self.t[nom]

    def neuf_id(self, nom, col, ancien):
        t = self.table(nom)
        pris = getattr(t, "_pris_" + col, None)
        if pris is None:
            pris = {t.valeurs(c).get(col) for _, c in t.lignes}
            setattr(t, "_pris_" + col, pris)
        n = ident_numerique(f"expanded:{nom}:{ancien}", pris)
        pris.add(n)
        return n

    def copier(self, nom, cle, corps, changes):
        """Ajoute la copie de la ligne `cle` avec les colonnes `changes` ; la clé d'enregistrement est l'ancienne où chaque
        valeur changée (3 caractères et plus) est remplacée par la neuve."""
        t = self.table(nom)
        anciennes = t.valeurs(corps)
        neuve_cle = cle
        for c, v in changes.items():
            corps = t.avec(corps, c, v)
            vieux = anciennes.get(c, "")
            if len(vieux) >= 3 and vieux != v and vieux in neuve_cle:
                neuve_cle = neuve_cle.replace(vieux, v, 1)
        if neuve_cle == cle:
            raise SystemExit(f"{nom} : la clé {cle} ne change pas à la recopie")
        if not t.ajouter(neuve_cle, corps):
            raise SystemExit(f"{nom} : clé {neuve_cle} déjà présente")
        self.compte[nom] = self.compte.get(nom, 0) + 1

    def lignes_ou(self, nom, filtre):
        t = self.table(nom)
        return [(k, c, t.valeurs(c)) for k, c in t.lignes if filtre(t.valeurs(c))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    R = Recopie()
    if R.lignes_ou("start_pos_factions", lambda v: v.get("campaign") == CIBLE) or \
            R.lignes_ou("start_pos_regions", lambda v: v.get("campaign") == CIBLE):
        raise SystemExit(f"{CIBLE} a déjà des lignes de départ : recopie refusée (pas de double recopie)")
    regions_carte = {v["region"] for _, _, v in R.lignes_ou("campaign_map_regions",
                                                             lambda v: v.get("campaign_map") == CARTE_CIBLE)}
    if not regions_carte:
        raise SystemExit(f"aucune région déclarée pour {CARTE_CIBLE}")
    F, C, RG, S = {}, {}, {}, {}
    # 0. calendrier (clé = campagne)
    for k, c, v in R.lignes_ou("start_pos_calendars", lambda v: v.get("campaign") == SOURCE):
        R.copier("start_pos_calendars", k, c, {"campaign": CIBLE})
    # 1. factions
    for k, c, v in R.lignes_ou("start_pos_factions", lambda v: v.get("campaign") == SOURCE):
        F[v["ID"]] = R.neuf_id("start_pos_factions", "ID", v["ID"])
        R.copier("start_pos_factions", k, c, {"ID": F[v["ID"]], "campaign": CIBLE})
    # 2. personnages (positions décalées)
    for k, c, v in R.lignes_ou("start_pos_characters", lambda v: v.get("faction") in F):
        C[v["ID"]] = R.neuf_id("start_pos_characters", "ID", v["ID"])
        ch = {"ID": C[v["ID"]], "faction": F[v["faction"]]}
        if v.get("startx") not in ("", "0") or v.get("starty") not in ("", "0"):
            ch["startx"], ch["starty"] = str(int(v["startx"]) + DX), str(int(v["starty"]) + DY)
        R.copier("start_pos_characters", k, c, ch)
    # 3. régions (reprises, écartées)
    ecartees = []
    for k, c, v in R.lignes_ou("start_pos_regions", lambda v: v.get("campaign") == SOURCE):
        cle_r = REPRISES.get(v["region"], v["region"])
        if cle_r not in regions_carte:
            ecartees.append(v["region"])
            continue
        RG[v["id"]] = R.neuf_id("start_pos_regions", "id", v["id"])
        ch = {"id": RG[v["id"]], "campaign": CIBLE, "owning_faction": F.get(v["owning_faction"], v["owning_faction"])}
        if cle_r != v["region"]:
            ch["region"] = cle_r
        R.copier("start_pos_regions", k, c, ch)
    # 4. colonies
    for k, c, v in R.lignes_ou("start_pos_settlements", lambda v: v.get("region") in RG):
        S[v["id"]] = R.neuf_id("start_pos_settlements", "id", v["id"])
        ch = {"id": S[v["id"]], "region": RG[v["region"]]}
        for vieux, neuf in REPRISES.items():
            if vieux in v.get("settlement_id", ""):
                ch["settlement_id"] = v["settlement_id"].replace(vieux, neuf)
        R.copier("start_pos_settlements", k, c, ch)
    # 5. emplacements de colonie (par clé de région)
    for k, c, v in R.lignes_ou("start_pos_region_slot_templates", lambda v: v.get("campaign") == SOURCE):
        cle_r = REPRISES.get(v["region"], v["region"])
        if cle_r not in regions_carte:
            continue
        ch = {"id": R.neuf_id("start_pos_region_slot_templates", "id", v["id"]), "campaign": CIBLE}
        if cle_r != v["region"]:
            ch["region"] = cle_r
        R.copier("start_pos_region_slot_templates", k, c, ch)
    # 6. ce qui dépend des personnages
    for nom, col in (("start_pos_land_units", "general"), ("start_pos_starting_general_options", "general"),
                     ("start_pos_character_traits", "character_id"), ("start_pos_character_ancillaries", "character_id"),
                     ("start_pos_horde_details", "general")):
        for k, c, v in R.lignes_ou(nom, lambda v, col=col: v.get(col) in C):
            ch = {col: C[v[col]]}
            for cid in COLONNES_ID:
                if cid in v:
                    ch[cid] = R.neuf_id(nom, cid, v[cid])
            R.copier(nom, k, c, ch)
    for k, c, v in R.lignes_ou("start_pos_character_to_settlements",
                               lambda v: v.get("character") in C and v.get("settlement") in S):
        R.copier("start_pos_character_to_settlements", k, c, {"character": C[v["character"]],
                                                              "settlement": S[v["settlement"]]})
    # 7. ce qui dépend des factions
    for nom, cols in (("start_pos_diplomacy", ("faction1", "faction2")), ("start_pos_past_events", ("source", "target")),
                      ("start_pos_victory_conditions", ("start_pos_faction",))):
        for k, c, v in R.lignes_ou(nom, lambda v, cols=cols: all(v.get(x) in F for x in cols)):
            ch = {x: F[v[x]] for x in cols}
            for cid in COLONNES_ID:
                if cid in v:
                    ch[cid] = R.neuf_id(nom, cid, v[cid])
            R.copier(nom, k, c, ch)
    print(f"recopie {SOURCE} -> {CIBLE} (carte {CARTE_CIBLE}, décalage ({DX}, {DY})) :")
    for nom, n in sorted(R.compte.items()):
        print(f"  {nom:44s} {n:5d} lignes")
    print(f"  régions écartées (absentes d'Expanded) : {ecartees or 'aucune'} ; reprises : {REPRISES}")
    corr = {"source": SOURCE, "cible": CIBLE, "decalage_hex": [DX, DY], "reprises": REPRISES,
            "factions": {R.table("start_pos_factions").valeurs(c)["faction"]: {"ancien": i, "neuf": F[i]}
                         for i in F for k, c in R.table("start_pos_factions").ou(ID=i)},
            "personnages": C, "regions": RG, "colonies": S}
    if not a.apply:
        print("à blanc ; relancer avec --apply (préavis du kit d'abord)")
        return 0
    dossier = os.path.join(ATELIER, "05-journal", "db-backups", time.strftime("%Y%m%d-%H%M%S") + "-recopie-depart-expanded")
    n = sum(t.ecrire(dossier) for t in R.t.values())
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(corr, f, ensure_ascii=False, indent=1)
    print(f"écrit : {n} lignes ; sauvegarde {dossier} ; correspondance {SORTIE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
