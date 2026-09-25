#!/usr/bin/env python3
"""
tuiles_wh1.py - les tuiles de la carte de campagne de Warhammer 1 (`tile_list.bin` v1), lues case par case.

Format (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\relief-tuiles-wh1.md` ; lecture corrigée par l'agent de
recherche des tuiles : l'ancienne lecture « x, y, ..., k, indice, e » depuis l'octet 23070 donnait à chaque pose
l'indice de nom de la pose suivante) :
- u16, u16, u32 n, puis n noms (u16 longueur + texte), `terrain\\tiles\\campaign\\<famille>\\<W>x<H>[_suffixe]\\` ;
- u32 + climats (u16 + texte) ; un en-tête ;
- u32 N puis N enregistrements de 21 octets : u16 k, u32 indice du nom, u8 e, u16 x, u16 y (cases, **y depuis le
  sud**), u8 code de rotation (0x10, 0x20, 0x40, 0x80 : 0x20 et 0x80 échangent largeur et hauteur), u8 climats,
  f32 min et f32 max du sol.
Emprise d'une pose : colonnes [x, x + W), lignes [y, y + H) comptées depuis le sud (vérifié : les tuiles de mer de
WH1 recouvrent notre mer à 99,66 %). Grille : 800 x 881 cases, celle de `tile_map.png` (2 cases par hex).

Usage (module) :
    familles = familles_par_case()     # tableau (881, 800) de noms de famille, ligne 0 = nord
"""

import os
import re
import struct
import sys

import numpy as np

ATELIER = r"C:\TotalWar-CampaignMap"
CARTE = "wh_dlc05_wood_elves_map_1"
FICHIER = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns", CARTE,
                       "tile_list.bin")
LARGEUR, HAUTEUR = 800, 881
TAILLE_ENR = 21


def lire(chemin=FICHIER):
    """(noms, poses) ; pose = (x, y, code, climats, k, indice du nom, e)."""
    b = open(chemin, "rb").read()
    n = struct.unpack_from("<I", b, 12)[0]
    o, noms = 16, []
    for _ in range(n):
        lg = struct.unpack_from("<H", b, o)[0]
        noms.append(b[o + 2:o + 2 + lg].decode("latin-1"))
        o += 2 + lg
    # le compte des poses : le u32 N tel que le reste du fichier fasse exactement N enregistrements
    debut = None
    for p in range(o, len(b) - 4):
        N = struct.unpack_from("<I", b, p)[0]
        if N and len(b) - (p + 4) == TAILLE_ENR * N:
            debut = p + 4
            break
    if debut is None:
        raise SystemExit(f"{chemin} : compte des poses introuvable")
    poses = []
    for i in range((len(b) - debut) // TAILLE_ENR):
        k, idx, e, x, y, code, clim, _, _ = struct.unpack_from("<HIBHHBBff", b, debut + TAILLE_ENR * i)
        poses.append((x, y, code, clim, k, idx, e))
    return noms, poses


def famille(nom):
    return nom.replace("/", "\\").split("\\")[3]


def taille(nom):
    m = re.match(r"(\d+)x(\d+)", nom.replace("/", "\\").split("\\")[4])
    return int(m.group(1)), int(m.group(2))


def familles_par_case(ordre=None):
    """Nom de famille de la tuile qui couvre chaque case (ligne 0 = nord). Quand des poses se recouvrent, la dernière
    de `ordre` (liste de familles, de la moins à la plus prioritaire) l'emporte ; les autres familles passent avant."""
    noms, poses = lire()
    out = np.full((HAUTEUR, LARGEUR), "", object)
    rang = {f: i for i, f in enumerate(ordre or [])}
    for x, y, code, _, _, idx, _ in sorted(poses, key=lambda p: rang.get(famille(noms[p[5]]), -1)):
        W, H = taille(noms[idx])
        if code & 0xF0 in (0x20, 0x80):
            W, H = H, W
        l0, l1 = HAUTEUR - (y + H), HAUTEUR - y
        out[max(0, l0):max(0, l1), x:x + W] = famille(noms[idx])
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    noms, poses = lire()
    f = familles_par_case()
    vals, nb = np.unique(f, return_counts=True)
    print(f"{len(noms)} noms, {len(poses)} poses ; familles par case :",
          sorted(zip(nb.tolist(), vals.tolist()), reverse=True)[:12])
