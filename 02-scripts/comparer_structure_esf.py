#!/usr/bin/env python3
"""
comparer_structure_esf.py - chercher dans un startpos.esf ce qui manque par rapport à un startpos qui
charge en jeu, **type de nœud par type de nœud**.

Pourquoi (21.09.2026, 19 h) : le jeu plantait au chargement de la campagne parce que 18 colonies
n'avaient aucun emplacement (`primary` introuvable, lecture de 0x30). Le startpos se générait sans
erreur : seule la lecture en jeu tombait. Ce genre de manque se voit dans la structure — une
colonie de référence a toujours ses emplacements, les nôtres non. D'où ce contrôle générique.

Méthode : les deux startpos sont décompressés (bloc `COMPRESSED_DATA`, LZMA). Pour chaque type
d'enregistrement présent des deux côtés, on relève les enfants-enregistrements que **toutes** les
instances de référence portent (au moins MIN instances), puis les instances de notre fichier à qui
l'un d'eux manque. Idem pour les blocs : un bloc jamais vide chez la référence et vide chez nous.

Usage :
    python comparer_structure_esf.py --esf <notre startpos.esf> --reference <startpos qui charge.esf>
        [--min 5] [--exemples 3]
"""

import argparse
import lzma
import os
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lire_esf as E                                                # noqa: E402


def interne(chemin):
    """ESF interne (décompressé) d'un startpos, ou le fichier lui-même s'il n'est pas compressé."""
    esf = E.Esf(open(chemin, "rb").read())
    racine = esf.analyse()
    comp = [e for e in racine["enfants"] if e["type"] == "record" and esf.nom(e["nom"]) == "COMPRESSED_DATA"]
    if not comp:
        return esf
    donnees = [e for e in comp[0]["enfants"] if e["type"] == "tableau"][0]["données"]
    info = [e for e in comp[0]["enfants"] if e["type"] == "record"][0]["enfants"]
    taille = [int.from_bytes(v["données"], "big" if v["base"] in (0x18, 0x1C) else "little")
              for v in info if v["type"] == "valeur"][0]
    props = [v["données"] for v in info if v["type"] == "tableau"][0]
    brut = lzma.decompress(props + struct.pack("<Q", taille) + donnees, format=lzma.FORMAT_ALONE)
    dedans = E.Esf(brut)
    dedans.analyse()
    return dedans


def enfants_records(n):
    """Enfants-enregistrements directs, groupes de bloc aplatis."""
    for e in n["enfants"]:
        if e["type"] == "record":
            yield e
        elif e["type"] == "groupe":
            for f in e["enfants"]:
                if f["type"] == "record":
                    yield f


def releve(esf):
    """nom -> liste d'instances ; instance = (chemin, Counter des noms d'enfants, nb groupes si bloc)."""
    out = defaultdict(list)

    def visite(n, chemin):
        nom = esf.nom(n["nom"])
        c = chemin + (nom,)
        noms = Counter(esf.nom(e["nom"]) for e in enfants_records(n))
        out[nom].append(("/".join(c[-4:]), noms, len(n["enfants"]) if n["bloc"] else None))
        for e in enfants_records(n):
            visite(e, c)

    visite(esf.racine, ())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--esf", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--min", type=int, default=5, help="instances de référence minimum pour conclure")
    ap.add_argument("--exemples", type=int, default=3)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    nous, ref = releve(interne(a.esf)), releve(interne(a.reference))
    print(f"types d'enregistrement : nous {len(nous)}, référence {len(ref)}, communs {len(set(nous) & set(ref))}")
    anomalies = 0
    for nom in sorted(set(nous) & set(ref)):
        r = ref[nom]
        if len(r) < a.min:
            continue
        toujours = set.intersection(*(set(i[1]) for i in r))
        for enfant in sorted(toujours):
            manque = [i for i in nous[nom] if enfant not in i[1]]
            if manque:
                anomalies += 1
                print(f"\n!! {nom} : l'enfant {enfant} est dans les {len(r)} instances de référence, "
                      f"absent de {len(manque)}/{len(nous[nom])} des nôtres")
                for chemin, _, _ in manque[:a.exemples]:
                    print(f"     {chemin}")
        if all(i[2] is not None for i in r) and min(i[2] for i in r) > 0:
            vides = [i for i in nous[nom] if i[2] == 0]
            if vides:
                anomalies += 1
                print(f"\n!! bloc {nom} : jamais vide chez la référence ({len(r)} instances, "
                      f"min {min(i[2] for i in r)}), vide dans {len(vides)}/{len(nous[nom])} des nôtres")
                for chemin, _, _ in vides[:a.exemples]:
                    print(f"     {chemin}")
    absents = sorted(n for n in set(ref) - set(nous) if len(ref[n]) >= a.min)
    print(f"\n{anomalies} anomalie(s).")
    print(f"types présents chez la référence (>= {a.min} fois) et jamais chez nous : {len(absents)}")
    print("   " + ", ".join(absents[:80]))
    return 1 if anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
