#!/usr/bin/env python3
"""
audit_fidelite.py - audit indépendant de la carte de WH1 portée dans WH3 (lecture seule, ne modifie rien).

Pourquoi (22.09.2026, 22 h 40, Charles) : « une map de campagne identique », « aucun oubli », « le relief
exactement pareil », « les décors exactement pareils ». La construction est faite par la session « Saison des
Révélations » ; cet audit mesure le résultat sur les fichiers finaux (packs, sorties de BOB), jamais sur les
compteurs des scripts qui les ont produits (erreur 81).

Sous-commandes :
    inventaire   fichiers de WH1 propres à la carte (tous ses packs) face à ceux de nos packs, par dossier
    structure    fichiers d'une carte dans les packs de CA de WH3, puis dans les nôtres (quels types WH3 attend)
    entites      entités de global_props.bin de WH1 autres que les objets à modèle de `rigidmodels/` ou
                 `terrain/` : lumières ponctuelles, formes sonores, émetteurs d'effets, scènes composites,
                 objets à modèle `vfx/`. Exemplaires uniques, noms connus de WH3 ou non, présence chez nous
                 (calques du projet Terry et global_props.bin du pack). Écrit la liste complète en JSON.

Formes d'enregistrement de WH1 (lots FASTBIN0 v21, établies le 22.09.2026 sur les octets) :
    lumière  u16 4 | x y z rayon r g b intensité (8 f32) | 17 octets | u16 n + « WPLFT_* » (atténuation)
    son      u16 6 | u16 n + clé d'événement | u16 n + « SST_* » | u32 k | k points (x y z)
    effet    u16 4 | u16 n + nom d'effet | matrice 3 x 3 | x y z
    scène    u16 3 | matrice 3 x 3 | x y z | u16 n + « composite_scene/...csc »
    objet    u16 12 | u16 n + chemin du modèle | matrice 3 x 3 | x y z  (lire_props_wh1 ; `vfx/` exclu de son motif)

Usage :
    python audit_fidelite.py inventaire [--filtre wh_dlc05_wood_elves] [--tout]
    python audit_fidelite.py structure [--carte wh3_main_prologue_map] [--n 15]
    python audit_fidelite.py entites [--pack <pack>] [--json <sortie>]
"""

import argparse
import glob
import json
import os
import re
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contenu_pack as CP                                            # noqa: E402

WH1_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\data"
WH3_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
NOS_PACKS = ("saison_des_revelations", "zz_startpos_db")
CARTE = "wh_dlc05_wood_elves_map_1"
PROJET_KIT = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data"
              r"\terrain\campaigns\wh_dlc05_wood_elves_map_1")
JOURNAL = r"C:\TotalWar-CampaignMap\05-journal\2026-09-22-phase-4"
CARTES_WH3 = ("wh3_main_prologue_map", "wh3_main_combi_map_1", "wh3_main_chaos_map_1")


def fichiers_packs(dossier, garder, filtre):
    """{chemin normalisé: [(pack, taille), ...]} des fichiers dont le chemin contient `filtre`,
    pour les packs du dossier que `garder(nom)` retient (ordre alphabétique)."""
    out = defaultdict(list)
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".pack") or not garder(nom):
            continue
        try:
            for c, taille in CP.entrees(os.path.join(dossier, nom)):
                n = c.replace("\\", "/").lower()
                if filtre in n:
                    out[n].append((nom, taille))
        except (SystemExit, ValueError, IndexError) as e:
            print(f"  pack illisible, ignoré : {nom} ({e})")
    return out


def dossier_de(chemin, profondeur=4):
    return "/".join(chemin.split("/")[:-1][:profondeur]) or "."


def inventaire(a):
    wh1 = fichiers_packs(WH1_DATA, lambda n: True, a.filtre)
    nous = fichiers_packs(WH3_DATA, lambda n: any(p in n for p in NOS_PACKS), a.filtre)
    print(f"WH1 : {len(wh1)} fichiers contenant « {a.filtre} » ; nos packs : {len(nous)}")
    doss = sorted({dossier_de(c) for c in wh1} | {dossier_de(c) for c in nous})
    print(f"\n{'dossier':70s} {'WH1':>6s} {'nous':>6s} {'communs':>8s} {'WH1 seul':>9s} {'nous seul':>9s}")
    for d in doss:
        w = {c for c in wh1 if dossier_de(c) == d}
        n = {c for c in nous if dossier_de(c) == d}
        print(f"{d:70s} {len(w):6d} {len(n):6d} {len(w & n):8d} {len(w - n):9d} {len(n - w):9d}")
    seuls = sorted(set(wh1) - set(nous))
    print(f"\nFichiers de WH1 sans fichier de même chemin chez nous : {len(seuls)}")
    par_dossier = defaultdict(list)
    for c in seuls:
        par_dossier[dossier_de(c, 6)].append(c)
    for d, liste in sorted(par_dossier.items()):
        print(f"  {d}  ({len(liste)})")
        for c in (liste if a.tout else liste[:12]):
            packs = ", ".join(sorted({p for p, _ in wh1[c]}))
            print(f"      {wh1[c][-1][1]:>10d}  {c.split('/')[-1]}   [{packs}]")
        if not a.tout and len(liste) > 12:
            print(f"      ... et {len(liste) - 12} autres (--tout)")
    doubles = {c: v for c, v in wh1.items() if len({p for p, _ in v}) > 1}
    if doubles:
        print(f"\nFichiers de WH1 présents dans plusieurs packs (le dernier chargé l'emporte) : {len(doubles)}")
        for c, v in sorted(doubles.items())[:20]:
            print(f"  {c}  <- {', '.join(f'{p} ({t})' for p, t in v)}")


