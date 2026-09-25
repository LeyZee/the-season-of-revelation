#!/usr/bin/env python3
"""
compiler_terrain_bob.py - compile avec BOB le terrain visuel d'une carte de campagne NEUVE (WH3).

Pourquoi (trouvé le 21.09.2026, journal `05-journal\\2026-09-21-phase-3-terrain\\terrain.md` § 7) :
pour une campagne, le processeur Terrain de BOB (`bob_terrain`) cherche le nom du dossier de terrain dans
la table `campaign_map_playable_areas` de SA base. S'il ne le trouve pas, il crée une action d'erreur
muette (« Failed to find <carte> in the database », jamais affichée) et saute toutes les actions lourdes :
Tilemap, Global Tilemap, Campaign Heightmap, Campaign Shroud Heights, Campaign Global Blendmap, Campaign
Trees. Or la base de BOB est celle du jeu (`db.pack` : 10 zones jouables, 3 campagnes) ; ce que nous
ajoutons au kit (XML de `raw_data\\db`, binaires de `working_data\\db`, pack de mod, pack Release ou
Patch) n'y entre pas. Terry n'obtient donc que 6 actions (Terry file + 5 masques), même sur le projet des
Empires de ChaosRobie copié sous un autre nom.

Ce que fait le script : il lance BOB avec la commande EXACTE que Terry emploie (capturée le 21.09.2026),
sous `cdb`, et au retour de `record_from_name` (bob_terrain+0x2918f) fournit, si la recherche a échoué,
un enregistrement dont seuls `minx` (+0xF0) et `maxx` (+0xF4) sont lus : les valeurs déclarées pour la
carte dans le kit. Rien n'est modifié sur disque en dehors des sorties normales de BOB.

Usage :
    python compiler_terrain_bob.py --carte wh_dlc05_wood_elves_map_1            # vérifications seules
    python compiler_terrain_bob.py --carte wh_dlc05_wood_elves_map_1 --apply    # compilation
Prérequis : Terry fermé (il verrouille des fichiers de `working_data`), `cdb` (paquet WinDbg du Store).
Journaux de chaque compilation : `05-journal\\2026-09-21-phase-3-terrain\\compilations\\<carte>-<date>\\`.
"""

import argparse
import hashlib
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import time

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
BIN = os.path.join(KIT, "binaries")
ATELIER = r"C:\TotalWar-CampaignMap"
JOURNAL = os.path.join(ATELIER, "05-journal", "2026-09-21-phase-3-terrain", "compilations")

# bob_terrain.modder.x64.dll de l'Assembly Kit du 20.09.2026 (branche patch_8_1). Les décalages ne valent
# que pour cette version : le script refuse de tourner si l'empreinte change.
DLL = os.path.join(BIN, "bob_terrain.modder.x64.dll")
DLL_SHA256 = "b50b3653cdcdbb9ce7be77c0623edb69fc71fe20017b59cfc90fd1ead03167d7"
APPEL_RECHERCHE = 0x29189      # call [CAMPAIGN_MAP_PLAYABLE_AREAS_TABLE::record_from_name]
RETOUR_RECHERCHE = 0x2918F     # mov rbx, rax
OCTETS_ATTENDUS = {0x29189: "ff15d1661300", 0x2918F: "488bd8", 0x292E3: "f30f1083f4000000",
                   0x294BF: "e89cd2fdff", 0x29776: "e80558feff"}
