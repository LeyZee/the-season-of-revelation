#!/usr/bin/env python3
"""
preparer_minicarte.py - fabriquer la minicarte (parchemin) et les deux images de correspondance
des regions, au format exact de CA, pour l'ecran « Nouvelle campagne » et la carte de campagne.

Pourquoi (21.09.2026, journal `phase-2-startpos-temoin.md` § 21). En jeu, l'onglet « Carte » de
l'ecran de selection affichait une image de regions brute (fond vert, regions en rouges) au lieu
d'un parchemin. Cause : notre `radar_file` pointait vers une image de correspondance de Warhammer 1,
et nos deux images de correspondance (`overlay_file`, `minimap_lookup_file`) etaient celles de
Warhammer 1 — 500 x 464, 254 couleurs, dans un codage qui n'est pas celui de Warhammer 3 et sur une
geometrie qui n'est pas celle de notre carte.

Le modele, releve chez CA (`wh3_main_chaos_map_4`) :
- `radar_file`          : parchemin RGBA, moitie de la resolution de l'image de correspondance ;
- `overlay_file`        : image de correspondance, **TGA a palette, 16 bits par pixel**, palette
                          BGRA 32 bits, origine en bas, une couleur par region (celle de `regions`) ;
- `minimap_lookup_file` : la meme au quart de la resolution.
Les trois couvrent exactement l'etendue du monde de la carte.

Ce que fait le script :
1. l'image de correspondance vient de **CAIME**, calculee depuis notre `map.hex`
   (`working_data\\...\\<campagne>_lookup.bmp`) : geometrie exacte, 61 couleurs = les 61 couleurs
   de nos regions (verifie) ;
2. le parchemin est **celui de Warhammer 1** pour cette campagne (aucun asset neuf), recale sur la
   geometrie de la carte : une transformation affine est ajustee par moindres carres entre le
   centre de chaque province dans l'image de correspondance et la position de son nom sur le
   parchemin (26 reperes) ;
3. il ecrit les trois fichiers et une image de controle ou les frontieres des regions sont
   dessinees sur le parchemin recale.

Usage :
    python preparer_minicarte.py [--sortie <dossier>]
"""

import argparse
import io
import os
import re
import shutil
import sys
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ATELIER = r"C:\TotalWar-CampaignMap"
AKIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
CAMPAGNE, CARTE = "wh_dlc05_wood_elves", "wh_dlc05_wood_elves_map_1"
# parchemin de WH1 : le FRANÇAIS (local_fr de WH1, dossier `affichage-carte` de la session d'audit) pour le pack principal ;
# l'anglais (kit de WH1) pour le pack `_en` (23.09.2026, audit de l'interface E1 : noms anglais dans le jeu français)
PARCHEMIN = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "affichage-carte", "campaign_maps", CARTE,
                         f"{CAMPAGNE}_map.png")
PARCHEMIN_EN = os.path.join(ATELIER, "03-references", "saison-des-revelations", CARTE, f"{CAMPAGNE}_map.png")
SORTIE_EN = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "images-carte-en", "campaign_maps", CARTE)
LOOKUP_BMP = os.path.join(AKIT, "working_data", "campaign_maps", CARTE, f"{CAMPAGNE}_lookup.bmp")
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "images-carte")
# Chaque carte de CA a un `prebattle_map.png` (image a palette) dans son dossier ; celui de
# Warhammer 1 pour cette carte, repris tel quel (21.09.2026, journal § 22).
PREBATTLE = os.path.join(ATELIER, "03-references", "saison-des-revelations", CARTE, "prebattle_map.png")

SIGMA_CONTOURS = 3.0          # px de l'image de correspondance (1600 x 2032) ; 0 = contours en marches d'hexagone

