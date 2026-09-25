#!/usr/bin/env python3
"""
entites_wh1.py - la vie de la carte de WH1 en entités Terry : lumières ponctuelles, formes sonores, effets (braseros,
lave, brumes, cascades...), scènes composites de faune ; et la couleur de la mer de WH1.

Pourquoi (22.09.2026, audit de fidélité, `05-journal\\2026-09-22-phase-4\\audit-fidelite.md`) : `global_props.bin`
de WH1 porte, en plus des objets, 1 028 lumières, 1 021 formes sonores, 1 859 émetteurs d'effets et 36 scènes de
faune, que la conversion des objets ne lisait pas (son motif ne prend que les modèles). Aucune n'était sur notre
carte. Charles (22.09.2026, 23 h 35) : « attaque tout ça ».

Interface convenue avec la construction (`terrain_wh1_vers_terry.py` appelle, écrit un calque de plus) :
    entites_ambiance(recaler_y=None) -> {région de WH1: [blocs XML <entity>]}
        positions de WH1 brutes (espace hex = monde des entités de WH3, erreur 89) ; `recaler_y(x, y, z)` rend le y
        final (décalage de notre sol sur celui de WH1) ; identifiants stables (même règle que
        `terrain_wh1_vers_terry.ident`) ; masques de culture par `props_wh1_vers_layers.masque_culture`.
    couleur_mer_wh1() -> tableau uint8 (3524, 3200, 4), ligne 0 au nord, pour la couche `color_overlay_sea`.

Formes d'enregistrement de WH1 (lots FASTBIN0 v21, établies sur les octets, 22.09.2026) :
    lumière  u16 4 | x y z rayon r g b intensité (f32) | u8 animation | f32 vitesse1 vitesse2 couleur_min
             décalage_aléatoire | u16 n + « WPLFT_* »
    son      u16 6 | u16 n + clé | u16 n + « SST_POINT | SST_LINE_LIST | SST_SPHERE » | u32 k | k × (x y z)
    effet    u16 4 | u16 n + nom | matrice 3 x 3 | x y z
    scène    u16 3 | matrice 3 x 3 | x y z | u16 n + « composite_scene/...csc »

Conversions vers WH3 (Terry, modèles relevés dans le projet des Empires) :
- lumière -> ECPointLight avec les réglages que CA a choisis dans WH3 pour le même effet (révisé le 23.09.2026 :
  voir `reglages_lumieres_ca` ; la première version, loi d'intensité et rayon de WH1, donnait des taches orange
  vives). Sans effet voisin : couleur de WH1 × 255, rayon × 0,5, colour_scale 500 000, SMOOTH ; l'animation de WH1
  (`LAT_NONE`, `LAT_RADIUS_SIN`, `LAT_RADIUS_SIN_SIN` pour 0, 1, 2 ; vitesses, `colour_min`, `random_offset`) reprise.
- son -> ECSoundMarker `key` ; ligne -> ECPolyline3D (points relatifs, y = 0, comme CA ; SST_LINE_LIST de WH1 est une
  ligne continue : 3, 5, 7 points existent, et les paires ne se touchent jamais). Clés inconnues des cartes de CA de
  WH3 et sphères : écartées ; vent de montagne retiré, rivières et lave espacées (`SONS_RETIRES`, `ESPACEMENT_SONS`).
- effet -> ECVFX `vfx`, rotation et échelle de la matrice ; noms inconnus de WH3 : écartés (comptés).
- scène -> ECCompositeScene `path` (les 16 chemins existent dans WH3).

Usage :
    python entites_wh1.py            # bilan par type, exemples d'entités
    python entites_wh1.py --ecrire <calque.layer>   # un calque d'essai autonome (hors chaîne)
"""

import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lire_props_wh1 as LP                                          # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit)
WH3_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
CACHE_WH3 = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "entites-wh1", "noms_connus_wh3.json")
LF_SEA_COLOUR_WH1 = os.path.join(ATELIER, "03-references", "saison-des-revelations", "terrain-wh1", "terrain", "campaigns",
                                 carte_config.CARTE_SOURCE, "lf_sea_colour.dds")
