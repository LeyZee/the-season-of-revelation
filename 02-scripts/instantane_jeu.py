#!/usr/bin/env python3
r"""
instantane_jeu.py - photographier la version installée de Warhammer 3 (et du kit) avant une mise à jour, pour savoir
ensuite exactement ce que la mise à jour a changé.

Pourquoi (23.09.2026) : la mise à jour 9.0 (« Lords of the End Times », 24.09.2026) refond les Comtes Vampires, les
conditions de victoire et les fins de partie ; notre mod copie des lignes de CA, appelle ses scripts et ses interfaces.
Sans l'état d'avant, impossible de dire ce qui a changé.

Ce qui est écrit dans `03-references\instantane-wh3-<étiquette>\` :
- `manifeste.json` : chaque fichier de `<jeu>\data\*.pack`, de l'exe et du kit (`assembly_kit\raw_data\db\*.xml`,
  `binaries\*.exe|dll`) : taille, date, empreinte SHA-1 (sur tout le fichier pour les fichiers de moins de 64 Mo, sinon
  sur le premier et le dernier Mo : assez pour savoir si un gros pack a changé) ;
- des copies intégrales de ce que le mod lit ou copie : `db.pack`, `data_script.pack`, `local_en.pack`, `local_fr.pack`,
  `data.pack`, l'exe, et le dossier `assembly_kit\raw_data\db` (compressé en .zip).

Usage :
    python instantane_jeu.py --etiquette 8.1            # photographie
    python instantane_jeu.py --comparer 8.1             # liste ce qui a changé depuis (après la mise à jour)
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile

JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
ATELIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ATELIER, "03-references")
COPIES = ["data/db.pack", "data/data_script.pack", "data/local_en.pack", "data/local_fr.pack", "data/data.pack",
          "Warhammer3.exe"]
# nos propres fichiers dans <jeu>\data : hors de la photo
NOTRES = ("saison_des_revelations", "!saison_des_revelations", "zz_startpos_db", "zz_saison_essai_auto")


def empreinte(chemin):
    taille = os.path.getsize(chemin)
    h = hashlib.sha1()
    with open(chemin, "rb") as f:
        if taille < 64 * 2 ** 20:
            for bloc in iter(lambda: f.read(2 ** 20), b""):
                h.update(bloc)
        else:
            h.update(f.read(2 ** 20))
            f.seek(-2 ** 20, 2)
            h.update(f.read(2 ** 20))
    return {"taille": taille, "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(chemin))),
            "sha1": h.hexdigest()}


def fichiers():
    out = []
    for n in sorted(os.listdir(os.path.join(JEU, "data"))):
        if n.endswith(".pack") and not n.startswith(NOTRES):
            out.append("data/" + n)
    out.append("Warhammer3.exe")
    kit_db = os.path.join(JEU, "assembly_kit", "raw_data", "db")
    out += ["assembly_kit/raw_data/db/" + n for n in sorted(os.listdir(kit_db)) if n.endswith(".xml")]
    binaires = os.path.join(JEU, "assembly_kit", "binaries")
    out += ["assembly_kit/binaries/" + n for n in sorted(os.listdir(binaires)) if n.endswith((".exe", ".dll"))]
    return out


def photographier(etiquette):
    dossier = os.path.join(REF, f"instantane-wh3-{etiquette}")
    os.makedirs(dossier, exist_ok=True)
    manifeste = {}
    for rel in fichiers():
        manifeste[rel] = empreinte(os.path.join(JEU, *rel.split("/")))
    with open(os.path.join(dossier, "manifeste.json"), "w", encoding="utf-8") as f:
        json.dump({"pris_le": time.strftime("%Y-%m-%d %H:%M:%S"), "fichiers": manifeste}, f, indent=1)
    print(f"manifeste : {len(manifeste)} fichiers")
    for rel in COPIES:
        cible = os.path.join(dossier, *rel.split("/"))
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        shutil.copy2(os.path.join(JEU, *rel.split("/")), cible)
        print(f"copie : {rel} ({os.path.getsize(cible) // 2 ** 20} Mo)")
    kit_db = os.path.join(JEU, "assembly_kit", "raw_data", "db")
    with zipfile.ZipFile(os.path.join(dossier, "kit_raw_data_db.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(kit_db)):
            z.write(os.path.join(kit_db, n), n)
    print(f"kit : raw_data\\db compressé ({os.path.getsize(os.path.join(dossier, 'kit_raw_data_db.zip')) // 2 ** 20} Mo)")


def comparer(etiquette):
    ancien = json.load(open(os.path.join(REF, f"instantane-wh3-{etiquette}", "manifeste.json"), encoding="utf-8"))
    ancien = ancien["fichiers"]
    actuels = set(fichiers())
    for rel in sorted(actuels | set(ancien)):
        if rel not in ancien:
            print(f"NOUVEAU   {rel}")
        elif rel not in actuels:
            print(f"DISPARU   {rel}")
        else:
            e = empreinte(os.path.join(JEU, *rel.split("/")))
            if e["sha1"] != ancien[rel]["sha1"] or e["taille"] != ancien[rel]["taille"]:
                print(f"CHANGÉ    {rel}  ({ancien[rel]['taille']} -> {e['taille']} octets)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etiquette")
    ap.add_argument("--comparer")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.comparer:
        comparer(a.comparer)
    elif a.etiquette:
        photographier(a.etiquette)
    else:
        ap.error("--etiquette ou --comparer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
