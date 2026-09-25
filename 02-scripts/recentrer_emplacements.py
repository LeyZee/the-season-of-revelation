#!/usr/bin/env python3
"""
recentrer_emplacements.py - peindre chaque emplacement de colonie selon le modele de CA, le seul
dont MapDataBuilder sait tirer la position logique de la colonie.

Pourquoi (21 et 22.09.2026, journal `phase-2-startpos-temoin.md` §§ 15 et 17). La generation du
startpos meurt a `Warhammer3+0x2A4401A` depuis `+0x27A2E98` sur la coordonnee sentinelle
`0xFFFFFFFF`. Dans `map_data.esf`, `SETTLEMENT_INFO` porte la position logique de chaque colonie
et trois des 57 l'ont a `0xFFFF` : Bordeleaux, Brionne et Mousillon — **nos trois seuls ports**.

Le modele, releve dans la carte source de CA (`wh3_main_chaos_map_4\\map.hex`, colonie portuaire
`wh3_dlc20_chaos_region_chantillon`, dont le `map_data.esf` livre a bien une position) :

- l'emplacement est un **disque hexagonal parfait de rayon 2** (19 hex), et la position logique
  est son centre ;
- colonie **interieure** : les 19 hex portent l'emplacement principal (index 0) ;
- colonie **portuaire** : **16** hex portent l'emplacement principal (index 0), tous sur terre, et
  **3 hex consecutifs du second anneau, cote mer**, portent l'emplacement de port (index 1) —
  chez CA deux sur terre et un en mer, dans la region de mer. L'union forme le disque ;
- l'etalement urbain (TownSprawl) couvre exactement les 19 hex, et aucun n'est infranchissable.

Nos ports faisaient bien 16 + 3 = 19 hex, mais **l'union n'etait pas un disque** :
`grow_town_slots.py` avait fait pousser l'emplacement principal sans tenir compte des hex de port.
Ce que les essais du 21.09.2026 ont montre ne pas suffire, et que ce script ne fait donc plus :
un disque de 19 hex tout en terre pour le principal en laissant le port a cote ; retirer le port.

Le script ne touche que les emplacements qui ne suivent pas le modele. Pour chacun, il cherche le
centre dont le disque respecte toutes les contraintes, au plus pres de l'emplacement actuel — la
ville ne bouge que d'un hex ou deux — puis il efface l'ancien emplacement et peint le nouveau.

Comme les autres outils de couches, il lit `--layers`, ecrit dans `--out`, et **n'ecrit jamais
dans le map.hex** : l'import reste une commande separee, et **seules `TownSlots` et `TownSprawl`
doivent etre reimportees** (`read_layer` puis `encode_flat` aplatit `Rivers`, `Roads` et
`RegionBorders`).

Usage :
    python recentrer_emplacements.py --layers <dossier> --out <dossier> --noms-carte <map.hex>
                                     --caime <CAIME.exe> [--dry-run]
"""

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from caime_layers import read_layer, encode_flat, caime_names      # noqa: E402
from grow_town_slots import neighbours, MAIN_SLOT, PORT_SLOT       # noqa: E402

NB_PORT = 3              # hex d'emplacement de port dans le modele de CA


def anneau1(q, r, w, h):
    return set(neighbours(q, r, w, h))


def disque(q, r, w, h):
    """(ensemble des 19 hex, anneau 2 ordonne en tournant) ; ensemble plus petit au bord."""
    a1 = anneau1(q, r, w, h)
    a2 = set()
    for (q1, r1) in a1:
        a2 |= anneau1(q1, r1, w, h)
    a2 -= a1 | {(q, r)}

    # ordre angulaire : colonnes impaires decalees d'un demi-hex vers le haut (voisinage CAIME)
    def pos(c):
        return (c[0] * math.sqrt(3) / 2, c[1] + 0.5 * (c[0] & 1))
    cx, cy = pos((q, r))
    ordre = sorted(a2, key=lambda c: math.atan2(pos(c)[1] - cy, pos(c)[0] - cx))
    return {(q, r)} | a1 | a2, ordre


def disque_parfait(ens, w, h):
    """Le centre d'un disque de rayon 2 entierement contenu dans `ens`, ou None."""
    for (q, r) in ens:
        d, _ = disque(q, r, w, h)
        if len(d) == 19 and d <= ens:
            return (q, r)
    return None