def structure(a):
    """Dossiers et fichiers d'une carte dans les packs de CA de WH3 (hors nos packs), puis dans les nôtres :
    dit si un type de fichier que WH1 avait (ex. `global_meshes`) existe aussi dans les cartes de WH3."""
    for titre, dossier, garder in (("WH3 (packs de CA)", WH3_DATA, lambda n: not any(p in n for p in NOS_PACKS)),
                                   ("nos packs", WH3_DATA, lambda n: any(p in n for p in NOS_PACKS))):
        f = fichiers_packs(dossier, garder, a.carte)
        print(f"\n== {titre} : {len(f)} fichiers contenant « {a.carte} »")
        par = defaultdict(list)
        for c, v in f.items():
            par[dossier_de(c, 6)].append((c.split("/")[-1], v[-1][1], v[-1][0]))
        for d, liste in sorted(par.items()):
            print(f"  {d}  ({len(liste)})")
            for nom, t, p in sorted(liste)[:a.n]:
                print(f"      {t:>10d}  {nom}   [{p}]")
            if len(liste) > a.n:
                print(f"      ... et {len(liste) - a.n} autres")


RX_LUMIERE = re.compile(rb"WPLFT_[A-Z]+")
RX_SON = re.compile(rb"SST_[A-Z_]+")
RX_EFFET = re.compile(rb"\x04\x00([\x05-\x7f])\x00(?=[a-z])")
RX_SCENE = re.compile(rb"composite_scene/[\x20-\x7e]+?\.csc")
RX_OBJET_VFX = re.compile(rb"\x0c\x00(.)(.)(vfx/[\x20-\x7e]+?\.(?:wsmodel|rigid_model_v2))", re.S)
NOM_EFFET = re.compile(r"^[a-z][a-z0-9_]{4,}$")


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0] if 0 <= o <= len(b) - 2 else -1


def _f(b, o, n):
    return list(struct.unpack_from(f"<{n}f", b, o)) if 0 <= o <= len(b) - 4 * n else None


def _chaine_avant(b, fin, maxi=160):
    """Chaîne u16 n + ASCII qui se termine juste avant `fin` : (début, texte) ou (None, None)."""
    for k in range(3, maxi):
        d = fin - k
        if d < 2:
            break
        if _u16(b, d - 2) == k and all(0x20 <= c <= 0x7e for c in b[d:fin]):
            return d, b[d:fin].decode("ascii")
    return None, None


def entites_wh1_lot(blob):
    """[(type, nom, position, extra)] des entités non-objets d'un lot de WH1, et les anomalies de forme."""
    out, anomalies = [], Counter()
    for m in RX_LUMIERE.finditer(blob):
        s = m.start()
        if _u16(blob, s - 2) != len(m.group(0)) or _u16(blob, s - 53) != 4:
            anomalies["lumière hors forme"] += 1
            continue
        v = _f(blob, s - 51, 8)
        out.append(("lumière", m.group(0).decode(), tuple(v[:3]),
                    {"rayon": v[3], "couleur": v[4:7], "intensite": v[7], "atténuation": m.group(0).decode()}))
    for m in RX_SON.finditer(blob):
        s, e = m.start(), m.end()
        if _u16(blob, s - 2) != len(m.group(0)):
            anomalies["son hors forme"] += 1
            continue
        d, cle = _chaine_avant(blob, s - 2)
        k = struct.unpack_from("<I", blob, e)[0] if e + 4 <= len(blob) else 0
        pts = [tuple(_f(blob, e + 4 + 12 * i, 3)) for i in range(min(k, 64))] if 0 < k < 10000 else []
        if not cle or not pts:
            anomalies["son hors forme"] += 1
            continue
        out.append(("son", cle, pts[0], {"forme": m.group(0).decode(), "points": len(pts), "version": _u16(blob, d - 4)}))
    for m in RX_EFFET.finditer(blob):
        n, deb = m.group(1)[0], m.end()
        nom = blob[deb:deb + n]
        if len(nom) != n or not all(0x20 <= c <= 0x7e for c in nom):
            continue
        nom = nom.decode("ascii")
        if not NOM_EFFET.match(nom) or ("campaign" not in nom and not nom.startswith("vfx")):
            continue
        v = _f(blob, deb + n, 12)
        if not v or not all(abs(x) < 1e4 for x in v):
            anomalies["effet hors forme"] += 1
            continue
        out.append(("effet", nom, tuple(v[9:12]), {"matrice": v[:9]}))
    for m in RX_SCENE.finditer(blob):
        s = m.start()
        if _u16(blob, s - 2) != len(m.group(0)) or _u16(blob, s - 52) != 3:
            anomalies["scène hors forme"] += 1
            continue
        v = _f(blob, s - 50, 12)
        out.append(("scène", m.group(0).decode().lower(), tuple(v[9:12]), {"matrice": v[:9]}))
    for m in RX_OBJET_VFX.finditer(blob):
        n = m.group(1)[0] | (m.group(2)[0] << 8)
        if n != len(m.group(3)):
            continue
        v = _f(blob, m.end(), 12)
        out.append(("objet vfx", m.group(3).decode().lower(), tuple(v[9:12]), {"matrice": v[:9]}))
    return out, anomalies


