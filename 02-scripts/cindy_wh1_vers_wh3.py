#!/usr/bin/env python3
"""
cindy_wh1_vers_wh3.py - met les scènes Cindy de WH1 (versions 20 et 21) au format 22, le plus ancien que WH3 livre
(20 scènes et caméras d'une bataille de quête de Kroq-Gar) : un format dont on sait que le moteur de WH3 le lit.

Pourquoi (23.09.2026) : l'intro de la mini-campagne (v21) et sa fin (v20) sont des fichiers de WH1 ; WH3 ne livre
aucune scène sous la version 22 (relevé de toutes les scènes des packs : v22, 23, 26, 27). Écarts relevés entre les
versions (`05-journal\\2026-09-22-gameplay-wh3\\plan.md`, 23.09.2026) :
- scène (SCENE_FILE) : même structure de la v20 à la v22 ; seule la version change ;
- caméra (WARSCAPE_PROPERTIES_FILE) v21 -> v22 : `NODE DOF_focus` (Variance seule) devient `VARIANCE DOF_focus`
  (Variable + Variance) ;
- caméra v20 -> v22 : yaw, pitch et roll passent dans `NODE rotation` ; « speed of time / of cinematic / of logic »
  deviennent `NODE time speed multipliers` (global, cinematic, game logic) ; `VARIANCE DOF_focus` est déjà au format.
Les images clés, les valeurs et l'ordre des attributs ne changent pas.

Garde : chaque fichier est d'abord relu puis réécrit tel quel ; si la réécriture n'est pas identique à l'octet près
(fins de ligne comprises), le fichier n'est pas touché.

Usage :
    python cindy_wh1_vers_wh3.py <dossier> [--apply]     # tous les .CindyScene et cameras\\*.xml du dossier
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

VERSION_CIBLE = "22"
VITESSES = {  # v20 -> v22 : (nom, nom affiché, ordre)
    "speed of time": ("global", "Global", "0"),
    "speed of cinematic": ("cinematic", "Cinematic", "1"),
    "speed of logic": ("game logic", "Game Logic", "2"),
}


def ecrire(racine, fin_de_ligne):
    """Sérialisation au style des fichiers de CA : une balise par ligne, un espace d'indentation par niveau,
    attributs dans l'ordre lu, balises vides fermées par « /> »."""
    lignes = []

    def marcher(e, n):
        attrs = "".join(f' {k}="{escape(v, {chr(34): "&quot;"})}"' for k, v in e.attrib.items())
        if len(e):
            lignes.append(" " * n + f"<{e.tag}{attrs}>")
            for f in e:
                marcher(f, n + 1)
            lignes.append(" " * n + f"</{e.tag}>")
        else:
            lignes.append(" " * n + f"<{e.tag}{attrs}/>")

    marcher(racine, 0)
    return (fin_de_ligne.join(lignes) + fin_de_ligne).encode("utf-8")


def fin_de_ligne(octets):
    return "\r\n" if b"\r\n" in octets else "\n"


def camera_v20(cam):
    """Rotation et vitesses de la v20 rangées comme en v21 / v22."""
    rotation = [e for e in list(cam) if e.tag == "RADIAN" and e.get("name") in ("yaw", "pitch", "roll")]
    vitesses = [e for e in list(cam) if e.tag == "DOUBLE" and e.get("name") in VITESSES]
    if rotation:
        noeud = ET.Element("NODE", {"name": "rotation"})
        for nom in ("yaw", "pitch", "roll"):
            for e in rotation:
                if e.get("name") == nom:
                    cam.remove(e)
                    noeud.append(e)
        cam.append(noeud)
    if vitesses:
        noeud = ET.Element("NODE", {"name": "time speed multipliers", "user_friendy_name": "Time Speed Multipliers"})
        for ancien in VITESSES:
            for e in vitesses:
                if e.get("name") == ancien:
                    cam.remove(e)
                    nom, affiche, ordre = VITESSES[ancien]
                    e.set("name", nom)
                    e.set("user_friendy_name", affiche)
                    e.set("order", ordre)
                    noeud.append(e)
        cam.append(noeud)


def camera_v21(cam):
    """`NODE DOF_focus` (Variance seule) -> `VARIANCE DOF_focus` (Variable + Variance), comme en v20 et v22."""
    for e in list(cam):
        if e.tag == "NODE" and e.get("name") == "DOF_focus":
            e.tag = "VARIANCE"
            if not any(f.get("name") == "Variable" for f in e):
                # même ordre d'attributs que la Variance voisine ; valeurs de la v20 et de la v22 (Variable 0, cachée)
                valeurs = {"name": "Variable", "default": "0", "hidden": "true", "animated": "1",
                           "single_keyframe_only": "0", "order": "0"}
                modele = next((f for f in e if f.tag == "DOUBLE"), None)
                cles = list(modele.attrib) if modele is not None else list(valeurs)
                e.insert(0, ET.Element("DOUBLE", {k: valeurs.get(k, modele.get(k) if modele is not None else "")
                                                  for k in cles}))


def convertir(chemin):
    """Rend (octets convertis ou None, message)."""
    octets = open(chemin, "rb").read()
    fdl = fin_de_ligne(octets)
    racine = ET.fromstring(octets)
    if ecrire(racine, fdl) != octets:
        return None, "réécriture non identique à l'original : fichier laissé tel quel"
    version = racine.get("version")
    if version == VERSION_CIBLE:
        return None, f"déjà en v{VERSION_CIBLE}"
    if version not in ("20", "21"):
        return None, f"version {version} non prise en charge"
    if racine.tag == "WARSCAPE_PROPERTIES_FILE":
        cam = next((e for e in racine if e.tag == "NODE" and e.get("name") == "Camera"), None)
        if cam is None:
            return None, "pas de nœud Camera"
        if version == "20":
            camera_v20(cam)
        camera_v21(cam)
    elif racine.tag != "SCENE_FILE":
        return None, f"racine {racine.tag} non prise en charge"
    racine.set("version", VERSION_CIBLE)
    return ecrire(racine, fdl), f"v{version} -> v{VERSION_CIBLE}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dossier")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    n = 0
    for r, _d, fs in os.walk(a.dossier):
        for f in sorted(fs):
            fl = f.lower()
            if not (fl.endswith(".cindyscene") or (fl.endswith(".xml") and os.path.basename(r).lower() == "cameras")):
                continue
            chemin = os.path.join(r, f)
            neuf, msg = convertir(chemin)
            print(f"  {os.path.relpath(chemin, a.dossier)} : {msg}")
            if neuf is not None:
                ET.fromstring(neuf)  # relisible
                n += 1
                if a.apply:
                    with open(chemin, "wb") as sortie:
                        sortie.write(neuf)
    print(f"{n} fichier(s) {'converti(s)' if a.apply else 'à convertir'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
