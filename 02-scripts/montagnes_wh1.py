#!/usr/bin/env python3
"""
montagnes_wh1.py - les montagnes de Warhammer 1, posées dans notre carte comme dans WH1.

Pourquoi (22.09.2026, 22 h ; Charles : « les montagnes, c'est le gros problème : il faut qu'elles soient vraiment pareilles
que dans Warhammer 1 »). Les montagnes de WH1 ne sont pas du relief : ce sont 31 maillages sculptés et texturés
(`terrain/tiles/campaign/{empire,generic}_mountains/<tuile>/custom_mesh.rigid_model_v2`, 514 poses, 30,7 % de la carte),
posés par son moteur de tuiles. Établi le 22.09.2026 (journal `05-journal\\2026-09-22-phase-4\\montagnes-wh1.md`) :
- **WH3 dessine ce type de maillage** : ses falaises de côte (`cliff_gen`) ont le même format (RMV2, matériau 49
  `rigid_default`, chemin de texture de base sans suffixe, sommets de 36 octets) ; il y ajoute `_base_colour`,
  `_material_map`, `_normal` (textures de ses falaises dans ses packs).
- **Pose** (règle de l'agent de recherche, confirmée sur la hauteur de caméra de WH1 pour les 23 plus grandes
  montagnes : aucune autre orientation, base ni échelle ne fait mieux) : emprise au coin sud-ouest (x, y) en cases,
  repère local u = x / 128 vers l'est, n = z / 128 + H vers le nord ; codes 0x10, 0x20, 0x40, 0x80 = quarts de tour
  (`CHOIX`) ; **maillage drapé** : y du monde = relief de base de WH1 + 0,2546 + S x y local, S = case / 128 (échelle
  isotrope).
- Fichier : 4 niveaux de détail de 1 ou 2 morceaux ; boîte englobante de chaque morceau à +24 (6 flottants).

Réalisation dans WH3 : chaque pose devient un objet (entité `ECMesh` d'un calque Terry) dont le modèle est une copie du
maillage de WH1 **drapée d'avance** (chaque sommet relevé du relief de base sous lui) ; position = coin de l'emprise,
rotation autour de y, échelle S. Textures de WH1 converties au chemin de base qu'elles ont dans WH1 (`decalques_wh1` :
couleur sans réencodage, rugosité = 255 - brillance, normale telle quelle), déplacées sous `_wh1/` si WH3 a quelque chose
à ce chemin.

Usage :
    python montagnes_wh1.py                  # bilan à blanc
    python montagnes_wh1.py --essai 432,433  # quelques poses dans un calque d'essai du projet Terry (sauvegardé avant)
"""

import argparse
import math
import os
import re
import shutil
import struct
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tuiles_wh1 as T                                              # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
KIT_WD = os.path.join(KIT, "working_data")
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit)
PROJET = os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE)
SORTIE = carte_config.dans_projet("montagnes-wh1")
DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"

# montagnes, puis falaises intérieures de WH1 et leurs extrémités (22.09.2026, 22 h : même format, matériau 49, textures
# `badlands_mountain_small_01/1_badlands_diamond` ; aucune pose en miroir). Les falaises de côte (`cliff_custom`, 233
# poses) les rejoignent le 23.09.2026 (Charles, dans Terry : « les bords autour de la mer… des carrés… plus naturel ») :
# même repère que les falaises intérieures (z local de -256 à 0, y de -422 à +9 : la face descend de 1,1 sous le sol,
# jusqu'au fond de la mer), posées dans WH1 par-dessus ses maillages de terre et de mer (0 % de leur emprise hors
# maillage) ; elles remplacent les `cliff_gen` de WH3 de l'ancienne bande de côte.
FAMILLES = ("empire_mountains", "generic_mountains", "cliff_inland_custom", "cliff_inland_custom_passable",
            "cliff_end_anchors", "cliff_custom")
