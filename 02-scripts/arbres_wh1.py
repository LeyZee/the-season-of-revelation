#!/usr/bin/env python3
"""
arbres_wh1.py - les arbres de campagne de Warhammer 1 dans Warhammer 3, avec LEURS modèles.

Pourquoi (22.09.2026) : Charles veut les arbres de WH1 (forêts bretonnes, clairières d'automne et
d'hiver d'Athel Loren...) avec leurs propres modèles : WH3 n'a aucun arbre d'automne et ses essences ne
sont pas celles de WH1. Nos arbres (21.09.2026) étaient des familles de WH3 (`FAMILLES_ARBRES`).

Comment WH3 place les arbres (relevé) : `tree.tif` du projet Terry (palette = `campaign_tree_ids`) ; BOB
(« Campaign Trees ») en fait `display\\trees\\trees.campaign_tree_list` : en-tête (version 4, bornes de
la carte), puis par **identifiant** d'arbre son nom et ses enregistrements de 15 octets (x, hauteur, z en
flottants, puis 3 octets). Le modèle est choisi **au chargement** : `campaign_tree_variants` (identifiant
x type d'arbre) et `campaign_tree_type_cultures` (culture du propriétaire -> type). Mais BOB ne connaît que
la base du jeu (`db.pack`) : un identifiant neuf n'y est pas.

D'où la recette :
1. `tree.tif` est peint avec une famille **porteuse** de WH3 par famille de WH1 (`PORTEUSES`, même
   nature : grand arbre, petit arbre, herbe, arbuste ; familles jamais employées ailleurs sur la carte) ;
2. après BOB, `recomposer()` réécrit la liste compilée : les enregistrements de chaque famille porteuse
   sont répartis, dans leur ordre (blocs spatiaux), entre les identifiants de WH1 de la couleur, préfixés
   `wh1_` (comme WH1, qui tirait au hasard parmi les identifiants d'une couleur) ;
3. nos lignes de base déclarent ces identifiants (`campaign_tree_ids`, couleur propre qui ne croise
   aucune couleur de WH3) et **toutes leurs variantes par culture de WH1** (`campaign_tree_variants`),
   avec les modèles de WH1 (`fichiers_wh1.Relocateur` : chemin de WH1, ou `_wh1/` si WH3 a un autre
   fichier au même chemin) et les sons d'arbres de WH3 équivalents (`SONS`). Aucune ligne de CA n'est
   touchée : les identifiants sont neufs.

Usage :
    python arbres_wh1.py            # bilan à blanc
    python arbres_wh1.py --apply    # écrit les lignes dans raw_data\\db du kit (sauvegarde db-backups)
"""

