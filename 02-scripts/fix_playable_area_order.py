#!/usr/bin/env python3
"""
fix_playable_area_order.py - contourne un défaut de l'Assembly Kit : **MapDataBuilder plante si la
ligne de `campaign_map_playable_areas` de la carte traitée est la dernière de la table.**

Constaté le 20.09.2026 sur `wh_dlc05_wood_elves_map_1`, vérifié quatre fois dans les deux sens :

| Ordre de la table | notre carte | l'île |
|---|---|---|
| … combi5, île, **NOUS** (la nôtre en dernier) | plante | passe |
| … combi5, **NOUS**, île | passe | passe |
| … combi5, **NOUS** seule (ligne de l'île retirée) | passe | — |

Le plantage est un déréférencement de pointeur nul (`0xC0000005`, lecture de l'adresse 8) dans
`empireutility.modder.x64.dll+0x318ead`, visible grâce au filtre d'exception ajouté à
MapDataBuilder dans le fork. Le contenu des lignes est identique dans les trois cas : **seul
l'ordre change**.

Le script déplace la ligne demandée d'un cran vers le haut quand elle est en dernière position,
sans rien changer d'autre : même contenu, même encodage, mêmes fins de ligne. Il ne fait rien si
la table compte moins de deux lignes ou si la ligne n'est pas la dernière.

Usage :
    python fix_playable_area_order.py --asskit "<kit WH3>" --index 1758400002 [--check]
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime

ATELIER = r"C:\TotalWar-CampaignMap"
TABLE = "campaign_map_playable_areas"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asskit", required=True)
    ap.add_argument("--index", required=True, help="index (clé) de la zone jouable de la carte")
    ap.add_argument("--check", action="store_true", help="dire seulement où en est l'ordre")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    path = os.path.join(a.asskit, "raw_data", "db", TABLE + ".xml")
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    pattern = re.compile(rf'<{TABLE} [^>]*record_key="([^"]*)">.*?</{TABLE}>\r?\n?', re.S)
    rows = {m.group(1): m.group(0) for m in pattern.finditer(text)}
    order = [m.group(1) for m in pattern.finditer(text)]

    if a.index not in rows:
        raise SystemExit(f"aucune zone jouable d'index {a.index} dans {TABLE}")
    position = order.index(a.index)
    print(f"  {len(order)} zones jouables ; la nôtre est en position {position + 1}")

    if position != len(order) - 1:
        print("  rien à faire : elle n'est pas en dernier.")
        return 0
    if len(order) < 2:
        print("  rien à faire : c'est la seule ligne de la table.")
        return 0
    if a.check:
        print("  ATTENTION : elle est en dernier, MapDataBuilder plantera. Relancer sans --check.")
        return 1

    new_order = order[:-2] + [order[-1], order[-2]]
    first = text.find(rows[order[0]])
    last = text.rfind(rows[order[-1]]) + len(rows[order[-1]])
    rebuilt = text[:first] + "".join(rows[k] for k in new_order) + text[last:]

    backup = os.path.join(ATELIER, "05-journal", "db-backups",
                          "ordre-zones-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(backup, exist_ok=True)
    shutil.copy2(path, os.path.join(backup, TABLE + ".xml"))
    with open(path, "wb") as f:
        f.write((b"\xef\xbb\xbf" if bom else b"") + rebuilt.encode("utf-8"))
    print(f"  déplacée en position {len(order) - 1} (avant « {new_order[-1]} ») ; sauvegarde dans {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
