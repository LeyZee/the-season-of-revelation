#!/usr/bin/env python3
"""
injecter_textes.py - poser les textes de la mini-campagne, en francais et en anglais, dans les
packs Warhammer 3.

Entrees : les JSON de `extraire_textes_wh1.py` (textes officiels de Warhammer 1, `textes-wh1.json`
en francais et `textes-wh1-en.json` en anglais) et `correspondances.json`.

Le travail, revu le 21.09.2026 (journal `phase-2-startpos-temoin.md` § 22) :

1. **Traduire les cles.** Une cle de localisation est `<table>_<colonne>_<cle de la ligne>`. Quand
   la ligne est une faction, sa cle a change entre les deux jeux : on applique
   `correspondances.json`, du plus long au plus court. La zone jouable a change de numero
   (1564135548 dans WH1, le notre est lu dans le kit) : c'est sous ce numero que l'ecran « Nouvelle
   campagne » cherche le titre et la description de la vignette (`Name`, `DescriptionText` de
   `CcoCampaignMapPlayableAreaRecord`). La premiere version ne le faisait pas : vignette sans titre.

2. **Ne jamais ecraser un texte du jeu.** Warhammer 3 charge les `.loc` d'un mod **quelle que soit
   la langue du joueur**. 2 772 des 3 590 cles reprises de WH1 existent deja dans Warhammer 3
   (unites, competences, batiments, effets des Elfes sylvains...) : notre pack les remplacait par
   la redaction de Warhammer 1, en francais pour tout le monde, et jusque dans les Empires
   Immortels. On retire donc toute cle que le jeu connait : il la fournit lui-meme, a jour, dans
   la langue du joueur. Liste des cles du jeu : `cles-vanilla-wh3.txt.gz` (`--vanilla` la refait
   depuis `local_en.pack` et `local_fr.pack`).

3. **Deux langues, deux packs.** Ce qui reste est propre a la campagne. L'anglais va dans le pack
   principal, sous `text/db/saison_des_revelations.loc` ; le francais dans
   `!saison_des_revelations_fr.pack` (mod de traduction a part), **sous le meme chemin** : quand ce
   petit pack est active, il passe devant le pack principal (le « ! » le met en tete de l'ordre de
   chargement) et son fichier masque l'anglais. (Jusqu'au 25.09.2026, 23 h, c'etait l'inverse :
   francais dans le principal, anglais dans `!saison_des_revelations_en.pack`.) Une cle absente d'une langue prend le texte de l'autre ; les textes
   « placeholder » ne sont pas repris.

4. Quelques textes n'existaient pas dans Warhammer 1 : la phrase de depart des deux seigneurs de la
   mini-campagne (`frontend_description`, colonne apparue avec Warhammer 3). Ils sont ecrits ici,
   dans les deux langues, a partir du recit de chargement de Warhammer 1.

Une copie lisible de chaque langue est ecrite dans `04-projets\\saison-des-revelations\\textes\\`.

Usage :
    python injecter_textes.py                     # essai a blanc (ecrit seulement les copies)
    python injecter_textes.py --apply
    python injecter_textes.py --vanilla           # refaire la liste des cles du jeu
"""

import argparse
import gzip
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpfm_mcp import session, call, text                            # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
DATA = r"C:/Program Files (x86)/Steam/steamapps/common/Total War WARHAMMER III/data/"
PACK = DATA + "saison_des_revelations.pack"
PACK_EN = DATA + "!saison_des_revelations_en.pack"         # jusqu'au 25.09.2026 (rangé)
# 25.09.2026, 23 h (Charles : « le pack en anglais, et un autre mod avec la traduction française ») : l'ANGLAIS dans le
# pack principal, le FRANÇAIS dans le pack de traduction, sous le même chemin (le « ! » le fait passer devant)
PACK_FR = DATA + "!saison_des_revelations_fr.pack"
LANGUE_PRINCIPALE, LANGUE_TRADUCTION = "en", "fr"
KIT_ZONES = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
             r"\raw_data\db\campaign_map_playable_areas.xml")
REFS = os.path.join(ATELIER, "03-references", "saison-des-revelations")
TEXTES = {"fr": os.path.join(REFS, "textes-wh1.json"), "en": os.path.join(REFS, "textes-wh1-en.json")}
VANILLA = os.path.join(REFS, "cles-vanilla-wh3.txt.gz")
CORR = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "correspondances.json")
COPIES = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "textes")
CHEMIN_LOC = "text/db/saison_des_revelations.loc"
NOM = "saison_des_revelations"
CARTE = "wh_dlc05_wood_elves_map_1"
INDEX_ZONE_WH1 = "1564135548"
PLACEHOLDERS = {"", "placeholder", "not used", "temp", "tbd"}

