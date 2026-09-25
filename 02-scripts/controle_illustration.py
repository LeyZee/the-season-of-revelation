#!/usr/bin/env python3
"""
controle_illustration.py - contrôler une illustration reçue pour « La Saison des Révélations » : taille, style (mesures
comparées aux images d'événement de CA) et lisibilité à la taille du jeu (380 × 214).

Pourquoi (24.09.2026, session « Illustrations ») : Charles génère les images d'événement sur ChatGPT ; avant de les
transmettre à la session « IA et modding 3D », on vérifie qu'elles se fondent parmi celles du jeu (guide :
04-projets\\saison-des-revelations\\illustrations\\GUIDE-DE-STYLE.md, § 2.2 et § 6). Les chiffres signalent ; l'œil décide.

Ce que fait le script, en LECTURE SEULE sur le jeu :
  1. vérifie le rapport 16:9 et la largeur (au moins 1280 px) ;
  2. réduit l'image à 380 × 214 (recadrage centré en 16:9 puis LANCZOS, comme la pose dans le pack) ;
  3. mesure teinte médiane, saturation, luminosité, contraste et part de pixels hors sépia, et les compare aux cibles
     du style A (lavis sépia de CA) ou B (peinture en couleurs retenues) ;
  4. fait une planche : l'image à 380 × 214, à côté de trois images de CA de la même culture, extraites de ui2.pack
     (décompressées par contenu_pack.decompresser) dans un cache du dossier temporaire, jamais dans le jeu.

Usage :
    python controle_illustration.py <image> [<image> ...] [--culture brt|vmp|wef|grn|bst|all] [--style A|B]
                                    [--sortie <dossier>]
Sortie par défaut : 04-projets\\saison-des-revelations\\illustrations\\controle\\ (<nom>_380.png et <nom>_controle.png).
"""

import argparse
import colorsys
import os
import statistics
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contenu_pack as CP  # noqa: E402

UI2 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\ui2.pack"
CACHE = os.path.join(os.environ.get("TEMP", "."), "illustrations_eventpics_ca")
SORTIE = r"C:\TotalWar-CampaignMap\04-projets\saison-des-revelations\illustrations\controle"
W, H = 380, 214

# trois images de CA par culture, pour la planche (mêmes cultures que les images génériques de nos missions)
REFERENCES = {
    "brt": ["brt\\generic.png", "brt\\blessing_of_the_lady.png", "brt\\errant_war.png"],
    "vmp": ["vmp\\generic.png", "vmp\\funeral.png", "vmp\\land_victory.png"],
    "wef": ["wef\\generic.png", "wef\\morghur_emerges.png", "wef\\oak_of_ages_level_5.png"],
    "grn": ["grn\\generic.png", "grn\\army_morale_up.png", "grn\\land_victory.png"],
    "bst": ["bst\\generic.png", "bst\\bray_herd_rises.png", "bst\\faction.png"],
    "all": ["all\\gotrek_felix.png", "all\\queen_and_crone.png", "all\\chaos_invasion.png"],
}

# cibles (guide § 2.2 et § 3) : (min, max) ; « hors » = part de pixels colorés hors de la bande 15°-50°
CIBLES = {
    "A": {"teinte": (25, 40), "saturation": (0.40, 0.62), "luminosite": (0.28, 0.48), "contraste": (0.11, 0.17),
          "hors_sepia": (0.0, 0.06)},
    "B": {"teinte": (20, 45), "saturation": (0.30, 0.50), "luminosite": (0.24, 0.42), "contraste": (0.14, 0.20),
          "hors_sepia": (0.04, 0.15)},
}
HORS_SEPIA_VAMPIRES = 0.20        # patine gris-vert des Comtes Vampires (style A)


def a_la_taille_du_jeu(im):
    """Recadrage centré en 16:9, puis réduction à 380 × 214."""
    im = im.convert("RGB")
    w, h = im.size
    cible = W / H
    if w / h > cible:
        nw = round(h * cible)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < cible:
        nh = round(w / cible)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((W, H), Image.LANCZOS)


