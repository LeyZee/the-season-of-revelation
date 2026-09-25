#!/usr/bin/env python3
"""
image_menu_vers_jeu.py - l'image clé de la Saison (écran « Nouvelle campagne », audit de l'avant-campagne A7, 25.09.2026)
recadrée aux trois formats de CA, aux dimensions et au mode EXACTS des fichiers actuels de
04-projets\\saison-des-revelations\\images-campagne\\ (mêmes noms), déposés dans illustrations\\recadrages-menu\\ ; la
construction les met en place (images-campagne, build_pack). Traitement de CA relevé sur les fichiers actuels :
bouton au bord gauche assombri, vertical à bande sombre en bas.

Session « IA et modding 3D ». Usage :
    python image_menu_vers_jeu.py            # bilan à blanc
    python image_menu_vers_jeu.py --apply    # écrit les trois PNG et une planche de contrôle
"""

import argparse
import os
import sys

from PIL import Image

ATELIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
ORIGINAL = os.path.join(PROJET, "illustrations", "saison_menu.png")
ACTUELS = os.path.join(PROJET, "images-campagne")
SORTIE = os.path.join(PROJET, "illustrations", "recadrages-menu")
BASE = "wh_dlc05_wood_elves_map_1"


def recadrer(im, w, h):
    """Recadrage au centre au rapport w/h, puis réduction Lanczos."""
    W, H = im.size
    if W / H > w / h:
        nw = round(H * w / h)
        im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = round(W * h / w)
        im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    return im.resize((w, h), Image.LANCZOS)


def assombrir(im, sens, part, force):
    """Dégradé noir : sens « gauche » (du bord gauche vers la droite) ou « bas » (du bas vers le haut), sur `part` de
    la largeur ou de la hauteur, opacité maximale `force` (0 à 1) au bord."""
    im = im.convert("RGBA")
    w, h = im.size
    voile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = voile.load()
    longueur = int((w if sens == "gauche" else h) * part)
    for i in range(longueur):
        a = int(255 * force * (1 - i / longueur) ** 1.5)
        if sens == "gauche":
            for y in range(h):
                px[i, y] = (0, 0, 0, a)
        else:
            for x in range(w):
                px[x, h - 1 - i] = (0, 0, 0, a)
    return Image.alpha_composite(im, voile)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    src = Image.open(ORIGINAL).convert("RGB")
    print("original :", ORIGINAL, src.size)
    formats = {"": None, "_button": ("gauche", 0.45, 0.75), "_vertical": ("bas", 0.35, 0.8)}
    sorties = []
    for suffixe, voile in formats.items():
        actuel = Image.open(os.path.join(ACTUELS, BASE + suffixe + ".png"))
        w, h = actuel.size
        im = recadrer(src, w, h)
        if voile:
            im = assombrir(im, *voile)
        im = im.convert(actuel.mode)
        dest = os.path.join(SORTIE, BASE + suffixe + ".png")
        print(f"  {BASE + suffixe}.png : {w} x {h}, mode {actuel.mode} -> {dest}")
        sorties.append(im)
        if a.apply:
            os.makedirs(SORTIE, exist_ok=True)
            im.save(dest, "PNG", optimize=True)
    if a.apply:
        # planche de contrôle : les trois côte à côte
        hauteur = max(s.size[1] for s in sorties)
        planche = Image.new("RGB", (sum(s.size[0] for s in sorties) + 40, hauteur), (40, 40, 40))
        x = 0
        for s in sorties:
            planche.paste(s.convert("RGB"), (x, 0))
            x += s.size[0] + 20
        planche.save(os.path.join(SORTIE, "planche_controle.png"))
        print("écrit, avec planche_controle.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