def chaines_cartes_wh3(src):
    """Noms d'effets, clés de sons et scènes composites employés par les cartes de CA de WH3."""
    effets, sons, scenes = Counter(), Counter(), Counter()
    for carte in CARTES_WH3:
        b = src.lire(f"terrain/campaigns/{carte}/global_props.bin")
        if not b:
            continue
        for m in re.finditer(rb"[\x20-\x7e]{5,}", b):
            s = m.group(0).decode("ascii")
            if s.startswith("Sound_"):
                sons[s] += 1
            elif s.lower().startswith("composite_scene/"):
                scenes[s.lower()] += 1
            elif "_campaign_" in s and NOM_EFFET.match(s):
                effets[s] += 1
    return effets, sons, scenes


def entites(a):
    import lire_props_wh1 as LP
    uniques, variantes, regions, anomalies, bruts = {}, defaultdict(set), defaultdict(set), Counter(), Counter()
    for court, region, _, v, blob in LP.lots(LP.GLOBAL_PROPS):
        ents, an = entites_wh1_lot(blob)
        anomalies.update(an)
        for t, nom, pos, extra in ents:
            bruts[t] += 1
            cle = (t, nom, tuple(round(x, 3) for x in pos))
            uniques.setdefault(cle, extra)
            variantes[cle].add("base" if v is None else str(v))
            regions[cle].add(region)
    par_type = Counter(t for t, _, _ in uniques)
    print("Entités de global_props.bin de WH1 hors objets de `rigidmodels/` et `terrain/` :")
    for t in ("lumière", "son", "effet", "scène", "objet vfx"):
        seul_variante = sum(1 for k in uniques if k[0] == t and "base" not in variantes[k])
        print(f"  {t:10s} {bruts[t]:6d} enregistrements, {par_type[t]:6d} uniques "
              f"(dont {seul_variante} seulement dans des lots de variante de culture)")
    if anomalies:
        print("  anomalies de forme (ignorées, à examiner) :", dict(anomalies))

    src = CP.SourcePacks(WH3_DATA)
    fichiers_wh3 = set(src.ou)
    bases = defaultdict(set)
    for c in fichiers_wh3:
        bases[os.path.splitext(c.rsplit("/", 1)[-1])[0]].add(c)
    eff3, sons3, scenes3 = chaines_cartes_wh3(src)
    print("\nNoms employés, et s'ils existent dans WH3 :")
    for t, connu in (("effet", lambda n: n in eff3 or n in bases),
                     ("son", lambda n: n in sons3),
                     ("scène", lambda n: n in fichiers_wh3 or n in scenes3),
                     ("objet vfx", lambda n: n in fichiers_wh3),
                     ("lumière", lambda n: True)):
        noms = Counter(k[1] for k in uniques if k[0] == t)
        if not noms:
            continue
        inconnus = {n: c for n, c in noms.items() if not connu(n)}
        print(f"  {t} : {len(noms)} noms, {sum(noms.values())} exemplaires ; inconnus de WH3 : {len(inconnus)} noms, "
              f"{sum(inconnus.values())} exemplaires")
        for n, c in noms.most_common(a.n):
            print(f"      {c:5d}  {n}{'' if connu(n) else '   <- inconnu de WH3'}")
        if len(noms) > a.n:
            print(f"      ... et {len(noms) - a.n} autres noms (liste complète dans le JSON)")

    print("\nChez nous :")
    balises = Counter()
    for f in glob.glob(os.path.join(PROJET_KIT, "*.layer")):
        balises.update(re.findall(r"<(EC[A-Za-z0-9]+)\b", open(f, encoding="utf-8", errors="replace").read()))
    for c in ("ECPointLight", "ECSpotLight", "ECSoundMarker", "ECVFX", "ECCompositeScene", "ECPropMesh", "ECDecal"):
        print(f"  projet Terry : {balises[c]:7d}  {c}")
    b = CP.extraire(a.pack, f"terrain/campaigns/{CARTE}/global_props.bin")
    if b:
        print(f"  global_props.bin du pack ({os.path.basename(a.pack)}, {len(b)} octets) : "
              f"WPLFT_* {len(re.findall(rb'WPLFT_[A-Z]+', b))}, SST_* {len(re.findall(rb'SST_[A-Z_]+', b))}, "
              f"scènes composites {len(re.findall(rb'composite_scene/', b))}, "
              f"noms d'effets {len(re.findall(rb'_campaign_[a-z_]+', b))}")

    sortie = a.json or os.path.join(JOURNAL, "audit-fidelite-entites-wh1.json")
    liste = [{"type": t, "nom": nom, "position": list(pos), "variantes": sorted(variantes[(t, nom, pos)]),
              "regions": sorted(r for r in regions[(t, nom, pos)] if r), **uniques[(t, nom, pos)]}
             for (t, nom, pos) in sorted(uniques, key=lambda k: (k[0], k[1], k[2]))]
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=0)
    print(f"\n{len(liste)} entités uniques écrites dans {sortie}")


