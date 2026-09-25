#!/usr/bin/env python3
"""
spec_from_wh1.py - fabrique la fiche map_spec.json d'une carte de Warhammer 1 pour la redéclarer
dans Warhammer 3 avec declare_map.py (projet « La Saison des Révélations »).

Lit dans le kit WH1 (raw_data\\db\\*.xml, analyseur XML, jamais d'expression régulière sur les
lignes) : campaign_map_regions (les régions de la carte), regions (noms, couleurs, mer),
region_to_province_junctions (province, capitale), provinces (noms), campaign_map_roads (routes de la
campagne), campaign_maps (taille en hex), campaign_map_playable_areas (zone jouable en unités monde).

Les clés WH1 sont conservées telles quelles (aucune clé wh_dlc05_ de région n'existe dans la base
WH3, vérifié le 20.09.2026) ; la région partagée wh_main_sea_lake est déclarée aussi, absente de WH3.

Usage :
    python spec_from_wh1.py --map wh_dlc05_wood_elves_map_1 --campaign wh_dlc05_wood_elves
        --out 04-projets\\saison-des-revelations\\map_spec.json [--asskit-wh1 <kit WH1>] [--index 1758400002]
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit"


def rows(path):
    return [r for r in ET.parse(path).getroot() if r.tag != "edit_uuid"]


def rowdict(r):
    d = {"record_key": r.get("record_key", "")}
    for c in r:
        d[c.tag] = (c.text or "").strip()
    return d


def table(asskit, name):
    return [rowdict(r) for r in rows(os.path.join(asskit, "raw_data", "db", name + ".xml"))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", required=True)
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--asskit-wh1", default=WH1)
    ap.add_argument("--index", type=int, default=1758400002, help="index de campaign_map_playable_areas (unique dans WH3)")
    ap.add_argument("--onscreen", default=None, help="nom affiché de la campagne (défaut : celui de WH1)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    K = a.asskit_wh1
    map_regions = [r["region"] for r in table(K, "campaign_map_regions") if r["campaign_map"] == a.map]
    regions = {r["key"]: r for r in table(K, "regions")}
    provinces = {p["key"]: p for p in table(K, "provinces")}
    junctions = {j["region"]: j for j in table(K, "region_to_province_junctions")}
    roads = [r for r in table(K, "campaign_map_roads") if r["campaign"] == a.campaign]
    cmap = next(r for r in table(K, "campaign_maps") if r["mapname"] == a.map)
    area = next(r for r in table(K, "campaign_map_playable_areas") if r["mapname"] == a.map)
    camp = next(r for r in table(K, "campaigns") if r["campaign_name"] == a.campaign)

    spec_regions, used_provinces, seen_rgb, missing = [], [], {}, []
    for key in sorted(map_regions):
        r = regions.get(key)
        if r is None:
            missing.append(key)
            continue
        rgb = [int(r["r"]), int(r["g"]), int(r["b"])]
        is_sea = int(r.get("is_sea", 0))
        entry = {"key": key, "onscreen": r.get("onscreen", key), "battle_name": r.get("battle_name", r.get("onscreen", key)),
                 "in_encyclopedia": int(r.get("in_encyclopedia", 0)), "rgb": rgb}
        if is_sea:
            entry["is_sea"] = 1
        j = junctions.get(key)
        if j:
            entry["province"] = j["province"]
            entry["is_capital"] = int(j.get("is_capital", 0))
            if j["province"] not in used_provinces:
                used_provinces.append(j["province"])
        if not is_sea:
            if tuple(rgb) in seen_rgb:
                print(f"ATTENTION couleur {rgb} partagée par {seen_rgb[tuple(rgb)]} et {key}")
            seen_rgb[tuple(rgb)] = key
        spec_regions.append(entry)

    # Les colonies : Warhammer 1 ne connaît qu'un climat de colonie (« arid ») pour cette carte ;
    # Warhammer 3 en a onze. On choisit d'après la province, ce que le jeu affiche à l'écran de
    # colonie : les clairières d'Athel Loren en forêt magique, les cols en montagne, la Bretonnie
    # en tempéré.
    settlements_wh1 = {s["record_key"].split("settlement:", 1)[-1]
                       for s in table(K, "campaign_map_settlements")}
    MOUNTAIN = {"wh_dlc05_grey_mountains", "wh_dlc05_grey_mountains_2", "wh_dlc05_massif_orcal"}
    FOREST = {"wh_dlc05_anmyr", "wh_dlc05_argwylon", "wh_dlc05_arranoc", "wh_dlc05_atylwyth",
              "wh_dlc05_cavaroc", "wh_dlc05_cythral", "wh_dlc05_fyr_darric", "wh_dlc05_modryn",
              "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn", "wh_dlc05_tirsyth", "wh_dlc05_torgovann",
              "wh_dlc05_wydrioth"}
    settlements = []
    for r in spec_regions:
        if r["key"] not in settlements_wh1:
            continue
        province = r.get("province", "")
        climate = ("climate_mountain" if province in MOUNTAIN else
                   "climate_magicforest" if province in FOREST else "climate_temperate")
        settlements.append({"region": r["key"], "climate_type": climate})

    onscreen = a.onscreen or camp.get("onscreen_name", a.campaign)
    spec = {
        "_commentaire": f"Fiche générée par spec_from_wh1.py depuis le kit Warhammer 1 ({a.map}, campagne {a.campaign}). Clés WH1 conservées.",
        "map": {"name": a.map, "minx": int(float(cmap["minx"])), "miny": int(float(cmap["miny"])),
                "maxx": int(float(cmap["maxx"])), "maxy": int(float(cmap["maxy"])), "game_expansion_key": "warhammer3"},
        "campaign": {"name": a.campaign, "onscreen": onscreen, "description": camp.get("description", ""),
                     "available_for_mp": 0, "script_path": f"script/campaign/{a.campaign}"},
        "provinces": [{"key": p, "onscreen": provinces[p]["onscreen"]} for p in sorted(used_provinces)],
        "regions": spec_regions,
        "roads": [{"key": r["key"], "movement_cost": int(r["movement_cost"]), "threshold": int(r["threshold"]),
                   "turns_required_to_downgrade_from": int(r.get("turns_required_to_downgrade_from", 1)),
                   "turns_required_to_upgrade_to": int(r.get("turns_required_to_upgrade_to", 1))} for r in roads],
        "settlements": settlements,
        "playable_area": {"index": a.index, "onscreen": area.get("onscreen_name", onscreen),
                          "description": area.get("onscreen_description", ""),
                          "minx": float(area["minx"]), "miny": float(area["miny"]), "maxx": float(area["maxx"]), "maxy": float(area["maxy"]),
                          "stem": a.map, "meaningful_id": area.get("meaningful_id", "main_rome_map")},
        "areas_of_interest": [],
    }

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    land = sum(1 for r in spec_regions if not r.get("is_sea"))
    print(f"écrit {a.out}")
    print(f"  régions : {len(spec_regions)} ({land} terrestres, {len(spec_regions) - land} maritimes) ; provinces : {len(used_provinces)} ; routes : {len(roads)}")
    print(f"  carte {spec['map']['maxx']} x {spec['map']['maxy']} ; zone jouable {area['minx']}..{area['maxx']} x {area['miny']}..{area['maxy']}")
    caps = sum(1 for r in spec_regions if r.get("is_capital"))
    print(f"  capitales : {caps} ; régions sans province : {[r['key'] for r in spec_regions if 'province' not in r]}")
    if missing:
        print("  ABSENTES de regions.xml :", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
