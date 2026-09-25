# The Season of Revelation, rebuilt in Warhammer III: modder's guide (DRAFT)

> Draft by the "IA et modding 3D" session, 25.09.2026, for Charles and the Construction session (which owns the
> documentation). Charles asked to open the workshop to other modders. Nothing here is published; the target place (for
> example `MODDERS.md` at the root) is Construction's call.

This workshop ports Warhammer I's mini-campaign **The Season of Revelation** (campaign `wh_dlc05_wood_elves`, map
`wh_dlc05_wood_elves_map_1`, 400 × 440 hexes, 61 regions) into **Total War: WARHAMMER III, patch 9.0**. Warhammer I's
map is kept as it is (relief, props, trees, textures, water), with Warhammer III gameplay and Warhammer I's story, and
ten playable legendary lords.

## 0. Legal line, read first

- **Warhammer I assets are never redistributed.** The private build pack contains files converted from Warhammer I, so
  it is not public. Anything shared with modders is **our code, our tables, our texts and our documentation only**,
  produced by `02-scripts\exporter_partageable.py` (allow-list, with an audit that refuses Warhammer I and CA files).
- To rebuild the map yourself you need **your own** copies of Warhammer I and Warhammer III, with their Assembly Kits.
- Non-commercial. Warhammer is © Games Workshop; Total War is © Creative Assembly / SEGA.

## 1. Requirements

| What | Version / note |
|---|---|
| Total War: WARHAMMER III + Assembly Kit | patch 9.0 |
| Total War: WARHAMMER + Assembly Kit | the source of the map and of the story |
| *Realm of the Wood Elves* DLC | needed to play the campaign (checked in the menu and at start) |
| Python | 3.12 (standard library only, except where a script says otherwise) |
| RPFM | 5.0.6, with `rpfm_server` running (pack building) |
| CAIME (Campaign Map Toolkit) | the fork `LeyZee/CampaignMapToolkit` (map layers, `map.hex`) |
| Terry, BOB | from the WH3 Assembly Kit (terrain export) |
| WinDbg `cdb.exe` | optional, for crash dumps |

## 2. Set up your machine

All paths live in **`02-scripts\chemins_atelier.py`**. Defaults are the original author's machine. Override them
either with environment variables (`SAISON_ATELIER`, `SAISON_WH3`, `SAISON_WH1`) or with a file
`atelier_local.json` at the workshop root (never shared):

```json
{"WH3": "D:/SteamLibrary/steamapps/common/Total War WARHAMMER III",
 "WH1": "D:/SteamLibrary/steamapps/common/Total War WARHAMMER"}
```

Check with `python 02-scripts\chemins_atelier.py` (every line should say `ok`).
*Migration in progress: scripts are being moved onto this module one by one; until then some still carry the original
paths.*

## 3. Layout

```
01-outils\      installed tools (RPFM, CAIME fork)
02-scripts\     one script = one job, usage at the top of each file (French)
03-references\  extracted reference data (WH1 extractions: private)
04-projets\saison-des-revelations\
   scripts-campagne\script\   campaign Lua (ours): campaign\wh_dlc05_wood_elves\saison_*.lua, frontend\mod\
   textes\textes_gameplay.json   every text we add, FR + EN (single source)
   startpos\, map_spec.json, ...  map data and generated files
05-journal\     dated evidence, logs, backups (large; start with 05-journal\INDEX.md)
CLAUDE.md       current state and rules (French)   GUIDE.md  know-how and known pitfalls (§ 15)
ERREURS-ET-LECONS.md   every mistake made, with the rule that prevents it (270 entries)
```

## 4. How the mod is built

**Keys.** Everything we create is keyed `saison_…`; Warhammer I content keeps its `wh_dlc05_…` keys. Every db table
file in the pack is named `saison_des_revelations`. **We never overwrite a CA table or a CA row**: the Immortal
Empires campaign must keep working with the mod enabled.

**Game data (db).** Rows are written into the Assembly Kit (`raw_data\db`) by **lots**: `donnees_campagne.py --lot
etapeN` (dry run), then `--apply` (backs up first, then checks the lot is idempotent). Each lot is a documented
function `lot_etapeN`. Which rows go into the pack is declared in `tables_gameplay.py` (`TABLES_LOTnn` entries: table,
key column, exact keys / prefix / filter). A lot kept out of the pack is named `EN_ATTENTE_TABLES_LOTnn`.

**Campaign scripts.** Loaded by `required.lua`, started by `saison_start.lua` (one protected call per system, logged).
Listeners are protected: a failing condition is logged once and never stops the event for the others.

**Texts.** Only in `textes_gameplay.json` (FR + EN). `verifier_textes.py` must report 0 defects;
`injecter_textes.py --apply` writes them into the language packs after the pack is built.

**Build recipes** (game and Terry closed, `rpfm_server` under 8 GB, Steam running):

1. Pack: `verifier_textes.py`, `verifier_groupes.py`, `build_pack.py`, then `injecter_textes.py --apply`. Read the log:
   each table of a new lot must appear with its row count.
2. Start position (after changing any `start_pos_*` table): `synchroniser_pack_startpos.py`, `valider_start_pos.py`
   (0 cells to fix), pack, `startpos_manuel.py … --sans-working-dir --ai-map-data`, `verifier_compteur_startpos.py`,
   then pack again (the pack wins over loose files).
3. Terrain chain (8 steps, about 30 min): see `GUIDE.md` § 12.3.
4. Tests: `essai_tours_auto.py --seigneur <lord|tous> --tours N`; results in `05-journal\2026-09-23-essais-auto\`.

**Checks before any pack:** `verifier_lua.py <scripts folder>` (0 errors) and `verifier_api_lua.py` (every called
name exists in CA's scripts, ours, or the game interface).

## 5. Pitfalls that cost us the most (details in ERREURS-ET-LECONS.md)

- A new db table in a played pack = a start-up test before announcing it (error 107).
- A campaign map linked to a DLC content pack makes the game quit at start, even with one row (error 268): lock the
  DLC by script (menu + campaign), never through the playable area.
- Without `--sans-working-dir`, the start-position generator exits in 9 s doing nothing (error 39).
- In CAIME, `Impassable = 1` means passable (error 40).
- The pack overrides loose files (error 58).
- Under `all_players_ai`, the player's faction does not play: its numbers mean nothing in tests (error 210).
- `rpfm_server` leaks memory at every pack: restart it above 8 GB (error 265).
- Never ship our file at a path CA uses, never replace a CA file outside the named exceptions of `build_pack.py`
  (error 254).
- A starting war in the start position is not stopped by closing war declarations by script: make peace first
  (25.09.2026, Grom and Aquitaine).

## 6. Working rules

- Back up before writing `raw_data\db` (lots do it; `05-journal\db-backups\`).
- Never delete: move to `99-archives\` with a note.
- Lore: official Games Workshop names and translations, nothing invented without a source.
- One change per test when validating the test driver (error 239).
