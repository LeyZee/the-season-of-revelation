#!/usr/bin/env python3
"""
startpos_manuel.py - construire un startpos **sans passer par RPFM**, en écrivant soi-même le
script que le jeu exécute.

Pourquoi : le 20.09.2026 au soir, `build_starpos` de RPFM plante le jeu même sur une campagne
**vanilla**, depuis un pack vide (témoin, `startpos_essai.py`). Le `user.script.txt` que RPFM
écrit est celui-ci, 121 octets ::

    <vide>
        mod <pack>;
        process_campaign_startpos <campagne> ;
        <vide>
        quit_after_campaign_processing;

Deux emplacements du gabarit restent vides, dont celui de
`add_working_directory assembly_kit\\working_data;` — et les tables `start_pos_*` ne vivent que
dans l'Assembly Kit, jamais dans un pack. D'où l'essai : écrire le script **avec** cette ligne et
lancer le jeu nous-mêmes, exactement comme RPFM le fait (`steam_appid.txt` posé à côté de
`Warhammer3.exe`, puis l'exécutable lancé directement).

Le script écrit est sauvegardé dans `05-journal\\<journal>\\` avec la sortie, pour que l'essai soit
rejouable et comparable.

Usage :
    python startpos_manuel.py --campagne wh3_main_prologue --pack temoin_startpos.pack
    python startpos_manuel.py --campagne wh3_main_prologue --pack temoin_startpos.pack --sans-working-dir
        (le contre-essai : le même script sans la ligne, pour vérifier que c'est bien elle)
"""

import argparse
import os
import subprocess
import sys
import time

JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
EXE = os.path.join(JEU, "Warhammer3.exe")
RACINE_CA = os.path.join(os.environ["APPDATA"], "The Creative Assembly")
# `-sptest` fait basculer le jeu sur un profil separe : il n'ecrit plus dans `Warhammer3` mais
# dans `Warhammer3_autotest` (verifie le 20.09.2026 : le dossier nait au premier lancement, et
# le jeu y charge en plus `script\_lib\mod\qa_console.lua`). Le `user.script.txt` doit donc y
# aller aussi, sinon le jeu n'en lit aucun.
CA = os.path.join(RACINE_CA, "Warhammer3")
SCRIPT = os.path.join(CA, "scripts", "user.script.txt")
LOGS, CRASH = os.path.join(CA, "logs"), os.path.join(CA, "crash_report")
APPARITION, EXECUTION = 180, 900

# Ce que BOB passe au jeu (chaines de bob_campaign.modder.x64.dll) : le dossier des campagnes
# exportees, en **relatif** (`../raw_data/EmpireDesignData/campaigns/` depuis assembly_kit\binaries).
# Ici le jeu est lance depuis sa racine, donc le meme dossier s'ecrit sans `..`.
# Un chemin absolu ne marche pas : il contient des espaces et le parseur de commandes du jeu
# coupe dessus (essai du 20.09.2026 21 h 03 : le jeu sort au bout de 13 s sans rien faire).
DEFAUT_STARTPOS_DIR = "assembly_kit/raw_data/EmpireDesignData/campaigns/"


def jeu_tourne():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Warhammer3.exe", "/NH"],
                         capture_output=True, text=True).stdout
    return "Warhammer3.exe" in out


def empreinte():
    out = {}
    for d in (LOGS, CRASH, os.path.join(JEU, "data")):
        for root, _, names in os.walk(d):
            for n in names:
                p = os.path.join(root, n)
                try:
                    out[p] = (os.path.getmtime(p), os.path.getsize(p))
                except OSError:
                    pass
    return out


