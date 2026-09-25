#!/usr/bin/env python3
"""
vue_de_loin.py - la carte superposée que WH3 affiche quand on dézoome (carte peinte et carte des régions), pour
notre carte, à partir du parchemin de WH1.

Pourquoi (23.09.2026 ; Charles : « lorsqu'on zoome et dézoome sur la carte, je veux que ça rende exactement comme
Warhammer 3 ») : en dézoomant, WH3 remplace la carte 3D par une carte peinte superposée, déclarée dans
`campaign_map_playable_areas` (`campaign_overlay_map`, `campaign_overlay_lookup`, `campaign_overlay_map_text`) et
rangée dans `campaign_maps/<carte>/`. Les trois nous manquaient (build_pack : « texture absente, signalée
seulement »).

Relevé chez CA (23.09.2026) :
- carte peinte : un parchemin (Empires : `wh3_main_combi_map.dds` DXT5 5760 x 4480, 13 mips ; prologue : BC7 UNORM
  2816 x 2212, 12 mips), lignes NORD EN HAUT (mip 6 des Empires face à leur minicarte : corrélation 0,75 tel quel,
  -0,15 retourné) ; son rapport largeur / hauteur est celui de la zone jouable ;
- carte des régions : `*_lookup.dds` en R16_UNORM (format 56), 1 mip, EXACTEMENT les octets de pixels du
  `*_lookup.tga` à palette 16 bits (même ordre de lignes, vérifié sur les Empires et le prologue) ;
- calque de textes : le prologue le déclare sans le livrer ; notre parchemin porte déjà les noms : pas de calque.

La carte peinte est le parchemin de WH1 (celui de la carte stratégique : français pour le pack principal, anglais
pour le pack _en), en BC7 UNORM avec tous ses mips, comme le prologue.

Sorties (à l'arborescence du pack) :
    04-projets\\saison-des-revelations\\affichage-carte\\campaign_maps\\<carte>\\wh_dlc05_wood_elves.dds  (+ _lookup.dds)
    04-projets\\saison-des-revelations\\affichage-carte-en\\campaign_maps\\<carte>\\wh_dlc05_wood_elves.dds

Usage :
    python vue_de_loin.py [--apply]
"""

import argparse
import os
import struct
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc7                                                           # noqa: E402

Image.MAX_IMAGE_PIXELS = None
ATELIER = r"C:\TotalWar-CampaignMap"
CARTE = "wh_dlc05_wood_elves_map_1"
PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
FR = os.path.join(PROJET, "affichage-carte", "campaign_maps", CARTE, "wh_dlc05_wood_elves_map.png")
EN = os.path.join(PROJET, "affichage-carte-en", "campaign_maps", CARTE, "wh_dlc05_wood_elves_map.png")
LOOKUP_TGA = os.path.join(PROJET, "images-carte", "wh_dlc05_wood_elves_lookup.tga")
SORTIE_FR = os.path.join(PROJET, "affichage-carte", "campaign_maps", CARTE)
SORTIE_EN = os.path.join(PROJET, "affichage-carte-en", "campaign_maps", CARTE)


def multiple_de_4(rgba):
    """23.09.2026, 03 h 15 (Charles : au dézoom maximal, une carte grise au lieu du parchemin) : le parchemin de WH1 fait
    2500 x 3175, et 3175 n'est pas un multiple de 4. Direct3D refuse une texture compressée par blocs (BC7) dont le
    niveau 0 n'a pas des côtés multiples de 4 ; toutes celles de CA en ont (Empires 5760 x 4480, Chaos 4432 x 3336,
    prologue 2816 x 2212). On complète le bord sud par répétition (1 ligne : 0,03 % de la hauteur)."""
    h, w = rgba.shape[:2]
    return np.pad(rgba, ((0, (-h) % 4), (0, (-w) % 4), (0, 0)), mode="edge")


# Calque des noms (`campaign_overlay_map_text`) : les Empires et le Chaos en ont un (BC7, dans local_xx.pack), le
# prologue le déclare sans le livrer. Nos noms sont peints dans le parchemin : un calque TRANSPARENT, au rapport de la
# zone jouable, pour que la vue de loin ne manque d'aucun fichier déclaré.
CALQUE_TEXTE = (624, 792)