CARTES_WH3 = ("wh3_main_prologue_map", "wh3_main_combi_map_1", "wh3_main_chaos_map_1")
H_RASTER, L_RASTER = 3524, 3200

# Lumières (révisé le 23.09.2026, essai de Charles : « grandes taches orange vif au sol » près des braseros). CA a
# repris les braseros de WH1 dans WH3 avec la MÊME couleur (255 158 78) mais rayon 1,0 au lieu de 2,0, colour_scale
# 630 000 et atténuation SMOOTH (réglage le plus fréquent des 1 698 lumières de brasero des Empires). Règle : chaque
# lumière de WH1 prend les réglages de CA pour l'effet de WH1 le plus proche (< 1 unité), relevés aux Empires
# (`reglages_lumieres_ca`, cache `lumieres_ca.json`) ; sans effet voisin ou sans équivalent chez CA : couleur de WH1,
# rayon de WH1 × 0,5 (rapport du brasero), colour_scale 500 000 (médiane des 24 105 lumières des Empires), SMOOTH.
CACHE_LUMIERES_CA = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "entites-wh1", "lumieres_ca.json")
PROJET_EMPIRES = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain"
                  r"\campaigns\wh3_main_combi_map_1")
RAYON_SANS_EFFET, ECHELLE_SANS_EFFET = 0.5, 500000.0
DISTANCE_EFFET = 1.0
ANIMATIONS = {0: "LAT_NONE", 1: "LAT_RADIUS_SIN", 2: "LAT_RADIUS_SIN_SIN"}
# Sons (révisé le 23.09.2026, essai de Charles : « pas mal de problèmes avec le son »). WH1 posait 100 fois plus de
# sons de rivière et 2 000 fois plus de vent de montagne par unité de surface que CA aux Empires ; dans WH3 le vent de
# montagne, la mer et les marais viennent du type de sol (`audio_campaign_environment_ground_type_sound_assignments`,
# six lignes par carte chez CA). Règle : les sons de vent de montagne de WH1 sont retirés (le type de sol Montagne les
# remplace) ; ceux de rivière et de lave sont espacés d'au moins `ESPACEMENT_SONS` unités ; les autres restent.
SONS_RETIRES = {"Sound_Environment_Wind_Mountain_Moderate_Light", "Sound_Environment_Wind_Mountain_Moderate_Strong"}
ESPACEMENT_SONS = {"Sound_Environment_River_Small_Moderate": 20.0, "Sound_Environment_Lava_River": 20.0}
# Effets écartés (23.09.2026, 16 h 40, session du rendu ; erreur 146 de la construction) : l'herbe de WH1 recréée
# (`effets-wh1\vfx\wh_main_campaign_enviro_grass.xml`, émetteur `grass` de `wh_main_lib_campaign_enviro2`, qu'aucun effet
# de CA n'active dans WH3) plantait le rendu (Warhammer3.exe+0x1A3DCFA, tâche de rendu, pointeur 0x20) dès qu'elle entrait
# dans le champ de la caméra : Alberic à Bordeleaux au tour 1, Durthu au tour 9. Preuve : pack d'essai sans l'émetteur,
# plus de plantage (4 et 5 tours). Ses 33 poses sont retirées (l'effet reste vide dans le pack).
# 23.09.2026, 17 h 50 (construction) : Grom plantait encore à la même adresse, au tour 1, l'herbe seule désactivée ; avec
# les six effets de WH1 recréés vides, plus rien. Les six sont vidés dans `effets-wh1\vfx` (originaux dans 99-archives) et
# leurs poses retirées ici ; leur reconversion sur des effets de CA se fera un par un, testée en jeu.
EFFETS_ECARTES = {"wh_main_campaign_enviro_grass", "wh_dlc05_campaign_enviro_shadow_shapes",
                  "wh_dlc05_campaign_enviro_snowstorm", "wh_main_campaign_enviro_cloud1", "wh_main_campaign_motes",
                  "wh_main_campaign_static_godrays"}

