#!/usr/bin/env python3
r"""
preparer_depots_publics.py - prépare, EN LOCAL, les deux dépôts GitHub publics du mod : la Saison originale et Saison
Expanded. Rien n'est poussé ici (la poussée se fait à la main, après accord de Charles et de la construction).

Pourquoi (25.09.2026, vers 19 h, décisions de Charles) : « un dépôt GitHub public avec un joli README », « il en faudra
deux » (original et Expanded), « tout doit être agréable à lire, on doit comprendre d'un coup d'œil » ; la documentation
peut être publique ; le dépôt du SITE reste privé (sessions « Extension » et « Vidéo »).

Contenu :
- la Saison : la liste blanche de `exporter_partageable.py` (nos scripts, nos Lua, nos textes, la documentation) ;
- Expanded : la liste blanche de la construction (25.09.2026) : README.md, PLAN.md, JOURNAL.md, map_spec_expanded.json,
  outils\*.py ; tout le reste de 04-projets\saison-expanded (caime, couches, terry, relief, aperçus, captures, pack,
  relevés) est dérivé de WH1 et EXCLU.
Dans les COPIES seulement (jamais les sources), les chemins de la machine sont anonymisés (condition de la construction).
Chaque fichier copié repasse l'audit : extensions, taille, données sensibles, chemins restants.
Présentation, dans la direction artistique du site (bretonia.dev) : bannière sur vélin avec cadre orné en damier et
écoinçons fleurdelisés, sceaux de cire (`sceaux.py`, `decors_carte.py` du site, lus sans écrire), polices du site
(Grenze Gotisch, IM Fell English) embarquées dans les SVG ; README en anglais et en français ; LICENSE (MIT) ; NOTICE.

Usage :
    python preparer_depots_publics.py                  # à blanc : listes et audit
    python preparer_depots_publics.py --apply          # écrit les deux dossiers (Downloads\the-season-of-revelation*)
    python preparer_depots_publics.py --apply --depot expanded
"""

import argparse
import base64
import glob
import io
import os
import re
import shutil
import sys

import exporter_partageable as EXP
from chemins_atelier import ATELIER, JOURNAL

DOWNLOADS = os.path.dirname(ATELIER)
TRAVAIL_ATLAS = os.path.join(JOURNAL, "2026-09-23-extension-carte", "travail")
EXPANDED = os.path.join(ATELIER, "04-projets", "saison-expanded")
MARQUE = ".depot-genere"          # un dossier qui porte ce fichier a été fait ici : on peut le régénérer

DEPOTS = {
    "saison": {"dossier": os.path.join(DOWNLOADS, "the-season-of-revelation"), "nom": "the-season-of-revelation"},
    "expanded": {"dossier": os.path.join(DOWNLOADS, "the-season-of-revelation-expanded"),
                 "nom": "the-season-of-revelation-expanded"},
}
GITHUB = "https://github.com/LeyZee/"
SITE = "https://bretonia.dev"
# 25.09.2026, 22 h 45 (Charles : « la bêta est out », « j'ouvre les collaborations ») : lien de la page Workshop de la Saison
WORKSHOP = "https://steamcommunity.com/sharedfiles/filedetails/?id=3807973986"

# ---------------------------------------------------------------------------------------------------------------------
# Anonymisation (copies seulement)
# ---------------------------------------------------------------------------------------------------------------------

_RACINE_ATELIER = [r"C:\TotalWar-CampaignMap", r"C:/TotalWar-CampaignMap",
                   r"C:\\TotalWar-CampaignMap"]
_REMPLACEMENTS = [(v, v.replace("Users" + v[2] + "USER" + v[2] + "Downloads" + v[2], "")) for v in _RACINE_ATELIER[:2]] + [
    (_RACINE_ATELIER[2], r"C:\\TotalWar-CampaignMap"),
    (r"C:\Users\you", r"C:\Users\you"), (r"C:/Users/you", r"C:/Users/you"), (r"C:\\Users\\you", r"C:\\Users\\you"),
    (r"/c/Users/you", r"/c/Users/you"),
]


def anonymiser(texte):
    """Chemins de la machine de Charles -> chemins neutres (C:\\TotalWar-CampaignMap, C:\\Users\\you) ; sans changer la
    syntaxe (les scripts restent valides, chemins_atelier.py les règle)."""
    for avant, apres in _REMPLACEMENTS:
        texte = texte.replace(avant, apres)
    return texte


# motifs découpés : ce fichier est lui-même publié et ne doit pas se refuser (ni contenir l'adresse qu'il cherche)
RESTE_PERSONNEL = re.compile(r"(?i)users[\\/]+USER\b|" + "charles" + chr(64) + "|" + "impera" + r"-agency\.")


# ---------------------------------------------------------------------------------------------------------------------
# Direction artistique (le site : vélin, encre, rouge héraldique, sceaux de cire, cadre orné)
# ---------------------------------------------------------------------------------------------------------------------

ENCRE, ROUGE, VELIN, FOND = "#2b1d10", "#8e1b14", "#efe3c2", "#e6d6ae"


def _atlas():
    """Les modules de dessin du site, en lecture seule."""
    if TRAVAIL_ATLAS not in sys.path:
        sys.path.insert(0, TRAVAIL_ATLAS)
    import decors_carte  # noqa: E402
    import sceaux  # noqa: E402
    return sceaux, decors_carte


def _police(nom_fichier, famille, style="normal", graisse="400"):
    donnees = open(os.path.join(TRAVAIL_ATLAS, "polices", nom_fichier), "rb").read()
    return (f"@font-face{{font-family:'{famille}';font-style:{style};font-weight:{graisse};"
            f"src:url(data:font/woff2;base64,{base64.b64encode(donnees).decode()}) format('woff2')}}")


