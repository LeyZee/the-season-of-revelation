#!/usr/bin/env python3
"""
modeles_wh1.py - rassembler les modèles de campagne de Warhammer 1 (et leurs dépendances) que notre
carte emploie et que Warhammer 3 n'a pas, pour les mettre dans le pack et dans `working_data` du kit.

Décision de Charles (21.09.2026, 22 h 55) : les objets de la carte sont les **vrais objets de WH1**,
extraits de son installation ; le pack contient donc des fichiers de WH1 et **reste strictement
privé** (jamais publié). Faisabilité : WH3 lit encore le format de WH1 (RMV2 version 7 : 41 % d'un
échantillon de ses propres modèles).

Règles :
- un fichier dont le chemin existe dans les packs de WH3 n'est **jamais** repris de WH1 : le pack est
  chargé par toutes les campagnes et remplacerait le fichier de CA partout ;
- un modèle `.rigid_model_v2` entraîne ses textures (chemins `.dds` cités dans le fichier) ; un
  `.wsmodel` (XML) entraîne les fichiers qu'il cite (modèle, matériaux), récursivement ;
- les fichiers sont copiés sous leur chemin de WH1 dans `04-projets\\saison-des-revelations\\
  modeles-wh1\\` (que `build_pack.py` embarque) et dans `<kit>\\working_data\\` (où BOB et Terry les
  trouvent), sans rien écraser.

Usage :
    python modeles_wh1.py            # bilan à blanc des modèles employés par les calques du projet
    python modeles_wh1.py --apply
"""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contenu_pack import chemins_du_jeu, index                     # noqa: E402

DATA_WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\data"
DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
KIT_WD = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\working_data"
PROJET = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain\campaigns\wh_dlc05_wood_elves_map_1"
SORTIE = r"C:\TotalWar-CampaignMap\04-projets\saison-des-revelations\modeles-wh1"
CHAINE = re.compile(rb"[\x20-\x7e]{6,}")


def norme(c):
    return c.replace("\\", "/").lower()


class SourceWH1:
    """Index des packs de WH1 : chemin normalisé -> (pack, décalage, taille). Le dernier pack lu
    l'emporte, comme dans le jeu (ordre alphabétique des packs de CA : patchs et DLC après data)."""

    def __init__(self):
        self.ou = {}
        for nom in sorted(os.listdir(DATA_WH1)):
            if not nom.endswith(".pack") or nom.startswith("!"):
                continue                      # les packs « ! » sont des mods de Charles, pas du jeu
            chemin = os.path.join(DATA_WH1, nom)
            try:
                for c, taille, off, comp in index(chemin):
                    if not comp:
                        self.ou[norme(c)] = (chemin, off, taille)
            except SystemExit:
                continue

    def lire(self, c):
        p = self.ou.get(norme(c))
        if not p:
            return None
        with open(p[0], "rb") as f:
            f.seek(p[1])
            return f.read(p[2])


def dependances(c, octets):
    """Fichiers cités par un modèle ou un .wsmodel (textures, modèles, matériaux)."""
    out = set()
    for s in CHAINE.findall(octets):
        t = s.decode("ascii", "replace").strip()
        for m in re.finditer(r"[\w./\\-]+\.(?:dds|rigid_model_v2|wsmodel|material|xml\.material|xml)", t, re.I):
            chemin = norme(m.group(0))
            if chemin.startswith(("rigidmodels/", "materials/", "shaders/", "textures/", "variantmeshes/")):
                out.add(chemin)
    return out - {norme(c)}


def modeles_des_calques():
    """Chemins des modèles cités par les calques du projet Terry."""
    out = set()
    for f in glob.glob(os.path.join(PROJET, "*.layer")):
        out |= {norme(m) for m in re.findall(r'model_path="([^"]+)"', open(f, encoding="utf-8").read())}
    return out


