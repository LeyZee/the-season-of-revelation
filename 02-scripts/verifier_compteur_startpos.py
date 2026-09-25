#!/usr/bin/env python3
"""
verifier_compteur_startpos.py - le startpos porte-t-il les valeurs de script d'une partie neuve ?

Pourquoi (23.09.2026, erreur 112, GUIDE § 15 n° 117) : `cm:is_new_game()` vaut « `__save_counter` == 1 ». Le compteur
n'est écrit que si les scripts de la campagne tournent pendant la génération du startpos. Un startpos plus ancien que
les scripts le laisse à 0 : chaque nouvelle partie passe pour une sauvegarde (ni intro, ni missions). Les valeurs de
script sont dans le bloc `COMPRESSED_DATA` (LZMA) : on le décompresse (`comparer_structure_esf.interne`) et on y
cherche les noms, en ASCII et en UTF-16.

Usage :
    python verifier_compteur_startpos.py <startpos.esf> [nom de valeur ...]
    (sans nom : __save_counter ; code de sortie 1 si l'un des noms manque)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comparer_structure_esf as C                                  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    chemin, noms = sys.argv[1], (sys.argv[2:] or ["__save_counter"])
    octets = bytes(C.interne(chemin).b)                                 # ESF décompressé (`lire_esf.Esf.b`)
    print(f"{chemin} : ESF interne de {len(octets)} octets")
    manque = False
    for nom in noms:
        a, u = octets.count(nom.encode("ascii")), octets.count(nom.encode("utf-16-le"))
        print(f"  {nom} : {a} en ASCII, {u} en UTF-16")
        manque |= not (a or u)
    return 1 if manque else 0


if __name__ == "__main__":
    sys.exit(main())
