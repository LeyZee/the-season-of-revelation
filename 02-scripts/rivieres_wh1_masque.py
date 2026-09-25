#!/usr/bin/env python3
"""
rivieres_wh1_masque.py - PREMIÈRE VERSION de `rivieres_wh1.py` (22.09.2026, 20 h 19), écrasée par erreur le 23.09.2026 à
00 h 50 par la seconde (maillages d'eau drapés) et restaurée depuis l'historique des fichiers de Claude Code sous ce
nom : elle garde le masque des rubans (`blend0.dds`) et la règle de pose établie sur 1 974 bords de tuiles.

rivieres_wh1.py - les rivières de Warhammer 1, à leur place exacte, dans notre carte de Warhammer 3.

Pourquoi (22.09.2026, 21 h ; Charles : « le réseau de rivières de WH1, attaque ça » ; journal
`05-journal\\2026-09-22-phase-4\\rivieres-wh1.md`). WH1 dessinait ses rivières avec des **tuiles** (familles river,
river_stream, river_start, river_mouth, river_confluence, river_crossing : 1 399 poses) dont le mélange local
`blend0.dds` porte le ruban de la rivière ; leur relief propre est presque nul (grille hf de -2 à +4 unités locales,
0,0026 unité du monde par unité locale) : le lit vient du relief de base, que nous avons. CA ne pose aucune tuile de
rivière dans ses cartes de WH3 (listes compilées des Empires, du Chaos, du prologue) : ses rivières sont du relief,
des textures et des surfaces d'eau planes (`ECPolygonMesh`, matériau d'eau).

Pose des tuiles de WH1 (établie le 22.09.2026 sur 1 974 bords communs de tuiles de rivière et sur les trous du
maillage de terrain de WH1) :
- emprise : coin sud-ouest (x, y) de la pose, W x H cases vers l'est et le nord (0x20 et 0x80 échangent W et H) ;
  le maillage de terrain de WH1 est troué à 81 % dans l'emprise contre 31 % autour ;
- `blend0.dds` : 32 px par case, marge d'une case tout autour (128 px pour une 2 x 2), ligne 0 au sud ;
- code 0x10 : 0° ; 0x20 : 90° ; 0x40 : 180° ; 0x80 : 270° (en symétries de l'image, ligne 0 au nord : retournement
  vertical, transposition, retournement horizontal, anti-transposition) ; bit 0x04 (rivières seulement, 29 % des
  poses) : miroir local sur x avant la rotation ;
- le canal du ruban varie d'une tuile à l'autre (G pour la plupart, B pour d'autres) : c'est celui qui touche au
  plus trois bords de la tuile (entrée, sortie, confluence) sans couvrir le fond.

Usage (module, appelé par `terrain_wh1_vers_terry.py`) :
    riv = Rivieres()                    # lit les tuiles de WH1
    masque = riv.masque(px_par_case)    # raster monde (ligne 0 au nord), 0..1
    for pose in riv.poses: pose.masque32, pose.r0, pose.c0 ...
    python rivieres_wh1.py              # contrôle : image du réseau
"""

import io
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tuiles_wh1 as T                                              # noqa: E402

FAMILLES = ("river", "river_stream", "river_start", "river_mouth", "river_confluence", "river_crossing")
PX_TUILE = 32                       # px par case dans blend0.dds
SYMETRIE = {0x10: 6, 0x20: 7, 0x40: 4, 0x80: 5}
BIT_MIROIR = 0x04


def symetrie(a, k):
    r = np.rot90(a, k % 4)
    return r[:, ::-1] if k >= 4 else r


def canal_du_ruban(a):
    """Canal (0-3) du ruban de rivière d'un blend0 rogné (h, w, 4) en 0..1, ou None."""
    best, bc = None, -1.0
    for c in range(4):
        m = a[..., c]
        if not 0.01 < m.mean() < 0.6:
            continue
        cotes = [m[:, 0].mean(), m[:, -1].mean(), m[0, :].mean(), m[-1, :].mean()]
        touches = sum(v > 0.05 for v in cotes)
        if touches == 4 and min(cotes) > 0.5:          # le fond touche tout
            continue
        s = sorted(cotes, reverse=True)[1] * (1 if touches <= 3 else 0.5)
        if s > bc:
            best, bc = c, s
    return best


class Pose:
    __slots__ = ("x", "y", "code", "idx", "famille", "W", "H", "r0", "c0", "masque32")


class Rivieres:
    def __init__(self, wh1=None):
        if wh1 is None:
            from modeles_wh1 import SourceWH1
            wh1 = SourceWH1()
        noms, poses = T.lire()
        rubans = {}
        self.poses = []
        self.sans_ruban = 0
        for x, y, code, _clim, _k, idx, _e in poses:
            fam = T.famille(noms[idx])
            if fam not in FAMILLES:
                continue
            if idx not in rubans:
                b = wh1.lire(noms[idx].replace("\\", "/").lower() + "blend0.dds")
                a = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))[PX_TUILE:-PX_TUILE, PX_TUILE:-PX_TUILE]
                a = a.astype(np.float32) / 255
                c = canal_du_ruban(a)
                rubans[idx] = a[..., c] if c is not None else None
            m = rubans[idx]
            if m is None:
                self.sans_ruban += 1
                continue
            W, H = T.taille(noms[idx])
            rot = code & 0xF0
            if rot in (0x20, 0x80):
                W, H = H, W
            if code & BIT_MIROIR:
                m = m[:, ::-1]
            m = symetrie(m, SYMETRIE[rot])
            if m.shape != (H * PX_TUILE, W * PX_TUILE):
                raise SystemExit(f"{noms[idx]} code {code:#x} : ruban {m.shape}, emprise {H} x {W} cases")
            p = Pose()
            p.x, p.y, p.code, p.idx, p.famille = x, y, code, idx, fam
            p.W, p.H = W, H
            p.r0, p.c0 = T.HAUTEUR - (y + H), x                  # cases, ligne 0 au nord
            p.masque32 = np.ascontiguousarray(m)
            self.poses.append(p)

    def masque(self, px_par_case):
        """Raster monde (T.HAUTEUR x T.LARGEUR cases, `px_par_case` px par case, ligne 0 au nord) : ruban 0..1."""
        f = PX_TUILE // px_par_case
        if f * px_par_case != PX_TUILE:
            raise ValueError("px_par_case doit diviser 32")
        out = np.zeros((T.HAUTEUR * px_par_case, T.LARGEUR * px_par_case), np.float32)
        for p in self.poses:
            m = p.masque32.reshape(p.H * px_par_case, f, p.W * px_par_case, f).mean(axis=(1, 3))
            r0, c0 = p.r0 * px_par_case, p.c0 * px_par_case
            zone = out[r0:r0 + m.shape[0], c0:c0 + m.shape[1]]
            np.maximum(zone, m[:zone.shape[0], :zone.shape[1]], out=zone)
        return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    riv = Rivieres()
    print(f"{len(riv.poses)} poses de rivière avec ruban ; {riv.sans_ruban} sans ruban détecté")
    m = riv.masque(8)
    print(f"masque 8 px / case : {m.shape}, eau (> 0,5) {int((m > 0.5).sum())} px")
    ici = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "04-projets", "saison-des-revelations", "terrain-controle")
    os.makedirs(ici, exist_ok=True)
    Image.fromarray((m[::2, ::2] * 255).astype(np.uint8)).save(os.path.join(ici, "rivieres_wh1.png"))