import argparse
import os
import random
import re
import struct
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KIT = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
ATELIER = r"C:\TotalWar-CampaignMap"
import carte_config                                                  # noqa: E402  (Saison Expanded, phase 1)
CARTE = carte_config.CARTE                                           # la cible (kit)
CARTE_SOURCE = carte_config.CARTE_SOURCE                             # WH1
DB_WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
DB_WH3 = os.path.join(KIT, "raw_data", "db")
ARBRES_WH1 = os.path.join(ATELIER, "03-references", "saison-des-revelations", CARTE_SOURCE, "trees.png")
LISTE_BOB = os.path.join(KIT, "working_data", "campaign_maps", CARTE, "display", "trees", "trees.campaign_tree_list")
PREFIXE = "wh1_"
# Les arbres d'Athel Loren (23.09.2026, 03 h 55 ; Charles, captures WH1 / WH3 : « tu as ajouté beaucoup de pins… dans
# Warhammer 1 il n'y a pas de pins ») : le modèle est choisi par la culture du propriétaire de la région ; une région en
# ruine, sans propriétaire ou tenue par les Hommes-bêtes (aucune variante de WH1 pour eux) prend la variante BASE, qui
# est un pin ou un feuillu de l'Empire (`gen_large_trees_01`, `emp_*`). Les arbres situés dans les provinces d'Athel Loren
# passent sous des identifiants `wh1_al_*` dont la variante BASE est celle des elfes sylvains ; les autres cultures
# (Bretonnie, Chaos, vampires...) gardent leurs variantes de WH1. Ailleurs, rien ne change.
PREFIXE_AL = "wh1_al_"
# L'OCTET 12 DES ARBRES (24.09.2026, 02 h 30, session du rendu, piste du plantage de rendu TILE_DATABASE ; brouillons
# `controle_arbres.py`, `arbres_sans_base.py`) : dans chaque enregistrement (x, y, z en f32, puis 3 octets), BOB écrit 1
# à l'octet 12 pour toutes les cartes de WH3 (Empires 241 116 arbres, prologue 17 799, notre carte 80 453) ; la liste de
# WH1, que `liste_wh1` recopie, a 0 partout. On écrit la valeur de WH3.
OCTET_12_COMME_BOB = True
# LA VARIANTE BASE DE SECOURS (24.09.2026, même piste) : 5 identifiants de WH1 n'ont pas de variante BASE, celle que le jeu
# prend quand la culture du propriétaire n'a pas de variante (ruine, sans propriétaire, Hommes-bêtes, Peaux-vertes...) :
# wh1_tree_small_5 (4 129 arbres, CHAOS et EMPIRE seulement), wh1_shrubs_grass_4 / 5 et wh1_al_shrubs_grass_4 / 5 (1 218
# buissons). CA : 1 identifiant sur 267. Ils reçoivent une BASE : le modèle des elfes sylvains pour `wh1_al_*`, sinon celui
# de la variante EMPIRE (`bases_de_secours`).
BASE_DE_SECOURS = True
ECART_COULEUR_MAX = 16
# la liste compilée des arbres de WH1 (packs de WH1) et la nôtre, écrite par terrain_wh1_vers_terry.py, embarquée par
# build_pack.py à la place de celle de BOB
LISTE_WH1 = f"campaign_maps/{CARTE_SOURCE}/display/trees/trees.campaign_tree_list"
SORTIE_LISTE = carte_config.dans_projet("arbres-wh1", "trees.campaign_tree_list")
Z_HEX = 3 ** 0.5 / 2                           # z de la liste (espace des hex) -> monde

# famille de WH1 -> famille porteuse de WH3 (dans la palette de tree.tif, de même nature)
PORTEUSES = {
    "brt_trees_large": "tree_large_palm",
    "tree_large": "tree_large_jungle", "tree_med": "tree_large_jungle",
    "wef_aut_tree_large": "tree_large_snow_pro", "wef_aut_tree_medium": "tree_large_snow_pro",
    "wef_win_tree_large": "tree_large_snow_pro_tze", "wef_win_tree_medium": "tree_large_snow_pro_tze",
    "tree_small": "tree_small_jungle",
    "wef_aut_tree_small": "tree_small_snow_pro",
    "wef_win_tree_small": "tree_small_snow_pro_tze",
    "grass": "grass_desert_def",
    "wef_wild_grass": "grass_snow_pro_tze",
    "shrubs_grass": "shrubs_desert_def",
    "wef_wild_shrubs_grass": "shrubs_desert",
    "marsh": "shrubs_swamp",
    "marsh_shrubs": "shrubs_mtn",
}
# sons d'arbres de WH1 -> clés de audio_campaign_tree_types de WH3
SONS = {"": "", "greenskins": "Tree_Type_Audio_Greenskins", "empire": "Tree_Type_Audio_Empire",
        "bretonnia": "Tree_Type_Audio_Bretonnia", "vampire": "Tree_Type_Audio_Vampire",
        "chaos": "Tree_Type_Audio_Chaos", "nordic": "Tree_Type_Audio_Norsca", "dwarfs": "Tree_Type_Audio_Dwarfs",
        "wood_elves_generic": "Tree_Type_Audio_Wood_Elves", "wood_elves_winter": "Tree_Type_Audio_Wood_Elves",
        "wood_elves_autumn": "Tree_Type_Audio_Wood_Elves"}


def lire_liste(octets):
    """(en-tête de 20 octets, [(identifiant, enregistrements (n, 15) uint8)]) d'une `trees.campaign_tree_list` v4."""
    if struct.unpack_from("<I", octets, 0)[0] != 4:
        raise SystemExit("trees.campaign_tree_list : version 4 attendue")
    n = struct.unpack_from("<I", octets, 20)[0]
    o, groupes = 24, []
    for _ in range(n):
        ln = struct.unpack_from("<H", octets, o)[0]
        o += 2
        nom = octets[o:o + ln].decode("ascii")
        o += ln
        cnt = struct.unpack_from("<I", octets, o)[0]
        o += 4
        groupes.append((nom, np.frombuffer(octets, np.uint8, count=15 * cnt, offset=o).reshape(cnt, 15)))
        o += 15 * cnt
    if o != len(octets):
        raise SystemExit("trees.campaign_tree_list : fin de fichier inattendue")
    return octets[:20], groupes


