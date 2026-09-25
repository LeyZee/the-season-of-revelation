#!/usr/bin/env python3
"""
caime_layers.py - build CAIME .hex_layer files from an image, or from a procedural design.

CAIME (Campaign Map Toolkit) paints Total War campaign data on a hex grid. Its Import/Export
format for one layer is trivial:

    4 bytes  little-endian int32  layer id (see LAYER_IDS)
    N bytes  one byte per hex, row-major (y * width + x); Regions use two bytes per hex

Hex row 0 is the BOTTOM of the map (game coordinates, y up): CAIME's own PNG export flips the
bitmap vertically so the picture reads like the in-game view. Images are top-down, so this
script flips every image-space array before encoding it, and design.png is the in-game view.

Value encodings, taken from CAIME/Classes/Importers/LayerImporter.cs:

    GroundTypes / Climates / Attritions / TownSlots : index + 1   (0 = unset)
        GroundTypes index runs over [land types..., sea types...]  (flat space)
    Regions        : id + 1 packed as  lower = (v & 0x1F) << 3 ; upper = v >> 5
        Regions id runs over [land regions..., sea regions...]     (flat space)
    Impassable     : 1 = passable, 0 = impassable        (careful: it is a passability flag)
    Rivers / Roads / TradeRoutes : any non-zero = present  (CAIME rebuilds the edge masks)
    Beaches / Bridges / TownSprawl / RegionBorders : 1 = set

Subcommands:

    names   --caime CAIME.exe --map map.hex
            Print the name lists CAIME stores in the map (via `CAIME.exe info --names`).

    from-image --image design.png --legend legend.json --width W --height H --out DIR
            Convert a painted PNG into one .hex_layer per layer named in the legend.
            legend.json: {"GroundTypes": {"#RRGGBB": 3, ...}, "Impassable": {"_default": 1, "#000000": 0}, ...}

    demo    --caime CAIME.exe --map map.hex --out DIR [--seed N] [--regions K]
            Design an island map procedurally (sea, beaches, plains, forests, mountains, a river,
            K land regions + 1 sea region), write design.png + legend.json + the .hex_layer files,
            sized to the map, using the map's own ground type / region names.

    remap   --caime CAIME.exe --source-map A.hex --target-map B.hex --layers DIR --out DIR2
            Renumber layers exported from map A so their indices point at the same NAMES in map B.
            Regions, ground types, climates and attritions are indices into the name lists each map
            file holds, and two games never number them alike (Warhammer 1 has 13 land ground types
            and 24 climates where Warhammer 3 has 15 and 40). Flags and town slots are copied as is.
            Names the target does not know are reported and their hexes left unset; exit code 1.

Import the result with:   CAIME.exe import-layer -m map.hex --layer GroundTypes --file DIR/GroundTypes.hex_layer ...
"""

import argparse
import json
import math
import os
import re
import struct
import subprocess
import sys

import numpy as np
from PIL import Image

LAYER_IDS = {
    "Impassable": 0, "TradeRoutes": 1, "Roads": 2, "TownSlots": 3, "TownSprawl": 4,
    "Bridges": 5, "Rivers": 6, "Beaches": 7, "RegionBorders": 8, "Regions": 9,
    "Attritions": 10, "Climates": 11, "GroundTypes": 12,
}
INDEX_PLUS_ONE = {"GroundTypes", "Climates", "Attritions", "TownSlots"}
FLAG_LAYERS = {"Impassable", "Rivers", "Roads", "TradeRoutes", "Beaches", "Bridges", "TownSprawl", "RegionBorders"}


# ----------------------------------------------------------------------------- encoding

def encode_layer(name, values):
    """values: 2-D numpy array (height, width) of ints already in CAIME's on-disk meaning
    (index for index layers, region id for Regions, 0/1 for flags). Returns bytes."""
    if name not in LAYER_IDS:
        raise ValueError(f"unknown layer {name}")
    flat = np.asarray(values).reshape(-1)
    header = struct.pack("<i", LAYER_IDS[name])
    if name == "Regions":
        v = (flat.astype(np.int64) + 1)  # -1 (unset) -> 0
        lower = ((v & 0x1F) << 3).astype(np.uint8)
        upper = (v >> 5).astype(np.uint8)
        body = np.empty(flat.size * 2, dtype=np.uint8)
        body[0::2] = lower
        body[1::2] = upper
        return header + body.tobytes()
    if name in INDEX_PLUS_ONE:
        body = (flat.astype(np.int64) + 1).clip(0, 255).astype(np.uint8)  # -1 (unset) -> 0
        return header + body.tobytes()
    body = (flat != 0).astype(np.uint8)
    return header + body.tobytes()


