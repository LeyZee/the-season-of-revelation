#!/usr/bin/env python3
"""
sommets_rmv2.py - positions des sommets du LOD 0 d'un modèle RMV2 (v7 de WH1, v8 de WH3), pour poser un objet sur le sol
au sommet près (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\objets-zones-de-tuiles.md` § 8).

Format relevé sur nos modèles :
- en-tête de fichier de 140 octets, puis une entrée de 20 octets par LOD : u32 nombre de maillages, u32 taille, u32
  décalage du premier maillage, ... (le premier maillage du LOD 0 commence à l'octet 152 lu en u32 : c'est le 3e champ
  de la 1re entrée) ;
- en-tête de maillage : u16 matériau, u16, u32 taille du maillage, u32 décalage des sommets, u32 nombre de sommets,
  u32 décalage des indices, u32 nombre d'indices (décalages relatifs au début du maillage) ; boîte englobante à +24 ;
- sommet : position en tête, 4 demi-flottants (x, y, z, w) pour les pas de 8, 20, 28, 32 octets (feuillage 97,
  objets 68, terrain de tuile 96...), 3 flottants pour les pas de 36 et plus (maillages propres des tuiles) ;
  **en demi-flottants, la position est relative au centre de la boîte englobante du maillage** (vérifié : colline
  modelée, sommets de −0,529 à +0,529 en y, boîte de −0,249 à 0,809 ; arbre de −1,778 à +1,778, boîte de 0 à 3,556) :
  on lui ajoute ce centre ;
- **en v8 (WH3), la position en demi-flottants vaut (x, y, z) × w** (w de 1 à 2 ; en v7, w = 1) : vérifié le
  22.09.2026 sur la pierre de lien `wef_waystone01`, présente dans les deux jeux (mêmes 202 sommets, dans un autre
  ordre : x·w, y·w, z·w de WH3 = x, y, z de WH1 à 5e-4 près).
Les maillages suivants du LOD 0 se suivent : le suivant commence à décalage + taille.

Usage (module) :
    v = sommets(octets)       # tableau (n, 3) float64, ou None si le format n'est pas reconnu
"""

import struct

import numpy as np


def sommets(octets, max_maillages=16):
    r = maillage(octets, max_maillages)
    return None if r is None else r[0]


def maillage(octets, max_maillages=16):
    """(sommets (n, 3), triangles (m, 3) d'indices dans ces sommets) du LOD 0, ou None. Les sommets non finis sont
    retirés avec les triangles qui les emploient."""
    if not octets or octets[:4] != b"RMV2" or len(octets) < 160:
        return None
    version = struct.unpack_from("<I", octets, 4)[0]
    nb = struct.unpack_from("<I", octets, 140)[0]
    off = struct.unpack_from("<I", octets, 152)[0]
    tout, demi, boite, tris, base = [], [], None, [], 0
    boites_m = {}
    for _ in range(min(max(nb, 1), max_maillages)):
        if off + 24 > len(octets):
            break
        taille, voff, vcount, ioff, icount = struct.unpack_from("<IIIII", octets, off + 4)
        if vcount == 0 or ioff <= voff:
            break
        pas = (ioff - voff) // vcount
        debut = off + voff
        if debut + vcount * pas > len(octets):
            break
        brut = np.frombuffer(octets, np.uint8, count=vcount * pas, offset=debut).reshape(vcount, pas)
        if pas in (8, 20, 28, 32):
            q = brut[:, :8].copy().view("<f2").reshape(vcount, 4).astype(np.float64)
            p = q[:, :3] * q[:, 3:4] if version >= 8 else q[:, :3]
            demi.append(len(tout))
            boites_m[len(tout)] = np.frombuffer(octets, "<f4", count=6, offset=off + 24).astype(np.float64)
            if boite is None:
                boite = boites_m[len(tout)]
        elif pas >= 36:
            p = brut[:, :12].copy().view("<f4").reshape(vcount, 3).astype(np.float64)
        else:
            break
        tout.append(p)
        fin = off + ioff + 2 * icount
        if icount >= 3 and fin <= len(octets):
            t = np.frombuffer(octets, "<u2", count=icount - icount % 3, offset=off + ioff).reshape(-1, 3).astype(np.int64)
            t = t[(t < vcount).all(1)]
            tris.append(t + base)
        base += vcount
        if taille == 0:
            break
        off += taille
    if not tout:
        return None
    def centre_sur(v, bx):
        ext_v, ext_b = v.max(0) - v.min(0), bx[3:] - bx[:3]
        tol = 0.02 + 0.01 * np.abs(ext_b)
        return np.all(np.abs(ext_v - ext_b) < tol) and np.all(np.abs((v.max(0) + v.min(0)) / 2) < tol)

    if demi and boite is not None:
        # le centrage vaut en général pour le modèle entier : l'union des sommets en demi-flottants a l'étendue de la
        # boîte (commune à tous les maillages) et son milieu en 0. Les « prefab_as_mesh » de WH1 (idoles peaux-vertes,
        # 8 et 9 morceaux) centrent au contraire chaque maillage sur SA boîte : lus sans ce centrage, leurs sommets
        # restaient autour de 0 (y de -1,03 à 1,03 pour une boîte de -0,20 à 3,99 ; 23.09.2026, erreur 101)
        u = np.concatenate([tout[i] for i in demi])
        if centre_sur(u, boite):
            centre = (boite[:3] + boite[3:]) / 2
            for i in demi:
                tout[i] = tout[i] + centre
        else:
            for i in demi:
                if centre_sur(tout[i], boites_m[i]):
                    tout[i] = tout[i] + (boites_m[i][:3] + boites_m[i][3:]) / 2
    v = np.concatenate(tout)
    t = np.concatenate(tris) if tris else np.zeros((0, 3), np.int64)
    fini = np.isfinite(v).all(1)
    if not fini.all():
        nouveau = np.cumsum(fini) - 1
        t = nouveau[t[fini[t].all(1)]]
        v = v[fini]
    return v, t