LARGEUR_MONDE = 266.53
HORS_CAMPAGNE = ("/prebattle_screens/",)
# Repère (erreur 89, 22.09.2026, 23 h 20 ; contre-vérifié sur les Empires de CA : z des herbes de 55 à 734 pour une
# profondeur de relief « en pixels carrés » de 648, et 23,9 % à 0,1 du sol en lisant le relief à z × √3/2 contre 2,7 %
# à z tel quel) : dans WH3 comme dans WH1, les entités (objets, décalques, lumières...) et la liste des arbres sont en
# espace hex ; les rasters (Height tif, tile_map, blend...) couvrent la même carte étirée de 2/√3 en z. Une position
# d'entité de WH1 se reprend donc telle quelle, et un raster se lit à la ligne de z × √3/2.
Z_ENTITE_WH1_VERS_NOUS = 1.0
Z_ENTITE_VERS_RASTER = 3 ** 0.5 / 2


def norm_modele(chemin):
    """Chemin de modèle comparable entre WH1 et nous : minuscules, barres obliques, sans le dossier `_wh1/`
    où `fichiers_wh1.py` range la version de WH1 d'un fichier que WH3 a aussi."""
    return chemin.replace("\\", "/").lower().replace("/_wh1/", "/")


def objets_wh1_uniques(facteur_z=Z_ENTITE_WH1_VERS_NOUS):
    """{(modèle normalisé, x, y, z arrondis, matrice arrondie): {"matrice", "position", "variantes", "regions"}} pour
    tous les enregistrements d'objets (et de décalques) de global_props.bin de WH1, lots de variante compris ; z
    multiplié par `facteur_z` (1 : repère des entités de WH3 ; √3/2 : l'ancien repère de la construction)."""
    import lire_props_wh1 as LP
    out = {}
    for court, region, _, v, blob in LP.lots(LP.GLOBAL_PROPS):
        for o in LP.objets(blob):
            x, y, z = o["position"]
            pos = (x, y, z * facteur_z)
            # deux objets de même modèle au même point mais tournés autrement (murs nains, échafaudages) sont deux
            # objets : la matrice fait partie de la clé, comme dans `props_wh1_vers_layers.objets_uniques`
            cle = (norm_modele(o["modele"]), *(round(c, 3) for c in pos), tuple(round(c, 3) for c in o["matrice"]))
            e = out.setdefault(cle, {"matrice": o["matrice"], "position": pos, "position_wh1": (x, y, z),
                                     "variantes": set(), "regions": set(), "modele_wh1": o["modele"]})
            e["variantes"].add("-" if v is None else str(v))
            e["regions"].add(region or "")
    return out


def entites_calques(projet=PROJET_KIT):
    """Entités à modèle des calques écrits : dict(calque, type, modele, position, rotation, echelle, masque)."""
    out = []
    for f in glob.glob(os.path.join(projet, "*.layer")):
        t = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(r"<!-- (\S+) -->", t)
        calque = m.group(1) if m else os.path.basename(f)
        for e in re.findall(r"<entity\b.*?</entity>", t, re.S):
            m = re.search(r'<EC(Mesh|Decal) model_path="([^"]+)"', e)
            tr = re.search(r'<ECTransform position="([^"]+)" rotation="([^"]+)" scale="([^"]+)"', e)
            if not tr:
                continue
            k = re.search(r'culture_mask="([^"]*)"', e)
            poly = "<ECPolygonMesh" in e
            out.append({"calque": calque, "type": "décalque" if m and m.group(1) == "Decal" else
                        ("polygone" if poly else ("objet" if m else "autre")),
                        "modele": norm_modele(m.group(2)) if m else "", "modele_ecrit": m.group(2) if m else "",
                        "position": tuple(float(x) for x in tr.group(1).split()),
                        "rotation": tuple(float(x) for x in tr.group(2).split()),
                        "echelle": tuple(float(x) for x in tr.group(3).split()),
                        "masque": k.group(1) if k else ""})
    return out


def _R(axe, t):
    import numpy as np
    c, s = np.cos(np.radians(t)), np.sin(np.radians(t))
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
            "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axe]


def calibrer_rotation(paires):
    """Convention d'angles de Terry établie sur les données : parmi les 6 ordres x 2 signes x (transposée ou
    non), celle qui recompose le mieux la matrice de WH1 sur les objets inclinés. Rend (convention, écart médian)."""
    import itertools
    import numpy as np
    meilleure = None
    for ordre in itertools.permutations("xyz"):
        for signe in (1, -1):
            for transp in (False, True):
                ecarts = []
                for M, rot, ech in paires:
                    ang = dict(zip("xyz", rot))
                    P = _R(ordre[0], signe * ang[ordre[0]]) @ _R(ordre[1], signe * ang[ordre[1]]) @ \
                        _R(ordre[2], signe * ang[ordre[2]])
                    if transp:
                        P = P.T
                    ecarts.append(float(np.abs(np.diag(ech) @ P - M).max()))
                med = float(np.median(ecarts)) if ecarts else 9.9
                if meilleure is None or med < meilleure[1]:
                    meilleure = (("".join(ordre), signe, transp), med)
    return meilleure


