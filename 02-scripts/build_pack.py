#!/usr/bin/env python3
"""
build_pack.py - fabrique le pack de « La Saison des Révélations » : les tables de la base et les
fichiers produits par CAIME, prêts pour `build_starpos`.

Un mod de campagne Warhammer 3 porte, d'après la lecture de « The Old World Campaign »
(`05-journal\\2026-09-20-inventaire-wh1\\phase-2-base-et-startpos.md` § 2) :

- `db\\<table>_tables\\<nom>` : la campagne, la zone jouable, la carte, les régions, les provinces,
  leurs rattachements, les colonies et les routes ;
- `campaign_maps\\<carte>\\` : les cinq fichiers produits par CAIME plus les images de lookup ;
- `terrain\\campaigns\\<carte>\\` : le terrain compilé par `compiler_terrain_bob.py` (21.09.2026) ;
- `campaigns\\<campagne>\\startpos.esf` ; (plus tard) les scripts.

Les tables sont lues dans l'Assembly Kit — donc exactement ce que `declare_map.py` y a écrit — et
recopiées dans le pack au format de RPFM, colonne par colonne, dans l'ordre du schéma du jeu.
Les colonnes que le kit ne connaît pas reçoivent la valeur vide, celles qu'il a en trop sont
abandonnées : le schéma du jeu fait foi.

Le pack doit être dans `<jeu>\\data\\` pour que RPFM accepte d'en construire le startpos.

Usage :
    python build_pack.py [--pack "<chemin du .pack>"] [--no-files]
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402
from lire_esf import convertir_vers_abca                             # noqa: E402
from declarer_gabarits_elfes import lignes_du_mod                    # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
AKIT = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/assembly_kit"
GAME_DATA = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data"
PACK = GAME_DATA + "/saison_des_revelations.pack"
MAP = "wh_dlc05_wood_elves_map_1"
CAMPAIGN = "wh_dlc05_wood_elves"
PREFIX = "saison_des_revelations"

# table du kit -> (table du jeu, colonne qui porte la clé de sélection, valeur attendue)
TABLES = [
    ("campaigns", "campaigns_tables", "campaign_name", CAMPAIGN),
    ("campaign_maps", "campaign_maps_tables", "mapname", MAP),
    ("campaign_map_playable_areas", "campaign_map_playable_areas_tables", "mapname", MAP),
    ("campaign_map_regions", "campaign_map_regions_tables", "campaign_map", MAP),
    ("campaign_map_settlements", "campaign_map_settlements_tables", "settlement_id", "settlement:wh_dlc05_"),
    ("campaign_map_roads", "campaign_map_roads_tables", "campaign", CAMPAIGN),
    ("regions", "regions_tables", "key", "wh_dlc05_"),
    ("provinces", "provinces_tables", "key", "wh_dlc05_"),
    ("region_to_province_junctions", "region_to_province_junctions_tables", "region", "wh_dlc05_"),
    # les deux seigneurs de l'ecran de selection propres a la mini-campagne, comme dans Warhammer 1
    # (21.09.2026, `ajouter_seigneurs_jouables.py`, journal § 22)
    ("frontend_faction_leaders", "frontend_faction_leaders_tables", "key", "wh_dlc05_political_party_mini_"),
    # sons d'ambiance par type de sol (vent de montagne, mer, marais...), comme les Empires (23.09.2026, session d'audit,
    # `donnees_campagne.py`)
    ("audio_campaign_environment_ground_type_sound_assignments",
     "audio_campaign_environment_ground_type_sound_assignments_tables", "map", MAP),
]
# Gabarits d'emplacement des colonies elfes, règles de WH3 (21.09.2026, 21 h, erreur 60) : clés
# exactes données par `declarer_gabarits_elfes.lignes_du_mod()` — un préfixe attraperait aussi les
# gabarits du Chêne des Âges de CA, qui commencent de la même façon.
for _table, (_colonne, _cles) in lignes_du_mod().items():
    TABLES.append((_table, _table + "_tables", _colonne, _cles))
# Les arbres de WH1 avec leurs modèles (22.09.2026, `arbres_wh1.py`) : identifiants neufs `wh1_*` et leurs
# variantes par culture ; aucune ligne de CA.
from arbres_wh1 import ArbresWH1                                     # noqa: E402
_ARBRES = ArbresWH1()
for _table in ("campaign_tree_ids", "campaign_tree_variants"):
    TABLES.append((_table, _table + "_tables", "tree_id", _ARBRES.cles()))
# Bandeaux des colonies relevés par niveau de bâtiment, à la manière de CA (25.09.2026, décision de Charles « niveaux de
# CA » : clés de CA, dont une ligne de CA changée ; `bandeaux_niveaux.py`)
from bandeaux_niveaux import BANDEAUX                                # noqa: E402
TABLES.append(("settlement_nameplate_offsets_per_primary_building_levels",
               "settlement_nameplate_offsets_per_primary_building_levels_tables", "building_level", tuple(BANDEAUX)))
# Données de campagne (gameplay) de la session « IA et modding 3D » (23.09.2026) : lots TABLES_LOT<n> de
# `tables_gameplay.py`, dont elle est propriétaire ; aucune n'est lue par la génération du startpos.
import tables_gameplay                                               # noqa: E402
# Tables qu'aucun pack ne doit porter (23.09.2026, 02 h 30) : avec la jonction de propriété de la zone jouable (verrou du
# DLC, lot 2), le jeu se ferme tout seul 8 s après le lancement (TerminateProcess code 0, sans vidage ni message ; pile
# sur `campaign_map_playable_area_ownership_content_pack_junctions`, cdb). Le verrou passe par le script
# `saison_verrou_dlc.lua`.
# (25.09.2026, 17 h 05, demande de Charles : « le verrou avant de lancer la partie », cadenas de la campagne comme aux
# Empires) ESSAI : la table revient avec UN SEUL paquet pour notre zone (wh1_wood_elves ; lot 2 de l'IA), l'hypothèse
# de l'erreur 107 étant les deux paquets. Essai de démarrage obligatoire (le jeu doit tenir 45 s) ; s'il se ferme,
# remettre la table ici. RÉSULTAT (25.09.2026, 17 h 55, pack de 17 h 54) : le jeu se ferme encore 20 s après le lancement,
# code 0, comme le 23.09 (essais Duc et Kemmler) : une zone jouable rattachée à un paquet de DLC est refusée même avec UNE
# seule ligne (aucune carte de CA n'est verrouillée ainsi ; CA verrouille par faction). Table de nouveau exclue ; le
# verrou visible avant la partie passe par le script du menu (plan B, saison_choix_par_defaut.VERROU_MENU).
TABLES_EXCLUES = {"campaign_map_playable_area_ownership_content_pack_junctions_tables"}
# Scripts de la session d'audit tenus hors du pack jusqu'à correction (chemins du pack, en minuscules). 23.09.2026,
# 05 h 35 : à l'essai de démarrage, sans aucun clic, la vidéo d'intro de WH1 s'est lancée au menu 11,7 s après
# `UICreated` (`script_log_230926_0535.txt`) ; au bout, le script simule un clic sur « Commencer la campagne ».
# Fichiers qu'aucune citation ne relie à ce que le jeu charge (audit du poids de la carte, session du rendu, 24.09.2026,
# rapport-pack-textures.md § 3.1) : copies sous terrain/ des textures de montagne (les montagnes citent leurs copies sous
# rigidmodels/_wh1/, GUIDE n° 138), sol brûlé et écran d'avant-bataille du Chaos jamais posés : ~109 Mo. Les textures
# factices `test_*` de ces dossiers restent (des modèles les citent). Filtrés à l'ajout et retirés du pack (rouvert).
NON_EMBARQUES = ("terrain/textures/campaign/default/empire_mountain_large_01/",
                 "terrain/textures/campaign/default/empire_mountain_small_01/",
                 "terrain/textures/campaign/default/badlands_mountain_large_01/",
                 "terrain/textures/campaign/default/badlands_mountain_small_01/",
                 "terrain/textures/campaign/default/burnt_ground/",
                 "rigidmodels/_wh1/textures_terrain/campaign/default/burnt_ground/",
                 "rigidmodels/campaign/generic_props/prebattle_screens/chaos/")


# ... et la liste exacte des textures de WH1 à leur chemin d'origine que rien de NOS fichiers ne cite (même audit,
# `05-journal\2026-09-23-rendu-carte\restes-textures-a-ne-pas-embarquer.txt`, 94 fichiers) : 61 d'entre elles étaient
# lues au chemin exact par des modèles de CA de toutes les campagnes, mod actif (règle « les campagnes coexistent »).
def _liste_non_embarques():
    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "05-journal",
                          "2026-09-23-rendu-carte", "restes-textures-a-ne-pas-embarquer.txt")
    if not os.path.exists(chemin):
        return frozenset()
    with open(chemin, encoding="utf-8") as f:
        return frozenset(l.split("\t")[0].strip().replace("\\", "/").lower() for l in f
                         if l.strip() and not l.startswith("#"))


NON_EMBARQUES_EXACTS = _liste_non_embarques()
# 25.09.2026 (chaîne 15, accord de Charles ; règle « les campagnes coexistent ») : nos substituts posés À DES CHEMINS DE
# CA que CA ne livre pas mais que ses modèles citent (283 arbres de CA lisaient notre flatnormal.dds dans toutes les
# campagnes). Nos modèles de WH1 citent désormais des copies à nous (fichiers_wh1.SUBSTITUTS_A_NOUS) ; ceux-ci ne sont
# plus embarqués et sont retirés du pack rouvert (erreur 203).
SUBSTITUTS_CA_RETIRES = frozenset(p.lower() for p in (
    "rigidmodels/campaign/beastmen/textures/test_black.dds",
    "rigidmodels/campaign/beastmen/textures/test_gloss_map.dds",
    "rigidmodels/campaign/beastmen/textures/test_mask.dds",
    "rigidmodels/campaign/dlc02_blood_pack/textures/test_mask.dds",
    "rigidmodels/campaign/settlements/textures/flatnormal.dds",
    "rigidmodels/campaign/settlements/textures/test_black.dds",
    "rigidmodels/campaign/settlements/textures/test_gloss_map.dds",
    "rigidmodels/campaign/settlements/textures/test_gray.dds",
    "rigidmodels/campaign/settlements/textures/test_mask.dds",
    "rigidmodels/campaign/vegetation/textures/flatnormal.dds",
    "rigidmodels/campaign/vegetation/textures/test_black.dds",
    "rigidmodels/campaign/vegetation/textures/test_gloss_map.dds",
    "rigidmodels/campaign/vegetation/textures/test_gray.dds",
    "rigidmodels/campaign/vegetation/textures/test_mask.dds",
    "rigidmodels/campaign/wood_elves/textures/test_mask.dds"))
NON_EMBARQUES_EXACTS = NON_EMBARQUES_EXACTS | SUBSTITUTS_CA_RETIRES


def garde_substituts_ca():
    """Aucun de NOS modèles ne doit encore citer un chemin de SUBSTITUTS_CA_RETIRES (sinon il perdrait sa texture en jeu :
    modeles_wh1 --apply n'a pas repointé). 1 171 citations avant le repointage (session du rendu, 25.09.2026, 03 h 15)."""
    projet = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
    motifs = [p.encode("ascii") for p in SUBSTITUTS_CA_RETIRES]
    restes = {}
    for d, _, fs in os.walk(projet):
        for f in fs:
            if f.lower().endswith((".rigid_model_v2", ".wsmodel", ".material", ".xml.material")):
                b = open(os.path.join(d, f), "rb").read().lower().replace(b"\\", b"/")
                for m in motifs:
                    if m in b:
                        restes[m.decode()] = restes.get(m.decode(), 0) + 1
    if restes:
        raise SystemExit("substituts de CA encore cités par nos modèles (lancer modeles_wh1 --apply avec "
                         f"SUBSTITUTS_A_NOUS) : {sorted(restes.items())[:5]}… ({sum(restes.values())} citations)")


def non_embarque(rel):
    r = rel.lower()
    return r in NON_EMBARQUES_EXACTS or any(
        r.startswith(p) and not r[len(p):].startswith("test_") and "/" not in r[len(p):] for p in NON_EMBARQUES)


SCRIPTS_ECARTES = set()             # vidéo avant chargement réintégrée (05 h 38 : écran et bouton visibles exigés,
                                    # clic pris après 1 s ; l'essai du 05 h 35 était sans doute un clic de Charles)
# Revue du pack avant la bêta (25.09.2026, 19 h 15 ; accord de la session « IA et modding 3D ») : scripts que
# `required.lua` ne charge pas (essais à drapeau, copiés dans le pack d'essai quand il le faut ; mécaniques éteintes
# pour la bêta : salles tombées, décision de Charles ; lieux du lore, tables du lot 22 hors pack) : hors du pack.
SCRIPTS_ECARTES |= {f"script/campaign/wh_dlc05_wood_elves/{n}.lua" for n in (
    "saison_diagnostic", "saison_essai_corruption", "saison_essai_drycha_hors_harde", "saison_essai_filet",
    "saison_essai_isoler", "saison_essai_sortie", "saison_essai_tour11", "saison_essai_transfert",
    "saison_lieux", "saison_salles")}
for _nom in sorted(n for n in dir(tables_gameplay) if n.startswith("TABLES_LOT")):
    TABLES.extend(t for t in getattr(tables_gameplay, _nom) if t[1] not in TABLES_EXCLUES)


ESF_KIT, ESF_JEU = 0xABCB, 0xABCA
ESF_CORRIGES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "esf-corriges")


