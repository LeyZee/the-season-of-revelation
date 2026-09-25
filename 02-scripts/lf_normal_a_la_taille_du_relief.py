#!/usr/bin/env python3
"""
lf_normal_a_la_taille_du_relief.py - ramener `lf_normal.dds` à la taille du relief compilé, comme CA.

Pourquoi (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\terry-trous.md`) : chez CA, `lf_normal.dds` a
toujours la taille de `full_height_map.dds` (Empires 11 520 × 7 764, prologue 6 400 × 4 804). Le nôtre, repris
de WH1 (`lf_normal_wh1_vers_wh3.py`), fait le double (6 400 × 7 048 pour un relief de 3 200 × 3 524) : c'est la
dernière entorse aux règles de CA relevée dans notre terrain compilé, alors que Terry et le jeu n'affichent le
sol que par parcelles.

Sans réencodage : le DDS (DXT5, 13 niveaux) contient déjà sa version à la bonne taille, son deuxième niveau.
On réécrit le fichier avec ce niveau comme niveau principal (en-tête : largeur, hauteur, pas, nombre de
niveaux), après sauvegarde. À relancer après `lf_normal_wh1_vers_wh3.py`.

Usage :
    python lf_normal_a_la_taille_du_relief.py --carte wh_dlc05_wood_elves_map_1 [--apply]
"""

import argparse
import os
import shutil
import struct
import sys
import time

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
SAUVEGARDES = r"C:\TotalWar-CampaignMap\05-journal\terrain-backups"


def taille_dxt5(w, h):
    return max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 16


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carte", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    dossier = os.path.join(KIT, "working_data", "terrain", "campaigns", a.carte)
    normales = os.path.join(dossier, "lf_normal.dds")
    relief = open(os.path.join(dossier, "full_height_map.dds"), "rb").read(32)
    rh, rw = struct.unpack_from("<II", relief, 12)
    b = open(normales, "rb").read()
    h, w = struct.unpack_from("<II", b, 12)
    mips = struct.unpack_from("<I", b, 28)[0]
    if b[84:88] != b"DXT5":
        sys.exit(f"{normales} : attendu DXT5, trouvé {b[84:88]!r}")
    print(f"relief {rw}x{rh} ; lf_normal {w}x{h}, {mips} niveaux")
    if (w, h) == (rw, rh):
        print("déjà à la taille du relief : rien à faire")
        return 0
    if (w // 2, h // 2) != (rw, rh):
        sys.exit("lf_normal n'est pas au double du relief : cas non prévu")
    premier = taille_dxt5(w, h)
    attendu = sum(taille_dxt5(max(1, w >> k), max(1, h >> k)) for k in range(mips))
    if len(b) - 128 != attendu:
        sys.exit(f"taille des données {len(b) - 128} au lieu de {attendu} : fichier inattendu")
    tete = bytearray(b[:128])
    struct.pack_into("<II", tete, 12, rh, rw)                       # hauteur, largeur
    struct.pack_into("<I", tete, 20, taille_dxt5(rw, rh))          # taille du niveau principal
    struct.pack_into("<I", tete, 28, mips - 1)
    neuf = bytes(tete) + b[128 + premier:]
    print(f"nouveau : {rw}x{rh}, {mips - 1} niveaux, {len(neuf)} octets")
    if not a.apply:
        print("contrôle fait ; relancer avec --apply")
        return 0
    garde = os.path.join(SAUVEGARDES, f"lf_normal-double-{time.strftime('%Y%m%d-%H%M%S')}.dds")
    shutil.copy2(normales, garde)
    with open(normales, "wb") as f:
        f.write(neuf)
    print(f"écrit : {normales} (sauvegarde {garde})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