def _polices():
    return (_police("grenze-gotisch-700-latin.woff2", "Grenze", graisse="700")
            + _police("im-fell-english-400-latin.woff2", "Fell")
            + _police("im-fell-english-400i-latin.woff2", "Fell", style="italic"))


def _ecu_data(largeur=220):
    """L'écu peint du site (logo), réduit, en data URI WebP."""
    from PIL import Image
    im = Image.open(os.path.join(TRAVAIL_ATLAS, "images_source", "logo", "logo.webp")).convert("RGBA")
    h = round(im.height * largeur / im.width)
    im = im.resize((largeur, h), Image.LANCZOS)
    tampon = io.BytesIO()
    im.save(tampon, "WEBP", quality=88)
    return "data:image/webp;base64," + base64.b64encode(tampon.getvalue()).decode(), largeur, h


def _grain(identifiant):
    return (f'<filter id="{identifiant}" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed="11" result="n"/>'
            '<feColorMatrix in="n" values="0 0 0 0 0.30  0 0 0 0 0.20  0 0 0 0 0.09  0 0 0 0.13 0"/></filter>'
            f'<filter id="{identifiant}-taches" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.010" numOctaves="2" seed="4" result="n"/>'
            '<feColorMatrix in="n" values="0 0 0 0 0.42  0 0 0 0 0.30  0 0 0 0 0.14  0 0 0 0.16 0"/></filter>')


def _lys(x, y, echelle, couleur, extra=""):
    _, D = _atlas()
    return f'<path transform="translate({x},{y}) scale({echelle})" d="{D.LYS}" fill="{couleur}"{extra}/>'


def banniere(titre, rubrique, ligne, mention):
    """La bannière du README : vélin, cadre orné du site, écu peint à gauche, sceau de cire fleurdelisé à droite."""
    S, D = _atlas()
    W, H = 1280, 440
    ecu, ew, eh = _ecu_data(150)
    x0, y0, x1, y1 = 34, 34, W - 34, H - 34
    cadre = D.cadre_orne(x0, y0, x1, y1, (x1 - x0) / 60, (y1 - y0) / 18, prefixe="f")
    relief = S.TEINTES["rouge"][4]
    taille = min(78, int(760 / (len(titre) * 0.40)))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="{titre}">'
        f'<defs><style>{_polices()}</style>{_grain("g")}{D.symbole_sceau("rouge")}'
        '<radialGradient id="vignette" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#5a3a14" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#5a3a14" stop-opacity=".30"/></radialGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="{FOND}"/>'
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{VELIN}"/>'
        f'<rect width="{W}" height="{H}" filter="url(#g-taches)"/><rect width="{W}" height="{H}" filter="url(#g)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>'
        f'{cadre}'
        # l'écu peint (gauche) et le grand sceau (droite), à hauteur du titre
        f'<image href="{ecu}" x="{112 - ew / 2:.0f}" y="{150 - eh / 2:.0f}" width="{ew}" height="{eh}"/>'
        f'<g filter="drop-shadow(0 3px 2px rgba(40,14,4,.45))"><use href="#sceau-rouge" x="1098" y="80" width="136" height="136"/></g>'
        f'{_lys(1167.5, 152.5, 3.1, "#5f0f0a", " opacity=\".6\"")}'
        f'{_lys(1166, 151, 3.1, relief)}'
        # le titre, lettrine rouge ; corps réglé sur la longueur (entre l'écu et le sceau : ~800 px ; Grenze ≈ 0,40 em)
        f'<text x="640" y="182" text-anchor="middle" font-family="Grenze" font-weight="700" font-size="{taille}" fill="{ENCRE}">'
        f'<tspan fill="{ROUGE}" font-size="{round(taille * 1.23)}">{titre[0]}</tspan>{titre[1:]}</text>'
        f'<text x="640" y="238" text-anchor="middle" font-family="Fell" font-style="italic" font-size="27" fill="{ROUGE}">{rubrique}</text>'
        # filet gravé fleurdelisé
        f'<path d="M330 272H604M676 272H950" stroke="{ENCRE}" stroke-width="1.4"/>'
        f'<path d="M330 277H604M676 277H950" stroke="{ENCRE}" stroke-width=".6" opacity=".7"/>'
        f'{_lys(640, 277, 1.45, ROUGE)}'
        f'<text x="640" y="322" text-anchor="middle" font-family="Fell" font-size="23" fill="{ENCRE}">{ligne}</text>'
        f'<text x="640" y="360" text-anchor="middle" font-family="Fell" font-style="italic" font-size="16" fill="{ENCRE}" '
        f'opacity=".72">{mention}</text>'
        '</svg>')


def separateur():
    """Filet gravé entre les parties du README : double trait d'encre, filet rouge, petit sceau fleurdelisé au centre."""
    S, D = _atlas()
    W, H = 1280, 56
    relief = S.TEINTES["rouge"][4]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs>{D.symbole_sceau("rouge")}</defs>'
            f'<path d="M80 26H598M682 26H1200" stroke="{ENCRE}" stroke-width="1.6"/>'
            f'<path d="M140 31.5H598M682 31.5H1140" stroke="{ROUGE}" stroke-width="1"/>'
            f'<path d="M80 26l-9 3 9 3zM1200 26l9 3-9 3z" fill="{ENCRE}"/>'
            f'<use href="#sceau-rouge" x="612" y="0" width="56" height="56"/>'
            f'{_lys(640, 29.5, .95, "#5f0f0a", " opacity=\".5\"")}{_lys(639.5, 29, .95, relief)}'
            '</svg>')


