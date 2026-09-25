#!/usr/bin/env python3
"""
contenu_pack.py - lister les fichiers d'un pack (chemin et taille), avec un filtre.

Pourquoi (21.09.2026) : après `build_pack.py`, vérifier qu'un fichier régénéré est bien celui du
pack (la liste d'arbres, par exemple, passait de 24 octets à 1,2 Mo), sans ouvrir RPFM à la main.
Lit l'index du pack directement (format PFH5 de Warhammer 3 : en-tête de 28 octets, index des
packs dépendants, puis une entrée par fichier : taille u32, horodatage u32 si le drapeau 0x40 est
posé, octet de compression, chemin terminé par 0).

Usage :
    python contenu_pack.py [--pack <chemin>] [--filtre <texte>]
"""

import argparse
import os
import struct
import sys

PACK = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\saison_des_revelations.pack"


def index(chemin):
    """[(chemin interne, taille, décalage des données, compressé)] d'un pack PFH4 (Warhammer 1) ou
    PFH5 (Warhammer 3). En-tête : 28 octets, 48 si le drapeau 0x100 (en-tête étendu) est posé ;
    horodatage par fichier si 0x40 ; octet de compression par fichier en PFH5 seulement. Les données
    suivent l'index, dans l'ordre de l'index."""
    with open(chemin, "rb") as f:
        tete = f.read(48)
        version = tete[:4]
        if version not in (b"PFH4", b"PFH5"):
            raise SystemExit(f"{chemin} : format de pack non lu ({version!r})")
        drapeaux, n_packs, taille_packs, n_fichiers, taille_index = struct.unpack_from("<IIIII", tete, 4)
        entete = 48 if drapeaux & 0x100 else 28
        f.seek(0)
        b = f.read(entete + taille_packs + taille_index)
    o = entete + taille_packs
    horodatage = bool(drapeaux & 0x40)
    donnees = entete + taille_packs + taille_index
    out = []
    for _ in range(n_fichiers):
        taille = struct.unpack_from("<I", b, o)[0]
        o += 4 + (4 if horodatage else 0)
        compresse = False
        if version == b"PFH5":
            compresse = bool(b[o])
            o += 1
        fin = b.index(b"\x00", o)
        out.append((b[o:fin].decode("utf-8", "replace"), taille, donnees, compresse))
        donnees += taille
        o = fin + 1
    return out


def entrees(chemin):
    """(chemin interne, taille) de chaque fichier."""
    for c, t, _, _ in index(chemin):
        yield c, t


# Compression des packs de WH3 (22.09.2026) : un fichier compressé commence par sa taille décompressée
# (u32), puis le flux : zstd (magie 28 b5 2f fd, le cas de terrain_camp.pack, terrainb.pack...) ou LZMA1
# (5 octets de propriétés). Python 3.12 n'a pas zstd : on emploie la bibliothèque que RPFM livre.
ZSTD_DLL = r"C:\TotalWar-CampaignMap\01-outils\RPFM\rpfm-v5.0.6-x86_64-pc-windows-msvc\zstd.dll"
_zstd = None


def _zstd_decompresser(flux, taille):
    global _zstd
    import ctypes
    if _zstd is None:
        _zstd = ctypes.CDLL(ZSTD_DLL)
        _zstd.ZSTD_decompress.restype = ctypes.c_size_t
        _zstd.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
        _zstd.ZSTD_isError.restype = ctypes.c_uint
        _zstd.ZSTD_isError.argtypes = [ctypes.c_size_t]
    dst = ctypes.create_string_buffer(taille)
    src = ctypes.create_string_buffer(flux, len(flux))
    n = _zstd.ZSTD_decompress(dst, taille, src, len(flux))
    if _zstd.ZSTD_isError(n):
        raise ValueError(f"zstd : erreur {n}")
    return dst.raw[:n]


def decompresser(octets):
    """Octets d'un fichier compressé d'un pack de WH3 (taille u32 puis flux zstd ou LZMA1)."""
    import lzma
    taille = struct.unpack_from("<I", octets, 0)[0]
    flux = octets[4:]
    if flux[:4] == b"\x28\xb5\x2f\xfd":
        return _zstd_decompresser(flux, taille)
    if flux[:4] == b"\x04\x22\x4d\x18":
        # trame LZ4 (fichiers de terrain_camp, models_other... ; `lire_lz4.py`, session d'audit, 22.09.2026)
        from lire_lz4 import decompresser_trame
        return bytes(decompresser_trame(flux))[:taille]
    return lzma.decompress(flux[:5] + struct.pack("<Q", taille) + flux[5:], format=lzma.FORMAT_ALONE)[:taille]


def extraire(pack, chemin_interne):
    """Octets d'un fichier du pack (décompressé s'il le faut), ou None s'il n'y est pas."""
    cible = chemin_interne.replace("/", "\\").lower()
    for c, taille, off, compresse in index(pack):
        if c.lower() == cible or c.lower().replace("\\", "/") == chemin_interne.lower():
            with open(pack, "rb") as f:
                f.seek(off)
                b = f.read(taille)
            return decompresser(b) if compresse else b
    return None


class SourcePacks:
    """Index de tous les packs d'un dossier `data` : chemin normalisé -> (pack, décalage, taille,
    compressé). Le dernier pack lu (ordre alphabétique) l'emporte. `exclure` : nos propres packs."""

    def __init__(self, dossier_data, exclure=("saison_des_revelations", "zz_startpos_db"), sauf_prefixe="!"):
        self.ou = {}
        for nom in sorted(os.listdir(dossier_data)):
            if not nom.endswith(".pack") or any(e in nom for e in exclure) or nom.startswith(sauf_prefixe):
                continue
            chemin = os.path.join(dossier_data, nom)
            try:
                for c, taille, off, comp in index(chemin):
                    self.ou[c.replace("\\", "/").lower()] = (chemin, off, taille, comp)
            except (SystemExit, struct.error, ValueError):
                continue

    def __contains__(self, chemin):
        return chemin.replace("\\", "/").lower() in self.ou

    def lire(self, chemin):
        p = self.ou.get(chemin.replace("\\", "/").lower())
        if not p:
            return None
        with open(p[0], "rb") as f:
            f.seek(p[1])
            b = f.read(p[2])
        return decompresser(b) if p[3] else b


def chemins_du_jeu(dossier_data, exclure=("saison_des_revelations", "zz_startpos_db")):
    """Ensemble des chemins internes (en minuscules, barres obliques) de tous les packs du jeu."""
    out = set()
    for nom in sorted(os.listdir(dossier_data)):
        if not nom.endswith(".pack") or any(e in nom for e in exclure):
            continue
        try:
            for c, _ in entrees(os.path.join(dossier_data, nom)):
                out.add(c.replace("\\", "/").lower())
        except (SystemExit, struct.error, ValueError) as e:
            print(f"  pack illisible, ignoré : {nom} ({e})")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default=PACK)
    ap.add_argument("--filtre", default="")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    n = 0
    for chemin, taille in entrees(a.pack):
        if a.filtre.lower() in chemin.lower():
            print(f"{taille:12d}  {chemin}")
            n += 1
    print(f"{n} fichier(s) ; pack {os.path.getsize(a.pack)} octets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
