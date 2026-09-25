#!/usr/bin/env python3
"""
lf_normal_depuis_relief.py - `lf_normal.dds` recalculée depuis NOTRE relief, au codage exact de CA.

Pourquoi (24.09.2026, 00 h 45, session du rendu ; Charles, depuis le 23.09 : « quand je dézoome, il y a un carré », 00 h 40 :
« comme s'il y avait deux cartes, une en petit et une en grand, c'est au niveau de la luminosité »). Notre `lf_normal.dds`
était celle de WH1 (`lf_normal_wh1_vers_wh3.py`, 22.09.2026), ramenée à la taille du relief : elle ne suit plus notre relief
(corrélation de ses composantes avec nos pentes : -0,29 / -0,31), alors que celle des Empires suit le leur à 0,89 / 0,91
(brouillon `lf_normal_etalon_ie.py`). Le jeu éclaire le relief lointain par elle, le proche par la géométrie : deux
éclairages, et un carré autour de la caméra au dézoom. BOB n'en produit pas pour une campagne.

Codage de CA (étalonné sur les Empires, `--etalonner`) : DXT5 à la taille du relief du projet, niveaux complets ; R = 255,
B = 0 ; A = 127,5 + 127,5 nx ; G = 127,5 + 127,5 nz ; n = normale unitaire de (-k dh/dx, 1, -k dh/dz), x vers l'est, z vers le
SUD (lignes de l'image), pentes par pixel rapportées à la largeur d'un pixel en x pour les deux axes, k ajusté.

Usage :
    python lf_normal_depuis_relief.py --etalonner      # ajuste k sur les Empires (lecture seule)
    python lf_normal_depuis_relief.py                  # contrôle à blanc sur notre relief (aperçus dans le scratchpad)
    python lf_normal_depuis_relief.py --apply          # écrit working_data\\...\\lf_normal.dds (ancienne sauvegardée)
"""

import argparse
import glob
import io
import os
import shutil
import struct
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

Image.MAX_IMAGE_PIXELS = None
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
ATELIER = r"C:\TotalWar-CampaignMap"
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE
PROJET = os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE)
COMPILE = os.path.join(KIT, "working_data", "terrain", "campaigns", CARTE)
IE = os.path.join(KIT, "raw_data", "terrain", "campaigns", "wh3_main_combi_map_1")
SAUVEGARDES = os.path.join(ATELIER, "05-journal", "terrain-backups")
LARGEUR_MONDE, LARGEUR_IE = 266.53, 961.3
K_RETENU = 2.35               # ajusté sur les Empires (--etalonner, 24.09.2026 : écart quadratique 11,6 sur 255)
# (25.09.2026, 02 h 35, session du rendu : stries grises des montagnes vues de loin) le relief de WH1 est rainuré (maillages
# de montagnes posés sur un relief bruité) ; ses normales brutes ont un contraste fin (écart à la moyenne locale sur 2 u, sur
# la terre) de 0,489 contre 0,227 aux Empires. Relief lissé (gaussien, sigma en pixels) avant le calcul : 0,218 à 12 px (1 u).
# Mesure : scratchpad `peaufinage_montagnes\choisir_sigma.py`. 0 = relief brut.
LISSAGE_PX = 12.0


def lisser(h, sigma):
    if not sigma:
        return h
    import cv2
    return cv2.GaussianBlur(h, (0, 0), float(sigma), borderType=cv2.BORDER_REPLICATE)


def relief(dossier):
    f = glob.glob(os.path.join(dossier, "*.height.*.tif"))
    if len(f) != 1:
        raise SystemExit(f"relief du projet introuvable ou ambigu dans {dossier} : {f}")
    return np.asarray(Image.open(f[0]), np.float64)


def normales(h, px, k):
    """(nx, nz) unitaires : x vers l'est (colonnes), z vers le sud (lignes) ; pentes par pixel / px (plat pour les
    derniers niveaux, trop petits pour une pente)."""
    gz = np.gradient(h, axis=0) if h.shape[0] >= 2 else np.zeros_like(h)
    gx = np.gradient(h, axis=1) if h.shape[1] >= 2 else np.zeros_like(h)
    ax, az = -k * gx / px, -k * gz / px
    lg = np.sqrt(ax * ax + az * az + 1.0)
    return ax / lg, az / lg


