#!/usr/bin/env python3
"""
audit_objets.py - combien d'objets volent dans le projet Terry écrit (erreur 81 : mesurer le résultat, pas le bilan).

Relit sur disque les calques `.layer` du projet (modèle, position, rotation, échelle, masque de culture) et le relief
écrit (`*.height.*.tif`) ; pour chaque objet (hors décalques et hors calque des montagnes), point le plus bas de ses
sommets (LOD 0, `sommets_rmv2`) moins le sol sous ce point. Un objet porté par un autre (colline modelée, plateforme)
compte comme volant ici : la liste des plus hauts permet de juger à l'image (caméra Terry collée).

Usage :
    python audit_objets.py            # bilan et les 25 plus hauts
"""

import glob
import math
import os
import re
import sys
from collections import Counter

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_wh1_vers_layers as PL                                  # noqa: E402
import sommets_rmv2                                                  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
PROJET = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain\campaigns\wh_dlc05_wood_elves_map_1"
LARGEUR_MONDE = 266.53
SEUILS = (0.05, 0.2, 0.5, 1.0)


def rot(axe, t):
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
            "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axe]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tif = [f for f in os.listdir(PROJET) if ".height." in f and f.endswith(".tif")][0]
    sol = np.array(Image.open(os.path.join(PROJET, tif)), np.float64)
    H, L = sol.shape
    # en mer, le sol visible est le fond (`sea_height`), là où `tile_map.png` déclare la mer (4 px par case)
    fond = np.array(Image.open(os.path.join(PROJET, [f for f in os.listdir(PROJET) if ".sea_height." in f][0])), np.float64)
    tm = np.array(Image.open(os.path.join(PROJET, "tile_map.png")).convert("RGB"))
    mer = np.all(tm == (83, 141, 213), axis=-1)
    mer = np.repeat(np.repeat(mer, 4, 0), 4, 1)[:H, :L]
    sol = np.where(mer, fond, sol)
    pas = L / LARGEUR_MONDE

    def sous(xs, zs):
        cx = np.clip(xs * pas - 0.5, 0, L - 1.001)
        cy = np.clip((H - 1.5) - zs * PL.Z_VERS_RASTER * pas, 0, H - 1.001)      # monde (espace hex) -> raster
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        return (sol[r0, c0] * (1 - fx) * (1 - fy) + sol[r0, c0 + 1] * fx * (1 - fy)
                + sol[r0 + 1, c0] * (1 - fx) * fy + sol[r0 + 1, c0 + 1] * fx * fy)

    boites = PL.Boites()
    geo = {}

    def geometrie(c):
        if c not in geo:
            b = boites._octets(c.replace("\\", "/").lower())
            if b and c.lower().endswith(".wsmodel"):
                m = re.search(rb"<geometry>([^<]+)</geometry>", b)
                b = boites._octets(m.group(1).decode().replace("\\", "/").lower()) if m else None
            geo[c] = sommets_rmv2.sommets(b) if b else None
        return geo[c]

    rows, sans = [], 0
    for f in glob.glob(os.path.join(PROJET, "*.layer")):
        t = open(f, encoding="utf-8").read()
        nom = re.search(r"<!-- (\S+) -->", t).group(1)
        if nom.startswith("montagnes_wh1"):
            continue
        for e in re.findall(r"<entity\b.*?</entity>", t, re.S):
            m = re.search(r'<ECMesh model_path="([^"]+)"', e)
            if not m:
                continue
            tr = re.search(r'<ECTransform position="([^"]+)" rotation="([^"]+)" scale="([^"]+)"', e)
            pos = np.array([float(v) for v in tr.group(1).split()])
            r = [float(v) for v in tr.group(2).split()]
            ech = [float(v) for v in tr.group(3).split()]
            masque = re.search(r'culture_mask="([^"]*)"', e).group(1)
            v = geometrie(m.group(1))
            if v is None or not len(v):
                sans += 1
                continue
            M = np.diag(ech) @ rot("x", -r[0]) @ rot("y", -r[1]) @ rot("z", -r[2])
            w = v @ M + pos
            d = w[:, 1] - sous(w[:, 0], w[:, 2])
            rows.append((float(d.min()), m.group(1), nom, pos, masque))
    g = np.array([x[0] for x in rows])
    print(f"{len(rows)} objets mesurés ({sans} sans géométrie lisible), relief {tif}")
    for s in SEUILS:
        print(f"  point le plus bas à plus de {s:.2f} au-dessus du sol : {int((g > s).sum()):6d} ({(g > s).mean():.1%})")
    fam = lambda c: re.sub(r"_?\d+$", "", c.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    vol = [x for x in rows if x[0] > 0.05]
    print("  au-dessus du sol, par famille :", Counter(fam(x[1]) for x in vol).most_common(20))
    print("  les 25 plus hauts (hauteur au-dessus du sol, modèle, région, position) :")
    for x in sorted(vol, key=lambda x: -x[0])[:25]:
        print(f"     {x[0]:+.2f}  {x[1].rsplit('/', 1)[-1]:40} {x[2]:40} ({x[3][0]:.2f}, {x[3][1]:.2f}, {x[3][2]:.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