def rassembler(modeles, jeu=None, source=None):
    """{chemin : octets} des fichiers de WH1 à reprendre (modèles absents de WH3 et leurs dépendances
    absentes de WH3), et la liste des chemins introuvables dans WH1."""
    jeu = jeu or chemins_du_jeu(DATA_WH3)
    source = source or SourceWH1()
    a_faire = [m for m in modeles if m not in jeu]
    vus, fichiers, introuvables = set(), {}, []
    while a_faire:
        c = a_faire.pop()
        if c in vus:
            continue
        vus.add(c)
        octets = source.lire(c)
        if octets is None:
            introuvables.append(c)
            continue
        fichiers[c] = octets
        for d in dependances(c, octets):
            if d not in jeu and d not in vus:
                a_faire.append(d)
    return fichiers, introuvables


FICHIERS_WH1 = r"C:\TotalWar-CampaignMap\04-projets\saison-des-revelations\fichiers-wh1"


def modeles_des_objets_wh1():
    """Chemins de WH1 de tous les modèles des objets de la carte de WH1 (`global_props.bin`)."""
    import lire_props_wh1 as L
    out = set()
    for _, _, _, _, blob in L.lots(L.GLOBAL_PROPS):
        out |= {norme(o["modele"]) for o in L.objets(blob)}
    return out


def rassembler_tout():
    """22.09.2026 (Charles : « tous les objets de WH1, sans équivalences de WH3 ») : les fichiers de WH1
    des objets et des arbres, par `fichiers_wh1.Relocateur` (chemin de WH1, ou `_wh1/` quand WH3 a un
    autre fichier au même chemin). Rend le Relocateur (octets à livrer dans `.octets`)."""
    from fichiers_wh1 import Relocateur
    from arbres_wh1 import ArbresWH1
    r = Relocateur()
    for m in sorted(modeles_des_objets_wh1()):
        r.cible(m)
    # les objets des ponts de WH1 (tuiles `river_crossing`, 23.09.2026, session du rendu : `ponts_wh1`)
    import ponts_wh1
    for m in ponts_wh1.modeles():
        r.cible(m)
    ArbresWH1().lignes(r)
    return r


# LES SUBSTITUTS DE TEXTURE DE CA (23.09.2026, 19 h, session du rendu ; Charles, capture près du Cromlech de Cadai : « des
# problèmes de texture sur les gros pics » ; à 06 h 05 déjà : « les statues n'ont toujours pas l'air d'avoir de
# textures »). Les modèles de WH1 citent des textures d'attente de CA sous leur propre dossier
# (`rigidmodels/campaign/settlements/textures/test_mask.dds` : 260 modèles, 13 185 poses ; `vegetation/textures/
# test_mask.dds` : 130 modèles ; `test_black`, `test_gray`, `test_white`, `flatnormal`, `test_gloss_map`...), absentes
# des deux jeux à ces chemins (brouillon `test_mask.py`) : le moteur met sa texture par défaut (les cornes du Chaos
# `chs_cmp_props_horn*` sortent blanches). WH3 a ces textures d'attente dans `commontextures/` : on les livre aux
# chemins cités (`test_gloss_map`, sans équivalent, prend le gris neutre `test_gray`).
SUBSTITUTS_CA = {"test_mask.dds": "commontextures/test_mask.dds", "test_black.dds": "commontextures/test_black.dds",
                 "test_gray.dds": "commontextures/test_gray.dds", "test_white.dds": "commontextures/test_white.dds",
                 "flatnormal.dds": "commontextures/flatnormal.dds", "test_gloss_map.dds": "commontextures/test_gray.dds"}