def sceau(teinte):
    """Un sceau de cire fleurdelisé (en-têtes des parties) ; teintes du site : rouge, vert, or, gris, bronze."""
    S, _ = _atlas()
    svg = S.svg_sceau(teinte)
    profond, relief = S.TEINTES[teinte][3], S.TEINTES[teinte][4]
    lys = (_lys(32.6, 34.6, 1.18, profond, ' opacity=".6"') + _lys(32, 34, 1.18, relief))
    return svg.replace("</svg>", lys + "</svg>")


# ---------------------------------------------------------------------------------------------------------------------
# Textes des README
# ---------------------------------------------------------------------------------------------------------------------

SEIGNEURS = [
    ("Orion", "The Wood Elves of Athel Loren", "Realm of the Wood Elves"),
    ("Durthu", "Argwylon", "Realm of the Wood Elves"),
    ("Drycha", "Drycha's spirits of the forest", "Realm of the Wood Elves"),
    ("The Sisters of Twilight", "The Sisters of Twilight", "The Twisted & The Twilight"),
    ("Alberic de Bordeleaux", "Bordeleaux", "Bretonnia (free)"),
    ("The Fay Enchantress", "Carcassonne", "Bretonnia (free)"),
    ("Morghur", "The Shadowgave's herd", "Call of the Beastmen"),
    ("The Red Duke", "Mousillon", "Total War: WARHAMMER"),
    ("Heinrich Kemmler", "The Barrow Legion", "Total War: WARHAMMER"),
    ("Grom the Paunch", "Broken Axe", "The Warden & The Paunch"),
]
SEIGNEURS_FR = {
    "The Sisters of Twilight": "Les Sœurs du Crépuscule", "Alberic de Bordeleaux": "Albéric de Bordeleaux",
    "The Fay Enchantress": "La Fée Enchanteresse", "The Red Duke": "Le Duc écarlate", "Grom the Paunch": "Grom la Panse",
    "The Wood Elves of Athel Loren": "Les Elfes sylvains d'Athel Loren", "Drycha's spirits of the forest":
    "Les esprits de la forêt de Drycha", "The Shadowgave's herd": "La harde de l'Enfant de l'Ombre",
    "The Barrow Legion": "La Légion des Tertres", "Broken Axe": "La Hache Brisée", "Bretonnia (free)": "Bretonnie (gratuit)",
    "Realm of the Wood Elves": "Le Royaume des Elfes Sylvains", "Call of the Beastmen": "L'Appel des Hommes-bêtes",
}


def _h2(teinte, titre):
    return f'## <img src="docs/art/seal-{teinte}.svg" height="34" alt=""> {titre}'


SEPARATEUR = '<p align="center"><img src="docs/art/divider.svg" width="100%" alt=""></p>'