def sol_nous(projet=PROJET_KIT):
    """Fonction (xs, zs) -> hauteur de notre sol écrit (Height tif ; fond de mer là où tile_map dit la mer),
    interpolée, avec la convention de pixels des scripts de l'atelier (pas = L / 266,53, ligne 0 au nord). `zs` est
    un z de RASTER : pour une entité, passer z × Z_ENTITE_VERS_RASTER."""
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    tif = [f for f in os.listdir(projet) if ".height." in f and f.endswith(".tif") and ".sea_" not in f][0]
    sol = np.array(Image.open(os.path.join(projet, tif)), np.float64)
    H, L = sol.shape
    mers = [f for f in os.listdir(projet) if ".sea_height." in f]
    if mers and os.path.exists(os.path.join(projet, "tile_map.png")):
        fond = np.array(Image.open(os.path.join(projet, mers[0])), np.float64)
        tm = np.array(Image.open(os.path.join(projet, "tile_map.png")).convert("RGB"))
        mer = np.all(tm == (83, 141, 213), axis=-1)
        mer = np.repeat(np.repeat(mer, 4, 0), 4, 1)[:H, :L]
        if fond.shape == sol.shape:
            sol = np.where(mer, fond, sol)
    pas = L / LARGEUR_MONDE

    def sous(xs, zs):
        xs, zs = np.asarray(xs, float), np.asarray(zs, float)
        cx = np.clip(xs * pas - 0.5, 0, L - 1.001)
        cy = np.clip((H - 1.5) - zs * pas, 0, H - 1.001)
        c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
        fx, fy = cx - c0, cy - r0
        return (sol[r0, c0] * (1 - fx) * (1 - fy) + sol[r0, c0 + 1] * fx * (1 - fy)
                + sol[r0 + 1, c0] * (1 - fx) * fy + sol[r0 + 1, c0 + 1] * fx * fy)
    return sous, tif