ORION = "wh_dlc05_political_party_mini_wood_elves_ruler"
DURTHU = "wh_dlc05_political_party_mini_wood_elves_durthu"
# Textes sans equivalent dans Warhammer 1 (voir 4. ci-dessus)
TEXTES_PROPRES = {
    f"frontend_faction_leaders_frontend_description_{ORION}": {
        "fr": "Renaissant avec le printemps, Orion s'éveille dans la Clairière Royale et découvre "
              "Athel Loren ravagée par un ennemi inconnu, auquel il jure la vengeance de la forêt.",
        "en": "Reborn with the spring, Orion rises in the King's Glade to find Athel Loren ravaged "
              "by an unknown foe, and swears the vengeance of the forest upon it.",
    },
    f"frontend_faction_leaders_frontend_description_{DURTHU}": {
        "fr": "Depuis le Palais des Chutes, en Argwylon, Durthu remonte la piste de dévastation "
              "laissée dans la forêt pour déchaîner sur les profanateurs la colère de ses esprits.",
        "en": "From the Waterfall Palace in Argwylon, Durthu follows the trail of devastation left "
              "through the forest, to unleash the wrath of its spirits upon the despoilers.",
    },
    # objectif scripté de la victoire (`saison_victoire.lua`, session « IA et modding 3D », 23.09.2026) : la table
    # `mission_text` n'existe que dans le kit, le jeu ne lit que la clé de texte (GUIDE § 15, n° 107)
    "mission_text_text_wh_dlc05_mini_delay_victory": {
        "fr": "Clore la Saison des Révélations",
        "en": "Bring the Season of Revelations to a close",
    },
    # « comment jouer » de la mini-campagne (session « IA et modding 3D », 23.09.2026, 02 h 15) : l'évènement de CA est
    # coupé par `suppress_how_they_play_event` ; sauts de paragraphe en vrais sauts de ligne, comme les .loc de CA
    # (0 sur 4 712 textes anglais n'a de « \n » littéral : audit de l'interface de la même session, 23.09.2026)
    "event_feed_strings_text_wh_dlc05_saison_comment_jouer_secondary_detail": {
        "fr": "Tel le cœur battant d'Athel Loren, le Chêne des Âges doit atteindre sa plus grande taille. Faites grandir "
              "le puissant Chêne avec l'or [[img:icon_treasury]][[/img]] ; son dernier niveau ne s'éveille qu'avec le "
              "Rituel de Renaissance d'Athel Loren. Morghur l'Enfant de l'Ombre et ses hardes d'Hommes-bêtes tenteront "
              "de le détruire : si le Chêne des Âges tombe, la victoire vous échappera.\n\n"
              "{{tr:how_they_play_wood_elves}}",
        "en": "As Athel Loren's beating heart, the Oak of Ages must reach its highest level. Grow the mighty Oak with "
              "[[img:icon_treasury]][[/img]]gold; its final level only awakens through the Ritual of Rebirth of Athel "
              "Loren. Morghur the Shadowgave and his Beastmen herds will seek to destroy it: should the Oak of Ages "
              "fall, victory will slip from your grasp.\n\n{{tr:how_they_play_wood_elves}}",
    },
}


# Textes de la session « IA et modding 3D » (23.09.2026) : un ou plusieurs fichiers JSON {clé: {"fr": ..., "en": ...}}
# dans ce dossier, lus en plus de TEXTES_PROPRES et PRIORITAIRES sur eux et sur les textes de WH1 (titre harmonisé,
# récits) ; mêmes règles : seules les clés inconnues du jeu sont posées.
DOSSIER_TEXTES_SESSION = os.path.join(r"C:\TotalWar-CampaignMap", "04-projets",
                                      "saison-des-revelations", "textes")


