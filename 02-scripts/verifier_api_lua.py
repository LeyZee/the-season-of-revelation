"""
verifier_api_lua.py - chaque nom de fonction appelé par nos scripts de campagne existe-t-il dans Warhammer 3 ?

Complète `verifier_lua.py` (syntaxe) : un nom mal écrit ou absent de WH3 ne se voit qu'en partie, par une erreur de
script qui coupe l'écouteur (l'histoire s'arrête sans plantage). Un nom appelé est accepté s'il est défini :
  - par un script Lua de CA (packs du jeu, `script/**.lua`, lus en lecture seule par `contenu_pack.SourcePacks`) ;
  - par nos propres scripts (fonction, alias local `local x = y`) ;
  - ou s'il figure comme chaîne dans l'exécutable (interface du jeu : `cm:make_region_seen_in_shroud`, `faction:treasury`).
Ce contrôle ne vérifie pas les arguments. Aucun pack du projet n'est ouvert.

Usage : python verifier_api_lua.py [dossier_scripts]   (défaut : scripts-campagne\\script du projet)
Code de sortie 1 si un nom est introuvable.
23.09.2026 (session d'audit).
"""
import glob
import os
import pickle
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contenu_pack as CP                                            # noqa: E402

JEU = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III"
DATA = JEU + "/data"
EXE = JEU + "/Warhammer3.exe"
NOS = r"C:\TotalWar-CampaignMap\04-projets\saison-des-revelations\scripts-campagne\script"
CACHE = os.path.join(tempfile.gettempdir(), "verifier_api_lua_ca.pkl")

LUA = {"print", "type", "tostring", "tonumber", "pairs", "ipairs", "pcall", "xpcall", "error", "require", "select",
       "unpack", "next", "setmetatable", "getmetatable", "rawget", "rawset", "assert", "loadstring", "dofile",
       "if", "while", "return", "and", "or", "not", "elseif", "until", "function", "local"}


def scripts_ca():
    """Textes des scripts Lua de CA, mis en cache (clé : taille et date des packs du jeu)."""
    signature = sorted((os.path.basename(p), os.path.getsize(p), int(os.path.getmtime(p)))
                       for p in glob.glob(os.path.join(DATA, "*.pack")) if not os.path.basename(p).startswith("!")
                       and "saison" not in p and "zz_" not in p)
    if os.path.exists(CACHE):
        sig, textes = pickle.load(open(CACHE, "rb"))
        if sig == signature:
            return textes
    src = CP.SourcePacks(DATA)
    textes = {p: src.lire(p).decode("utf-8", "replace") for p in src.ou
              if p.lower().startswith("script/") and p.lower().endswith(".lua")}
    pickle.dump((signature, textes), open(CACHE, "wb"))
    return textes


def sans_commentaires_ni_chaines(t):
    t = re.sub(r"--\[(=*)\[.*?\]\1\]", " ", t, flags=re.S)
    t = re.sub(r"\[(=*)\[.*?\]\1\]", '""', t, flags=re.S)
    sortie, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == "-" and t.startswith("--", i):
            j = t.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "\"'":
            j = i + 1
            while j < n and t[j] != c and t[j] != "\n":
                j += 2 if t[j] == "\\" else 1
            sortie.append('""')
            i = j + 1
            continue
        sortie.append(c)
        i += 1
    return "".join(sortie)


def definitions(t):
    d = set(re.findall(r"function\s+[\w\.]+[:\.](\w+)\s*\(", t))
    d |= set(re.findall(r"function\s+(\w+)\s*\(", t))
    d |= set(re.findall(r"(\w+)\s*=\s*function\s*\(", t))
    d |= set(re.findall(r"local\s+(\w+)\s*=\s*[\w\.:]+\s*[;\n]", t))  # alias local
    return d


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dossier = sys.argv[1] if len(sys.argv) > 1 else NOS
    ca = scripts_ca()
    connus = set(LUA)
    for t in ca.values():
        connus |= definitions(sans_commentaires_ni_chaines(t))
    nos = {p: sans_commentaires_ni_chaines(open(p, encoding="utf-8").read())
           for p in glob.glob(os.path.join(dossier, "**", "*.lua"), recursive=True)}
    for t in nos.values():
        connus |= definitions(t)
    exe = open(EXE, "rb").read()
    manque = {}
    for p, t in nos.items():
        appels = set(re.findall(r"[:\.](\w+)\s*\(", t)) | set(re.findall(r"(?<![\w\.:])(\w+)\s*\(", t))
        for nom in appels:
            if nom in connus or (b"\0" + nom.encode() + b"\0") in exe:
                continue
            manque.setdefault(nom, set()).add(os.path.relpath(p, dossier))
    print(f"{len(ca)} scripts de CA, {len(nos)} scripts à nous")
    if not manque:
        print("OK : tous les noms appelés existent (CA, nos scripts ou interface du jeu).")
        return 0
    print("Noms introuvables :")
    for nom, ou in sorted(manque.items()):
        print(f"  {nom:45s} {', '.join(sorted(ou))}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
