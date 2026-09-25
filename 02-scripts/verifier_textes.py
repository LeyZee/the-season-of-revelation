"""Contrôle des textes à nous (textes_gameplay.json) avant toute injection ou livraison.

    python verifier_textes.py [fichier.json]

Cherche : caractères de contrôle (erreur 140 : U+0001 semé par un heredoc), « \\n » littéraux, balises [[ ]]
déséquilibrées, typographie française (espace insécable U+00A0 avant « ; ? ! : », dans « »), insécables égarées dans
l'anglais, français identique à l'anglais sur un texte long. Code de retour 1 s'il y a au moins un défaut.
Lecture seule. Session « IA et modding 3D », 23.09.2026."""
import json
import os
import re
import sys
from collections import Counter

JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "04-projets", "saison-des-revelations", "textes",
                  "textes_gameplay.json")
NB = " "


def defauts(textes):
    pb = []
    for k, v in textes.items():
        if not isinstance(v, dict):
            continue                      # « _commentaire » et autres notes
        for l, t in v.items():
            if not isinstance(t, str):
                continue
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", t):
                pb.append((k, l, "caractère de contrôle", ""))
            if "\\n" in t:
                pb.append((k, l, "\\n littéral", ""))
            # 25.09.2026 (étude des textes) : antislash avant un vrai saut de ligne, reste de la conversion de WH1
            if "\\\n" in t:
                pb.append((k, l, "antislash avant un saut de ligne", ""))
            ouv, ferm = len(re.findall(r"\[\[(?!/)", t)), len(re.findall(r"\[\[/", t))
            if ouv != ferm:
                pb.append((k, l, "balises [[ ]] déséquilibrées", f"{ouv} ouvrantes, {ferm} fermantes"))
            s = re.sub(r"\[\[[^\]]*\]\]", "", t)
            s = re.sub(r"\{\{[^}]*\}\}", "", s)
            s = re.sub(r"https?://\S+", "", s)
            if l == "fr":
                for m in re.finditer(r"(?<=[^\s" + NB + r" ])[;?!](?=\s|$|»)", s):
                    if s[max(0, m.start() - 5):m.start()].endswith("Waaagh"):
                        continue          # nom propre (Waaagh!)
                    pb.append((k, l, "sans insécable avant " + m.group(0), s[max(0, m.start() - 30):m.end() + 3]))
                for m in re.finditer(r"(?<=[A-Za-zÀ-ÿ»\)])(:)(?=\s)", s):
                    pb.append((k, l, "sans insécable avant :", s[max(0, m.start() - 30):m.end() + 3]))
                for m in re.finditer(r" [:;?!»]", s):
                    pb.append((k, l, "espace normale avant " + m.group(0).strip(), s[max(0, m.start() - 30):m.end() + 3]))
                for m in re.finditer(r"« ", s):
                    pb.append((k, l, "espace normale après «", s[max(0, m.start() - 5):m.end() + 20]))
            if l == "en" and re.search(NB + r"[:;?!]", t):
                pb.append((k, l, "insécable en anglais", ""))
        # (un renvoi pur à un texte de CA, {{tr:…}}, est le même dans toutes les langues : voulu, 25.09.2026)
        if v.get("fr") and v.get("fr") == v.get("en") and len(v["fr"]) > 25 \
                and not re.fullmatch(r"\{\{tr:[A-Za-z0-9_]+\}\}", v["fr"]):
            pb.append((k, "fr=en", "français identique à l'anglais", v["fr"][:60]))
    return pb


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    chemin = sys.argv[1] if len(sys.argv) > 1 else JS
    textes = json.load(open(chemin, encoding="utf-8"))
    pb = defauts(textes)
    print(f"{len(textes)} clés ; {len(pb)} défaut(s)")
    for genre, n in Counter(p[2] for p in pb).most_common():
        print(f"  {n:4d}  {genre}")
    for p in pb[:40]:
        print("  ", p)
    return 1 if pb else 0


if __name__ == "__main__":
    sys.exit(main())
