#!/usr/bin/env python3
"""
synchroniser_pack_startpos.py - recopie dans `zz_startpos_db.pack` les lignes d'une table `start_pos_*`
du kit qui manquent au pack.

Pourquoi : le jeu génère le startpos à partir des tables du **pack** `zz_startpos_db.pack`, pas des XML
du kit. Une ligne ajoutée au kit (par `declare_campaign.py`, par exemple) n'existe pour le jeu qu'une
fois recopiée ici. Écrit le 21.09.2026 pour les 36 lignes d'emplacements des régions d'Athel Loren.

Le script apparie les lignes sur une colonne clé (`id` par défaut), n'ajoute que les lignes absentes
du pack et signale, sans les toucher, celles qui diffèrent. Sauvegarde du pack dans
`05-journal\\db-backups\\` avant écriture. Il faut `rpfm_server` lancé (`lancer-outils.ps1 -Outil rpfm-server`).

Usage :
    python synchroniser_pack_startpos.py --table start_pos_region_slot_templates [--apply]
        [--campagne wh_dlc05_wood_elves] [--cle id]
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
PACK = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data/zz_startpos_db.pack"


def ids_factions(campagne):
    """Identifiants (colonne ID de start_pos_factions) des factions de la campagne."""
    with open(os.path.join(KIT_DB, "start_pos_factions.xml"), encoding="utf-8") as f:
        t = f.read()
    out = set()
    for m in re.finditer(r"<start_pos_factions\b[^>]*>(.*?)</start_pos_factions>", t, re.S):
        champs = dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
        if champs.get("campaign") == campagne:
            out.add(champs["ID"])
    return out


def ids_personnages(campagne):
    """Identifiants (colonne ID de start_pos_characters) des personnages des factions de la campagne."""
    factions = ids_factions(campagne)
    with open(os.path.join(KIT_DB, "start_pos_characters.xml"), encoding="utf-8") as f:
        t = f.read()
    out = set()
    for m in re.finditer(r"<start_pos_characters\b[^>]*>(.*?)</start_pos_characters>", t, re.S):
        champs = dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
        if champs.get("faction") in factions:
            out.add(champs["ID"])
    return out


def ids_regions(campagne):
    """Identifiants (colonne id de start_pos_regions) des régions de la campagne."""
    with open(os.path.join(KIT_DB, "start_pos_regions.xml"), encoding="utf-8") as f:
        t = f.read()
    out = set()
    for m in re.finditer(r"<start_pos_regions\b[^>]*>(.*?)</start_pos_regions>", t, re.S):
        champs = dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
        if champs.get("campaign") == campagne:
            out.add(champs["id"])
    return out


def lignes_kit(table, campagne):
    """Lignes du kit qui appartiennent à la campagne : par la colonne `campaign` quand la table en a
    une ; sinon (diplomatie) quand ses deux factions (`faction1`, `faction2`) sont de la campagne ;
    sinon (traits, objets, hordes : 23.09.2026) quand son personnage (`character_id` ou `general`) est
    un des personnages de la campagne."""
    with open(os.path.join(KIT_DB, table + ".xml"), encoding="utf-8") as f:
        t = f.read()
    ids = persos = regions = None
    out = []
    for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S):
        champs = {k: v for k, v in re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1))}
        if "campaign" in champs:
            garde = champs["campaign"] == campagne
        elif "faction1" in champs and "faction2" in champs:
            ids = ids if ids is not None else ids_factions(campagne)
            garde = champs["faction1"] in ids and champs["faction2"] in ids
        elif "character_id" in champs or "general" in champs or "character" in champs:
            persos = persos if persos is not None else ids_personnages(campagne)
            garde = champs.get("character_id", champs.get("general", champs.get("character"))) in persos
        elif "faction" in champs and champs["faction"].isdigit():
            ids = ids if ids is not None else ids_factions(campagne)
            garde = champs["faction"] in ids
        elif "region" in champs and champs["region"].isdigit():
            regions = regions if regions is not None else ids_regions(campagne)
            garde = champs["region"] in regions
        else:
            sys.exit(f"{table} : ni colonne campaign, ni faction1/faction2, ni personnage : filtre à écrire")
        if garde:
            out.append(champs)
    return out


# Colonnes de texte que le pack laisse VIDES (23.09.2026, 13 h 20) : le kit porte « PLACEHOLDER » et « <culture> Rebels »
# (reprises de WH1), le pack des tables de départ les a vides sur toutes ses lignes. Recopiée depuis le kit, la
# description « PLACEHOLDER » du Poste de la Pierre Noire faisait planter la création du monde à la génération du
# startpos (sans vidage ; trouvé par dichotomie). Jamais recopiées : toujours écrites vides. Limité aux RÉGIONS : les lignes
# de factions du pack ont des descriptions non vides avec lesquelles la génération marche.
TEXTES_VIDES_PAR_TABLE = {"start_pos_regions": {"rebel_faction_name", "long_description"}}
TEXTES_VIDES = set()


def valeur(type_, brut):
    if type_ in ("I16", "I32", "I64", "OptionalI16", "OptionalI32", "OptionalI64"):
        return int(brut or 0)
    if type_ in ("F32", "F64"):
        return float(brut or 0)
    if type_ == "Boolean":
        return brut.strip().lower() in ("1", "true")
    return brut


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--campagne", default="wh_dlc05_wood_elves")
    ap.add_argument("--cle", default="id")
    ap.add_argument("--maj", action="store_true",
                    help="réécrire aussi, depuis le kit, les lignes présentes qui diffèrent (sinon : signalées)")
    ap.add_argument("--max-retraits", type=int, default=60,
                    help="bride de --supprimer (défaut 60) ; la lever seulement pour un lot qui retire en masse, décompte vérifié")
    ap.add_argument("--supprimer", action="store_true",
                    help="retirer aussi du pack les lignes de la campagne que le kit n'a plus (23.09.2026 : anciennes "
                         "unités et garnisons des chefs remplacés par Drycha et Grom)")
    ap.add_argument("--seulement", default=None,
                    help="clés (séparées par des virgules) : --maj ne réécrit que ces lignes (23.09.2026 : la ligne du "
                         "Poste de la Pierre Noire, sans toucher aux écarts anciens des autres régions)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    TEXTES_VIDES.update(TEXTES_VIDES_PAR_TABLE.get(a.table, ()))

    sid = session()
    i = [1]

    def c(outil, args):
        i[0] += 1
        return text(call(sid, outil, args, i[0]))

    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    c("open_packfiles", {"paths": [PACK]})
    # `get_tables_by_table_name` rend une liste vide ici (rpfm_server 5.0.6) : on lit l'inventaire du pack
    rep = c("open_pack_info", {"pack_key": PACK})
    chemins = sorted(set(re.findall(rf'"(db/{a.table}_tables/[^"]+)"', rep)))
    if len(chemins) != 1:
        print(f"table {a.table} : {len(chemins)} fichier(s) dans le pack, il en faut un : {rep[:300]}")
        return 2
    chemin = chemins[0]
    h = json.loads(c("decode_packed_file", {"pack_key": PACK, "path": chemin, "source": "PackFile"}))["DBRFileInfo"][0]
    rep = json.loads(c("fields_processed", {"definition": json.dumps(h["table"]["definition"])}))
    champs = rep if isinstance(rep, list) else list(rep.values())[0]
    noms = [f["name"] for f in champs]
    types = {f["name"]: f["field_type"] for f in champs}
    donnees = h["table"]["table_data"]

    def v(ligne, col):
        cell = ligne[noms.index(col)]
        return list(cell.values())[0] if isinstance(cell, dict) else cell

    print(f"{chemin} : {len(donnees)} lignes ; colonnes {noms}")
    if donnees:
        print("   exemple :", donnees[0])
    du_pack = {str(v(l, a.cle)): l for l in donnees}
    kit = lignes_kit(a.table, a.campagne)
    manquantes = [k for k in kit if str(k.get(a.cle, "")) not in du_pack]
    differentes = []
    for k in kit:
        p = du_pack.get(str(k.get(a.cle, "")))
        if p is not None:
            ecarts = [n for n in noms if n in k and n not in TEXTES_VIDES and valeur(types[n], k[n]) != v(p, n)]
            if ecarts:
                differentes.append((k.get(a.cle), ecarts))
    print(f"kit : {len(kit)} lignes pour {a.campagne} ; absentes du pack : {len(manquantes)} ; "
          f"différentes : {len(differentes)} {differentes[:5]}")
    colonnes_absentes = [n for n in noms if kit and n not in kit[0]]
    if colonnes_absentes:
        print("colonnes du pack absentes du kit :", colonnes_absentes)
        return 2
    for k in manquantes[:5]:
        print("   à ajouter :", {n: k[n] for n in noms})
    for cle, ecarts in differentes[:40]:
        print(f"   diffère : {a.cle}={cle} colonnes {ecarts}")
    # lignes du pack que le kit n'a plus : le pack ne porte que notre campagne (fichiers `*_wh_dlc05_wood_elves`) ; une
    # colonne `campaign` éventuelle est vérifiée quand même
    cles_kit = {str(k.get(a.cle, "")) for k in kit}
    en_trop = [cle for cle, l in du_pack.items() if cle not in cles_kit
               and ("campaign" not in noms or v(l, "campaign") == a.campagne)]
    if en_trop:
        print(f"lignes du pack absentes du kit : {len(en_trop)} {en_trop[:10]}"
              + ("" if a.supprimer else " (--supprimer pour les retirer)"))
        if a.supprimer and len(en_trop) > a.max_retraits:
            sys.exit(f"{len(en_trop)} lignes à retirer : trop pour une retouche, vérifier le filtre avant de continuer")
    if not a.apply:
        print("essai à blanc : relancer avec --apply" + ("" if a.maj else " (et --maj pour réécrire les lignes qui diffèrent)"))
        return 0
    seules = set(a.seulement.split(",")) if a.seulement else None
    a_reecrire = [k for k in kit if str(k.get(a.cle, "")) in du_pack and a.maj
                  and (seules is None or str(k.get(a.cle, "")) in seules)
                  and (any(n in k and n not in TEXTES_VIDES and valeur(types[n], k[n]) != v(du_pack[str(k[a.cle])], n)
                           for n in noms)
                       or any(n in TEXTES_VIDES and v(du_pack[str(k[a.cle])], n) not in ("", None) for n in noms))]
    a_retirer = en_trop if a.supprimer else []
    if not manquantes and not a_reecrire and not a_retirer:
        return 0
    dossier = os.path.join(ATELIER, "05-journal", "db-backups",
                           datetime.now().strftime("%Y%m%d-%H%M%S") + "-zz-startpos-db")
    os.makedirs(dossier, exist_ok=True)
    shutil.copy2(PACK, dossier)
    for k in manquantes:
        donnees.append([{types[n]: "" if n in TEXTES_VIDES else valeur(types[n], k[n])} for n in noms])
    for k in a_reecrire:
        ligne = du_pack[str(k[a.cle])]
        for j, n in enumerate(noms):
            if n in k:
                ligne[j] = {types[n]: "" if n in TEXTES_VIDES else valeur(types[n], k[n])}
    if a_retirer:
        retirees = {id(du_pack[cle]) for cle in a_retirer}
        h["table"]["table_data"] = [l for l in donnees if id(l) not in retirees]
    rep = c("save_packed_file_from_view", {"pack_key": PACK, "path": chemin, "data": json.dumps({"DB": h})})
    if "Success" not in rep:
        # 21.09.2026 : une écriture refusée ne dit rien si on ne lit pas la réponse ; le pack restait
        # inchangé alors que le script annonçait les lignes ajoutées.
        sys.exit(f"RPFM a refusé la table : {rep[:400]}")
    rep = c("save_packfile", {"pack_key": PACK})
    if "Error" in rep[:40]:
        # le pack est verrouillé tant que le jeu (ou RPFM ailleurs) le tient ouvert : fermer le jeu
        sys.exit(f"pack non enregistré : {rep[:300]}")
    print(rep[:200])
    print(f"pack : {len(manquantes)} ligne(s) ajoutée(s), {len(a_reecrire)} réécrite(s), {len(a_retirer)} retirée(s) ; "
          f"sauvegarde dans {dossier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
