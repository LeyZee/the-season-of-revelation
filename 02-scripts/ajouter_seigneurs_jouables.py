#!/usr/bin/env python3
"""
ajouter_seigneurs_jouables.py - rendre Orion et Durthu choisissables dans l'ecran « Nouvelle
campagne » de Warhammer 3, avec les fiches propres a la mini-campagne.

Premiere etape (21.09.2026, journal `phase-2-startpos-temoin.md` § 20). Le startpos genere, Charles
a ouvert la campagne en jeu : la race « Elfes sylvains » apparaissait, mais **aucun seigneur**
n'etait propose (pas de portrait, textes bruts `dy_description` / `dy_faction`, blason par defaut
de l'Empire, marqueur en (0, 0)). Le mecanisme, releve dans les donnees de CA :
- `frontend_faction_leaders` decrit chaque seigneur de l'ecran (portrait, scene 3D, video, ecran de
  chargement, doublage, textes) ; sa cle est libre (aucune reference) ;
- **`start_pos_starting_general_options`** relie un personnage du startpos (`general`, son
  identifiant dans `start_pos_characters`) a l'une de ces fiches (`frontend_faction_leader`).
  La notre etait vide : le startpos n'avait aucun noeud `STARTING_GENERAL_OPTION`. Warhammer 1
  n'avait pas cette table.

Seconde etape (21.09.2026, § 22). Les fiches de Warhammer 3 pour Orion et Durthu sont celles des
Empires Immortels : leur phrase de depart parle de la foret de Chalons et des Montagnes Grises.
Warhammer 1 avait, pour la mini-campagne, **ses propres fiches** :
`wh_dlc05_political_party_mini_wood_elves_ruler` et `..._durthu`, avec le recit de chargement de
la Saison de la Revelation. On les recree : copie de la fiche de Warhammer 3 (portrait, scene,
video, doublage, image de chargement : tous presents dans le jeu), sous la cle de Warhammer 1, et on
y relie nos deux personnages. Les textes (francais et anglais) sont poses par `injecter_textes.py`
sous les cles de Warhammer 1 ; le kit recoit la version anglaise, comme chez CA.

Le script ecrit **a la source** — `raw_data\\db\\frontend_faction_leaders.xml` et
`start_pos_starting_general_options.xml`, apres sauvegarde dans `05-journal\\db-backups\\` — **et**
dans `zz_startpos_db.pack`, ou le jeu lit les tables de depart quand il genere le startpos.
Il est rejouable : il ne cree que ce qui manque et ne reecrit que ce qui differe.

Apres lui : `build_pack.py` (qui embarque les fiches), regenerer le startpos (`startpos_manuel.py`,
commande du temoin), le recopier dans `04-projets\\saison-des-revelations\\startpos\\`, puis
`build_pack.py` a nouveau.

Usage :
    python ajouter_seigneurs_jouables.py            # essai a blanc
    python ajouter_seigneurs_jouables.py --apply
"""

import argparse
import io
import json
import os
import re
import shutil
import struct
import sys
import time
import uuid
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402
from injecter_textes import TEXTES_PROPRES, textes_session         # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
KIT_OPTIONS = os.path.join(KIT_DB, "start_pos_starting_general_options.xml")
KIT_FICHES = os.path.join(KIT_DB, "frontend_faction_leaders.xml")
TEXTES_EN = os.path.join(ATELIER, "03-references", "saison-des-revelations", "textes-wh1-en.json")
PACK = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data/zz_startpos_db.pack"
CHEMIN = "db/start_pos_starting_general_options_tables/start_pos_starting_general_options_wh_dlc05_wood_elves"
CHEMIN_PERSOS = "db/start_pos_characters_tables/start_pos_characters_wh_dlc05_wood_elves"