def objets(a):
    import numpy as np
    import lire_props_wh1 as LP
    nous = entites_calques()
    # repère du projet écrit : celui des entités de WH3 (z de WH1 tel quel) ou l'ancien (z × √3/2, erreur 89)
    ici = {(e["modele"], round(e["position"][0], 3), round(e["position"][2], 3)) for e in nous if e["modele"]}
    choix = []
    for f, lib in ((Z_ENTITE_WH1_VERS_NOUS, "z de WH1 tel quel (repère des entités de WH3)"),
                   (Z_ENTITE_VERS_RASTER, "z de WH1 × √3/2 (ancien repère de la construction)")):
        w = objets_wh1_uniques(f)
        n = sum(1 for c in w if (c[0], round(c[1], 3), round(c[3], 3)) in ici)
        choix.append((n, f, lib, w))
        print(f"objets de WH1 retrouvés au même point en plan, {lib} : {n} / {len(w)}")
    _, f_retenu, lib, wh1 = max(choix, key=lambda t: t[0])
    if f_retenu != Z_ENTITE_WH1_VERS_NOUS:
        print("ATTENTION : le projet écrit est dans l'ancien repère ; ses entités s'affichent tassées de 13 % vers le "
              "sud par rapport à WH1 (erreur 89). La suite mesure dans ce repère.")
    print(f"WH1 : {len(wh1)} objets et décalques uniques (modèle + position), lots de variante compris")
    types = Counter((e["type"], e["calque"].startswith("montagnes_wh1")) for e in nous)
    print("Projet Terry écrit :", ", ".join(f"{t}{' (calque montagnes_wh1)' if m else ''} {n}" for (t, m), n in
                                          sorted(types.items())))
    par_modele = defaultdict(list)
    for i, e in enumerate(nous):
        if e["modele"] and not e["calque"].startswith("montagnes_wh1"):
            par_modele[e["modele"]].append(i)
    cles = sorted(wh1)
    trouve, dist = [None] * len(cles), np.full(len(cles), np.inf)
    wh1_par_modele = defaultdict(list)
    for j, c in enumerate(cles):
        wh1_par_modele[c[0]].append(j)
    utilises = np.zeros(len(nous), bool)

    def ecart_matrice(M, e):
        ang = dict(zip("xyz", e["rotation"]))
        P = _R("x", -ang["x"]) @ _R("y", -ang["y"]) @ _R("z", -ang["z"])
        return float(np.abs(np.diag(e["echelle"]) @ P - M).max())

    for mod, js in wh1_par_modele.items():
        idx = par_modele.get(mod)
        if not idx:
            continue
        pn = np.array([nous[i]["position"] for i in idx])
        pw = np.array([wh1[cles[j]]["position"] for j in js])
        for d0 in range(0, len(js), 2000):
            bloc = pw[d0:d0 + 2000]
            d2 = (bloc[:, None, 0] - pn[None, :, 0]) ** 2 + (bloc[:, None, 2] - pn[None, :, 2]) ** 2
            for r in range(len(bloc)):
                j = js[d0 + r]
                proches = np.flatnonzero(d2[r] < 1e-6)
                if len(proches) > 1:
                    # plusieurs des nôtres au même point : celui dont la matrice recompose le mieux celle de WH1,
                    # en préférant un objet pas encore apparié
                    M = np.array(wh1[cles[j]]["matrice"], float).reshape(3, 3)
                    kk = min(proches, key=lambda p: (utilises[idx[p]], ecart_matrice(M, nous[idx[p]])))
                else:
                    kk = int(np.argmin(d2[r]))
                trouve[j], dist[j] = idx[kk], float(np.sqrt(d2[r, kk]))
                if dist[j] < 0.05:
                    utilises[idx[kk]] = True
    exclus = [j for j, c in enumerate(cles) if any(h in c[0] for h in HORS_CAMPAGNE)]
    eau = [j for j, c in enumerate(cles) if "water_plane" in c[0]]
    speciaux = set(exclus) | set(eau)
    normaux = [j for j in range(len(cles)) if j not in speciaux]
    d = dist[normaux]
    print(f"\nPrésence, en plan (même modèle, distance horizontale au plus proche des nôtres) sur {len(normaux)} "
          f"objets de WH1 (hors {len(exclus)} de pré-bataille écartés exprès et {len(eau)} plans d'eau) :")
    for lim, lib in ((1e-3, "< 0,001 (recopié)"), (0.05, "< 0,05"), (0.5, "< 0,5"), (np.inf, "plus loin")):
        print(f"  {lib:20s} {int(np.sum(d < lim)) if lim != np.inf else int(np.sum(np.isfinite(d) & (d >= 0.5))):7d}")
    absents = [j for j in normaux if not np.isfinite(dist[j]) or dist[j] >= 0.05]
    print(f"  absents (aucun des nôtres à moins de 0,05 avec ce modèle) : {len(absents)}")
    cpt = Counter(cles[j][0] for j in absents)
    for mod, n in cpt.most_common(a.n):
        exemple = next(j for j in absents if cles[j][0] == mod)
        dd = dist[exemple]
        print(f"      {n:5d}  {mod}   (plus proche des nôtres : {'aucun de ce modèle' if not np.isfinite(dd) else f'{dd:.3f}'})")
    en_trop = [i for i, e in enumerate(nous) if e["type"] in ("objet", "décalque") and not e["calque"].startswith(
        "montagnes_wh1") and not utilises[i]]
    print(f"  des nôtres sans objet de WH1 à moins de 0,05 : {len(en_trop)}")
    for mod, n in Counter(nous[i]["modele"] for i in en_trop).most_common(10):
        print(f"      {n:5d}  {mod}")

    apparies = [j for j in normaux if np.isfinite(dist[j]) and dist[j] < 0.05]
    dy = np.array([nous[trouve[j]]["position"][1] - wh1[cles[j]]["position"][1] for j in apparies])
    print(f"\nHauteur (notre y moins celui de WH1) sur {len(apparies)} objets appariés : "
          f"= 0 à 0,001 près : {int(np.sum(np.abs(dy) < 1e-3))} ; |dy| > 0,05 : {int(np.sum(np.abs(dy) > 0.05))} ; "
          f"> 0,2 : {int(np.sum(np.abs(dy) > 0.2))} ; > 1 : {int(np.sum(np.abs(dy) > 1))}")
    print(f"  montés : {int(np.sum(dy > 0.05))} ; descendus : {int(np.sum(dy < -0.05))} ; "
          f"quantiles 1 / 50 / 99 % : {np.percentile(dy, [1, 50, 99]).round(3).tolist()}")
    grands = Counter()
    for j, v in zip(apparies, dy):
        if abs(v) > 0.2:
            grands[cles[j][0]] += 1
    print("  modèles les plus déplacés en hauteur (> 0,2) :")
    for mod, n in grands.most_common(12):
        vals = [v for j, v in zip(apparies, dy) if cles[j][0] == mod and abs(v) > 0.2]
        print(f"      {n:5d}  {mod}   médiane {np.median(vals):+.2f}")

    # où sont les objets déplacés en hauteur : famille de la tuile de WH1 sous l'objet (tile_list.bin de WH1), et,
    # pour la végétation (pivot au pied), écart entre la hauteur de WH1 et notre sol écrit : là où il n'est pas nul,
    # notre relief n'est pas celui sur lequel WH1 avait posé ses objets
    import tuiles_wh1 as TW
    fam = TW.familles_par_case()
    Hc, Lc = fam.shape
    pas_case = Lc / LARGEUR_MONDE
    sous, tif = sol_nous()

    def famille_en(x, z):
        c = int(np.clip(x * pas_case, 0, Lc - 1))
        r = int(np.clip((Hc - 1) - z * pas_case, 0, Hc - 1))
        return fam[r, c] or "sol ordinaire (maillages)"
    par_fam, veg_fam = defaultdict(list), defaultdict(list)
    for j, v in zip(apparies, dy):
        x, y, z1 = wh1[cles[j]]["position_wh1"]
        zr = z1 * Z_ENTITE_VERS_RASTER                  # ligne de raster de l'endroit de WH1
        f = famille_en(x, zr)
        par_fam[f].append(v)
        if "/vegetation/" in cles[j][0]:
            veg_fam[f].append(y - float(sous(x, zr)))
    print(f"\nPar famille de tuile de WH1 sous l'objet, à son endroit de WH1 (sol écrit : {tif}) :")
    print(f"  {'famille':28s} {'objets':>7s} {'déplacés':>9s} {'%':>6s} {'méd. dépl.':>10s} | végétation : "
          f"{'n':>5s} {'méd. yWH1-sol':>13s} {'|.|>0,1':>8s}")
    for f, vs in sorted(par_fam.items(), key=lambda t: -len(t[1])):
        vs = np.array(vs)
        dep = vs[np.abs(vs) > 0.05]
        vg = np.array(veg_fam.get(f, []))
        print(f"  {f:28s} {len(vs):7d} {len(dep):9d} {100 * len(dep) / len(vs):6.1f} "
              f"{(np.median(dep) if len(dep) else 0):+10.2f} |              "
              f"{len(vg):5d} {(np.median(vg) if len(vg) else 0):+13.3f} {(np.mean(np.abs(vg) > 0.1) * 100 if len(vg) else 0):7.1f}%")

    # rotation et échelle
    paires, err_ech = [], []
    for j in apparies:
        M = np.array(wh1[cles[j]]["matrice"], float).reshape(3, 3)
        e = nous[trouve[j]]
        ech_wh1 = np.linalg.norm(M, axis=1)
        err_ech.append(float(np.abs(ech_wh1 - np.array(e["echelle"])).max()))
        _, _, inclin = LP.decompose(wh1[cles[j]]["matrice"])
        if inclin > 1 and len(paires) < 3000:
            paires.append((M, e["rotation"], np.array(e["echelle"])))
    err_ech = np.array(err_ech)
    print(f"\nÉchelle : écart max {err_ech.max():.4f} ; > 0,01 : {int(np.sum(err_ech > 0.01))}")
    conv, med = calibrer_rotation(paires)
    print(f"Rotation : convention qui recompose le mieux les {len(paires)} objets inclinés : ordre {conv[0]}, signe "
          f"{conv[1]:+d}, transposée {conv[2]} ; écart médian {med:.5f}")
    ordre, signe, transp = conv
    mauvais = []
    for j in apparies:
        M = np.array(wh1[cles[j]]["matrice"], float).reshape(3, 3)
        e = nous[trouve[j]]
        ang = dict(zip("xyz", e["rotation"]))
        P = _R(ordre[0], signe * ang[ordre[0]]) @ _R(ordre[1], signe * ang[ordre[1]]) @ _R(ordre[2], signe * ang[ordre[2]])
        P = P.T if transp else P
        err = float(np.abs(np.diag(e["echelle"]) @ P - M).max())
        if err > 0.01:
            mauvais.append((err, cles[j][0]))
    print(f"  objets dont la matrice recomposée s'écarte de plus de 0,01 : {len(mauvais)}")
    for mod, n in Counter(m for _, m in mauvais).most_common(8):
        print(f"      {n:5d}  {mod}")

    # focus demandé : pivot de WH1 face à notre sol écrit
    if a.focus:
        print(f"\nFocus « {a.focus} » (sol : {tif} ; « sol WH1 » = notre sol à l'endroit de WH1, « sol affiché » = "
              f"sous notre entité telle que WH3 la place) :")
        print(f"  {'modèle':38s} {'x':>8s} {'z WH1':>8s} {'y WH1':>7s} {'y nous':>7s} {'sol WH1':>8s} {'sol aff.':>8s} "
              f"{'dh plan':>8s} variantes / régions")
        for j in [j for j in range(len(cles)) if a.focus in cles[j][0]]:
            w = wh1[cles[j]]
            x, y, z1 = w["position_wh1"]
            e = nous[trouve[j]] if trouve[j] is not None else None
            yn = e["position"][1] if e else float("nan")
            s_aff = float(sous(e["position"][0], e["position"][2] * Z_ENTITE_VERS_RASTER)) if e else float("nan")
            print(f"  {cles[j][0].split('/')[-1]:38s} {x:8.3f} {z1:8.3f} {y:7.3f} {yn:7.3f} "
                  f"{float(sous(x, z1 * Z_ENTITE_VERS_RASTER)):8.3f} {s_aff:8.3f} {dist[j]:8.4f} "
                  f"{','.join(sorted(w['variantes']))} {','.join(sorted(w['regions']))[:40]}")
    sortie = os.path.join(JOURNAL, "audit-fidelite-objets.json")
    json.dump({"absents": [{"modele": cles[j][0], "position": wh1[cles[j]]["position"],
                            "plus_proche": None if not np.isfinite(dist[j]) else float(dist[j]),
                            "variantes": sorted(wh1[cles[j]]["variantes"]), "regions": sorted(wh1[cles[j]]["regions"])}
                           for j in absents],
               "en_trop": [{k: nous[i][k] for k in ("calque", "modele_ecrit", "position", "masque")} for i in en_trop],
               "hauteur": [{"modele": cles[j][0], "position_wh1": wh1[cles[j]]["position"],
                            "y_nous": nous[trouve[j]]["position"][1], "dy": float(v)}
                           for j, v in zip(apparies, dy) if abs(v) > 0.05]},
              open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"\nDétail écrit dans {sortie}")