BLOC = 0x20000000              # bloc de 0x1000 octets alloué dans BOB pour l'enregistrement fourni
# Kit de la 9.0 (24.09.2026, 17 h 13 ; relevé en lecture seule par la construction et par la session du rendu, qui
# concordent) : le code a glissé d'environ +0xAF10. L'appel indirect vise toujours l'import
# ?record_from_name@CAMPAIGN_MAP_PLAYABLE_AREAS_TABLE (IAT 0x174918, seul appel de ce type) ; même disposition de
# l'enregistrement (maxx lu en [rbx+0F4h], 0x341F4). Constructeurs d'actions NON reportés : plusieurs sites ambigus, et un
# point d'arrêt au milieu d'une instruction ferait planter BOB ; les lignes « Finished Terrain / … » de BOB suffisent.
VERSIONS_DLL = {
    "45a1237be7819881de6ac3de3bf8661d523eed5d9998a044900ad48087371645": {
        "appel": 0x34099, "retour": 0x3409F,
        "octets": {0x34099: "ff1579081400", 0x3409F: "488bd8", 0x341F4: "f30f1083f4000000"},
        "constructeurs": {}},
}

# Actions lourdes : adresse de l'appel de leur constructeur dans bob_terrain (fonction 0x282f0).
# Les deux dernières ne sont créées que si la règle `save_meta_data_map` vaut vrai (c'est le cas de
# `raw_data\terrain\campaigns\rules.bob`) : test `cmp byte [rbp+3D8h], 0` en bob_terrain+0x293ee.
CONSTRUCTEURS = {0x293A2: "Tilemap", 0x29BE1: "Global Tilemap", 0x29CE4: "Campaign Heightmap",
                 0x29D68: "Campaign Shroud Heights", 0x29C67: "Campaign Global Blendmap",
                 0x29B58: "Campaign Trees", 0x29E17: "Heights & Normals",
                 0x294BF: "Battle Locations Map", 0x29776: "Battle Catchment AGF"}

# Configuration écrite par Terry pour un projet de campagne (BOB\_terry_auto_configuration.xml, 21.09.2026).
SORTIES = ["<working>/terrain/campaigns/{c}/tile_map.tiles", "<working>/terrain/campaigns/{c}/tile_map.index",
           "<working>/terrain/campaigns/{c}/tile_list.bin", "<working>/terrain/campaigns/{c}/tile_mask.dds",
           "<working>/terrain/campaigns/{c}/patch_mask.dds", "<working>/terrain/campaigns/{c}/global_map/tile_list.bin",
           "<working>/terrain/campaigns/{c}/full_height_map.dds",
           "<working>/terrain/campaigns/{c}/full_logic_map.compressed_map",
           "<working>/terrain/campaigns/{c}/lf_normal.dds", "<working>/terrain/campaigns/{c}/global_map/global_blend.dds",
           "<working>/terrain/campaigns/{c}/global_map/texture_arrays.xml",
           "<working>/terrain/campaigns/{c}/colour_overlay.dds", "<working>/terrain/campaigns/{c}/lf_sea_colour.dds",
           "<working>/terrain/campaigns/{c}/snow_mask.dds", "<working>/terrain/campaigns/{c}/corruption_mask.dds",
           "<working>/terrain/campaigns/{c}/terrain_visibility_mask.dds",
           "<working>/campaign_maps/{c}/camera_heightmap.png",
           "<working>/campaign_maps/{c}/display/trees/trees.campaign_tree_list",
           "<working>/terrain/campaigns/{c}/shroud_heights.dds", "<working>/campaign_maps/{c}/map_data.esf",
           "<working>/terrain/campaigns/{c}/global_props.bin",
           "<working>/terrain/campaigns/{c}/environment_collection.xml",
           "<working>/warscape_asset_variation_db/warscape_asset_variation_db.xml",
           "<working>/warscape_asset_variation_db/warscape_asset_variation_db.bin"]
