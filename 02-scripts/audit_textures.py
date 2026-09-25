#!/usr/bin/env python3
"""
audit_textures.py - chaque texture citée par chaque modèle posé sur la carte (calques du projet et liste des arbres de
WH1 : essences du kit), classée selon ce que le JEU lira à ce chemin (23.09.2026 ; captures de Charles : arbres gris,
lisières noires, cristaux de glace roses).

Le jeu lit un chemin dans nos packs d'abord, puis dans ceux de WH3. Nos fichiers de WH1 ne remplacent jamais un chemin de
WH3 (`fichiers_wh1` : « _wh1/ » quand WH3 a un autre fichier) : si un modèle cite encore le chemin d'origine alors que
WH3 y a un AUTRE fichier, le jeu applique la texture de WH3 (autre atlas, autres couleurs) au modèle de WH1.

Classes : « nous » (seulement dans nos fichiers), « WH3 identique », « WH3 AUTRE » (le défaut cherché), « absente »
(ni chez nous ni dans WH3 : texture factice de WH1, `test_*`, sans effet ou gris selon le type).

Usage :
    python audit_textures.py            # bilan par classe, par type de texture, et les modèles touchés
"""

import collections
import glob
import hashlib
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_wh1_vers_layers as PL                                  # noqa: E402
from contenu_pack import SourcePacks, chemins_du_jeu                 # noqa: E402

PROJET = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain\campaigns\wh_dlc05_wood_elves_map_1"
DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
# dossiers embarqués dans le pack (build_pack.py) : ce que le jeu trouve chez nous
NOS_DOSSIERS = [os.path.join(r"C:\TotalWar-CampaignMap\04-projets\saison-des-revelations", d)
                for d in ("fichiers-wh1", "montagnes-wh1", "rivieres-wh1", "affichage-carte", "eclairage-wh1")]


def textures_du_modele(b):
    """[(lod, morceau, matériau, type, chemin)] des textures citées par un RMV2 (v6 à v8)."""
    ver, nlod = struct.unpack_from("<II", b, 4)
    pas_lod = 28 if ver in (6, 7) else 20
    out = []
    for k in range(nlod):
        nb = struct.unpack_from("<I", b, 140 + pas_lod * k)[0]
        off = struct.unpack_from("<I", b, 140 + pas_lod * k + 12)[0]
        for m in range(nb):
            if off + 24 > len(b):
                break
            mat, _u, taille, voff, _vc, _ioff, _ic = struct.unpack_from("<HHIIIII", b, off)
            tete = b[off:off + min(voff, len(b) - off)]
            for t in re.finditer(rb"[a-z0-9_/\\.\-]{6,}\.dds", tete, re.I):
                typ = struct.unpack_from("<I", tete, t.start() - 4)[0] if t.start() >= 4 else None
                out.append((k, m, mat, typ, t.group().decode().replace("\\", "/").lower()))
            if taille == 0:
                break
            off += taille
    return out


SUFFIXES_WH1 = ("_diffuse", "_specular", "_gloss_map", "_normal", "_mask")


