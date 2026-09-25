#!/usr/bin/env python3
"""
camera_heightmap.py - fabrique `campaign_maps\\<carte>\\camera_heightmap.png` (hauteur de la caméra).

Toutes les cartes de CA et celle d'Old World livrent ce fichier. BOB le calcule par l'action
« Generate Camera Height Map », qui plante chez nous : DirectX lui refuse une surface d'affichage
(E_ACCESSDENIED en mode flip, repli en mode classique) puis `warscape` appelle un pointeur nul
(journal de phase 3, § 7.7). On le fabrique donc à partir de la couche de hauteur du projet Terry.

Format relevé sur trois cartes (prologue, Empires Immortels, Old World) :
- PNG en niveaux de gris 16 bits ; texte PNG `height_scale` (6 décimales) ; hauteur = valeur × échelle ;
  la valeur maximale est toujours 65535 (normalisé sur le point le plus haut) ;
- taille = `tile_map` / 4 (Empires 2880 × 1941 -> 720 × 486 ; Old World 4096 × 3549 -> 1024 × 887) ;
- même rangement des lignes que les rasters de Terry (nord en haut) ;
- contenu (vérifié sur les Empires contre leur `height.tif`) : sur terre et sur les côtes, le **maximum
  des hauteurs du bloc** (16 × 16 px de la couche de hauteur) à 0,01 près en médiane ; en mer (maximum
  du bloc <= 0), une valeur constante de **1,03**. Aucun flou. 10 % des blocs de terre sont plus hauts
  chez CA (au-delà de +2), sans doute les objets et les falaises, qu'on ne reproduit pas.

Usage :
    python camera_heightmap.py            # calcule et contrôle, n'écrit rien
    python camera_heightmap.py --apply    # écrit dans working_data\\campaign_maps\\<carte>\\
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

Image.MAX_IMAGE_PIXELS = None
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
PROJET = os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE)
CIBLE = os.path.join(KIT, "working_data", "campaign_maps", CARTE, "camera_heightmap.png")
MER = 1.03          # valeur relevée en mer sur les Empires (médiane 1,030, p10 1,030)
BLOC = 16           # couche de hauteur à 8 px par hex, tile_map à 2 px par hex, caméra à tile_map / 4


def couche_hauteur():
    """Le fichier de la couche Height déclarée dans le .terry (et non une copie traînant à côté)."""
    t = open(os.path.join(PROJET, f"{CARTE}.terry"), encoding="utf-8").read()
    m = re.search(r'type="Height" size="(\d+)x(\d+)"[^>]*/>\s*<pc type="QTU::TerrainMapLayer">\s*<data id="([0-9a-f]+)"', t)
    if not m:
        sys.exit("couche Height introuvable dans le .terry")
    chemin = os.path.join(PROJET, f"{CARTE}.height.{m.group(3)}.tif")
    if not os.path.exists(chemin):
        sys.exit(f"fichier de la couche absent : {chemin}")
    return chemin, int(m.group(1)), int(m.group(2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    chemin, l, h = couche_hauteur()
    hauteurs = np.asarray(Image.open(chemin), dtype=np.float32)
    if hauteurs.shape != (h, l):
        sys.exit(f"taille inattendue {hauteurs.shape} pour {l} x {h}")
    tuiles = Image.open(os.path.join(PROJET, "tile_map.png")).size
    L, H = -(-tuiles[0] // 4), -(-tuiles[1] // 4)            # arrondi supérieur, comme les Empires
    pad = np.full((H * BLOC, L * BLOC), -1e9, dtype=np.float32)
    pad[: min(h, H * BLOC), : min(l, L * BLOC)] = hauteurs[: H * BLOC, : L * BLOC]
    bmax = pad.reshape(H, BLOC, L, BLOC).max(axis=(1, 3))
    camera = np.where(bmax > 0, bmax, MER).astype(np.float64)
    echelle = camera.max() / 65535.0
    valeurs = np.clip(np.round(camera / echelle), 0, 65535).astype(np.uint16)
    print(f"couche {os.path.basename(chemin)} ({l} x {h}) ; tile_map {tuiles[0]} x {tuiles[1]} -> caméra {L} x {H}")
    print(f"hauteur max {camera.max():.3f} ; height_scale {echelle:.6f} ; mer {100 * (bmax <= 0).mean():.1f} % des pixels")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply pour écrire", CIBLE)
        return
    info = PngInfo()
    info.add_text("height_scale", f"{echelle:.6f}")
    Image.fromarray(valeurs).save(CIBLE, pnginfo=info)       # uint16 -> PNG 16 bits (mode I;16)
    r = Image.open(CIBLE)
    print("écrit :", CIBLE, r.size, r.mode, "height_scale =", r.info.get("height_scale"),
          "max", int(np.asarray(r).max()))


if __name__ == "__main__":
    main()
