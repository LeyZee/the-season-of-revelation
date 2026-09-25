#!/usr/bin/env python3
"""
lire_lz4.py - décompresser un flux LZ4 (format « frame », magie 04 22 4d 18) sans bibliothèque extérieure.

Pourquoi (22.09.2026) : certains fichiers des packs de WH3 (ex. `campaign_skybox.wsmodel` du prologue, dans
models_other.pack) sont compressés en LZ4 ; `contenu_pack.decompresser` ne gère que zstd et LZMA, et Python n'a ni
`lz4` ni `zstandard` ici.

Usage (module) :
    from lire_lz4 import decompresser_trame
    octets = decompresser_trame(flux)            # flux = octets après la taille u32 du pack
"""

import struct


def decompresser_bloc(src, dst=None):
    """Un bloc LZ4 brut ; `dst` : bytearray de sortie (les renvois peuvent viser les blocs précédents)."""
    out = dst if dst is not None else bytearray()
    i, n = 0, len(src)
    while i < n:
        jeton = src[i]
        i += 1
        lit = jeton >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        out += src[i:i + lit]
        i += lit
        if i >= n:                                  # dernière séquence : littéraux seuls
            break
        dec = src[i] | (src[i + 1] << 8)
        i += 2
        lg = jeton & 15
        if lg == 15:
            while True:
                b = src[i]
                i += 1
                lg += b
                if b != 255:
                    break
        lg += 4
        debut = len(out) - dec
        if dec >= lg:
            out += out[debut:debut + lg]
        else:                                       # recouvrement : copie octet par octet
            for k in range(lg):
                out.append(out[debut + k])
    return out


def decompresser_trame(flux):
    """Une trame LZ4 complète (magie, descripteur, blocs, marque de fin)."""
    if flux[:4] != b"\x04\x22\x4d\x18":
        raise ValueError("pas une trame LZ4")
    flg = flux[4]
    o = 6 + (8 if flg & 0x08 else 0) + (4 if flg & 0x01 else 0) + 1      # FLG, BD, [taille], [dico], HC
    somme_bloc = bool(flg & 0x10)
    out = bytearray()
    while True:
        taille = struct.unpack_from("<I", flux, o)[0]
        o += 4
        if taille == 0:
            break
        brut = bool(taille & 0x80000000)
        taille &= 0x7FFFFFFF
        bloc = flux[o:o + taille]
        o += taille + (4 if somme_bloc else 0)
        if brut:
            out += bloc
        else:
            decompresser_bloc(bloc, out)
    return bytes(out)