# (24.09.2026, 04 h 20 ; proposition de la session IA, relayée par la construction ; vidéo de WH1 : colonnes de lumière verte
# au-dessus du Chêne et de la Clairière Royale) : les rais de lumière de WH1 (`wh_main_campaign_static_godrays`, vidé et
# écarté plus haut) sont posés avec l'effet de CA `wh_main_campaign_enviro_godrays`, déjà posé 2 fois chez nous sans
# plantage depuis le 23.09.
EFFETS_REMPLACES = {"wh_main_campaign_static_godrays": "wh_main_campaign_enviro_godrays",
                    # (24.09.2026, chaîne 11 ; Charles : « les animations, les particules ») les poussières lumineuses de
                    # WH1 (2 poses à Tal Esth) et sa tempête de neige (1 pose à Tal Amere) par les effets de CA les plus
                    # proches, définis dans les packs de CA (brouillon `effets_ecartes.py`) ; les nuages hauts (cloud1),
                    # les ombres d'Athel Loren et l'herbe restent écartés
                    "wh_main_campaign_motes": "wh2_main_campaign_enviro_sparkles",
                    "wh_dlc05_campaign_enviro_snowstorm": "wh_dlc05_campaign_snowstorm_spawn"}

# LA FAUNE DE WH1 À L'ÉCHELLE DE CA (24.09.2026, chaîne 11 ; construction, vidéo V2 de Charles, 127 et 130 s : cerf, renard
# et cheval « aussi hauts que les arbres »). Les mêmes scènes chez CA (Empires) et chez WH1, échelle de pose relevée
# (brouillons `faune_ie.py`, `faune_wh1.py`) : chevaux 0,36 à 0,43 contre 0,47 à 0,59 ; loups 0,57 contre 0,69 à 0,98 :
# un rapport constant d'environ 0,7. Les scènes de faune au sol de WH1 sont posées à ECHELLE_FAUNE_WH1 de leur échelle ;
# oiseaux et créatures volantes gardent la leur.
ECHELLE_FAUNE_WH1 = 0.7
FAUNE_VOLANTE = ("/birds/", "/flying/", "/bi1/", "/gc1/")

RX_LUMIERE = re.compile(rb"WPLFT_[A-Z]+")
RX_SON = re.compile(rb"SST_[A-Z_]+")
RX_EFFET = re.compile(rb"\x04\x00([\x05-\x7f])\x00(?=[a-z])")
RX_SCENE = re.compile(rb"composite_scene/[\x20-\x7e]+?\.csc")
NOM_EFFET = re.compile(r"^[a-z][a-z0-9_]{4,}$")


def ident(graine):
    """Identifiant Terry stable : même règle que `terrain_wh1_vers_terry.ident`."""
    return "1" + hashlib.sha1(f"{CARTE}:{graine}".encode()).hexdigest()[:14]


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0] if 0 <= o <= len(b) - 2 else -1


def _chaine_avant(b, fin, maxi=160):
    for k in range(3, maxi):
        d = fin - k
        if d < 2:
            break
        if _u16(b, d - 2) == k and all(0x20 <= c <= 0x7e for c in b[d:fin]):
            return b[d:fin].decode("ascii")
    return None