def readme_saison_en():
    lignes_seigneurs = "\n".join(f"| **{n}** | {f} | {d} |" for n, f, d in SEIGNEURS)
    return f"""<p align="center"><img src="docs/art/banner.svg" width="100%" alt="The Season of Revelation, rebuilt for Total War: WARHAMMER III"></p>

<p align="center">
<a href="{SITE}"><b>Atlas of Bretonnia</b></a> ·
<a href="{SITE}/#film"><b>Watch the film</b></a> ·
<a href="MODDERS.md"><b>Modder's guide</b></a> ·
<a href="README.fr.md"><b>Lire en français</b></a> ·
<a href="{GITHUB}the-season-of-revelation-expanded"><b>Expanded</b></a>
</p>

In 2016, *Realm of the Wood Elves* shipped a small, beautiful campaign: **The Season of Revelation**, one autumn in
Athel Loren while Morghur's herds gather and the Oak of Ages calls its lords. This project brings that campaign into
**Total War: WARHAMMER III (patch 9.0)**. The map is Warhammer I's, untouched, the story is Warhammer I's, and the
gameplay is Warhammer III's, with ten legendary lords to play.

{SEPARATEUR}

{_h2("green", "At a glance")}

| | |
|---|---|
| **The map** | Warhammer I's mini-campaign map, kept as it was: 400 × 440 hexes, 61 regions, same relief, props, trees, textures and water. Warhammer III adds only what was missing. |
| **The story** | Warhammer I's *Season of Revelation*: the Oak of Ages, Morghur's invasions, the battle at the Silver Pinnacle; plus a chronicle for each lord. |
| **The gameplay** | Warhammer III 9.0, whole: vampire bloodlines and Blood Decrees, the Forge of Daith, Grom's cauldron, the Wild Hunt, 9.0 victory conditions. |
| **The lords** | Ten, each with a short and a long victory of their own, written from the lore. |
| **The tone** | Harder than the base game, and grimdark. When the lore makes something a threat, we kept it a threat. |
| **Status** | **Beta, on the [Steam Workshop]({WORKSHOP}).** Needs *Realm of the Wood Elves*. Compatibility with other mods is untested: tell us what breaks. |

{SEPARATEUR}

{_h2("gold", "What this repository is (and is not)")}

**It is** everything we wrote to make the port: the build tools (Python), the campaign scripts (Lua), every text we
added (French and English), the game-data lots, and the full workshop documentation, including every mistake we made
and the rule that now prevents it.

**It is not** the playable mod. The mod pack contains files converted from Warhammer I, so it is never published here.
This repository holds **no Warhammer I or Creative Assembly asset**: no models, textures, terrain, start position or
pack. To rebuild the map you need your own copies of both games and their Assembly Kits (see [NOTICE](NOTICE.md)).

{SEPARATEUR}

{_h2("red", "The ten lords")}

| Lord | Faction | Needs |
|---|---|---|
{lignes_seigneurs}

The campaign itself needs *Realm of the Wood Elves*: without it, the **Start** button is greyed out in the menu, with a
message. Each lord also needs the DLC that unlocks it in Immortal Empires.

{SEPARATEUR}

{_h2("bronze", "How the port is built")}

```mermaid
flowchart LR
    A["Warhammer I<br/>map, story, assets<br/><i>(your own copy)</i>"] --> B["Terrain chain<br/>02-scripts"]
    B --> C["Assembly Kit<br/>Warhammer III"]
    D["Game-data lots<br/>donnees_campagne.py"] --> C
    C --> E["build_pack.py"]
    F["Campaign scripts<br/>Lua"] --> E
    G["Texts FR + EN<br/>textes_gameplay.json"] --> E
    E --> H["Private mod pack"]
    H --> I["Automatic tests<br/>essai_tours_auto.py"]
```

- **Keys.** Everything we create is keyed `saison_…`; Warhammer I content keeps its `wh_dlc05_…` keys. We never
  overwrite a Creative Assembly table or row, so Immortal Empires keeps working with the mod enabled.
- **Game data** is written by documented, dated, idempotent *lots* (`donnees_campagne.py --lot etapeN [--apply]`).
- **Campaign scripts** start one system at a time, each one protected. A failing listener is logged, and never stops
  the others.
- **Every text** lives in one file, in French and English, and is checked before each pack.

{SEPARATEUR}

{_h2("grey", "Repository layout")}

```
02-scripts/                              build tools: terrain chain, data lots, pack, checks, tests
04-projets/saison-des-revelations/
    scripts-campagne/script/             campaign Lua (campaign/wh_dlc05_wood_elves, frontend/mod)
    textes/textes_gameplay.json          every text we add, French + English
docs/atelier/                            the workshop documentation (French): state, know-how, 270 lessons
MODDERS.md                               start here if you want to build or change the mod
NOTICE.md  LICENSE                       legal notes, MIT licence for our code
```

{SEPARATEUR}

{_h2("green", "Getting started")}

1. Read **[MODDERS.md](MODDERS.md)**: requirements, machine setup, how a pack is built, and the pitfalls that cost us
   the most.
2. Point the tools at your installs: copy `atelier_local.json.example` to `atelier_local.json` and edit it, then check
   with `python 02-scripts/chemins_atelier.py`.
3. The workshop documentation (French) is in [`docs/atelier/`](docs/atelier/). `GUIDE.md` § 15 lists the known traps;
   `ERREURS-ET-LECONS.md` tells why each rule exists.

{SEPARATEUR}

{_h2("red", "Join in")}

This is a community project now, and collaboration is open. Welcome help:

- **Play the beta** ([Steam Workshop]({WORKSHOP})) and report bugs and crashes, with your logs (see the Workshop page).
- **Lore**: proofread texts and victories against the sources; the project lead has the final say.
- **Translations**: every text lives in one file (`textes_gameplay.json`), French and English today.
- **Maps and code**: terrain, CAIME, Lua, data. Open an issue or a pull request, or come and talk on the Discord
  linked from [bretonia.dev]({SITE}).

{SEPARATEUR}

{_h2("gold", "Credits")}

A fan project by **LeyZee**, open source, by a fan for fellow fans, built with Claude Code.

- **Campaign Map Toolkit (CAIME)**: MrJox (aka victimized.), Maruka and Marthenil (founders), ChaosRobbie, Celebdil,
  Leoman (aka justLeo), Ophis, Causeless, PeteCA, Mitch, CharlesWoodhill, TadeoM, Frodo, Daniu, Ironic, OtherTomCA, and
  CAIME's beta testers. Our fork: [LeyZee/CampaignMapToolkit]({GITHUB}CampaignMapToolkit).
- **RPFM** (Rusted PackFile Manager) by Frodo45127.
- **Creative Assembly's Assembly Kit** for Total War: WARHAMMER III (BOB, Terry, DaVE).
- *The Season of Revelation*, its map and its story: **Creative Assembly**, Total War: WARHAMMER, *Realm of the Wood
  Elves*.

{SEPARATEUR}

{_h2("red", "Legal")}

Warhammer, the Warhammer world and all related names belong to **Games Workshop**. Total War: WARHAMMER belongs to
**Creative Assembly** and **SEGA**. This is a **non-commercial fan project**, not affiliated with or endorsed by them.
Our own code is under the [MIT licence](LICENSE); see [NOTICE](NOTICE.md) for what that covers and what it does not.
"""