def textes_session():
    """{clé: {"fr", "en"}} de tous les JSON de DOSSIER_TEXTES_SESSION ; une langue absente prend l'autre."""
    out = {}
    if not os.path.isdir(DOSSIER_TEXTES_SESSION):
        return out
    for nom in sorted(os.listdir(DOSSIER_TEXTES_SESSION)):
        if not nom.lower().endswith(".json"):
            continue
        with open(os.path.join(DOSSIER_TEXTES_SESSION, nom), encoding="utf-8") as f:
            brut = json.load(f)
        for cle, t in brut.items():
            if cle.startswith("_"):                     # « _commentaire » et autres notes : pas des textes
                continue
            if not isinstance(t, dict) or not (t.get("fr") or t.get("en")):
                raise SystemExit(f"{nom} : {cle} n'a ni texte français ni texte anglais")
            if cle in out:
                raise SystemExit(f"{nom} : clé {cle} déjà définie dans un autre fichier du dossier")
            out[cle] = {"fr": t.get("fr") or t["en"], "en": t.get("en") or t["fr"]}
    return out


def index_zone():
    """Le numero de notre zone jouable, tel que le kit l'a enregistre."""
    with open(KIT_ZONES, encoding="utf-8") as f:
        xml = f.read()
    for bloc in re.findall(r"<campaign_map_playable_areas\b.*?</campaign_map_playable_areas>", xml, re.S):
        if f"<mapname>{CARTE}</mapname>" in bloc:
            return re.search(r"<index>(\d+)</index>", bloc).group(1)
    raise SystemExit(f"!! zone jouable de {CARTE} absente du kit")


def paires_de_cles():
    corr = json.load(open(CORR, encoding="utf-8"))
    paires = [(wh1, v["wh3"]) for wh1, v in corr["factions"].items()
              if v.get("wh3") and v["wh3"] != wh1]
    # du plus long au plus court : sinon `wh_dlc05_wef_mini` pourrait manger un prefixe plus long
    paires.sort(key=lambda p: -len(p[0]))
    paires.append((f"campaign_map_playable_areas_onscreen_name_{INDEX_ZONE_WH1}",
                   f"campaign_map_playable_areas_onscreen_name_{index_zone()}"))
    paires.append((f"campaign_map_playable_areas_onscreen_description_{INDEX_ZONE_WH1}",
                   f"campaign_map_playable_areas_onscreen_description_{index_zone()}"))
    return paires


def refaire_vanilla(c):
    """Les cles de localisation de Warhammer 3 (anglais par table, francais en un fichier)."""
    cles = set()
    with tempfile.TemporaryDirectory() as tmp:
        for langue in ("en", "fr"):
            pack = f"{DATA}local_{langue}.pack"
            c("open_packfiles", {"paths": [pack]})
            dest = os.path.join(tmp, langue)
            c("extract_packed_files", {"pack_key": pack, "destination_path": dest, "export_as_tsv": True,
                                       "source_paths": json.dumps({"PackFile": [{"Folder": "text"}]})})
            for racine, _, noms in os.walk(dest):
                for n in noms:
                    if n.endswith(".loc.tsv"):
                        with open(os.path.join(racine, n), encoding="utf-8") as f:
                            for i, ligne in enumerate(f):
                                if i >= 2 and "\t" in ligne:
                                    cles.add(ligne.split("\t", 1)[0])
    with gzip.open(VANILLA, "wt", encoding="utf-8") as f:
        f.write("\n".join(sorted(cles)))
    print(f"cles du jeu : {len(cles)} -> {VANILLA}")
    return cles


