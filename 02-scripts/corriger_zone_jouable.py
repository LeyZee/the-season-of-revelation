#!/usr/bin/env python3
"""
corriger_zone_jouable.py - corriger A LA SOURCE (dans l'Assembly Kit) les colonnes de fichiers de
notre ligne `campaign_map_playable_areas`.

Pourquoi (21.09.2026, journal `phase-2-startpos-temoin.md` § 17). Une fois le monde de campagne
construit, la generation du startpos meurt a `Warhammer3+0x3211033` (appel virtuel sur un objet
nul) en voulant **lire la minicarte** : le vidage montre qu'elle ouvre
`campaign_maps/wh_dlc05_wood_elves_map_1/wh_dlc05_wood_elves_map_1_minimap.png`, le nom declare
dans `radar_file`. Ce fichier n'existe pas ; le decodeur d'image rend un objet nul, et l'appelant
ne le teste pas.

C'est l'erreur A33 du 20.09.2026 (« aucune des sept colonnes de fichiers ne pointe vers un
fichier du pack »), qu'on croyait corrigee. `ajouter_images_campagne.py` avait bien reecrit la
ligne **dans le pack** — mais `build_pack.py` recopie a chaque construction la ligne **du kit**,
jamais corrigee, et effacait donc la correction a chaque fois.

Ce script ecrit dans `raw_data\\db\\campaign_map_playable_areas.xml`, la source que `build_pack.py`
recopie. Il sauvegarde d'abord le fichier dans `05-journal\\db-backups\\` (regle de l'atelier), ne
remplace que le texte des sept champs **dans notre seul enregistrement**, et garde tout le reste a
l'octet pres. Les noms sont ceux de `ajouter_images_campagne.py` — la convention de CA, cle de
campagne en radical — qui sont les fichiers reellement presents dans le pack.

Ajout du 21.09.2026 (§ 22), trois valeurs qui ne sont pas des fichiers :
- `preview_width` x `preview_height` : l'apercu que le jeu grave dans le startpos
  (`SAVE_GAME_HEADER`, 256 x 256 chez nous jusqu'ici) est fait a cette taille. Warhammer 1 avait
  472 x 600 pour cette carte, soit exactement les proportions du parchemin (800 x 1016) ; nous
  avions 256 x 256, recopie du prologue, qui ecrasait la carte en carre ;
- `sort_order` : 3, apres les trois campagnes de CA (prologue 0, Empires 1, Chaos 2) ; nous etions
  a 0, a egalite avec le prologue.

Usage :
    python corriger_zone_jouable.py            # essai a blanc
    python corriger_zone_jouable.py --apply
"""

import argparse
import io
import os
import re
import shutil
import sys
import time

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
          r"\raw_data\db")
TABLE = os.path.join(KIT_DB, "campaign_map_playable_areas.xml")
CARTE, CAMPAGNE = "wh_dlc05_wood_elves_map_1", "wh_dlc05_wood_elves"

# memes valeurs que `ajouter_images_campagne.py` : c'est lui qui a mis ces fichiers dans le pack
VOULU = {
    "map_file": f"{CAMPAGNE}_map.png",
    "overlay_file": f"{CAMPAGNE}_lookup.tga",
    "radar_file": f"{CAMPAGNE}_minimap.png",
    "minimap_lookup_file": f"{CAMPAGNE}_lookup_minimap.tga",
    "campaign_overlay_map": f"{CAMPAGNE}.dds",
    "campaign_overlay_lookup": f"{CAMPAGNE}_lookup.dds",
    "campaign_overlay_map_text": f"{CAMPAGNE}_text.dds",
    "frontend_image": f"ui/frontend UI/campaign_images/{CARTE}.png",
    # valeurs de Warhammer 1 pour cette carte, et rang apres les campagnes de CA (voir plus haut)
    "preview_width": "472",
    "preview_height": "600",
    "sort_order": "3",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    with io.open(TABLE, encoding="utf-8", newline="") as f:
        texte = f.read()
    motif = re.compile(r"<campaign_map_playable_areas\s[^>]*>(?:(?!</campaign_map_playable_areas>).)*?"
                       rf"<mapname>{CARTE}</mapname>.*?</campaign_map_playable_areas>", re.S)
    trouves = list(motif.finditer(texte))
    if len(trouves) != 1:
        print(f"!! {len(trouves)} enregistrement(s) pour {CARTE} : il en faut exactement un")
        return 2
    m = trouves[0]
    bloc = m.group(0)
    neuf = bloc
    changes = 0
    for champ, valeur in VOULU.items():
        v = re.search(rf"<{champ}>(.*?)</{champ}>", neuf, re.S)
        if not v:
            print(f"   {champ:28} absent de l'enregistrement : laisse tel quel")
            continue
        if v.group(1) == valeur:
            print(f"   {champ:28} deja juste  {valeur!r}")
            continue
        print(f"   {champ:28} {v.group(1)!r}  ->  {valeur!r}")
        neuf = neuf[:v.start(1)] + valeur + neuf[v.end(1):]
        changes += 1
    if not changes:
        print("rien a changer.")
        return 0
    if not a.apply:
        print(f"\n{changes} champ(s) a corriger (essai a blanc, relancer avec --apply)")
        return 0
    dest = os.path.join(ATELIER, "05-journal", "db-backups",
                        "playable-areas-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(TABLE, dest)
    print(f"\nsauvegarde : {dest}")
    texte = texte[:m.start()] + neuf + texte[m.end():]
    with io.open(TABLE, "w", encoding="utf-8", newline="") as f:
        f.write(texte)
    print(f"{changes} champ(s) corrige(s) dans {TABLE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