# (sous-type du personnage, faction) -> (fiche de la mini-campagne, fiche de Warhammer 3 copiee)
SEIGNEURS = {
    ("wh_dlc05_wef_orion", "wh_dlc05_wef_wood_elves"):
        ("wh_dlc05_political_party_mini_wood_elves_ruler", "wh_dlc05_political_party_wood_elves_ruler"),
    ("wh_dlc05_wef_durthu", "wh_dlc05_wef_argwylon"):
        ("wh_dlc05_political_party_mini_wood_elves_durthu", "wh_dlc05_political_party_wood_elves_durthu"),
    # Seigneurs de WH3 rendus jouables (23.09.2026, 05 h 15, demande de Charles : « toutes ces nouvelles factions jouables
    # sur l'écran de sélection, avant d'entrer dans la campagne ») ; clés et fiches de CA à recopier : spécification de la
    # session d'audit (`05-journal\2026-09-22-gameplay-wh3\spec-seigneurs-jouables.md`), textes dans les siens
    ("wh_dlc07_brt_alberic", "wh_main_brt_bordeleaux"):
        ("wh_dlc05_political_party_mini_bretonnia_alberic", "wh_dlc07_political_party_bretonnia_alberic"),
    ("wh_dlc07_brt_fay_enchantress", "wh_main_brt_carcassonne"):
        ("wh_dlc05_political_party_mini_bretonnia_fay", "wh_dlc07_political_party_bretonnia_fay"),
    ("wh_dlc05_bst_morghur", "wh_dlc05_bst_morghur_herd"):
        ("wh_dlc05_political_party_mini_beastmen_morghur", "wh_dlc03_political_party_beastmen_morghur"),
    ("wh_dlc05_vmp_red_duke", "wh_main_vmp_mousillon"):
        ("wh_dlc05_political_party_mini_vampire_counts_red_duke", "wh_main_political_party_vampire_ruler"),
    # Drycha, Kemmler et Grom (23.09.2026, 13 h ; `seigneurs_drycha_kemmler_grom.py` pour leurs lignes de départ ;
    # spécification `05-journal\2026-09-22-gameplay-wh3\spec-drycha-kemmler-grom.md`), clés des textes de la session d'audit
    ("wh2_dlc16_wef_drycha", "wh2_dlc16_wef_drycha"):
        ("wh_dlc05_political_party_mini_wood_elves_drycha", "wh2_dlc16_political_party_wef_drycha"),
    ("wh_main_vmp_heinrich_kemmler", "wh2_dlc11_vmp_the_barrow_legion"):
        ("wh_dlc05_political_party_mini_vampire_counts_kemmler", "wh_main_political_party_vampire_heinrich"),
    ("wh2_dlc15_grn_grom_the_paunch", "wh2_dlc15_grn_broken_axe"):
        ("wh_dlc05_political_party_mini_greenskins_grom", "wh2_dlc15_political_party_grn_grom"),
    # les Sœurs du Crépuscule (24.09.2026, 00 h 10 ; `seigneur_soeurs.py` ; spécification
    # `05-journal\2026-09-22-gameplay-wh3\spec-soeurs-du-crepuscule.md`), clé de fiche des textes de la session IA
    ("wh2_dlc16_wef_sisters_of_twilight", "wh2_dlc16_wef_sisters_of_twilight"):
        ("wh_dlc05_political_party_mini_wood_elves_sisters", "wh2_dlc16_political_party_wef_sisters_of_twilight"),
}
# Colonnes remplacées dans la copie de la fiche de CA. Aucune bataille de prologue ni vidéo d'intro des Empires (nos
# fiches d'Orion et de Durthu n'en ont pas). Le Duc rouge n'a pas de fiche chez CA (il n'est pas jouable aux Empires) :
# celle de Mannfred, avec son portrait, sa vidéo, son doublage et sa scène à lui (`SCENE_DUC_ROUGE`).
SCENE_DUC_ROUGE = "composite_scene\\lord_selection\\undead\\wh_dlc05_saison_red_duke.csc"
REMPLACEMENTS = {
    "wh_dlc05_political_party_mini_bretonnia_alberic": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_bretonnia_fay": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_beastmen_morghur": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_wood_elves_drycha": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_vampire_counts_kemmler": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_greenskins_grom": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_wood_elves_sisters": {"prelude_battle": "", "loading_screen_intro_video": ""},
    "wh_dlc05_political_party_mini_vampire_counts_red_duke": {
        "prelude_battle": "", "loading_screen_intro_video": "",
        "character_image": "UI\\Portraits\\Faction_leaders\\vmp_the_red_duke_0.png",
        "uniform": SCENE_DUC_ROUGE,
        "video": "Front_end_selection_movies/red_duke_front_end",
        "voiceover": "wh_dlc05_vo_actor_vmp_cha_red_duke",
        "agent_subtype_record": "wh_dlc05_vmp_red_duke",
        "faction": "wh_main_vmp_mousillon"},
}
# Pointeur de l'onglet « Carte » de l'écran de sélection (23.09.2026, 05 h 55 ; Charles : « les pointeurs pour indiquer
# où ils commencent, comme avec les elfes sylvains »). Le startpos grave pour chaque faction jouable la position de son
# seigneur en fraction de la carte (FACTION_INFOS de CAMPAIGN_PREOPEN_MAP_INFO : Orion (0,677 ; 0,200) pour (270, 88)).
# Un chef EN GARNISON est en (0, 0) : pointeur dans le coin. CA a la colonne pour ce cas : `override_force_location_x/y`
# (seule Eltharion, en garnison à Tor Yvresse, 0,398 / 0,420). On y met la case de la capitale, lue dans le startpos.
POINTEURS_GARNISON = {"wh_dlc05_political_party_mini_bretonnia_alberic": "wh_dlc05_bordeleaux_bordeleaux",
                      "wh_dlc05_political_party_mini_bretonnia_fay": "wh_dlc05_carcassonne_castle_carcassonne",
                      "wh_dlc05_political_party_mini_vampire_counts_red_duke": "wh_dlc05_mousillon_mousillon"}