# Position du nom de chaque province sur le parchemin, relevee sur un apercu de 700 x 889 pixels
# (parchemin natif 2500 x 3175). Les noms sont poses par l'illustrateur a peu pres au centre de
# chaque province : l'ajustement par moindres carres absorbe l'imprecision.
APERCU = (700, 889)
REPERES = {
    "wh_dlc05_gisoreux": (245, 112), "wh_dlc05_mousillon": (65, 232),
    "wh_dlc05_bastonne": (182, 262), "wh_dlc05_montfort": (282, 268),
    "wh_dlc05_grey_mountains": (375, 212), "wh_dlc05_grey_mountains_2": (562, 267),
    "wh_dlc05_massif_orcal": (234, 358), "wh_dlc05_bordeleaux": (85, 345),
    "wh_dlc05_parravon": (395, 338), "wh_dlc05_aquitaine": (145, 424),
    "wh_dlc05_tirsyth": (408, 440), "wh_dlc05_argwylon": (470, 435),
    "wh_dlc05_arranoc": (540, 455), "wh_dlc05_brionne": (90, 500),
    "wh_dlc05_fyr_darric": (443, 525), "wh_dlc05_quenelles": (220, 553),
    "wh_dlc05_anmyr": (352, 553), "wh_dlc05_wydrioth": (530, 578),
    "wh_dlc05_torgovann": (412, 605), "wh_dlc05_carcassonne": (177, 653),
    "wh_dlc05_oak_of_ages": (470, 663), "wh_dlc05_modryn": (345, 703),
    "wh_dlc05_talsyn": (468, 703), "wh_dlc05_cythral": (548, 757),
    "wh_dlc05_cavaroc": (345, 797), "wh_dlc05_atylwyth": (447, 790),
}


def couleurs_regions():
    t = io.open(os.path.join(AKIT, "raw_data", "db", "regions.xml"), encoding="utf-8").read()
    out = {}
    for b in re.findall(r"<regions\s[^>]*>(.*?)</regions>", t, re.S):
        k = re.search(r"<key>(.*?)</key>", b).group(1)
        if k.startswith("wh_dlc05_"):
            out[k] = tuple(int(re.search(rf"<{c}>(\d+)</{c}>", b).group(1)) for c in "rgb")
    return out


def provinces():
    t = io.open(os.path.join(AKIT, "raw_data", "db", "region_to_province_junctions.xml"),
                encoding="utf-8").read()
    out = defaultdict(list)
    for b in re.findall(r"<region_to_province_junctions\s[^>]*>(.*?)</region_to_province_junctions>",
                        t, re.S):
        r = re.search(r"<region>(.*?)</region>", b).group(1)
        if r.startswith("wh_dlc05_"):
            out[re.search(r"<province>(.*?)</province>", b).group(1)].append(r)
    return out