LISTE_ARBRES = f"campaign_maps/{CARTE}/display/trees/trees.campaign_tree_list"


def lire_liste_arbres(octets):
    """(en-tête de 20 octets, [(identifiant, enregistrements (n, 15) octets)]) d'une trees.campaign_tree_list v4 :
    u32 4 | 16 octets (bornes) | u32 n | n x (u16 + nom, u32 k, k x 15 octets : x, hauteur, z en f32 + 3 octets)."""
    if struct.unpack_from("<I", octets, 0)[0] != 4:
        raise ValueError("version 4 attendue")
    n = struct.unpack_from("<I", octets, 20)[0]
    o, out = 24, []
    for _ in range(n):
        ln = struct.unpack_from("<H", octets, o)[0]
        nom = octets[o + 2:o + 2 + ln].decode("ascii")
        o += 2 + ln
        k = struct.unpack_from("<I", octets, o)[0]
        o += 4
        out.append((nom, [octets[o + 15 * i:o + 15 * (i + 1)] for i in range(k)]))
        o += 15 * k
    if o != len(octets):
        raise ValueError("fin de fichier inattendue")
    return octets[:20], out


def octets_table(pack, table):
    """Octets bout à bout des fichiers d'une table de base de données du pack."""
    out = b""
    for c, t, off, comp in CP.index(pack):
        n = c.replace("\\", "/").lower()
        if n.startswith(f"db/{table}/"):
            with open(pack, "rb") as f:
                f.seek(off)
                b = f.read(t)
            out += CP.decompresser(b) if comp else b
    return out