def etalonner():
    from contenu_pack import SourcePacks
    b = SourcePacks(os.path.join(os.path.dirname(KIT), "data")).lire("terrain/campaigns/wh3_main_combi_map_1/lf_normal.dds")
    im = Image.open(io.BytesIO(b))
    im.load()
    n = np.asarray(im.convert("RGBA"))
    h = relief(IE)
    if h.shape != n.shape[:2]:
        raise SystemExit(f"relief {h.shape} et lf_normal {n.shape[:2]} des Empires de tailles différentes")
    px = LARGEUR_IE / h.shape[1]
    rng = np.random.default_rng(1)
    ii = rng.integers(1, h.shape[0] - 1, 400000)
    jj = rng.integers(1, h.shape[1] - 1, 400000)
    A, G = n[ii, jj, 3].astype(np.float64), n[ii, jj, 1].astype(np.float64)
    gz = (h[ii + 1, jj] - h[ii - 1, jj]) / 2.0
    gx = (h[ii, jj + 1] - h[ii, jj - 1]) / 2.0
    meilleur = None
    for k in np.arange(0.5, 4.0001, 0.05):
        ax, az = -k * gx / px, -k * gz / px
        lg = np.sqrt(ax * ax + az * az + 1.0)
        e = np.sqrt(np.mean((127.5 + 127.5 * ax / lg - A) ** 2 + (127.5 + 127.5 * az / lg - G) ** 2) / 2)
        if meilleur is None or e < meilleur[1]:
            meilleur = (float(k), float(e))
    print(f"Empires : k = {meilleur[0]:.2f}, écart quadratique moyen {meilleur[1]:.2f} (sur 255) ; R = {n[..., 0].mean():.1f}, "
          f"B = {n[..., 2].mean():.1f}")
    return meilleur[0]


def encoder_dxt5(nx, nz):
    """Octets DXT5 (niveau 0) de l'image R = 255, G = nz, B = 0, A = nx (codeur BCn de Pillow)."""
    rgba = np.empty(nx.shape + (4,), np.uint8)
    rgba[..., 0] = 255
    rgba[..., 1] = np.clip(np.round(127.5 + 127.5 * nz), 0, 255)
    rgba[..., 2] = 0
    rgba[..., 3] = np.clip(np.round(127.5 + 127.5 * nx), 0, 255)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "DDS", pixel_format="DXT5")
    return buf.getvalue()[128:]


def construire(k, modele):
    """Octets du nouveau lf_normal.dds : en-tête de `modele` (le fichier en place : taille, niveaux, drapeaux), niveaux
    recalculés (chaque niveau depuis le relief moyenné 2 x 2, normales renormalisées)."""
    H, L = struct.unpack_from("<II", modele, 12)
    mips = max(struct.unpack_from("<I", modele, 28)[0], 1)
    h = lisser(relief(PROJET), LISSAGE_PX)
    if h.shape != (H, L):
        raise SystemExit(f"relief du projet {h.shape} et lf_normal en place {(H, L)} de tailles différentes")
    px = LARGEUR_MONDE / L
    niveaux, rel, p = [], h, px
    for m in range(mips):
        nx, nz = normales(rel, p, k)
        niveaux.append(encoder_dxt5(nx, nz))
        if m == mips - 1:
            break
        hh, ll = rel.shape
        rel = rel[:hh - hh % 2, :ll - ll % 2].reshape(hh // 2, 2, ll // 2, 2).mean((1, 3)) if min(hh, ll) >= 2 else rel
        if rel.shape[0] == 0 or rel.shape[1] == 0:
            break
        p *= 2
    data = b"".join(niveaux)
    if 128 + len(data) != len(modele):
        raise SystemExit(f"taille {128 + len(data)} différente de celle du fichier en place {len(modele)} : niveaux ?")
    return modele[:128] + data


def controle(b, titre):
    im = Image.open(io.BytesIO(b))
    im.load()
    n = np.asarray(im.convert("RGBA")).astype(np.float64)
    h = relief(PROJET)
    gz, gx = np.gradient(h)
    d = 3
    c1 = np.corrcoef(n[::d, ::d, 3].ravel(), -gx[::d, ::d].ravel())[0, 1]
    c2 = np.corrcoef(n[::d, ::d, 1].ravel(), -gz[::d, ::d].ravel())[0, 1]
    print(f"{titre} : corrélation A / -dh/dx {c1:+.3f}, G / -dh/dz {c2:+.3f} ; R {n[..., 0].mean():.1f}, B {n[..., 2].mean():.1f}, "
          f"G {n[..., 1].mean():.1f} ± {n[..., 1].std():.1f}, A {n[..., 3].mean():.1f} ± {n[..., 3].std():.1f}")
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etalonner", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("-k", type=float, default=None, help="facteur de pente (défaut : ajusté sur les Empires)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.etalonner:
        etalonner()
        return 0
    k = a.k if a.k is not None else K_RETENU
    chemin = os.path.join(COMPILE, "lf_normal.dds")
    ancien = open(chemin, "rb").read()
    controle(ancien, "en place (WH1)")
    neuf = construire(k, ancien)
    n = controle(neuf, f"recalculée (k = {k})")
    apercu = os.path.join(os.environ.get("TEMP", ATELIER), "lf_normal_neuve_apercu.png")
    t = Image.fromarray(np.dstack([n[..., 3], n[..., 1], np.full(n.shape[:2], 128.0)]).astype(np.uint8))
    t.thumbnail((800, 880))
    t.save(apercu)
    print("aperçu (rouge = A, vert = G) :", apercu)
    if not a.apply:
        print("contrôle fait ; relancer avec --apply pour écrire")
        return 0
    os.makedirs(SAUVEGARDES, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(chemin, os.path.join(SAUVEGARDES, f"lf_normal-avant-{stamp}.dds"))
    with open(chemin, "wb") as f:
        f.write(neuf)
    print(f"écrit : {chemin} ; ancienne : lf_normal-avant-{stamp}.dds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
