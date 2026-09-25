#!/usr/bin/env python3
"""
declare_map.py - déclare une carte de campagne NEUVE dans les tables XML de l'Assembly Kit
(raw_data\\db\\*.xml), exactement comme le ferait Dave, à partir d'une fiche JSON.

Tables écrites (celles que CAIME lit et que le guide § 5 exige) :
    campaign_maps, campaigns, provinces, regions, campaign_map_regions,
    region_to_province_junctions, campaign_map_roads, campaign_map_playable_areas,
    campaign_map_areas_of_interest (optionnelle)

Usage :
    python declare_map.py --spec 04-projets/<projet>/map_spec.json --asskit "<assembly_kit>"          # essai à blanc
    python declare_map.py --spec ... --asskit ... --apply                                               # écrit (avec sauvegarde)
    python declare_map.py --spec ... --asskit ... --undo --apply                                        # retire ce que la fiche déclare

Chaque enregistrement ajouté reçoit un record_uuid, un record_timestamp et la record_key que Dave
aurait produite ; un enregistrement dont la clé existe déjà est laissé tel quel (idempotent).
Avant toute écriture, chaque XML touché est copié dans --backup-dir (défaut : 05-journal\\db-backups\\<date>).
Encodage et fins de ligne du fichier d'origine sont conservés.

Fiche JSON minimale : voir 04-projets/ile_claude/map_spec.json.
"""

import argparse
import html
import json
import os
import re
import shutil
import sys
import time
import uuid
from datetime import datetime

WORKSHOP = r"C:\TotalWar-CampaignMap"


# ----------------------------------------------------------------------------- XML helpers

def esc(v):
    return html.escape(str(v), quote=True)


def plain(name, value):
    return f"<{name}>{esc(value)}</{name}>"


def approved(name, value):
    """Champ texte localisable, tel que Dave l'exporte."""
    v = esc(value)
    return f'<{name} state="APPROVED" last_approved_text="{v}" last_edit_user="bob">{v}</{name}>'


def record(table, key, fields, nl):
    """fields : liste de chaînes déjà rendues (ordre = ordre du schéma vanilla)."""
    head = (f'<{table} record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{int(time.time() * 1000)}" '
            f'record_key="{esc(key)}">')
    return nl.join([head] + fields + [f"</{table}>"])