LARGEUR_MONDE = 266.53
CASE = LARGEUR_MONDE / T.LARGEUR                   # 0,33316 unité par case
S = CASE / 128                                     # unité locale -> monde, horizontale et verticale
BASE = 0.2546                                      # maillages de terrain de WH1 - relief de base (médiane)
PROFONDEUR_MONDE = T.HAUTEUR * CASE                # 293,5
BORD = 0.05                                        # marge des boîtes déclarées au bord de la carte
# local (u, n) -> emprise (X, Y), en cases : (échange, u -> W - u, n -> H - n), appliqués dans cet ordre : miroirs puis
# échange (règle de l'agent de recherche, `poser_tuiles_wh1.CHOIX`)
CHOIX = {0x10: (False, False, False), 0x20: (True, True, False), 0x40: (False, True, True), 0x80: (True, False, True)}
DOSSIER_MODELES = "rigidmodels/_wh1/campaign/montagnes"
# NIVEAUX DE DÉTAIL (23.09.2026, 17 h 45 ; Charles : « des montagnes vertes, ça fait très vallonné, bizarre »). Les
# maillages de WH1 déclarent leur LOD 0 jusqu'à 20 u (845 fichiers) ou 100 u (416), puis des LOD grossiers ; ceux-ci passent
# sous notre sol (2 cm sous le LOD 0) sur 11 % (LOD 1) à 29 % (LOD 2) de leur surface, en médiane (brouillon `lod_ecarts.py`,
# journal du rendu § 2.8) : aux distances de la caméra de campagne, le sol (sous-bois vert) perçait. Le LOD 0, léger (2 200
# à 5 900 triangles), sert désormais à toutes les distances (distances croissantes jusqu'à 99 999, la dernière de CA).
DISTANCE_LOD = 99999.0
# Repère (22.09.2026, 23 h 10, erreur 89) : les calculs ci-dessous (cases, relief, drapé) sont dans le repère des rasters,
# à pixels carrés (profondeur 293,5) ; le monde de WH3, où vivent les entités, est l'espace des hex, étiré de 2/√3 en z
# (profondeur 338,9 ; `props_wh1_vers_layers.Z_VERS_RASTER`). Une montagne s'y pose donc à z × 2/√3 et s'y étire d'autant
# du sud au nord (échelle de l'entité sur l'axe local qui pointe vers le nord).
Z_VERS_MONDE = 2 / 3 ** 0.5


def ident(graine):
    """Identifiant Terry stable (même règle que `terrain_wh1_vers_terry.ident`)."""
    import hashlib
    return "1" + hashlib.sha1(f"{CARTE}:{graine}".encode()).hexdigest()[:14]


def cadre(u, n, W, H, choix):
    s, mx, my = choix
    if mx:
        u = W - u
    if my:
        n = H - n
    if s:
        u, n = n, u
    return u, n


class Pose:
    __slots__ = ("k", "x", "y", "code", "idx", "nom", "famille", "W", "H")


def poses():
    """Les poses de montagne de WH1, dans l'ordre de `tile_list.bin`."""
    noms, recs = T.lire()
    out = []
    for k, (x, y, code, _clim, _k, idx, _e) in enumerate(recs):
        fam = T.famille(noms[idx])
        if fam not in FAMILLES:
            continue
        p = Pose()
        p.k, p.x, p.y, p.code, p.idx = k, x, y, code, idx
        p.nom = noms[idx].replace("\\", "/").lower()
        p.famille = fam
        p.W, p.H = T.taille(noms[idx])
        out.append(p)
    return out


def vers_monde(p, vx, vz):
    """Sommets locaux (unités de la tuile) -> (x, z) du monde."""
    u, n = vx / 128.0, vz / 128.0 + p.H
    X, Y = cadre(u, n, p.W, p.H, CHOIX[p.code & 0xF0])
    return (p.x + X) * CASE, (p.y + Y) * CASE


def transformation(p):
    """(position x, position z, ry en degrés) de l'objet : monde = position + v @ (S · Ry(-ry)), convention des calques
    Terry (`props_wh1_vers_layers.rotation_terry`). Vérifie qu'il s'agit bien d'une rotation."""
    pts = np.array([[0.0, 0.0], [128.0, 0.0], [0.0, 128.0]])
    wx, wz = vers_monde(p, pts[:, 0], pts[:, 1])
    t = np.array([wx[0], wz[0]])
    a = np.array([[wx[1] - wx[0], wx[2] - wx[0]], [wz[1] - wz[0], wz[2] - wz[0]]]) / (128.0 * S)
    if abs(np.linalg.det(a) - 1) > 1e-6 or np.abs(a @ a.T - np.eye(2)).max() > 1e-6:
        raise SystemExit(f"pose {p.k} : la transformation n'est pas une rotation ({a.tolist()})")
    # v @ Ry(θ) : x' = c vx - s vz ; z' = s vx + c vz  ->  a = [[c, -s], [s, c]] ; θ = -ry
    theta = math.atan2(a[1, 0], a[0, 0])
    return float(t[0]), float(t[1]), -math.degrees(theta)


