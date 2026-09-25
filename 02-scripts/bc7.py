#!/usr/bin/env python3
"""
bc7.py - encodeur BC7 (mode 6) en numpy, pour produire des textures au format exact de celles de Warhammer 3
(`_base_colour` en BC7 sRGB, `_material_map` en BC7), sans outil extérieur (22.09.2026 ; aucun encodeur BC7
n'est installé et rien n'est téléchargé sans l'accord de Charles).

Mode 6 : un seul sous-ensemble, extrémités RGBA sur 7 bits + un bit P par extrémité, 16 indices de 4 bits (le
premier, « ancre », sur 3 bits). Choix des extrémités : axe principal (itérations de puissance), puis deux
passes de moindres carrés sur les indices choisis ; bit P et arrondi choisis au mieux par extrémité.
Qualité suffisante pour des textures de sol (contrôle : PSNR mesuré par `controle()`).

Usage (module) :
    blocs = encoder(rgba)            # rgba : uint8 (h, w, 4), h et w multiples de 4 -> bytes (16 par bloc)
    dds = dds_bc7(niveaux, srgb=True)  # niveaux : liste d'images uint8 (h, w, 4), de la plus grande à 1 x 1
"""

import io
import struct
import sys

import numpy as np

POIDS = np.array([0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64], np.float64)