def readme_saison_fr():
    lignes_seigneurs = "\n".join(f"| **{SEIGNEURS_FR.get(n, n)}** | {SEIGNEURS_FR.get(f, f)} | {SEIGNEURS_FR.get(d, d)} |"
                                 for n, f, d in SEIGNEURS)
    return f"""<p align="center"><img src="docs/art/banner-fr.svg" width="100%" alt="La Saison de la Révélation, refaite pour Total War: WARHAMMER III"></p>

<p align="center">
<a href="{SITE}"><b>Atlas de Bretonnie</b></a> ·
<a href="{SITE}/#film"><b>Voir le film</b></a> ·
<a href="MODDERS.md"><b>Guide des moddeurs (EN)</b></a> ·
<a href="README.md"><b>Read in English</b></a> ·
<a href="{GITHUB}the-season-of-revelation-expanded"><b>Expanded</b></a>
</p>

En 2016, *Le Royaume des Elfes Sylvains* apportait une petite campagne magnifique : **la Saison de la Révélation**, un
automne à Athel Loren, pendant que les hardes de Morghur se rassemblent et que le Chêne des Âges appelle ses seigneurs.
Ce projet la porte dans **Total War: WARHAMMER III (patch 9.0)**. La carte et l'histoire sont celles de Warhammer I,
intactes, le gameplay est celui de Warhammer III, et dix seigneurs légendaires sont jouables.

{SEPARATEUR}

{_h2("green", "D'un coup d'œil")}

| | |
|---|---|
| **La carte** | Celle de la mini-campagne de Warhammer I, telle quelle : 400 × 440 hex, 61 régions, mêmes reliefs, objets, arbres, textures et eaux. Warhammer III n'ajoute que ce qui manquait. |
| **L'histoire** | La *Saison de la Révélation* de Warhammer I : le Chêne des Âges, les invasions de Morghur, la bataille du Pic d'Argent ; et une chronique pour chaque seigneur. |
| **Le gameplay** | Celui de Warhammer III 9.0, en entier : lignées vampiriques et Décrets de sang, Forge de Daith, marmite de Grom, Chasse Sauvage, victoires de la 9.0. |
| **Les seigneurs** | Dix, chacun avec une victoire courte et une longue qui lui sont propres, écrites d'après le lore. |
| **Le ton** | Plus dur que le jeu de base, et grimdark : une menace du lore reste une menace. |
| **État** | **Bêta, sur le [Steam Workshop]({WORKSHOP}).** Demande *Le Royaume des Elfes Sylvains*. Compatibilité avec les autres mods non testée : dites-nous ce qui casse. |

{SEPARATEUR}

{_h2("gold", "Ce que contient ce dépôt (et ce qu'il ne contient pas)")}

**Il contient** tout ce que nous avons écrit pour ce portage : les outils de construction (Python), les scripts de
campagne (Lua), tous nos textes (français et anglais), les lots de données, et toute la documentation de l'atelier,
y compris chaque erreur commise et la règle qui l'évite désormais.

**Il ne contient pas** le mod jouable. Le pack contient des fichiers convertis de Warhammer I : il n'est jamais publié
ici. Aucun fichier de Warhammer I ni de Creative Assembly : ni modèles, ni textures, ni terrain, ni position de départ,
ni pack. Pour reconstruire la carte, il faut ses propres exemplaires des deux jeux et de leurs Assembly Kits (voir
[NOTICE](NOTICE.md)).

{SEPARATEUR}

{_h2("red", "Les dix seigneurs")}

| Seigneur | Faction | Contenu requis |
|---|---|---|
{lignes_seigneurs}

La campagne demande *Le Royaume des Elfes Sylvains* : sans lui, le bouton **Lancer** est grisé au menu, avec un
message. Chaque seigneur demande aussi le contenu qui le débloque aux Empires Immortels.

{SEPARATEUR}

{_h2("bronze", "Comment le portage est construit")}

- **Clés.** Tout ce que nous créons est clé `saison_…` ; ce qui vient de Warhammer I garde ses clés `wh_dlc05_…`.
  Aucune table ni ligne de Creative Assembly n'est écrasée : les Empires Immortels marchent avec le mod actif.
- **Les données de jeu** sont écrites par des *lots* documentés, datés, rejouables sans effet
  (`donnees_campagne.py --lot etapeN [--apply]`).
- **Les scripts de campagne** démarrent un système à la fois, chacun protégé : un écouteur en erreur est écrit au
  journal et n'arrête jamais les autres.
- **Tous les textes** sont dans un seul fichier, en français et en anglais, vérifiés avant chaque pack.

Le schéma de la chaîne est dans le [README anglais](README.md#how-the-port-is-built).

{SEPARATEUR}

{_h2("green", "Pour commencer")}

1. Lire **[MODDERS.md](MODDERS.md)** (en anglais) : prérequis, réglage de la machine, construction d'un pack, pièges.
2. Régler les chemins : copier `atelier_local.json.example` en `atelier_local.json`, puis vérifier avec
   `python 02-scripts/chemins_atelier.py`.
3. La documentation de l'atelier est dans [`docs/atelier/`](docs/atelier/) : `GUIDE.md` § 15 pour les pièges connus,
   `ERREURS-ET-LECONS.md` pour la raison de chaque règle.

{SEPARATEUR}

{_h2("red", "Participer")}

C'est désormais un projet communautaire, et les collaborations sont ouvertes. Toute aide est bienvenue :

- **Jouer la bêta** ([Steam Workshop]({WORKSHOP})) et signaler bugs et plantages, avec vos journaux (voir la page
  Workshop).
- **Lore** : relire textes et victoires d'après les sources ; le porteur du projet garde le dernier mot.
- **Traductions** : tous les textes sont dans un seul fichier (`textes_gameplay.json`), en français et en anglais
  aujourd'hui.
- **Carte et code** : terrain, CAIME, Lua, données. Ouvrez une issue ou une pull request, ou venez en parler sur le
  Discord indiqué par [bretonia.dev]({SITE}).

{SEPARATEUR}

{_h2("gold", "Crédits")}

Un projet de fan de **LeyZee**, open source, par un passionné, pour d'autres passionnés, construit avec Claude Code. Outils : **CAIME** (Campaign Map Toolkit : MrJox,
Maruka, Marthenil, ChaosRobbie, Celebdil, Leoman, Ophis, Causeless, PeteCA, Mitch, CharlesWoodhill, TadeoM, Frodo,
Daniu, Ironic, OtherTomCA et ses testeurs ; notre fork : [LeyZee/CampaignMapToolkit]({GITHUB}CampaignMapToolkit)),
**RPFM** de Frodo45127, et l'**Assembly Kit** de Creative Assembly. *La Saison de la Révélation*, sa carte et son
histoire : **Creative Assembly**.

{SEPARATEUR}

{_h2("red", "Mentions")}

Warhammer et tous les noms associés appartiennent à **Games Workshop** ; Total War: WARHAMMER à **Creative Assembly**
et **SEGA**. Projet de fan **non commercial**, sans lien avec eux ni approbation de leur part. Notre code est sous
[licence MIT](LICENSE) ; la [NOTICE](NOTICE.md) dit ce qu'elle couvre et ce qu'elle ne couvre pas.
"""


