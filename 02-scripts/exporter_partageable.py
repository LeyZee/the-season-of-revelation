#!/usr/bin/env python3
r"""
exporter_partageable.py - prépare une version PARTAGEABLE de l'atelier : notre code, nos textes, notre documentation,
AUCUN fichier de Warhammer I ni de CA.

Pourquoi (25.09.2026, 18 h 50, demande de Charles : « on peut ouvrir » l'atelier aux autres moddeurs). Le pack de la
Saison contient des fichiers convertis de WH1 : il reste privé. Ce qui peut se partager, c'est ce que nous avons écrit.
Les lignes de tables ne sont pas exportées : les lots de `donnees_campagne.py` (exportés) les régénèrent, et les
lignes de WH1 (régions, factions de la carte) sont des données de WH1.

Méthode : LISTE BLANCHE, puis audit de chaque fichier retenu.
- retenus : 02-scripts\*.py et *.ps1 ; nos Lua de campagne (en-tête « La Saison ») ; textes\*.json ; la documentation
  de la racine et le brouillon anglais (05-journal\2026-09-25-ouverture-moddeurs\README-EN-brouillon.md) ;
- « à trancher » (listés, NON copiés) : les Lua sans notre en-tête (scripts de faction repris de WH1 ou de CA) ;
- refusés par l'audit : tout ce qui vient de 03-references, des captures, des db-backups ou d'un dossier `data` ;
  toute extension binaire ou de ressource (modèles, textures, scènes, caméras, packs, vidages...) ; tout fichier de plus
  de 2 Mo ; tout fichier où l'on trouve une donnée sensible (adresse e-mail, jeton, clé d'API).
Garde-fous de la construction (25.09.2026) : ne lit ni n'ouvre jamais un pack (ni celui du jeu, ni zz_startpos_db) ;
travaille depuis les sources de l'atelier ; sortie hors de `data` et hors de 02-scripts. RIEN n'est publié : Charles
décide où et quoi.

Usage :
    python exporter_partageable.py                 # à blanc : ce qui serait copié, à trancher, refusé
    python exporter_partageable.py --apply         # copie dans 05-journal\2026-09-25-ouverture-moddeurs\export-<date>\
    python exporter_partageable.py --apply --sortie D:\partage\saison
"""

import argparse
import glob
import os
import re
import shutil
import sys
from datetime import datetime

from chemins_atelier import ATELIER, JOURNAL, PROJET, SCRIPTS, WH1, WH3

LUA = os.path.join(PROJET, "scripts-campagne")
TEXTES = os.path.join(PROJET, "textes")
DOCS = ["CLAUDE.md", "README.md", "GUIDE.md", "ERREURS-ET-LECONS.md", "AGENTS.md"]
README_EN = os.path.join(JOURNAL, "2026-09-25-ouverture-moddeurs", "README-EN-brouillon.md")
SORTIE_DEFAUT = os.path.join(JOURNAL, "2026-09-25-ouverture-moddeurs")

EXTENSIONS_PERMISES = {".py", ".ps1", ".lua", ".json", ".md"}
DOSSIERS_REFUSES = {"03-references", "captures", "captures-charles", "db-backups", "data", "__pycache__",
                    "startpos-backups", "terrain-backups"}
TAILLE_MAX = 2 * 1024 * 1024
SENSIBLE = [
    ("adresse e-mail", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|fr|net|org|io|dev|agency)\b")),
    ("jeton JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")),
    ("clé d'API", re.compile(r"\b(?:sk|pk|rk)[-_](?:live|test|proj|ant)?[-_]?[A-Za-z0-9]{20,}")),
    ("jeton GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("secret nommé", re.compile(r"(?i)\b(?:api[_-]?key|secret|password|mot[_ ]de[_ ]passe|token)\s*[=:]\s*['\"][^'\"]{8,}")),
]
# un Lua est à nous si son en-tête le dit : notre convention (date de 2026, décision de Charles, nom du projet ou de nos
# clés) ; les scripts de CA ou de WH1 n'ont rien de tout cela
EN_TETE_NOTRE = re.compile(r"2026|Charles|Saison|saison_|\bWH[13]\b", re.I)


def candidats():
    """(source, chemin relatif dans l'export, catégorie) : la liste blanche, avant audit."""
    for p in sorted(glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.join(SCRIPTS, "*.ps1"))):
        yield p, os.path.join("02-scripts", os.path.basename(p)), "script"
    for p in sorted(glob.glob(os.path.join(LUA, "**", "*"), recursive=True)):
        if os.path.isfile(p):
            yield p, os.path.join("scripts-campagne", os.path.relpath(p, LUA)), "lua"
    for p in sorted(glob.glob(os.path.join(TEXTES, "*.json"))):
        yield p, os.path.join("textes", os.path.basename(p)), "textes"
    for nom in DOCS:
        p = os.path.join(ATELIER, nom)
        if os.path.isfile(p):
            yield p, nom, "doc"
    if os.path.isfile(README_EN):
        yield README_EN, "MODDERS-EN-draft.md", "doc"