def lire_lot(blob):
    """Entités d'un lot : dicts (type, nom, position, ...)."""
    out = []
    for m in RX_LUMIERE.finditer(blob):
        s = m.start()
        if _u16(blob, s - 2) != len(m.group(0)) or _u16(blob, s - 53) != 4:
            continue
        x, y, z, rayon, r, g, bl, inten = struct.unpack_from("<8f", blob, s - 51)
        anim = blob[s - 19]
        v1, v2, cmin, alea = struct.unpack_from("<4f", blob, s - 18)
        out.append({"type": "lumiere", "nom": m.group(0).decode(), "position": (x, y, z), "rayon": rayon,
                    "couleur": (r, g, bl), "intensite": inten, "animation": anim, "vitesses": (v1, v2),
                    "couleur_min": cmin, "decalage": alea})
    for m in RX_SON.finditer(blob):
        s, e = m.start(), m.end()
        if _u16(blob, s - 2) != len(m.group(0)):
            continue
        cle = _chaine_avant(blob, s - 2)
        k = struct.unpack_from("<I", blob, e)[0] if e + 4 <= len(blob) else 0
        if not cle or not 0 < k < 4096:
            continue
        pts = [struct.unpack_from("<3f", blob, e + 4 + 12 * i) for i in range(k)]
        out.append({"type": "son", "nom": cle, "forme": m.group(0).decode(), "position": pts[0], "points": pts})
    for m in RX_EFFET.finditer(blob):
        n, deb = m.group(1)[0], m.end()
        nom = blob[deb:deb + n]
        if len(nom) != n or not all(0x20 <= c <= 0x7e for c in nom):
            continue
        nom = nom.decode("ascii")
        if not NOM_EFFET.match(nom) or ("campaign" not in nom and not nom.startswith("vfx")):
            continue
        v = struct.unpack_from("<12f", blob, deb + n) if deb + n + 48 <= len(blob) else None
        if not v or not all(abs(c) < 1e4 for c in v):
            continue
        out.append({"type": "effet", "nom": nom, "matrice": v[:9], "position": v[9:12]})
    for m in RX_SCENE.finditer(blob):
        s = m.start()
        if _u16(blob, s - 2) != len(m.group(0)) or _u16(blob, s - 52) != 3:
            continue
        v = struct.unpack_from("<12f", blob, s - 50)
        out.append({"type": "scene", "nom": m.group(0).decode().lower(), "matrice": v[:9], "position": v[9:12]})
    return out


def entites_uniques():
    """Chaque entité de WH1 une fois, avec sa région et l'ensemble des bits (cultures) des lots où elle figure — même
    règle que `props_wh1_vers_layers.objets_uniques` (lots sans variante ou sans région ignorés)."""
    import props_wh1_vers_layers as PL
    vus = {}
    for court, region, a, v, blob in LP.lots(LP.GLOBAL_PROPS):
        if v is None or region is None:
            continue
        bit = PL.BIT_DE_VARIANTE.get(v, v)
        for e in lire_lot(blob):
            cle = (e["type"], e["nom"], tuple(round(c, 3) for c in e["position"]))
            if cle not in vus:
                vus[cle] = dict(e, region=region, bits=set())
            vus[cle]["bits"].add(bit)
    return list(vus.values())


EFFETS_PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "effets-wh1", "vfx")


def effets_du_projet():
    """Effets que NOUS livrons (23.09.2026, session de construction) : les six effets de WH1 dont WH3 a les émetteurs
    mais pas le fichier de haut niveau `vfx/<effet>.xml` (grass, shadow_shapes, cloud1, static_godrays, motes,
    snowstorm), recréés dans `effets-wh1\\vfx\\` et embarqués par build_pack. Ils comptent comme connus de WH3."""
    if not os.path.isdir(EFFETS_PROJET):
        return set()
    return {f[:-len(".xml")] for f in os.listdir(EFFETS_PROJET) if f.endswith(".xml")}


def noms_connus_wh3():
    """{"effets": [...], "sons": [...], "scenes": [...]} que WH3 connaît (mis en cache) : effets définis par un fichier
    `vfx/<nom>.xml` des packs de CA (35 des 41 noms de WH1 ; certains, comme `wh_dlc05_campaign_enviro_waystone` ou
    `..._forest_spirits`, n'ont aucune pose sur les cartes de CA mais existent) ou posés par une carte de CA ; clés de
    son employées par une carte de CA (les banques de sons ne sont pas lisibles ici) ; scènes composites présentes.
    Le cache ne tient que ce qui vient de CA ; les effets du projet (`effets_du_projet`) s'y ajoutent à chaque appel."""
    if os.path.exists(CACHE_WH3):
        out = json.load(open(CACHE_WH3, encoding="utf-8"))
        out["effets"] = sorted(set(out["effets"]) | effets_du_projet())
        return out
    import contenu_pack as CP
    src = CP.SourcePacks(WH3_DATA)
    effets, sons, scenes = set(), set(), set()
    effets |= {c[len("vfx/"):-len(".xml")] for c in src.ou if c.startswith("vfx/") and c.endswith(".xml")}
    for carte in CARTES_WH3:
        b = src.lire(f"terrain/campaigns/{carte}/global_props.bin")
        for m in re.finditer(rb"[\x20-\x7e]{5,}", b or b""):
            s = m.group(0).decode("ascii")
            if s.startswith("Sound_"):
                sons.add(s)
            elif s.lower().startswith("composite_scene/"):
                scenes.add(s.lower())
            elif "_campaign_" in s and NOM_EFFET.match(s):
                effets.add(s)
    scenes |= {c for c in src.ou if c.startswith("composite_scene/") and c.endswith(".csc")}
    out = {"effets": sorted(effets), "sons": sorted(sons), "scenes": sorted(scenes)}
    os.makedirs(os.path.dirname(CACHE_WH3), exist_ok=True)
    json.dump(out, open(CACHE_WH3, "w", encoding="utf-8"), indent=0)
    out["effets"] = sorted(set(out["effets"]) | effets_du_projet())
    return out


