#!/usr/bin/env python3
"""
lire_props_wh1.py - lire les objets (props) du terrain de campagne compilé de Warhammer 1
(`terrain\\campaigns\\<carte>\\global_props.bin`).

Pourquoi (21.09.2026, 21 h 40, Charles : « la carte est vide », « il manque des villes ») : WH1
habillait sa carte et ses villes de ~100 000 objets (rochers, arbustes, maisons, murets, bannières,
décors propres à chaque culture) ; notre terrain WH3 n'en a aucun (`global_props.bin` de 4 octets).
Ce module les relit pour les réécrire en entités de calques Terry (`props_wh1_vers_layers.py`).

Format, établi sur les octets (grammaire vérifiée : chaque lot se lit jusqu'à son dernier octet) :

    global_props.bin : u32 nombre de lots, puis pour chacun nom ASCII terminé par 0 + u32 décalage
                       (depuis la fin de l'index) ; puis les lots, bout à bout.
    nom d'un lot     : terrain/campaigns/<carte>/bmd_objects.<région>.<a>[.<b>].bin
                       a = case spatiale, b = variante (absente : objets communs) ; le dernier lot,
                       bmd_objects.bin, est le lot maître.
    lot              : fichier BMD « FASTBIN0 », version 21 (WH3 : 27).

Dans un lot, la liste d'objets est une suite d'enregistrements de version 12 :

    u16 12 | u16 n + chemin du modèle (ASCII) | 12 flottants : matrice 3 x 3 (rotation x échelle,
    lignes = axes X, Y, Z) puis position (x, y = hauteur, z) | 30 octets de drapeaux |
    u16 n + mode de hauteur (« BHM_CLASSIC »...) | u32 | u8

Le lecteur cherche ces enregistrements par leur forme (version, chemin `rigidmodels/...` ou
`.wsmodel`, puis mode de hauteur `BHM_` à la bonne place) et vérifie leur enchaînement.

Usage :
    python lire_props_wh1.py [--global-props <fichier>] [--resume]
"""

import argparse
import math
import re
import struct
import sys
from collections import Counter, defaultdict

GLOBAL_PROPS = (r"C:\TotalWar-CampaignMap\03-references\saison-des-revelations"
                r"\terrain-wh1\terrain\campaigns\wh_dlc05_wood_elves_map_1\global_props.bin")
DRAPEAUX = 30
MOTIF = re.compile(rb"\x0c\x00(.)(.)((?:rigidmodels|RigidModels|Rigidmodels|terrain)/[\x20-\x7e]+?\.(?:wsmodel|rigid_model_v2))", re.S)


def lots(chemin):
    """(nom court, région, a, b, octets) pour chaque lot."""
    b = open(chemin, "rb").read()
    n = struct.unpack_from("<I", b, 0)[0]
    o, entrees = 4, []
    for _ in range(n):
        fin = b.index(b"\x00", o)
        entrees.append((b[o:fin].decode("ascii"), struct.unpack_from("<I", b, fin + 1)[0]))
        o = fin + 5
    base = o
    for i, (nom, off) in enumerate(entrees):
        fin = entrees[i + 1][1] if i + 1 < len(entrees) else len(b) - base
        court = nom.split("bmd_objects.")[-1]
        m = re.match(r"(.*?)\.(\d+)(?:\.(\d+))?\.bin$", court)
        region, a, v = (m.group(1), int(m.group(2)), None if m.group(3) is None else int(m.group(3))) if m else (None, None, None)
        yield court, region, a, v, b[base + off:base + fin]


def objets(blob):
    """Enregistrements d'objets d'un lot : dict(modele, matrice, position, drapeaux, hauteur)."""
    out = []
    for m in MOTIF.finditer(blob):
        n = m.group(1)[0] | (m.group(2)[0] << 8)
        chemin = m.group(3)
        if n != len(chemin):
            continue
        o = m.end()
        if o + 48 + DRAPEAUX + 2 > len(blob):
            continue
        f = struct.unpack_from("<12f", blob, o)
        o += 48
        drapeaux = blob[o:o + DRAPEAUX]
        o += DRAPEAUX
        k = struct.unpack_from("<H", blob, o)[0]
        mode = blob[o + 2:o + 2 + k]
        if not mode.startswith(b"BHM_"):
            continue
        out.append({"modele": chemin.decode("ascii"), "matrice": f[:9], "position": f[9:12],
                    "drapeaux": drapeaux, "hauteur": mode.decode("ascii"), "fin": o + 2 + k + 5})
    return out


def decompose(matrice):
    """Matrice 3 x 3 (lignes = axes) -> (échelle x, y, z), lacet autour de Y (degrés), inclinaison
    maximale des axes par rapport à la verticale (degrés)."""
    ax = matrice[0:3], matrice[3:6], matrice[6:9]
    ech = tuple(math.sqrt(sum(c * c for c in v)) for v in ax)
    x = [c / (ech[0] or 1) for c in ax[0]]
    y = [c / (ech[1] or 1) for c in ax[1]]
    lacet = math.degrees(math.atan2(-x[2], x[0]))
    inclinaison = math.degrees(math.acos(max(-1.0, min(1.0, y[1]))))
    return ech, lacet, inclinaison


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--global-props", default=GLOBAL_PROPS)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    total, par_variante, dossiers_par_variante = 0, Counter(), defaultdict(Counter)
    modeles, inclin, echelles, trous = Counter(), Counter(), Counter(), 0
    for court, region, _, v, blob in lots(a.global_props):
        obj = objets(blob)
        total += len(obj)
        par_variante[v] += len(obj)
        for o in obj:
            modeles[o["modele"].lower()] += 1
            dossiers_par_variante[v]["/".join(o["modele"].lower().split("/")[2:4])] += 1
            ech, _, inc = decompose(o["matrice"])
            inclin[round(inc / 5) * 5] += 1
            echelles["uniforme" if max(ech) - min(ech) < 1e-3 else "non uniforme"] += 1
        # enchaînement : chaque enregistrement doit commencer là où le précédent finit
        for p, s in zip(obj, obj[1:]):
            if blob.find(b"\x0c\x00", p["fin"]) != p["fin"]:
                trous += 1
    print(f"{total} objets ; {len(modeles)} modèles distincts ; ruptures d'enchaînement : {trous}")
    print("par variante :", dict(sorted(par_variante.items(), key=lambda t: (t[0] is None, t[0] or 0))))
    for v in sorted(dossiers_par_variante, key=lambda t: (t is None, t or 0)):
        print(f"   variante {v} : {dossiers_par_variante[v].most_common(6)}")
    print("inclinaison (degrés) :", sorted(inclin.items())[:12])
    print("échelles :", dict(echelles))
    return 0


if __name__ == "__main__":
    sys.exit(main())