def morceaux(b):
    """(début, matériau, décalage des sommets, nombre, pas) de chaque morceau de chaque niveau de détail."""
    ver, nlod = struct.unpack_from("<II", b, 4)
    if b[:4] != b"RMV2" or ver not in (6, 7):
        raise ValueError("RMV2 v6 ou v7 attendu")
    out = []
    for k in range(nlod):
        nb, _, _, off = struct.unpack_from("<IIII", b, 140 + 28 * k)
        for _ in range(nb):
            mat, _, taille, voff, vc, ioff, _ic = struct.unpack_from("<HHIIIII", b, off)
            out.append((off, mat, voff, vc, (ioff - voff) // max(vc, 1)))
            off += taille
    if off != len(b):
        raise ValueError(f"fin des morceaux {off} != taille {len(b)}")
    return out


# LES NORMALES SUIVENT LE DRAPÉ (24.09.2026, 00 h 20, session du rendu ; Charles, 23.09.2026, 23 h 25 : « les montagnes n'ont
# pas du tout l'aspect qu'elles avaient dans le 1, elles sont beaucoup plus moches »). Le drapé relevait chaque sommet sans
# toucher à sa normale ni à ses tangentes : l'écart entre la normale stockée et celle de la surface drapée passait de 0,4-5°
# (fichiers de WH1) à 13-22° en médiane sur la moitié des montagnes (brouillons `normales_drapees.py`,
# `format_sommets_montagnes.py`, `tangentes_montagnes.py`) : lumière et reliefs des textures faux. Le moteur de WH1 drapait
# à l'affichage et éclairait la surface drapée. Sommet de 36 octets : position f32 x 3 (0), w f32 (12), normale (16),
# tangente (20), bitangente (24) en u8 dans l'ordre z, y, x (+ w), coordonnées de texture f16 x 2 (28). Le drapé
# y' = y + f(x, z) a pour jacobienne J = I + e_y (fx, 0, fz) : normale par l'inverse transposée (n - n_y (fx, 0, fz)),
# tangente et bitangente par J (t + (0, fx t_x + fz t_z, 0)), renormalisées ; les w sont gardés.
NORMALES_DRAPEES = True
PENTE_DRAPE_PX = 1.5                               # px du relief : pas des pentes du drapé (essai : 1 à 2 px au mieux)
# LES SOMMETS DANS LEUR BOÎTE (24.09.2026, 01 h 50, session du rendu, piste du plantage +0x1A3DCFA ; brouillon
# `controle_maillages_montagnes.py`) : la boîte déclarée est ramenée dans la carte pour BOB, mais 16 modèles des bords
# gardaient des sommets au-delà (jusqu'à 1,72 u hors de la carte et de leur boîte) ; CA n'en a aucun. Ces sommets sont
# ramenés sur la boîte, donc sur le bord de la carte (variante V1e de la construction).
BORDS_RAMENES = True


def _vecteur_drape(o, fx, fz, normale):
    """Octets u8 (composantes z, y, x) d'un vecteur de sommet, transformés par le drapé (voir NORMALES_DRAPEES)."""
    c = o.astype(np.float64) / 127.5 - 1.0
    x, y, z = c[:, 2], c[:, 1], c[:, 0]
    if normale:
        x, z = x - fx * y, z - fz * y
    else:
        y = y + fx * x + fz * z
    n = np.sqrt(x * x + y * y + z * z)
    n = np.where(n > 1e-9, n, 1.0)
    out = np.stack([z / n, y / n, x / n], 1)
    return np.clip(np.round((out + 1.0) * 127.5), 0, 255).astype(np.uint8)


def draper(b, p, sol, pas):
    """Copie du maillage où chaque sommet est relevé du relief `sol` (raster ligne 0 au nord, `pas` px par unité) sous
    lui, relatif à y0 (moyenne du relief sous la pose) : rend (octets, y0). Boîtes englobantes mises à jour ; normales,
    tangentes et bitangentes transformées par le drapé (NORMALES_DRAPEES)."""
    H_, L_ = sol.shape

    def sous(xs, zs):
        cx = np.clip(xs * pas - 0.5, 0, L_ - 1.001)
        cy = np.clip((H_ - 1.5) - zs * pas, 0, H_ - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        return (sol[r0, c0] * (1 - fx) * (1 - fy) + sol[r0, c0 + 1] * fx * (1 - fy)
                + sol[r0 + 1, c0] * (1 - fx) * fy + sol[r0 + 1, c0 + 1] * fx * fy)

    out = bytearray(b)
    parts = morceaux(b)
    y0 = None
    for off, mat, voff, vc, pas_v in parts:
        if pas_v < 12:
            raise ValueError(f"pas de sommet {pas_v} inattendu")
        v = np.frombuffer(b, np.uint8, count=vc * pas_v, offset=off + voff).reshape(vc, pas_v)
        xyz = v[:, :12].copy().view("<f4").reshape(vc, 3).astype(np.float64)
        wx, wz = vers_monde(p, xyz[:, 0], xyz[:, 2])
        base = sous(wx, wz) + BASE
        if y0 is None:
            y0 = float(np.mean(base))
        y = xyz[:, 1] + (base - y0) / S
        brut = np.frombuffer(bytes(v), np.uint8).reshape(vc, pas_v).copy()
        brut[:, 4:8] = y.astype("<f4").view(np.uint8).reshape(vc, 4)
        if NORMALES_DRAPEES and pas_v == 36:
            # pentes du drapé en unités locales, sur un demi-pixel du relief
            d = PENTE_DRAPE_PX / (pas * S)
            fx = (sous(*vers_monde(p, xyz[:, 0] + d, xyz[:, 2])) + BASE - base) / (S * d)
            fz = (sous(*vers_monde(p, xyz[:, 0], xyz[:, 2] + d)) + BASE - base) / (S * d)
            brut[:, 16:19] = _vecteur_drape(brut[:, 16:19], fx, fz, True)
            brut[:, 20:23] = _vecteur_drape(brut[:, 20:23], fx, fz, False)
            brut[:, 24:27] = _vecteur_drape(brut[:, 24:27], fx, fz, False)
        out[off + voff:off + voff + vc * pas_v] = brut.tobytes()
        # boîte déclarée : hauteurs drapées ; en x et z, ramenée dans la carte (BOB refuse un objet dont la boîte
        # déborde : « Failed to find valid quadtree node », 10 montagnes du bord le 22.09.2026 à 21 h 41)
        dedans = (wx >= BORD) & (wx <= LARGEUR_MONDE - BORD) & (wz >= BORD) & (wz <= PROFONDEUR_MONDE - BORD)
        garde = dedans if dedans.any() else np.ones(vc, bool)
        boite = [float(xyz[garde, 0].min()), float(y.min()), float(xyz[garde, 2].min()),
                 float(xyz[garde, 0].max()), float(y.max()), float(xyz[garde, 2].max())]
        struct.pack_into("<6f", out, off + 24, *boite)
        if BORDS_RAMENES and not garde.all():
            # (24.09.2026) les sommets hors de la carte, donc hors de la boîte, ramenés sur elle (voir BORDS_RAMENES)
            xyz_b = np.stack([np.clip(xyz[:, 0], boite[0], boite[3]), y, np.clip(xyz[:, 2], boite[2], boite[5])], 1)
            brut[:, 0:12] = xyz_b.astype("<f4").view(np.uint8).reshape(vc, 12)
            out[off + voff:off + voff + vc * pas_v] = brut.tobytes()
    return bytes(out), y0


def lod_fin_partout(b):
    """Distances des niveaux de détail réécrites (entrées de 28 octets, f32 à +16) : le LOD 0 jusqu'à DISTANCE_LOD - (n -
    1), les suivants au-delà (jamais atteints) ; la géométrie ne change pas."""
    out = bytearray(b)
    n = struct.unpack_from("<I", b, 8)[0]
    for k in range(n):
        struct.pack_into("<f", out, 140 + 28 * k + 16, DISTANCE_LOD - (n - 1 - k))
    return bytes(out)


def base_texture(b):
    """Chemin de base des textures cité par le premier morceau (champ de 256 octets à +80)."""
    off = struct.unpack_from("<I", b, 152)[0]
    return b[off + 80:off + 80 + 256].split(b"\0")[0].decode("ascii").replace("\\", "/").lower()


def bases_textures(b):
    """Chemins de base des textures de TOUS les morceaux (un modèle peut en citer plusieurs)."""
    return sorted({b[off + 80:off + 80 + 256].split(b"\0")[0].decode("ascii").replace("\\", "/").lower()
                   for off, *_ in morceaux(b)})


def remplacer_base(b, ancienne, nouvelle, barre="\\"):
    """Réécrit le chemin de base des textures dans chaque morceau (champ de taille fixe), avec le séparateur `barre`."""
    out = bytearray(b)
    for off, *_ in morceaux(b):
        champ = out[off + 80:off + 80 + 256].split(b"\0")[0].decode("ascii").replace("\\", "/").lower()
        if champ != ancienne:
            continue
        neuf = nouvelle.replace("/", barre).encode("ascii")
        if len(neuf) >= 256:
            raise ValueError("chemin trop long")
        out[off + 80:off + 80 + 256] = neuf + b"\0" * (256 - len(neuf))
    return bytes(out)


# LES TEXTURES SOUS UN CHEMIN D'OBJET (23.09.2026, 21 h, session du rendu, avec la construction ; piste du plantage de rendu
# +0x1A3DCFA) : le vidage de 20 h 21 montre, dans l'objet de rendu libéré puis relu, le chemin de nos textures de montagne
# (`terrain\textures\campaign\default\badlands_mountain_small_01\1_badlands_diamond_*`, 841 modèles) ; ces maillages citent
# un chemin de base de texture DE TERRAIN, comme les maillages de falaise des tuiles de CA (`cliff_gen/custom_mesh`), alors
# que nous les posons en objets (ECMesh) ; la pile citait la base des tuiles (TILE_DATABASE). Choix de la construction :
# les textures passent sous DOSSIER_TEXTURES, chemin d'objet, et le chemin de base est réécrit dans chaque morceau, en barres
# obliques et minuscules comme nos autres objets de WH1 qui s'affichent (décalques) ; géométrie inchangée.
TEXTURES_OBJET = True
DOSSIER_TEXTURES = f"{DOSSIER_MODELES}/textures"


# MATIÈRE PAR PIXEL (23.09.2026, 18 h ; Charles : « que les montagnes rendent mieux, avec de meilleures textures ») : la
# rugosité de chaque pixel vient de la brillance du `_spec_gloss` de WH1 (G = 255 - alpha, R = B = 0, A = 255), encodée en
# BC7 1024² comme les textures de sol de WH1 (`textures_sol_wh1.convertir`, `bc7.py`) ; avant, une rugosité uniforme (la
# moyenne), faute d'encodeur : roche mouillée, neige et arêtes brillaient toutes pareil.
MATIERE_PAR_PIXEL = True


def matiere_par_pixel(specgloss):
    """`_material_map` de CA (DX10 BC7, niveaux jusqu'à 1 x 1) depuis le `_spec_gloss` de WH1."""
    import io
    import bc7
    from PIL import Image
    sg = np.array(Image.open(io.BytesIO(specgloss)).convert("RGBA"))
    while sg.shape[0] > 1024:
        sg = bc7.reduire(sg)
    mat = np.zeros_like(sg)
    mat[..., 1] = 255 - sg[..., 3]
    mat[..., 3] = 255
    return bc7.dds_bc7(bc7.chaine(mat), srgb=False)


def textures(wh1, base):
    """{chemin de WH3 : octets} des textures d'une montagne de WH1 de chemin de base `base`."""
    from decalques_wh1 import en_dx10, carte_materiau, rugosite_de, DXGI_BC3_UNORM_SRGB
    diffuse = wh1.lire(base + "_diffuse.dds")
    if diffuse is None:
        raise SystemExit(f"{base}_diffuse.dds absent de WH1")
    specgloss = wh1.lire(base + "_spec_gloss.dds")
    out = {base + "_base_colour.dds": en_dx10(diffuse, DXGI_BC3_UNORM_SRGB),
           base + "_material_map.dds": (matiere_par_pixel(specgloss) if MATIERE_PAR_PIXEL and specgloss is not None
                                        else carte_materiau(rugosite_de(specgloss)))}
    normale = wh1.lire(base + "_normal.dds")
    if normale is not None:
        out[base + "_normal.dds"] = normale
    return out


def surface(lf, pas, liste=None):
    """Dessus des montagnes posées (drapées sur `lf` + BASE, jupes exclues) rastérisé sur la grille du relief (ligne 0 au
    nord, `pas` px par unité) : maximum des maillages du LOD 0 ; NaN hors des montagnes."""
    import sommets_rmv2
    import relief_maillages_wh1 as R
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    H_, L_ = lf.shape
    grille = np.full((H_, L_), np.nan)
    cache = {}

    def sous(xs, zs):
        cx = np.clip(xs * pas - 0.5, 0, L_ - 1.001)
        cy = np.clip((H_ - 1.5) - zs * pas, 0, H_ - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        return (lf[r0, c0] * (1 - fx) * (1 - fy) + lf[r0, c0 + 1] * fx * (1 - fy)
                + lf[r0 + 1, c0] * (1 - fx) * fy + lf[r0 + 1, c0 + 1] * fx * fy)

    for p in (liste if liste is not None else poses()):
        if p.nom not in cache:
            cache[p.nom] = sommets_rmv2.maillage(wh1.lire(p.nom + "custom_mesh.rigid_model_v2"))
        v, t = cache[p.nom]
        wx, wz = vers_monde(p, v[:, 0], v[:, 2])
        hy = sous(wx, wz) + BASE + S * np.maximum(v[:, 1], 0)
        R.rasteriser_px(wx * pas - 0.5, (H_ - 1.5) - wz * pas, hy, t, grille)
    return grille


def entite(ident, modele, x, y, z, ry):
    """Entité d'objet de montagne, réglée comme les montagnes des Empires (3 044 poses de
    `generic_props/mountains/<culture>/`) : visible en vue tactique et sous le brouillard, forme reportée dans le relief
    logique (`apply_height_patch`). `x, y, z` dans le repère des rasters : l'entité est écrite dans le monde de WH3
    (z × Z_VERS_MONDE), étirée de Z_VERS_MONDE sur l'axe local qui y pointe vers le nord (x local si ry = ±90°, z local
    si ry = 0 ou 180° : convention monde = v @ (diag(échelle) · Ry(-ry)) + position)."""
    nord_local_x = abs(math.sin(math.radians(ry))) > 0.5
    if abs(abs(math.sin(math.radians(ry))) - (1.0 if nord_local_x else 0.0)) > 1e-6:
        raise SystemExit(f"{modele} : rotation {ry}° qui n'est pas un quart de tour")
    sx, sz = (S * Z_VERS_MONDE, S) if nord_local_x else (S, S * Z_VERS_MONDE)
    z = z * Z_VERS_MONDE
    return (f'\t\t<entity id="{ident}">\n'
            '\t\t\t<ECPropMesh/>\n'
            f'\t\t\t<ECMesh model_path="{modele}" opacity="1"/>\n'
            '\t\t\t<ECMeshRenderSettings receive_decals="True"/>\n'
            '\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="True" visible_in_tactical_view_only="False"/>\n'
            # pas de report de la forme dans le relief : notre relief suit déjà la montagne (2 cm dessous) ; reporté,
            # il modifiait le sol affiché autour d'elle (22.09.2026, 22 h 35)
            '\t\t\t<ECPropHeightPatch apply_height_patch="False" for_camera_height_map_only="false"/>\n'
            '\t\t\t<ECCampaignProperties visible_inside_snow_region="True" visible_outside_snow_region="True" '
            'visible_inside_destruction_region="True" visible_outside_destruction_region="True" '
            'visible_in_shroud="True" visible_in_shroud_only="False" no_culling="False" culture_mask=""/>\n'
            f'\t\t\t<ECTransform position="{x:.5f} {y:.5f} {z:.5f}" rotation="0.00000 {ry:.5f} 0.00000" '
            f'scale="{sx:.7f} {S:.7f} {sz:.7f}" pivot="0 0 0"/>\n'
            '\t\t</entity>\n')


# LES FALAISES DE CÔTE SUR LA CÔTE NATURELLE (24.09.2026, 02 h 20, session du rendu ; `cotes_wh1`) : les 233 falaises de côte
# de WH1 (`cliff_custom`, 2 x 2 cases) décoraient les angles de l'escalier de sa côte ; la côte lissée arrondit les caps, et
# 79 d'entre elles se retrouveraient debout en pleine mer. Une falaise de côte n'est posée que si son emprise (plus 2 px)
# contient encore de la terre et de la mer (`sur_la_cote`).
FALAISES_SUR_LA_COTE = True
# PLUS DE FALAISES DE CÔTE (24.09.2026, 05 h, chaîne 11 ; vidéo V2 de Charles, 50 s et 70 s, Mousillon : « murs pâles en
# escalier », le liseré blanc le long de la côte). Les 151 falaises gardées au bord de la côte naturelle y dessinaient
# encore l'escalier de WH1 : blocs de 2 x 2 cases faits pour ses marches, faces claires hors de l'eau. La côte naturelle
# n'en veut aucune : ni objet, ni dessus de maillage sous le sol (`poses_retenues`, pour `construire` et `surface`).
# REMISES (24.09.2026, chaîne 12 ; Charles, 18 h 55 : « fais exactement comme dans Warhammer 1 au niveau du découpage de la
# côte ») : la côte reprend le découpage de WH1 à la case près (`cotes_wh1.LISSAGE = False`), les falaises retrouvent les
# angles pour lesquels WH1 les avait faites.
# RETIRÉES DE NOUVEAU (24.09.2026, 22 h 50, chaîne 13 ; capture de Charles, 22 h 40, golfe nord du Bidouze : « murs sombres
# verticaux » le long d'une côte en escalier) : 75 % du trait de côte du golfe était à moins de 4 px d'une de ces falaises (57 %
# sur la carte). Avec la côte lisse remise (`cotes_wh1.LISSAGE`), elles n'ont plus d'angles où se poser. Les 233 poses
# `cliff_custom` touchent toutes la mer de WH1 ; aucune autre famille ne la touche (`falaises_cote_compte.py`) : les 1 149
# montagnes et falaises intérieures (dont 545 `cliff_inland_*` et 90 `cliff_end_anchors`) restent.
FALAISES_DE_COTE = False


def poses_retenues(mer=None):
    """Les poses de montagne posées : sans les falaises de côte (`cliff_custom`) si FALAISES_DE_COTE est faux ; sinon,
    avec `mer` et FALAISES_SUR_LA_COTE, seulement celles qui touchent la côte."""
    liste = poses()
    if not FALAISES_DE_COTE:
        return [p for p in liste if p.famille != "cliff_custom"]
    if mer is not None and FALAISES_SUR_LA_COTE:
        return [p for p in liste if p.famille != "cliff_custom" or sur_la_cote(p, mer)]
    return liste


def sur_la_cote(p, mer, marge=2):
    """La pose `p` (emprise en cases) touche-t-elle la côte du masque `mer` (raster, ligne 0 au nord) ?"""
    W, Hh = (p.H, p.W) if (p.code & 0xF0) in (0x20, 0x80) else (p.W, p.H)
    k = mer.shape[0] // T.HAUTEUR
    r0, c0 = (T.HAUTEUR - (p.y + Hh)) * k, p.x * k
    e = mer[max(r0 - marge, 0):r0 + Hh * k + marge, max(c0 - marge, 0):c0 + W * k + marge]
    return bool(e.any() and not e.all())


def construire(choisies=None, ecrire=False, mer=None):
    """Maillages drapés, textures, entités. `choisies` : indices dans la liste des poses (None : toutes). `mer` : masque
    de la mer finale (raster) pour ne garder que les falaises de côte qui la touchent (FALAISES_SUR_LA_COTE)."""
    from modeles_wh1 import SourceWH1
    from contenu_pack import chemins_du_jeu
    import relief_maillages_wh1 as R
    wh1 = SourceWH1()
    jeu = chemins_du_jeu(DATA_WH3)
    lf = R.relief_lf().astype(np.float64)
    toutes = poses()
    liste = [toutes[i] for i in choisies] if choisies is not None else toutes
    if not FALAISES_DE_COTE:
        avant = len(liste)
        liste = [p for p in liste if p.famille != "cliff_custom"]
        print(f"falaises de côte de WH1 écartées (FALAISES_DE_COTE) : {avant - len(liste)}")
    elif mer is not None and FALAISES_SUR_LA_COTE:
        avant = len(liste)
        liste = [p for p in liste if p.famille != "cliff_custom" or sur_la_cote(p, mer)]
        print(f"falaises de côte qui ne touchent plus la côte, écartées : {avant - len(liste)}")
    fichiers, entites, bases = {}, [], {}
    for p in liste:
        brut = wh1.lire(p.nom + "custom_mesh.rigid_model_v2")
        if brut is None:
            raise SystemExit(f"{p.nom}custom_mesh.rigid_model_v2 absent de WH1")
        for base in (bases_textures(brut) if TEXTURES_OBJET else [base_texture(brut)]):
            if base not in bases:
                if TEXTURES_OBJET:
                    dest = f"{DOSSIER_TEXTURES}/{'/'.join(base.split('/')[-2:])}"
                    if any(c.startswith(dest) for c in jeu):
                        raise SystemExit(f"{dest} : chemin présent dans WH3")
                else:
                    dest = base if not any(c.startswith(base) for c in jeu) else base.replace("terrain/", "terrain/_wh1/", 1)
                bases[base] = dest
                for c, octets in textures(wh1, base).items():
                    fichiers[dest + c[len(base):]] = octets
            if bases[base] != base:
                brut = remplacer_base(brut, base, bases[base], barre="/" if TEXTURES_OBJET else "\\")
        drape, y0 = draper(brut, p, lf, R.PAS)
        drape = lod_fin_partout(drape)
        modele = f"{DOSSIER_MODELES}/{p.famille}/{p.nom.rstrip('/').rsplit('/', 1)[1]}_pose{p.k}.rigid_model_v2"
        if modele in jeu:
            raise SystemExit(f"{modele} existe dans WH3")
        fichiers[modele] = drape
        x, z, ry = transformation(p)
        entites.append(entite(ident(f"montagne:{p.k}"), modele, x, y0, z, ry))
    print(f"{len(liste)} poses ; {len(bases)} jeux de textures ({sum(1 for b, d in bases.items() if b != d)} déplacés "
          f"sous {DOSSIER_TEXTURES if TEXTURES_OBJET else '_wh1'}) ; {len(fichiers)} fichiers, "
          f"{sum(len(v) for v in fichiers.values()) / 1e6:.1f} Mo")
    if ecrire:
        if choisies is None and os.path.isdir(SORTIE):
            shutil.rmtree(SORTIE)                        # sortie régénérée en entier : pas de fichier périmé dans le pack
        for racine in (SORTIE, KIT_WD):
            for c, octets in fichiers.items():
                chemin = os.path.join(racine, *c.split("/"))
                os.makedirs(os.path.dirname(chemin), exist_ok=True)
                with open(chemin, "wb") as f:
                    f.write(octets)
        print(f"écrits dans {SORTIE} et {KIT_WD}")
    return entites, fichiers


def essai(indices):
    """Calque d'essai `montagnes_wh1_essai` ajouté au projet Terry (projet sauvegardé d'abord)."""
    entites, _ = construire(indices, ecrire=True)
    terry = os.path.join(PROJET, f"{CARTE}.terry")
    dest = os.path.join(ATELIER, "05-journal", "terrain-backups", "terry-avant-montagnes-" + time.strftime("%Y%m%d-%H%M%S") + ".terry")
    shutil.copy(terry, dest)
    id_calque = ident("calque:montagnes_wh1_essai")
    calque = os.path.join(PROJET, f"{CARTE}.{id_calque}.layer")
    with open(calque, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- montagnes_wh1_essai -->\n<layer version="41">\n\t<entities>\n'
                + "".join(entites) + "\t</entities>\n\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
    t = open(terry, encoding="utf-8").read()
    if id_calque not in t:
        bloc = (f'      <entity id="{id_calque}" name="montagnes_wh1_essai">\n'
                '        <ECFileLayer export="true" bmd_export_type=""/>\n      </entity>\n')
        t = t.replace("    </data>\n  </pc>\n  <pc type=\"QTU::Terrain\">", bloc + "    </data>\n  </pc>\n  <pc type=\"QTU::Terrain\">", 1)
        if id_calque not in t:
            raise SystemExit("point d'insertion du calque introuvable dans le .terry")
        with open(terry, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
    print(f"calque d'essai : {calque} ; .terry sauvegardé dans {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", help="indices de poses (dans la liste des montagnes) séparés par des virgules")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.essai:
        essai([int(i) for i in a.essai.split(",")])
    else:
        construire()
    return 0


if __name__ == "__main__":
    sys.exit(main())