def surface_sous(v, t, x, z):
    """Hauteur du dessus du maillage (sommets v déjà placés, triangles t) à la verticale de (x, z) : maximum des
    triangles qui contiennent le point en projection horizontale ; None si aucun."""
    if not len(t):
        return None
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    x0, z0, x1, z1, x2, z2 = a[:, 0], a[:, 2], b[:, 0], b[:, 2], c[:, 0], c[:, 2]
    det = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2)
    ok = np.abs(det) > 1e-12
    with np.errstate(divide="ignore", invalid="ignore"):          # triangles verticaux : det nul, écartés par `ok`
        l0 = ((z1 - z2) * (x - x2) + (x2 - x1) * (z - z2)) / det
        l1 = ((z2 - z0) * (x - x2) + (x0 - x2) * (z - z2)) / det
        l2 = 1 - l0 - l1
        dedans = ok & (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not dedans.any():
            return None
        return float((l0 * a[:, 1] + l1 * b[:, 1] + l2 * c[:, 1])[dedans].max())


CELLULE_CONTACT = 0.04
_DECALAGES = np.array([dx + (dy << 21) + (dz << 42) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)],
                      np.int64)


def echantillons(w, t, lo, hi, cellule=CELLULE_CONTACT, subdiv_max=64):
    """Points des triangles de (w, t) qui recoupent la boîte [lo, hi], au pas `cellule`, gardés dans la boîte."""
    if not len(t):
        p = w
    else:
        a, b, c = w[t[:, 0]], w[t[:, 1]], w[t[:, 2]]
        tlo, thi = np.minimum(np.minimum(a, b), c), np.maximum(np.maximum(a, b), c)
        k = np.all(thi >= lo, 1) & np.all(tlo <= hi, 1)
        a, b, c = a[k], b[k], c[k]
        if not len(a):
            return np.zeros((0, 3))
        cote = np.maximum(np.maximum(np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1)),
                          np.linalg.norm(a - c, axis=1))
        n = np.clip(np.ceil(cote / cellule).astype(int), 1, subdiv_max)
        morceaux = [w[np.unique(t[k].ravel())]]
        for nn in np.unique(n):
            s = n == nn
            ii, jj = np.meshgrid(np.arange(nn + 1), np.arange(nn + 1), indexing="ij")
            g = (ii + jj) <= nn
            u, v = ii[g] / nn, jj[g] / nn
            pts = (a[s][:, None, :] * (1 - u - v)[None, :, None] + b[s][:, None, :] * u[None, :, None]
                   + c[s][:, None, :] * v[None, :, None])
            morceaux.append(pts.reshape(-1, 3))
        p = np.concatenate(morceaux)
    return p[np.all((p >= lo) & (p <= hi), 1)]


def _cles(p, cellule):
    q = np.floor(p / cellule).astype(np.int64) + (1 << 20)
    return q[:, 0] + (q[:, 1] << 21) + (q[:, 2] << 42)


def se_touchent(wi, ti, wj, tj, cellule=CELLULE_CONTACT):
    """Les surfaces de deux maillages placés (sommets, triangles) passent-elles à moins d'une cellule l'une de l'autre ?
    Échantillonnage des triangles au pas `cellule` dans la boîte commune (22.09.2026, 23 h : les boîtes qui se recoupent
    « accrochaient » à un voisin des objets qui, dans WH1, flottaient à côté de lui)."""
    lo = np.maximum(wi.min(0), wj.min(0)) - cellule
    hi = np.minimum(wi.max(0), wj.max(0)) + cellule
    if np.any(lo > hi):
        return False
    pi, pj = echantillons(wi, ti, lo, hi, cellule), echantillons(wj, tj, lo, hi, cellule)
    if not len(pi) or not len(pj):
        return False
    ki = np.unique(_cles(pi, cellule))
    return bool(np.isin(_cles(pj, cellule), np.unique((ki[:, None] + _DECALAGES[None, :]).ravel())).any())


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for chemin in sys.argv[1:]:
        v = sommets(open(chemin, "rb").read())
        print(chemin, None if v is None else (v.shape, v.min(0).round(3).tolist(), v.max(0).round(3).tolist()))
