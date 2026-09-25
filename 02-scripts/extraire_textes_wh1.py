#!/usr/bin/env python3
"""
extraire_textes_wh1.py - recuperer les textes de la mini-campagne dans les packs de Warhammer 1,
dans une langue donnee.

Pourquoi : notre pack ne contenait **aucun** fichier `.loc`. Charles a ouvert la campagne dans le
menu le 20.09.2026 : elle apparaissait, mais **sans ses textes** (noms de factions, de regions, de
colonies, description de la campagne). Les kits ne livrent pas de `.loc` : ils sont dans les packs
de langue du jeu.

21.09.2026 (journal `phase-2-startpos-temoin.md` § 22) : Charles veut la campagne **en francais et
en anglais**. La premiere version lisait les textes par les dependances de RPFM, donc dans la seule
langue installee (le francais). Celle-ci ouvre directement les packs de langue de Warhammer 1 :

    local_<langue>_we.pack, local_<langue>_bm.pack, local_<langue>_bl.pack, local_<langue>.pack

dans cet ordre, qui est aussi la priorite : une cle vue deux fois garde son premier texte (le
correctif d'un DLC avant le jeu de base ; dans un meme pack, `__core` en dernier). Les deux langues
n'ont pas la meme organisation (l'anglais a un fichier par table, le francais un fichier par
extension) : on lit tous les `.loc` que le pack contient.

On garde les cles qui citent un prefixe (`wh_dlc05_`) et les cles purement numeriques que la
recherche par prefixe manquait :
- le titre et la description de la zone jouable de Warhammer 1, sous son numero (1564135548) ;
- la description de chaque faction de depart (`start_pos_factions_description_<ID>`, que CA
  remplit pour ses factions jouables) : nos lignes `start_pos_factions` ont garde les identifiants
  de Warhammer 1 (verifie : 2120137230 pour Orion, 2120137202 pour Durthu), on les lit dans le kit.

Regle apprise le 20.09.2026 : **une session MCP = un etat** (jeu selectionne, packs ouverts).
Ce script fait toute la partie Warhammer 1 en une seule session et n'ecrit rien cote WH3.
`injecter_textes.py` pose ensuite les textes dans les packs Warhammer 3.

Usage :
    python extraire_textes_wh1.py                      # francais -> textes-wh1.json
    python extraire_textes_wh1.py --langue en          # anglais  -> textes-wh1-en.json
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
REFS = os.path.join(ATELIER, "03-references", "saison-des-revelations")
WH1_DATA = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER/data/"
SUFFIXES_PACKS = ["_we", "_bm", "_bl", ""]          # priorite : correctifs des DLC, puis la base
INDEX_ZONE_WH1 = "1564135548"                       # campaign_map_playable_areas de WH1
CAMPAGNE = "wh_dlc05_wood_elves"
KIT_FACTIONS = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
                r"\raw_data\db\start_pos_factions.xml")


def cles_exactes():
    cles = {f"campaign_map_playable_areas_onscreen_name_{INDEX_ZONE_WH1}",
            f"campaign_map_playable_areas_onscreen_description_{INDEX_ZONE_WH1}"}
    with open(KIT_FACTIONS, encoding="utf-8") as f:
        xml = f.read()
    for bloc in re.findall(r"<start_pos_factions\b.*?</start_pos_factions>", xml, re.S):
        if f"<campaign>{CAMPAGNE}</campaign>" in bloc:
            cles.add("start_pos_factions_description_" + re.search(r"<ID>(\d+)</ID>", bloc).group(1))
    return cles


def entrees(donnees):
    """Les lignes (cle, texte, relance) d'un fichier Loc decode par RPFM."""
    info = donnees["LocRFileInfo"][0]
    noms = [f["name"] for f in info["table"]["definition"]["fields"]]
    out = []
    for ligne in info["table"]["table_data"]:
        valeurs = [list(cell.values())[0] if isinstance(cell, dict) else cell for cell in ligne]
        out.append(dict(zip(noms, valeurs)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--langue", default="fr", help="code des packs de langue de WH1 : fr, en, ge...")
    ap.add_argument("--prefixes", nargs="+", default=["wh_dlc05_"])
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sortie = a.out or os.path.join(REFS, "textes-wh1.json" if a.langue == "fr"
                                   else f"textes-wh1-{a.langue}.json")

    sid = session()
    i = [1]

    def c(tool, args):
        i[0] += 1
        return text(call(sid, tool, args, i[0]))

    c("set_game_selected", {"game_name": "warhammer", "rebuild_dependencies": False})
    exactes = cles_exactes()
    print(f"  {len(exactes)} cles exactes (zone jouable, factions de depart)")
    garde, total = {}, 0
    for suffixe in SUFFIXES_PACKS:
        pack = f"{WH1_DATA}local_{a.langue}{suffixe}.pack"
        if not os.path.exists(pack):
            print(f"  {os.path.basename(pack):24s} absent, ignore")
            continue
        c("open_packfiles", {"paths": [pack]})
        chemins = re.findall(r'"(text/[^"]+\.loc)"', c("open_pack_info", {"pack_key": pack}))
        chemins.sort(key=lambda p: ("__core" in p, p))           # __core en dernier
        for chemin in chemins:
            brut = c("decode_packed_file", {"pack_key": pack, "path": chemin, "source": "PackFile"})
            try:
                lignes = entrees(json.loads(brut))
            except (ValueError, KeyError):
                print(f"  {chemin:44s} illisible, ignore")
                continue
            total += len(lignes)
            n = 0
            for l in lignes:
                cle = l.get("key", "")
                if cle in exactes or any(p in cle for p in a.prefixes):
                    if cle not in garde:
                        garde[cle] = {"text": l.get("text", ""),
                                      "source": f"{os.path.basename(pack)}:{chemin}"}
                        n += 1
            if n:
                print(f"  {os.path.basename(pack):24s} {chemin:44s} {len(lignes):6d} lignes, {n:5d} retenues")

    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(garde, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"\n{len(garde)} entrees gardees sur {total} lues -> {sortie}")

    # un apercu, pour voir tout de suite si on a bien les textes de l'ecran de selection
    for motif in ("campaigns_onscreen_name", "campaign_map_playable_areas", "factions_screen_name",
                  "regions_onscreen", "frontend_faction_leaders_loading_screen_text"):
        ex = [(k, v["text"]) for k, v in garde.items() if motif in k][:2]
        for k, t in ex:
            print(f"     {k}  =  {t[:70]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