def niveaux_mips(rgba):
    """Tous les niveaux jusqu'à 1 x 1 (côtés divisés par 2, arrondis vers le bas), filtre boîte."""
    out = [rgba]
    while out[-1].shape[0] > 1 or out[-1].shape[1] > 1:
        h, w = out[-1].shape[:2]
        out.append(np.array(Image.fromarray(out[-1], "RGBA").resize((max(1, w // 2), max(1, h // 2)), Image.BOX)))
    return out


def _completer4(img):
    """Complète à un multiple de 4 par répétition des bords (blocs de 4 x 4)."""
    h, w = img.shape[:2]
    return np.pad(img, ((0, (-h) % 4), (0, (-w) % 4), (0, 0)), mode="edge")


def dds_bc7_mips(niveaux):
    """DDS BC7 UNORM (format 98, comme le prologue) avec des niveaux de côtés quelconques."""
    h, w = niveaux[0].shape[:2]
    tete = bytearray(128)
    tete[0:4] = b"DDS "
    struct.pack_into("<7I", tete, 4, 124, 0xA1007, h, w, ((w + 3) // 4) * ((h + 3) // 4) * 16, 1, len(niveaux))
    struct.pack_into("<II", tete, 76, 32, 0x4)
    tete[84:88] = b"DX10"
    struct.pack_into("<I", tete, 108, 0x401008)
    dx10 = struct.pack("<5I", 98, 3, 0, 1, 0)
    return bytes(tete) + dx10 + b"".join(bc7.encoder(_completer4(n)) for n in niveaux)


def lire_tga16(chemin):
    """(largeur, hauteur, octets des pixels) d'un TGA à palette 16 bits (type 1), tel que CA les écrit."""
    b = open(chemin, "rb").read()
    idlen, cmtype, itype = b[0], b[1], b[2]
    _, cmlen, cmbits = struct.unpack_from("<HHB", b, 3)
    w, h, bpp, _ = struct.unpack_from("<HHBB", b, 12)
    if itype != 1 or bpp != 16:
        raise SystemExit(f"{chemin} : TGA de type {itype}, {bpp} bits ; attendu type 1, 16 bits")
    off = 18 + idlen + cmlen * ((cmbits + 7) // 8)
    return w, h, b[off:off + w * h * 2]


def dds_r16(w, h, pixels):
    """DDS R16_UNORM (format 56), 1 mip, en-tête DX10 comme les lookups de CA."""
    tete = bytearray(128)
    tete[0:4] = b"DDS "
    struct.pack_into("<7I", tete, 4, 124, 0x2100F, h, w, w * 2, 1, 1)          # champs du lookup du prologue
    struct.pack_into("<II", tete, 76, 32, 0x4)
    tete[84:88] = b"DX10"
    struct.pack_into("<I", tete, 108, 0x1000)
    return bytes(tete) + struct.pack("<5I", 56, 3, 0, 1, 0) + pixels


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    w, h, px = lire_tga16(LOOKUP_TGA)
    lookup = dds_r16(w, h, px)
    print(f"lookup : {w} x {h}, {len(np.unique(np.frombuffer(px, '<u2')))} valeurs ; DDS {len(lookup)} octets")
    sorties = {os.path.join(SORTIE_FR, "wh_dlc05_wood_elves_lookup.dds"): lookup}
    w_t, h_t = CALQUE_TEXTE
    calque = dds_bc7_mips(niveaux_mips(np.zeros((h_t, w_t, 4), np.uint8)))
    print(f"calque des noms : transparent, {w_t} x {h_t}, BC7 {len(calque)} octets")
    sorties[os.path.join(SORTIE_FR, "wh_dlc05_wood_elves_text.dds")] = calque
    for src, dossier in ((FR, SORTIE_FR), (EN, SORTIE_EN)):
        t0 = time.time()
        img = multiple_de_4(np.array(Image.open(src).convert("RGBA")))
        assert img.shape[0] % 4 == 0 and img.shape[1] % 4 == 0
        niveaux = niveaux_mips(img)
        d = dds_bc7_mips(niveaux)
        print(f"{os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(src))))} : parchemin "
              f"{img.shape[1]} x {img.shape[0]}, {len(niveaux)} niveaux, BC7 {len(d)} octets ({time.time() - t0:.0f} s)")
        sorties[os.path.join(dossier, "wh_dlc05_wood_elves.dds")] = d
    for p, d in sorties.items():
        print(f"{'écrit' if a.apply else 'à écrire'} : {p}")
        if a.apply:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