LARGEUR_HEX, HAUTEUR_HEX = 400, 440
# position gravée par le jeu = case + ce décalage, divisée par la taille (Orion, Durthu, Morghur : écart < 0,0005)
DECALAGE_X, DECALAGE_Y = 0.68, -0.15


def pointeurs():
    """{fiche: {override_force_location_x, _y}} pour les chefs en garnison, d'après les cases de colonie du startpos."""
    import placer_chefs_capitale as P
    colonies, _ = P.cases_des_colonies()
    out = {}
    for fiche, region in POINTEURS_GARNISON.items():
        if region not in colonies:
            raise SystemExit(f"!! colonie {region} absente du startpos")
        x, y = colonies[region]
        out[fiche] = {"override_force_location_x": f"{(x + DECALAGE_X) / LARGEUR_HEX:.4f}",
                      "override_force_location_y": f"{(y + DECALAGE_Y) / HAUTEUR_HEX:.4f}"}
    return out


# factions rendues jouables (`start_pos_factions.playable`), par leur identifiant dans la table
FACTIONS_JOUABLES = {"2120137086": "wh_main_brt_bordeleaux", "2120137100": "wh_main_brt_carcassonne",
                     "2120137128": "wh_dlc05_bst_morghur_herd", "2120137457": "wh_main_vmp_mousillon"}
KIT_FACTIONS = os.path.join(KIT_DB, "start_pos_factions.xml")
# scène du Duc rouge : celle de Vlad (épée et bouclier, comme lui ; Mannfred tient un bâton), son modèle remplacé
SCENE_MODELE = "composite_scene/lord_selection/undead/vlad_von_carstein.csc"
SCENE_CHAINES = {"vmp_ch_vlad": "vmp_the_red_duke",
                 "variantmeshes\\variantmeshdefinitions\\vmp_ch_vlad.variantmeshdefinition":
                     "variantmeshes\\variantmeshdefinitions\\vmp_the_red_duke.variantmeshdefinition"}
DOSSIER_SEIGNEURS = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "seigneurs")
DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
# colonnes localisees de la fiche : le kit porte le texte anglais
COLONNES_TEXTE = ("localised_description", "localised_action_points", "loading_screen_text",
                  "frontend_description")
# identifiants de nos lignes d'options : sous 2^31 (colonne entiere), hors de la plage de CA
PREMIER_ID = 2140790001
# `startpos_map` : **`default`** (21.09.2026, 18 h). Recopier la valeur de la fiche modele et y mettre
# notre cle neuve faisait planter le jeu au tout debut du chargement de la campagne (recherche qui rend
# nul, `Warhammer3.exe+0x27A7DFF`, journal de phase 3 § 9) : ce champ designe une variante de depart
# qui doit exister. Les 176 fiches neuves d'Old World valent toutes `default` ; les autres reprennent
# la cle d'un seigneur existant de CA ; aucune n'utilise sa propre cle neuve.
STARTPOS_MAP = "default"