def corrige_esf(chemins):
    """Découverte du 21.09.2026, mesurée en jeu (journal `phase-2-startpos-temoin.md` § 14) :
    **MapDataBuilder du kit écrit `map_data.esf` au format ESF `0xABCB`, alors que Warhammer 3 ne
    consomme que `0xABCA`** — la magie de tous les `map_data.esf` livrés dans les packs de CA.
    Avec `0xABCB`, le jeu laisse son tableau « une entrée de 10 octets par hex » à sa valeur de
    remplissage `0xFFFF0000`, et la génération du startpos meurt dans l'IA de campagne à
    `Warhammer3+0x2A4401A`. Vérifié par aller-retour : en `0xABCA` le plantage disparaît, en
    `0xABCB` il revient à l'identique.

    La seule différence entre les deux formats, sur ces fichiers, est la **largeur du champ de
    longueur des deux tables de chaînes** en fin de fichier : `u16` pour `0xABCA`, `u32` pour
    `0xABCB`. L'en-tête, l'arbre de nœuds et la table des noms sont identiques. Changer la seule
    magie ne suffit donc pas : le jeu décale alors sa lecture et indexe hors du tableau des
    chaînes (plantage à `Warhammer3+0x4946BB`). `lire_esf.convertir_vers_abca` fait la vraie
    conversion et relit le résultat pour le vérifier.

    Le fichier du kit n'est jamais touché : on écrit une copie, puisque `process --map-data` le
    régénère. Rend la liste des chemins à mettre dans le pack."""
    os.makedirs(ESF_CORRIGES, exist_ok=True)
    sortie, corriges = [], 0
    for p in chemins:
        if not p.lower().endswith(".esf"):
            sortie.append(p)
            continue
        with open(p, "rb") as f:
            blob = f.read()
        if len(blob) < 4 or int.from_bytes(blob[:4], "little") != ESF_KIT:
            sortie.append(p)
            continue
        converti = convertir_vers_abca(blob)
        cible = os.path.join(ESF_CORRIGES, os.path.basename(p))
        with open(cible, "wb") as f:
            f.write(converti)
        sortie.append(cible)
        corriges += 1
        print(f"  ESF converti {ESF_KIT:#x} -> {ESF_JEU:#x} : {os.path.basename(p)} "
              f"({len(blob)} -> {len(converti)} octets)")
    if not corriges:
        print("  aucun ESF à convertir (déjà en 0xABCA)")
    return sortie


def kit_rows(table, column, value):
    path = os.path.join(AKIT, "raw_data", "db", table + ".xml")
    out = []
    for r in ET.parse(path).getroot():
        if r.tag == "edit_uuid":
            continue
        d = {c.tag: (c.text or "").strip() for c in r}
        field = d.get(column, "")
        if callable(value):
            # 25.09.2026 (lot 33, clé composée faction + agent + sous-type) : filtre sur la ligne entière, pour ne prendre
            # que NOS lignes quand une colonne seule prendrait aussi celles de CA
            garde = bool(value(d))
        elif isinstance(value, (tuple, list)):
            garde = field in value                  # liste de clés exactes
        else:
            garde = field == value or (value.endswith("_") and field.startswith(value))
        if garde:
            out.append(d)
    return out


def processed_fields(sid, definition):
    """RPFM veut les lignes au format « traité » : groupes de couleur fusionnés, bits et
    énumérations dépliés. Sans cela, l'enregistrement refuse la ligne (« expected a row with 6
    fields, but we got a row with 8 »)."""
    answer = json.loads(text(call(sid, "fields_processed", {"definition": json.dumps(definition)}, 20)))
    fields = answer if isinstance(answer, list) else list(answer.values())[0]
    return [(f["name"], f["field_type"]) for f in fields]


def cell(value, ftype):
    if ftype == "Boolean":
        return {"Boolean": value in ("1", "true", "True")}
    if ftype in ("I16", "I32", "I64"):
        return {ftype: int(float(value or 0))}
    if ftype in ("F32", "F64"):
        return {ftype: float(value or 0)}
    if ftype in ("OptionalStringU8", "OptionalStringU16"):
        return {ftype: value}
    if ftype == "ColourRGB":
        return {"ColourRGB": value or "000000"}
    return {"StringU8": value}


