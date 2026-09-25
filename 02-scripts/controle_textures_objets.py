#!/usr/bin/env python3
"""
controle_textures_objets.py - chaque objet de la carte a-t-il ses textures ? (contrôle en lecture seule)

Pourquoi (Charles, 23.09.2026, 20 h : « une grosse passe minutieuse pour vérifier que chaque élément a bien une texture ;
c'est très important » ; captures des cornes du Chaos blanches près du Cromlech de Cadai, 18 h). Session du rendu.

Ce qui est contrôlé :
- les modèles cités par les calques du projet Terry (ECMesh, ECDecal) et les modèles des arbres de WH1
  (campaign_tree_variants du kit, identifiants wh1_*) ;
- pour un .wsmodel : ses matériaux (.xml.material), dont les textures REMPLACENT celles écrites dans la géométrie ;
- pour un .rigid_model_v2 : les textures qu'il cite ; pour un décalque de WH1 (qui cite un chemin de BASE, sans
  extension) : base + `_base_colour` (couleur), `_normal` ou `_parallax`, `_material_map` ;
- chaque texture est cherchée dans nos dossiers embarqués par build_pack, puis dans les packs de WH3.
Erreurs (code de sortie 1) : sur un fichier À NOUS (WH1 converti, nos matériaux) : modèle absent, texture absente,
décalque sans couleur, couleur faite seulement de textures d'attente (test_*, flatnormal : l'objet sort gris ou blanc),
texture ou dossier de textures cité sous `terrain/` (textures des tuiles de CA ; 23.09.2026, 21 h).
Informations : références mortes dans des fichiers de CA eux-mêmes (ex. `_specular` que WH3 n'a plus), sans effet.

Usage :
    python controle_textures_objets.py [--projet <dossier Terry>] [--json <sortie>]
"""

import argparse
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contenu_pack import SourcePacks                                          # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
PROJET_SR = os.path.join(ATELIER, "04-projets", "saison-des-revelations")
EMBARQUES = ("fichiers-wh1", "textures-sol-wh1", "montagnes-wh1", "affichage-carte", "rivieres-wh1", "eclairage-wh1",
             "effets-wh1", "videos-wh1", "eau-carte", "seigneurs", "scripts-campagne")
KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
CARTE = "wh_dlc05_wood_elves_map_1"
DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
ATTENTE = re.compile(r"(^|/)(test_[a-z_]+|flatnormal|flat_normal)\.dds$")
COULEUR = re.compile(r"_(diffuse|base_colour)\.dds$")
# Aucun de nos objets ne cite une texture (ou un dossier de textures) sous `terrain/`, où CA range les textures des tuiles
# (23.09.2026, 21 h : plantage de rendu +0x1A3DCFA, piste « b » ; `montagnes_wh1.TEXTURES_OBJET`, `fichiers_wh1.hors_terrain`)
TERRAIN_CITE = re.compile(rb"(?<![\w/\\.-])terrain[/\\][\w/\\.-]*", re.I)


def textures_de_terrain(octets):
    """Textures, chemins de base et dossiers cités sous `terrain/` (un modèle ou un matériau sous `terrain/` n'en est pas)."""
    cites = {norme(m.decode("latin-1")) for m in TERRAIN_CITE.findall(octets)}
    return sorted(c for c in cites if c.endswith((".dds", "/")) or "." not in c.rsplit("/", 1)[-1])


def norme(c):
    return c.replace("\\", "/").lower().strip()


class Index:
    def __init__(self):
        self.nous = {}
        for d in EMBARQUES:
            racine = os.path.join(PROJET_SR, d)
            for root, _, fichiers in os.walk(racine):
                for f in fichiers:
                    p = os.path.join(root, f)
                    self.nous[norme(os.path.relpath(p, racine))] = p
        wd = os.path.join(KIT, "working_data")
        for root, _, fichiers in os.walk(os.path.join(wd, "terrain", "campaigns", CARTE, "models")):
            for f in fichiers:
                p = os.path.join(root, f)
                self.nous.setdefault(norme(os.path.relpath(p, wd)), p)
        self.w3 = SourcePacks(DATA_WH3)

    def ou(self, c):
        c = norme(c)
        return "nous" if c in self.nous else ("WH3" if c in self.w3.ou else None)

    def lire(self, c):
        c = norme(c)
        if c in self.nous:
            return open(self.nous[c], "rb").read()
        return self.w3.lire(c)


