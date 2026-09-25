#!/usr/bin/env python3
"""
relief_maillages_wh1.py - le vrai sol de Warhammer 1, tiré de ses maillages de terrain, dans la grille de notre
relief (3200 x 3524, nord en haut, 12,01 px par unité).

Pourquoi (22.09.2026, 16 h, capture de Charles dans Terry : « plein de trucs flottants, des pics ») : notre
relief venait de `lf_height_map.dds` de WH1, étalonné sur les sommets des maillages avec un écart moyen de
0,383 (journal `2026-09-21-phase-3-terrain\\terrain.md` § 2). WH1 dessine son sol avec
`global_meshes\\land_mesh_N.rigid_model_v2` (72 morceaux de 36,65 unités, RMV2 v7, sommets x, y, z + 4
octets, indices u16) ; ses objets ont été posés sur ce sol-là. Là où les deux surfaces diffèrent (montagnes,
falaises : les tuiles de WH1), nos rochers flottent ou sortent en pointes.

Ce script rastérise les triangles des maillages (hauteur maximale par pixel : le dessus d'une falaise
l'emporte), aux centres des pixels de notre grille, puis compare aux objets de WH1 (`global_props.bin`) :
écart de hauteur objet / sol, pour notre ancien relief et pour celui des maillages.

Sorties (`--apply`) : `04-projets\\saison-des-revelations\\relief-wh1\\relief_maillages.npy` (float32, NaN
hors maillages), `mer_maillages.npy` (fond marin des `sea_mesh_N`), images de contrôle.

Usage :
    python relief_maillages_wh1.py            # rastérise et mesure, n'écrit que les images de contrôle
    python relief_maillages_wh1.py --apply    # écrit aussi les .npy que terrain_wh1_vers_terry.py lit
"""

import argparse
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ATELIER = r"C:\TotalWar-CampaignMap"
WH1 = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns",
                   "wh_dlc05_wood_elves_map_1")
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1")
H, L = 3524, 3200
PAS = L / 266.53                                   # px par unité (même calage que le 21.09.2026)
A_HAUTEUR, B_HAUTEUR = 0.0002185272, -0.753375     # lf_height_map.dds -> unités


def lire_maillage(chemin):
    """Sommets (n, 3) et triangles (m, 3) du premier maillage du LOD 0 d'un RMV2 de terrain de WH1."""
    b = open(chemin, "rb").read()
    first = struct.unpack_from("<I", b, 152)[0]
    typ, flag, taille, voff, vcount, ioff, icount = struct.unpack_from("<HHIIIII", b, first)
    pas_sommet = (ioff - voff) // vcount
    if pas_sommet != 16:
        raise ValueError(f"{chemin} : {pas_sommet} octets par sommet, 16 attendus")
    v = np.frombuffer(b, "<f4", count=vcount * 4, offset=first + voff).reshape(vcount, 4)[:, :3]
    t = np.frombuffer(b, "<u2", count=icount, offset=first + ioff).reshape(-1, 3)
    return v.astype(np.float64), t.astype(np.int64)


def rasteriser(sommets, triangles, grille):
    """Hauteur maximale des triangles aux centres des pixels (np.fmax dans `grille`, NaN = rien)."""
    # coordonnées continues de pixel : colonne c a son centre en x = (c + 0,5) / PAS ; ligne r en
    # z = (H - 1,5 - r) / PAS (ligne = int(H - 1 - z * PAS), calage du 21.09.2026)
    cx = sommets[:, 0] * PAS - 0.5
    cy = (H - 1.5) - sommets[:, 2] * PAS
    rasteriser_px(cx, cy, sommets[:, 1], triangles, grille)


