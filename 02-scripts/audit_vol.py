#!/usr/bin/env python3
"""
audit_vol.py - les objets qui volent vraiment dans le projet Terry écrit : ni au sol, ni posés sur un objet, ni
accrochés à un objet qui, de proche en proche, touche le sol (22.09.2026, 23 h ; Charles : « il ne faut plus qu'il y ait
un seul truc qui vole »).

`audit_objets.py` compte comme volant tout objet dont le point le plus bas est au-dessus du sol, y compris une lanterne
pendue à une branche ou une pierre posée sur une autre : il surestime. Ici, mesuré sur les fichiers écrits :
- au sol : un sommet à moins de TOL_SOL au-dessus du sol affiché (relief ; fond en mer, d'après `tile_map.png`), ou
  sous le sol ;
- contact : les surfaces de deux objets (triangles échantillonnés au pas CELLULE) passent à moins d'une cellule l'une
  de l'autre ;
- tenu : relié au sol par une chaîne de contacts, chaque appui étant visible chaque fois que l'objet l'est (masques de
  culture : un appui masqué pour la culture de l'objet ne le tient pas) ; les montagnes de WH1 (`montagnes_wh1`) sont
  au sol par construction.
Le reste vole, en groupes d'objets qui se touchent, triés par hauteur. Les arbres de WH1 (liste embarquée dans le pack)
ne sont pas des objets de Terry : un groupe à moins de PRES_ARBRE d'un arbre est signalé (il peut y pendre, en jeu).

Usage :
    python audit_vol.py [--json sortie.json] [--liste 40]
"""

import argparse
import glob
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict, deque

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_wh1_vers_layers as PL                                  # noqa: E402
import sommets_rmv2                                                  # noqa: E402
from arbres_wh1 import SORTIE_LISTE, lire_liste                      # noqa: E402

Image.MAX_IMAGE_PIXELS = None
PROJET = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain\campaigns\wh_dlc05_wood_elves_map_1"
LARGEUR_MONDE = 266.53
TOL_SOL = 0.05
CELLULE = 0.04
MAILLE = 1.0                        # grille des emprises, unités
PRES_ARBRE = 0.6
SUBDIV_MAX = 64


def rot(axe, t):
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
            "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axe]


