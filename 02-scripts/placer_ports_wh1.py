#!/usr/bin/env python3
"""
placer_ports_wh1.py - remettre les trois ports (Bordeleaux, Brionne, Mousillon) a leur hex EXACT de Warhammer 1.

Pourquoi (23.09.2026, 23 h 10, demande de Charles : « tout a la meme position que dans WH1 »). Les 54 colonies de
l'interieur sont deja a leur position de WH1 au millieme ; les trois ports avaient ete deplaces de 1 a 2 hex vers
l'interieur le 21.09 par `recentrer_emplacements.py`, dont la regle « un hex de port a terre touche la mer » (modele de
CA : 2 hex de port a terre, 1 en mer) n'est pas satisfaite a la position de WH1. Recherche du 23.09.2026 (brouillon
`sim_a.py`) : centres de WH1 lus dans le `map_data.esf` de WH1 ; le disque de 19 hex y est complet, centre et 16 hex
principaux sur la terre de la region, 3 hex de mer consecutifs dans l'anneau 2 ; `CAIME validate --town-slots
--town-sprawl` sans avertissement neuf. Seule inconnue : MapDataBuilder avec 3 hex de port tous en mer -> controle
obligatoire apres `process --all` (SETTLEMENT_INFO sans position 0xFFFF).

Comme `recentrer_emplacements.py`, lit `--layers`, ecrit `--out`, et n'ecrit jamais dans le map.hex : seules
`TownSlots` et `TownSprawl` sont a reimporter.

Usage :
    python placer_ports_wh1.py --layers <couches exportees> --md <md.json> --out <dossier> [--dry-run]
    (md.json : regions de notre map_data.esf avec leurs hex principaux et de port, `md_colonies.py`, 23.09.2026)
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recentrer_emplacements as RE                                # noqa: E402
from caime_layers import encode_flat                               # noqa: E402
from grow_town_slots import MAIN_SLOT, PORT_SLOT                   # noqa: E402

W, H = 400, 440
# hex de la colonie dans le map_data.esf de Warhammer 1 (SETTLEMENT_INFO)
CENTRES_WH1 = {
    "wh_dlc05_bordeleaux_bordeleaux": (35, 255),
    "wh_dlc05_brionne_brionne": (23, 183),
    "wh_dlc05_mousillon_mousillon": (53, 302),
}
SOL_MER = 15             # types de sol >= 15 : mer (relevé de la recherche du 23.09.2026, conforme a sim_a.py)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layers", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    couches = RE.charge(a.layers)
    for n in ("GroundTypes", "TownSlots", "TownSprawl"):
        if n not in couches:
            sys.exit(f"couche {n} absente de {a.layers}")
    sol = couches["GroundTypes"][0]
    slots = couches["TownSlots"][0].copy()
    sprawl = couches["TownSprawl"][0].copy()

    def ij(c):
        return c[1] * W + c[0]

    md = json.load(open(a.md, encoding="utf-8"))
    vus = set()
    for R in md["regions"]:
        if R["nom"] not in CENTRES_WH1:
            continue
        vus.add(R["nom"])
        anciens = set(map(tuple, R["prim"])) | set(map(tuple, R["port"]))
        for c in anciens:
            slots[ij(c)] = -1
            sprawl[ij(c)] = 0
        d, ordre = RE.disque(*CENTRES_WH1[R["nom"]], W, H)
        if len(d) != 19:
            sys.exit(f"{R['nom']} : disque incomplet ({len(d)} hex)")
        port = [c for c in d if sol[ij(c)] >= SOL_MER]
        if len(port) != 3 or CENTRES_WH1[R["nom"]] in port:
            sys.exit(f"{R['nom']} : {len(port)} hex de mer dans le disque (3 attendus, centre a terre)")
        for c in d:
            slots[ij(c)] = MAIN_SLOT
            sprawl[ij(c)] = 1
        for c in port:
            slots[ij(c)] = PORT_SLOT
        print(f"{R['nom']} : centre {CENTRES_WH1[R['nom']]} (WH1) ; port {sorted(port)} ; "
              f"{len(anciens)} anciens hex effaces")
    manque = set(CENTRES_WH1) - vus
    if manque:
        sys.exit(f"regions absentes de {a.md} : {sorted(manque)}")
    if a.dry_run:
        print("essai a blanc : rien d'ecrit")
        return
    os.makedirs(a.out, exist_ok=True)
    for nom, (val, f) in couches.items():
        v = {"TownSlots": slots, "TownSprawl": sprawl}.get(nom)
        if v is not None:
            open(os.path.join(a.out, f), "wb").write(encode_flat(nom, np.asarray(v).reshape(-1)))
            print(f"ecrit : {os.path.join(a.out, f)}")


if __name__ == "__main__":
    main()