def charge(dossier):
    out = {}
    for f in sorted(os.listdir(dossier)):
        if f.lower().endswith(".hex_layer"):
            nom, val = read_layer(os.path.join(dossier, f))
            out[nom] = (np.asarray(val).reshape(-1), f)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--noms-carte", required=True, help="map.hex, pour les listes de noms")
    ap.add_argument("--caime", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    noms, W, H = caime_names(a.caime, a.noms_carte)
    regions = noms["Land regions"] + noms["Sea regions"]
    n_land_reg = len(noms["Land regions"])
    n_land_sol = len(noms["Land ground types"])

    couches = charge(a.layers)
    for n in ("Regions", "GroundTypes", "TownSlots", "TownSprawl", "Impassable"):
        if n not in couches:
            print(f"!! couche {n} absente de {a.layers}")
            return 2
    reg = couches["Regions"][0]
    sol = couches["GroundTypes"][0]
    passable = couches["Impassable"][0] == 1          # CAIME : 1 = franchissable
    slots = couches["TownSlots"][0].copy()
    sprawl = couches["TownSprawl"][0].copy()
    terre = sol < n_land_sol
    mer_reg = reg >= n_land_reg
    print(f"carte {W} x {H} ; {n_land_reg} regions de terre, {len(regions) - n_land_reg} de mer")

    def ij(c):
        return c[1] * W + c[0]

    principaux = {}
    for i in np.nonzero(slots == MAIN_SLOT)[0]:
        principaux.setdefault(int(reg[i]), set()).add((int(i % W), int(i // W)))
    ports_hex = [(int(i % W), int(i // W)) for i in np.nonzero(slots == PORT_SLOT)[0]]

    refaits, conformes, echecs = 0, 0, []
    for rid, prin in sorted(principaux.items()):
        if rid >= n_land_reg:
            continue
        port = {p for p in ports_hex
                if min(abs(p[0] - q) + abs(p[1] - r) for q, r in prin) <= 2}
        union = prin | port
        est_port = bool(port)
        centre = disque_parfait(union, W, H)
        if centre and len(union) == 19 and len(prin) == (16 if est_port else 19):
            conformes += 1
            continue

        cx = sum(q for q, _ in union) / len(union)
        cy = sum(r for _, r in union) / len(union)
        # hex occupes par l'emplacement d'une AUTRE colonie : interdits
        a_nous = {ij(c) for c in union}
        autre = (slots >= 0).copy()
        for j in a_nous:
            autre[j] = False

        meilleurs = []
        for q in range(max(0, int(cx) - 8), min(W, int(cx) + 9)):
            for r in range(max(0, int(cy) - 8), min(H, int(cy) + 9)):
                d, ordre = disque(q, r, W, H)
                if len(d) != 19 or len(ordre) != 12:
                    continue
                if any(autre[ij(c)] for c in d):
                    continue
                mers = [c for c in d if not terre[ij(c)]]
                terres = [c for c in d if terre[ij(c)]]
                # toute la terre du disque : dans la region, franchissable
                if any(reg[ij(c)] != rid or not passable[ij(c)] for c in terres):
                    continue
                if not est_port:
                    if mers:
                        continue
                    principal, arc = set(d), []
                else:
                    # la mer du disque doit etre en region de mer et tenir dans un arc de 3 hex
                    # consecutifs du second anneau ; le reste (16 hex) est de la terre
                    if not mers or len(mers) > NB_PORT:
                        continue
                    if any(not mer_reg[ij(c)] for c in mers):
                        continue
                    arc = None
                    for k in range(12):
                        cand = [ordre[(k + t) % 12] for t in range(NB_PORT)]
                        if set(mers) <= set(cand):
                            # au moins un hex de port a terre touche la mer (validateur CAIME)
                            if any(terre[ij(c)] and any(not terre[ij(n)] for n in
                                                        anneau1(c[0], c[1], W, H))
                                   for c in cand):
                                arc = cand
                                break
                    if arc is None:
                        continue
                    principal = set(d) - set(arc)
                dist = (q - cx) ** 2 + (r - cy) ** 2
                meilleurs.append((dist, (q, r), principal, arc, d))

        nom = regions[rid]
        if not meilleurs:
            echecs.append(nom)
            print(f"  {nom:42} : aucun disque ne respecte le modele")
            continue
        dist, c0, principal, arc, d = min(meilleurs, key=lambda m: m[0])
        for c in union:                          # effacer l'ancien emplacement
            slots[ij(c)] = -1
            sprawl[ij(c)] = 0
        for c in principal:
            slots[ij(c)] = MAIN_SLOT
        for c in arc:
            slots[ij(c)] = PORT_SLOT
        for c in d:
            sprawl[ij(c)] = 1
        n_mer = sum(1 for c in d if not terre[ij(c)])
        print(f"  {nom:42} : {len(prin)}+{len(port)} hex hors modele -> disque en {c0}, "
              f"{len(principal)} principal + {len(arc)} port ({n_mer} en mer), "
              f"centre deplace de {math.sqrt(dist):.1f} hex")
        refaits += 1

    print(f"\n{conformes} emplacement(s) deja conforme(s), {refaits} repeint(s), "
          f"{len(echecs)} echec(s)")
    if a.dry_run:
        print("essai a blanc : rien ecrit")
        return 0
    os.makedirs(a.out, exist_ok=True)
    for nom, (val, fichier) in couches.items():
        données = {"TownSlots": slots, "TownSprawl": sprawl}.get(nom, val)
        with open(os.path.join(a.out, fichier), "wb") as f:
            f.write(encode_flat(nom, np.asarray(données).reshape(-1)))
    print(f"{len(couches)} couche(s) ecrite(s) dans {a.out} — N'IMPORTER QUE TownSlots et TownSprawl.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