def reglages_lumieres_ca():
    """{nom d'effet: réglages de lumière de CA} : aux Empires, chaque ECPointLight est rattachée à l'ECVFX le plus
    proche (< 1 unité) ; par effet, le réglage le plus fréquent. Mis en cache (le relevé lit les 635 calques)."""
    if os.path.exists(CACHE_LUMIERES_CA):
        return json.load(open(CACHE_LUMIERES_CA, encoding="utf-8"))
    import glob
    import numpy as np
    lum, fx = [], []
    for f in glob.glob(os.path.join(PROJET_EMPIRES, "*.layer")):
        t = open(f, encoding="utf-8", errors="replace").read()
        for e in re.findall(r"<entity\b.*?</entity>", t, re.S):
            p = re.search(r'<ECTransform position="([^"]+)"', e)
            if not p:
                continue
            pos = [float(c) for c in p.group(1).split()]
            m = re.search(r"<ECPointLight ([^>]*)/>", e)
            if m:
                lum.append((dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))), pos))
            m = re.search(r'<ECVFX vfx="([^"]+)"', e)
            if m:
                fx.append((m.group(1), pos))
    P = np.array([p for _, p in fx])
    par_effet = defaultdict(Counter)
    for d, p in lum:
        dd = np.hypot(P[:, 0] - p[0], P[:, 2] - p[2])
        k = int(np.argmin(dd))
        if dd[k] < DISTANCE_EFFET:
            par_effet[fx[k][0]][(round(float(d["radius"]), 2), d["colour_scale"], d["colour"], d["falloff_type"],
                                  d["animation_type"], d.get("animation_speed_scale", "0.0 0.0"),
                                  d.get("colour_min", "0.0"), d.get("random_offset", "0.0"))] += 1
    out = {}
    for n, c in par_effet.items():
        (r, cs, col, fo, an, sp, cm, ro), k = c.most_common(1)[0]
        out[n] = {"radius": r, "colour_scale": float(cs), "colour": col, "falloff_type": fo, "animation_type": an,
                  "animation_speed_scale": sp, "colour_min": cm, "random_offset": ro, "exemples": k,
                  "total": sum(c.values())}
    os.makedirs(os.path.dirname(CACHE_LUMIERES_CA), exist_ok=True)
    json.dump(out, open(CACHE_LUMIERES_CA, "w", encoding="utf-8"), indent=1)
    return out


def _f(v):
    return f"{v:.5f}"


def _commun(masque, position, rotation=(0.0, 0.0, 0.0), echelle=(1.0, 1.0, 1.0), campagne=None):
    pos = " ".join(_f(c) for c in position)
    rot = " ".join(_f(c) for c in rotation)
    ech = " ".join(_f(c) for c in echelle)
    camp = campagne or (f'\t\t\t<ECCampaignProperties visible_in_shroud="False" visible_in_shroud_only="False" '
                        f'no_culling="False" culture_mask="{masque}"/>\n')
    return (camp + f'\t\t\t<ECTransform position="{pos}" rotation="{rot}" scale="{ech}" pivot="0 0 0"/>\n')


VISIBILITE = ('\t\t\t<ECVisibilitySettingsCampaign visible_in_tactical_view="False" '
              'visible_in_tactical_view_only="False"/>\n')