def readme_expanded_en():
    return f"""<p align="center"><img src="docs/art/banner.svg" width="100%" alt="The Season of Revelation: Expanded"></p>

<p align="center">
<a href="{SITE}"><b>Atlas of Bretonnia</b></a> ·
<a href="{GITHUB}the-season-of-revelation"><b>The original Season</b></a> ·
<a href="docs/fr/JOURNAL.md"><b>Build journal</b></a> ·
<a href="README.fr.md"><b>Lire en français</b></a>
</p>

**The Season of Revelation: Expanded** grows Warhammer I's mini-campaign map into **all of Bretonnia**. Warhammer I's
map is the heart of it: its relief, props, trees and water are kept, while its provinces are redrawn after the Atlas
(new towns, three coastline seams). Around it, the land of the extension is drawn from the
[Atlas of Bretonnia]({SITE}): the dukedoms, the mountains, the coasts, and, far to the south, the Dreaming Wood.
It is **built in public**: every step is logged in the [journal](docs/fr/JOURNAL.md).

{SEPARATEUR}

{_h2("green", "At a glance")}

| | |
|---|---|
| **Grid** | 560 × 825 hexes. Warhammer I's map is placed at (+120, +250), and the offset is even, as CAIME requires. |
| **Centre** | Warhammer I's terrain kept (relief, props, trees, water); provinces and three coastline seams follow the Atlas. It stays the playable area for now. |
| **Around** | New land from the Atlas: relief modelled from its heights, soils, forests, rivers and coasts, joined smoothly to Warhammer I's relief. |
| **The Dreaming Wood** | A mirrored reflection of Athel Loren in a sea of aether, south of the forest. |
| **Keys** | Map `saison_expanded_map`, campaign `saison_expanded`, new regions `saison_…`. The beta's keys are never reused. |
| **Status** | Work in progress, not playable yet: grid, regions, towns and minimap done; terrain of the extension under way (relief, rivers, the Dreaming Wood). See [PLAN](docs/fr/PLAN.md). Collaboration is open: issues, pull requests, and the Discord linked from [bretonia.dev]({SITE}). |

{SEPARATEUR}

{_h2("gold", "What is here")}

- [`outils/`](outils/): the Expanded tools. They build the grid, relief, joins and previews, and write the map
  declaration (`spec_expanded.py` → `map_spec_expanded.json`).
- [`map_spec_expanded.json`](map_spec_expanded.json): the map declaration (map, campaign, playable area, roads,
  regions).
- [`docs/fr/`](docs/fr/): the project page, the plan in phases, and the timestamped build journal (French).

**Not here, on purpose.** Everything derived from Warhammer I (map layers, terrain rasters, relief, previews, packs)
stays private. The tools also read the Atlas's geographic data, which belongs to the private site project and is not
provided. The shared build chain (terrain, data, pack) lives in the
[original Season repository]({GITHUB}the-season-of-revelation) (`02-scripts`, map profiles in `carte_config.py`).

{SEPARATEUR}

{_h2("red", "Legal")}

Warhammer and all related names belong to **Games Workshop**; Total War: WARHAMMER to **Creative Assembly** and
**SEGA**. Non-commercial fan project, not affiliated with or endorsed by them. Our code: [MIT licence](LICENSE); see
[NOTICE](NOTICE.md).
"""