def textures_materiaux(idx, c, octets, prof=0):
    """[texture] citées par un .wsmodel ou un matériau (récursif), et [références introuvables]."""
    s = octets.decode("utf-16") if octets[:2] in (b"\xff\xfe", b"\xfe\xff") else octets.decode("utf-8", "replace")
    tex, morts = [], []
    for ref in re.findall(r">\s*([^<>]+\.(?:xml\.material|material|dds))\s*<", s, re.I):
        r_ = norme(ref)
        if r_.endswith(".dds"):
            tex.append(r_)
        elif prof < 3:
            b2 = idx.lire(r_)
            if b2 is None:
                morts.append(r_)
            else:
                t2, m2 = textures_materiaux(idx, r_, b2, prof + 1)
                tex += t2
                morts += m2
    return tex, morts


def examiner(idx, c):
    ou = idx.ou(c)
    octets = idx.lire(c)
    fiche = {"modele": c, "ou": ou, "erreurs": [], "infos": []}
    a_nous = ou == "nous"
    if octets is None:
        fiche["erreurs"].append("modèle absent")
        return fiche
    terrain = textures_de_terrain(octets) if a_nous else []
    if terrain:
        fiche["erreurs"].append(f"cite des textures de terrain (sous terrain/) : {terrain[:3]}")
    if c.endswith(".wsmodel"):
        tex, morts = textures_materiaux(idx, c, octets)
        geo = re.search(r"<geometry>\s*([^<]+?)\s*</geometry>", octets.decode("utf-8", "replace"))
        if geo and idx.ou(geo.group(1)) is None:
            fiche["erreurs"].append(f"géométrie absente : {norme(geo.group(1))}")
        for m in morts:
            (fiche["erreurs"] if a_nous else fiche["infos"]).append(f"matériau absent : {m}")
    else:
        tex = sorted({norme(m.decode("latin-1")) for m in re.findall(rb"[\w/\\.-]{6,}\.dds", octets)})
        if not tex:
            bases = sorted({norme(m.decode("latin-1")) for m in
                            re.findall(rb"(?:rigidmodels|terrain|variantmeshes)[\w/\\.-]{4,}", octets)
                            if not m.lower().endswith((b".rigid_model_v2", b".dds"))})
            if not bases:
                (fiche["erreurs"] if a_nous else fiche["infos"]).append("aucune texture citée")
            for base in bases:
                if not (idx.ou(base + "_base_colour.dds") or idx.ou(base + "_diffuse.dds")):
                    fiche["erreurs"].append(f"décalque sans couleur : {base}")
            return fiche
    couleurs = []
    for t in sorted(set(tex)):
        o = idx.ou(t)
        if o is None:
            (fiche["erreurs"] if a_nous else fiche["infos"]).append(f"texture absente : {t}")
        if a_nous and c.endswith(".wsmodel") and t.startswith("terrain/"):
            fiche["erreurs"].append(f"cite une texture de terrain par un matériau : {t}")
        if COULEUR.search(t) or (ATTENTE.search(t) and not re.search(r"normal|mask|gloss|black", t)):
            couleurs.append(t)
    if couleurs and all(ATTENTE.search(t) for t in couleurs):
        fiche["erreurs"].append(f"couleur faite de textures d'attente seulement : {couleurs}")
    return fiche


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projet", default=os.path.join(KIT, "raw_data", "terrain", "campaigns", CARTE))
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    idx = Index()
    poses = collections.Counter()
    for f in glob.glob(os.path.join(a.projet, "*.layer")):
        t = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<EC(?:Mesh|Decal) model_path="([^"]+)"', t):
            poses[norme(m.group(1))] += 1
    arbres = {}
    t = open(os.path.join(KIT, "raw_data", "db", "campaign_tree_variants.xml"), encoding="utf-8").read()
    for m in re.finditer(r"<tree_id>([^<]*)</tree_id>.*?<tree_rigid>([^<]*)</tree_rigid>", t, re.S):
        if m.group(1).startswith("wh1_"):
            arbres[norme(m.group(2))] = m.group(1)
    fiches = [examiner(idx, c) for c in sorted(set(poses) | set(arbres))]
    erreurs = [f for f in fiches if f["erreurs"]]
    infos = [f for f in fiches if f["infos"] and not f["erreurs"]]
    print(f"projet : {a.projet}")
    print(f"{len(fiches)} modèles ({sum(poses.values())} poses, {len(arbres)} modèles d'arbres de WH1) ; "
          f"avec erreur : {len(erreurs)} ; références mortes dans des fichiers de CA (sans effet) : {len(infos)}")
    for f in sorted(erreurs, key=lambda f: -poses.get(f["modele"], 0)):
        print(f"  ERREUR {poses.get(f['modele'], 0):5d} poses {f['modele']} [{f['ou']}]")
        for e in f["erreurs"][:4]:
            print(f"         - {e}")
    if a.json:
        json.dump({"projet": a.projet, "fiches": fiches}, open(a.json, "w", encoding="utf-8"), ensure_ascii=False,
                  indent=1)
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