# (25.09.2026, 04 h 45, chaîne 16 ; Charles, capture de 04 h 05 : taches d'eau turquoise vif sur la terre et au delta du
# Grismerie ; enquête `scratchpad\enquete_deltas\`) : ce sont les lumières turquoise (7, 255, 206) des feux de bale des
# vampires, au rayon de CA (1,5 u) ; WH1 : 0,63 u pour 53 d'entre elles, 0,9 ou 1,2 pour les autres (5,7 fois moins de
# surface). Pour ces effets, le rayon de WH1 ; couleur, intensité et animation de CA gardées.
RAYON_WH1_EFFETS = ("bale_fire",)


def entite_xml(e, masque, position):
    """Bloc <entity> Terry pour l'entité `e` de WH1 à `position` (monde des entités)."""
    import props_wh1_vers_layers as PL
    graine = f"{e['type']}:{e['region']}:{e['nom']}:{tuple(round(c, 3) for c in e['position'])}"
    tete = f'\t\t<entity id="{ident(graine)}">\n'
    if e["type"] == "lumiere":
        ca = e.get("reglage_ca")
        if ca:
            couleur, echelle, rayon, attenuation = ca["colour"], ca["colour_scale"], ca["radius"], ca["falloff_type"]
            anim, vitesses, cmin, alea = (ca["animation_type"], ca["animation_speed_scale"], ca["colour_min"],
                                          ca["random_offset"])
            if any(m in e.get("effet_voisin", "") for m in RAYON_WH1_EFFETS):
                rayon = e["rayon"]
        else:
            r, g, b = (max(0, min(255, round(c * 255))) for c in e["couleur"])
            couleur, echelle, rayon, attenuation = f"{r} {g} {b} 255", ECHELLE_SANS_EFFET, e["rayon"] * RAYON_SANS_EFFET, \
                "WPLFT_SMOOTH"
            anim = ANIMATIONS.get(e["animation"], "LAT_NONE")
            vitesses = f'{e["vitesses"][0]:.5f} {e["vitesses"][1]:.5f}'
            cmin, alea = f'{e["couleur_min"]:.5f}', f'{e["decalage"]:.5f}'
        corps = (f'\t\t\t<ECPointLight colour="{couleur}" colour_scale="{float(echelle):.1f}" '
                 f'radius="{float(rayon):.5f}" animation_type="{anim}" animation_speed_scale="{vitesses}" '
                 f'colour_min="{cmin}" random_offset="{alea}" falloff_type="{attenuation}" '
                 'for_light_probes_only="False"/>\n' + VISIBILITE + _commun(masque, position))
    elif e["type"] == "son":
        corps = f'\t\t\t<ECSoundMarker key="{e["nom"]}" />\n' + _commun(
            masque, position, campagne=f'\t\t\t<ECCampaignProperties culture_mask="{masque}"/>\n')
        if e["forme"] == "SST_LINE_LIST" and len(e["points"]) > 1:
            x0, _, z0 = e["points"][0]
            pts = "".join(f'\t\t\t\t\t<point x="{_f(x - x0)}" y="0.0" z="{_f(z - z0)}"/>\n' for x, _, z in e["points"])
            corps += ('\t\t\t<ECPolyline3D>\n\t\t\t\t<polyline3d closed="false">\n' + pts +
                      '\t\t\t\t</polyline3d>\n\t\t\t</ECPolyline3D>\n')
    elif e["type"] in ("effet", "scene"):
        rot, ech = PL.rotation_terry(e["matrice"])
        if e["type"] == "effet":
            corps = (VISIBILITE + f'\t\t\t<ECVFX vfx="{e["nom"]}" autoplay="true" scale="1" instance_name=""/>\n'
                     + _commun(masque, position, rot, ech))
        else:
            if "campaign_fauna/" in e["nom"] and not any(v in e["nom"] for v in FAUNE_VOLANTE):
                ech = tuple(c * ECHELLE_FAUNE_WH1 for c in ech)
            corps = (f'\t\t\t<ECCompositeScene path="{e["nom"]}" script_id="" autoplay="true"/>\n' + VISIBILITE
                     + _commun(masque, position, rot, ech))
    else:
        return None
    return tete + corps + "\t\t</entity>\n"


