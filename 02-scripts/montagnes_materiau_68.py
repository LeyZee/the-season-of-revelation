#!/usr/bin/env python3
"""
montagnes_materiau_68.py - convertit SUR PLACE, au matériau 68 des objets de CA, les modèles de montagne et de falaise de WH1
déjà produits par `montagnes_wh1.py` (dans le projet et dans `working_data`), sans refaire toute la chaîne du terrain.

Pourquoi (03.10.2026, plantage de rendu `+0x1AC3FF2`, GUIDE § 15 n° 150, accord de Charles) : voir
`montagnes_wh1.MATERIAU_OBJET`. La chaîne normale (`terrain_wh1_vers_terry.py` -> `montagnes_wh1.construire`) produit
désormais directement des modèles au matériau 68 ; ce script convertit les fichiers déjà en place, identiques à ce que la
chaîne écrirait (la conversion est la dernière étape de `construire`). Un modèle déjà au matériau 68 est laissé tel quel.

Usage :
    python montagnes_materiau_68.py            # à blanc : compte et contrôle
    python montagnes_materiau_68.py --apply    # sauvegarde des deux dossiers, puis conversion
"""
import argparse
import glob
import os
import shutil
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import montagnes_wh1 as MW                                          # noqa: E402

RACINES = [MW.SORTIE, MW.KIT_WD]
SAUVEGARDES = os.path.join(MW.ATELIER, "05-journal", "terrain-backups")


def modeles(racine):
    return sorted(glob.glob(os.path.join(racine, *MW.DOSSIER_MODELES.split("/"), "**", "*.rigid_model_v2"),
                            recursive=True))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    plan = []
    for racine in RACINES:
        fs = modeles(racine)
        a49 = [f for f in fs if MW.morceaux(open(f, "rb").read())[0][1] == 49]
        print(f"{racine} : {len(fs)} modèles, {len(a49)} au matériau 49")
        plan.append((racine, fs, a49))
    convertis = {}
    for racine, fs, a49 in plan:
        for f in fs:
            b = open(f, "rb").read()
            if f in a49:
                convertis[f] = MW.vers_materiau_68(b, os.path.basename(f).rsplit(".", 1)[0])
            else:
                # déjà au matériau 68 (passage du 03.10, 18 h 34) : le masque de CA remplacé par le nôtre (erreur 254)
                corrige = MW.masque_68(b)
                if corrige != b:
                    convertis[f] = corrige
    print(f"conversion à blanc : {len(convertis)} fichiers, {sum(len(v) for v in convertis.values()) / 1e6:.1f} Mo")
    if not a.apply:
        print("à blanc ; relancer avec --apply")
        return 0
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, (racine, fs, a49) in enumerate(plan):
        if a49:
            dest = os.path.join(SAUVEGARDES, f"montagnes-avant-68-{stamp}-{i}")
            shutil.copytree(os.path.join(racine, *MW.DOSSIER_MODELES.split("/")), dest)
            print(f"sauvegarde : {dest}")
    for f, octets in convertis.items():
        with open(f, "wb") as h:
            h.write(octets)
    restants = sum(1 for racine, fs, _ in plan for f in modeles(racine)
                   if MW.morceaux(open(f, "rb").read())[0][1] != 68)
    print(f"écrits : {len(convertis)} ; modèles pas au matériau 68 après conversion : {restants}")
    return 1 if restants else 0


if __name__ == "__main__":
    sys.exit(main())