def readme_expanded_fr():
    return f"""<p align="center"><img src="docs/art/banner-fr.svg" width="100%" alt="La Saison de la Révélation : Expanded"></p>

<p align="center">
<a href="{SITE}"><b>Atlas de Bretonnie</b></a> ·
<a href="{GITHUB}the-season-of-revelation"><b>La Saison originale</b></a> ·
<a href="docs/fr/JOURNAL.md"><b>Journal du chantier</b></a> ·
<a href="README.md"><b>Read in English</b></a>
</p>

**La Saison de la Révélation : Expanded** agrandit la carte de la mini-campagne de Warhammer I à **toute la Bretonnie**.
La carte de Warhammer I en est le cœur : son relief, ses objets, ses arbres et ses eaux sont gardés, tandis que ses
provinces sont redessinées d'après l'Atlas (villes nouvelles, trois raccords de côte). Autour, la terre de l'extension est dessinée
d'après l'[Atlas de Bretonnie]({SITE}) : les duchés, les montagnes, les côtes et, loin au sud, le Bois Rêveur. Le
chantier est **construit en public** : chaque étape est dans le [journal](docs/fr/JOURNAL.md).

{SEPARATEUR}

{_h2("green", "D'un coup d'œil")}

| | |
|---|---|
| **Grille** | 560 × 825 hex. La carte de Warhammer I est placée en (+120, +250), un décalage pair comme CAIME l'exige. |
| **Au centre** | Le terrain de Warhammer I gardé (relief, objets, arbres, eaux) ; les provinces et trois raccords de côte suivent l'Atlas. Elle reste la zone jouable pour l'instant. |
| **Autour** | La terre de l'Atlas : relief modelé depuis ses altitudes, sols, forêts, rivières et côtes, raccordés en douceur au relief de Warhammer I. |
| **Le Bois Rêveur** | Le reflet d'Athel Loren en miroir, dans une mer d'éther, au sud de la forêt. |
| **Clés** | Carte `saison_expanded_map`, campagne `saison_expanded`, régions neuves `saison_…` ; jamais les clés de la bêta. |
| **État** | En chantier, pas encore jouable : grille, régions, villes et minicarte faites ; terrain de l'extension en cours (relief, rivières, Bois Rêveur). Voir le [PLAN](docs/fr/PLAN.md). Les collaborations sont ouvertes : issues, pull requests, et le Discord indiqué par [bretonia.dev]({SITE}). |

{SEPARATEUR}

{_h2("gold", "Ce qu'on trouve ici")}

- [`outils/`](outils/) : les outils d'Expanded. Ils font la grille, le relief, les raccords et les aperçus, et écrivent
  la déclaration de la carte (`spec_expanded.py` → `map_spec_expanded.json`).
- [`map_spec_expanded.json`](map_spec_expanded.json) : la déclaration de la carte.
- [`docs/fr/`](docs/fr/) : la page du chantier, le plan en phases, le journal horodaté.

**Absent, volontairement.** Tout ce qui dérive de Warhammer I (couches de carte, rasters de terrain, relief, aperçus,
packs) reste privé. Les outils lisent aussi les données géographiques de l'Atlas, qui appartiennent au projet privé du
site et ne sont pas fournies. La chaîne commune (terrain, données, pack) est dans le
[dépôt de la Saison originale]({GITHUB}the-season-of-revelation).

{SEPARATEUR}

{_h2("red", "Mentions")}

Warhammer et tous les noms associés appartiennent à **Games Workshop** ; Total War: WARHAMMER à **Creative Assembly**
et **SEGA**. Projet de fan non commercial, sans lien avec eux. Notre code : [licence MIT](LICENSE) ; voir la
[NOTICE](NOTICE.md).
"""


LICENCE = """MIT License

Copyright (c) 2026 LeyZee

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

NOTICE = """# Notice

**Unofficial, non-commercial fan project.** Not affiliated with, authorised or endorsed by Games Workshop, Creative
Assembly or SEGA.

- Warhammer, the Warhammer world, and all associated names, characters, places and imagery are © and ™ **Games
  Workshop Limited**.
- Total War, Total War: WARHAMMER and their content are © **Creative Assembly** and **SEGA**. *The Season of
  Revelation* (Total War: WARHAMMER, *Realm of the Wood Elves*) is their work: its map, its story and its assets.

## What the MIT licence covers

Only the code and documentation **written for this project**: the Python tools, the Lua campaign scripts, our game-data
lots, and our own texts.

It does **not** cover names, quotes or game data that belong to Games Workshop or Creative Assembly and appear in our
texts or tables (for example the names of lords and places, and a few in-game quotes). Those remain theirs.

## No game assets

This repository contains **no file from Warhammer I or Warhammer III**: no models, textures, terrain, start position,
database extract or pack. The tools read **your own** installed copies of the games and their Assembly Kits. The
playable mod pack, which contains converted Warhammer I files, is never distributed here.

## Third-party tools

The build uses Creative Assembly's Assembly Kit (under its own terms), RPFM, and the Campaign Map Toolkit (CAIME, under
its own EULA). None of them is included here.
"""

GITIGNORE = """# machine settings (never shared)
atelier_local.json
# Python
__pycache__/
*.pyc
# game files and dumps: never in this repository
*.pack
*.esf
*.mdmp
*.dds
*.rigid_model_v2
*.wsmodel
# workshop folders that hold Warhammer I extractions or local evidence
03-references/
05-journal/
99-archives/
"""

EXEMPLE_LOCAL = """{
  "ATELIER": "C:/TotalWar-CampaignMap",
  "WH3": "C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III",
  "WH1": "C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER"
}
"""


# ---------------------------------------------------------------------------------------------------------------------
# Contenu
# ---------------------------------------------------------------------------------------------------------------------

def contenu_saison():
    """(source, chemin dans le dépôt) pour la Saison : liste blanche et audit de exporter_partageable."""
    fichiers, ecartes = [], []
    for source, relatif, categorie in EXP.candidats():
        verdict = EXP.auditer(source, categorie)
        if verdict:
            ecartes.append((relatif, verdict[1]))
            continue
        relatif = relatif.replace("\\", "/")
        if categorie == "lua":
            cible = "04-projets/saison-des-revelations/" + relatif
        elif categorie == "textes":
            cible = "04-projets/saison-des-revelations/" + relatif
        elif relatif == "MODDERS-EN-draft.md":
            cible = "MODDERS.md"
        elif categorie == "doc":
            cible = "docs/atelier/" + ("ORGANISATION.md" if relatif == "README.md" else relatif)
        else:
            cible = relatif
        fichiers.append((source, cible))
    return fichiers, ecartes


def contenu_expanded():
    """(source, chemin dans le dépôt) pour Expanded : la liste blanche de la construction, rien d'autre."""
    fichiers = [(os.path.join(EXPANDED, n), "docs/fr/" + ("README-chantier.md" if n == "README.md" else n))
                for n in ("README.md", "PLAN.md", "JOURNAL.md")]
    fichiers.append((os.path.join(EXPANDED, "map_spec_expanded.json"), "map_spec_expanded.json"))
    fichiers += [(p, "outils/" + os.path.basename(p)) for p in sorted(glob.glob(os.path.join(EXPANDED, "outils", "*.py")))]
    return fichiers, []