def ecrit_tga_palette(chemin, indices, palette):
    """TGA type 1 (a palette, non compresse), indices sur 16 bits, palette BGRA 32 bits, origine
    en bas — exactement le format des images de correspondance de CA."""
    h, w = indices.shape
    entete = bytearray(18)
    entete[1] = 1                                    # palette presente
    entete[2] = 1                                    # image a palette, non compressee
    entete[5:7] = len(palette).to_bytes(2, "little")
    entete[7] = 32                                   # 32 bits par entree de palette
    entete[12:14] = w.to_bytes(2, "little")
    entete[14:16] = h.to_bytes(2, "little")
    entete[16] = 16                                  # 16 bits par pixel
    # 25.09.2026 (audit des calques, session du rendu) : CA ecrit ses lookups LIGNE 0 = NORD avec l'octet 17 a 0x10
    # (Empires, Chaos : correlation avec la carte peinte 0,31 telle quelle, -0,02 retournee) ; le jeu lit les lignes
    # dans l'ordre du fichier, sans tenir compte de l'origine TGA. Nos lookups etaient ecrits du sud au nord (0,05
    # contre 0,21 retournes) : territoires, frontieres au dezoom et minicarte a l'envers. Meme ordre et meme octet que CA.
    entete[17] = 0x10                                # comme CA (lignes du nord au sud dans le fichier)
    pal = bytearray()
    for r, g, b, a in palette:
        pal += bytes((b, g, r, a))
    donnees = indices.astype("<u2").tobytes()        # lignes du nord au sud, comme CA
    with open(chemin, "wb") as f:
        f.write(bytes(entete) + bytes(pal) + donnees)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sortie", default=SORTIE)
    # 23.09.2026 (audit de l'interface, E1) : le parchemin anglais du kit de WH1 portait les noms anglais dans le jeu
    # français ; la minicarte se fait depuis le parchemin FRANÇAIS de WH1 (`affichage-carte`), et l'anglaise, au même
    # chemin, va dans le pack `_en` (`--minicarte-seule --sortie ...images-carte-en\campaign_maps\<carte>`)
    ap.add_argument("--parchemin", default=PARCHEMIN)
    ap.add_argument("--minicarte-seule", action="store_true",
                    help="n'écrire que la minicarte (pas les images de correspondance ni le contrôle)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(a.sortie, exist_ok=True)

    lk = np.asarray(Image.open(LOOKUP_BMP).convert("RGB")).astype(np.int64)
    H, W = lk.shape[:2]
    cle = lk[:, :, 0] * 65536 + lk[:, :, 1] * 256 + lk[:, :, 2]
    coul = couleurs_regions()
    region_de = {r * 65536 + g * 256 + b: k for k, (r, g, b) in coul.items()}
    manque = [c for c in np.unique(cle) if int(c) not in region_de]
    print(f"image de correspondance CAIME : {W} x {H}, {len(np.unique(cle))} couleurs, "
          f"{len(manque)} inconnue(s) de `regions`")
    if manque:
        return 2

    # 1. centre de chaque province dans l'image de correspondance
    prov = provinces()
    ys, xs = np.mgrid[0:H, 0:W]
    src, dst, noms = [], [], []
    for p, (px, py) in REPERES.items():
        masque = np.zeros((H, W), bool)
        for r in prov[p]:
            rr, gg, bb = coul[r]
            masque |= cle == rr * 65536 + gg * 256 + bb
        if not masque.any():
            print(f"  !! {p} absent de l'image")
            continue
        src.append((xs[masque].mean(), ys[masque].mean()))
        dst.append((px, py))
        noms.append(p)
    src = np.array(src)
    par = Image.open(a.parchemin).convert("RGB")
    PW, PH = par.size
    dst = np.array(dst, dtype=float) * (PW / APERCU[0], PH / APERCU[1])

    # 2. affine lookup -> parchemin par moindres carres : [x', y'] = [x, y, 1] @ M
    A = np.hstack([src, np.ones((len(src), 1))])
    M, *_ = np.linalg.lstsq(A, dst, rcond=None)
    residus = np.linalg.norm(A @ M - dst, axis=1)
    print(f"ajustement sur {len(src)} reperes : echelle x {M[0,0]:.3f}, y {M[1,1]:.3f}, "
          f"cisaillement {M[1,0]:.3f}/{M[0,1]:.3f}, decalage ({M[2,0]:.0f}, {M[2,1]:.0f}) px")
    print(f"  residu moyen {residus.mean():.0f} px, maximal {residus.max():.0f} px "
          f"(parchemin natif {PW} x {PH})")
    for n, r in sorted(zip(noms, residus), key=lambda t: -t[1])[:4]:
        print(f"     plus grand ecart : {n:30} {r:.0f} px")

    # 3. la minicarte : moitie de la resolution de l'image de correspondance (rapport de CA)
    # (25.09.2026, 19 h ; Charles : « garder exactement la même teinte ») : le parchemin (2500 x 3175) était échantillonné
    # en bilinéaire à ~1/3 de sa résolution, d'où un trait brouillé ; il est maintenant rendu à 3 fois la minicarte puis
    # réduit par moyenne de zone. Aucun réglage de couleur : la teinte est celle d'avant.
    RW, RH = W // 2, H // 2
    F = 3
    s = W / (RW * F)
    aff = np.array([[M[0, 0] * s, M[1, 0] * s, (M[0, 0] + M[1, 0]) * 0.5 * s + M[2, 0]],
                    [M[0, 1] * s, M[1, 1] * s, (M[0, 1] + M[1, 1]) * 0.5 * s + M[2, 1]]], np.float64)
    grand = cv2.warpAffine(np.asarray(par), aff, (RW * F, RH * F), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_REPLICATE)
    val = cv2.resize(grand, (RW, RH), interpolation=cv2.INTER_AREA)
    radar = np.dstack([val.clip(0, 255).astype(np.uint8), np.full((RH, RW), 255, np.uint8)])
    chemin_radar = os.path.join(a.sortie, f"{CAMPAGNE}_minimap.png")
    Image.fromarray(radar, "RGBA").save(chemin_radar)
    print(f"minicarte : {chemin_radar} ({RW} x {RH}), depuis {a.parchemin}")
    if a.minicarte_seule:
        return 0

    # 4. les deux images de correspondance, au format de CA
    palette_cles = sorted(np.unique(cle).tolist())
    index_de = {c: i for i, c in enumerate(palette_cles)}
    palette = [((c >> 16) & 255, (c >> 8) & 255, c & 255, 255) for c in palette_cles]
    table = np.vectorize(index_de.get)
    idx = table(cle).astype(np.uint16)
    # CONTOURS LISSÉS (25.09.2026, 19 h ; Charles : « mieux détourer la province », aperçu validé) : l'image de CAIME suit
    # les marches des hexagones ; chaque pixel prend la région la plus présente autour de lui (masques flous, écart-type
    # SIGMA_CONTOURS px, argmax). Contrôles : toutes les régions gardent des pixels, aucune ne varie de plus de 2 %.
    if SIGMA_CONTOURS:
        meilleur = np.full(idx.shape, -1.0, np.float32)
        lisse = np.zeros(idx.shape, np.uint16)
        for i in range(len(palette)):
            m = cv2.GaussianBlur((idx == i).astype(np.float32), (0, 0), SIGMA_CONTOURS)
            plus = m > meilleur
            meilleur[plus] = m[plus]
            lisse[plus] = i
        n_av = np.bincount(idx.ravel(), minlength=len(palette))
        n_ap = np.bincount(lisse.ravel(), minlength=len(palette))
        ecart = float(np.max(np.abs(n_ap.astype(float) - n_av) / np.maximum(n_av, 1)))
        print(f"contours lissés : {100 * (lisse != idx).mean():.2f} % des pixels ; plus grand écart de surface "
              f"{100 * ecart:.2f} % ; régions sans pixel : {int((n_ap == 0).sum())}")
        if (n_ap == 0).any() or ecart > 0.02:
            print("  !! contrôle des contours lissés en échec : images de correspondance NON écrites")
            return 3
        idx = lisse
    ecrit_tga_palette(os.path.join(a.sortie, f"{CAMPAGNE}_lookup.tga"), idx, palette)
    petit = idx[::4, ::4]
    ecrit_tga_palette(os.path.join(a.sortie, f"{CAMPAGNE}_lookup_minimap.tga"), petit, palette)
    print(f"correspondance : {W} x {H} et {petit.shape[1]} x {petit.shape[0]}, "
          f"palette {len(palette)} couleurs, 16 bits par pixel")

    # 5. controle : frontieres des regions sur la minicarte
    lr = cle[::2, ::2][:RH, :RW]
    bord = np.zeros((RH, RW), bool)
    bord[:, 1:] |= lr[:, 1:] != lr[:, :-1]
    bord[1:, :] |= lr[1:, :] != lr[:-1, :]
    ctrl = radar[:, :, :3].copy()
    ctrl[bord] = (0, 160, 255)
    chemin_ctrl = os.path.join(a.sortie, "controle_superposition.png")
    Image.fromarray(ctrl).save(chemin_ctrl)
    print(f"controle : {chemin_ctrl}")

    # 6. l'image d'avant-bataille de Warhammer 1, que CA range a cote de la minicarte
    if os.path.exists(PREBATTLE):
        shutil.copy2(PREBATTLE, os.path.join(a.sortie, "prebattle_map.png"))
        print(f"avant-bataille : prebattle_map.png (Warhammer 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
