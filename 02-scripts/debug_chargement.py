#!/usr/bin/env python3
"""
debug_chargement.py - lancer Warhammer 3 sous `cdb` pour voir **quelle résolution échoue** quand le jeu
construit la campagne, pendant que Charles fait lui-même le chemin dans le menu.

Pourquoi (21.09.2026, 19 h 45) : après le correctif des emplacements, le jeu plante plus loin
(`Warhammer3.exe+0x255EF20`, lecture à `0xD8A`). Le vidage montre que la liste des factions de l'IA de
campagne (CAI_WORLD, conteneur +0x110) contient encore l'**identifiant** de la faction (2 = Orion) au
lieu du pointeur : la passe de résolution des objets de l'IA ne l'a pas converti. Cette passe
(`CAI_WORLD` vtable +8, `Warhammer3+0x26EFE2C`) enchaîne les conteneurs et **abandonne au premier
échec** ; le premier conteneur est celui des théâtres, le second celui des factions. Le vidage ne
dit pas quelle étape a échoué ; ce script le fait dire au jeu.

Ce qui est journalisé (points d'arrêt qui écrivent puis continuent, rien n'est modifié) :
- [W00] à [W23] : chaque étape de CAI_WORLD::resolve qui **échoue** (saut vers l'échec) ;
- [WOK] / [WKO] : fin de CAI_WORLD::resolve, succès ou échec ;
- [T..] : résolution du théâtre (clé cherchée, liste des théâtres, résultat) ;
- [F..] : résolution de chaque CAI_FACTION (identifiant, échec) ;
- [H] : réglage « HUMAN » de la faction du joueur (là où le jeu plante ensuite) ;
- l'exception de seconde chance : registres, pile, vidage `plantage.dmp`, puis le jeu est fermé.

Le jeu est lancé sans argument, depuis son dossier, comme le fait `startpos_manuel.py` ;
`user.script.txt` doit contenir la ligne `mod saison_des_revelations.pack;` et rien qui ferme le jeu.
**Personne d'autre que Charles ne clique dans le jeu** : le script attend qu'il ait fait le chemin
(Nouvelle campagne > La Saison des Révélations > Orion > Commencer) et que le jeu plante ou soit fermé.

Usage :
    python debug_chargement.py            # lance le jeu sous cdb et attend (30 min au plus)
    python debug_chargement.py --essai    # écrit seulement les commandes cdb, sans lancer
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
import time

JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
EXE = os.path.join(JEU, "Warhammer3.exe")
SCRIPT = os.path.join(os.environ["APPDATA"], "The Creative Assembly", "Warhammer3", "scripts", "user.script.txt")
JOURNAL = r"C:\TotalWar-CampaignMap\05-journal\2026-09-21-phase-3-terrain\debug-chargement"
# Nom du module dans un processus vivant : l'exe s'appelle en interne `warhammer3.retail.x64.exe`
# (dans un vidage relu par `cdb -z`, le même module s'appelle `Warhammer3`, d'après le nom du fichier).
# Premier essai du 21.09.2026, 19 h 43 : `bu Warhammer3+...` n'a posé aucun point d'arrêt.
MODULE = "warhammer3_retail_x64"

# CAI_WORLD::resolve (Warhammer3+0x26EFE2C) : les sauts vers l'échec (0x26F0463), dans l'ordre du code.
# Relevés dans le désassemblage du 21.09.2026 (patch 8.1) ; le script vérifie les octets avant de lancer.
SAUTS_ECHEC_MONDE = [0x26efe55, 0x26efe90, 0x26efebf, 0x26efeee, 0x26eff1d, 0x26eff4c, 0x26eff7b,
                     0x26effaa, 0x26effd9, 0x26f0008, 0x26f0034, 0x26f0054, 0x26f006c, 0x26f0093,
                     0x26f00c2, 0x26f00f7, 0x26f030c, 0x26f033b, 0x26f036a, 0x26f0399, 0x26f03c8,
                     0x26f03f7, 0x26f0422, 0x26f044d]
OCTETS_ATTENDUS = {0x26efe2c: "48895c2408", 0x26ef97c: "48895c2408", 0x26ee770: "48895c2408",
                   0x2574470: "48895c2408", 0x26f045f: "b001", 0x26f0463: "32c0"}


def cdb():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-AppxPackage Microsoft.WinDbg* | Select-Object -First 1).InstallLocation"],
                       capture_output=True, text=True)
    chemin = os.path.join(r.stdout.strip(), "amd64", "cdb.exe")
    if not os.path.isfile(chemin):
        sys.exit("cdb.exe introuvable : installer WinDbg (Microsoft Store)")
    return chemin


def verifier_exe():
    """Les adresses sont celles du patch 8.1 : on refuse de lancer si le code a changé."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lire_dll as L
    b = open(EXE, "rb").read()
    base, secs, opt = L.sections(b)
    for rva, attendu in OCTETS_ATTENDUS.items():
        off = L.rva_vers_offset(secs, rva)
        vu = b[off:off + len(attendu) // 2].hex()
        if vu != attendu:
            sys.exit(f"Warhammer3.exe a changé : octets {vu} à +0x{rva:x} au lieu de {attendu}")
    for rva in SAUTS_ECHEC_MONDE:
        off = L.rva_vers_offset(secs, rva)
        if b[off] not in (0x0F, 0x74):
            sys.exit(f"Warhammer3.exe a changé : pas de saut conditionnel à +0x{rva:x}")


def commandes(dossier):
    vidage = os.path.join(dossier, "plantage.dmp").replace("\\", "/")
    p = lambda texte: texte.replace('"', '\\"')                         # guillemets dans une commande de point d'arrêt
    l = [f'sxd -c2 ".printf \\"EXCEPTION SECONDE CHANCE\\\\n\\"; r; k 30; .dump /m {vidage}; .kill; q" av',
         "sxd eh", "sxd ld", "sxd ud", "sxd ct", "sxd et", "sxd cpr", "sxd epr"]
    for i, rva in enumerate(SAUTS_ECHEC_MONDE):
        l.append(f'bu {MODULE}+0x{rva:x} ".if (@zf == 1) {{ .printf \\"[W{i:02d}] CAI_WORLD resolve : '
                 f'echec a l etape {i} (+0x{rva:x})\\\\n\\" }}; gc"')
    l += [
        f'bu {MODULE}+0x26efe2c ".printf \\"[W] CAI_WORLD resolve : debut this=%p\\\\n\\", @rcx; gc"',
        f'bu {MODULE}+0x26f045f ".printf \\"[WOK] CAI_WORLD resolve : succes\\\\n\\"; gc"',
        f'bu {MODULE}+0x26f0463 ".printf \\"[WKO] CAI_WORLD resolve : ECHEC\\\\n\\"; gc"',
        # théâtre : clé cherchée et liste, juste avant la recherche (rcx = porteur de la liste, rdx = clé)
        f'bu {MODULE}+0x26ef9c7 ".printf \\"[T1] theatre : liste %p, %d element(s) ; cle :\\\\n\\", '
        'poi(poi(@rcx)+0x28), dwo(poi(@rcx)+0x24); dq @rdx L2; da @rdx; da poi(@rdx+8); '
        'r $t0 = poi(poi(poi(@rcx)+0x28)); .if (@$t0 != 0) { .printf \\"[T1] premier theatre :\\\\n\\"; '
        'dq @$t0+0x18 L2; da @$t0+0x18; da poi(@$t0+0x20) }; gc"',
        f'bu {MODULE}+0x26ef9cc ".printf \\"[T2] theatre : resultat de la recherche %p\\\\n\\", @rax; gc"',
        f'bu {MODULE}+0x26efab0 ".printf \\"[T3] theatre : resolu\\\\n\\"; gc"',
        f'bu {MODULE}+0x26efab4 ".printf \\"[T4] theatre : ECHEC\\\\n\\"; gc"',
        # factions de l'IA
        f'bu {MODULE}+0x26ee770 ".printf \\"[F1] CAI_FACTION resolve : id %p\\\\n\\", poi(@rcx+0x168); gc"',
        f'bu {MODULE}+0x26ee8e3 ".printf \\"[F2] CAI_FACTION resolve : ECHEC (valeur %p)\\\\n\\", '
        'poi(@rbx+0x168); gc"',
        # réglage du joueur humain (le plantage vient juste après)
        f'bu {MODULE}+0x2574470 ".printf \\"[H] reglage HUMAN de la faction %p\\\\n\\", @rcx; gc"',
        "g",
    ]
    return "\n".join(l) + "\n"


def jeu_tourne():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Warhammer3.exe", "/NH"],
                         capture_output=True, text=True).stdout
    return "Warhammer3.exe" in out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", action="store_true", help="écrire les commandes sans lancer le jeu")
    ap.add_argument("--duree", type=int, default=1800, help="attente maximale en secondes")
    ap.add_argument("--arret-apres", type=int, default=0,
                    help="fermer le jeu au bout de N secondes s'il n'a pas planté (0 : attendre --duree)")
    ap.add_argument("--commandes", default=None,
                    help="fichier de points d'arrêt cdb à poser à la place de ceux du script (une commande par "
                         "ligne ; la gestion des exceptions et le `g` final restent ceux du script)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    verifier_exe()
    contenu = io.open(SCRIPT, encoding="utf-8", errors="replace").read() if os.path.exists(SCRIPT) else ""
    if "mod saison_des_revelations.pack;" not in contenu or "quit_after" in contenu:
        sys.exit(f"user.script.txt inattendu (il faut la ligne du mod et rien qui ferme le jeu) :\n{contenu}")
    if jeu_tourne():
        sys.exit("Warhammer 3 tourne déjà : le fermer d'abord")
    dossier = os.path.join(JOURNAL, time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dossier)
    texte = commandes(dossier)
    if a.commandes:
        lignes = texte.splitlines()
        garde = [l for l in lignes if l.startswith("sxd")]
        propres = [l for l in io.open(a.commandes, encoding="ascii").read().splitlines() if l.strip()]
        texte = "\n".join(garde + propres + ["g"]) + "\n"
    with open(os.path.join(dossier, "commandes.cdb"), "w", encoding="ascii", newline="\n") as f:
        f.write(texte)
    print("commandes :", os.path.join(dossier, "commandes.cdb"))
    if a.essai:
        return 0

    log = os.path.join(dossier, "cdb.log")
    commande = [cdb(), "-G", "-hd", "-logo", log, "-cf", os.path.join(dossier, "commandes.cdb"), EXE]
    print("jeu lancé sous cdb", time.strftime("%H:%M:%S"), "— à Charles de faire le chemin dans le menu")
    t0 = time.time()
    limite = a.arret_apres or a.duree
    try:
        subprocess.run(commande, cwd=JEU, timeout=limite, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        if a.arret_apres:
            # pas de plantage dans le délai : le chargement a passé ; on ferme le jeu (cdb suit)
            print(f"pas de plantage en {limite} s : le jeu est fermé")
            subprocess.run(["taskkill", "/IM", "Warhammer3.exe", "/F"], capture_output=True)
            time.sleep(5)
            subprocess.run(["taskkill", "/IM", "cdb.exe", "/F"], capture_output=True)
        else:
            print(f"!! rien après {a.duree} s : le jeu tourne peut-être encore (le fermer)")
    print(f"fin après {int(time.time() - t0)} s")
    texte = io.open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
    for ligne in texte.splitlines():
        if ligne.startswith(("[", "EXCEPTION")) or "Access violation" in ligne:
            print("  ", ligne)
    print("journal complet :", log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