# Terrain de BATAILLE de la campagne (22.09.2026, journal `05-journal\2026-09-22-phase-4\plantage-fin-de-tour.md`) :
# sans lui le jeu plante à la première bataille terrestre (Warhammer3.exe+0x1497949, masque des lieux de bataille
# nul). Projet fabriqué par `dossier_bataille_campagne.py` dans `raw_data\terrain\battles\<carte>\` ; BOB le
# compile par sa branche « bataille » (« Heights & Normals », « Battle Locations Map » si `save_meta_data_map`).
# Les 10 fichiers que CA livre dans `terrain/battles/<dossier>/`, hors les trois cartes de captage, qui ne naissent
# que de calques peints (`blm_catchment_override*.png`) que nous n'avons pas.
SORTIES_BATAILLE = ["<working>/terrain/battles/{c}/tile_map.tiles", "<working>/terrain/battles/{c}/tile_map.index",
                    "<working>/terrain/battles/{c}/tile_map.bmd", "<working>/terrain/battles/{c}/tile_list.bin",
                    "<working>/terrain/battles/{c}/full_lf_logic_map.compressed_map",
                    "<working>/terrain/battles/{c}/lf_normal.dds",
                    "<working>/terrain/battles/{c}/battle_locations_map.bin",
                    "<working>/terrain/battles/{c}/battle_locations_map.xml",
                    "<working>/terrain/battles/{c}/blm_primary_mask.dds",
                    "<working>/terrain/battles/{c}/blm_secondary_mask.dds"]
# Le dossier des prefabs de bataille porte la règle `[Prefab] TargetPath` dont « Generate Tile Map BMD » a besoin
# (sans lui : « prefab root ... does not have a valid TargetPath », pas de tile_map.bmd).
DOSSIERS_BATAILLE = ["<raw>/terrain/battles/{c}/", "<working>/terrain/battles/{c}/", "<raw>/art/prefabs/battle/"]
DOSSIERS = ["<raw>/terrain/campaigns/{c}/", "<working>/terrain/campaigns/{c}/",
            "<raw>/EmpireDesignData/campaign_maps/{c}/", "<raw>/art/campaign/prefabs/",
            "<raw>/warscape_asset_variation_db/"]


def configuration(carte, sans=(), bataille=False):
    e = lambda s: s.replace("<", "&lt;")
    sorties = [s for s in (SORTIES_BATAILLE if bataille else SORTIES) if not any(s.endswith("/" + x) for x in sans)]
    lignes = ["<bob_configuration>", "    <processors>"]
    lignes += [f"        <processor>{p}</processor>" for p in ("Terrain", "Texture", "WarscapeAssetVariationDB")]
    lignes += ["    </processors>", "    <directories>"]
    lignes += [f"        <directory>{e(d.format(c=carte))}</directory>" for d in (DOSSIERS_BATAILLE if bataille else DOSSIERS)]
    lignes += ["    </directories>", "    <global_rules/>"]
    for cle, val in [("retail", 0), ("silent", 1), ("show_errors", 0), ("no_progress", 1), ("fail_on_assert", 0),
                     ("scan_perforce", 1), ("merge_for_checkin_mode", 3), ("keep_output", 1),
                     ("load_asset_graph", 0), ("use_heap_asset_graph", 0), ("asset_graph_mode", ""),
                     ("clean_asset_graph", 0), ("get_latest", 0), ("add_source_files_to_perforce", 0)]:
        lignes.append(f"    <{cle}>{val}</{cle}>")
    lignes.append("    <selected_providers>")
    lignes += [f"        <entry>{e(s.format(c=carte))}</entry>" for s in sorties]
    lignes += ["    </selected_providers>", "    <selected_consumers/>", "</bob_configuration>", ""]
    return "\n".join(lignes)


def zone_jouable(carte):
    t = io.open(os.path.join(KIT, "raw_data", "db", "campaign_map_playable_areas.xml"), encoding="utf-8").read()
    for r in re.findall(r"<campaign_map_playable_areas\b[^>]*>(.*?)</campaign_map_playable_areas>", t, re.S):
        if re.search(rf"<mapname>{re.escape(carte)}</mapname>", r):
            minx = float(re.search(r"<minx>(.*?)</minx>", r).group(1))
            maxx = float(re.search(r"<maxx>(.*?)</maxx>", r).group(1))
            return minx, maxx
    sys.exit(f"{carte} absente de raw_data\\db\\campaign_map_playable_areas.xml : la déclarer d'abord")