# 25.09.2026 : rpfm_server garde la mémoire de chaque pack construit (69,7 Go validés après une nuit de packs ; 111 Go
# réservés sur 127,7 sur la machine). Soupçonné du plantage de rendu `Warhammer3.exe+0x1AC7576`, puis mis hors de cause
# (plantage revenu sur un PC redémarré, erreur 265) ; la fuite reste. Au-delà du seuil, on refuse de construire :
# relancer rpfm_server (`lancer-outils.ps1 -Outil rpfm-server`) avant le pack.
SEUIL_RPFM_GO = 8


def garde_memoire_rpfm():
    import subprocess
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process rpfm_server -ErrorAction SilentlyContinue | Measure-Object PrivateMemorySize64 -Sum).Sum"],
                       capture_output=True, text=True)
    try:
        go = int(r.stdout.strip() or 0) / 2 ** 30
    except ValueError:
        return
    print(f"  rpfm_server : {go:.1f} Go de mémoire privée (seuil {SEUIL_RPFM_GO} Go)")
    if go > SEUIL_RPFM_GO:
        raise SystemExit(f"rpfm_server tient {go:.1f} Go (fuite, plantages de rendu du 25.09) : le fermer et le relancer "
                         "(lancer-outils.ps1 -Outil rpfm-server), puis refaire le pack.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default=PACK)
    ap.add_argument("--no-files", action="store_true", help="ne pas ajouter les fichiers de carte")
    ap.add_argument("--sans-journal", action="store_true",
                    help="pack « à jouer » : sans script/enable_console_logging (journal de script éteint ; décision de "
                         "Charles du 24.09.2026, T21 : journal allumé tant que durent les essais)")
    # 25.09.2026 (audit du contenu du pack, point 2 ; accord de Charles) : zstd, comme les packs de CA en 9.0 (847 → ~461 Mio
    # à lire). Éteint par défaut tant qu'un essai de démarrage ne l'a pas validé (erreur 107).
    ap.add_argument("--zstd", action="store_true", help="compresser le pack en zstd (RPFM change_compression_format)")
    # 25.09.2026 (bêta pour des testeurs, Charles) : le pack est d'ordinaire ROUVERT (erreur 203 : les restes d'anciennes
    # constructions y restent tant qu'on ne les retire pas). Pour une version livrée : pack recréé de zéro, l'ancien rangé
    # (jamais supprimé) dans 05-journal\pack-backups\.
    ap.add_argument("--neuf", action="store_true", help="recréer le pack de zéro (l'ancien est rangé dans pack-backups)")
    ap.add_argument("--sortie", action="store_true", help="version livrée : --neuf et --sans-journal")
    a = ap.parse_args()
    if a.sortie:
        a.neuf = a.sans_journal = True
    if a.sans_journal:
        SCRIPTS_ECARTES.add("script/enable_console_logging")
    sys.stdout.reconfigure(encoding="utf-8")
    if not a.no_files:
        garde_substituts_ca()
    garde_memoire_rpfm()
    if a.neuf and os.path.exists(a.pack):
        import shutil
        import time
        rangement = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "05-journal", "pack-backups")
        os.makedirs(rangement, exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(a.pack))
        dest = os.path.join(rangement, f"{base}-{time.strftime('%Y%m%d-%H%M%S')}{ext}")
        shutil.move(a.pack, dest)
        print(f"  pack à neuf : l'ancien est rangé dans {dest}")

    sid = session()
    call(sid, "set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": True}, 2)
    if not os.path.exists(a.pack):
        call(sid, "new_pack", {}, 3)
        lst = json.loads(text(call(sid, "list_open_packs", {}, 4)))
        key = [e[0] if isinstance(e, list) else e for v in lst.values() for e in v][0]
        call(sid, "save_pack_as", {"pack_key": key, "path": a.pack}, 5)
        call(sid, "close_all_packs", {}, 6)
    call(sid, "open_packfiles", {"paths": [a.pack]}, 7)
    key = a.pack
    # une table exclue qu'une construction précédente aurait laissée dans le pack en est retirée (le pack est rouvert,
    # jamais recréé : ses fichiers restent tant qu'on ne les retire pas)
    presents = {c.replace("\\", "/").lower() for c, _ in __import__("contenu_pack").entrees(a.pack)} \
        if os.path.exists(a.pack) else set()
    for t in sorted(TABLES_EXCLUES):
        chemin = f"db/{t}/{PREFIX}"
        if chemin.lower() in presents:
            call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
            print(f"  {t:42s} retirée du pack (table exclue)")
    # Tables qui REMPLACENT celles de CA (fichier `data__`, le seul de db.pack pour elles ; 23.09.2026, plantage de
    # l'infobulle des bosquets : `tables_gameplay.REMPLACE_CA`) : l'ancien fichier à notre nom est retiré.
    # Fichiers restés d'anciennes constructions ou que le jeu ne lit pas (audit de l'interface, 23.09.2026, C5 et C7) :
    # l'image de correspondance de CAIME en .bmp (13 Mo) et l'ancienne minicarte, qu'aucune colonne ne déclare.
    for chemin in (f"campaign_maps/{MAP}/wh_dlc05_wood_elves_lookup.bmp",
                   f"campaign_maps/{MAP}/wh_dlc05_wood_elves_map_minimap.png",
                   f"campaign_maps/{MAP}/wh_dlc05_wood_elves_map_minimap.tga"):
        if chemin.lower() in presents:
            call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
            print(f"  {chemin} retiré du pack (périmé ou inutile)")
    # Restes d'anciennes constructions relevés le 24.09.2026 à 05 h 40 (erreur 203) : 2 798 anciens maillages de rivière
    # `river_wh1_<n>` (nommage d'avant les tuiles `river_wh1_cXX_YY`, orphelins). Aucune source actuelle ne les fournit ; le
    # pack étant rouvert, ils restaient. (Les six textures `ice0|ice2` aux chemins de CA ne sont PAS des restes : c'est
    # l'exception voulue `textures_sol_wh1.remplacements_glace`, ajoutée plus bas.)
    restes = re.compile(r"^(terrain/campaigns/%s/models/river_wh1_\d+\.wsmodel(\.rigid_model_v2)?|%s)$"
                        % (MAP, "|".join(re.escape(p) + r"(?!test_)[^/]+" for p in NON_EMBARQUES)))
    retires = [c for c in sorted(presents) if restes.match(c) or c in NON_EMBARQUES_EXACTS]
    # 25.09.2026 (audit du contenu du pack, point 6) : dossiers du pack remplis par UN SEUL dossier du projet (vérifié : aucun
    # autre ne les fournit) ; tout fichier présent au pack sans source actuelle est un reste (233 falaises `cliff_custom`
    # retirées par la côte lissée, `river_wh1_c20_02`…). Retiré avant les ajouts, qui remettent ce qui existe.
    projet = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
    for prefixe, dossier in (("rigidmodels/_wh1/campaign/montagnes/", "montagnes-wh1"),
                             (f"terrain/campaigns/{MAP}/models/river_wh1_", "rivieres-wh1")):
        racine = os.path.join(projet, dossier)
        if not os.path.isdir(racine):
            continue
        sources = {os.path.relpath(os.path.join(d, f), racine).replace("\\", "/").lower()
                   for d, _, fs in os.walk(racine) for f in fs}
        orphelins = [c for c in sorted(presents) if c.startswith(prefixe) and c not in sources and c not in retires]
        if len(orphelins) > 0.5 * max(1, sum(1 for s in sources if s.startswith(prefixe))) and len(orphelins) > 300:
            raise SystemExit(f"{prefixe} : {len(orphelins)} fichiers du pack sans source dans {dossier} "
                             "(dossier source vide ou en cours de réécriture ?) ; rien retiré")
        retires += orphelins
        if orphelins:
            print(f"  {len(orphelins)} fichier(s) de {prefixe} sans source dans {dossier} : retirés (ex. {orphelins[0]})")
    for i in range(0, len(retires), 200):
        call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": c} for c in retires[i:i + 200]])}, 7)
    if retires:
        print(f"  {len(retires)} restes d'anciennes constructions retirés du pack (erreur 203)")
    for chemin in sorted(SCRIPTS_ECARTES):
        if chemin in presents:
            call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
            print(f"  {chemin} retiré du pack (script écarté jusqu'à correction)")
    remplace_ca = getattr(tables_gameplay, "REMPLACE_CA", {})
    for t in sorted(remplace_ca):
        chemin = f"db/{t}/{PREFIX}"
        if chemin.lower() in presents:
            call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
            print(f"  {t:42s} ancien fichier {PREFIX} retiré (la table remplace désormais celle de CA)")
    # L'inverse : un fichier `db/<table>/<nom de CA>` d'une construction précédente dont la table ne remplace PLUS celle
    # de CA (23.09.2026 : clés à nous pour les Racines du monde, REMPLACE_CA vidé). Le pack étant rouvert, il resterait
    # et masquerait toujours la table de CA dans toutes les campagnes.
    for chemin in sorted(presents):
        morceaux = chemin.split("/")
        if len(morceaux) == 3 and morceaux[0] == "db" and morceaux[2] != PREFIX.lower() \
                and remplace_ca.get(morceaux[1]) != morceaux[2]:
            call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
            print(f"  {chemin} retiré du pack (table de CA qui n'est plus remplacée)")

    total = 0
    # Plusieurs entrées pour une même table (23.09.2026 : gabarits des elfes de `declarer_gabarits_elfes` et monuments de
    # la session gameplay dans `slot_templates`) : leurs lignes sont réunies dans UN fichier ; sinon le second fichier,
    # au même nom, écraserait le premier.
    groupes, lignes_pack = {}, {}
    for kit_table, game_table, column, value in TABLES:
        groupes.setdefault(game_table, []).append((kit_table, column, value))
    for game_table, entrees in groupes.items():
        kit_table = entrees[0][0]
        rows, vues = [], set()
        for kt, column, value in entrees:
            for r in kit_rows(kt, column, value):
                cle = tuple(sorted(r.items()))
                if cle not in vues:
                    vues.add(cle)
                    rows.append(r)
        if len(entrees) > 1:
            print(f"  {game_table:42s} {len(entrees)} entrées réunies")
        lignes_pack[game_table] = rows
        if not rows:
            print(f"  {game_table:42s} aucune ligne dans le kit")
            continue
        nom_fichier = remplace_ca.get(game_table, PREFIX)
        path = f"db/{game_table}/{nom_fichier}"
        answer = json.loads(text(call(sid, "get_table_version_from_dependency_pack_file",
                                      {"value": game_table}, 8)))
        if "I32" not in answer:
            # Warhammer 3 n'a pas toutes les tables de Warhammer 1 : `campaign_maps_tables` par
            # exemple n'existe plus, la carte se déclare par `campaigns.map_name` et la zone jouable.
            print(f"  {game_table:42s} absente de Warhammer 3, ignorée")
            continue
        version = answer["I32"]
        call(sid, "new_packed_file", {"pack_key": key, "path": path,
                                      "new_file": json.dumps({"DB": [nom_fichier, game_table, version]})}, 9)
        decoded = json.loads(text(call(sid, "decode_packed_file",
                                       {"pack_key": key, "path": path, "source": "PackFile"}, 10)))
        holder = decoded["DBRFileInfo"][0]
        fields = processed_fields(sid, holder["table"]["definition"])

        def build(row):
            out = []
            for name, ftype in fields:
                if ftype == "ColourRGB":
                    # le groupe de couleur fusionne les colonnes r, g, b du kit
                    rgb = tuple(int(row.get(c, 0) or 0) for c in ("r", "g", "b"))
                    out.append({"ColourRGB": "%02X%02X%02X" % rgb})
                else:
                    out.append(cell(row.get(name, ""), ftype))
            return out

        holder["table"]["table_data"] = [build(r) for r in rows]
        res = call(sid, "save_packed_file_from_view",
                   {"pack_key": key, "path": path, "data": json.dumps({"DB": holder})}, 11)
        ok = "Success" in text(res)
        print(f"  {game_table:42s} {len(rows):5d} lignes, {len(fields):2d} colonnes  {'ok' if ok else text(res)[:80]}"
              + (f"  (REMPLACE {path})" if nom_fichier != PREFIX else ""))
        total += len(rows) if ok else 0

    if not a.no_files:
        # Erreur du 20.09.2026 (ERREURS-ET-LECONS A32) : `os.listdir` ne descend pas dans les
        # sous-dossiers, et `display\borders\borders.pbd` n'entrait donc jamais dans le pack alors
        # que le jeu le lit sous ce chemin exact (vérifié sur le prologue vanilla). On parcourt
        # l'arborescence et on garde les chemins relatifs ; `debug\` est écarté, ce sont les
        # images de contrôle de CAIME.
        produced = os.path.join(AKIT, "working_data", "campaign_maps", MAP)
        files = []
        for root, dirs, names in os.walk(produced):
            dirs[:] = [d for d in dirs if d != "debug"]
            # le .bmp de correspondance de CAIME (13 Mo) : le jeu lit le .tga et le .dds, jamais le .bmp
            files += [os.path.join(root, n) for n in names if not n.lower().endswith(".bmp")]
        rel = [os.path.relpath(f, produced).replace("\\", "/") for f in files]
        dest = [{"File": f"campaign_maps/{MAP}/{r}"} for r in rel]
        sources = corrige_esf(files)
        # Les arbres de WH1 (22.09.2026, 22 h, `arbres_wh1.liste_wh1`) : la liste compilée des arbres de WH1 elle-même
        # (chaque arbre à sa position de WH1, essences `wh1_*`, hauteur recalée sur notre sol), écrite par
        # terrain_wh1_vers_terry.py, remplace celle que BOB a placée d'après tree.tif.
        from arbres_wh1 import SORTIE_LISTE, lire_liste
        for k, r in enumerate(rel):
            if r.endswith("display/trees/trees.campaign_tree_list"):
                if not os.path.exists(SORTIE_LISTE):
                    raise SystemExit(f"{SORTIE_LISTE} absent : lancer terrain_wh1_vers_terry.py --apply")
                _, groupes = lire_liste(open(SORTIE_LISTE, "rb").read())
                # rochers et herbes de montagne de CA (23.09.2026, session du rendu) : identifiants de CA déjà dans db.pack
                import ajouts_carte_wh3
                ca = set(ajouts_carte_wh3.IDS_ARBRES_CA)
                inconnus = sorted({nom for nom, _ in groupes if not nom.startswith("wh1_") and nom not in ca})
                if inconnus:
                    raise SystemExit(f"liste des arbres : identifiants ni wh1_* ni ajouts de CA déclarés : {inconnus[:5]}")
                sources[k] = SORTIE_LISTE
                n_ca = sum(len(g) for nom, g in groupes if nom in ca)
                print(f"  arbres de WH1 à leurs positions de WH1 : {sum(len(g) for _, g in groupes) - n_ca} arbres ; "
                      f"rochers et herbes de montagne de CA : {n_ca} en {sum(1 for nom, _ in groupes if nom in ca)} "
                      f"identifiants")
        res = call(sid, "add_packed_files", {"pack_key": key, "source_paths": sources,
                                             "destination_paths": json.dumps(dest)}, 12)
        print(f"  fichiers de carte ajoutés : {len(files)}  {'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")

    # Minicarte et images de correspondance au format de CA (21.09.2026, § 21 du journal) :
    # `preparer_minicarte.py` les fabrique dans le projet ; elles remplacent, sous les mêmes noms,
    # les images de Warhammer 1 que `ajouter_images_campagne.py` avait mises dans le pack.
    images = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "images-carte")
    if os.path.isdir(images) and not a.no_files:
        noms = sorted(n for n in os.listdir(images)
                      if n.lower().endswith((".png", ".tga")) and not n.startswith("controle"))
        if noms:
            call(sid, "add_packed_files", {"pack_key": key,
                                           "source_paths": [os.path.join(images, n) for n in noms],
                                           "destination_paths": json.dumps(
                                               [{"File": f"campaign_maps/{MAP}/{n}"} for n in noms])}, 15)
            print(f"  images de carte ajoutées : {', '.join(noms)}")

    # La vignette de la campagne dans l'écran Nouvelle campagne (21.09.2026, journal § 22) : la mise
    # en page de CA lit `frontend_image` et lui accole `_button` et `_vertical`.
    # `preparer_images_campagne.py` fabrique les trois ; on les range dans le dossier que déclare
    # la ligne de zone jouable, casse comprise, pour que la vérification ci-dessous les retrouve.
    vignettes = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "images-campagne")
    if os.path.isdir(vignettes) and not a.no_files:
        noms = sorted(n for n in os.listdir(vignettes)
                      if n.lower().endswith(".png") and not n.startswith("controle"))
        if noms:
            call(sid, "add_packed_files", {"pack_key": key,
                                           "source_paths": [os.path.join(vignettes, n) for n in noms],
                                           "destination_paths": json.dumps(
                                               [{"File": f"{DOSSIER_VIGNETTES}/{n}"} for n in noms])}, 16)
            print(f"  images de la vignette ajoutées : {', '.join(noms)}")

    # Le startpos, une fois généré (21.09.2026) : `startpos_manuel.py` le fait écrire par le jeu dans
    # `<jeu>\data\campaigns\<campagne>\startpos.esf` ; on en garde la copie de référence dans le
    # projet et on l'embarque dans le pack, là où CA range les siens. Il est mis **tel que le jeu
    # l'a écrit** (ESF 0xABCB, contenu compressé compris) : il ne passe pas par `corrige_esf`, qui
    # ne convertirait que l'enveloppe et laisserait le contenu compressé dans l'autre format.
    startpos = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "startpos", "startpos.esf")
    if os.path.exists(startpos) and not a.no_files:
        # un startpos sans `__save_counter` fait passer chaque nouvelle partie pour une sauvegarde (ni intro ni missions :
        # erreur 112, GUIDE n° 117) : il doit être régénéré APRÈS les scripts de campagne
        import verifier_compteur_startpos
        if verifier_compteur_startpos.C.interne(startpos).b.count(b"__save_counter") == 0:
            raise SystemExit(f"{startpos} : pas de __save_counter (startpos plus ancien que les scripts de campagne) ; "
                             "régénérer par startpos_manuel.py ... --ai-map-data, puis le recopier ici")
        res = call(sid, "add_packed_files", {"pack_key": key, "source_paths": [startpos],
                                             "destination_paths": json.dumps(
                                                 [{"File": f"campaigns/{CAMPAIGN}/startpos.esf"}])}, 14)
        print(f"  startpos ajouté : campaigns/{CAMPAIGN}/startpos.esf "
              f"({os.path.getsize(startpos)} octets)")

    # Les données de carte de l'IA de campagne (21.09.2026, 20 h 05) : `hlp_data.esf` et
    # `spd_data.esf`, que le jeu écrit quand on génère le startpos avec `process_campaign_ai_map_data`
    # (`startpos_manuel.py --ai-map-data`). Sans elles, le chargement de l'IA s'arrête sans erreur
    # avant de relier ses factions (`Warhammer3.exe+0x277A0FE`) et le jeu plante dès le réglage du
    # joueur humain. Old World les livre au même endroit. Mis tels que le jeu les a écrits (0xABCB).
    # Attention : dans le pack, le startpos passe **devant** la copie en vrac de `<jeu>\data\` ; un
    # startpos régénéré ne compte en jeu qu'une fois le pack reconstruit (erreur 58).
    ia = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "ia-carte")
    noms_ia = ["hlp_data.esf", "spd_data.esf"]
    if not a.no_files:
        absents = [n for n in noms_ia if not os.path.exists(os.path.join(ia, n))]
        if absents:
            print(f"  !! données de carte de l'IA absentes : {', '.join(absents)} "
                  f"(régénérer le startpos avec --ai-map-data) : le jeu plantera au chargement")
        else:
            call(sid, "add_packed_files", {"pack_key": key,
                                           "source_paths": [os.path.join(ia, n) for n in noms_ia],
                                           "destination_paths": json.dumps(
                                               [{"File": f"campaign_maps/{MAP}/{n}"} for n in noms_ia])}, 17)
            print(f"  données de carte de l'IA ajoutées : {', '.join(noms_ia)}")

    # Les vrais objets de WH1 (21.09.2026, 22 h 55, décision de Charles ; `modeles_wh1.py`) : modèles et
    # textures de WH1. PACK PRIVÉ : il contient des fichiers de WH1 et ne doit jamais être publié.
    # 22.09.2026 : tous les objets et tous les arbres de WH1, sans équivalents de WH3 (`fichiers_wh1.py` :
    # chemin de WH1, ou `_wh1/` quand WH3 a un autre fichier au même chemin), dossier `fichiers-wh1`.
    # Garde-fou : aucun de ces chemins ne doit exister dans les packs de WH3, sinon le fichier de CA
    # serait remplacé dans toutes les campagnes.
    # Les textures de sol de WH1 (22.09.2026, `textures_sol_wh1.py`) : 57 textures au format de CA sous
    # `terrain/textures/campaign/wh1/`, citées par la liste compilée de la carte ; même garde-fou.
    # Les montagnes de WH1 (22.09.2026, `montagnes_wh1.py`) : 514 maillages drapés sous `rigidmodels/_wh1/campaign/
    # montagnes/` et leurs textures au chemin de WH1 ; même garde-fou.
    # Les fichiers d'affichage de la carte (22.09.2026, 23 h 40 ; `affichage_carte.py` de la session d'audit) : ciel
    # (`campaign_skybox.wsmodel` du prologue, maillage et textures de WH1), flèches, frontières, rivières, commerce,
    # tunnels, et la carte stratégique FRANÇAISE (local_fr.pack de WH1) : ajoutés après les fichiers de working_data,
    # ils remplacent ceux de même chemin (l'anglaise de WH1 va dans le pack _en, `ajoute_affichage_en`).
    for dossier, quoi in (("fichiers-wh1", "objets de WH1"), ("textures-sol-wh1", "textures de sol de WH1"),
                          ("montagnes-wh1", "montagnes de WH1"), ("affichage-carte", "affichage de la carte"),
                          ("rivieres-wh1", "rivières de WH1"),
                          # notre matériau de neige de campagne (lit NOTRE masque de neige : `eclairage_wh1.NEIGE_NOUS`)
                          ("eclairage-wh1", "matériaux d'éclairage"),
                          # les six effets de campagne de WH1 dont WH3 n'a plus le fichier de haut niveau (ses émetteurs,
                          # retouchés par CA, sont toujours dans ses bibliothèques : variante « émetteurs de CA » du
                          # convertisseur, 23.09.2026) et la brume toxique verte (modèle et matériau au format de WH3)
                          ("effets-wh1", "effets de WH1"),
                          # la vidéo d'intro de la mini-campagne de WH1 (`movies/warhammer/race_intro_wef_mini.ca_vp8`,
                          # 79 Mo, conteneur CAMV identique à celui de WH3 ; ligne `videos` : session d'audit)
                          ("videos-wh1", "vidéo d'intro de WH1"),
                          # NOTRE matériau d'eau (mer, rivières, lacs) et ses masques (23.09.2026, session d'audit) : celui
                          # des Empires lit leur mer et leurs rivières ; cité par `eau_carte.materiau()` dès qu'il existe
                          ("eau-carte", "matériau d'eau de la carte"),
                          # scènes 3D de l'écran de sélection des seigneurs (`ajouter_seigneurs_jouables.py` : Duc rouge)
                          ("seigneurs", "scènes des seigneurs"),
                          # scripts de campagne (session d'audit, gameplay), à l'arborescence du pack
                          ("scripts-campagne", "scripts de campagne"),
                          # illustrations des évènements et missions (24.09.2026, session « IA et modding 3D » :
                          # `illustrations_vers_jeu.py`, ui/eventpics/saison/*.png, citées par ui_image des missions)
                          ("images-evenements", "images d'évènements")):
        wh1 = os.path.join(ATELIER, "04-projets", "saison-des-revelations", dossier)
        if not os.path.isdir(wh1) or a.no_files:
            continue
        from contenu_pack import chemins_du_jeu
        rel = []
        for root, _, names in os.walk(wh1):
            rel += [os.path.relpath(os.path.join(root, n), wh1).replace("\\", "/") for n in names]
        sans_lien = [r for r in rel if non_embarque(r)]
        if sans_lien:
            rel = [r for r in rel if not non_embarque(r)]
            print(f"  {quoi} : {len(sans_lien)} fichier(s) sans citation non embarqué(s) (NON_EMBARQUES)")
        ecartes = [r for r in rel if r.lower() in SCRIPTS_ECARTES]
        if ecartes:
            rel = [r for r in rel if r.lower() not in SCRIPTS_ECARTES]
            print(f"  {quoi} : écartés de ce pack {ecartes} (SCRIPTS_ECARTES)")
        collisions = sorted(set(r.lower() for r in rel) & chemins_du_jeu(GAME_DATA))
        if collisions:
            raise SystemExit(f"{quoi} : {len(collisions)} chemin(s) de WH3 seraient remplacés : {collisions[:5]}")
        if dossier in ("fichiers-wh1", "montagnes-wh1"):
            # aucun jeu de textures de WH1 que le moteur remplacerait par celui de CA (erreur 100, cristaux roses)
            import audit_textures
            detournes = audit_textures.textures_detournees([wh1])
            if detournes:
                raise SystemExit(f"{quoi} : {len(detournes)} jeu(x) de textures de WH1 pris en jeu par ceux de CA "
                                 f"(relancer modeles_wh1.py --apply) : {sorted(detournes)[:5]}")
        if dossier == "scripts-campagne":
            # un script RETIRÉ du dossier est retiré du pack (23.09.2026, 13 h : vidéo avant chargement abandonnée à la
            # demande de Charles) : le pack est rouvert, jamais recréé, et un script resté dedans tournerait toujours
            vivants = {r.lower() for r in rel}
            for chemin in sorted(p for p in presents if p.startswith("script/") and p not in vivants):
                call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": chemin}])}, 7)
                print(f"  {chemin} retiré du pack (plus dans {dossier})")
            # syntaxe de chaque script avant de l'embarquer (23.09.2026, proposition de la session des scripts) : une
            # erreur dans un fichier que `required.lua` charge fait échouer tout le chargement de la campagne
            import verifier_lua
            lua = verifier_lua.charger_lua()
            L = lua.luaL_newstate()
            fautes = [(f, e) for f in verifier_lua.fichiers([wh1]) for e in [verifier_lua.verifier(lua, L, f)] if e]
            lua.lua_close(L)
            if fautes:
                raise SystemExit(f"{quoi} : {len(fautes)} script(s) en erreur de syntaxe : "
                                 + " ; ".join(e for _, e in fautes[:5]))
            print(f"  {quoi} : syntaxe Lua vérifiée ({sum(1 for r in rel if r.endswith('.lua'))} fichiers)")
        res = call(sid, "add_packed_files", {"pack_key": key,
                                             "source_paths": [os.path.join(wh1, *r.split("/")) for r in rel],
                                             "destination_paths": json.dumps([{"File": r} for r in rel])}, 18)
        print(f"  {quoi} ajoutés : {len(rel)} fichiers  {'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")

    # La neige et la glace de WH1 à la place des fichiers de deux groupes de CA qu'aucune campagne de CA n'emploie
    # (`textures_sol_wh1.GLACE_WH1`, 23.09.2026) : la SEULE exception au garde-fou « jamais un chemin de WH3 », limitée à
    # ces six fichiers.
    # 24.09.2026, chaîne 13 (session du rendu) : la neige de WH1 passe dans NOS groupes `wh1_snow2` / `wh1_snow3`
    # (`GLACE_WH1 = {}`) ; l'exception tombe. Elle suit le terrain COMPILÉ, pas le seul réglage : tant que la liste compilée
    # n'a pas `wh1_snow2`, le terrain emploie encore ice0 / ice2 et les six fichiers restent (sinon la neige de WH1
    # redeviendrait la glace de CA) ; dès qu'elle l'a, ils sont retirés du pack rouvert (erreur 203).
    if not a.no_files:
        import textures_sol_wh1
        permis = {f"terrain/textures/campaign/default/ice/{g}{s}.dds" for g in ("ice0", "ice2")
                  for s in ("_base_colour", "_material_map", "_normal")}
        liste = os.path.join(AKIT, "working_data", "terrain", "campaigns", MAP, "global_map", "texture_arrays.xml")
        with open(liste, encoding="utf-8") as f:
            neige_a_nous = "<group>wh1_snow2</group>" in f.read()
        paires = textures_sol_wh1.remplacements_glace()
        if neige_a_nous:
            if paires:
                raise SystemExit("neige : le terrain compilé a ses groupes wh1_snow*, mais GLACE_WH1 remplace encore "
                                 "des fichiers de CA : vider GLACE_WH1")
            vieux = sorted(p for p in permis if p in presents)
            if vieux:
                call(sid, "delete_packed_files", {"pack_key": key, "paths": json.dumps([{"File": p} for p in vieux])}, 7)
            print(f"  neige de WH1 dans nos groupes wh1_snow* : plus aucun fichier de CA remplacé "
                  f"({len(vieux)} ancien(s) fichier(s) ice0 / ice2 retiré(s) du pack)")
        else:
            if not paires:
                # terrain compilé avant la chaîne 13 : l'ancienne correspondance, le temps que la chaîne passe
                GLACE_AVANT_13 = {"ice0": "snow3", "ice2": "snow2"}
                sauve, textures_sol_wh1.GLACE_WH1 = textures_sol_wh1.GLACE_WH1, GLACE_AVANT_13
                try:
                    paires = textures_sol_wh1.remplacements_glace()
                finally:
                    textures_sol_wh1.GLACE_WH1 = sauve
            if {p for p, _ in paires} != permis:
                raise SystemExit(f"remplacements de glace hors de la liste permise : {sorted(p for p, _ in paires)}")
            res = call(sid, "add_packed_files", {"pack_key": key, "source_paths": [loc for _, loc in paires],
                                                 "destination_paths": json.dumps([{"File": p} for p, _ in paires])}, 18)
            print(f"  neige et glace de WH1 (groupes ice0 et ice2 ; terrain compilé avant la chaîne 13) : {len(paires)} "
                  f"fichiers  {'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")
        # Seconde exception (23.09.2026, 23 h 40 ; Charles : « les terres désolées du Chaos ») : sans leurs clés dans la
        # base de variantes de CA, nos 17 groupes de sol wh1_* retombent sur la dernière texture du tableau (cendre du
        # Chaos). Copie de la base de CA, ses 440 entrées identiques à l'octet (contrôlé par la fonction), nos clés wh1_*
        # à la suite. Elle passe devant celle de CA tant que le mod est actif : à REFAIRE après toute mise à jour du jeu.
        paires = textures_sol_wh1.remplacements_base_variantes()
        # 25.09.2026, 22 h (compatibilité) : avec le catalogue séparé, seul notre fichier à nous part (plus de copie de CA).
        base = textures_sol_wh1.CATALOGUE_SEPARE_CHEMIN if textures_sol_wh1.CATALOGUE_SEPARE else textures_sol_wh1.BASE_VARIANTES
        permis = {base, base + ".xml"}
        if paires and {p for p, _ in paires} != permis:
            raise SystemExit(f"base de variantes hors de la liste permise : {sorted(p for p, _ in paires)}")
        if paires:
            res = call(sid, "add_packed_files", {"pack_key": key, "source_paths": [loc for _, loc in paires],
                                                 "destination_paths": json.dumps([{"File": p} for p, _ in paires])}, 18)
            print(f"  base de variantes du sol ({base}) : {len(paires)} fichiers  "
                  f"{'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")

    # Le terrain compilé (21.09.2026, journal de phase 3 § 7) : `compiler_terrain_bob.py` le fait
    # écrire par BOB dans `working_data\terrain\campaigns\<carte>\`. On n'embarque que la liste que
    # le jeu reçoit pour les Empires Immortels (plus `terrain_visibility_mask.dds`, présent chez Old
    # World), jamais les intermédiaires de BOB, et seulement des fichiers plus récents que le projet
    # Terry : le dossier a été amorcé avec le terrain des Empires pour que Terry s'ouvre.
    if not a.no_files:
        ajoute_terrain(sid, key)
        ajoute_terrain_bataille(sid, key)
    ajoute_icones_monuments(sid, key)

    # toujours explicite : le pack étant rouvert, il garderait sinon la compression de la construction précédente
    print("  compression :", text(call(sid, "change_compression_format",
                                        {"pack_key": key, "format": "\"Zstd\"" if a.zstd else "\"None\""}, 12))[:200])
    enregistrement = text(call(sid, "save_packfile", {"pack_key": key}, 13))
    print("enregistrement :", enregistrement[:400])
    # 22.09.2026 (16 h) : Terry ouvert tenait le pack (il lit les packs de `data\`) ; l'enregistrement
    # échouait (« fichier utilisé par un autre processus ») et le script finissait quand même avec le
    # code 0, le pack de la veille restant en place.
    if '"Error"' in enregistrement:
        raise SystemExit("PACK NON ENREGISTRÉ : fermer Terry et le jeu, qui tiennent le fichier, puis relancer")
    print(f"{total} lignes de base écrites dans {a.pack}")
    if not a.no_files:
        ajoute_affichage_en(sid)
    return verifie_fichiers_declares(sid, key)