def lignes_db(dossier, table):
    t = open(os.path.join(dossier, table + ".xml"), encoding="utf-8").read()
    return [dict(re.findall(r"<(\w+)(?:\s[^>]*)?>([^<]*)</\1>", m.group(1)))
            for m in re.finditer(rf"<{table}\b[^>]*>(.*?)</{table}>", t, re.S)]


def famille(tree_id):
    return re.sub(r"_\d+$", "", tree_id)


def masque_athel_loren(H, L):
    """Raster (H x L, ligne 0 au nord, 8 px par hex, la grille des rasters du terrain) : True dans les provinces
    d'Athel Loren (calque Regions de CAIME, noms dans l'ordre de CAIME, provinces du kit)."""
    import captage_campagne as CC
    import donnees_campagne as DC
    from terrain_wh1_vers_terry import hex_de_pixel
    reg, sol = CC.calques()                                  # ligne 0 au sud
    noms = CC.noms_regions()
    provinces = DC.nos_regions()
    dans = np.array([provinces.get(n, "").replace("wh_dlc05_", "") in DC.PROVINCES_ATHEL_LOREN for n in noms] + [False])
    idx = np.where((reg >= 0) & (reg < len(noms)), reg, len(noms))
    al_hex = dans[idx]
    col8, lig8 = hex_de_pixel(L, H, 8)
    return al_hex[lig8, col8]