def verifier_dll():
    global APPEL_RECHERCHE, RETOUR_RECHERCHE, OCTETS_ATTENDUS, CONSTRUCTEURS
    b = open(DLL, "rb").read()
    empreinte = hashlib.sha256(b).hexdigest()
    if empreinte in VERSIONS_DLL:
        v = VERSIONS_DLL[empreinte]
        APPEL_RECHERCHE, RETOUR_RECHERCHE = v["appel"], v["retour"]
        OCTETS_ATTENDUS, CONSTRUCTEURS = v["octets"], v["constructeurs"]
    elif empreinte != DLL_SHA256:
        sys.exit("bob_terrain.modder.x64.dll a changé (mise à jour du kit ?) : décalages à relever de nouveau")
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt = pe + 24 + struct.unpack_from("<H", b, pe + 20)[0]
    for rva, attendu in OCTETS_ATTENDUS.items():
        for i in range(nsec):
            vsz, va, rsz, rptr = struct.unpack_from("<IIII", b, opt + 40 * i + 8)
            if va <= rva < va + vsz:
                vu = b[rptr + rva - va: rptr + rva - va + len(attendu) // 2].hex()
                if vu != attendu:
                    sys.exit(f"octets inattendus à bob_terrain+0x{rva:x} : {vu} au lieu de {attendu}")


def cdb():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-AppxPackage Microsoft.WinDbg* | Select-Object -First 1).InstallLocation"],
                       capture_output=True, text=True)
    chemin = os.path.join(r.stdout.strip(), "amd64", "cdb.exe")
    if not os.path.isfile(chemin):
        sys.exit("cdb.exe introuvable : installer WinDbg (Microsoft Store)")
    return chemin