PACK_EN = GAME_DATA + "/!saison_des_revelations_en.pack"


def ajoute_icones_monuments(sid, key):
    """Icônes des monuments du lore (lot 21 de la session « IA et modding 3D », 23.09.2026) : chaque clé d'icône de
    `donnees_campagne.ICONES_MONUMENTS` dont la source est un fichier du projet va sous `ui/buildings/icons/<clé>.png` ;
    les autres (« icône de CA ») sont celles du jeu. Aucun chemin de CA remplacé (garde)."""
    import donnees_campagne
    from contenu_pack import chemins_du_jeu
    sources, rel = [], []
    for cle, source in sorted(donnees_campagne.ICONES_MONUMENTS.items()):
        chemin = os.path.join(ATELIER, source) if not os.path.isabs(source) else source
        if not source.lower().endswith(".png"):
            continue
        if not os.path.isfile(chemin):
            raise SystemExit(f"icône de monument absente : {chemin}")
        sources.append(chemin)
        rel.append(f"ui/buildings/icons/{cle}.png")
    if not rel:
        return
    collisions = sorted(set(r.lower() for r in rel) & chemins_du_jeu(GAME_DATA))
    if collisions:
        raise SystemExit(f"icônes de monuments : {len(collisions)} chemin(s) de WH3 seraient remplacés : {collisions[:5]}")
    call(sid, "add_packed_files", {"pack_key": key, "source_paths": sources,
                                   "destination_paths": json.dumps([{"File": r} for r in rel])}, 14)
    print(f"  icônes de monuments ajoutées : {len(rel)}")


