#!/usr/bin/env python3
"""
affichage_carte.py - les fichiers d'affichage propres à la carte (flèches, frontières, rivières, commerce, tunnels,
ciel) et la carte stratégique de WH1, rangés à l'arborescence du pack pour `build_pack.py`.

Pourquoi (22.09.2026, 23 h 35) : l'audit de fidélité (`05-journal\\2026-09-22-phase-4\\audit-fidelite.md`) a montré
que notre carte n'a aucun des fichiers `campaign_maps/<carte>/display/...` que WH1 livrait pour elle et que chaque
carte de CA dans WH3 livre aussi (le prologue en a 17). Charles, en jeu : la portée de déplacement ne s'affiche pas
quand il sélectionne un personnage, et des « carrés lumineux » apparaissent dans le ciel. Et la carte stratégique
était la version anglaise de `data.pack` (« Duchy of Bordeleaux »), alors que WH1 livre la française dans
`local_fr.pack` (« Duché de Bordeleaux »).

Relevé (22.09.2026) :
- les textures d'affichage de WH1 et du prologue de WH3 ont le même format (DDS DXT5, mêmes tailles), la plupart sont
  identiques octet pour octet (les flèches de WH3 diffèrent un peu) : on prend celles de WH1 ;
- le ciel : le `.rigid_model_v2` de WH1 est identique à celui du prologue ; WH3 veut en plus un
  `campaign_skybox.wsmodel`, qui chez CA pose un modèle factice et le matériau `materials/skyboxes/
  wh_skydome_campaign.xml.material` (lu dans le prologue, compressé en LZ4) : on écrit le même ;
- la carte stratégique française est dans `local_fr.pack` au chemin à barre oblique initiale.

Sorties :
    04-projets\\saison-des-revelations\\affichage-carte\\     (pack principal, carte stratégique en français)
    04-projets\\saison-des-revelations\\affichage-carte-en\\  (pack anglais : la carte stratégique en anglais)

Usage :
    python affichage_carte.py            # dit ce qu'il écrirait
    python affichage_carte.py --apply    # écrit les deux dossiers
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contenu_pack as CP                                            # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
WH1_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\data"
WH3_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
CARTE = "wh_dlc05_wood_elves_map_1"
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "affichage-carte")
SORTIE_EN = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "affichage-carte-en")
AFFICHAGE = ["tunnel_path.dds",
             "arrows/arrow.dds", "arrows/arrow_head.dds", "arrows/arrow_reinforce.dds", "arrows/arrow_shaft.dds",
             "borders/textures/border_diffuse.dds", "borders/textures/border_dotted_diffuse.dds",
             "borders/textures/border_internal_diffuse.dds",
             "rivers/textures/river_diffuse.dds", "rivers/textures/river_froth.dds",
             "rivers/textures/river_moving_normal.dds", "rivers/textures/river_static_normal.dds",
             "skybox/campaign_skybox.rigid_model_v2",
             "skybox/textures/campaign_skybox_diffuse.dds", "skybox/textures/campaign_skybox_normal.dds",
             "trade/textures/dotted_line_trade.dds"]
# le .wsmodel du ciel du prologue de WH3, tel quel (models_other.pack, LZ4)
WSMODEL_CIEL = ("<model>\n\n\t<geometry>vfx\\models\\dummy_model.rigid_model_v2</geometry>\n\n\t<materials>\n\n"
                "\t\t<material>materials/skyboxes/wh_skydome_campaign.xml.material</material>\n\n\t</materials>\n\n"
                "</model>")
CARTE_STRAT = f"campaign_maps/{CARTE}/wh_dlc05_wood_elves_map.png"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    data = os.path.join(WH1_DATA, "data.pack")
    fichiers = {}                                       # (dossier de sortie, chemin interne) -> octets
    for f in AFFICHAGE:
        b = CP.extraire(data, f"campaign_maps/{CARTE}/display/{f}")
        if not b:
            raise SystemExit(f"absent de data.pack de WH1 : {f}")
        fichiers[(SORTIE, f"campaign_maps/{CARTE}/display/{f}")] = b
    fichiers[(SORTIE, f"campaign_maps/{CARTE}/display/skybox/campaign_skybox.wsmodel")] = WSMODEL_CIEL.encode("utf-8")
    fr = CP.extraire(os.path.join(WH1_DATA, "local_fr.pack"), "/" + CARTE_STRAT)
    en = CP.extraire(data, CARTE_STRAT)
    if not fr or not en:
        raise SystemExit("carte stratégique introuvable (local_fr.pack ou data.pack de WH1)")
    fichiers[(SORTIE, CARTE_STRAT)] = fr
    fichiers[(SORTIE_EN, CARTE_STRAT)] = en
    # garde : aucun chemin qui existe déjà dans les packs de CA de WH3
    jeu = CP.chemins_du_jeu(WH3_DATA)
    for (_, c), _ in fichiers.items():
        if c.lower() in jeu:
            raise SystemExit(f"chemin déjà présent dans WH3, refusé : {c}")
    for (d, c), b in sorted(fichiers.items()):
        print(f"{'écrit' if a.apply else 'à écrire'} : {os.path.basename(d)}\\{c}  ({len(b)} octets, "
              f"sha1 {hashlib.sha1(b).hexdigest()[:10]})")
        if a.apply:
            p = os.path.join(d, *c.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(b)
    print(f"{len(fichiers)} fichiers ; {'écrits' if a.apply else 'rien écrit (--apply pour écrire)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