def substituts_de_ca():
    """{chemin cité : octets} : les textures d'attente citées par les modèles livrés dans `fichiers-wh1`, absentes de WH1,
    de WH3 et de nos fichiers, remplacées par celles de CA (`SUBSTITUTS_CA`).
    RETIRÉ (25.09.2026, 02 h 30 ; accord de Charles) : ces fichiers, posés au chemin cité, l'étaient aussi pour les modèles de
    CA qui citent les mêmes chemins sans les livrer (277 citations de `vegetation/textures/flatnormal.dds` par 283 arbres de
    CA) : nos textures d'attente changeaient leurs objets dans toutes les campagnes. Elles sont désormais livrées par
    `fichiers_wh1.Relocateur` sous un chemin à nous (`SUBSTITUTS_A_NOUS`), les modèles de WH1 corrigés : plus rien à poser."""
    import fichiers_wh1
    if fichiers_wh1.SUBSTITUTS_A_NOUS:
        return {}
    import re
    from contenu_pack import SourcePacks
    wh1 = SourceWH1()
    wh3 = SourcePacks(DATA_WH3)
    cites = set()
    for root, _, noms in os.walk(FICHIERS_WH1):
        for n in noms:
            if n.endswith(".rigid_model_v2"):
                b = open(os.path.join(root, n), "rb").read()
                cites |= {norme(m.decode("latin-1")) for m in re.findall(rb"[\w/\\.-]{6,}\.dds", b)}
    out = {}
    for c in sorted(cites):
        base = c.rsplit("/", 1)[-1]
        if base not in SUBSTITUTS_CA or wh1.lire(c) is not None or wh3.lire(c) is not None:
            continue
        if os.path.exists(os.path.join(FICHIERS_WH1, *c.split("/"))):
            continue
        octets = wh3.lire(SUBSTITUTS_CA[base])
        if octets is None:
            raise SystemExit(f"{SUBSTITUTS_CA[base]} absent de WH3")
        out[c] = octets
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--substituts", action="store_true",
                    help="seulement les textures d'attente de CA aux chemins cités par nos modèles de WH1")
    ap.add_argument("--ancien", action="store_true",
                    help="ancienne règle du 21.09.2026 (fichier de WH3 quand le chemin existe) vers modeles-wh1")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.substituts:
        from fichiers_wh1 import ecrire
        s = substituts_de_ca()
        print(f"textures d'attente de CA à livrer : {len(s)} ; {sorted(s)[:12]}")
        if a.apply and s:
            ecrire(s, (FICHIERS_WH1, KIT_WD))
            print(f"{len(s)} fichiers écrits dans {FICHIERS_WH1} et working_data")
        return 0
    if not a.ancien:
        from fichiers_wh1 import ecrire
        r = rassembler_tout()
        print(r.bilan())
        if r.introuvables:
            print("introuvables dans WH1 :", sorted(set(r.introuvables))[:20])
        if a.apply:
            ecrire(r.octets, (FICHIERS_WH1, KIT_WD))
            print(f"{len(r.octets)} fichiers écrits dans {FICHIERS_WH1} et working_data")
            s = substituts_de_ca()
            if s:
                ecrire(s, (FICHIERS_WH1, KIT_WD))
                print(f"textures d'attente de CA : {len(s)} fichiers écrits")
        else:
            print("essai à blanc : relancer avec --apply")
        return 0
    modeles = modeles_des_calques()
    jeu = chemins_du_jeu(DATA_WH3)
    fichiers, introuvables = rassembler(modeles, jeu)
    par_ext = {}
    for c, o in fichiers.items():
        e = c.rsplit(".", 1)[-1]
        n, t = par_ext.get(e, (0, 0))
        par_ext[e] = (n + 1, t + len(o))
    print(f"{len(modeles)} modèles cités par les calques ; {sum(1 for m in modeles if m not in jeu)} absents de WH3")
    print("fichiers de WH1 à reprendre :", {e: f"{n} fichiers, {t / 1e6:.1f} Mo" for e, (n, t) in par_ext.items()})
    if introuvables:
        print(f"introuvables dans WH1 ({len(introuvables)}) :", introuvables[:15])
    if not a.apply:
        print("essai à blanc : relancer avec --apply")
        return 0
    ecrits = 0
    for c, o in fichiers.items():
        for racine in (SORTIE, KIT_WD):
            cible = os.path.join(racine, *c.split("/"))
            if os.path.exists(cible):
                continue
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            with open(cible, "wb") as f:
                f.write(o)
            ecrits += 1
    print(f"{ecrits} fichiers écrits (projet et working_data), rien d'écrasé")
    return 0


if __name__ == "__main__":
    sys.exit(main())
