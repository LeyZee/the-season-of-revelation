#!/usr/bin/env python3
"""
chaines_de_fonctions.py - pour des adresses d'un exécutable 64 bits (pile d'un vidage), donne la
fonction qui les contient et les chaînes que cette fonction référence (LEA relatives à RIP).

Rapide même sur Warhammer3.exe : recherche binaire dans la table .pdata, et motifs cherchés par
expressions régulières (pas de boucle Python octet par octet).

Usage :
    python chaines_de_fonctions.py <exe> 27A7DFF 27C583F ...     # RVA en hexadécimal
"""

import bisect
import re
import struct
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
import lire_dll as L  # noqa: E402

LEA = re.compile(rb"[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", re.S)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    b = open(sys.argv[1], "rb").read()
    base, secs, opt = L.sections(b)
    fns = sorted(L.fonctions(b, secs, opt))
    debuts = [f[0] for f in fns]
    for a in sys.argv[2:]:
        rva = int(a, 16)
        k = bisect.bisect_right(debuts, rva) - 1
        if k < 0 or not (fns[k][0] <= rva < fns[k][1]):
            print(f"0x{rva:x} : hors des fonctions déclarées")
            continue
        d, f = fns[k]
        va, _, code = L.code_de(b, secs, d)        # la section qui contient la fonction (erreur 56)
        morceau = code[d - va: f - va]
        vus = []
        for m in LEA.finditer(morceau):
            i = m.start()
            cible = d + i + 7 + struct.unpack_from("<i", morceau, i + 3)[0]
            c = L.chaine(b, secs, cible)
            if c and c not in vus:
                vus.append(c)
        print(f"0x{rva:x} dans 0x{d:x}-0x{f:x} ({f - d} octets) : " + (" | ".join(vus[:25]) if vus else "aucune chaîne"))


if __name__ == "__main__":
    main()