def entites_ambiance(recaler_y=None, bilan=None):
    """{région de WH1: [blocs XML <entity>]} ; `bilan` (dict) reçoit les comptes par type et les écartés."""
    import numpy as np
    import props_wh1_vers_layers as PL
    connus = noms_connus_wh3()
    effets_ok, sons_ok, scenes_ok = set(connus["effets"]), set(connus["sons"]), set(connus["scenes"])
    reglages = reglages_lumieres_ca()
    out = defaultdict(list)
    b = bilan if bilan is not None else {}
    for t in ("lumiere", "son", "effet", "scene"):
        b[t] = Counter()
    uniques = entites_uniques()
    effets = [e for e in uniques if e["type"] == "effet"]
    pos_effets = np.array([[e["position"][0], e["position"][2]] for e in effets]) if effets else np.zeros((0, 2))
    gardes = defaultdict(list)                          # sons espacés : positions déjà gardées, par clé
    for e in sorted(uniques, key=lambda e: (e["type"], e["nom"], e["position"])):
        t = e["type"]
        if t == "lumiere" and len(pos_effets):
            d = np.hypot(pos_effets[:, 0] - e["position"][0], pos_effets[:, 1] - e["position"][2])
            k = int(np.argmin(d))
            if d[k] < DISTANCE_EFFET and effets[k]["nom"] in reglages:
                e = dict(e, reglage_ca=reglages[effets[k]["nom"]], effet_voisin=effets[k]["nom"])
                b[t][f"réglage de CA ({effets[k]['nom']})"] += 1
            else:
                b[t]["règle sans effet voisin"] += 1
        if t == "son" and (e["nom"] not in sons_ok or e["forme"] == "SST_SPHERE"):
            b[t]["écarté : clé inconnue de WH3 ou sphère"] += 1
            continue
        if t == "son" and e["nom"] in SONS_RETIRES:
            b[t]["retiré : vent de montagne (type de sol Montagne de WH3)"] += 1
            continue
        if t == "son" and e["nom"] in ESPACEMENT_SONS:
            x, _, z = e["position"]
            if any(math.hypot(x - gx, z - gz) < ESPACEMENT_SONS[e["nom"]] for gx, gz in gardes[e["nom"]]):
                b[t][f"espacé : {e['nom']}"] += 1
                continue
            gardes[e["nom"]].append((x, z))
        if t == "effet" and e["nom"] in EFFETS_REMPLACES:
            e = dict(e, nom=EFFETS_REMPLACES[e["nom"]])
            b[t]["remplacé par un effet de CA (EFFETS_REMPLACES)"] += 1
        if t == "effet" and e["nom"] not in effets_ok:
            b[t]["écarté : effet inconnu de WH3"] += 1
            continue
        if t == "effet" and e["nom"] in EFFETS_ECARTES:
            b[t]["écarté : effet qui plante le rendu (EFFETS_ECARTES)"] += 1
            continue
        if t == "scene" and e["nom"] not in scenes_ok:
            b[t]["écarté : scène inconnue de WH3"] += 1
            continue
        masque, garder = PL.masque_culture({"bits": e["bits"], "region": e["region"]})
        if not garder:
            b[t]["écarté : dévastation seule (masque nul)"] += 1
            continue
        x, y, z = e["position"]
        if recaler_y is not None:
            y = recaler_y(x, y, z)
        bloc = entite_xml(e, masque, (x, y, z))
        if bloc:
            out[e["region"]].append(bloc)
            b[t]["écrit" + (" (masqué)" if masque else "")] += 1
    return dict(out)