def ajoute_affichage_en(sid):
    """Le pack des textes anglais (`injecter_textes.py`) reçoit aussi la carte stratégique ANGLAISE de WH1, au même
    chemin que la française du pack principal : activé, il passe devant (22.09.2026, 23 h 40)."""
    # la minicarte ANGLAISE aussi (`images-carte-en`, `preparer_minicarte.py --minicarte-seule`, 23.09.2026) : celle du
    # pack principal est désormais faite sur le parchemin français
    dossiers = [os.path.join(ATELIER, "04-projets", "saison-des-revelations", d)
                for d in ("affichage-carte-en", "images-carte-en")]
    dossiers = [d for d in dossiers if os.path.isdir(d)]
    if not dossiers:
        return
    if not os.path.exists(PACK_EN):
        print(f"  !! {PACK_EN} absent (lancer injecter_textes.py --apply) : carte anglaise non ajoutée")
        return
    from contenu_pack import chemins_du_jeu
    rel, sources = [], []
    for dossier in dossiers:
        for root, _, names in os.walk(dossier):
            for n in names:
                rel.append(os.path.relpath(os.path.join(root, n), dossier).replace("\\", "/"))
                sources.append(os.path.join(root, n))
    collisions = sorted(set(r.lower() for r in rel) & chemins_du_jeu(GAME_DATA))
    if collisions:
        raise SystemExit(f"affichage anglais : {len(collisions)} chemin(s) de WH3 seraient remplacés : {collisions[:5]}")
    call(sid, "open_packfiles", {"paths": [PACK_EN]}, 30)
    call(sid, "add_packed_files", {"pack_key": PACK_EN,
                                   "source_paths": sources,
                                   "destination_paths": json.dumps([{"File": r} for r in rel])}, 31)
    res = text(call(sid, "save_packfile", {"pack_key": PACK_EN}, 32))
    if '"Error"' in res:
        raise SystemExit(f"PACK ANGLAIS NON ENREGISTRÉ : {res[:200]}")
    print(f"  pack anglais : {len(rel)} fichier(s) d'affichage ajoutés ({', '.join(rel)})")


