#!/usr/bin/env python3
"""
chmf.py - lire les cartes de hauteur compressées « CHMF » de Total War (version 5, Warhammer 1) :
`hf_height_map.data` des tuiles de terrain et `global_meshes\\land_mesh_N.logic_heights` des cartes.

Format relevé le 22.09.2026 (aucune documentation publique ; journal
`05-journal\\2026-09-22-phase-4\\relief-tuiles-wh1.md`), entiers et flottants petit-boutistes :

    0   "CHMF", u32 version (5)
    8   u32 largeur, u32 hauteur          taille utile de la grille
    16  u32 nx, u32 ny                    sous-grilles (1 x 1 le plus souvent)
    24  f32 min, f32 max                  bornes des hauteurs
    32  sous-grille : u32 a, u32 b, u32 0, u32 0, u32 gl, u32 gh (grille découpée en blocs de 16 x 16),
        u32 quantification (0xFFFF0000), u32 n blocs, u32 taille de la charge, u32 0,
        u32 x (n - 1) débuts des blocs 2 à n dans la charge, puis la charge

Un bloc code 16 x 16 valeurs de 16 bits (une par échantillon, ligne par ligne) :
    mode 0            u16 base : toutes les valeurs valent la base
    mode 1 à 127      u16 base, n valeurs u16 absolues (palette triée), puis 256 indices de
                      ceil(log2(n + 1)) bits ; indice 0 = base, indice i = palette[i - 1]
    mode 0x80 + b     u16 base, puis 256 écarts de b + 1 bits : valeur = base + écart
    mode 0x8f         256 valeurs u16 brutes
Hauteur = min + (max - min) x valeur / 65535.

Usage (contrôle) :
    python chmf.py <fichier .data ou .logic_heights>
"""

import math
import struct
import sys

import numpy as np

BLOC = 16


def _bits(octets, n, largeur):
    """n entiers de `largeur` bits, lus à la suite dans `octets`, bit de poids faible d'abord."""
    brut = np.frombuffer(octets, np.uint8)
    bits = np.unpackbits(brut, bitorder="little")[:n * largeur].reshape(n, largeur)
    poids = (1 << np.arange(largeur, dtype=np.uint32))
    return (bits.astype(np.uint32) * poids).sum(1)


def decoder_bloc(blk):
    mode = blk[0]
    if mode == 0x8F:
        return np.frombuffer(blk, "<u2", count=256, offset=1).astype(np.uint32)
    base = struct.unpack_from("<H", blk, 1)[0]
    if mode == 0:
        return np.full(256, base, np.uint32)
    if mode & 0x80:
        largeur = (mode & 0x7F) + 1
        return base + _bits(blk[3:], 256, largeur)
    n = mode
    palette = np.concatenate([[base], np.frombuffer(blk, "<u2", count=n, offset=3).astype(np.uint32)])
    largeur = max(1, math.ceil(math.log2(n + 1)))
    idx = _bits(blk[3 + 2 * n:], 256, largeur)
    return palette[idx]


def lire(octets):
    """Rend (hauteurs float32 de forme (hauteur, largeur) de la première sous-grille, en-tête)."""
    if octets[:4] != b"CHMF":
        raise ValueError("pas un fichier CHMF")
    version, w, h, nx, ny = struct.unpack_from("<5I", octets, 4)
    mn, mx = struct.unpack_from("<ff", octets, 24)
    a, b, _, _, gl, gh, quant, nblocs, taille, _ = struct.unpack_from("<10I", octets, 32)
    offs = [0] + list(struct.unpack_from(f"<{nblocs - 1}I", octets, 72)) + [taille]
    debut = 72 + 4 * (nblocs - 1)
    bl, bh = -(-gl // BLOC), -(-gh // BLOC)
    if bl * bh != nblocs:
        raise ValueError(f"{nblocs} blocs pour une grille {gl} x {gh}")
    grille = np.zeros((bh * BLOC, bl * BLOC), np.uint32)
    for k in range(nblocs):
        v = decoder_bloc(octets[debut + offs[k]:debut + offs[k + 1]])
        by, bx = divmod(k, bl)
        grille[by * BLOC:(by + 1) * BLOC, bx * BLOC:(bx + 1) * BLOC] = v.reshape(BLOC, BLOC)
    grille = grille[:gh, :gl]
    hauteurs = mn + (mx - mn) * grille.astype(np.float64) / 65535.0
    tete = dict(version=version, largeur=w, hauteur=h, nx=nx, ny=ny, min=mn, max=mx, a=a, b=b,
                grille=(gl, gh), quant=quant, blocs=nblocs)
    return hauteurs.astype(np.float32), tete


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for chemin in sys.argv[1:]:
        z, t = lire(open(chemin, "rb").read())
        dx = np.abs(np.diff(z, axis=1)).mean()
        dy = np.abs(np.diff(z, axis=0)).mean()
        print(chemin, t, f"hauteurs [{z.min():.3f}, {z.max():.3f}], écart moyen entre voisins x {dx:.4f} y {dy:.4f}")
