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
        print(f"  {'ok ' if e is None else '!! '} {f}" + ("" if e is None else f"\n       {e}"))
        erreurs += e is not None
    lua.lua_close(L)
    print(f"{erreurs} erreur(s)")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
