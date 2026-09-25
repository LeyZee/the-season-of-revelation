#!/usr/bin/env python3
"""
lf_normal_wh1_vers_wh3.py - reprend la normal map basse fréquence de WH1 (`lf_normal.dds`) pour WH3.

Conseil de ChaosRobie (21.09.2026) : reprendre telles quelles la carte de hauteur de WH1 et sa
normal map ; c'est `lf_normal` qui donne au relief son modelé en jeu (les hauteurs, quantifiées,
sont bosselées), « this is literally how it works in WH3 ». Pour une campagne, BOB ne produit pas
ce fichier (l'action des normales n'existe que pour les batailles).

Vérifié le 21.09.2026 (journal de phase 3, § 8) par corrélation entre les canaux de la normal map
et les pentes de la carte de hauteur, dans WH1 et dans les Empires Immortels :
- même rangement des lignes que la carte de hauteur dans les deux jeux (retournée : corrélation nulle) ;
- DXT5 « dxt5n » dans les deux : X dans l'alpha, Y dans le vert ;
- X de même signe (−0,71 / −0,71), **Y de signe opposé** (+0,70 dans WH1, −0,74 dans WH3).
Conversion : inverser le vert, **directement dans les blocs compressés** (vert sur 6 bits des deux
couleurs extrêmes de chaque bloc BC1 : g -> 63 − g), ce qui est exact et sans perte parce qu'un bloc
DXT5 interpole toujours en mode 4 couleurs. Taille, sens et mipmaps de WH1 sont conservés.

Usage :
    python lf_normal_wh1_vers_wh3.py            # contrôle seul (corrélations avant/après)
    python lf_normal_wh1_vers_wh3.py --apply    # écrit dans working_data\\terrain\\campaigns\\<carte>\\
"""

import argparse
import os
import shutil
import struct
import sys
import time

import numpy as np

ATELIER = r"C:\TotalWar-CampaignMap"
CARTE = "wh_dlc05_wood_elves_map_1"
SOURCE = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns",
                      CARTE, "lf_normal.dds")
HAUTEUR_WH1 = os.path.join(os.path.dirname(SOURCE), "lf_height_map.dds")
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
CIBLE = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE, "lf_normal.dds")
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "terrain-backups")


def entete(b):
    if b[:4] != b"DDS " or b[84:88] != b"DXT5":
        sys.exit("lf_normal de WH1 : DXT5 attendu")
    h, l = struct.unpack_from("<II", b, 12)
    mips = max(1, struct.unpack_from("<I", b, 28)[0])
    return l, h, mips


def inverse_vert(b):
    """Renvoie une copie où le vert de chaque bloc DXT5 est inversé, pour toutes les mipmaps."""
    l, h, mips = entete(b)
    sortie = bytearray(b)
    o = 128
    for _ in range(mips):
        blocs = max(1, (l + 3) // 4) * max(1, (h + 3) // 4)
        v = np.frombuffer(sortie, dtype="<u2", count=blocs * 8, offset=o).reshape(blocs, 8).copy()
        for k in (4, 5):                              # couleurs extrêmes aux octets 8-9 et 10-11
            c = v[:, k].astype(np.uint32)
            g = (c >> 5) & 0x3F
            v[:, k] = ((c & ~np.uint32(0x3F << 5)) | ((63 - g) << 5)).astype(np.uint16)
        sortie[o:o + blocs * 16] = v.tobytes()
        o += blocs * 16
        l, h = max(1, l // 2), max(1, h // 2)
    if o != len(b):
        sys.exit(f"taille inattendue : {o} octets lus pour {len(b)}")
    return bytes(sortie)


def controle(donnees):
    """Corrélation du vert (Y) avec la pente vers le bas des lignes, sur la carte de hauteur de WH1."""
    from io import BytesIO
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(BytesIO(donnees))
    im.load()
    a = np.asarray(im)[::2, ::2]
    nx = a[..., 3].astype(np.float32) - 127.5
    ny = a[..., 1].astype(np.float32) - 127.5
    hb = open(HAUTEUR_WH1, "rb").read()
    hh = np.frombuffer(hb[128:128 + 3200 * 3524 * 2], dtype="<u2").reshape(3524, 3200).astype(np.float32)
    dy, dx = np.gradient(hh)
    c = lambda u, w: float(((u - u.mean()) * (w - w.mean())).sum() / np.sqrt(((u - u.mean()) ** 2).sum() * ((w - w.mean()) ** 2).sum()))
    return c(nx, dx), c(ny, dy)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    b = open(SOURCE, "rb").read()
    l, h, mips = entete(b)
    neuf = inverse_vert(b)
    x0, y0 = controle(b)
    x1, y1 = controle(neuf)
    print(f"lf_normal de WH1 : {l} x {h}, DXT5, {mips} mipmaps")
    print(f"  avant : corr(X, dh/dx) {x0:+.3f}   corr(Y, dh/dlignes) {y0:+.3f}   (WH1)")
    print(f"  après : corr(X, dh/dx) {x1:+.3f}   corr(Y, dh/dlignes) {y1:+.3f}   (WH3 attend −0,71 / −0,74)")
    if not (x1 < -0.5 and y1 < -0.5):
        sys.exit("contrôle raté : rien n'est écrit")
    if not a.apply:
        print("contrôle bon ; relancer avec --apply pour écrire", CIBLE)
        return
    if os.path.exists(CIBLE):
        dest = os.path.join(SAUVEGARDES, f"lf_normal-avant-{time.strftime('%Y%m%d-%H%M%S')}.dds")
        os.makedirs(SAUVEGARDES, exist_ok=True)
        shutil.copy2(CIBLE, dest)
        print("  ancien fichier sauvegardé :", dest)
    with open(CIBLE, "wb") as f:
        f.write(neuf)
    print("  écrit :", CIBLE, len(neuf), "octets")


if __name__ == "__main__":
    main()