def rasteriser_px(cx, cy, hy, triangles, grille):
    """Idem, sommets déjà en coordonnées continues de pixel de `grille` (centre du pixel c en c)."""
    H, L = grille.shape
    x0, x1, x2 = cx[triangles[:, 0]], cx[triangles[:, 1]], cx[triangles[:, 2]]
    y0, y1, y2 = cy[triangles[:, 0]], cy[triangles[:, 1]], cy[triangles[:, 2]]
    h0, h1, h2 = hy[triangles[:, 0]], hy[triangles[:, 1]], hy[triangles[:, 2]]
    det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    ok = np.abs(det) > 1e-12                          # triangles verticaux (parois) : sans surface vue de dessus
    cmin = np.floor(np.minimum(np.minimum(x0, x1), x2)).astype(np.int64)
    cmax = np.ceil(np.maximum(np.maximum(x0, x1), x2)).astype(np.int64)
    rmin = np.floor(np.minimum(np.minimum(y0, y1), y2)).astype(np.int64)
    rmax = np.ceil(np.maximum(np.maximum(y0, y1), y2)).astype(np.int64)
    taille = np.maximum(cmax - cmin, rmax - rmin) + 1
    for borne in (4, 8, 16, 32, 64, 10 ** 9):
        sel = np.nonzero(ok & (taille <= borne) & (taille > borne // 2 if borne > 4 else True))[0]
        if borne == 10 ** 9:
            sel = np.nonzero(ok & (taille > 64))[0]
        if len(sel) == 0:
            continue
        w = int(taille[sel].max())
        for debut in range(0, len(sel), max(1, 2_000_000 // (w * w))):
            s = sel[debut:debut + max(1, 2_000_000 // (w * w))]
            dc, dr = np.meshgrid(np.arange(w), np.arange(w))
            cc = cmin[s, None] + dc.ravel()[None, :]
            rr = rmin[s, None] + dr.ravel()[None, :]
            px, py = cc.astype(np.float64), rr.astype(np.float64)
            d = det[s, None]
            l0 = ((y1[s, None] - y2[s, None]) * (px - x2[s, None]) + (x2[s, None] - x1[s, None]) * (py - y2[s, None])) / d
            l1 = ((y2[s, None] - y0[s, None]) * (px - x2[s, None]) + (x0[s, None] - x2[s, None]) * (py - y2[s, None])) / d
            l2 = 1 - l0 - l1
            e = -1e-6
            dedans = (l0 >= e) & (l1 >= e) & (l2 >= e) & (cc >= 0) & (cc < L) & (rr >= 0) & (rr < H)
            h = l0 * h0[s, None] + l1 * h1[s, None] + l2 * h2[s, None]
            idx = rr[dedans] * L + cc[dedans]
            if idx.size == 0:
                continue
            plat = grille.ravel()
            # fmax par pixel (NaN = vide) : on trie par indice puis on garde le maximum de chaque groupe
            ordre = np.lexsort((h[dedans], idx))
            idx_o, h_o = idx[ordre], h[dedans][ordre]
            dernier = np.r_[idx_o[1:] != idx_o[:-1], True]
            plat[idx_o[dernier]] = np.fmax(plat[idx_o[dernier]], h_o[dernier])


def relief_lf():
    v = np.frombuffer(open(os.path.join(WH1, "lf_height_map.dds"), "rb").read(), "<u2", count=H * L,
                      offset=128).reshape(H, L).astype(np.float32)
    return A_HAUTEUR * v + B_HAUTEUR


def ecarts_objets(sol, nom):
    """Écart hauteur de l'objet - sol sous l'objet, pour les objets de WH1 posés (hors décalques)."""
    import lire_props_wh1 as LP
    pts = []
    for _, _, _, var, blob in LP.lots(LP.GLOBAL_PROPS):
        if var == 1:
            pts += [(o["position"], o["modele"]) for o in LP.objets(blob) if o["drapeaux"][0] == 0]
    p = np.array([q for q, _ in pts], np.float64)
    c = np.clip((p[:, 0] * PAS).astype(int), 0, L - 1)
    r = np.clip(((H - 1) - p[:, 2] * PAS).astype(int), 0, H - 1)
    s = sol[r, c]
    d = p[:, 1] - s
    ok = np.isfinite(d)
    q = np.percentile(d[ok], [5, 25, 50, 75, 95])
    print(f"   objets contre {nom:22}: n {ok.sum()} ; écart (objet - sol) p5/p25/p50/p75/p95 "
          f"{np.round(q, 3).tolist()} ; |écart| > 0,5 : {(np.abs(d[ok]) > 0.5).mean():.1%} ; > 1 : {(np.abs(d[ok]) > 1).mean():.1%}")
    return p, d, [m for _, m in pts]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(SORTIE, exist_ok=True)
    G = os.path.join(WH1, "global_meshes")
    terre = np.full((H, L), np.nan, np.float64)
    mer = np.full((H, L), np.nan, np.float64)
    nt = {"land": 0, "sea": 0}
    for n in sorted(os.listdir(G)):
        if not n.endswith(".rigid_model_v2"):
            continue
        v, t = lire_maillage(os.path.join(G, n))
        genre = "land" if n.startswith("land_mesh_") else "sea"
        nt[genre] += len(t)
        rasteriser(v, t, terre if genre == "land" else mer)
    print(f"triangles : terre {nt['land']}, mer {nt['sea']} ; pixels couverts : terre {np.isfinite(terre).mean():.1%}, "
          f"mer {np.isfinite(mer).mean():.1%}, l'un ou l'autre {(np.isfinite(terre) | np.isfinite(mer)).mean():.1%}")
    lf = relief_lf()
    both = np.isfinite(terre)
    d = terre[both] - lf[both]
    print(f"maillages - lf_height_map (terre) : p1/p5/p50/p95/p99 {np.round(np.percentile(d, [1, 5, 50, 95, 99]), 3).tolist()} ;"
          f" moyenne |d| {np.abs(d).mean():.3f} ; |d| > 1 : {(np.abs(d) > 1).mean():.2%}")
    ecarts_objets(lf, "lf_height_map")
    p, dd, modeles = ecarts_objets(np.where(np.isfinite(terre), terre, lf), "maillages de WH1")
    # images de contrôle : l'écart maillages - lf (bleu : maillage plus bas, rouge : plus haut)
    diff = np.where(both, terre - lf, 0)
    img = np.zeros((H, L, 3), np.uint8)
    img[..., 0] = np.clip(diff * 120, 0, 255)
    img[..., 2] = np.clip(-diff * 120, 0, 255)
    img[~both] = (40, 40, 40)
    Image.fromarray(img[::4, ::4]).save(os.path.join(SORTIE, "ecart_maillages_lf.png"))
    ombre = np.where(both, terre, lf)
    gy, gx = np.gradient(ombre[::2, ::2])
    Image.fromarray((np.clip(0.55 + 2.5 * (gx - gy), 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(SORTIE, "relief_maillages_ombre.png"))
    print(f"contrôles : {SORTIE}")
    if a.apply:
        np.save(os.path.join(SORTIE, "relief_maillages.npy"), terre.astype(np.float32))
        np.save(os.path.join(SORTIE, "mer_maillages.npy"), mer.astype(np.float32))
        print("écrit : relief_maillages.npy, mer_maillages.npy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
