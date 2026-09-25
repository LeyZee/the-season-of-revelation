#!/usr/bin/env python3
"""
grow_town_slots.py - agrandit les emplacements de colonie d'une carte Warhammer 1 aux tailles que
Warhammer 3 exige (projet « La Saison des Révélations »).

Warhammer 1 peint 7 hex par colonie (4 quand la mer en mange trois) ; le validateur de CAIME veut
**19 hex de terre pour une colonie intérieure, 16 pour un port** (`TownSlotsValidator`, règle
appliquée à warhammer, warhammer2 et warhammer3). Il ne compte que les hex de TERRE (le type de
sol, pas la région) portant l'emplacement principal (index 0) **dans la même région**.

Contraintes que le script respecte, toutes lues dans le validateur :
- un emplacement non portuaire ne se pose jamais sur un hex de mer ;
- tout hex d'emplacement doit être dans l'étalement urbain (TownSprawl) : le script l'étend ;
- l'étalement de deux régions ne doit pas se toucher : la croissance reste dans la région, et les
  contacts restants sont signalés ;
- une colonie a besoin d'un hex entouré de 6 hex du même emplacement : la croissance part du
  centre, en disque, ce qui le garantit.

Le script lit les couches exportées (dossier `--layers`, au format .hex_layer de CAIME), écrit les
couches corrigées dans `--out` et n'écrit jamais dans le map.hex lui-même : l'import reste manuel.

Usage :
    python grow_town_slots.py --caime CAIME.exe --map <map.hex de destination>
        --layers <dossier des couches> --out <dossier de sortie> [--dry-run]

Les couches nécessaires dans `--layers` : Regions, GroundTypes, TownSlots, TownSprawl.
Toutes les autres sont recopiées telles quelles.
"""

import argparse
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from caime_layers import read_layer, encode_flat, caime_names   # noqa: E402

MAIN_SLOT, PORT_SLOT = 0, 1
TARGET_INLAND, TARGET_PORT = 19, 16
# 21.09.2026 : la cible portuaire reste **16**, comme le validateur de CAIME. Mesure chez CA
# (`wh3_main_chaos_map_4`, 26 colonies portuaires) : le bloc principal fait 16 hex et le bloc de
# port 19, ce dernier etant le disque complet dont le primaire est le sous-ensemble terrestre.
# Porter la cible a 19 a ete essaye le 21.09.2026 et **n'a rien change** au defaut cherche
# (position logique absente pour Bordeleaux, Brionne et Mousillon) : voir le journal, section 15.

# Hexagones à sommet plat, décalage sur les colonnes impaires (CAIME : Hex.Directions_FlatTop
# indexé par Q & 1). Les six directions, colonnes paires puis impaires.
DIRS = (
    ((0, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)),
    ((0, 1), (1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1)),
)


def neighbours(q, r, w, h):
    for dq, dr in DIRS[q & 1]:
        nq, nr = q + dq, r + dr
        if 0 <= nq < w and 0 <= nr < h:
            yield nq, nr


def cube(q, r):
    z = r - (q - (q & 1)) // 2
    return q, -q - z, z


def hex_distance(a, b):
    ax, ay, az = cube(*a)
    bx, by, bz = cube(*b)
    return (abs(ax - bx) + abs(ay - by) + abs(az - bz)) // 2


def load(layers_dir):
    """Returns {layer name: (flat values, file name)} for every .hex_layer in the folder."""
    out = {}
    for fname in sorted(os.listdir(layers_dir)):
        if fname.lower().endswith(".hex_layer"):
            name, values = read_layer(os.path.join(layers_dir, fname))
            out[name] = (values, fname)
    return out


def components(mask, W, H):
    """Connected components of a boolean grid. Returns (id grid, -1 outside) and the count."""
    ids = np.full((H, W), -1, dtype=np.int32)
    count = 0
    for r0 in range(H):
        for q0 in range(W):
            if not mask[r0, q0] or ids[r0, q0] >= 0:
                continue
            queue = deque([(q0, r0)])
            ids[r0, q0] = count
            while queue:
                q, r = queue.popleft()
                for nq, nr in neighbours(q, r, W, H):
                    if mask[nr, nq] and ids[nr, nq] < 0:
                        ids[nr, nq] = count
                        queue.append((nq, nr))
            count += 1
    return ids, count