def _blocs(rgba):
    h, w, _ = rgba.shape
    return rgba.reshape(h // 4, 4, w // 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 4).astype(np.float64)


def _quantifier(e):
    """Extrémité flottante (n, 4) -> (valeur 8 bits reconstruite (n, 4), q 7 bits (n, 4), p (n,))."""
    meilleurs = None
    for p in (0, 1):
        q = np.clip(np.round((e - p) / 2.0), 0, 127)
        v = 2 * q + p
        err = ((v - e) ** 2).sum(1)
        if meilleurs is None:
            meilleurs = [v, q, np.full(len(e), p), err]
        else:
            m = err < meilleurs[3]
            meilleurs[0][m] = v[m]; meilleurs[1][m] = q[m]; meilleurs[2][m] = p; meilleurs[3][m] = err[m]
    return meilleurs[0], meilleurs[1].astype(np.int64), meilleurs[2].astype(np.int64)


def _indices(x, v0, v1):
    pal = ((64 - POIDS)[None, :, None] * v0[:, None, :] + POIDS[None, :, None] * v1[:, None, :] + 32) // 64
    d = ((x[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(3)       # (n, 16 pixels, 16 entrées)
    return d.argmin(2), d.min(2).sum(1)


def _encoder_blocs(x):
    n = len(x)
    mu = x.mean(1)
    c = x - mu[:, None, :]
    cov = np.einsum("npi,npj->nij", c, c)
    v = np.ones((n, 4)) / 2.0
    for _ in range(8):
        v = np.einsum("nij,nj->ni", cov, v)
        v /= np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
    t = np.einsum("npi,ni->np", c, v)
    e0 = np.clip(mu + t.min(1)[:, None] * v, 0, 255)
    e1 = np.clip(mu + t.max(1)[:, None] * v, 0, 255)
    for passe in range(3):
        v0, q0, p0 = _quantifier(e0)
        v1, q1, p1 = _quantifier(e1)
        idx, err = _indices(x, v0, v1)
        if passe == 2:
            break
        # moindres carrés : x = (1 - a) e0 + a e1, a = poids / 64
        a = POIDS[idx] / 64.0
        s00 = ((1 - a) ** 2).sum(1); s01 = ((1 - a) * a).sum(1); s11 = (a ** 2).sum(1)
        b0 = np.einsum("np,npc->nc", 1 - a, x); b1 = np.einsum("np,npc->nc", a, x)
        det = s00 * s11 - s01 ** 2
        ok = np.abs(det) > 1e-9
        ne0 = np.where(ok[:, None], (s11[:, None] * b0 - s01[:, None] * b1) / np.where(ok, det, 1)[:, None], e0)
        ne1 = np.where(ok[:, None], (s00[:, None] * b1 - s01[:, None] * b0) / np.where(ok, det, 1)[:, None], e1)
        e0, e1 = np.clip(ne0, 0, 255), np.clip(ne1, 0, 255)
    # ancre : l'indice du pixel 0 doit avoir son bit de poids fort à 0
    inv = idx[:, 0] >= 8
    q0, q1 = np.where(inv[:, None], q1, q0), np.where(inv[:, None], q0, q1)
    p0, p1 = np.where(inv, p1, p0), np.where(inv, p0, p1)
    idx = np.where(inv[:, None], 15 - idx, idx)
    # empaquetage : 128 bits, bit de poids faible d'abord
    lo = np.full(n, 1 << 6, np.uint64)                                     # mode 6
    pos = 7
    for canal in range(4):
        for q in (q0, q1):
            lo |= (q[:, canal].astype(np.uint64) << np.uint64(pos))
            pos += 7
    lo |= (p0.astype(np.uint64) << np.uint64(63))
    hi = p1.astype(np.uint64)
    hi |= (idx[:, 0].astype(np.uint64) << np.uint64(1))
    pos = 4
    for k in range(1, 16):
        hi |= (idx[:, k].astype(np.uint64) << np.uint64(pos))
        pos += 4
    out = np.empty((n, 2), np.uint64)
    out[:, 0], out[:, 1] = lo, hi
    return out.astype("<u8").tobytes()


def encoder(rgba, par=16384):
    x = _blocs(np.ascontiguousarray(rgba))
    return b"".join(_encoder_blocs(x[i:i + par]) for i in range(0, len(x), par))


def reduire(rgba):
    """Niveau suivant : moyenne 2 x 2 (image de côté pair, ou 1)."""
    h, w, _ = rgba.shape
    if h == 1 and w == 1:
        return None
    a = rgba.astype(np.float64)
    if h > 1:
        a = (a[0::2] + a[1::2]) / 2
    if w > 1:
        a = (a[:, 0::2] + a[:, 1::2]) / 2
    return np.clip(np.round(a), 0, 255).astype(np.uint8)


def chaine(rgba):
    niveaux = [rgba]
    while True:
        s = reduire(niveaux[-1])
        if s is None:
            return niveaux
        niveaux.append(s)


def _bloc4(img):
    """Image de moins de 4 px de côté : complétée par répétition des bords jusqu'à 4 x 4."""
    h, w, _ = img.shape
    if h >= 4 and w >= 4:
        return img
    return np.pad(img, ((0, max(0, 4 - h)), (0, max(0, 4 - w)), (0, 0)), mode="edge")


def dds_bc7(niveaux, srgb):
    """Fichier DDS (en-tête DX10 comme ceux de CA : drapeaux 0xA1007, profondeur 1, caps 0x401008)."""
    h, w, _ = niveaux[0].shape
    tete = bytearray(128)
    tete[0:4] = b"DDS "
    struct.pack_into("<7I", tete, 4, 124, 0xA1007, h, w, (w // 4) * (h // 4) * 16, 1, len(niveaux))
    struct.pack_into("<II", tete, 76, 32, 0x4)
    tete[84:88] = b"DX10"
    struct.pack_into("<I", tete, 108, 0x401008)
    dx10 = struct.pack("<5I", 99 if srgb else 98, 3, 0, 1, 0)
    return bytes(tete) + dx10 + b"".join(encoder(_bloc4(n)) for n in niveaux)


def controle(rgba):
    """PSNR (dB) de l'encodage d'une image, décodée par Pillow."""
    from PIL import Image
    d = dds_bc7([rgba], srgb=False)
    b = Image.open(io.BytesIO(d)).convert("RGBA")
    r = np.array(b).astype(np.float64)
    mse = ((r - rgba.astype(np.float64)) ** 2).mean()
    return 10 * np.log10(255 ** 2 / max(mse, 1e-9))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rng = np.random.default_rng(0)
    y, x = np.mgrid[0:64, 0:64]
    test = np.stack([(x * 4) % 256, (y * 4) % 256, ((x + y) * 2) % 256, np.full_like(x, 255)], -1).astype(np.uint8)
    print(f"dégradé : PSNR {controle(test):.1f} dB")
