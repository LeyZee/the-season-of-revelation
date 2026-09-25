#!/usr/bin/env python3
"""
illustrations_vers_jeu.py - les illustrations de Charles (04-projets\\saison-des-revelations\\illustrations\\<clé>.png ou
.webp, 16:9) réduites à la taille des grandes images d'évènement de CA (800 × 450, PNG), à l'arborescence du pack :
04-projets\\saison-des-revelations\\images-evenements\\ui\\eventpics\\saison\\<clé>.png. Les clés sont celles de
donnees_campagne.ILLUSTRATIONS (colonne ui_image « saison/<clé> » des missions, lot 12).

Session « IA et modding 3D », 24.09.2026. Taille relevée sur les images de CA (ui/eventpics/brt/generic.png,
wef/generic.png… : 380 × 214). Recadrage au centre si le rapport n'est pas exactement 16:9 ; réduction Lanczos.
25.09.2026 : 800 × 450 (images larges de CA : victory.png, defeat.png, incident de l'arrivée d'Ariel ; le panneau de fin
de mission affiche du 800 × 450, où le 380 × 214 était agrandi et flou ; le jeu réduit lui-même pour les petits cadres).
Recherche : scratchpad de la session IA, images-lot5\rapport.md.

Usage :
    python illustrations_vers_jeu.py            # bilan à blanc
    python illustrations_vers_jeu.py --apply    # écrit les PNG du jeu
"""

import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import donnees_campagne as D                                          # noqa: E402

ATELIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
ORIGINAUX = os.path.join(PROJET, "illustrations")
SORTIE = os.path.join(PROJET, "images-evenements", "ui", "eventpics", "saison")
LARGEUR, HAUTEUR = 800, 450


def original(cle):
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        p = os.path.join(ORIGINAUX, cle + ext)
        if os.path.exists(p):
            return p
    return None


def reduire(chemin):
    im = Image.open(chemin).convert("RGB")
    w, h = im.size
    cible = LARGEUR / HAUTEUR
    if w / h > cible:
        nw = round(h * cible)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < cible:
        nh = round(w / cible)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((LARGEUR, HAUTEUR), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    manquants = 0
    for cle, valeur in D.ILLUSTRATIONS.items():
        nom = valeur.split("/", 1)[1]
        src = original(cle)
        if not src:
            print(f"  !! {cle} : aucun original dans {ORIGINAUX}")
            manquants += 1
            continue
        im = reduire(src)
        dest = os.path.join(SORTIE, nom + ".png")
        print(f"  {cle} : {os.path.basename(src)} {Image.open(src).size} -> {im.size} {dest}")
        if a.apply:
            os.makedirs(SORTIE, exist_ok=True)
            im.save(dest, "PNG", optimize=True)
    print("écrit" if a.apply else "à blanc : rien d'écrit (--apply)")
    return 1 if manquants else 0


if __name__ == "__main__":
    sys.exit(main())
