#!/usr/bin/env python3
"""
essai_tours_auto.py - parties automatiques longues de « La Saison des Révélations » : l'IA joue toutes les factions,
le jeu tourne sous `cdb`, le script surveille les tours, les erreurs de script, les plantages et les gels.

Pourquoi (23.09.2026, mission de Charles : « qu'on puisse faire une centaine de tours sans problème … toutes les
factions ») : un essai à la main ne dépasse pas quelques tours ; une partie de 100 à 200 tours par seigneur ne se fait
qu'en automatique.

Comment :
- un PACK D'ESSAI SÉPARÉ, `<jeu>\\data\\zz_saison_essai_auto.pack`, recréé à chaque essai et retiré à la fin, porte
  deux scripts (`04-projets\\saison-des-revelations\\essai-auto\\script\\`) :
  * menu : lancement PAR L'INTERFACE comme un joueur (Campagne, Nouvelle campagne, notre campagne, race, seigneur,
    Commencer : GUIDE § 15 n° 131 ; `frontend.start_campaign` referme notre campagne, erreur 128), journal propre
    `<jeu>\\saison_essai_menu.txt` ;
  * campagne : `_G.saison_essai_auto = true` (nos scripts coupent intros, cinématiques et répliques : interrupteur de la
    session « IA et modding 3D », `saison_en_essai_auto()` de required.lua), « Continuer » de l'écran de chargement,
    une ligne « [ESSAI] tour N » par round, fin de tour de la faction locale 5 s après chaque round (notifications
    passées une à une, erreur 137 ; BLOCAGE si le tour reste ouvert 60 s après), bilan des neuf factions jouables tous
    les 10 tours avec compteurs (recrues, bâtiments, batailles, conquêtes, missions) ;
- `user.script.txt` : `mod saison_des_revelations.pack;`, `mod zz_saison_essai_auto.pack;`, `all_players_ai;`
  (commande du jeu « Enable all players ai » ; `--sans-ia` pour le mode joueur) ; celui de Charles est gardé et remis ;
- plantage : `cdb` écrit un vidage à l'exception de seconde chance et ferme le jeu ; gel (ni tour ni ligne de journal
  pendant `--gel` minutes) : vidage non invasif (`cdb -pv`, piles de tous les fils) puis fermeture ;
- tout va dans `05-journal\\2026-09-23-essais-auto\\<horodatage>-<seigneur>\\` : `bilan.json`, copie du script_log,
  `cdb.log`, vidages, nouveaux fichiers de `crash_report\\`.

**Le jeu prend l'écran : Charles doit être prévenu avant chaque lancement et ne pas cliquer dedans.** Steam doit
tourner (sinon le jeu sort en 6 s), le jeu et Terry fermés.

Usage :
    python essai_tours_auto.py --seigneur orion --tours 5            # premier essai court
    python essai_tours_auto.py --seigneur tous --tours 150          # les neuf, l'un après l'autre
    python essai_tours_auto.py --seigneur grom --essai              # prépare seulement (pack, scripts), sans lancer
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from rpfm_mcp import session, call, text                            # noqa: E402

ATELIER = os.path.dirname(ICI)
JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
EXE = os.path.join(JEU, "Warhammer3.exe")
DATA = os.path.join(JEU, "data")
CA = os.path.join(os.environ["APPDATA"], "The Creative Assembly", "Warhammer3")
SCRIPT = os.path.join(CA, "scripts", "user.script.txt")
CRASH = os.path.join(CA, "crash_report")
SOURCES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "essai-auto")
JOURNAL = os.path.join(ATELIER, "05-journal", "2026-09-23-essais-auto")
PACK_ESSAI = "zz_saison_essai_auto.pack"
PACK_JEU = "saison_des_revelations.pack"
# journal propre du script de menu (le script_log du menu est écrasé si la campagne démarre dans la même minute)
MENU = os.path.join(JEU, "saison_essai_menu.txt")
CAMPAGNE = "wh_dlc05_wood_elves"
# --armees : pose `_G.saison_essai_armees` (armées des finales et des Échos posées tour à tour, session « IA et modding 3D »)
ARMEES = False
# --sans-dlc : pose `_G.saison_essai_sans_dlc` (verrou du DLC éprouvé : joueur sans le DLC simulé, saison_verrou_dlc.lua)
SANS_DLC = False
# --sans-dlc-seigneur : pose `_G.saison_essai_sans_dlc_seigneur` (contenu de CA du seigneur joué simulé absent ; prendre un
# seigneur dont le produit n'est pas celui de la campagne : Grom, la Fée, les Sœurs…)
SANS_DLC_SEIGNEUR = False
# --menu-sans-dlc : pose `_G.saison_essai_menu_sans_dlc` au menu (plan B du verrou : bouton de lancement grisé ; le pilote
# ne peut pas lancer la campagne : conclure sur saison_choix_menu.txt)
MENU_SANS_DLC = False
# --neutre-vfx : le pack d'essai remplace les 6 effets de WH1 (effets-wh1\vfx) par des effets vides, pour savoir s'ils
# causent le plantage Warhammer3.exe+0x1A3DCFA (23.09.2026, 16 h : Durthu, Alberic, la Fée)
NEUTRE_VFX = False
# --pause-tour N : au round N, la fin de tour automatique s'arrête et la caméra se pose sur le chef de la faction
# locale ; le jeu reste ouvert pour que Charles regarde (le pilote attend --limite ; fermer le jeu termine l'essai)
PAUSE_TOUR = 0
# --delai-fin S : secondes avant la fin de tour automatique de la faction locale à chaque round (24.09.2026, erreur 210 :
# avec 5 s, la faction du joueur ne recrutait ni ne construisait sous `all_players_ai`)
DELAI_FIN = 5
# --ajout <dossier> : tout le contenu de essai-auto\<dossier>\ va dans le pack d'essai sous son chemin relatif (script
# d'essai d'une autre session, par exemple essai-auto\transfert\script\campaign\mod\...) ; répétable
AJOUTS = []
VIDAGE_COMPLET = False

# alias -> (faction, identifiant de départ du seigneur) ; identifiants : start_pos_characters, écrans de chargement de
# `saison_ecrans_de_chargement.lua` (le bouton du seigneur porte cet identifiant, propriété `lord_key`)
SEIGNEURS = {
    "orion": ("wh_dlc05_wef_wood_elves", "2140783885"),
    "durthu": ("wh_dlc05_wef_argwylon", "2140783843"),
    "alberic": ("wh_main_brt_bordeleaux", "2140783762"),
    "fee": ("wh_main_brt_carcassonne", "2140783791"),
    "morghur": ("wh_dlc05_bst_morghur_herd", "2140783911"),
    "duc": ("wh_main_vmp_mousillon", "2140784082"),
    "drycha": ("wh2_dlc16_wef_drycha", "2140783871"),
    "kemmler": ("wh2_dlc11_vmp_the_barrow_legion", "2140784200"),
    "grom": ("wh2_dlc15_grn_broken_axe", "2140783823"),
    "soeurs": ("wh2_dlc16_wef_sisters_of_twilight", "2140784201"),     # 24.09.2026, dixième seigneur
}

# durée d'un tour : horodatage du journal (« <166.1s> »), pas os.time() du jeu (pas de 128 s, 23.09.2026)
TOUR = re.compile(r"<([\d.]+)s>\s+\[ESSAI\] tour (\d+) ;")
# Preuves des essais ciblés (05-journal\2026-09-23-audits\essais-cibles.md, session « IA et modding 3D ») : lignes du
# journal de script qui prouvent qu'une fonction a tourné ; relevées dans le bilan (les 5 premières de chaque).
PREUVES = {"guerres_de_depart": "guerre de depart", "ducs_nommes": "ducs nommes selon le lore",
           "racines_du_monde": "Racines du monde ouvertes", "dent_noire": "Revanche de Dent-Noire",
           "diag_kemmler": "[DIAG] constructions", "corruption": "ESSAI DE CORRUPTION", "etapes_histoire": " : etape ",
           "chroniques": "chronique", "felix": "Felix", "echos": "echo "}
MOTIFS = {"erreurs": "SCRIPT ERROR", "blocages": "[ESSAI] BLOCAGE", "chargements_rates": "Failed to load mod file",
          "executions_ratees": "Failed to execute loaded mod file"}


def jeu_tourne():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Warhammer3.exe", "/NH"], capture_output=True, text=True).stdout
    return "Warhammer3.exe" in out


def pid_jeu():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Warhammer3.exe", "/NH", "/FO", "CSV"],
                         capture_output=True, text=True).stdout
    m = re.search(r'"Warhammer3\.exe","(\d+)"', out)
    return int(m.group(1)) if m else None


def steam_tourne():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"], capture_output=True, text=True).stdout
    return "steam.exe" in out.lower()


def cdb():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-AppxPackage Microsoft.WinDbg* | Select-Object -First 1).InstallLocation"],
                       capture_output=True, text=True)
    chemin = os.path.join(r.stdout.strip(), "amd64", "cdb.exe")
    if not os.path.isfile(chemin):
        sys.exit("cdb.exe introuvable : installer WinDbg (Microsoft Store)")
    return chemin


def scripts_generes(dossier, faction, fiche, tours, ia=True):
    """Copie des deux scripts d'essai avec le seigneur et le nombre de tours de cet essai."""
    sortie = os.path.join(dossier, "pack")
    fichiers = []
    for rel in ("script/frontend/mod/saison_essai_auto.lua", "script/campaign/mod/saison_essai_auto.lua"):
        s = open(os.path.join(SOURCES, rel), encoding="utf-8").read()
        if "frontend" in rel:
            s, n = re.subn(r'seigneur = "[^"]*"', f'seigneur = "{fiche}"', s, count=1)
            if n != 1:
                sys.exit(f"!! {rel} : seigneur introuvable dans le script")
            if MENU_SANS_DLC:
                s, n = re.subn(r"_G\.saison_essai_menu_sans_dlc = false;", "_G.saison_essai_menu_sans_dlc = true;", s,
                               count=1)
                if n != 1:
                    sys.exit(f"!! {rel} : _G.saison_essai_menu_sans_dlc introuvable")
        else:
            s, n = re.subn(r"SAISON_ESSAI_MAX_TOURS = \d+", f"SAISON_ESSAI_MAX_TOURS = {tours}", s, count=1)
            s, n2 = re.subn(r"SAISON_ESSAI_PAUSE_TOUR = \d+", f"SAISON_ESSAI_PAUSE_TOUR = {PAUSE_TOUR}", s, count=1)
            if n2 != 1:
                sys.exit(f"!! {rel} : SAISON_ESSAI_PAUSE_TOUR introuvable")
            s, n3 = re.subn(r"SAISON_ESSAI_DELAI_FIN = \d+", f"SAISON_ESSAI_DELAI_FIN = {DELAI_FIN}", s, count=1)
            if n3 != 1:
                sys.exit(f"!! {rel} : SAISON_ESSAI_DELAI_FIN introuvable")
            # 25.09.2026 (audit de fluidité R2) : 3 clics sous l'IA essayés à 02 h 15 et 02 h 24 → le clic de fin de tour
            # n'était plus accepté (BLOCAGE à chaque tour, erreur 239) ; retour aux 30 clics éprouvés dans les deux modes
            s, n4 = re.subn(r"SAISON_ESSAI_MAX_NOTIFS = \d+", "SAISON_ESSAI_MAX_NOTIFS = 30", s, count=1)
            if n4 != 1:
                sys.exit(f"!! {rel} : SAISON_ESSAI_MAX_NOTIFS introuvable")
            if n != 1:
                sys.exit(f"!! {rel} : SAISON_ESSAI_MAX_TOURS introuvable")
            if ARMEES:
                s, n = re.subn(r"_G\.saison_essai_armees = false;", "_G.saison_essai_armees = true;", s, count=1)
                if n != 1:
                    sys.exit(f"!! {rel} : _G.saison_essai_armees introuvable")
            if SANS_DLC:
                s, n = re.subn(r"_G\.saison_essai_sans_dlc = false;", "_G.saison_essai_sans_dlc = true;", s, count=1)
                if n != 1:
                    sys.exit(f"!! {rel} : _G.saison_essai_sans_dlc introuvable")
            if SANS_DLC_SEIGNEUR:
                s, n = re.subn(r"_G\.saison_essai_sans_dlc_seigneur = false;", "_G.saison_essai_sans_dlc_seigneur = true;",
                               s, count=1)
                if n != 1:
                    sys.exit(f"!! {rel} : _G.saison_essai_sans_dlc_seigneur introuvable")
        cible = os.path.join(sortie, *rel.split("/"))
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        with open(cible, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        fichiers.append((cible, rel))
    # syntaxe vérifiée comme pour le pack de jeu (13 h 53 : une chaîne coupée a fait échouer le script du menu, jeu figé)
    import verifier_lua
    lua = verifier_lua.charger_lua()
    L = lua.luaL_newstate()
    fautes = [e for c, _ in fichiers for e in [verifier_lua.verifier(lua, L, c)] if e]
    lua.lua_close(L)
    if fautes:
        sys.exit(f"!! scripts d'essai en erreur de syntaxe : {fautes}")
    return fichiers


def construire_pack(fichiers):
    """Pack d'essai recréé de zéro (rpfm_server doit tourner)."""
    chemin = os.path.join(DATA, PACK_ESSAI)
    if os.path.exists(chemin):
        os.remove(chemin)
    sid = session()
    call(sid, "set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False}, 2)
    call(sid, "close_all_packs", {}, 3)
    call(sid, "new_pack", {}, 4)
    lst = json.loads(text(call(sid, "list_open_packs", {}, 5)))
    cle = [e[0] if isinstance(e, list) else e for v in lst.values() for e in v][0]
    call(sid, "save_pack_as", {"pack_key": cle, "path": chemin}, 6)
    call(sid, "close_all_packs", {}, 7)
    call(sid, "open_packfiles", {"paths": [chemin]}, 8)
    call(sid, "add_packed_files", {"pack_key": chemin, "source_paths": [s for s, _ in fichiers],
                                   "destination_paths": json.dumps([{"File": r} for _, r in fichiers])}, 9)
    res = text(call(sid, "save_packfile", {"pack_key": chemin}, 10))
    call(sid, "close_all_packs", {}, 11)
    if '"Error"' in res or not os.path.exists(chemin):
        sys.exit(f"!! pack d'essai non enregistré : {res[:300]}")
    import contenu_pack
    # RPFM ajoute ses réglages (`*.rpfm_reserved`), que le jeu ignore
    dedans = sorted(c.replace("\\", "/") for c, _ in contenu_pack.entrees(chemin)
                    if not c.endswith(".rpfm_reserved"))
    if dedans != sorted(r for _, r in fichiers):
        sys.exit(f"!! pack d'essai : contenu inattendu {dedans}")
    print(f"pack d'essai : {chemin} ({os.path.getsize(chemin)} octets, {len(dedans)} scripts)")


def script_propre():
    """Le user.script.txt de Charles SANS nos lignes d'essai (24.09.2026, 01 h : un essai arrêté de force laissait
    « mod zz_saison_essai_auto.pack; », l'essai suivant le « restaurait » tel quel, et les parties de Charles tournaient
    avec le pack d'essai : intros et scripts de début coupés). None si le fichier n'existe pas."""
    if not os.path.exists(SCRIPT):
        return None
    lignes = open(SCRIPT, "rb").read().decode("utf-8", "replace").splitlines(keepends=True)
    parasites = ("saison_essai_auto", "all_players_ai", "quit_after_campaign_processing", "process_campaign")
    return "".join(l for l in lignes if not any(p in l for p in parasites)).encode("utf-8")


def nettoyer():
    """Après un essai arrêté de force (TaskStop, fenêtre fermée) : user.script.txt propre, packs d'essai retirés,
    drapeaux d'essai rangés dans essai-auto\\drapeaux\\inutilise\\."""
    propre = script_propre()
    if propre is not None:
        open(SCRIPT, "wb").write(propre)
        print("user.script.txt :", propre.decode("utf-8").strip() or "(vide)")
    if os.path.exists(SCRIPT + ".bak"):
        os.remove(SCRIPT + ".bak")
    for nom in ("zz_saison_essai_auto.pack", "!!saison_essai_auto.pack"):
        p = os.path.join(DATA, nom)
        if os.path.exists(p):
            os.remove(p)
            print("retiré :", nom)
    drapeaux = os.path.join(DATA, "script", "campaign", "wh_dlc05_wood_elves")
    rangement = os.path.join(SOURCES, "drapeaux", "inutilise")
    if os.path.isdir(drapeaux):
        os.makedirs(rangement, exist_ok=True)
        for n in os.listdir(drapeaux):
            if n.startswith("saison_essai_") and n.endswith(".txt"):
                shutil.move(os.path.join(drapeaux, n),
                            os.path.join(rangement, n[:-4] + time.strftime("-retire-%Y%m%d-%H%M%S.txt")))
                print("drapeau rangé :", n)


def commandes_cdb(dossier):
    # barres obliques : dans la commande entre guillemets de cdb, les antislashs sont mangés (13 h 51, vidage perdu)
    vidage = os.path.join(dossier, "plantage.dmp").replace(os.sep, "/")
    # --vidage-complet : /ma (tout le tas, plusieurs Go) pour nommer l'objet fautif d'un plantage de rendu (23.09.2026)
    # sinon /mi (mémoire citée par les piles et les registres), et, jeu encore vivant, les tables virtuelles des objets
    # pointés par les registres : `lire_dll.py vtable <exe> <rva>` en donne la classe (proposition de la session
    # « IA et modding 3D », 23.09.2026, plantage +0x2532B26)
    genre = "/ma" if VIDAGE_COMPLET else "/mi"
    # pile et vidage D'ABORD, puis les lectures risquées chacune sous .catch : une lecture ratée (registre qui contient
    # du texte, 19 h 20) interrompait toute la suite, vidage compris
    objets = "; ".join(f".catch {{ dps @{reg} L2 }}; .catch {{ ln poi(@{reg}) }}"
                       for reg in ("rcx", "rdx", "rbx", "rsi", "rdi", "r14"))
    action = (f'.printf \\"EXCEPTION SECONDE CHANCE\\\\n\\"; r; ~*k 20; .dump {genre} {vidage}; '
              f'{objets}; .catch {{ dps poi(@rcx+0xed0) L6 }}; '
              # texte trouvé à +0xED0 dans deux plantages (« wh_dlc05 », 19 h 24) : lire la chaîne entière
              # (proposition de la session « IA et modding 3D », 23.09.2026)
              f'.catch {{ da @rcx+0xe80 L100 }}; .catch {{ du @rcx+0xe80 L80 }}; .catch {{ db @rcx+0xe80 L100 }}; '
              f'.kill; q')
    lignes = [f'sxd -c2 "{action}" {code}' for code in ("av", "sov", "eh", "dz", "ii", "c000041d", "c0000409")]
    lignes += ["sxd ld", "sxd ud", "sxd ct", "sxd et", "sxd cpr", "sxd epr", "g"]
    chemin = os.path.join(dossier, "commandes.cdb")
    with open(chemin, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    return chemin


def vidage_gel(dossier, pid):
    """Gel : vidage non invasif (le jeu est déjà sous cdb) avec les piles de tous les fils."""
    log = os.path.join(dossier, "gel.log")
    vid = os.path.join(dossier, "gel.dmp").replace(os.sep, "/")
    subprocess.run([cdb(), "-pv", "-p", str(pid), "-logo", log, "-c", f"~*k 30; .dump /m {vid}; qd"],
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)


def lire_etat(apres):
    etat = {"tours": [], "compteurs": {k: 0 for k in MOTIFS}, "fin": False, "journaux": [], "extraits_erreurs": [],
            "bilans": [], "etapes_histoire": 0, "humaine": [], "echec_lancement": False,
            "armees_ok": 0, "armees_echec": [], "preuves": {k: [] for k in PREUVES}}
    logs = sorted((p for p in glob.glob(os.path.join(JEU, "script_log_*.txt")) + [MENU]
                   if os.path.exists(p) and os.path.getmtime(p) >= apres), key=os.path.getmtime)
    for p in logs:
        etat["journaux"].append(p)
        lignes = open(p, encoding="utf-8", errors="replace").read().splitlines()
        for i, l in enumerate(lignes):
            m = TOUR.search(l)
            if m:
                horo = float(m.group(1))
                duree = round(horo - etat["_dernier"], 1) if etat.get("_dernier") is not None else 0
                etat["_dernier"] = horo
                etat["tours"].append((int(m.group(2)), duree))
            for k, motif in MOTIFS.items():
                if motif in l:
                    etat["compteurs"][k] += 1
                    if k == "erreurs" and len(etat["extraits_erreurs"]) < 40:
                        etat["extraits_erreurs"].append("\n".join(lignes[i + 1:i + 8]))
            for cle_preuve, motif_preuve in PREUVES.items():
                if motif_preuve in l and len(etat["preuves"][cle_preuve]) < 5:
                    etat["preuves"][cle_preuve].append(l.strip()[-220:])
            # armées d'essai des finales et des Échos (`_G.saison_essai_armees`, session « IA et modding 3D »)
            if "ESSAI ARMEE" in l:
                if " ok" in l:
                    etat["armees_ok"] += 1
                elif "echec" in l or "jamais parue" in l:
                    etat["armees_echec"].append(l.strip()[-200:])
            if "[ESSAI] FIN" in l:
                etat["fin"] = True
            if "[ESSAI] ECHEC" in l:
                etat["echec_lancement"] = True
            if "[ESSAI] bilan" in l:
                etat["bilans"].append(l.strip())
            if "[ESSAI] tour de la faction locale" in l and len(etat["humaine"]) < 3:
                etat["humaine"].append(l.strip())
            if re.search(r"\betape \d", l):
                etat["etapes_histoire"] += 1
    return etat


def un_essai(alias, tours, gel_min, limite_h, essai_seul, ia=True):
    faction, fiche = SEIGNEURS[alias]
    dossier = os.path.join(JOURNAL, time.strftime("%Y%m%d-%H%M%S") + "-" + alias)
    os.makedirs(dossier)
    print(f"\n=== {alias} : {faction} / {fiche}, {tours} tours ; dossier {dossier}")
    fichiers = scripts_generes(dossier, faction, fiche, tours, ia)
    if NEUTRE_VFX:
        neutres = os.path.join(SOURCES, NEUTRE_VFX, "vfx")
        fichiers += [(os.path.join(neutres, n), "vfx/" + n) for n in sorted(os.listdir(neutres))]
        print(f"effets de WH1 neutralisés dans le pack d'essai : {len(os.listdir(neutres))}")
    for dossier_ajout in AJOUTS:
        base = os.path.join(SOURCES, dossier_ajout)
        for racine, _, noms in os.walk(base):
            for n in noms:
                chemin = os.path.join(racine, n)
                fichiers.append((chemin, os.path.relpath(chemin, base).replace(os.sep, "/")))
        print(f"ajout au pack d'essai : {dossier_ajout}")
    construire_pack(fichiers)
    cmd_cdb = commandes_cdb(dossier)
    if essai_seul:
        print("--essai : rien n'est lancé")
        os.remove(os.path.join(DATA, PACK_ESSAI))
        return {"seigneur": alias, "lance": False}

    script_charles = script_propre()
    crash_avant = set(os.listdir(CRASH)) if os.path.isdir(CRASH) else set()
    t0 = time.time()
    bilan = {"seigneur": alias, "faction": faction, "fiche": fiche, "tours_demandes": tours, "all_players_ai": ia, "neutre_vfx": NEUTRE_VFX, "armees": ARMEES,
             "debut": time.strftime("%Y-%m-%d %H:%M:%S")}
    proc = None
    try:
        if os.path.exists(MENU):
            os.remove(MENU)
        with open(SCRIPT, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"    mod {PACK_JEU};\n    mod {PACK_ESSAI};\n" + ("    all_players_ai;\n" if ia else ""))
        log_cdb = os.path.join(dossier, "cdb.log")
        proc = subprocess.Popen([cdb(), "-G", "-hd", "-logo", log_cdb, "-cf", cmd_cdb, EXE], cwd=JEU,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("jeu lancé sous cdb", time.strftime("%H:%M:%S"))
        dernier_progres, dernier_signe = time.time(), None
        issue = None
        while True:
            time.sleep(20)
            etat = lire_etat(t0 - 5)
            # progrès = un tour de plus (le journal grossit aussi quand le tour est bloqué : lignes BLOCAGE, 15 h 51) ;
            # avant le tour 1, la croissance du journal compte (chargement)
            signe = (len(etat["tours"]),) if etat["tours"] else \
                (0, sum(os.path.getsize(p) for p in etat["journaux"]))
            if signe != dernier_signe:
                dernier_signe, dernier_progres = signe, time.time()
                if etat["tours"]:
                    t, d = etat["tours"][-1]
                    print(f"  {time.strftime('%H:%M:%S')} tour {t} ({d} s) ; erreurs {etat['compteurs']['erreurs']} ; "
                          f"blocages {etat['compteurs']['blocages']}", flush=True)
            if etat["fin"]:
                issue = "fin"
                break
            if etat["echec_lancement"]:
                issue = "echec_lancement"
                break
            if proc.poll() is not None:
                # plantage = vidage écrit OU exception de seconde chance dans cdb.log (vidage perdu, 19 h 20)
                journal_cdb = os.path.join(dossier, "cdb.log")
                seconde = (os.path.exists(journal_cdb)
                           and any(l.strip() == "EXCEPTION SECONDE CHANCE"
                                   for l in open(journal_cdb, encoding="utf-8", errors="replace")))
                issue = ("plantage" if os.path.exists(os.path.join(dossier, "plantage.dmp")) or seconde
                         else "sortie")
                break
            if time.time() - dernier_progres > gel_min * 60:
                issue = "gel"
                pid = pid_jeu()
                if pid:
                    print(f"  !! aucun progrès depuis {gel_min} min : vidage du gel")
                    vidage_gel(dossier, pid)
                break
            if time.time() - t0 > limite_h * 3600:
                issue = "limite"
                break
        bilan["issue"] = issue
    finally:
        if jeu_tourne():
            subprocess.run(["taskkill", "/IM", "Warhammer3.exe", "/F"], capture_output=True)
            time.sleep(8)
        if proc and proc.poll() is None:
            proc.kill()
        if script_charles is not None:
            open(SCRIPT, "wb").write(script_charles)
        if os.path.exists(SCRIPT + ".bak"):
            os.remove(SCRIPT + ".bak")
        try:
            os.remove(os.path.join(DATA, PACK_ESSAI))
        except OSError:
            pass
    etat = lire_etat(t0 - 5)
    for p in etat["journaux"]:
        shutil.copy2(p, dossier)
    nouveaux = sorted(set(os.listdir(CRASH)) - crash_avant) if os.path.isdir(CRASH) else []
    for n in nouveaux:
        src = os.path.join(CRASH, n)
        (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, os.path.join(dossier, n))
    durees = [d for _, d in etat["tours"]]
    bilan.update({"duree_s": int(time.time() - t0), "dernier_tour": etat["tours"][-1][0] if etat["tours"] else None,
                  "tour_moyen_s": round(sum(durees) / len(durees), 1) if durees else None,
                  "tour_max_s": max(durees) if durees else None, "compteurs": etat["compteurs"],
                  "etapes_histoire": etat["etapes_histoire"], "faction_locale": etat["humaine"],
                  "derniers_bilans": etat["bilans"][-9:], "extraits_erreurs": etat["extraits_erreurs"],
                  "crash_report": nouveaux, "armees_ok": etat["armees_ok"],
                  "armees_echec": etat["armees_echec"], "preuves": etat["preuves"]})
    with open(os.path.join(dossier, "bilan.json"), "w", encoding="utf-8") as f:
        json.dump(bilan, f, ensure_ascii=False, indent=1)
    print(f"=== {alias} : {bilan['issue']} au tour {bilan['dernier_tour']} en {bilan['duree_s'] // 60} min ; "
          f"tour moyen {bilan['tour_moyen_s']} s, max {bilan['tour_max_s']} s ; {etat['compteurs']}")
    return bilan


def main():
    if "--nettoyer" in sys.argv:
        # après tout essai arrêté de force (TaskStop) : à lancer AVANT de rendre la main à Charles
        sys.stdout.reconfigure(encoding="utf-8")
        nettoyer()
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nettoyer", action="store_true",
                    help="seul : user.script.txt propre, packs d'essai retirés, drapeaux rangés (après un arrêt forcé)")
    ap.add_argument("--seigneur", action="append", required=True, help=f"{', '.join(SEIGNEURS)} ou tous ; répétable")
    ap.add_argument("--tours", type=int, default=100)
    ap.add_argument("--gel", type=float, default=15, help="minutes sans progrès avant de conclure au gel")
    ap.add_argument("--limite", type=float, default=8, help="heures au plus par partie")
    ap.add_argument("--essai", action="store_true", help="prépare le pack et les commandes sans lancer le jeu")
    ap.add_argument("--neutre-vfx", nargs="?", const="neutre-vfx", default=None,
                    help="remplace des effets de WH1 par ceux du dossier essai-auto/<nom>/vfx (défaut : neutre-vfx, les 6 vides ; herbe-seule : l'herbe sans émetteur)")
    ap.add_argument("--pause-tour", type=int, default=0,
                    help="au round N, arrêter la fin de tour et poser la caméra sur le chef (Charles regarde)")
    ap.add_argument("--delai-fin", type=int, default=5,
                    help="secondes avant la fin de tour automatique de la faction locale (défaut 5 ; plus long pour "
                         "laisser l'IA jouer la faction du joueur sous all_players_ai, erreur 210)")
    ap.add_argument("--ajout", action="append", default=[],
                    help="dossier de essai-auto dont le contenu va dans le pack d'essai (répétable)")
    ap.add_argument("--prioritaire", action="store_true",
                    help="pack d'essai nommé !!saison_essai_auto.pack : il passe DEVANT notre pack (ordre alphabétique, "
                         "« ! » d'abord) et peut remplacer nos fichiers (variante de terrain dans --ajout)")
    ap.add_argument("--vidage-complet", action="store_true",
                    help="vidage /ma au plantage (plusieurs Go) pour nommer l'objet fautif")
    ap.add_argument("--armees", action="store_true",
                    help="pose _G.saison_essai_armees : armées des finales et des Échos posées tour à tour")
    ap.add_argument("--sans-ia", action="store_true",
                    help="sans `all_players_ai` : la faction du joueur ne fait que finir ses tours (filet de 90 s)")
    ap.add_argument("--sans-dlc", action="store_true",
                    help="pose _G.saison_essai_sans_dlc : joueur sans le DLC des Elfes Sylvains simulé (verrou attendu : "
                         "message, campagne bloquée, retour au menu ; 25.09.2026, bêta)")
    ap.add_argument("--sans-dlc-seigneur", action="store_true",
                    help="pose _G.saison_essai_sans_dlc_seigneur : contenu de CA du seigneur joué simulé absent")
    ap.add_argument("--menu-sans-dlc", action="store_true",
                    help="pose _G.saison_essai_menu_sans_dlc au menu (plan B du verrou : bouton de lancement grisé)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    global ARMEES, NEUTRE_VFX, PAUSE_TOUR, AJOUTS, VIDAGE_COMPLET, PACK_ESSAI, DELAI_FIN, SANS_DLC, SANS_DLC_SEIGNEUR
    global MENU_SANS_DLC
    SANS_DLC = a.sans_dlc
    MENU_SANS_DLC = a.menu_sans_dlc
    SANS_DLC_SEIGNEUR = a.sans_dlc_seigneur
    VIDAGE_COMPLET = a.vidage_complet
    DELAI_FIN = a.delai_fin
    if a.prioritaire:
        # 23.09.2026, 22 h 30 : zz_ passe APRÈS notre pack (un required.lua du pack d'essai ne remplaçait pas le nôtre)
        PACK_ESSAI = "!!saison_essai_auto.pack"
    AJOUTS = a.ajout
    PAUSE_TOUR = a.pause_tour
    ARMEES = a.armees
    NEUTRE_VFX = a.neutre_vfx
    seigneurs = list(SEIGNEURS) if "tous" in a.seigneur else a.seigneur
    inconnus = [s for s in seigneurs if s not in SEIGNEURS]
    if inconnus:
        sys.exit(f"!! seigneur(s) inconnu(s) : {inconnus}")
    if jeu_tourne():
        sys.exit("!! Warhammer 3 tourne déjà : le fermer d'abord")
    if not a.essai and not steam_tourne():
        sys.exit("!! Steam ne tourne pas : le jeu sortirait en 6 s")
    if not os.path.exists(os.path.join(DATA, PACK_JEU)):
        sys.exit(f"!! {PACK_JEU} absent de {DATA}")
    os.makedirs(JOURNAL, exist_ok=True)
    bilans = [un_essai(s, a.tours, a.gel, a.limite, a.essai, ia=not a.sans_ia) for s in seigneurs]
    if not a.essai:
        with open(os.path.join(JOURNAL, time.strftime("%Y%m%d-%H%M%S") + "-resume.json"), "w", encoding="utf-8") as f:
            json.dump(bilans, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