def fix_hazard_outline(sprawl, hazard, region, is_land, passable, W, H, max_passes=6):
    """Adds the hex that makes a hazard patch sitting two hexes from a sprawl blob touch it.
    Returns the number of hexes added. Blobs are never allowed to merge."""
    added_total = 0
    for _ in range(max_passes):
        blob_ids, blob_count = components(sprawl == 1, W, H)
        hazard_ids, _ = components(hazard, W, H)
        added = 0
        for blob in range(blob_count):
            cells = [(int(q), int(r)) for r, q in zip(*np.nonzero(blob_ids == blob))]
            ring1, ring2 = set(), set()
            for q, r in cells:
                for nq, nr in neighbours(q, r, W, H):
                    if blob_ids[nr, nq] != blob:
                        ring1.add((nq, nr))
            for q, r in ring1:
                for nq, nr in neighbours(q, r, W, H):
                    if blob_ids[nr, nq] != blob and (nq, nr) not in ring1:
                        ring2.add((nq, nr))
            touching = {int(hazard_ids[r, q]) for q, r in ring1 if hazard_ids[r, q] >= 0}
            faraway = {int(hazard_ids[r, q]) for q, r in ring2 if hazard_ids[r, q] >= 0} - touching
            if not faraway:
                continue
            main_region = max({int(region[r, q]) for q, r in cells if is_land[r, q]} or {-1},
                              key=lambda rid: sum(1 for q, r in cells if int(region[r, q]) == rid))
            for comp in faraway:
                for q, r in sorted(ring1):
                    if not passable[r, q]:
                        continue
                    if is_land[r, q] and int(region[r, q]) != main_region:
                        continue
                    # ne pas souder deux étalements
                    if any(sprawl[nr, nq] == 1 and blob_ids[nr, nq] != blob
                           for nq, nr in neighbours(q, r, W, H)):
                        continue
                    if any(hazard_ids[nr, nq] == comp for nq, nr in neighbours(q, r, W, H)):
                        sprawl[r, q] = 1
                        added += 1
                        break
        added_total += added
        if added == 0:
            break
    return added_total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--caime", required=True)
    ap.add_argument("--map", required=True, help="map.hex de destination (pour les listes de noms et la taille)")
    ap.add_argument("--layers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true", help="n'écrit rien, dit seulement ce qu'il ferait")
    ap.add_argument("--cible-port", type=int, default=TARGET_PORT,
                    help="hex de terre visés pour une colonie portuaire (défaut 19 : ce que "
                         "MapDataBuilder exige ; le validateur de CAIME, lui, accepte 16)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lists, W, H = caime_names(a.caime, a.map)
    land_regions = lists.get("Land regions", [])
    all_regions = land_regions + lists.get("Sea regions", [])
    land_ground_count = len(lists.get("Land ground types", []))

    layers = load(a.layers)
    for needed in ("Regions", "GroundTypes", "TownSlots", "TownSprawl"):
        if needed not in layers:
            raise SystemExit(f"couche {needed} absente de {a.layers}")
        if layers[needed][0].size != W * H:
            raise SystemExit(f"couche {needed} : {layers[needed][0].size} hex, la carte en a {W * H}")

    region = layers["Regions"][0].reshape(H, W)
    ground = layers["GroundTypes"][0].reshape(H, W)
    slots = layers["TownSlots"][0].reshape(H, W).copy()
    sprawl = layers["TownSprawl"][0].reshape(H, W).copy()
    is_land = (ground >= 0) & (ground < land_ground_count)

    # Un emplacement par région : on regroupe les hex de l'emplacement principal par région.
    main_by_region, port_regions = {}, set()
    for r in range(H):
        for q in range(W):
            s = slots[r, q]
            if s == MAIN_SLOT:
                main_by_region.setdefault(int(region[r, q]), []).append((q, r))
            elif s == PORT_SLOT:
                port_regions.add(int(region[r, q]))

    print(f"carte {W} x {H} ; {len(main_by_region)} emplacements principaux, {len(port_regions)} port(s)")

    grown, already, short = 0, 0, []
    for rid, hexes in sorted(main_by_region.items()):
        name = all_regions[rid] if 0 <= rid < len(all_regions) else f"#{rid}"
        target = a.cible_port if rid in port_regions else TARGET_INLAND
        on_land = [(q, r) for q, r in hexes if is_land[r, q]]
        if len(on_land) == target:
            already += 1
            continue

        # Centre : le hex de l'emplacement dont les voisins appartiennent le plus à l'emplacement.
        def score(cell):
            q, r = cell
            return sum(1 for nq, nr in neighbours(q, r, W, H) if slots[nr, nq] == MAIN_SLOT)
        centre = max(on_land or hexes, key=score)

        # Croissance en couronnes autour du centre : terre, même région, pas déjà un autre
        # emplacement. En anneaux, ce qui donne le disque de rayon 2 (19 hex) quand rien ne gêne.
        chosen, seen = [], set()
        queue = deque([centre])
        seen.add(centre)
        while queue and len(chosen) < target:
            q, r = queue.popleft()
            ok = (is_land[r, q] and int(region[r, q]) == rid
                  and slots[r, q] in (MAIN_SLOT, -1))
            if ok:
                chosen.append((q, r))
            for nq, nr in neighbours(q, r, W, H):
                if (nq, nr) not in seen and hex_distance((nq, nr), centre) <= 6:
                    seen.add((nq, nr))
                    queue.append((nq, nr))
        if len(chosen) < target:
            short.append((name, len(chosen), target))

        # Les hex de l'emplacement qui ne sont pas retenus redeviennent libres.
        for q, r in hexes:
            if (q, r) not in chosen:
                slots[r, q] = -1
        for q, r in chosen:
            slots[r, q] = MAIN_SLOT
            sprawl[r, q] = 1
        grown += 1

    # Tout hex d'emplacement doit être dans l'étalement (les ports aussi, en mer).
    sprawl[slots >= 0] = 1

    # --- deuxième passe : le contour du danger (SprawlValidator.ValidateHazardOutline) -----------
    # Un terrain « dangereux » (infranchissable, rivière, plage, falaise) qui arrive à deux hex de
    # l'étalement sans le toucher est une erreur : on ajoute l'hex intermédiaire pour qu'il le
    # touche. On n'ajoute jamais un hex infranchissable, ni un hex qui souderait deux étalements.
    sea = ~is_land
    beach = layers["Beaches"][0].reshape(H, W) != 0
    river = layers["Rivers"][0].reshape(H, W) != 0
    passable = layers["Impassable"][0].reshape(H, W) != 0      # 1 = franchissable
    cliff = np.zeros((H, W), dtype=bool)
    for r in range(H):
        for q in range(W):
            if is_land[r, q] and not beach[r, q]:
                cliff[r, q] = any(sea[nr, nq] for nq, nr in neighbours(q, r, W, H))
    hazard = (~passable) | river | beach | cliff

    added = fix_hazard_outline(sprawl, hazard, region, is_land, passable, W, H)
    print(f"  contour du danger : {added} hex ajouté(s) à l'étalement")

    # Contacts d'étalement entre régions (le validateur les refuse).
    touching = set()
    ys, xs = np.nonzero(sprawl == 1)
    for r, q in zip(ys.tolist(), xs.tolist()):
        if not is_land[r, q]:
            continue
        for nq, nr in neighbours(q, r, W, H):
            if sprawl[nr, nq] == 1 and is_land[nr, nq] and int(region[nr, nq]) != int(region[r, q]):
                touching.add(tuple(sorted((int(region[r, q]), int(region[nr, nq])))))

    print(f"  {grown} emplacement(s) agrandi(s), {already} déjà à la bonne taille")
    if short:
        print("  ATTENTION, la région ne contient pas assez de terre :")
        for name, got, want in short:
            print(f"    {name} : {got} hex au lieu de {want}")
    if touching:
        print(f"  ATTENTION, {len(touching)} paire(s) de régions dont l'étalement se touche :")
        for x, y in sorted(touching):
            nx = all_regions[x] if x < len(all_regions) else x
            ny = all_regions[y] if y < len(all_regions) else y
            print(f"    {nx} <-> {ny}")

    if a.dry_run:
        print("  essai à blanc : rien n'a été écrit")
        return 1 if (short or touching) else 0

    os.makedirs(a.out, exist_ok=True)
    for name, (values, fname) in layers.items():
        data = {"TownSlots": slots, "TownSprawl": sprawl}.get(name, values)
        with open(os.path.join(a.out, fname), "wb") as f:
            f.write(encode_flat(name, np.asarray(data).reshape(-1)))
    print(f"  {len(layers)} couche(s) écrite(s) dans {a.out}")
    return 1 if (short or touching) else 0


if __name__ == "__main__":
    sys.exit(main())