def dans_table(octets, texte):
    """La table contient-elle ce texte comme champ entier (u16 longueur + octets, sans schéma) ?"""
    t = texte.encode("utf-8")
    return struct.pack("<H", len(t)) + t in octets


def chaines_table(pack, table):
    """Chaînes ASCII des fichiers d'une table (u16 longueur + octets), pour y chercher des chemins."""
    b = octets_table(pack, table)
    out, o = set(), 0
    for m in re.finditer(rb"[\x20-\x7e]{4,}", b):
        s = m.start()
        n = struct.unpack_from("<H", b, s - 2)[0] if s >= 2 else -1
        out.add(m.group(0)[:n].decode("ascii") if 0 < n <= len(m.group(0)) else m.group(0).decode("ascii"))
    return out


def arbres(a):
    src1 = CP.SourcePacks(WH1_DATA, exclure=())
    b1 = src1.lire(LISTE_ARBRES)
    b3 = CP.extraire(a.pack, LISTE_ARBRES)
    if not b1 or not b3:
        print("liste introuvable :", "WH1" if not b1 else "pack")
        return
    t1, g1 = lire_liste_arbres(b1)
    t3, g3 = lire_liste_arbres(b3)
    print(f"en-têtes : WH1 {struct.unpack_from('<I4f', t1)} ; pack {struct.unpack_from('<I4f', t3)} ; "
          f"identiques : {t1 == t3}")
    n1, n3 = sum(len(r) for _, r in g1), sum(len(r) for _, r in g3)
    print(f"arbres : WH1 {n1} en {len(g1)} identifiants ; pack {n3} en {len(g3)} identifiants")
    # mêmes enregistrements, au même identifiant (préfixe du pack retiré) ?
    pref = os.path.commonprefix([n for n, _ in g3]) if g3 else ""
    c1 = Counter((n, r) for n, rs in g1 for r in rs)
    c3 = Counter((n[len("wh1_"):] if n.startswith("wh1_") else n, r) for n, rs in g3 for r in rs)
    commun = sum((c1 & c3).values())
    print(f"enregistrements identiques octet pour octet, même identifiant (préfixe « wh1_ » retiré) : {commun} / {n1}")
    r1 = Counter(r for _, rs in g1 for r in rs)
    r3 = Counter(r for _, rs in g3 for r in rs)
    print(f"mêmes enregistrements, identifiant ignoré : {sum((r1 & r3).values())} / {n1} ; "
          f"du pack absents de WH1 : {sum((r3 - r1).values())}")
    ids3 = sorted({n for n, _ in g3})
    print(f"identifiants du pack : {', '.join(ids3[:8])}{' ...' if len(ids3) > 8 else ''} (préfixe commun « {pref} »)")
    # déclarés dans les tables du pack ? (champ entier : u16 longueur + texte)
    oids = octets_table(a.pack, "campaign_tree_ids_tables")
    ovar = octets_table(a.pack, "campaign_tree_variants_tables")
    tvar = chaines_table(a.pack, "campaign_tree_variants_tables")
    manque_ids = [n for n in ids3 if not dans_table(oids, n)]
    manque_var = [n for n in ids3 if not dans_table(ovar, n)]
    # hauteurs : les enregistrements qui diffèrent de WH1 à même x / z
    par_xz = {r[0:4] + r[8:12]: r for _, rs in g1 for r in rs}
    dh = [struct.unpack_from("<f", r, 4)[0] - struct.unpack_from("<f", par_xz[r[0:4] + r[8:12]], 4)[0]
          for _, rs in g3 for r in rs if (r[0:4] + r[8:12]) in par_xz and par_xz[r[0:4] + r[8:12]] != r]
    if dh:
        print(f"enregistrements au même x / z que WH1 mais différents : {len(dh)} ; écart de hauteur min {min(dh):+.3f}, "
              f"max {max(dh):+.3f}")
    print(f"identifiants absents de campaign_tree_ids du pack : {len(manque_ids)} {manque_ids[:6]} ; "
          f"absents de campaign_tree_variants : {len(manque_var)} {manque_var[:6]}")
    modeles = sorted(s for s in tvar if s.lower().endswith((".wsmodel", ".rigid_model_v2", ".variantmeshdefinition")))
    src3 = CP.SourcePacks(WH3_DATA)
    notre = {c.replace("\\", "/").lower() for c, _ in CP.entrees(a.pack)}
    absents = [m for m in modeles if m.replace("\\", "/").lower() not in notre and m not in src3]
    print(f"modèles cités par campaign_tree_variants du pack : {len(modeles)} ; introuvables (pack et jeu) : "
          f"{len(absents)} {absents[:8]}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("inventaire")
    p.add_argument("--filtre", default="wh_dlc05_wood_elves")
    p.add_argument("--tout", action="store_true")
    p = sp.add_parser("structure")
    p.add_argument("--carte", default="wh3_main_prologue_map")
    p.add_argument("--n", type=int, default=15)
    p = sp.add_parser("entites")
    p.add_argument("--pack", default=CP.PACK)
    p.add_argument("--json", default="")
    p.add_argument("--n", type=int, default=25)
    p = sp.add_parser("objets")
    p.add_argument("--n", type=int, default=25)
    p.add_argument("--focus", default="waystone")
    p = sp.add_parser("arbres")
    p.add_argument("--pack", default=CP.PACK)
    a = ap.parse_args()
    {"inventaire": inventaire, "structure": structure, "entites": entites, "objets": objets, "arbres": arbres}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