def lignes_loc(noms, textes):
    out = []
    for cle, valeur in sorted(textes.items()):
        ligne = []
        for n in noms:
            if n == "key":
                ligne.append({"StringU16": cle})
            elif n == "text":
                ligne.append({"StringU16": valeur})
            elif n == "tooltip":
                ligne.append({"Boolean": False})
            else:
                ligne.append({"StringU16": ""})
        out.append(ligne)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default=PACK)
    ap.add_argument("--pack-traduction", default=PACK_FR)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--vanilla", action="store_true", help="refaire la liste des cles du jeu")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    sid, i = None, [1]

    def c(tool, args):
        i[0] += 1
        return text(call(sid, tool, args, i[0]))

    if a.vanilla or not os.path.exists(VANILLA):
        sid = session()
        c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
        vanilla = refaire_vanilla(c)
    else:
        with gzip.open(VANILLA, "rt", encoding="utf-8") as f:
            vanilla = set(f.read().split("\n"))
    print(f"{len(vanilla)} cles connues du jeu")

    paires = paires_de_cles()
    propres_session = textes_session()
    if propres_session:
        print(f"  textes de la session d'audit : {len(propres_session)} clés ({DOSSIER_TEXTES_SESSION})")
    langues = {}
    for langue, chemin in TEXTES.items():
        brut = json.load(open(chemin, encoding="utf-8"))
        out = {}
        for cle, v in brut.items():
            for wh1, wh3 in paires:
                if wh1 in cle:
                    cle = cle.replace(wh1, wh3)
                    break
            brut_texte = v["text"].strip().lower()
            if brut_texte not in PLACEHOLDERS and not brut_texte.startswith("placeholder"):
                out[cle] = v["text"]
        for cle, t in {**TEXTES_PROPRES, **propres_session}.items():
            out[cle] = t[langue]
        langues[langue] = out
        print(f"  {langue} : {len(brut)} entrees de WH1, {len(out)} utiles")

    toutes = set(langues["fr"]) | set(langues["en"])
    du_jeu = toutes & vanilla
    propres = sorted(toutes - vanilla)
    finales = {}
    for langue, autre in (("fr", "en"), ("en", "fr")):
        finales[langue] = {k: langues[langue].get(k) or langues[autre][k] for k in propres}
        emprunts = sum(1 for k in propres if k not in langues[langue])
        print(f"  {langue} : {len(finales[langue])} textes, dont {emprunts} pris dans l'autre langue")
    print(f"  {len(du_jeu)} cles laissees au jeu (il les fournit dans chaque langue)")
    # Garde (23.09.2026, erreur 140) : un caractere de controle (U+0000 a U+001F, sauf saut de ligne et tabulation)
    # trahit une passe automatique ratee (« \1 » devenu U+0001 : 102 textes sans leur ponctuation).
    fautifs = [(langue, k) for langue in finales for k, t in finales[langue].items()
               if t and any(ord(c) < 32 and c not in "\n\r\t" for c in t)]
    if fautifs:
        raise SystemExit(f"!! {len(fautifs)} texte(s) avec un caractere de controle : {fautifs[:5]}")

    os.makedirs(COPIES, exist_ok=True)
    for langue, textes in finales.items():
        with open(os.path.join(COPIES, f"textes_{langue}.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("key\ttext\n")
            for k, t in sorted(textes.items()):
                lisible = t.replace("\t", " ").replace("\n", "\\n")
                f.write(f"{k}\t{lisible}\n")
    print(f"  copies lisibles : {COPIES}\\textes_fr.tsv, textes_en.tsv")

    zone = index_zone()
    for cle in (f"campaign_map_playable_areas_onscreen_name_{zone}",
                f"campaign_map_playable_areas_onscreen_description_{zone}",
                "start_pos_factions_description_2120137230",
                f"frontend_faction_leaders_loading_screen_text_{ORION}"):
        for langue in ("fr", "en"):
            print(f"     {langue} {cle[:62]:62s} {finales[langue].get(cle, '!! ABSENT')[:60]!r}")

    if not a.apply:
        print("\nEssai a blanc. Relancer avec --apply pour ecrire dans les packs.")
        return 0

    if sid is None:
        sid = session()
    c("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": True})

    for pack, langue in ((a.pack, LANGUE_PRINCIPALE), (a.pack_traduction, LANGUE_TRADUCTION)):
        if not os.path.exists(pack):
            c("new_pack", {})
            lst = json.loads(c("list_open_packs", {}))
            neuf = [e[0] if isinstance(e, list) else e for v in lst.values() for e in v][-1]
            c("save_pack_as", {"pack_key": neuf, "path": pack})
            c("close_all_packs", {})
            print(f"  pack cree : {pack}")
        c("open_packfiles", {"paths": [pack]})
        c("new_packed_file", {"pack_key": pack, "path": CHEMIN_LOC, "new_file": json.dumps({"Loc": NOM})})
        info = json.loads(c("decode_packed_file", {"pack_key": pack, "path": CHEMIN_LOC,
                                                    "source": "PackFile"}))["LocRFileInfo"][0]
        noms = [f["name"] for f in info["table"]["definition"]["fields"]]
        info["table"]["table_data"] = lignes_loc(noms, finales[langue])
        res = c("save_packed_file_from_view", {"pack_key": pack, "path": CHEMIN_LOC,
                                               "data": json.dumps({"Loc": info})})
        print(f"\n  {os.path.basename(pack)} ({langue}) : {res[:60]}")
        print("  enregistrement :", c("save_packfile", {"pack_key": pack})[:80])
        verif = json.loads(c("decode_packed_file", {"pack_key": pack, "path": CHEMIN_LOC,
                                                    "source": "PackFile"}))["LocRFileInfo"][0]
        print(f"  relu : {len(verif['table']['table_data'])} lignes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
