#!/usr/bin/env python3
"""
placer_chefs_capitale.py - OBSOLÈTE (22.09.2026, 23 h 40) : NE PLUS LANCER. Remplacé par `garnisons_chefs.py`, qui a
annulé son effet : un chef posé sur la case de sa capitale se retrouve à deux cases, hors les murs ; WH1 et CA mettent
le chef en (0, 0) et le lient à sa colonie par `start_pos_character_to_settlements` (chef en garnison). Gardé pour
mémoire et pour sa lecture des cases de colonie dans le startpos (`cases_des_colonies`).

(texte d'origine) place dans leur capitale les chefs de faction que les tables de départ laissent en (0, 0).

Pourquoi (22.09.2026, 23 h 40 ; Charles en jeu : « il manque les armées des factions ennemies ») : dans les tables
`start_pos_characters` de la mini-campagne de WH1, 23 des 26 chefs de faction (duchés bretons, clairières elfes,
peaux-vertes, nains, Mousillon), chacun à la tête de 6 ou 7 unités, ont startx / starty = (0, 0) ; dans WH1 cela
voulait dire « à la capitale ». Le startpos de WH3 les a pris au pied de la lettre : les 23 armées sont toutes en case
(1, 1), monde (0,7 ; 1,2), dans le coin de la carte (relevé dans les LOCOMOTABLE des 78 CHARACTER du startpos).

Correctif : chaque chef va sur la colonie de sa capitale (`start_pos_regions.faction_capital` = 1 et
`owning_faction`). La case d'une colonie se lit dans notre startpos : centre du ZOE_BLOCK de
REGION/SETTLEMENT/GARRISON_RESIDENCE (ex. Castle Carcassonne (63, 134)), contrôlé par la présence, à cette case, du
chef de garnison que le jeu y a posé.

Le jeu génère le startpos depuis `zz_startpos_db.pack` : après `--apply` (kit, sauvegarde dans
`05-journal\\db-backups\\`), recopier par
    python synchroniser_pack_startpos.py --table start_pos_characters --cle ID --maj --apply
puis régénérer le startpos (commande exacte : CLAUDE.md), et le recopier dans le projet avant `build_pack.py`.

Usage :
    python placer_chefs_capitale.py            # à blanc : chefs, capitales, cases
    python placer_chefs_capitale.py --apply    # écrit start_pos_characters.xml du kit
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comparer_structure_esf as CS                                  # noqa: E402
import lire_esf as E                                                 # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
STARTPOS = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "startpos", "startpos.esf")
CAMPAGNE = "wh_dlc05_wood_elves"


def lignes(table):
    t = open(os.path.join(KIT_DB, table + ".xml"), encoding="utf-8").read()
    return t, [(m.start(), m.end(), dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1))))
               for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S)]


def cases_des_colonies():
    """{région: (x, y)} du startpos (centre du ZOE_BLOCK), et l'ensemble des cases des personnages."""
    esf = CS.interne(STARTPOS)
    _, ascii_, _ = E.lire_chaines(esf)
    A = dict(ascii_)
    colonies, persos = {}, set()
    for c, n in E.parcours(esf, esf.racine):
        if n["type"] != "record":
            continue
        if c[-1] == "SETTLEMENT" and "REGION" in c:
            cle = None
            for v in n["enfants"]:
                if v["type"] == "valeur" and "ascii" in E.NOMS_TYPES.get(v["base"], ""):
                    s = A.get(int.from_bytes(v["données"], "little"), "")
                    if s.startswith("settlement:"):
                        cle = s[len("settlement:"):]
                        break
            gr = [e for e in n["enfants"] if e["type"] == "record" and esf.nom(e["nom"]) == "GARRISON_RESIDENCE"]
            zoe = [e for e in gr[0]["enfants"] if e["type"] == "record" and esf.nom(e["nom"]) == "ZOE_BLOCK"] if gr else []
            vals = []
            for z in zoe:
                for g in z["enfants"]:
                    for v in (g["enfants"] if g["type"] == "groupe" else [g]):
                        if v["type"] == "valeur":
                            vals.append(int.from_bytes(v["données"], "little"))
            if cle and len(vals) >= 2:
                xs, ys = vals[0::2], vals[1::2]
                colonies[cle] = (round(sum(xs) / len(xs)), round(sum(ys) / len(ys)))
        elif c[-1] == "LOCOMOTABLE" and len(c) > 1 and c[-2] == "CHARACTER":
            vs = [v for v in n["enfants"] if v["type"] == "valeur"]
            persos.add((int.from_bytes(vs[1]["données"], "little"), int.from_bytes(vs[2]["données"], "little")))
    return colonies, persos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    _, fac = lignes("start_pos_factions")
    factions = {r["ID"]: r["faction"] for _, _, r in fac if r.get("campaign") == CAMPAGNE}
    _, reg = lignes("start_pos_regions")
    capitale = {r["owning_faction"]: r["region"] for _, _, r in reg
                if r.get("campaign") == CAMPAGNE and r.get("faction_capital") == "1"}
    colonies, persos = cases_des_colonies()
    texte, chars = lignes("start_pos_characters")
    a_ecrire, erreurs = [], []
    for debut, fin, r in chars:
        if r.get("faction") not in factions or (r["startx"], r["starty"]) != ("0", "0"):
            continue
        region = capitale.get(r["faction"])
        case = colonies.get(region) if region else None
        if not case:
            erreurs.append(f"{factions[r['faction']]} : capitale {region} sans case connue")
            continue
        controle = "chef de garnison sur la case" if case in persos else "AUCUN personnage sur la case (à vérifier)"
        print(f"  {factions[r['faction']]:34s} {r['subtype']:34s} -> {region:44s} {case}  [{controle}]")
        a_ecrire.append((debut, fin, case))
    for e in erreurs:
        print("  !!", e)
    print(f"{len(a_ecrire)} chef(s) à placer ; {len(erreurs)} sans capitale connue")
    if not a.apply or not a_ecrire:
        return 0 if not erreurs else 1
    dossier = os.path.join(ATELIER, "05-journal", "db-backups",
                           datetime.now().strftime("%Y%m%d-%H%M%S") + "-chefs-capitale")
    os.makedirs(dossier, exist_ok=True)
    shutil.copy2(os.path.join(KIT_DB, "start_pos_characters.xml"), dossier)
    morceaux, pos = [], 0
    for debut, fin, (x, y) in sorted(a_ecrire):
        bloc = texte[debut:fin]
        bloc = re.sub(r"<startx>0</startx>", f"<startx>{x}</startx>", bloc, count=1)
        bloc = re.sub(r"<starty>0</starty>", f"<starty>{y}</starty>", bloc, count=1)
        morceaux += [texte[pos:debut], bloc]
        pos = fin
    morceaux.append(texte[pos:])
    with open(os.path.join(KIT_DB, "start_pos_characters.xml"), "w", encoding="utf-8", newline="") as f:
        f.write("".join(morceaux))
    print(f"écrit : start_pos_characters.xml du kit ; sauvegarde dans {dossier}")
    print("suite : synchroniser_pack_startpos.py --table start_pos_characters --cle ID --maj --apply, puis startpos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