class ArbresWH1:
    def __init__(self):
        self.ids1 = lignes_db(DB_WH1, "campaign_tree_ids")
        self.var1 = lignes_db(DB_WH1, "campaign_tree_variants")
        self.ids3 = lignes_db(DB_WH3, "campaign_tree_ids")
        self.types3 = {r["tree_type"] for r in lignes_db(DB_WH3, "campaign_tree_types")}
        self.sons3 = {r["key"] for r in lignes_db(DB_WH3, "audio_campaign_tree_types")} | {""}
        self.couleur1 = {r["tree_id"]: (int(r["colour_r"]), int(r["colour_g"]), int(r["colour_b"])) for r in self.ids1}
        self.couleur_famille3 = {}
        for r in self.ids3:
            self.couleur_famille3.setdefault(famille(r["tree_id"]), (int(r["colour_r"]), int(r["colour_g"]), int(r["colour_b"])))
        self.ids3_par_famille = defaultdict(list)
        for r in self.ids3:
            self.ids3_par_famille[famille(r["tree_id"])].append(r["tree_id"])
        # identifiants de WH1 employés : ceux des familles de PORTEUSES
        self.ids = sorted(r["tree_id"] for r in self.ids1 if famille(r["tree_id"]) in PORTEUSES)
        self.par_porteuse = defaultdict(list)
        for i in self.ids:
            self.par_porteuse[PORTEUSES[famille(i)]].append(i)
        # identifiants qui ont une variante des elfes sylvains : leurs arbres d'Athel Loren passent sous `wh1_al_*`
        self.modele_elfe = {v["tree_id"]: v["tree_rigid"] for v in self.var1
                            if v["tree_type"] == "WOODELVES" and v["tree_id"] in self.ids}
        self.ids_elfes = sorted(self.modele_elfe)
        self.controle()

    def controle(self):
        for f, p in PORTEUSES.items():
            if p not in self.couleur_famille3:
                raise SystemExit(f"famille porteuse inconnue de WH3 : {p}")
        # une porteuse ne sert qu'à une couleur de WH1
        for p, ids in self.par_porteuse.items():
            couleurs = {self.couleur1[i] for i in ids}
            if len(couleurs) != 1:
                raise SystemExit(f"porteuse {p} : plusieurs couleurs de WH1 {couleurs}")

    def porteuse_de_famille(self, famille_wh1):
        return PORTEUSES.get(famille_wh1)

    def couleur_propre(self):
        """Couleurs des identifiants neufs (clés sans préfixe ; `al:` devant pour ceux d'Athel Loren) : aucune ne croise
        une couleur de WH3 (la table sert à BOB)."""
        prises = {(int(r["colour_r"]), int(r["colour_g"]), int(r["colour_b"])) for r in self.ids3}
        out, k = {}, 1
        for i in list(self.ids) + ["al:" + e for e in self.ids_elfes]:
            while (3, 3, k) in prises:
                k += 1
            out[i] = (3, 3, k)
            k += 1
        return out

    def lignes(self, relocateur):
        """{table : [(clé, champs rendus)]} pour le kit ; et le bilan des modèles."""
        from declare_map import plain
        couleurs = self.couleur_propre()
        ids_rows, var_rows, modeles, ignores = [], [], {}, []
        can = {r["tree_id"]: r.get("can_be_removed", "0") for r in self.ids1}
        saison = {r["tree_id"]: r.get("season", "ALL") or "ALL" for r in self.ids1}
        for i, cle, prefixe in ([(i, i, PREFIXE) for i in self.ids] +
                                [(e, "al:" + e, PREFIXE_AL) for e in self.ids_elfes]):
            r, g, b = couleurs[cle]
            ids_rows.append((prefixe + i, [plain("can_be_removed", can[i]), plain("colour_b", b), plain("colour_g", g),
                                           plain("colour_r", r), plain("season", saison[i]),
                                           plain("tree_id", prefixe + i)]))
        for v in self.var1:
            if v["tree_id"] not in self.ids:
                continue
            if v["tree_type"] not in self.types3:
                ignores.append((v["tree_id"], v["tree_type"]))
                continue
            copies = [(PREFIXE, v["tree_rigid"])]
            if v["tree_id"] in self.modele_elfe:        # Athel Loren : la BASE prend le modèle des elfes sylvains
                copies.append((PREFIXE_AL, self.modele_elfe[v["tree_id"]] if v["tree_type"] == "BASE"
                               else v["tree_rigid"]))
            son = SONS.get(v.get("tree_audio", ""), "")
            if son not in self.sons3:
                son = ""
            for prefixe, rigide in copies:
                modele = rigide.replace("\\", "/").lower()
                final = relocateur.cible(modele)
                if final is None:
                    raise SystemExit(f"modèle de WH1 introuvable : {modele}")
                modeles[modele] = final
                var_rows.append((prefixe + v["tree_id"] + v["tree_type"],
                                 [plain("tree_id", prefixe + v["tree_id"]), plain("tree_type", v["tree_type"]),
                                  plain("tree_rigid", final), plain("tree_audio", son), plain("receive_decals", 0)]))
        if BASE_DE_SECOURS:
            var_rows += self.bases_de_secours(var_rows, relocateur, modeles)
        return {"campaign_tree_ids": ids_rows, "campaign_tree_variants": var_rows}, modeles, ignores

    def bases_de_secours(self, var_rows, relocateur, modeles):
        """Lignes BASE des identifiants qui n'en ont pas (BASE_DE_SECOURS) : modèle des elfes sylvains pour `wh1_al_*`, sinon
        celui de la variante EMPIRE, sinon de la première variante (ordre alphabétique des types)."""
        par_id = defaultdict(dict)
        for cle, champs in var_rows:
            d = {c[0]: c[1] for c in ((m.group(1), m.group(2)) for m in
                                      (re.match(r"<(\w+)>([^<]*)</\1>", str(ch)) for ch in champs) if m)}
            par_id[d.get("tree_id", "")][d.get("tree_type", "")] = (d.get("tree_rigid", ""), d.get("tree_audio", ""))
        neuves = []
        from declare_map import plain
        for tid, types in sorted(par_id.items()):
            if not tid or "BASE" in types:
                continue
            if tid.startswith(PREFIXE_AL) and tid[len(PREFIXE_AL):] in self.modele_elfe:
                modele = self.modele_elfe[tid[len(PREFIXE_AL):]].replace("\\", "/").lower()
                rigide, son = relocateur.cible(modele), types.get("WOODELVES", ("", ""))[1]
                modeles[modele] = rigide
            else:
                rigide, son = types.get("EMPIRE") or types[sorted(types)[0]]
            neuves.append((tid + "BASE", [plain("tree_id", tid), plain("tree_type", "BASE"), plain("tree_rigid", rigide),
                                          plain("tree_audio", son), plain("receive_decals", 0)]))
        print(f"  arbres : variantes BASE de secours ajoutées pour {len(neuves)} identifiants "
              f"{[c[:-4] for c, _ in neuves]}")
        return neuves

    def cles(self):
        return tuple(PREFIXE + i for i in self.ids) + tuple(PREFIXE_AL + e for e in self.ids_elfes)

    # ------------------------------------------------------------------ liste d'arbres de WH1, telle quelle
    def liste_wh1(self, sol_nous, sol_wh1, pas, hors=None):
        """La liste compilée des arbres de WH1 (22.09.2026, 22 h ; Charles : « chaque arbre à sa position de WH1 ») :
        même format que celle de WH3 (version 4, bornes 266,53 x 339,77, z en espace des hex), 80 457 arbres en
        45 essences, chacun avec sa position et son orientation (octet 13, 0 à 5) ; essences renommées `wh1_*`,
        hauteur recalée de ce dont notre sol diffère de celui de WH1 sous l'arbre (rasters ligne 0 au nord, `pas` px
        par unité). `hors` (23.09.2026, session du rendu) : raster de même grille, True là où aucun arbre n'est planté (eau
        des étangs de `etangs_wh1`). Rend (octets, {identifiant : nombre})."""
        from modeles_wh1 import SourceWH1
        brut = SourceWH1().lire(LISTE_WH1)
        if brut is None:
            raise SystemExit(f"{LISTE_WH1} absent des packs de WH1")
        tete, groupes = lire_liste(brut)
        nous_ = np.asarray(sol_nous, np.float64)
        eux_ = np.asarray(sol_wh1, np.float64)
        ecart = nous_ - eux_
        H, L = ecart.shape

        def sous(xs, zs, raster=ecart):
            cx = np.clip(xs * pas - 0.5, 0, L - 1.001)
            cy = np.clip((H - 1.5) - zs * pas, 0, H - 1.001)
            c0, r0 = np.floor(cx).astype(int), np.floor(cy).astype(int)
            fx, fy = cx - c0, cy - r0
            return (raster[r0, c0] * (1 - fx) * (1 - fy) + raster[r0, c0 + 1] * fx * (1 - fy)
                    + raster[r0 + 1, c0] * (1 - fx) * fy + raster[r0 + 1, c0 + 1] * fx * fy)

        al = masque_athel_loren(H, L)                           # arbres d'Athel Loren : `wh1_al_*`
        blocs = []
        noyes = 0
        for nom, recs in groupes:
            if nom not in self.ids:
                raise SystemExit(f"arbre de WH1 {nom} : identifiant non déclaré (PORTEUSES)")
            xyz = recs[:, :12].copy().view("<f4").reshape(-1, 3).astype(np.float64)
            # un arbre au sec dans WH1 que notre rivage adouci (`terrain_wh1_vers_terry.rivage_naturel`) met sous l'eau
            # n'est pas planté (23.09.2026 : 4 arbres)
            garde = ~((sous(xyz[:, 0], xyz[:, 2] * Z_HEX, nous_) < 0) & (sous(xyz[:, 0], xyz[:, 2] * Z_HEX, eux_) >= 0))
            if hors is not None:
                c = np.clip(np.rint(xyz[:, 0] * pas - 0.5), 0, L - 1).astype(int)
                r = np.clip(np.rint((H - 1.5) - xyz[:, 2] * Z_HEX * pas), 0, H - 1).astype(int)
                dans_eau = hors[r, c]
                garde &= ~dans_eau
                self.dans_etangs = getattr(self, "dans_etangs", 0) + int(dans_eau.sum())
            noyes += int((~garde).sum())
            recs, xyz = recs[garde], xyz[garde]
            y = xyz[:, 1] + sous(xyz[:, 0], xyz[:, 2] * Z_HEX)
            neuf = recs.copy()
            neuf[:, 4:8] = y.astype("<f4").view(np.uint8).reshape(-1, 4)
            if OCTET_12_COMME_BOB:
                neuf[:, 12] = 1
            if nom in self.modele_elfe:
                c = np.clip(np.rint(xyz[:, 0] * pas - 0.5), 0, L - 1).astype(int)
                r = np.clip(np.rint((H - 1.5) - xyz[:, 2] * Z_HEX * pas), 0, H - 1).astype(int)
                dedans = al[r, c]
                blocs.append((PREFIXE + nom, neuf[~dedans]))
                blocs.append((PREFIXE_AL + nom, neuf[dedans]))
            else:
                blocs.append((PREFIXE + nom, neuf))
        blocs = [(cle, n) for cle, n in blocs if len(n)]
        out = bytearray(tete) + struct.pack("<I", len(blocs))
        comptes = {}
        for cle, n in blocs:
            out += struct.pack("<H", len(cle)) + cle.encode("ascii") + struct.pack("<I", len(n)) + n.tobytes()
            comptes[cle] = len(n)
        if noyes:
            print(f"  arbres de WH1 mis sous l'eau (rivage adouci, étangs : {getattr(self, 'dans_etangs', 0)}), "
                  f"non plantés : {noyes}")
        n_al = sum(v for k, v in comptes.items() if k.startswith(PREFIXE_AL))
        print(f"  arbres d'Athel Loren sous les identifiants {PREFIXE_AL}* (BASE = modèle des elfes sylvains) : {n_al}")
        return bytes(out), comptes

    # ------------------------------------------------------------------ liste d'arbres compilée (ancienne recette)
    def recomposer(self, octets, graine=20260922):
        version = struct.unpack_from("<I", octets, 0)[0]
        if version != 4:
            raise SystemExit(f"trees.campaign_tree_list : version {version} (attendu 4)")
        tete = octets[:20]
        n = struct.unpack_from("<I", octets, 20)[0]
        o = 24
        groupes = []
        for _ in range(n):
            ln = struct.unpack_from("<H", octets, o)[0]
            o += 2
            nom = octets[o:o + ln].decode("ascii")
            o += ln
            cnt = struct.unpack_from("<I", octets, o)[0]
            o += 4
            groupes.append((nom, [octets[o + 15 * k:o + 15 * k + 15] for k in range(cnt)]))
            o += 15 * cnt
        if o != len(octets):
            raise SystemExit("trees.campaign_tree_list : fin de fichier inattendue")
        rng = random.Random(graine)
        sortie = defaultdict(list)
        etrangers = []
        for nom, recs in groupes:
            p = famille(nom)
            if p in self.par_porteuse:
                cibles = self.par_porteuse[p]
                for rec in recs:
                    sortie[PREFIXE + cibles[rng.randrange(len(cibles))]].append(rec)
            else:
                etrangers.append(nom)
                sortie[nom].extend(recs)
        total_avant = sum(len(r) for _, r in groupes)
        total_apres = sum(len(r) for r in sortie.values())
        assert total_avant == total_apres, (total_avant, total_apres)
        out = bytearray(tete) + struct.pack("<I", len(sortie))
        for nom in sorted(sortie):
            out += struct.pack("<H", len(nom)) + nom.encode("ascii") + struct.pack("<I", len(sortie[nom]))
            out += b"".join(sortie[nom])
        return bytes(out), etrangers, {k: len(v) for k, v in sortie.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    from declare_map import Table
    from fichiers_wh1 import Relocateur
    A = ArbresWH1()
    print(f"{len(A.ids)} identifiants d'arbres de WH1 ; porteuses : "
          + ", ".join(f"{p} <- {len(v)}" for p, v in sorted(A.par_porteuse.items())))
    r = Relocateur()
    lignes, modeles, ignores = A.lignes(r)
    print(f"variantes : {len(lignes['campaign_tree_variants'])} ; modèles de WH1 : {len(modeles)} "
          f"(dont déplacés : {sum(1 for m, f in modeles.items() if m != f)}) ; types ignorés : {ignores}")
    print(r.bilan())
    if os.path.exists(SORTIE_LISTE):
        _, groupes = lire_liste(open(SORTIE_LISTE, "rb").read())
        print(f"liste des arbres de WH1 écrite : {sum(len(r) for _, r in groupes)} arbres en {len(groupes)} identifiants")
    sauvegarde = os.path.join(ATELIER, "05-journal", "db-backups", datetime.now().strftime("%Y%m%d-%H%M%S") + "-arbres-wh1")
    for table, recs in lignes.items():
        t = Table(KIT, table)
        for cle, champs in recs:
            if not t.replace(cle, champs):
                t.add(cle, champs)
        print(f"  {table:28s} ajouté {len(t.added):3d}  mis à jour {len(t.updated):3d}  inchangé {len(t.skipped):3d}")
        if a.apply and (t.added or t.updated):
            t.save(sauvegarde)
    print(f"sauvegardes : {sauvegarde}" if a.apply else "essai à blanc : relancer avec --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
