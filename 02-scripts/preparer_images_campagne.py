#!/usr/bin/env python3
"""
preparer_images_campagne.py - les trois images de la vignette « campagne » de l'ecran Nouvelle
campagne, faites comme celles de CA, a partir d'une illustration officielle deja dans le jeu.

Pourquoi (21.09.2026, journal `phase-2-startpos-temoin.md` § 22). Charles a ouvert l'ecran : la
vignette CAMPAGNE etait vide. La mise en page de CA (`ui/frontend ui/campaign_select_new.twui.xml`)
lit l'image de la zone jouable par `CcoCampaignMapPlayableAreaRecord.FrontendImagePath` (colonne
`frontend_image`) et lui accole un suffixe :

| fichier                   | taille chez CA        | ou                                            |
|---------------------------|-----------------------|-----------------------------------------------|
| `<nom>.png`               | 1600 x 900 (Empires)  | fond plein ecran, centre (`ScreenSizedComponent`) |
| `<nom>_button.png`        | 278 x 128             | bouton de la liste ; gauche fondue dans un brun tres sombre, liseré (55, 8, 2) |
| `<nom>_vertical.png`      | 380 x 735             | carte verticale ; 660 px d'image puis une bande unie (23, 8, 8) pour le titre |

Nous n'avions que `<nom>.png`, et c'etait la vignette verte et rouge de Warhammer 1.

Aucun asset neuf : la source est l'ecran de chargement des Elfes sylvains de Warhammer 3
(`ui/loading_ui/load_images/campaign_wood_elves1.png`, 1920 x 1200, extrait des fichiers du jeu dans
`03-references\\saison-des-revelations\\ui-wh3\\`). On en garde l'interieur, sans le cadre de
ronces : l'Homme-Arbre, les Elfes et la pierre-runique en fond, la pierre seule en carte verticale.
Le fondu et la bande reprennent les mesures faites sur les trois campagnes de CA.

Sortie : `04-projets\\saison-des-revelations\\images-campagne\\`, que `build_pack.py` embarque sous
`ui/frontend UI/campaign_images/`. Plus `controle_planche.png` (les notres a cote de celles de CA).

Usage :
    python preparer_images_campagne.py
"""

import os
import sys

import numpy as np
from PIL import Image, ImageEnhance

ATELIER = r"C:\TotalWar-CampaignMap"
UI3 = os.path.join(ATELIER, "03-references", "saison-des-revelations", "ui-wh3")
SOURCE = os.path.join(UI3, "ui", "loading_ui", "load_images", "campaign_wood_elves1.png")
CA = os.path.join(UI3, "ui", "frontend ui", "campaign_images")
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "images-campagne")
NOM = "wh_dlc05_wood_elves_map_1"          # base declaree par `frontend_image`

FOND = np.array([23, 8, 8], float)         # bande et fondu, mesures chez CA
LISERE = [55, 8, 2]                        # contour d'un pixel des boutons de CA

# cadrages dans l'illustration source (1920 x 1200), hors du cadre de ronces
CADRE_FOND = (282, 236, 1642, 1001)        # 1360 x 765, soit 16/9
CADRE_VERTICAL = (1136, 236, 1576, 1001)   # la pierre-runique
CADRE_BOUTON = (540, 236, 1642, 743)       # l'Homme-Arbre dans le fondu, la pierre a droite


def relever(img):
    """Un rien de contraste et de lumiere : l'illustration est plus brumeuse que celles de CA."""
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Brightness(img).enhance(1.08)
    return ImageEnhance.Color(img).enhance(1.05)


def image_fond(src):
    return relever(src.crop(CADRE_FOND).resize((1600, 900), Image.LANCZOS))


def image_verticale(src, fondu=70):
    art = np.asarray(relever(src.crop(CADRE_VERTICAL).resize((380, 660), Image.LANCZOS))).astype(float)
    t = np.clip((np.arange(660) - (660 - fondu)) / fondu, 0, 1)[:, None, None]
    t = t * t * (3 - 2 * t) * 0.6                     # le bas de l'image glisse vers la bande
    art = art * (1 - t) + FOND * t
    out = np.empty((735, 380, 3))
    out[:] = FOND
    out[:660] = art
    return Image.fromarray(out.round().astype(np.uint8))


def image_bouton(src):
    art = np.asarray(relever(src.crop(CADRE_BOUTON).resize((278, 128), Image.LANCZOS))).astype(float)
    x = np.arange(278)
    t = np.clip((x - 50) / (185 - 50), 0, 1)          # sombre jusqu'a 50 px, pleine image a 185 px
    f = (0.06 + 0.94 * t * t * (3 - 2 * t))[None, :, None]
    art = art * f + FOND * (1 - f)
    art[0, :] = art[-1, :] = LISERE
    art[:, 0] = art[:, -1] = LISERE
    return Image.fromarray(art.round().astype(np.uint8))


def planche(images):
    """Nos trois images a cote de celles des Empires Immortels, pour juger d'un coup d'oeil."""
    p = Image.new("RGB", (1600, 1000), (60, 60, 60))
    ie = lambda s: Image.open(os.path.join(CA, f"immortal_empires{s}.png")).convert("RGB")
    fond_ie, fond_nous = ie(""), images[""].copy()
    fond_ie.thumbnail((560, 315))
    fond_nous.thumbnail((560, 315))
    p.paste(fond_ie, (20, 20))
    p.paste(fond_nous, (20, 355))
    p.paste(ie("_button"), (20, 700))
    p.paste(images["_button"], (320, 700))
    p.paste(ie("_vertical"), (620, 20))
    p.paste(images["_vertical"], (1020, 20))
    return p


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(SOURCE):
        print(f"!! source absente : {SOURCE}\n   l'extraire des fichiers du jeu (rpfm, "
              f"`ui/loading_ui/load_images/campaign_wood_elves1.png`) dans {UI3}")
        return 2
    src = Image.open(SOURCE).convert("RGB")
    if src.size != (1920, 1200):
        print(f"!! taille inattendue {src.size} : les cadrages supposent 1920 x 1200")
        return 2
    os.makedirs(SORTIE, exist_ok=True)
    images = {"": image_fond(src), "_button": image_bouton(src), "_vertical": image_verticale(src)}
    for suffixe, img in images.items():
        chemin = os.path.join(SORTIE, f"{NOM}{suffixe}.png")
        img.save(chemin, optimize=True)
        print(f"  {os.path.basename(chemin):44s} {img.size[0]} x {img.size[1]}")
    planche(images).save(os.path.join(SORTIE, "controle_planche.png"))
    print(f"  controle_planche.png (a cote des images des Empires Immortels)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