def mesures(im):
    """Mesures d'une image déjà à 380 × 214 (un pixel sur trois)."""
    donnees = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
    px = list(donnees)[::3]
    sat, lum, teintes = [], [], []
    for r, g, b in px:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sat.append(s)
        lum.append(0.299 * r / 255 + 0.587 * g / 255 + 0.114 * b / 255)
        if s > 0.12 and v > 0.15:
            teintes.append(h * 360)
    return {
        "teinte": statistics.median(teintes) if teintes else float("nan"),
        "saturation": statistics.mean(sat),
        "luminosite": statistics.mean(lum),
        "contraste": statistics.pstdev(lum),
        "hors_sepia": sum(1 for t in teintes if not 15 <= t <= 50) / len(px),
    }


def reference(chemin_interne):
    """Image de CA (lecture seule dans ui2.pack), gardée dans le cache du dossier temporaire."""
    os.makedirs(CACHE, exist_ok=True)
    local = os.path.join(CACHE, chemin_interne.replace("\\", "_"))
    if not os.path.exists(local):
        octets = CP.extraire(UI2, "ui\\eventpics\\" + chemin_interne)
        if octets is None:
            return None
        with open(local, "wb") as f:
            f.write(octets)
    return Image.open(local)


def verdicts(m, style, culture):
    cibles = dict(CIBLES[style])
    if style == "A" and culture == "vmp":
        cibles["hors_sepia"] = (0.0, HORS_SEPIA_VAMPIRES)
    out = []
    for cle, (bas, haut) in cibles.items():
        v = m[cle]
        ok = bas <= v <= haut
        if cle in ("hors_sepia",):
            txt = f"{100 * v:.1f} % (cible {100 * bas:.0f} à {100 * haut:.0f} %)"
        elif cle == "teinte":
            txt = f"{v:.0f}° (cible {bas} à {haut}°)"
        else:
            txt = f"{v:.2f} (cible {bas:.2f} à {haut:.2f})"
        out.append((cle, ok, txt))
    return out


def planche(nom, petite, m, refs, sortie):
    bande = 30
    vignettes = [(nom, petite, m)] + refs
    largeur = 2 * (W + 6) + 6
    hauteur = ((len(vignettes) + 1) // 2) * (H + bande + 6) + 6
    fond = Image.new("RGB", (largeur, hauteur), (30, 30, 30))
    d = ImageDraw.Draw(fond)
    for k, (titre, im, mm) in enumerate(vignettes):
        x = 6 + (k % 2) * (W + 6)
        y = 6 + (k // 2) * (H + bande + 6)
        fond.paste(im, (x, y))
        d.text((x + 2, y + H + 2), titre[:60], fill=(235, 235, 235))
        d.text((x + 2, y + H + 15), f"teinte {mm['teinte']:.0f}  sat {mm['saturation']:.2f}  lum {mm['luminosite']:.2f}"
               f"  contraste {mm['contraste']:.2f}  hors sepia {100 * mm['hors_sepia']:.1f} %", fill=(200, 200, 200))
    chemin = os.path.join(sortie, f"{nom}_controle.png")
    fond.save(chemin)
    return chemin


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--culture", default="brt", choices=sorted(REFERENCES))
    ap.add_argument("--style", default="A", choices=["A", "B"])
    ap.add_argument("--sortie", default=SORTIE)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(a.sortie, exist_ok=True)
    refs = []
    for c in REFERENCES[a.culture]:
        im = reference(c)
        if im is None:
            print(f"  référence introuvable dans ui2.pack : {c}")
            continue
        petite = a_la_taille_du_jeu(im)
        refs.append((f"CA : {c}", petite, mesures(petite)))
    for chemin in a.images:
        nom = os.path.splitext(os.path.basename(chemin))[0]
        im = Image.open(chemin)
        w, h = im.size
        print(f"== {nom} : {w} × {h}, rapport {w / h:.3f} (16:9 = 1.778)")
        if abs(w / h - 16 / 9) > 0.02:
            print("   ! rapport différent de 16:9 : l'image sera rognée au centre")
        if w < 1280:
            print("   ! moins de 1280 px de large")
        petite = a_la_taille_du_jeu(im)
        petite.save(os.path.join(a.sortie, f"{nom}_380.png"))
        m = mesures(petite)
        for cle, ok, txt in verdicts(m, a.style, a.culture):
            print(f"   {'ok ' if ok else 'HORS'} {cle:<11} {txt}")
        print(f"   planche : {planche(nom, petite, m, refs, a.sortie)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