def auditer(source, categorie):
    """None si le fichier passe ; sinon (décision, raison) avec décision « refusé » ou « à trancher »."""
    parties = {x.lower() for x in os.path.normpath(source).split(os.sep)}
    if parties & DOSSIERS_REFUSES:
        return "refusé", "dossier exclu (" + ", ".join(sorted(parties & DOSSIERS_REFUSES)) + ")"
    for racine in (WH1, WH3):
        if os.path.normcase(source).startswith(os.path.normcase(racine)):
            return "refusé", "fichier d'une installation du jeu"
    ext = os.path.splitext(source)[1].lower()
    if ext not in EXTENSIONS_PERMISES:
        return "refusé", f"extension {ext or '(aucune)'} hors liste blanche (ressource ou binaire)"
    if os.path.getsize(source) > TAILLE_MAX:
        return "refusé", f"plus de {TAILLE_MAX // (1024 * 1024)} Mo"
    texte = open(source, encoding="utf-8", errors="replace").read()
    for nom, motif in SENSIBLE:
        m = motif.search(texte)
        if m:
            ligne = texte.count("\n", 0, m.start()) + 1
            return "refusé", f"donnée sensible possible ({nom}, ligne {ligne})"
    if categorie == "lua" and not EN_TETE_NOTRE.search("\n".join(texte.splitlines()[:40])):
        return "à trancher", "Lua sans notre en-tête (repris de WH1 ou de CA ?)"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--sortie", help="dossier de sortie (par défaut : 05-journal\\2026-09-25-ouverture-moddeurs\\export-<date>)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sortie = os.path.abspath(a.sortie or os.path.join(SORTIE_DEFAUT, "export-" + datetime.now().strftime("%Y%m%d-%H%M")))
    for interdit in (SCRIPTS, WH3, WH1):
        if os.path.normcase(sortie).startswith(os.path.normcase(interdit)):
            raise SystemExit(f"sortie refusée (dans {interdit}) : garde-fou de la construction")
    retenus, a_trancher, refuses = [], [], []
    for source, relatif, categorie in candidats():
        verdict = auditer(source, categorie)
        if verdict is None:
            retenus.append((source, relatif, categorie))
        elif verdict[0] == "à trancher":
            a_trancher.append((relatif, verdict[1]))
        else:
            refuses.append((relatif, verdict[1]))
    par_cat = {}
    for _, _, c in retenus:
        par_cat[c] = par_cat.get(c, 0) + 1
    print(f"retenus : {len(retenus)} {par_cat}")
    print(f"à trancher (non copiés) : {len(a_trancher)}")
    for r, raison in a_trancher:
        print(f"   ? {r} : {raison}")
    print(f"refusés : {len(refuses)}")
    for r, raison in refuses:
        print(f"   x {r} : {raison}")
    if not a.apply:
        print("\nà blanc : rien n'est copié (--apply pour préparer le dossier ; rien n'est publié)")
        return 0
    if os.path.exists(sortie):
        raise SystemExit(f"{sortie} existe déjà : choisir une autre sortie")
    for source, relatif, _ in retenus:
        cible = os.path.join(sortie, relatif)
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        shutil.copy2(source, cible)
    with open(os.path.join(sortie, "MANIFESTE.txt"), "w", encoding="utf-8") as f:
        f.write(f"Export partageable de l'atelier, {datetime.now():%d.%m.%Y %H:%M} (exporter_partageable.py)\n")
        f.write("Aucun fichier de Warhammer I ni de CA. NON PUBLIÉ : décision de Charles.\n\n")
        f.write(f"RETENUS ({len(retenus)})\n")
        f.writelines(f"  {r}\n" for _, r, _ in retenus)
        f.write(f"\nÀ TRANCHER, NON COPIÉS ({len(a_trancher)})\n")
        f.writelines(f"  {r} : {raison}\n" for r, raison in a_trancher)
        f.write(f"\nREFUSÉS ({len(refuses)})\n")
        f.writelines(f"  {r} : {raison}\n" for r, raison in refuses)
    print(f"\nexport préparé : {sortie} (MANIFESTE.txt) ; rien n'est publié")
    return 0


if __name__ == "__main__":
    sys.exit(main())