def textures_detournees(dossiers, jeu=None):
    """{base de jeu de textures : modèles} des jeux de textures de WH1 que le moteur de WH3 remplacerait par ceux de CA :
    un modèle cite X_diffuse (X_specular...) hors de `_wh1/` alors que WH3 a X_base_colour ou X_material_map à la même
    base (erreur 100 : cristaux de glace roses). Doit être vide ; garde de `build_pack.py`."""
    jeu = jeu if jeu is not None else chemins_du_jeu(PL.DATA_WH3)
    bases = collections.defaultdict(set)
    for dossier in dossiers:
        for racine, _, noms in os.walk(dossier):
            for n in noms:
                if not n.endswith(".rigid_model_v2"):
                    continue
                b = open(os.path.join(racine, n), "rb").read()
                if b[:4] != b"RMV2":
                    continue
                for _lod, _m, _mat, _typ, tex in textures_du_modele(b):
                    if "/_wh1/" in tex or tex.startswith("rigidmodels/_wh1/"):
                        continue
                    for s in SUFFIXES_WH1:
                        if tex.endswith(s + ".dds"):
                            bases[tex[:-len(s + ".dds")]].add(n)
    return {b: sorted(m) for b, m in bases.items()
            if (b + "_base_colour.dds") in jeu or (b + "_material_map.dds") in jeu}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    jeu = chemins_du_jeu(PL.DATA_WH3)
    src = SourcePacks(PL.DATA_WH3)

    def chez_nous(c):
        for d in NOS_DOSSIERS:
            p = os.path.join(d, *c.split("/"))
            if os.path.exists(p):
                return p
        return None

    def lire(c):
        p = chez_nous(c)
        if p:
            return open(p, "rb").read()
        return src.lire(c) if c in jeu else None

    # modèles employés : calques du projet (ECMesh) et essences de la liste des arbres (tree_rigid du kit)
    modeles = collections.Counter()
    for f in glob.glob(os.path.join(PROJET, "*.layer")):
        for m in re.finditer(r'<ECMesh model_path="([^"]+)"', open(f, encoding="utf-8").read()):
            modeles[m.group(1).replace("\\", "/").lower()] += 1
    t = open(os.path.join(DB, "campaign_tree_variants.xml"), encoding="utf-8").read()
    for m in re.finditer(r"<tree_id>(wh1_[^<]+)</tree_id>.*?<tree_rigid>([^<]+)</tree_rigid>", t, re.S):
        modeles[m.group(2).replace("\\", "/").lower()] += 1
    classes = collections.Counter()
    par_type = collections.defaultdict(collections.Counter)
    touches = collections.defaultdict(set)
    absentes = collections.defaultdict(set)
    empreinte = {}

    def classe(c):
        if c not in empreinte:
            nous = chez_nous(c)
            if nous and c in jeu:
                a = hashlib.sha1(open(nous, "rb").read()).hexdigest()
                b = hashlib.sha1(src.lire(c) or b"").hexdigest()
                empreinte[c] = "WH3 identique" if a == b else "WH3 AUTRE (chez nous aussi)"
            elif nous:
                empreinte[c] = "nous"
            elif c in jeu:
                empreinte[c] = "WH3 seulement"
            else:
                empreinte[c] = "absente"
        return empreinte[c]

    geometries = {}
    for c, n in modeles.items():
        b = lire(c)
        if b and c.endswith(".wsmodel"):
            g = re.search(rb"<geometry>([^<]+)</geometry>", b)
            c = g.group(1).decode().replace("\\", "/").lower() if g else c
            b = lire(c) if g else None
        if not b or b[:4] != b"RMV2" or c in geometries:
            continue
        geometries[c] = n
        for lod, morceau, mat, typ, tex in textures_du_modele(b):
            k = classe(tex)
            classes[k] += 1
            par_type[typ][k] += 1
            if k in ("WH3 seulement", "WH3 AUTRE (chez nous aussi)") and not tex.startswith("rigidmodels/_wh1/"):
                touches[(k, typ, tex)].add(c.rsplit("/", 1)[-1])
            if k == "absente":
                absentes[(typ, tex)].add((c.rsplit("/", 1)[-1], mat))
    print(f"{len(geometries)} géométries employées ; références de textures par classe : {dict(classes)}")
    print("par type de texture (0 diffuse WH1, 27 couleur de base WH3, 1 normale, 11 spéculaire, 12 brillance, 3 masque) :")
    for typ, c in sorted(par_type.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"   type {typ} : {dict(c)}")
    print("textures lues dans WH3 par nos modèles de WH1 (les plus citées) :")
    for (k, typ, tex), mods in sorted(touches.items(), key=lambda kv: -len(kv[1]))[:40]:
        print(f"   [{k}] type {typ} {tex}  <- {len(mods)} modèles, ex. {sorted(mods)[:3]}")
    # textures introuvables (ni chez nous ni dans WH3) : de couleur (types 0 et 27), un modèle sort sans couleur
    print("textures de couleur introuvables (types 0 et 27) :")
    for (typ, tex), mods in sorted(absentes.items(), key=lambda kv: (-len(kv[1]), kv[0][1])):
        if typ in (0, 27):
            print(f"   type {typ} {tex}  <- {len(mods)} (modèle, matériau), ex. {sorted(mods)[:4]}")
    autres = collections.Counter(tex.rsplit("/", 1)[-1].split("_")[0] for (typ, tex) in absentes if typ not in (0, 27))
    print(f"autres textures introuvables (normales, spéculaires, masques) : {len([1 for t, _ in absentes if t not in (0, 27)])} ;"
          f" préfixes les plus fréquents : {autres.most_common(8)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
