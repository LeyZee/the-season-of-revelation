#!/usr/bin/env python3
r"""
textes_boutons_missions.py - les deux textes que CA remplit pour chacune de ses lignes et que nos incidents et missions
n'avaient pas : le bouton d'un incident (`incidents_button_text_<clé>`) et le texte de mission accomplie
(`missions_localised_mission_completed_text_<clé>`).

Pourquoi (revue du pack de la bêta, 25.09.2026, M4) : 11 incidents à nous sans libellé de bouton, 90 missions sans
texte de réussite ; effet probable, un bouton ou un message vide. Comme CA (33 incidents de CA renvoient au texte d'un
autre, `{{tr:incidents_button_text_…}}`), nos textes RENVOIENT à ceux de CA : « Continuer » / « Continue » et
« Succès ! Vous avez atteint l'un de vos objectifs. », dans TOUTES les langues du jeu, sans traduction à tenir.

Portée : nos lignes du kit (clé `saison_…`) que le pack porte, sans texte chez nous ni chez CA. Les textes vont dans
textes_gameplay.json (la seule source ; injecter_textes.py les pose après le pack). Aucune ligne de CA touchée.

Usage :
    python textes_boutons_missions.py            # à blanc
    python textes_boutons_missions.py --apply    # ajoute les clés absentes à textes_gameplay.json
"""

import argparse
import json
import os
import sys

from chemins_atelier import PROJET
from donnees_campagne import TableKit

TEXTES = os.path.join(PROJET, "textes", "textes_gameplay.json")
# les textes de CA vers lesquels on renvoie (valeurs vérifiées dans le .loc 9.0, FR et EN)
REFERENCES = {
    "incidents": ("button_text", "incidents_button_text_", "Continue"),
    "missions": ("localised_mission_completed_text", "missions_localised_mission_completed_text_",
                 "Success! You have achieved one of your goals"),
}


def reference(t, champ, debut):
    """Une ligne de CA dont le champ commence par le texte générique voulu (la première trouvée : stable)."""
    for k, c in t.lignes:
        v = t.valeurs(c)
        if not str(v.get("key", "")).startswith(("saison_", "wh_dlc05_")) and (v.get(champ) or "").startswith(debut):
            return v["key"]
    raise SystemExit(f"aucune ligne de CA au texte « {debut} »")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    nos = json.load(open(TEXTES, encoding="utf-8"))
    ajouts = {}
    for table, (champ, prefixe, debut) in REFERENCES.items():
        t = TableKit(table)
        ref = reference(t, champ, debut)
        for k, c in t.lignes:
            cle = t.valeurs(c).get("key", "")
            if not cle.startswith("saison_"):
                continue
            loc = prefixe + cle
            if loc in nos:
                continue
            valeur = "{{tr:" + prefixe + ref + "}}"
            ajouts[loc] = {"fr": valeur, "en": valeur}
        print(f"{table}.{champ} : renvoi vers {prefixe}{ref} ; {sum(1 for c in ajouts if c.startswith(prefixe))} clé(s) à ajouter")
    if not a.apply:
        print("à blanc : --apply pour écrire")
        return 0
    nos.update(ajouts)
    with open(TEXTES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nos, f, ensure_ascii=False, indent=1)
    print(f"{len(ajouts)} clé(s) ajoutée(s) à {TEXTES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