def write_layer(out_dir, name, values):
    """values is in IMAGE space (row 0 = top); it is flipped to hex space (row 0 = bottom) here."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.hex_layer")
    with open(path, "wb") as f:
        f.write(encode_layer(name, np.asarray(values)[::-1]))
    return path


# ----------------------------------------------------------------------------- decoding

LAYER_BY_ID = {v: k for k, v in LAYER_IDS.items()}


def read_layer(path):
    """Reads a .hex_layer written by CAIME. Returns (layer name, values) where values is a flat
    array in HEX space (row 0 = bottom) holding CAIME's on-disk meaning: index for index layers,
    region id for Regions (-1 = unset), 0/1 for flags."""
    with open(path, "rb") as f:
        blob = f.read()
    if len(blob) < 4:
        raise SystemExit(f"{path}: too short to hold a layer header")
    layer_id = struct.unpack_from("<i", blob, 0)[0]
    if layer_id not in LAYER_BY_ID:
        raise SystemExit(f"{path}: unknown layer id {layer_id}")
    name = LAYER_BY_ID[layer_id]
    body = np.frombuffer(blob, dtype=np.uint8, offset=4)
    if name == "Regions":
        if body.size % 2:
            raise SystemExit(f"{path}: the Regions layer must hold two bytes per hex")
        packed = (body[0::2].astype(np.int64) >> 3) | (body[1::2].astype(np.int64) << 5)
        return name, packed - 1          # 0 (unset) -> -1
    if name in INDEX_PLUS_ONE:
        return name, body.astype(np.int64) - 1
    return name, body.astype(np.int64)


def encode_flat(name, values):
    """Same as encode_layer, for a flat array already in HEX space (no flip)."""
    return encode_layer(name, np.asarray(values).reshape(1, -1))


# ----------------------------------------------------------------------------- CAIME info

def caime_names(caime_exe, map_hex):
    """Run `CAIME.exe info --names` and return {list_name: [names...]} plus width/height."""
    proc = subprocess.run([caime_exe, "info", "-m", map_hex, "--names"], capture_output=True, text=True)
    text = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise SystemExit(f"CAIME info failed (exit {proc.returncode}):\n{text}")
    lists, current = {}, None
    size = re.search(r"Size:\s+(\d+) x (\d+) hexes", text)
    for line in text.splitlines():
        if line.startswith("Layer file sizes"):
            break   # the size table below repeats "Climates" / "Attritions" as row labels
        m = re.match(r"^\s{2}(Land regions|Sea regions|Land ground types|Sea ground types|Climates|Attritions|Areas of interest)\s+(\d+)\s*$", line)
        if m:
            current = m.group(1)
            lists[current] = []
            continue
        m = re.match(r"^\s+\[(\d+)\]\s+(.*)$", line)
        if m and current:
            lists[current].append(m.group(2).strip())
    if not size:
        raise SystemExit("could not read the map size from CAIME info output")
    return lists, int(size.group(1)), int(size.group(2))


def pick(names, keywords, fallback=0):
    """Index of the first name containing any keyword (in keyword priority order)."""
    low = [n.lower() for n in names]
    for kw in keywords:
        for i, n in enumerate(low):
            if kw in n:
                return i
    return fallback if names else -1


# ----------------------------------------------------------------------------- from-image

def hex_to_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def cmd_from_image(a):
    img = Image.open(a.image).convert("RGB")
    if img.size != (a.width, a.height):
        img = img.resize((a.width, a.height), Image.NEAREST)
    px = np.asarray(img)  # (H, W, 3)
    with open(a.legend, "r", encoding="utf-8") as f:
        legend = json.load(f)
    key = px[:, :, 0].astype(np.int64) * 65536 + px[:, :, 1].astype(np.int64) * 256 + px[:, :, 2].astype(np.int64)
    for layer, table in legend.items():
        if layer not in LAYER_IDS:
            raise SystemExit(f"legend names unknown layer '{layer}'")
        default = table.get("_default", -1 if (layer in INDEX_PLUS_ONE or layer == "Regions") else 0)
        values = np.full(key.shape, default, dtype=np.int64)
        for colour, value in table.items():
            if colour.startswith("_"):
                continue
            r, g, b = hex_to_rgb(colour)
            values[key == (r * 65536 + g * 256 + b)] = int(value)
        print(f"{layer:14} <- {os.path.basename(a.image)}  ->  {write_layer(a.out, layer, values)}")


# ----------------------------------------------------------------------------- demo design

# CAIME's grid is flat-top with the column parity deciding the vertical shove
# (Hex.Directions_FlatTop[q & 1]), in HEX space where row 0 is the bottom of the map.
_DIRS_HEX = {
    0: ((0, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)),   # even column: (dq, dr)
    1: ((0, 1), (1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1)),     # odd column
}


def hex_disc_image_space(y, x, radius, H, W):
    """All cells within `radius` hex steps of (y, x), computed in hex space (row flipped) so
    the disc is a true hex disc for CAIME, returned as image-space (y, x) pairs."""
    r0, q0 = H - 1 - y, x
    seen, frontier = {(q0, r0)}, [(q0, r0)]
    for _ in range(radius):
        nxt = []
        for (q, r) in frontier:
            for dq, dr in _DIRS_HEX[q & 1]:
                nq, nr = q + dq, r + dr
                if 0 <= nq < W and 0 <= nr < H and (nq, nr) not in seen:
                    seen.add((nq, nr))
                    nxt.append((nq, nr))
        frontier = nxt
    return [(H - 1 - r, q) for (q, r) in seen]


def fbm(shape, rng, octaves=5, base=6):
    """Cheap fractal noise: sum of upscaled random grids."""
    h, w = shape
    acc = np.zeros(shape, dtype=np.float64)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        grid = rng.random((max(2, math.ceil(h / w * n)) + 1, n + 1))
        layer = np.asarray(Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), dtype=np.float64) / 255.0
        acc += amp * layer
        total += amp
        amp *= 0.5
    return acc / total


def cmd_demo(a):
    lists, W, H = caime_names(a.caime, a.map)
    land_gt, sea_gt = lists.get("Land ground types", []), lists.get("Sea ground types", [])
    land_rg, sea_rg = lists.get("Land regions", []), lists.get("Sea regions", [])
    if not land_gt or not sea_gt:
        raise SystemExit("the map stores no ground type names yet; use a template map or a map opened once with its Assembly Kit")

    # Ground type indices in CAIME's flat space [land..., sea...].
    gt = {
        "plain":    pick(land_gt, ["grass", "plain", "field", "farm", "temperate"], 0),
        "forest":   pick(land_gt, ["forest", "wood"], 0),
        "hills":    pick(land_gt, ["hill", "upland"], 0),
        "mountain": pick(land_gt, ["mountain", "rock", "cliff", "alp"], 0),
        "desert":   pick(land_gt, ["desert", "arid", "sand"], 0),
        "sea":      len(land_gt) + pick(sea_gt, ["shallow", "coast", "sea"], 0),
        "ocean":    len(land_gt) + pick(sea_gt, ["deep", "ocean"], len(sea_gt) - 1),
    }
    print(f"map {W} x {H}; ground types: " + ", ".join(f"{k}={v}:{(land_gt + sea_gt)[v]}" for k, v in gt.items()))

    rng = np.random.default_rng(a.seed)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    radial = np.sqrt(cx ** 2 + (cy * 1.15) ** 2)
    height = fbm((H, W), rng, octaves=6, base=5) * 1.15 - radial * 0.9 + 0.25   # island: high middle, sea at the rim
    moisture = fbm((H, W), rng, octaves=4, base=4)

    sea = height < 0.0
    # Smooth the coast: a land hex with 5 or more sea neighbours (8-neighbourhood) is a spike the
    # validator flags ("coast hex should keep at least one non-coast land neighbour"). Twice.
    for _ in range(2):
        p = np.pad(sea, 1, constant_values=True)
        n_sea = sum(p[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx].astype(np.int64)
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
        sea = sea | (~sea & (n_sea >= 5))
    # Keep one landmass: islets would each become a disconnected piece of some region.
    from collections import deque as _dq
    comp = np.full((H, W), -1, dtype=np.int64)
    sizes = []
    for sy, sx in np.argwhere(~sea):
        if comp[sy, sx] >= 0:
            continue
        cid = len(sizes); comp[sy, sx] = cid; q = _dq([(int(sy), int(sx))]); n = 0
        while q:
            y, x = q.popleft(); n += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and not sea[ny, nx] and comp[ny, nx] < 0:
                    comp[ny, nx] = cid; q.append((ny, nx))
        sizes.append(n)
    if sizes:
        sea = sea | (comp != int(np.argmax(sizes)))
    deep = (height < -0.28) & sea
    land = ~sea
    mountain = land & (height > 0.62)
    hills = land & (height > 0.48) & ~mountain
    forest = land & ~mountain & ~hills & (moisture > 0.58)
    desert = land & ~mountain & ~hills & ~forest & (moisture < 0.33) & (cy > 0.15)

    ground = np.full((H, W), gt["plain"], dtype=np.int64)
    ground[forest] = gt["forest"]
    ground[hills] = gt["hills"]
    ground[desert] = gt["desert"]
    ground[mountain] = gt["mountain"]
    ground[sea] = gt["sea"]
    ground[deep] = gt["ocean"]

    # Beaches: land hexes touching sea, only where the land is flat.
    sea_pad = np.pad(sea, 1)
    touches_sea = sea_pad[:-2, 1:-1] | sea_pad[2:, 1:-1] | sea_pad[1:-1, :-2] | sea_pad[1:-1, 2:]
    beaches = land & touches_sea & ~mountain & ~hills

    # Impassable: mountains cores (1 = passable).
    passable = np.ones((H, W), dtype=np.int64)
    passable[land & (height > 0.70)] = 0

    # A river: walk downhill from the highest land hex towards the sea, stopping on the last
    # land hex (rivers live on land only; an edge pointing into the sea is a validator warning).
    rivers = np.zeros((H, W), dtype=np.int64)
    if land.any():
        y, x = np.unravel_index(np.argmax(np.where(land, height, -9)), height.shape)
        for _ in range(W + H):
            if sea[y, x]:
                break
            rivers[y, x] = 1
            best, by, bx = height[y, x], y, x
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and rivers[ny, nx] == 0 and height[ny, nx] < best:
                    best, by, bx = height[ny, nx], ny, nx
            if (by, bx) == (y, x):   # local minimum: carve towards the nearest sea direction
                by, bx = (y + (1 if cy[y, x] > 0 else -1), x) if abs(cy[y, x]) > abs(cx[y, x]) else (y, x + (1 if cx[y, x] > 0 else -1))
                if not (0 <= by < H and 0 <= bx < W):
                    break
            y, x = by, bx

    # Regions: K land regions grown from seeds by breadth-first flood over LAND ONLY, so every
    # region is one connected piece (a plain Voronoi split cuts regions across bays and inlets,
    # which the validator flags as "split into N disconnected areas" and breaks the startpos).
    k = max(1, min(a.regions, len(land_rg)))
    regions = np.full((H, W), len(land_rg) + (pick(sea_rg, ["sea", "ocean", "mare"], 0) if sea_rg else 0), dtype=np.int64)
    land_idx = np.argwhere(land)
    seeds = land_idx[rng.choice(len(land_idx), size=k, replace=False)] if len(land_idx) >= k else land_idx
    if len(seeds):
        from collections import deque
        owner = np.full((H, W), -1, dtype=np.int64)
        queue = deque()
        for rid, (sy, sx) in enumerate(seeds):
            owner[sy, sx] = rid
            queue.append((int(sy), int(sx)))
        while queue:
            y, x = queue.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and land[ny, nx] and owner[ny, nx] < 0:
                    owner[ny, nx] = owner[y, x]
                    queue.append((ny, nx))
        # Land pockets unreachable from any seed (islets): give them the nearest seed's region.
        orphans = land & (owner < 0)
        if orphans.any():
            d2 = np.stack([(yy - sy) ** 2 + (xx - sx) ** 2 for sy, sx in seeds])
            owner[orphans] = np.argmin(d2, axis=0)[orphans]
        regions[land] = owner[land]       # land region ids 0..k-1 (first k names of the land list)
    if not sea_rg:
        regions[sea] = -1

    # Climates: every hex needs one. One land climate, one sea climate (WH3 has both).
    climates_list = lists.get("Climates", [])
    cl_land = pick(climates_list, ["temperate", "grass", "default", "main"], 0) if climates_list else -1
    cl_sea = pick(climates_list, ["ocean", "sea", "coast"], cl_land) if climates_list else -1
    climate = np.full((H, W), cl_land, dtype=np.int64)
    climate[sea] = cl_sea

    # Town slots + sprawl: one 19-hex main slot (index 0, Hex.MAIN_SLOT_INDEX) per land region,
    # a hex disc of radius 2 around a seed pulled at least 3 hexes inland, as Warhammer's
    # validator expects (slot inside the sprawl, one sprawl blob per region, no hazard inside).
    slots = np.full((H, W), -1, dtype=np.int64)
    sprawl = np.zeros((H, W), dtype=np.int64)
    inland = land.copy()
    for _ in range(3):
        p = np.pad(inland, 1, constant_values=False)
        inland = inland & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    placed = 0
    for rid, (sy, sx) in enumerate(seeds):
        cand = np.argwhere(inland & (regions == rid))
        if len(cand) == 0:
            cand = np.argwhere(land & (regions == rid))
        if len(cand) == 0:
            continue
        cy0, cx0 = cand[np.argmin((cand[:, 0] - sy) ** 2 + (cand[:, 1] - sx) ** 2)]
        disc = hex_disc_image_space(int(cy0), int(cx0), 2, H, W)
        for (y, x) in disc:
            regions[y, x] = rid          # the slot lives in its own region
            ground[y, x] = gt["plain"]   # flat land under the town: no mountain, hill or sea
            passable[y, x] = 1
            rivers[y, x] = 0
            beaches[y, x] = False
            sea[y, x] = False
            land[y, x] = True
            slots[y, x] = 0
            sprawl[y, x] = 1
        placed += 1
    print(f"town slots placed: {placed} (19-hex main slots, index 0)")

    out = a.out
    os.makedirs(out, exist_ok=True)
    paths = [
        write_layer(out, "GroundTypes", ground),
        write_layer(out, "Impassable", passable),
        write_layer(out, "Rivers", rivers),
        write_layer(out, "Beaches", beaches.astype(np.int64)),
        write_layer(out, "Regions", regions),
        write_layer(out, "Climates", climate),
        write_layer(out, "TownSlots", slots),
        write_layer(out, "TownSprawl", sprawl),
    ]

    # design.png: a human-readable picture of the same design, plus the legend that maps it back.
    palette = {
        "ocean": (20, 50, 120), "sea": (50, 110, 190), "plain": (120, 180, 70), "forest": (30, 100, 40),
        "hills": (160, 140, 80), "mountain": (110, 100, 95), "desert": (220, 200, 120), "beach": (240, 225, 160),
        "river": (80, 170, 255), "impassable": (60, 55, 55),
    }
    img = np.zeros((H, W, 3), dtype=np.uint8)
    img[:] = palette["plain"]
    for key, mask in (("forest", forest), ("hills", hills), ("desert", desert), ("mountain", mountain),
                      ("sea", sea), ("ocean", deep), ("beach", beaches), ("impassable", passable == 0), ("river", rivers == 1)):
        img[mask] = palette[key]
    Image.fromarray(img).save(os.path.join(out, "design.png"))
    legend = {
        "GroundTypes": {"_default": gt["plain"], **{"#%02x%02x%02x" % palette[k]: gt[k] for k in ("ocean", "sea", "forest", "hills", "desert", "mountain")},
                        "#%02x%02x%02x" % palette["beach"]: gt["plain"], "#%02x%02x%02x" % palette["impassable"]: gt["mountain"],
                        "#%02x%02x%02x" % palette["river"]: gt["plain"]},
        "Impassable": {"_default": 1, "#%02x%02x%02x" % palette["impassable"]: 0},
        "Rivers": {"_default": 0, "#%02x%02x%02x" % palette["river"]: 1},
        "Beaches": {"_default": 0, "#%02x%02x%02x" % palette["beach"]: 1},
    }
    with open(os.path.join(out, "legend.json"), "w", encoding="utf-8") as f:
        json.dump(legend, f, indent=2)

    print("\n".join(paths))
    print(f"design: {os.path.join(out, 'design.png')}  legend: {os.path.join(out, 'legend.json')}")
    print(f"land {int(land.sum())} hexes, sea {int(sea.sum())}, mountains {int(mountain.sum())}, forest {int(forest.sum())}, "
          f"beaches {int(beaches.sum())}, river {int(rivers.sum())}, regions {k} land + {'1' if sea_rg else '0'} sea")
    print("import with:")
    layer_args = " ".join(f"--layer {os.path.basename(p).split('.')[0]} --file \"{p}\"" for p in paths)
    print(f'  "{a.caime}" import-layer -m "{a.map}" {layer_args}')


def cmd_names(a):
    lists, W, H = caime_names(a.caime, a.map)
    print(f"{W} x {H}")
    for k, v in lists.items():
        print(f"{k}: {len(v)}")
        for i, n in enumerate(v):
            print(f"  [{i}] {n}")


# ----------------------------------------------------------------------------- remap

# Which name lists each index layer runs over, in the flat order CAIME stores on disk.
# TownSlots is an index too, but a slot number rather than a name: it is copied unchanged.
NAME_LISTS = {
    "Regions":     ("Land regions", "Sea regions"),
    "GroundTypes": ("Land ground types", "Sea ground types"),
    "Climates":    ("Climates",),
    "Attritions":  ("Attritions",),
}


def flat_names(lists, layer):
    out = []
    for key in NAME_LISTS[layer]:
        out.extend(lists.get(key, []))
    return out


def cmd_remap(a):
    """Rewrites .hex_layer files exported from one map so their indices point at the same NAMES in
    another map. Regions, ground types, climates and attritions are stored as indices into the
    name lists the map file holds, and two games never number them alike."""
    src_lists, src_w, src_h = caime_names(a.caime, a.source_map)
    dst_lists, dst_w, dst_h = caime_names(a.caime, a.target_map)
    if (src_w, src_h) != (dst_w, dst_h):
        raise SystemExit(f"size mismatch: source is {src_w} x {src_h}, target is {dst_w} x {dst_h}")

    files = sorted(f for f in os.listdir(a.layers) if f.lower().endswith(".hex_layer"))
    if not files:
        raise SystemExit(f"no .hex_layer file in {a.layers}")
    os.makedirs(a.out, exist_ok=True)

    missing_total, changed_total = {}, 0
    for fname in files:
        layer, values = read_layer(os.path.join(a.layers, fname))
        expected = src_w * src_h
        if values.size != expected:
            raise SystemExit(f"{fname}: holds {values.size} hexes, the map has {expected}")

        if layer in NAME_LISTS:
            src_names = flat_names(src_lists, layer)
            dst_index = {n: i for i, n in enumerate(flat_names(dst_lists, layer))}
            table = np.full(len(src_names) + 1, -1, dtype=np.int64)   # +1 so index -1 stays -1
            missing = []
            for i, n in enumerate(src_names):
                if n in dst_index:
                    table[i] = dst_index[n]
                elif np.any(values == i):
                    missing.append(n)
            if missing:
                missing_total[layer] = missing
            remapped = np.where(values < 0, -1, table[np.clip(values, 0, None)])
            changed = int(np.count_nonzero(remapped != values))
            changed_total += changed
            note = f"{len(src_names)} -> {len(dst_index)} names, {changed} hexes renumbered"
            if missing:
                note += f", {len(missing)} name(s) absent from the target"
        else:
            remapped, note = values, "copied unchanged"

        out_path = os.path.join(a.out, fname)
        with open(out_path, "wb") as f:
            f.write(encode_flat(layer, remapped))
        print(f"  {layer:14s} {note}")

    print(f"{len(files)} layer(s) written to {a.out}; {changed_total} hexes renumbered in total.")
    if missing_total:
        print("\nNames used by the source map that the target map does not know:")
        for layer, names in missing_total.items():
            print(f"  {layer}: {', '.join(names)}")
        print("Those hexes are left unset (0). Declare the names in the target game's database,")
        print("run sync-names again, then re-run this command.")
        return 1
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("names"); s.add_argument("--caime", required=True); s.add_argument("--map", required=True); s.set_defaults(fn=cmd_names)

    s = sub.add_parser("from-image")
    s.add_argument("--image", required=True); s.add_argument("--legend", required=True)
    s.add_argument("--width", type=int, required=True); s.add_argument("--height", type=int, required=True)
    s.add_argument("--out", required=True); s.set_defaults(fn=cmd_from_image)

    s = sub.add_parser("demo")
    s.add_argument("--caime", required=True); s.add_argument("--map", required=True); s.add_argument("--out", required=True)
    s.add_argument("--seed", type=int, default=7); s.add_argument("--regions", type=int, default=8)
    s.set_defaults(fn=cmd_demo)

    s = sub.add_parser("remap", help="renumber exported layers from one map's name lists to another's")
    s.add_argument("--caime", required=True)
    s.add_argument("--source-map", required=True, help="map.hex the layers were exported from")
    s.add_argument("--target-map", required=True, help="map.hex they are to be imported into")
    s.add_argument("--layers", required=True, help="folder holding the exported .hex_layer files")
    s.add_argument("--out", required=True, help="folder to write the renumbered files to")
    s.set_defaults(fn=cmd_remap)

    a = p.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
