#!/usr/bin/env python3
"""
verifier_lua.py - vérifie la syntaxe des scripts Lua de la campagne avec le Lua 5.1 du kit de WH3, sans rien exécuter.

Pourquoi (23.09.2026) : une erreur de syntaxe dans un fichier que `required.lua` charge fait échouer tout le
chargement des scripts de la campagne ; en jeu, on ne la voit qu'au prochain essai de Charles. Le kit de WH3 livre
une bibliothèque Lua 5.1 (`assembly_kit\\binaries\\lualib.modder.x64.dll`, API C standard exportée) : on compile
chaque fichier avec `luaL_loadbuffer`, qui vérifie la syntaxe sans exécuter le code.

Usage :
    python verifier_lua.py <dossier ou fichier> [...]
Sortie : un fichier par ligne, « ok » ou le message d'erreur de Lua (fichier:ligne: message). Code de retour 1 si
au moins une erreur.
"""

import ctypes
import os
import re
import sys

DLL = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\binaries"
       r"\lualib.modder.x64.dll")


def charger_lua():
    lua = ctypes.CDLL(DLL)
    lua.luaL_newstate.restype = ctypes.c_void_p
    lua.luaL_loadbuffer.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p]
    lua.luaL_loadbuffer.restype = ctypes.c_int
    lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    lua.lua_tolstring.restype = ctypes.c_char_p
    lua.lua_settop.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lua.lua_close.argtypes = [ctypes.c_void_p]
    return lua


def verifier(lua, L, chemin):
    octets = open(chemin, "rb").read()
    nom = ("@" + os.path.basename(chemin)).encode("utf-8")
    r = lua.luaL_loadbuffer(L, octets, len(octets), nom)
    if r == 0:
        lua.lua_settop(L, 0)
        return None
    msg = lua.lua_tolstring(L, -1, None)
    lua.lua_settop(L, 0)
    return (msg or b"?").decode("utf-8", "replace")


# Appels interdits dans le jeu, même syntaxiquement justes (03.10.2026, passe de test des dix seigneurs, constat B-1) :
# string.find(s, motif, init, true), le « texte brut », rend nil à tort dans WH3 9.0.2 et corrompt la bibliothèque de
# chaînes de tout le processus (string.len, out() de CA). Remplacer par string.gmatch ou une comparaison de string.sub.
INTERDITS = [(re.compile(r"\bfind\s*\([^\n]*,\s*true\s*\)"), "string.find(..., true) interdit (texte brut, WH3 9.0.2)")]


def appels_interdits(chemin):
    """Messages « fichier:ligne: raison » pour chaque appel interdit hors commentaire."""
    sortie = []
    for n, ligne in enumerate(open(chemin, encoding="utf-8", errors="replace"), 1):
        code = ligne.split("--", 1)[0]
        for motif, raison in INTERDITS:
            if motif.search(code):
                sortie.append(f"{os.path.basename(chemin)}:{n}: {raison}")
    return sortie


def fichiers(cibles):
    for c in cibles:
        if os.path.isdir(c):
            for racine, _d, noms in os.walk(c):
                for n in sorted(noms):
                    if n.endswith(".lua"):
                        yield os.path.join(racine, n)
        else:
            yield c


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    lua = charger_lua()
    L = lua.luaL_newstate()
    erreurs = 0
    for f in fichiers(sys.argv[1:]):
        e = verifier(lua, L, f)
        interdits = appels_interdits(f)
        if interdits:
            e = (e + "\n       " if e else "") + "\n       ".join(interdits)
        print(f"  {'ok ' if e is None else '!! '} {f}" + ("" if e is None else f"\n       {e}"))
        erreurs += e is not None
    lua.lua_close(L)
    print(f"{erreurs} erreur(s)")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