def attendre(condition, limite, quoi):
    t0 = time.time()
    while time.time() - t0 < limite:
        if condition():
            return time.time() - t0
        time.sleep(3)
    print(f"  !! {quoi} : rien après {limite} s")
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campagne", required=True)
    ap.add_argument("--pack", action="append", default=None,
                    help="nom d'un .pack de <jeu>\\data\\ ; repetable, une ligne `mod` par pack. "
                         "Omis : aucune ligne `mod` (temoin sur une campagne vanilla)")
    ap.add_argument("--sans-working-dir", action="store_true")
    ap.add_argument("--ai-map-data", action="store_true", help="ajoute process_campaign_ai_map_data;")
    ap.add_argument("--arg", action="append", default=None,
                    help="argument de ligne de commande passe a Warhammer3.exe ; repetable. "
                         "`-sptest` est une option du jeu, relevee dans son binaire juste a cote "
                         "de `process_campaign_startpos`, `appdata_folder` et `branch_profile`")
    ap.add_argument("--startpos-dir", nargs="?", const=DEFAUT_STARTPOS_DIR, default=None,
                    help="ajoute set_campaign_startpos_working_directory <dossier> ; sans valeur, "
                         "prend le dossier des campagnes exportees par BOB")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    global CA, SCRIPT, LOGS, CRASH
    if a.arg and "-sptest" in a.arg:
        CA = os.path.join(RACINE_CA, "Warhammer3_autotest")
        SCRIPT = os.path.join(CA, "scripts", "user.script.txt")
        LOGS, CRASH = os.path.join(CA, "logs"), os.path.join(CA, "crash_report")
        print("-sptest : profil", CA)

    if jeu_tourne():
        print("!! Warhammer 3 tourne déjà : le fermer d'abord")
        return 2
    for p in (a.pack or []):
        if not os.path.exists(os.path.join(JEU, "data", p)):
            print(f"!! {p} absent de <jeu>\\data\\")
            return 2

    # Un pack de <jeu>\data\ n'est PAS charge tout seul : seule une ligne `mod` le charge
    # (modified.log le dit « unknown file » sinon). Sans --pack, le jeu tourne donc en vanilla.
    lignes = [f"    mod {p};" for p in (a.pack or [])]
    if not a.sans_working_dir:
        lignes.append("    add_working_directory assembly_kit\\working_data;")
    if a.startpos_dir:
        lignes.append(f"    set_campaign_startpos_working_directory {a.startpos_dir};")
    lignes.append(f"    process_campaign_startpos {a.campagne};")
    if a.ai_map_data:
        lignes.append("    process_campaign_ai_map_data;")
    lignes.append("    quit_after_campaign_processing;")
    contenu = "\n".join(lignes) + "\n"

    os.makedirs(os.path.dirname(SCRIPT), exist_ok=True)
    with open(SCRIPT, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    print("user.script.txt écrit :")
    for l in contenu.splitlines():
        print("   ", l)

    # le jeu ne doit pas repasser par Steam : le fichier est déjà là, on le vérifie seulement
    appid = os.path.join(JEU, "steam_appid.txt")
    print("steam_appid.txt :", open(appid).read().strip() if os.path.exists(appid) else "ABSENT")

    avant = empreinte()
    commande = [EXE] + (a.arg or [])
    print("commande :", " ".join(commande[1:]) or "(aucun argument)")
    subprocess.Popen(commande, cwd=JEU, close_fds=True)
    d = attendre(jeu_tourne, APPARITION, "le jeu n'a pas démarré")
    if d is None:
        return 3
    print(f"  jeu démarré après {d:.0f} s")
    d = attendre(lambda: not jeu_tourne(), EXECUTION, "le jeu ne s'est pas arrêté")
    if d is None:
        return 3
    print(f"  jeu terminé après {d:.0f} s")

    print("\n=== ce que cet essai a écrit ===")
    apres, vu = empreinte(), False
    for p, v in sorted(apres.items(), key=lambda kv: kv[1][0]):
        if avant.get(p) != v:
            vu = True
            print(f"    {time.strftime('%H:%M:%S', time.localtime(v[0]))}  {v[1]:>12d}  "
                  f"{p.replace(CA, '<CA>').replace(JEU, '<JEU>')}")
    if not vu:
        print("    (rien)")
    print("  rapport de plantage :",
          "OUI" if any("crash_report" in p and avant.get(p) != v for p, v in apres.items()) else "non")
    return 0


if __name__ == "__main__":
    sys.exit(main())