class Sol:
    """Sol affiché : relief, et fond marin là où `tile_map.png` déclare la mer (4 px de relief par case)."""

    def __init__(self):
        tif = [f for f in os.listdir(PROJET) if ".height." in f and f.endswith(".tif")][0]
        sol = np.array(Image.open(os.path.join(PROJET, tif)), np.float64)
        fond = np.array(Image.open(os.path.join(PROJET, [f for f in os.listdir(PROJET) if ".sea_height." in f][0])),
                        np.float64)
        tm = np.array(Image.open(os.path.join(PROJET, "tile_map.png")).convert("RGB"))
        mer = np.all(tm == (83, 141, 213), axis=-1)
        mer = np.repeat(np.repeat(mer, 4, 0), 4, 1)[:sol.shape[0], :sol.shape[1]]
        self.h = np.where(mer, fond, sol)
        self.H, self.L = self.h.shape
        self.pas = self.L / LARGEUR_MONDE
        self.nom = tif

    def sous(self, xs, zs):
        """Sol sous des points du monde (espace des hex : le raster se lit à z × √3/2, erreur 89)."""
        cx = np.clip(xs * self.pas - 0.5, 0, self.L - 1.001)
        cy = np.clip((self.H - 1.5) - zs * PL.Z_VERS_RASTER * self.pas, 0, self.H - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        h = self.h
        return (h[r0, c0] * (1 - fx) * (1 - fy) + h[r0, c0 + 1] * fx * (1 - fy)
                + h[r0 + 1, c0] * (1 - fx) * fy + h[r0 + 1, c0 + 1] * fx * fy)


def cultures(masque):
    return set(masque.split(",")) if masque else None       # None : toutes


def visible_avec(support, objet):
    """Le support est-il visible chaque fois que l'objet l'est ?"""
    cs, co = cultures(support), cultures(objet)
    return cs is None or (co is not None and co <= cs)


class Geometries:
    def __init__(self):
        self.boites = PL.Boites()
        self.cache = {}

    def maillage(self, chemin):
        c = chemin.replace("\\", "/").lower()
        if c not in self.cache:
            b = self.boites._octets(c)
            if b and c.endswith(".wsmodel"):
                m = re.search(rb"<geometry>([^<]+)</geometry>", b)
                b = self.boites._octets(m.group(1).decode().replace("\\", "/").lower()) if m else None
            r = sommets_rmv2.maillage(b) if b else None
            self.cache[c] = r if r is not None and len(r[0]) else None
        return self.cache[c]


def objets():
    """Entités `ECMesh` des calques écrits : (modèle, calque, position, matrice, masque, montagne)."""
    for f in sorted(glob.glob(os.path.join(PROJET, "*.layer"))):
        t = open(f, encoding="utf-8").read()
        nom = re.search(r"<!-- (\S+) -->", t).group(1)
        for e in re.findall(r"<entity\b.*?</entity>", t, re.S):
            m = re.search(r'<ECMesh model_path="([^"]+)"', e)
            if not m:
                continue
            tr = re.search(r'<ECTransform position="([^"]+)" rotation="([^"]+)" scale="([^"]+)"', e)
            pos = np.array([float(v) for v in tr.group(1).split()])
            r = [float(v) for v in tr.group(2).split()]
            ech = [float(v) for v in tr.group(3).split()]
            mq = re.search(r'culture_mask="([^"]*)"', e)
            yield {"modele": m.group(1), "calque": nom, "pos": pos,
                   "M": np.diag(ech) @ rot("x", -r[0]) @ rot("y", -r[1]) @ rot("z", -r[2]),
                   "masque": mq.group(1) if mq else "", "montagne": nom.startswith("montagnes_wh1")}


def contact(oi, oj, placer):
    if np.any(np.maximum(oi["lo"], oj["lo"]) - CELLULE > np.minimum(oi["hi"], oj["hi"]) + CELLULE):
        return False
    wi, ti = placer(oi)
    wj, tj = placer(oj)
    return sommets_rmv2.se_touchent(wi, ti, wj, tj, CELLULE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--liste", type=int, default=40)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sol = Sol()
    geo = Geometries()
    objs = []
    sans = 0
    for o in objets():
        g = geo.maillage(o["modele"])
        if g is None:
            sans += 1
            continue
        w = g[0] @ o["M"] + o["pos"]
        o["lo"], o["hi"] = w.min(0), w.max(0)
        if o["montagne"]:
            o["bas"], o["au_sol"] = 0.0, True
        else:
            d = w[:, 1] - sol.sous(w[:, 0], w[:, 2])
            o["bas"] = float(d.min())
            o["au_sol"] = o["bas"] <= TOL_SOL
        objs.append(o)

    def placer(o):
        g = geo.maillage(o["modele"])
        return g[0] @ o["M"] + o["pos"], g[1]

    grille = defaultdict(list)
    for i, o in enumerate(objs):
        for gx in range(int(o["lo"][0] // MAILLE), int(o["hi"][0] // MAILLE) + 1):
            for gz in range(int(o["lo"][2] // MAILLE), int(o["hi"][2] // MAILLE) + 1):
                grille[(gx, gz)].append(i)
    candidats = [i for i, o in enumerate(objs) if not o["au_sol"]]
    appuis = defaultdict(set)            # j -> {i} : j tient i
    touche = defaultdict(set)            # contacts sans condition de visibilité
    masques = 0
    for n, i in enumerate(candidats):
        oi = objs[i]
        vus = set()
        for gx in range(int(oi["lo"][0] // MAILLE), int(oi["hi"][0] // MAILLE) + 1):
            for gz in range(int(oi["lo"][2] // MAILLE), int(oi["hi"][2] // MAILLE) + 1):
                for j in grille[(gx, gz)]:
                    if j == i or j in vus:
                        continue
                    vus.add(j)
                    if contact(oi, objs[j], placer):
                        touche[i].add(j)
                        touche[j].add(i)
                        if visible_avec(objs[j]["masque"], oi["masque"]):
                            appuis[j].add(i)
                        else:
                            masques += 1
    tenu = [o["au_sol"] for o in objs]
    file = deque(i for i, o in enumerate(objs) if o["au_sol"])
    while file:
        j = file.popleft()
        for i in appuis.get(j, ()):
            if not tenu[i]:
                tenu[i] = True
                file.append(i)
    volants = [i for i in candidats if not tenu[i]]
    # groupes de volants qui se touchent
    groupe, groupes = {}, []
    ens = set(volants)
    for i in volants:
        if i in groupe:
            continue
        g, pile = [], [i]
        groupe[i] = len(groupes)
        while pile:
            k = pile.pop()
            g.append(k)
            for m in touche.get(k, ()):
                if m in ens and m not in groupe:
                    groupe[m] = len(groupes)
                    pile.append(m)
        groupes.append(g)
    # arbres de WH1 (liste du pack) : un groupe peut y pendre, en jeu
    arbres = []
    if os.path.exists(SORTIE_LISTE):
        _, gs = lire_liste(open(SORTIE_LISTE, "rb").read())
        for _, recs in gs:
            xyz = recs[:, :12].copy().view("<f4").reshape(-1, 3).astype(np.float64)
            arbres.append(np.c_[xyz[:, 0], xyz[:, 2]])          # la liste est en espace hex, comme les objets
    arbres = np.concatenate(arbres) if arbres else np.zeros((0, 2))
    grille_a = defaultdict(list)
    for k, (x, z) in enumerate(arbres):
        grille_a[(int(x // MAILLE), int(z // MAILLE))].append(k)

    def arbre_proche(lo, hi):
        best = None
        for gx in range(int((lo[0] - PRES_ARBRE) // MAILLE), int((hi[0] + PRES_ARBRE) // MAILLE) + 1):
            for gz in range(int((lo[2] - PRES_ARBRE) // MAILLE), int((hi[2] + PRES_ARBRE) // MAILLE) + 1):
                for k in grille_a.get((gx, gz), ()):
                    x, z = arbres[k]
                    dx = max(lo[0] - x, 0, x - hi[0])
                    dz = max(lo[2] - z, 0, z - hi[2])
                    d = math.hypot(dx, dz)
                    if best is None or d < best:
                        best = d
        return best

    fam = lambda c: re.sub(r"_?\d+$", "", c.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    rapport = []
    for g in groupes:
        lo = np.min([objs[i]["lo"] for i in g], 0)
        hi = np.max([objs[i]["hi"] for i in g], 0)
        bas = min(objs[i]["bas"] for i in g)
        pa = arbre_proche(lo, hi)
        rapport.append({"bas": round(bas, 3), "n": len(g), "centre": [round(float(v), 3) for v in (lo + hi) / 2],
                        "calque": objs[g[0]]["calque"], "arbre": None if pa is None else round(pa, 3),
                        "modeles": Counter(objs[i]["modele"].rsplit("/", 1)[-1] for i in g).most_common(6),
                        "objets": [{"modele": objs[i]["modele"], "pos": [round(float(v), 4) for v in objs[i]["pos"]],
                                    "bas": round(objs[i]["bas"], 3), "masque": objs[i]["masque"]} for i in g]})
    rapport.sort(key=lambda r: -r["bas"])
    pres = [r for r in rapport if r["arbre"] is not None and r["arbre"] < PRES_ARBRE]
    print(f"{len(objs)} objets ({sans} sans géométrie), sol {sol.nom}")
    print(f"  au sol : {sum(o['au_sol'] for o in objs)} ; tenus par un objet : "
          f"{sum(tenu) - sum(o['au_sol'] for o in objs)} ; volent : {len(volants)} objets en {len(groupes)} groupes "
          f"(dont {len(pres)} groupes à moins de {PRES_ARBRE} d'un arbre de WH1) ; contacts refusés (appui masqué) : "
          f"{masques}")
    for s in (0.05, 0.2, 0.5, 1.0):
        print(f"  groupes volants à plus de {s:.2f} : {sum(1 for r in rapport if r['bas'] > s)}")
    print("  familles des volants :", Counter(fam(objs[i]["modele"]) for i in volants).most_common(25))
    print(f"  les {a.liste} groupes les plus hauts (bas au-dessus du sol, objets, centre, arbre de WH1 le plus proche) :")
    for r in rapport[:a.liste]:
        print(f"     {r['bas']:+.2f}  {r['n']:3d}  ({r['centre'][0]:.2f}, {r['centre'][1]:.2f}, {r['centre'][2]:.2f})  "
              f"arbre {r['arbre']}  {r['calque'][:28]:28} {r['modeles'][:3]}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=1)
        print("écrit :", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