def auditer_copie(source, texte):
    """Audit du texte ANONYMISÉ : données sensibles, restes de chemins personnels, taille."""
    if len(texte.encode("utf-8")) > EXP.TAILLE_MAX:
        return "plus de 2 Mo"
    for nom, motif in EXP.SENSIBLE:
        m = motif.search(texte)
        if m:
            return f"donnée sensible possible ({nom}, ligne {texte.count(chr(10), 0, m.start()) + 1})"
    m = RESTE_PERSONNEL.search(texte)
    if m:
        return f"reste personnel « {m.group(0)} » (ligne {texte.count(chr(10), 0, m.start()) + 1})"
    return None


def generer(nom, apply):
    d = DEPOTS[nom]
    fichiers, ecartes = contenu_saison() if nom == "saison" else contenu_expanded()
    copies, refuses = [], list(ecartes)
    for source, cible in fichiers:
        if not os.path.isfile(source):
            refuses.append((cible, "source absente"))
            continue
        texte = anonymiser(open(source, encoding="utf-8", errors="strict").read())
        raison = auditer_copie(source, texte)
        if raison:
            refuses.append((cible, raison))
        else:
            copies.append((cible, texte))
    en, fr = (readme_saison_en(), readme_saison_fr()) if nom == "saison" else (readme_expanded_en(), readme_expanded_fr())
    produits = {"README.md": en, "README.fr.md": fr, "LICENSE": LICENCE, "NOTICE.md": NOTICE,
                ".gitignore": GITIGNORE + f"# marque de ce générateur\n{MARQUE}\n",
                ".gitattributes": "* text=auto eol=lf\n*.svg text eol=lf\n"}
    if nom == "saison":
        produits["atelier_local.json.example"] = EXEMPLE_LOCAL
    titres = {
        "saison": (("The Season of Revelation", "Warhammer I’s Wood Elves mini-campaign, rebuilt for Total War: WARHAMMER III",
                    "Warhammer I’s map, stone for stone  ·  Warhammer III gameplay  ·  Ten legendary lords"),
                   ("La Saison de la Révélation", "La mini-campagne des Elfes sylvains de Warhammer I, refaite pour Warhammer III",
                    "La carte de Warhammer I, pierre pour pierre  ·  Le gameplay de Warhammer III  ·  Dix seigneurs")),
        "expanded": (("The Season of Revelation: Expanded", "Warhammer I’s map at the heart of all Bretonnia",
                      "Drawn from the Atlas of Bretonnia  ·  Built in public  ·  Work in progress"),
                     ("La Saison de la Révélation : Expanded", "La carte de Warhammer I au cœur de toute la Bretonnie",
                      "D’après l’Atlas de Bretonnie  ·  Construit en public  ·  En chantier")),
    }[nom]
    mention_en = "A fan project  ·  non-commercial  ·  not affiliated with Games Workshop or Creative Assembly"
    mention_fr = "Projet de fan  ·  non commercial  ·  sans lien avec Games Workshop ni Creative Assembly"
    art = {"docs/art/banner.svg": banniere(*titres[0], mention_en), "docs/art/banner-fr.svg": banniere(*titres[1], mention_fr),
           "docs/art/divider.svg": separateur()}
    for teinte, nom_fichier in (("rouge", "red"), ("vert", "green"), ("or", "gold"), ("gris", "grey"), ("bronze", "bronze")):
        art[f"docs/art/seal-{nom_fichier}.svg"] = sceau(teinte)
    produits.update(art)

    print(f"\n=== {d['nom']} -> {d['dossier']}")
    print(f"copiés : {len(copies)} ; produits : {len(produits)} ; écartés : {len(refuses)}")
    for cible, raison in refuses:
        print(f"   x {cible} : {raison}")
    tailles = {k: len(v.encode('utf-8')) for k, v in art.items()}
    print("   art :", ", ".join(f"{os.path.basename(k)} {v // 1024} Ko" for k, v in tailles.items()))
    if not apply:
        return d["dossier"], copies, produits
    dossier = d["dossier"]
    if os.path.exists(dossier):
        if not os.path.isfile(os.path.join(dossier, MARQUE)):
            raise SystemExit(f"{dossier} existe et n'a pas été fait par ce script : rien n'est écrit")
        for entree in os.listdir(dossier):          # régénération : tout sauf l'historique git
            if entree == ".git":
                continue
            chemin = os.path.join(dossier, entree)
            shutil.rmtree(chemin) if os.path.isdir(chemin) else os.remove(chemin)
    os.makedirs(dossier, exist_ok=True)
    for cible, texte in copies + list(produits.items()):
        chemin = os.path.join(dossier, *cible.split("/"))
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8", newline="\n") as f:
            f.write(texte)
    open(os.path.join(dossier, MARQUE), "w", encoding="utf-8").write("généré par 02-scripts/preparer_depots_publics.py\n")
    print(f"écrit : {dossier}")
    return dossier, copies, produits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--depot", choices=sorted(DEPOTS))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    for nom in ([a.depot] if a.depot else list(DEPOTS)):
        generer(nom, a.apply)
    if not a.apply:
        print("\nà blanc : rien n'est écrit (--apply) ; rien n'est jamais poussé par ce script")
    return 0


if __name__ == "__main__":
    sys.exit(main())