def commandes_cdb(minx, maxx, dossier):
    bits = lambda f: struct.unpack("<I", struct.pack("<f", f))[0]
    vidage = os.path.join(dossier, "bob_plantage.dmp").replace("\\", "/")   # pas d'antislash dans cdb
    l = [f'sxd -c2 ".printf \\"EXCEPTION SECONDE CHANCE\\\\n\\"; r; dps @rsp L10; k 40; .dump /m {vidage}; '
         f'.kill; q" av',
         "sxd eh", "sxd ld", "sxd ud", "sxd ct", "sxd et",
         f".dvalloc /b 0x{BLOC:x} 0x1000",
         f"ed 0x{BLOC + 0xF0:x} 0x{bits(minx):08x}",
         f"ed 0x{BLOC + 0xF4:x} 0x{bits(maxx):08x}",
         f'bu bob_terrain_modder_x64+0x{RETOUR_RECHERCHE:x} ".if (@rax == 0) {{ r rax = 0x{BLOC:x}; '
         f'.printf \\"[recherche] carte absente de la base de BOB : enregistrement fourni\\\\n\\" }} '
         f'.else {{ .printf \\"[recherche] carte trouvee dans la base de BOB\\\\n\\" }}; gc"']
    for rva, nom in CONSTRUCTEURS.items():
        l.append(f'bu bob_terrain_modder_x64+0x{rva:x} ".printf \\"[action] {nom}\\\\n\\"; gc"')
    l.append("g")
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carte", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--delai", type=int, default=3600, help="durée maximale en secondes (défaut 3600)")
    ap.add_argument("--sans", default="",
                    help="sorties à ne pas redemander, séparées par des virgules ; ex. "
                         "full_height_map.dds,full_logic_map.compressed_map pour sauter le relief déjà "
                         "compilé (25 min, et BOB plante au nettoyage de cette action, voir le journal § 7.6)")
    ap.add_argument("--bataille", action="store_true",
                    help="compiler le terrain de BATAILLE de la campagne (raw_data\\terrain\\battles\\<carte>\\, "
                         "fabriqué par dossier_bataille_campagne.py) au lieu du terrain de campagne")
    a = ap.parse_args()
    # Toujours sauté : « Generate Camera Height Map » fait planter BOB (DirectX refuse la surface
    # d'affichage, puis appel d'un pointeur nul ; journal § 7.7). `camera_heightmap.py` le remplace.
    sans = ["camera_heightmap.png"] + [x.strip() for x in a.sans.split(",") if x.strip()]
    sys.stdout.reconfigure(encoding="utf-8")

    carte = a.carte
    terry = os.path.join(KIT, "raw_data", "terrain", "battles" if a.bataille else "campaigns", carte, f"{carte}.terry")
    if not os.path.isfile(terry):
        sys.exit(f"projet Terry absent : {terry}" +
                 (" (le fabriquer : dossier_bataille_campagne.py --apply)" if a.bataille else ""))
    verifier_dll()
    minx, maxx = zone_jouable(carte)
    outil = cdb()
    print(f"carte {carte} : minx {minx}, maxx {maxx} ; bob_terrain vérifié ; cdb : {outil}")
    if subprocess.run(["tasklist", "/FI", "IMAGENAME eq tweak.modder.x64.exe"], capture_output=True,
                      text=True).stdout.count("tweak.modder") and a.apply:
        sys.exit("Terry est ouvert : le fermer d'abord (il verrouille des fichiers de working_data)")
    if not a.apply:
        print("vérifications faites ; relancer avec --apply pour compiler")
        return

    nom_conf = f"zz_{carte}" + ("_bataille" if a.bataille else "")
    with open(os.path.join(BIN, "BOB", f"{nom_conf}_configuration.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(configuration(carte, sans, a.bataille))
    if sans:
        print("sorties non redemandées :", ", ".join(sans))
    dossier = os.path.join(JOURNAL, f"{carte}{'-bataille' if a.bataille else ''}-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dossier)
    with open(os.path.join(dossier, "commandes.cdb"), "w", encoding="ascii", newline="\n") as f:
        f.write(commandes_cdb(minx, maxx, dossier))
    chemin_terry = terry.replace("\\", "/").lower()
    # -hd : pas de tas de débogage pour BOB (sous débogueur, Windows l'active par défaut et change le
    # comportement de la mémoire ; première piste pour les plantages du 21.09.2026, journal § 7.6).
    commande = [outil, "-G", "-hd", "-logo", os.path.join(dossier, "cdb.log"), "-cf", os.path.join(dossier, "commandes.cdb"),
                os.path.join(BIN, "BOB.modder.x64.exe"), "/dont_stop_on_error", "/nosplashscreen",
                "/get_latest_rules", "-no_console", "/offline", f"/configuration:{nom_conf}", "/workspace:",
                f"/changelist:Terry ({chemin_terry})"]
    t0 = time.time()
    print("compilation lancée", time.strftime("%H:%M:%S"))
    subprocess.run(commande, cwd=BIN, timeout=a.delai, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"terminée en {int(time.time() - t0)} s")
    for journal in ("bob.log", "bob_error.log", "bob_warnings.log", "bob_plugin_error.log"):
        if os.path.exists(os.path.join(BIN, journal)):
            shutil.copy2(os.path.join(BIN, journal), dossier)
    log = io.open(os.path.join(dossier, "cdb.log"), encoding="utf-8", errors="replace").read()
    for ligne in log.splitlines():
        if ligne.startswith(("[recherche]", "[action]", "EXCEPTION")) or "Allocated 1000 bytes" in ligne:
            print("  ", ligne)
    bob = io.open(os.path.join(dossier, "bob.log"), encoding="utf-8", errors="replace").read()
    print("  ", bob.splitlines()[0] if bob else "bob.log vide")
    for m in re.finditer(r"^=== (\w+ / .+?) \(c:.*?\) \(STATUS: (\w+)\) ===", bob, re.M):
        print(f"     {m.group(2):20} {m.group(1)}")
    print("  ", (re.search(r"Exit code: .*", bob) or ["code de sortie absent"])[0])
    print("journaux :", dossier)


if __name__ == "__main__":
    main()