# `environment_collection.xml` : les zones d'éclairage de WH1, écrites par BOB d'après le calque `eclairage_wh1`
# du projet (22.09.2026 ; requis depuis que BOB effaçait la version posée à la main)
TERRAIN_REQUIS = ["full_height_map.dds", "full_logic_map.compressed_map", "lf_normal.dds", "shroud_heights.dds",
                  "tile_list.bin", "tile_mask.dds", "patch_mask.dds", "colour_overlay.dds", "lf_sea_colour.dds",
                  "snow_mask.dds", "corruption_mask.dds", "global_props.bin", "global_map/global_blend.dds",
                  "global_map/texture_arrays.xml", "global_map/tile_list.bin", "environment_collection.xml"]
TERRAIN_FACULTATIF = ["terrain_visibility_mask.dds"]
HORS_BOB = {"lf_normal.dds"}


def ajoute_terrain(sid, key):
    cible = os.path.join(AKIT, "working_data", "terrain", "campaigns", MAP)
    projet = os.path.join(AKIT, "raw_data", "terrain", "campaigns", MAP, f"{MAP}.terry")
    if not os.path.isdir(cible) or not os.path.exists(projet):
        print("  terrain : pas encore compilé, rien d'ajouté")
        return
    depuis = os.path.getmtime(projet)
    # Sans zone d'éclairage (`eclairage_wh1.ZONES_ACTIVES`, désactivées le 23.09.2026, erreur 96), BOB n'écrit plus
    # `environment_collection.xml` ; CA en livre un pour chaque campagne (éclairage global + zones) : on écrit le nôtre,
    # éclairage global seul.
    import eclairage_wh1
    collection = os.path.join(cible, "environment_collection.xml")
    # Zones de WH1 en cylindres (23.09.2026, `eclairage_wh1.ZONES_CYLINDRES`) : collection écrite ici à chaque fois, au
    # format compilé de CA (BOB n'écrit que les zones du projet, qui n'en a plus)
    # Réécrite à chaque fois dès que BOB ne l'écrit pas (zones du projet désactivées) : l'essai du 23.09.2026 à 02 h 53
    # a gardé des cylindres retirés depuis parce que l'ancienne condition ne l'écrivait que si elle manquait.
    if not eclairage_wh1.ZONES_ACTIVES:
        produits = eclairage_wh1.produire()[0]
        with open(collection, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(produits["environment_collection.xml"])
        # (24.09.2026, correctif proposé par la session du rendu pour les clairières, chaîne 12) les fichiers d'éclairage
        # aussi, comme la collection : un réglage de lumière ne demande plus qu'un pack, et la collection ne peut plus citer
        # des zones périmées (saut de lumière du 23.09)
        os.makedirs(os.path.join(cible, "lighting"), exist_ok=True)
        for chemin, texte in produits.items():
            if chemin.startswith("lighting/"):
                with open(os.path.join(cible, *chemin.split("/")), "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(texte)
        cyl = eclairage_wh1.cylindres_attendus()
        print(f"  environment_collection.xml et {sum(c.startswith('lighting/') for c in produits)} fichiers d'éclairage "
              "écrits (" + (f"zones en cylindres : {', '.join(cyl)}" if cyl else "éclairage global seul, zones désactivées")
              + ")")
    # `lf_normal.dds` ne vient pas de BOB (normal map de WH1, `lf_normal_wh1_vers_wh3.py` puis
    # `lf_normal_a_la_taille_du_relief.py`) : pas de contrôle de date, mais celui de CA sur la taille
    # (celle de `full_height_map.dds`, GUIDE § 15, n° 73).
    perimes = [f for f in TERRAIN_REQUIS
               if not os.path.exists(os.path.join(cible, f))
               or (f not in HORS_BOB and os.path.getmtime(os.path.join(cible, f)) < depuis)]
    for f in HORS_BOB:
        chemin = os.path.join(cible, f)
        if os.path.exists(chemin):
            with open(chemin, "rb") as g1, open(os.path.join(cible, "full_height_map.dds"), "rb") as g2:
                if g1.read(20)[12:20] != g2.read(20)[12:20]:
                    perimes.append(f"{f} (taille différente de full_height_map.dds)")
    if perimes:
        # fatal depuis le 22.09.2026 : un pack enregistré sans son terrain ferait planter le jeu au chargement
        raise SystemExit(f"terrain NON ajouté, pack non enregistré : absents ou antérieurs au projet Terry : "
                         f"{', '.join(perimes)}\n  -> lancer `compiler_terrain_bob.py --carte {MAP} --apply`")
    # 22.09.2026 : BOB réécrit la liste des textures et le mélange à chaque compilation ; sans
    # `textures_sol_wh1.py --apply` derrière, le jeu retomberait sur nos équivalents de WH3.
    # Depuis le 23.09.2026 (erreur 114), le mélange est réécrit vers les groupes de CA les plus proches et la liste reste
    # celle de BOB (`textures_sol_wh1.CHEMINS_WH1 = False`) : la preuve est la marque posée après la réécriture.
    import textures_sol_wh1
    sol_wh1 = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "textures-sol-wh1")
    with open(os.path.join(cible, "global_map", "texture_arrays.xml"), encoding="utf-8") as f:
        cite_wh1 = "terrain/textures/campaign/wh1/" in f.read()
    if textures_sol_wh1.CHEMINS_WH1:
        if os.path.isdir(sol_wh1) != cite_wh1:
            raise SystemExit("textures de sol de WH1 : la liste compilée ne les cite pas (lancer `textures_sol_wh1.py "
                             "--apply` après BOB)" if not cite_wh1 else
                             "textures de sol de WH1 citées par la liste compilée mais absentes du projet (--convertir)")
    else:
        # 23.09.2026, 22 h 15 (demande de Charles : sol de WH1 à 100 %) : 144 groupes de CA, plus éventuellement les
        # groupes neufs wh1_* après eux ; contrôle complet (marque, ordre, textures présentes, indices du mélange) dans
        # textures_sol_wh1.controle_compile, écrit par la session « Rendu de la carte ».
        bon, message = textures_sol_wh1.controle_compile(os.path.join(cible, "global_map"))
        if not bon:
            raise SystemExit(message)
        print("  " + message)
    import eclairage_wh1
    _, spheres = eclairage_wh1.zones()
    with open(os.path.join(cible, "environment_collection.xml"), encoding="utf-8") as f:
        texte_coll = f.read()
    n = texte_coll.count("<SPHERE ")
    if n != len(spheres):
        raise SystemExit(f"environment_collection.xml : {n} sphères au lieu des {len(spheres)} zones de WH1 "
                         "(calque `eclairage_wh1` du projet, compilé par BOB)")
    # (24.09.2026) cylindres attendus : `eclairage_wh1.cylindres_attendus()` (les quatre clairières, les 7 zones de WH1 ou
    # aucun, erreur 109) ; chaque fichier cité présent et identique à celui d'`eclairage_wh1.produire()`
    attendus = eclairage_wh1.cylindres_attendus()
    cites = re.findall(r"<CYLINDER [^>]*\blighting='terrain/campaigns/[^/]+/lighting/([^']+)'", texte_coll)
    if cites != attendus:
        raise SystemExit(f"environment_collection.xml : cylindres {cites} au lieu de {attendus} (erreur 109)")
    if not eclairage_wh1.ZONES_ACTIVES and "<SPHERE " in texte_coll:
        raise SystemExit("environment_collection.xml : des sphères d'éclairage alors qu'elles sont retirées (erreur 109)")
    produits_env = eclairage_wh1.produire()[0]
    for f_env in cites:
        chemin_env = os.path.join(cible, "lighting", f_env)
        if not os.path.exists(chemin_env):
            raise SystemExit(f"environment_collection.xml cite lighting/{f_env}, absent du terrain compilé")
        with open(chemin_env, encoding="utf-8") as f:
            if f.read() != produits_env[f"lighting/{f_env}"]:
                raise SystemExit(f"lighting/{f_env} du terrain compilé périmé (autre que eclairage_wh1.produire())")
    fichiers = TERRAIN_REQUIS + [f for f in TERRAIN_FACULTATIF if os.path.exists(os.path.join(cible, f))
                                 and os.path.getmtime(os.path.join(cible, f)) >= depuis]
    eclairage = os.path.join(cible, "lighting")
    if os.path.isdir(eclairage):
        fichiers += [f"lighting/{n}" for n in sorted(os.listdir(eclairage))]
    res = call(sid, "add_packed_files", {"pack_key": key,
                                         "source_paths": [os.path.join(cible, f) for f in fichiers],
                                         "destination_paths": json.dumps(
                                             [{"File": f"terrain/campaigns/{MAP}/{f}"} for f in fichiers])}, 17)
    taille = sum(os.path.getsize(os.path.join(cible, f)) for f in fichiers) / 1e6
    print(f"  terrain ajouté : {len(fichiers)} fichiers, {taille:.0f} Mo "
          f"{'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")


# Le terrain de BATAILLE de la campagne (22.09.2026, journal `05-journal\2026-09-22-phase-4\plantage-fin-de-tour.md`) :
# le jeu le lit dans `terrain_folder` (`terrain/battles/<carte>/`) dès la première bataille terrestre ; sans lui,
# plantage en fin de tour (Warhammer3.exe+0x1497949). Les 9 fichiers que CA livre pour chaque campagne, hors les
# trois cartes de captage (calques peints que nous n'avons pas). Fabriqué par `dossier_bataille_campagne.py`,
# compilé par `compiler_terrain_bob.py --bataille`.
TERRAIN_BATAILLE = ["battle_locations_map.bin", "battle_locations_map.xml", "blm_primary_mask.dds",
                    "blm_secondary_mask.dds", "full_lf_logic_map.compressed_map", "lf_normal.dds", "tile_map.bmd",
                    "tile_map.index", "tile_map.tiles"]
# Les cartes de captage (23.09.2026, dessinées par la session « IA et modding 3D », copiées par
# `dossier_bataille_campagne.py --captage`) : embarquées quand leur calque est dans le dossier de bataille du projet et
# que leur compilation est plus récente que lui.
CAPTAGE_BATAILLE = ["blm_catchment_override.compressed_map", "blm_catchment_override_settlement_standard.compressed_map",
                    "blm_catchment_override_settlement_unfortified.compressed_map"]


def ajoute_terrain_bataille(sid, key):
    cible = os.path.join(AKIT, "working_data", "terrain", "battles", MAP)
    brut = os.path.join(AKIT, "raw_data", "terrain", "battles", MAP)
    projet = os.path.join(brut, f"{MAP}.terry")
    if not os.path.exists(projet):
        print("  terrain de bataille : projet absent -> dossier_bataille_campagne.py --carte " + MAP + " --apply")
        return
    depuis = os.path.getmtime(projet)
    perimes = [f for f in TERRAIN_BATAILLE
               if not os.path.exists(os.path.join(cible, f)) or os.path.getmtime(os.path.join(cible, f)) < depuis]
    if perimes:
        print(f"  terrain de bataille NON ajouté : absents ou antérieurs au projet : {', '.join(perimes)}")
        print("  -> lancer `compiler_terrain_bob.py --carte " + MAP + " --bataille --apply`")
        return
    fichiers, captage_perime = list(TERRAIN_BATAILLE), []
    for f in CAPTAGE_BATAILLE:
        calque = os.path.join(brut, f.replace(".compressed_map", ".png"))
        if not os.path.exists(calque):
            continue
        compile_ = os.path.join(cible, f)
        if os.path.exists(compile_) and os.path.getmtime(compile_) >= max(depuis, os.path.getmtime(calque)):
            fichiers.append(f)
        else:
            captage_perime.append(f)
    if captage_perime:
        print(f"  cartes de captage NON ajoutées (calque plus récent que la compilation, ou compilation absente) : "
              f"{', '.join(captage_perime)} -> `compiler_terrain_bob.py --carte {MAP} --bataille --apply`")
    res = call(sid, "add_packed_files", {"pack_key": key,
                                         "source_paths": [os.path.join(cible, f) for f in fichiers],
                                         "destination_paths": json.dumps(
                                             [{"File": f"terrain/battles/{MAP}/{f}"} for f in fichiers])}, 19)
    taille = sum(os.path.getsize(os.path.join(cible, f)) for f in fichiers) / 1e6
    print(f"  terrain de bataille ajouté : {len(fichiers)} fichiers dont {len(fichiers) - len(TERRAIN_BATAILLE)} "
          f"cartes de captage, {taille:.0f} Mo {'ok' if 'Success' in text(res) or '[' in text(res) else text(res)[:80]}")


# Colonnes de `campaign_map_playable_areas` qui nomment un fichier, et où le jeu le cherche.
FICHIERS_DECLARES = {
    "map_file": "campaign_maps/{carte}/{v}",
    "overlay_file": "campaign_maps/{carte}/{v}",
    "radar_file": "campaign_maps/{carte}/{v}",
    "minimap_lookup_file": "campaign_maps/{carte}/{v}",
    "frontend_image": "{v}",
}
# L'image de la vignette se décline en trois : la mise en page de CA accole ces suffixes au nom.
SUFFIXES_VIGNETTE = ("_button", "_vertical")
DOSSIER_VIGNETTES = "ui/frontend UI/campaign_images"
# Les trois textures de l'overlay : CA elle-même ne les livre pas toutes (le prologue déclare un
# `_text.dds` absent), on se contente donc de les signaler.
DDS_DECLARES = ("campaign_overlay_map", "campaign_overlay_lookup", "campaign_overlay_map_text")


def verifie_fichiers_declares(sid, key):
    """Règle A33, enfin codée (21.09.2026) : chaque fichier que la ligne de zone jouable déclare
    doit exister dans le pack. Le 21.09.2026, `radar_file` pointait vers une minicarte absente —
    la correction faite dans le pack avait été effacée par ce même script, qui recopie la ligne du
    kit — et la génération du startpos mourait en lisant ce fichier (`Warhammer3+0x3211033`)."""
    info = text(call(sid, "open_pack_info", {"pack_key": key}, 30))
    presents = set(re.findall(r'"((?:campaign_maps|ui|terrain)/[^"]+)"', info))
    brut = text(call(sid, "decode_packed_file", {
        "pack_key": key, "path": f"db/campaign_map_playable_areas_tables/{PREFIX}",
        "source": "PackFile"}, 31))
    h = json.loads(brut)["DBRFileInfo"][0]
    noms = [n for n, _ in processed_fields(sid, h["table"]["definition"])]
    ligne = h["table"]["table_data"][0]

    def val(col):
        cell = ligne[noms.index(col)]
        return list(cell.values())[0] if isinstance(cell, dict) else cell

    manquants = 0
    print("\n  fichiers déclarés par campaign_map_playable_areas :")
    for col, gabarit in FICHIERS_DECLARES.items():
        chemin = gabarit.format(carte=MAP, v=val(col))
        ok = chemin in presents
        manquants += 0 if ok else 1
        print(f"     {'ok ' if ok else '!! '} {col:22s} {chemin}")
        if col == "frontend_image":
            base, ext = os.path.splitext(chemin)
            for suffixe in SUFFIXES_VIGNETTE:
                variante = base + suffixe + ext
                ok = variante in presents
                manquants += 0 if ok else 1
                print(f"     {'ok ' if ok else '!! '} {'  + ' + suffixe:22s} {variante}")
    for col in DDS_DECLARES:
        chemin = f"campaign_maps/{MAP}/{val(col)}"
        print(f"     {'ok ' if chemin in presents else '-- '} {col:22s} {chemin}"
              + ("" if chemin in presents else "   (texture absente, signalée seulement)"))
    # `terrain_folder` : le terrain de bataille, lu à la première bataille (plantage du 21.09.2026, 22 h 20).
    dossier = val("terrain_folder").replace("\\", "/").rstrip("/") + "/"
    for f in TERRAIN_BATAILLE:
        ok = (dossier + f) in presents
        manquants += 0 if ok else 1
        print(f"     {'ok ' if ok else '!! '} {'terrain_folder':22s} {dossier + f}")
    if manquants:
        print(f"  !! {manquants} fichier(s) déclaré(s) absent(s) du pack : le jeu les lira et "
              f"plantera. Corriger la ligne du kit (corriger_zone_jouable.py), pas le pack.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