def sauvegarde(fichier, nom):
    dest = os.path.join(ATELIER, "05-journal", "db-backups", f"{nom}-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(fichier, dest)
    print(f"  sauvegarde : {dest}")


def fiche_mini(xml, cle, modele, textes_en):
    """Le bloc XML de la fiche `cle`, copie de la fiche `modele` du kit."""
    m = re.search(r'<frontend_faction_leaders record_uuid="[^"]*" record_timestamp="[^"]*" '
                  rf'record_key="{modele}">.*?</frontend_faction_leaders>', xml, re.S)
    if not m:
        raise SystemExit(f"!! fiche modele absente du kit : {modele}")
    bloc = m.group(0)
    bloc = re.sub(r'record_uuid="[^"]*" record_timestamp="[^"]*" record_key="[^"]*"',
                  f'record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{int(time.time() * 1000)}" '
                  f'record_key="{cle}"', bloc, count=1)
    bloc = bloc.replace(f"<key>{modele}</key>", f"<key>{cle}</key>")
    bloc = re.sub(r"<startpos_map>[^<]*</startpos_map>", f"<startpos_map>{STARTPOS_MAP}</startpos_map>", bloc,
                  count=1)
    for col in COLONNES_TEXTE:
        texte = textes_en.get(f"frontend_faction_leaders_{col}_{cle}", "")
        neuf = (f'<{col} state="APPROVED" last_approved_text={quoteattr(texte)} '
                f'last_edit_user="bob">{escape(texte)}</{col}>') if texte else f"<{col}></{col}>"
        bloc, n = re.subn(rf"<{col}\b[^>]*>.*?</{col}>|<{col}\s*/>", lambda _: neuf, bloc, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"!! colonne {col} introuvable dans la fiche {modele}")
    for col, valeur in REMPLACEMENTS.get(cle, {}).items():
        neuf = f"<{col}>{escape(valeur)}</{col}>" if valeur else f"<{col}></{col}>"
        bloc, n = re.subn(rf"<{col}\b[^>]*>.*?</{col}>|<{col}\s*/>", lambda _: neuf, bloc, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"!! colonne {col} introuvable dans la fiche {modele}")
    return bloc


def scene_duc_rouge():
    """La scène 3D de l'écran de sélection du Duc rouge : celle de Vlad (ESF 0xABCA), les chaînes du modèle remplacées
    dans les tables de fin de fichier (l'arbre les cite par index : il ne bouge pas). Rend (chemin du pack, octets)."""
    from contenu_pack import SourcePacks, chemins_du_jeu
    import lire_esf as E
    chemin = SCENE_DUC_ROUGE.replace("\\", "/").lower()
    if chemin in chemins_du_jeu(DATA_WH3):
        raise SystemExit(f"!! {chemin} existe dans WH3 : jamais remplacé")
    blob = SourcePacks(DATA_WH3).lire(SCENE_MODELE)
    if blob is None:
        raise SystemExit(f"!! scène modèle introuvable : {SCENE_MODELE}")
    esf = E.Esf(blob)
    esf.analyse()
    u, a, fin = E.lire_chaines(esf)
    if esf.magie != 0xABCA or fin != len(blob):
        raise SystemExit("!! scène modèle : disposition ESF inattendue")
    faits = [t for _, t in a if t in SCENE_CHAINES]
    if sorted(faits) != sorted(SCENE_CHAINES):
        raise SystemExit(f"!! scène modèle : chaînes à remplacer trouvées {faits}")
    sortie = bytearray(blob[:esf.fin_noms])
    for liste, utf16 in ((u, True), (a, False)):
        sortie += struct.pack("<I", len(liste))
        for idx, texte in liste:
            texte = SCENE_CHAINES.get(texte, texte) if not utf16 else texte
            brut = texte.encode("utf-16-le") if utf16 else texte.encode("latin-1")
            sortie += struct.pack("<H", len(texte)) + brut + struct.pack("<I", idx)
    verif = E.Esf(bytes(sortie))
    verif.analyse()
    if E.lire_chaines(verif)[2] != len(sortie):
        raise SystemExit("!! scène du Duc rouge : ne se relit pas jusqu'au bout")
    return chemin, bytes(sortie)


def rendre_jouables(apply):
    """`playable` = 1 dans le kit pour FACTIONS_JOUABLES (sauvegarde avant) ; rend le nombre de lignes changées. Le pack des
    tables de départ suit par `synchroniser_pack_startpos.py --table start_pos_factions --cle ID --maj --apply`."""
    with io.open(KIT_FACTIONS, encoding="utf-8", newline="") as f:
        xml = f.read()
    changer = []
    for m in re.finditer(r"<start_pos_factions\b[^>]*>.*?</start_pos_factions>", xml, re.S):
        bloc = m.group(0)
        ident = re.search(r"<ID>(\d+)</ID>", bloc)
        if ident and ident.group(1) in FACTIONS_JOUABLES:
            if f"<faction>{FACTIONS_JOUABLES[ident.group(1)]}</faction>" not in bloc:
                raise SystemExit(f"!! start_pos_factions {ident.group(1)} n'est pas {FACTIONS_JOUABLES[ident.group(1)]}")
            if "<playable>1</playable>" not in bloc:
                changer.append((bloc, bloc.replace("<playable>0</playable>", "<playable>1</playable>", 1)))
    print(f"start_pos_factions du kit : {len(changer)} faction(s) à rendre jouable(s)")
    if apply and changer:
        sauvegarde(KIT_FACTIONS, "start-pos-factions")
        for ancien, neuf in changer:
            if ancien == neuf:
                raise SystemExit("!! colonne playable introuvable")
            xml = xml.replace(ancien, neuf, 1)
        with io.open(KIT_FACTIONS, "w", encoding="utf-8", newline="") as f:
            f.write(xml)
    return len(changer)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    textes_en = {k: v["text"] for k, v in json.load(open(TEXTES_EN, encoding="utf-8")).items()}
    textes_en.update({k: v["en"] for k, v in TEXTES_PROPRES.items()})
    textes_en.update({k: v["en"] for k, v in textes_session().items()})    # textes de la session d'audit (prioritaires)

    # 0. les factions jouables et la scène du Duc rouge (fichier du pack principal, `build_pack` : dossier « seigneurs »)
    rendre_jouables(a.apply)
    chemin_scene, octets_scene = scene_duc_rouge()
    print(f"scène du Duc rouge : {chemin_scene} ({len(octets_scene)} octets, depuis {SCENE_MODELE})")
    if a.apply:
        dest = os.path.join(DOSSIER_SEIGNEURS, *chemin_scene.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(octets_scene)

    sid = session()
    i = [1]

    def c(tool, args):
        i[0] += 1
        return text(call(sid, tool, args, i[0]))

    types_de = {}

    def table(chemin):
        h = json.loads(c("decode_packed_file", {"pack_key": PACK, "path": chemin,
                                                "source": "PackFile"}))["DBRFileInfo"][0]
        rep = json.loads(c("fields_processed", {"definition": json.dumps(h["table"]["definition"])}))
        champs = rep if isinstance(rep, list) else list(rep.values())[0]
        noms = [f["name"] for f in champs]
        types_de[chemin] = {f["name"]: f["field_type"] for f in champs}
        return h, noms

    def v(ligne, noms, col):
        cell = ligne[noms.index(col)]
        return list(cell.values())[0] if isinstance(cell, dict) else cell

    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": True})
    c("open_packfiles", {"paths": [PACK]})

    # 1. l'identifiant de chaque seigneur dans NOS personnages de depart
    hp, np_ = table(CHEMIN_PERSOS)
    hf, nf = table("db/start_pos_factions_tables/start_pos_factions_wh_dlc05_wood_elves")
    faction_de = {str(v(l, nf, "ID")): v(l, nf, "faction") for l in hf["table"]["table_data"]}
    voulu = {}                                          # general -> fiche de la mini-campagne
    for (sous_type, faction), (fiche, _) in SEIGNEURS.items():
        trouves = [l for l in hp["table"]["table_data"]
                   if v(l, np_, "subtype") == sous_type
                   and faction_de.get(str(v(l, np_, "faction"))) == faction]
        if len(trouves) != 1:
            print(f"!! {sous_type} / {faction} : {len(trouves)} personnage(s), il en faut un")
            return 2
        voulu[int(v(trouves[0], np_, "ID"))] = fiche
        print(f"   {fiche:50} <- personnage {v(trouves[0], np_, 'ID')} ({sous_type})")

    # 2. les fiches, a la source
    with io.open(KIT_FICHES, encoding="utf-8", newline="") as f:
        xml_fiches = f.read()
    fiches_neuves = [(fiche, modele) for fiche, modele in SEIGNEURS.values()
                     if f'record_key="{fiche}"' not in xml_fiches]
    # fiches deja creees avec une autre valeur de `startpos_map` (avant le 21.09.2026, 18 h) : a corriger
    motif_fiche = lambda cle: re.compile(rf'(<frontend_faction_leaders [^>]*record_key="{cle}">.*?)'
                                         rf'<startpos_map>([^<]*)</startpos_map>', re.S)
    fiches_a_corriger = [fiche for fiche, _ in SEIGNEURS.values()
                         if (m := motif_fiche(fiche).search(xml_fiches)) and m.group(2) != STARTPOS_MAP]
    print(f"\nfiches du kit : {len(fiches_neuves)} a creer, {len(fiches_a_corriger)} a corriger "
          f"(startpos_map -> {STARTPOS_MAP})")
    # pointeurs des chefs en garnison : dans les fiches neuves (REMPLACEMENTS) et dans celles qui existent déjà
    for fiche, cols in pointeurs().items():
        REMPLACEMENTS.setdefault(fiche, {}).update(cols)
        print(f"   pointeur de {fiche} : ({cols['override_force_location_x']} ; {cols['override_force_location_y']})")
    pointeurs_a_poser = []
    for fiche, cols in REMPLACEMENTS.items():
        m = re.search(rf'<frontend_faction_leaders [^>]*record_key="{fiche}">.*?</frontend_faction_leaders>', xml_fiches, re.S)
        if not m:
            continue
        bloc = m.group(0)
        for col in ("override_force_location_x", "override_force_location_y"):
            if col in cols and f"<{col}>{cols[col]}</{col}>" not in bloc:
                pointeurs_a_poser.append(fiche)
                break
    print(f"fiches du kit : {len(pointeurs_a_poser)} pointeur(s) à poser")
    if a.apply and pointeurs_a_poser:
        sauvegarde(KIT_FICHES, "frontend-faction-leaders")
        for fiche in pointeurs_a_poser:
            m = re.search(rf'<frontend_faction_leaders [^>]*record_key="{fiche}">.*?</frontend_faction_leaders>',
                          xml_fiches, re.S)
            bloc = m.group(0)
            for col in ("override_force_location_x", "override_force_location_y"):
                bloc, n = re.subn(rf"<{col}>[^<]*</{col}>", f"<{col}>{REMPLACEMENTS[fiche][col]}</{col}>", bloc, count=1)
                if n != 1:
                    raise SystemExit(f"!! colonne {col} introuvable dans la fiche {fiche}")
            xml_fiches = xml_fiches.replace(m.group(0), bloc, 1)
        with io.open(KIT_FICHES, "w", encoding="utf-8", newline="") as f:
            f.write(xml_fiches)
        print(f"  kit : {len(pointeurs_a_poser)} pointeur(s) posé(s)")

    # 3. les options de depart, a la source : une ligne par general, qui pointe la bonne fiche
    with io.open(KIT_OPTIONS, encoding="utf-8", newline="") as f:
        xml_options = f.read()
    ids_pris = {int(x) for x in re.findall(r"<id>(\d+)</id>", xml_options)}
    blocs_options = {int(g): (b, s) for b, g, s in re.findall(
        r"(<start_pos_starting_general_options [^>]*>\s*<id>\d+</id>\s*<general>(\d+)</general>.*?"
        r"<frontend_faction_leader>([^<]*)</frontend_faction_leader>.*?</start_pos_starting_general_options>\r?\n?)",
        xml_options, re.S)}
    a_changer = {g: f for g, f in voulu.items() if g in blocs_options and blocs_options[g][1] != f}
    a_creer = {g: f for g, f in voulu.items() if g not in blocs_options}
    print(f"options du kit : {len(a_changer)} a repointer, {len(a_creer)} a creer")

    # 4. le produit : la table du pack des tables de depart
    hs, ns = table(CHEMIN)
    lignes_pack = {int(v(l, ns, "general")): l for l in hs["table"]["table_data"]}
    a_ecrire_pack = {g: f for g, f in voulu.items()
                     if g not in lignes_pack or v(lignes_pack[g], ns, "frontend_faction_leader") != f}
    print(f"options du pack : {len(a_ecrire_pack)} ligne(s) a ecrire")
    if not a.apply:
        print("essai a blanc : relancer avec --apply")
        return 0

    if fiches_neuves or fiches_a_corriger:
        sauvegarde(KIT_FICHES, "frontend-faction-leaders")
        for fiche in fiches_a_corriger:
            xml_fiches = motif_fiche(fiche).sub(lambda m: f"{m.group(1)}<startpos_map>{STARTPOS_MAP}</startpos_map>",
                                                xml_fiches, count=1)
        blocs = "".join(fiche_mini(xml_fiches, fiche, modele, textes_en) + "\r\n"
                        for fiche, modele in fiches_neuves)
        fin = xml_fiches.rindex("</dataroot>")
        xml_fiches = xml_fiches[:fin] + blocs + xml_fiches[fin:]
        with io.open(KIT_FICHES, "w", encoding="utf-8", newline="") as f:
            f.write(xml_fiches)
        print(f"  kit : {len(fiches_neuves)} fiche(s) creee(s), {len(fiches_a_corriger)} corrigee(s)")

    if a_changer or a_creer:
        sauvegarde(KIT_OPTIONS, "starting-general-options")
        horodatage = int(time.time() * 1000)
        for g, fiche in a_changer.items():
            ancien = blocs_options[g][0]
            ident = re.search(r"<id>(\d+)</id>", ancien).group(1)
            neuf = (f'<start_pos_starting_general_options record_uuid="{{{uuid.uuid4()}}}" '
                    f'record_timestamp="{horodatage}" record_key="{ident}">\r\n'
                    f"<id>{ident}</id>\r\n<general>{g}</general>\r\n<precedence>0</precedence>\r\n"
                    f"<frontend_faction_leader>{fiche}</frontend_faction_leader>\r\n"
                    f"<exclude_other_options>0</exclude_other_options>\r\n"
                    f"</start_pos_starting_general_options>\r\n")
            xml_options = xml_options.replace(ancien, neuf, 1)
        prochain = PREMIER_ID
        blocs = ""
        for g, fiche in a_creer.items():
            while prochain in ids_pris:
                prochain += 1
            ids_pris.add(prochain)
            blocs += (f'<start_pos_starting_general_options record_uuid="{{{uuid.uuid4()}}}" '
                      f'record_timestamp="{horodatage}" record_key="{prochain}">\r\n'
                      f"<id>{prochain}</id>\r\n<general>{g}</general>\r\n<precedence>0</precedence>\r\n"
                      f"<frontend_faction_leader>{fiche}</frontend_faction_leader>\r\n"
                      f"<exclude_other_options>0</exclude_other_options>\r\n"
                      f"</start_pos_starting_general_options>\r\n")
        fin = xml_options.rindex("</dataroot>")
        xml_options = xml_options[:fin] + blocs + xml_options[fin:]
        with io.open(KIT_OPTIONS, "w", encoding="utf-8", newline="") as f:
            f.write(xml_options)
        print(f"  kit : {len(a_changer)} option(s) repointee(s), {len(a_creer)} creee(s)")

    if a_ecrire_pack:
        # l'identifiant de chaque ligne est celui qu'elle porte dans le kit : on le relit
        with io.open(KIT_OPTIONS, encoding="utf-8", newline="") as f:
            xml_options = f.read()
        id_du_kit = {int(g): int(k) for k, g in re.findall(
            r"<id>(\d+)</id>\s*<general>(\d+)</general>", xml_options)}
        types = types_de[CHEMIN]
        for g, fiche in a_ecrire_pack.items():
            valeurs = {"general": g, "id": id_du_kit[g], "precedence": 0,
                       "frontend_faction_leader": fiche, "exclude_other_options": False}
            ligne = [{types[n]: valeurs[n]} for n in ns]
            if g in lignes_pack:
                hs["table"]["table_data"][hs["table"]["table_data"].index(lignes_pack[g])] = ligne
            else:
                hs["table"]["table_data"].append(ligne)
            print(f"   pack : ligne {id_du_kit[g]}  {fiche}")
        sauvegarde(PACK, "pack")
        c("save_packed_file_from_view", {"pack_key": PACK, "path": CHEMIN, "data": json.dumps({"DB": hs})})
        c("save_packfile", {"pack_key": PACK})
        print(f"  pack : {len(a_ecrire_pack)} ligne(s) ecrite(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