class Table:
    def __init__(self, asskit, name):
        self.name = name
        self.path = os.path.join(asskit, "raw_data", "db", f"{name}.xml")
        raw = open(self.path, "rb").read()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.nl = "\r\n" if "\r\n" in text else "\n"
        self.text = text
        self.keys = set(re.findall(rf'<{name} [^>]*record_key="([^"]*)"', text))
        self.added, self.removed, self.skipped, self.updated = [], [], [], []

    def add(self, key, fields):
        if key in self.keys:
            self.skipped.append(key)
            return
        rec = record(self.name, key, fields, self.nl)
        marker = "</dataroot>"
        i = self.text.rfind(marker)
        if i < 0:
            raise SystemExit(f"{self.path}: pas de </dataroot>")
        self.text = self.text[:i] + rec + self.nl + self.text[i:]
        self.keys.add(key)
        self.added.append(key)

    def replace(self, key, fields):
        """Réécrit sur place le corps d'un enregistrement existant s'il diffère (21.09.2026 : les
        gabarits d'emplacement des régions elfes changent de valeur, pas de clé). L'en-tête garde
        son record_uuid ; seul record_timestamp est renouvelé. Rend True si quelque chose a changé."""
        pat = re.compile(rf'(<{self.name} [^>]*record_key="{re.escape(esc(key))}">)(.*?)(</{self.name}>)', re.S)
        m = pat.search(self.text)
        if not m:
            return False
        corps = self.nl + self.nl.join(fields) + self.nl
        if m.group(2) == corps:
            self.skipped.append(key)
            return False
        tete = re.sub(r'record_timestamp="\d+"', f'record_timestamp="{int(time.time() * 1000)}"', m.group(1))
        self.text = self.text[:m.start()] + tete + corps + m.group(3) + self.text[m.end():]
        self.updated.append(key)
        return True

    def remove(self, key):
        pat = re.compile(rf'<{self.name} [^>]*record_key="{re.escape(esc(key))}">.*?</{self.name}>\r?\n?', re.S)
        new, n = pat.subn("", self.text)
        if n:
            self.text = new
            self.keys.discard(key)
            self.removed.append(key)

    def save(self, backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(self.path, os.path.join(backup_dir, f"{self.name}.xml"))
        data = self.text.encode("utf-8")
        if self.bom:
            data = b"\xef\xbb\xbf" + data
        with open(self.path, "wb") as f:
            f.write(data)


# ----------------------------------------------------------------------------- the declaration

def build(spec):
    """Retourne {table: [(key, [fields]) ...]} dans l'ordre d'écriture."""
    m = spec["map"]
    c = spec["campaign"]
    mapname = m["name"]
    gek = m.get("game_expansion_key", "warhammer3")
    out = {t: [] for t in ("campaign_maps", "campaigns", "provinces", "regions", "campaign_map_regions",
                           "region_to_province_junctions", "campaign_map_roads",
                           "campaign_map_playable_areas", "campaign_map_areas_of_interest",
                           "campaign_map_settlements")}

    out["campaign_maps"].append((mapname, [
        plain("mapname", mapname), plain("minx", m.get("minx", 0)), plain("miny", m.get("miny", 0)),
        plain("maxx", m.get("maxx", 679)), plain("maxy", m.get("maxy", 556)), plain("game_expansion_key", gek)]))

    out["campaigns"].append((c["name"], [
        plain("campaign_name", c["name"]), approved("onscreen_name", c.get("onscreen", c["name"])),
        plain("description", c.get("description", "")), plain("map_name", mapname),
        plain("exportable", c.get("exportable", 1)), plain("bullet_list", ""),
        # `mask` renvoie à `campaign_map_masks` (trois lignes chez CA : `32`, `8`, `placeholder`,
        # identiques dans les deux jeux) et c'est la même valeur que le `map.hex` porte dans son
        # bloc d'entrées (§ 15 n° 15) : `32` pour les Elfes sylvains, `8` pour les Hommes-bêtes,
        # vide pour une campagne sans masque. Une carte portée depuis WH1 doit garder la sienne.
        plain("display_location", mapname), plain("mask", c.get("mask", "")),
        plain("available_for_mp", c.get("available_for_mp", 0)), plain("mp_sort_order", 0),
        plain("game_expansion_key", gek), plain("script_path", c.get("script_path", f"script/campaign/{c['name']}")),
        plain("battle_path", c.get("battle_path", mapname)), plain("terrain_location", c.get("terrain_location", mapname))]))

    for p in spec.get("provinces", []):
        out["provinces"].append((p["key"], [plain("key", p["key"]), approved("onscreen", p.get("onscreen", p["key"]))]))

    seen_rgb = {}
    for r in spec["regions"]:
        rgb = r.get("rgb", [0, 0, 0])
        is_sea = int(r.get("is_sea", 0))
        if not is_sea:
            if tuple(rgb) in seen_rgb:
                raise SystemExit(f"couleur RGB {rgb} partagée par {seen_rgb[tuple(rgb)]} et {r['key']} : chaque région terrestre doit être unique")
            seen_rgb[tuple(rgb)] = r["key"]
        out["regions"].append((r["key"], [
            plain("key", r["key"]), approved("onscreen", r.get("onscreen", r["key"])),
            plain("r", rgb[0]), plain("g", rgb[1]), plain("b", rgb[2]),
            approved("battle_name", r.get("battle_name", r.get("onscreen", r["key"]))),
            plain("in_encyclopedia", r.get("in_encyclopedia", 0)), plain("owner_bundle", r.get("owner_bundle", "")),
            plain("is_sea", is_sea), plain("faction_swapping_id", r.get("faction_swapping_id", "emp")),
            plain("hidden_settlement_override", r.get("hidden_settlement_override", 0)),
            plain("terrain_patch_area", r.get("terrain_patch_area", ""))]))
        out["campaign_map_regions"].append((mapname + r["key"], [plain("campaign_map", mapname), plain("region", r["key"])]))
        if r.get("province"):
            out["region_to_province_junctions"].append((r["key"] + r["province"], [
                plain("region", r["key"]), plain("province", r["province"]), plain("is_capital", r.get("is_capital", 0))]))

    for road in spec.get("roads", [{"key": f"{c['name']}_road_lv_1", "movement_cost": 80, "threshold": 0}]):
        out["campaign_map_roads"].append((road["key"], [
            plain("campaign", c["name"]), plain("key", road["key"]),
            plain("movement_cost", road.get("movement_cost", 80)), plain("threshold", road.get("threshold", 0)),
            plain("turns_required_to_downgrade_from", road.get("turns_required_to_downgrade_from", 1)),
            plain("turns_required_to_upgrade_to", road.get("turns_required_to_upgrade_to", 1))]))

    pa = spec.get("playable_area", {})
    index = int(pa.get("index", int(time.time()) % 2_000_000_000))
    # Le radical des sept fichiers de cette ligne est la **clé de campagne**, pas le nom de carte
    # (ERREURS-ET-LECONS A33). Vérifié sur les lignes de CA : prologue WH3 (`wh3_main_prologue_map.png`,
    # `wh3_main_prologue_lookup.tga`, `wh3_main_prologue_minimap.png`, `..._lookup_minimap.tga`,
    # `wh3_main_prologue.dds`, `wh3_main_prologue_lookup.dds`) et mini-campagne WH1
    # (`wh_dlc05_wood_elves_lookup.tga`, `wh_dlc05_wood_elves_minimap.png`). C'est aussi le nom que
    # CAIME donne au lookup qu'il produit : `<campagne>_lookup.bmp`.
    stem = pa.get("stem", c["name"])
    out["campaign_map_playable_areas"].append((str(index), [
        plain("mapname", mapname), plain("index", index), plain("minx", pa.get("minx", 0)), plain("maxx", pa.get("maxx", 533.74)),
        plain("sea_trade", pa.get("sea_trade", 0)), approved("onscreen_name", pa.get("onscreen", c.get("onscreen", c["name"]))),
        plain("map_file", pa.get("map_file", f"{stem}_map.png")), plain("overlay_file", f"{stem}_lookup.tga"),
        plain("radar_file", f"{stem}_minimap.png"),
        plain("meaningful_id", pa.get("meaningful_id", "main_rome_map")), plain("preview_width", 256), plain("preview_height", 256),
        plain("preview_border", 0), plain("minimap_lookup_file", f"{stem}_lookup_minimap.tga"),
        plain("is_available_in_custom_battle", 0), plain("terrain_folder", f"terrain/battles/{mapname}/"),
        plain("maxy", pa.get("maxy", 462.43)), plain("miny", pa.get("miny", 0)), plain("campaign_key", c["name"]),
        plain("frontend_image", pa.get("frontend_image", f"ui/frontend UI/campaign_images/{stem}.png")),
        plain("game_expansion_key", gek), approved("onscreen_description", pa.get("description", "")),
        plain("video", pa.get("video", "")), plain("is_mpc_available", 0),
        plain("campaign_overlay_lookup", f"{stem}_lookup.dds"), plain("campaign_overlay_map", f"{stem}.dds"),
        plain("quadtree_margin", 10), plain("sort_order", pa.get("sort_order", 0)),
        plain("campaign_overlay_map_text", f"{stem}_text.dds")]))

    for a in spec.get("areas_of_interest", []):
        out["campaign_map_areas_of_interest"].append((a, [plain("key", a), plain("campaign_map", mapname)]))

    # La colonie d'une région : une ligne par région qui en porte une. La clé et l'identifiant
    # valent tous deux « settlement:<région> », comme dans les tables livrées par CA.
    for s in spec.get("settlements", []):
        key = f"settlement:{s['region']}"
        out["campaign_map_settlements"].append((key, [
            plain("settlement_id", key), plain("climate_type", s.get("climate_type", "climate_temperate")),
            plain("citybar_height_offset", s.get("citybar_height_offset", 0)),
            plain("rotation", s.get("rotation", 0))]))

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--asskit", required=True)
    ap.add_argument("--apply", action="store_true", help="écrire réellement (sinon essai à blanc)")
    ap.add_argument("--undo", action="store_true", help="retirer les enregistrements que la fiche déclare")
    ap.add_argument("--backup-dir", default=os.path.join(WORKSHOP, "05-journal", "db-backups", datetime.now().strftime("%Y%m%d-%H%M%S")))
    a = ap.parse_args()

    if not os.path.isdir(os.path.join(a.asskit, "raw_data", "db")):
        raise SystemExit(f"Assembly Kit introuvable : {a.asskit}")
    with open(a.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)

    plan = build(spec)
    tables = {}
    for name, recs in plan.items():
        if not recs:
            continue
        t = Table(a.asskit, name)
        for key, fields in recs:
            if a.undo:
                t.remove(key)
            else:
                t.add(key, fields)
        tables[name] = t

    verb = "retiré" if a.undo else "ajouté"
    for name, t in tables.items():
        done = t.removed if a.undo else t.added
        print(f"{name:32} {verb} {len(done):3}  déjà présent {len(t.skipped):3}")
        for k in done:
            print(f"    {k}")

    if not a.apply:
        print("\nEssai à blanc : rien n'a été écrit. Relancer avec --apply.")
        return
    for t in tables.values():
        t.save(a.backup_dir)
    print(f"\nÉcrit. Sauvegardes des XML d'origine dans {a.backup_dir}")
    print("Rouvrir le projet dans CAIME (ou relancer la commande) pour qu'il relise la base.")


if __name__ == "__main__":
    main()
