#!/usr/bin/env python3
"""
shroud_heights.py - recalculer `shroud_heights.dds` (hauteurs du brouillard de guerre) selon la règle de CA.

Pourquoi (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\terry-trous.md`) : dans Terry comme en jeu, notre
terrain ne s'affiche que par parcelles, le reste montrant les nuages bleu sombre du brouillard. Le fichier
compilé par BOB (« Campaign Shroud Heights ») vaut **1,0 partout** : l'action a combiné le masque du projet
(`*.height_shroud.*.tif`, 1,0 presque partout, comme chez CA) avec un relief nul. Chez les Empires, le fichier
livré suit exactement la règle (mesurée sur 22 millions de pixels, écart médian 0,000, p5 −0,04) :

    hauteur du brouillard = max du relief sur chaque bloc de 2 × 2 pixels + masque

à la moitié de la résolution du relief, **rangée 0 au sud** (le tif est nord en haut), en R32F (DXGI 41,
en-tête DX10). Le brouillard flotte ainsi une unité au-dessus du sol ; à 1,0 partout, il était sous nos
collines (médiane 3,5), et le moteur perdait des parcelles entières.

Le script réécrit le fichier de BOB dans `working_data` en gardant son en-tête (mêmes dimensions, même format),
après sauvegarde. À relancer après chaque compilation BOB du terrain de campagne (recette, GUIDE § 12.3).

Usage :
    python shroud_heights.py --carte wh_dlc05_wood_elves_map_1            # contrôle
    python shroud_heights.py --carte wh_dlc05_wood_elves_map_1 --apply    # réécriture
"""

import argparse
import glob
import os
import shutil
import struct
import sys
import time

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
SAUVEGARDES = r"C:\TotalWar-CampaignMap\05-journal\terrain-backups"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carte", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    projet = os.path.join(KIT, "raw_data", "terrain", "campaigns", a.carte)
    cible = os.path.join(KIT, "working_data", "terrain", "campaigns", a.carte, "shroud_heights.dds")
    relief = np.array(Image.open(glob.glob(os.path.join(projet, "*.height.*.tif"))[0]), np.float32)
    masque = np.array(Image.open(glob.glob(os.path.join(projet, "*.height_shroud.*.tif"))[0]), np.float32)
    b = open(cible, "rb").read()
    if b[84:88] != b"DX10" or struct.unpack_from("<I", b, 128)[0] != 41:
        sys.exit(f"{cible} : format inattendu (attendu R32F DX10)")
    h, w = struct.unpack_from("<II", b, 12)
    if masque.shape != (h, w) or relief.shape != (2 * h, 2 * w):
        sys.exit(f"dimensions : fichier {w}x{h}, masque {masque.shape[::-1]}, relief {relief.shape[::-1]} (attendu 2 ×)")
    ancien = np.frombuffer(b[148:148 + w * h * 4], "<f4").reshape(h, w)
    haut = relief.reshape(h, 2, w, 2).max(axis=(1, 3)) + masque
    neuf = haut[::-1].astype("<f4")                   # rangée 0 au sud, comme le fichier des Empires
    print(f"relief {relief.shape[1]}x{relief.shape[0]} [{relief.min():.3f}, {relief.max():.3f}] ; masque [{masque.min()}, {masque.max()}]")
    print(f"ancien : [{ancien.min():.3f}, {ancien.max():.3f}], {len(np.unique(ancien))} valeur(s) ; "
          f"neuf : [{neuf.min():.3f}, {neuf.max():.3f}]")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply pour réécrire", cible)
        return 0
    os.makedirs(SAUVEGARDES, exist_ok=True)
    garde = os.path.join(SAUVEGARDES, f"shroud_heights-avant-{time.strftime('%Y%m%d-%H%M%S')}.dds")
    shutil.copy2(cible, garde)
    with open(cible, "wb") as f:
        f.write(b[:148] + neuf.tobytes() + b[148 + w * h * 4:])
    print(f"écrit : {cible} (sauvegarde {garde})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