def couleur_mer_wh1():
    """lf_sea_colour.dds de WH1 (800 x 881 cases, BGRA non compressé) agrandi 4 x : (3524, 3200, 4) uint8, ligne 0 au
    nord, alpha 255. Sens des lignes : établi par `--verifier-mer` (tile_map du projet)."""
    import numpy as np
    b = open(LF_SEA_COLOUR_WH1, "rb").read()
    h, w = struct.unpack_from("<II", b, 12)
    bits, rm, gm, bm, am = struct.unpack_from("<5I", b, 88)
    px = np.frombuffer(b, np.uint32, count=w * h, offset=128).reshape(h, w).astype(np.int64)

    def canal(m):
        s = (m & -m).bit_length() - 1
        return ((px & m) >> s).astype(np.uint8)
    rgba = np.stack([canal(rm), canal(gm), canal(bm), np.full((h, w), 255, np.uint8)], -1)
    if SENS_MER_RETOURNE:
        rgba = rgba[::-1]
    grand = np.repeat(np.repeat(rgba, 4, 0), 4, 1)
    out = np.zeros((H_RASTER, L_RASTER, 4), np.uint8)
    out[:min(H_RASTER, grand.shape[0]), :min(L_RASTER, grand.shape[1])] = grand[:H_RASTER, :L_RASTER]
    return out


# Sens des lignes établi le 22.09.2026 (`--verifier-mer` et image côte à côte avec la mer de tile_map.png) : le golfe
# du nord-ouest est en haut dans le fichier de WH1 tel quel, comme dans tile_map (ligne 0 au nord) -> pas de retournement.
SENS_MER_RETOURNE = False


def verifier_sens_mer():
    """Compare la couleur de la mer de WH1 à la mer de tile_map.png du projet dans les deux sens de lignes : dans le
    bon sens, les pixels de mer et de terre ont des couleurs moyennes nettement différentes."""
    import numpy as np
    from PIL import Image
    global SENS_MER_RETOURNE
    projet = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain"
              rf"\campaigns\{CARTE}")
    tm = np.array(Image.open(os.path.join(projet, "tile_map.png")).convert("RGB"))
    mer = np.all(tm == (83, 141, 213), axis=-1)                     # 881 x 800 cases, ligne 0 au nord
    b = open(LF_SEA_COLOUR_WH1, "rb").read()
    h, w = struct.unpack_from("<II", b, 12)
    px = np.frombuffer(b, np.uint32, count=w * h, offset=128).reshape(h, w)
    lum = ((px >> 16) & 255).astype(float) + ((px >> 8) & 255) + (px & 255)
    res = {}
    for retourne in (False, True):
        l = lum[::-1] if retourne else lum
        hh, ww = min(l.shape[0], mer.shape[0]), min(l.shape[1], mer.shape[1])
        m, ll = mer[:hh, :ww], l[:hh, :ww]
        res[retourne] = abs(ll[m].mean() - ll[~m].mean())
        print(f"  lignes {'retournées' if retourne else 'telles quelles'} : écart de luminosité mer / terre {res[retourne]:.2f}")
    SENS_MER_RETOURNE = max(res, key=res.get)
    return SENS_MER_RETOURNE


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ecrire", help="écrire un calque d'essai autonome")
    ap.add_argument("--verifier-mer", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.verifier_mer:
        print("sens des lignes de lf_sea_colour de WH1 : retournées" if verifier_sens_mer() else "telles quelles")
        return 0
    print(f"réglages de lumière de CA : {len(reglages_lumieres_ca())} effets ; sans effet voisin : rayon × "
          f"{RAYON_SANS_EFFET}, colour_scale {ECHELLE_SANS_EFFET:.0f}, SMOOTH")
    bilan = {}
    par_region = entites_ambiance(bilan=bilan)
    for t, c in bilan.items():
        print(f"  {t:8s} {dict(c)}")
    n = sum(len(v) for v in par_region.values())
    print(f"{n} entités dans {len(par_region)} régions")
    for t in ("ECPointLight", "ECSoundMarker", "ECVFX", "ECCompositeScene"):
        ex = next((x for v in par_region.values() for x in v if t in x), None)
        if ex:
            print(f"\nexemple {t} :\n{ex}")
    if a.ecrire:
        with open(a.ecrire, "w", encoding="utf-8", newline="\n") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- ambiance_wh1 -->\n<layer version="41">\n\t<entities>\n'
                    + "".join(x for v in par_region.values() for x in v) + '\t</entities>\n'
                    "\t<associations>\n\t\t<Logical/>\n\t\t<Transform/>\n\t</associations>\n</layer>\n")
        print("calque écrit :", a.ecrire)
    return 0


if __name__ == "__main__":
    sys.exit(main())
