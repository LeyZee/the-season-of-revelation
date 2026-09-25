#!/usr/bin/env python3
"""
donnees_campagne.py - donne à notre campagne les lignes de base que CA écrit pour la sienne (étape 1 du gameplay de
WH3, `05-journal\\2026-09-22-gameplay-wh3\\plan.md` et `donnees-campagne-manquantes.md`).

Pourquoi (23.09.2026) : beaucoup de systèmes de WH3 lisent des lignes propres à chaque carte, campagne, région,
province ou faction (sons du sol, Imperium, vents de magie, seigneurs recrutables...). Notre campagne n'en avait
presque aucune : 15 de nos factions ne pouvaient recruter ni seigneur ni héros, pas d'Imperium, pas de corruption,
pas de vents de magie (relevé de la session d'audit, 23.09.2026, 00 h 30).

Méthode, toujours dans `raw_data\\db\\<table>.xml` du kit :
- RECOPIE : une ligne de CA (sélectionnée par une colonne) est recopiée sous nos clés ; `record_key` est la
  concaténation des colonnes clés, on y remplace la première occurrence de l'ancienne clé ;
- AJOUT : une ligne neuve est faite sur le corps d'une ligne modèle de CA (même ordre de colonnes, mêmes attributs),
  valeurs remplacées ;
- une ligne déjà présente (même `record_key`) n'est jamais réécrite ; `record_uuid` neuf, horodatage du moment ;
- sauvegarde de chaque XML touché dans `05-journal\\db-backups\\<date>-donnees-campagne\\` avant écriture.
Le script affiche les entrées à donner à `build_pack.TABLES` (table du kit, table du jeu, colonne, préfixe ou liste).

Usage :
    python donnees_campagne.py --table <t> --colonne <c> --de <valeur de CA> --vers <notre valeur> [--apply]
    python donnees_campagne.py --lot etape1 [--apply]      # tout le lot 1 (aucune table du startpos)
    python donnees_campagne.py --lot etape2|...|etape11 [--apply]   # DLC et nains ; finale ; quêtes ;
                                                                              # captage ; interface ; forêt à nous ;
                                                                              # écrans des seigneurs ; startpos (horde, traits,
                                                                              # relever les morts)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import uuid
from datetime import datetime

ATELIER = r"C:\TotalWar-CampaignMap"
KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
CAMPAGNE = "wh_dlc05_wood_elves"
CARTE = "wh_dlc05_wood_elves_map_1"
IE = "wh3_main_combi"


class TableKit:
    """Une table XML du kit : lecture, recopie et ajout de lignes, écriture avec sauvegarde."""

    def __init__(self, nom):
        self.nom = nom
        self.chemin = os.path.join(KIT_DB, nom + ".xml")
        self.texte = open(self.chemin, encoding="utf-8").read()
        motif = re.compile(rf'<{nom} record_uuid="\{{[^}}]*\}}" record_timestamp="\d+" record_key="([^"]*)">(.*?)</{nom}>',
                           re.S)
        self.lignes = [(m.group(1), m.group(2)) for m in motif.finditer(self.texte)]
        self.cles = {k for k, _ in self.lignes}
        self.neuves = []
        self.deja = 0
        self.retirees = set()
        self.modifiees = {}

    @staticmethod
    def valeurs(corps):
        d = {}
        for c in re.findall(r"<([a-zA-Z0-9_]+)(?: [^>]*)?>(.*?)</\1>|<([a-zA-Z0-9_]+)\s*/>", corps, re.S):
            if c[0]:
                d[c[0]] = c[1]
            else:
                d[c[2]] = ""
        return d

    @staticmethod
    def avec(corps, col, val):
        """Le corps avec la colonne `col` valant `val` (balise pleine ou vide)."""
        nouveau, n = re.subn(rf"(<{col}(?: [^>]*)?>)[^<]*(</{col}>)", lambda m: m.group(1) + val + m.group(2), corps,
                             count=1)
        if n == 0:
            nouveau, n = re.subn(rf"<{col}\s*/>", f"<{col}>{val}</{col}>", corps, count=1)
        if n == 0:
            raise KeyError(f"colonne {col} absente d'une ligne de {TableKit.__name__}")
        return nouveau

    def ou(self, **egal):
        """Lignes (clé, corps) dont les colonnes valent exactement les valeurs données."""
        out = []
        for k, corps in self.lignes:
            d = self.valeurs(corps)
            if all(d.get(c) == v for c, v in egal.items()):
                out.append((k, corps))
        return out

    def ajouter(self, cle, corps):
        if cle in self.cles:
            self.deja += 1
            return False
        self.neuves.append(f'<{self.nom} record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{int(time.time() * 1000)}" '
                           f'record_key="{cle}">{corps}</{self.nom}>\n')
        self.cles.add(cle)
        return True

    def recopier(self, colonne, de, vers, sauf=None, autres=None):
        """Recopie les lignes où `colonne` == `de` sous `vers` ; `sauf(valeurs)` écarte des lignes ; `autres` = {col:
        valeur} remplacés en plus (hors clé). Rend le nombre de lignes neuves."""
        n = 0
        for k, corps in self.ou(**{colonne: de}):
            if sauf and sauf(self.valeurs(corps)):
                continue
            corps2 = self.avec(corps, colonne, vers)
            for c, v in (autres or {}).items():
                corps2 = self.avec(corps2, c, v)
            n += self.ajouter(k.replace(de, vers, 1), corps2)
        return n

    def modele(self, **egal):
        """Clé de la première ligne dont les colonnes valent les valeurs données."""
        lignes = self.ou(**egal)
        if not lignes:
            raise KeyError(f"{self.nom} : aucune ligne modèle {egal}")
        return lignes[0][0]

    def ajouter_sur_modele(self, cle_modele, valeurs):
        """Ligne neuve faite sur le corps de la ligne `cle_modele`, colonnes remplacées par `valeurs`. Sa clé est celle
        du modèle où chaque ancienne valeur changée (clés de 3 caractères et plus) est remplacée par la nouvelle : la
        clé d'enregistrement du kit est la concaténation des colonnes clés."""
        corps = dict(self.lignes)[cle_modele]
        anciennes = self.valeurs(corps)
        cle = cle_modele
        for c, v in valeurs.items():
            corps = self.avec(corps, c, v)
            vieux = anciennes.get(c, "")
            if len(vieux) >= 3 and vieux != v and vieux in cle:
                cle = cle.replace(vieux, v, 1)
        return self.ajouter(cle, corps)

    def retirer(self, cle):
        """Retire la ligne `cle` (23.09.2026 : nos propres lignes seulement, jamais une ligne de CA ; l'appelant choisit
        par nos clés). Rend True si la ligne existait."""
        if cle not in self.cles or cle in self.retirees:
            return False
        self.retirees.add(cle)
        return True

    def modifier(self, cle, valeurs):
        """Change des colonnes (hors clé) de la ligne `cle` (23.09.2026 : nos propres lignes seulement, jamais une ligne
        de CA ; l'appelant choisit par notre campagne). Rend True si une valeur change."""
        if cle not in self.cles or cle in self.retirees:
            raise KeyError(f"{self.nom} : ligne {cle} absente")
        actuelles = self.valeurs(dict(self.lignes)[cle])
        changees = {c: v for c, v in valeurs.items() if actuelles.get(c) != v}
        if changees:
            self.modifiees.setdefault(cle, {}).update(changees)
        return bool(changees)

    def ecrire(self, dossier):
        if not self.neuves and not self.retirees and not self.modifiees:
            return 0
        os.makedirs(dossier, exist_ok=True)
        if not os.path.exists(os.path.join(dossier, os.path.basename(self.chemin))):
            shutil.copy2(self.chemin, dossier)
        texte = self.texte
        for cle in self.retirees:
            texte, n = re.subn(rf'<{self.nom} record_uuid="\{{[^}}]*\}}" record_timestamp="\d+" '
                               rf'record_key="{re.escape(cle)}">.*?</{self.nom}>\r?\n?', "", texte, count=1, flags=re.S)
            if n != 1:
                raise SystemExit(f"{self.nom} : ligne {cle} introuvable à l'écriture")
        for cle, valeurs in self.modifiees.items():
            m = re.search(rf'(<{self.nom} record_uuid="\{{[^}}]*\}}" record_timestamp=")\d+(" record_key="{re.escape(cle)}">)'
                          rf'(.*?)(</{self.nom}>)', texte, re.S)
            if not m:
                raise SystemExit(f"{self.nom} : ligne {cle} introuvable à l'écriture")
            corps = m.group(3)
            for c, v in valeurs.items():
                corps = self.avec(corps, c, v)
            texte = (texte[:m.start()] + m.group(1) + str(int(time.time() * 1000)) + m.group(2) + corps + m.group(4)
                     + texte[m.end():])
        fin = texte.rindex("</dataroot>")
        with open(self.chemin, "w", encoding="utf-8", newline="") as f:
            f.write(texte[:fin] + "".join(self.neuves) + texte[fin:])
        return len(self.neuves) + len(self.retirees) + len(self.modifiees)


def recopier(table, colonne, de, vers, appliquer=False, dossier_sauvegarde=None):
    """Recopie les lignes (colonne == de) sous `vers`. Rend (nouvelles lignes, déjà présentes)."""
    t = TableKit(table)
    t.recopier(colonne, de, vers)
    if appliquer:
        t.ecrire(dossier_sauvegarde or os.path.join(
            ATELIER, "05-journal", "db-backups", datetime.now().strftime("%Y%m%d-%H%M%S") + "-donnees-campagne"))
    return t.neuves, t.deja


# --- Le lot 1 : données sans table du startpos -------------------------------------------------------------------

CLAIRIERES = ["wh_dlc05_wef_anmyr", "wh_dlc05_wef_arranoc", "wh_dlc05_wef_atylwyth", "wh_dlc05_wef_cavaroc",
              "wh_dlc05_wef_cythral", "wh_dlc05_wef_fyr_darric", "wh_dlc05_wef_modryn", "wh_dlc05_wef_tirsyth"]
DUCHES = ["wh_dlc05_brt_brionne", "wh_dlc05_brt_gisoroux", "wh_dlc05_brt_montfort", "wh_dlc05_brt_quenelles"]
HARDE = "wh_dlc03_bst_beastmen_brayherd"
FACTIONS_QB = ["wh_dlc05_wef_wood_elves_qb1", "wh_dlc05_wef_wood_elves_qb2", "wh_dlc05_wef_wood_elves_qb3",
               "wh_dlc03_bst_beastmen_qb1", "wh_dlc03_bst_beastmen_qb2", "wh_dlc03_bst_beastmen_qb3",
               "wh_main_vmp_vampire_counts_qb1", "wh_main_vmp_vampire_counts_qb2", "wh_main_vmp_vampire_counts_qb3"]
FACTIONS_WAAAGH = ["wh_main_grn_teef_snatchaz_waaagh", "wh_main_grn_skullsmasherz_waaagh"]
SEIGNEURS_LEGENDAIRES_BST = {"wh_dlc03_bst_khazrak", "wh_dlc03_bst_malagor", "wh_dlc05_bst_morghur"}
# Seigneurs et héros légendaires de la campagne : les 6 présents, Ariel (rituel de forêt) et le Chevalier vert.
LEGENDAIRES = ["wh_dlc05_wef_orion", "wh_dlc05_wef_durthu", "wh_dlc05_bst_morghur", "wh_dlc05_vmp_red_duke",
               "wh_dlc07_brt_alberic", "wh_dlc07_brt_fay_enchantress", "wh2_dlc16_wef_ariel", "wh_dlc07_brt_green_knight"]
# (table, colonne de la faction) des 5 tables « par faction » que toutes les factions ordinaires de l'IE remplissent
TABLES_FACTION = [("faction_agent_permitted_subtypes", "faction"), ("faction_rebellion_units_junctions", "faction_key"),
                  ("faction_to_faction_groups_junctions", "faction_key"),
                  ("campaign_map_attrition_faction_immunities", "faction"),
                  ("climbing_ladders_meshes_definitions", "faction_key")]
PROVINCES_ATHEL_LOREN = {"anmyr", "argwylon", "arranoc", "atylwyth", "cavaroc", "cythral", "fyr_darric", "modryn",
                         "oak_of_ages", "talsyn", "tirsyth", "torgovann", "wydrioth"}
PROVINCES_BRETONNIE = {"aquitaine", "bastonne", "bordeleaux", "brionne", "carcassonne", "gisoreux", "montfort",
                       "parravon", "quenelles", "mousillon"}
LISIERE = ["wh_dlc05_carcassonne_summersfall_fort", "wh_dlc05_parravon_grunere", "wh_dlc05_parravon_montlac",
           "wh_dlc05_quenelles_quenelles"]
GROUPE_LISIERE = "wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border"
CHENE = "wh_dlc05_oak_of_ages"
# groupe de forêt à nous pour Athel Loren (Worldroots.forests.athel_loren.region_group dans saison_foret.lua) : le Chêne
# et ses 4 régions de lisière (23.09.2026, 20 h : erreur 110 par le groupe de CA wh2_dlc16_forest_region_group_main_1)
GROUPE_FORET_ATHEL_LOREN = "wh_dlc05_saison_forest_region_group_athel_loren"


def nos_regions():
    """{région: province} de nos régions terrestres (jonctions région → province du kit)."""
    t = TableKit("region_to_province_junctions")
    out = {}
    for _k, corps in t.lignes:
        d = t.valeurs(corps)
        if d.get("region", "").startswith("wh_dlc05_"):
            out[d["region"]] = d["province"]
    return out


def ident_numerique(graine, pris):
    """Identifiant entier de 9 à 10 chiffres, stable (sha1 de la graine), hors des clés `pris`."""
    n = int(hashlib.sha1(f"{CAMPAGNE}:{graine}".encode()).hexdigest()[:8], 16) % 1_900_000_000 + 100_000_000
    while str(n) in pris:
        n += 1
    return str(n)


def lot_etape1():
    """Rend ({table: TableKit}, [entrées TABLES]) sans rien écrire."""
    tables, entrees = {}, []

    def T(nom):
        if nom not in tables:
            tables[nom] = TableKit(nom)
        return tables[nom]

    def entree(table, colonne, valeur):
        e = (table, table + "_tables", colonne, valeur)
        if e not in entrees:
            entrees.append(e)

    regions = nos_regions()
    provinces = sorted(set(regions.values()))

    # 1. Les 15 factions sans données de faction : recopie d'une faction modèle de même culture.
    modeles = [(f, "wh_dlc05_wef_torgovann", None) for f in CLAIRIERES]
    modeles += [(f, "wh_main_brt_bastonne", None) for f in DUCHES]
    modeles += [(HARDE, "wh_dlc03_bst_beastmen", lambda d: d.get("subtype") in SEIGNEURS_LEGENDAIRES_BST)]
    for table, col in TABLES_FACTION:
        for cible, modele, sauf in modeles:
            T(table).recopier(col, modele, cible, sauf=sauf if table == "faction_agent_permitted_subtypes" else None)
        entree(table, col, [f for f, _, _ in modeles])

    # 2. Imperium : les 19 paliers des Empires, identifiants neufs, et leurs plafonds de héros.
    fl, fj = T("fame_levels"), T("fame_level_agent_record_junctions")
    neufs = []
    # collisions jugées sur les clés des AUTRES campagnes : nos propres paliers déjà écrits gardent leur identifiant
    pris = {k for k, c in fl.lignes if TableKit.valeurs(c).get("campaign") != CAMPAGNE}
    for k, corps in fl.ou(campaign=IE):
        n = ident_numerique(f"fame_level:{k}", pris)
        corps2 = TableKit.avec(TableKit.avec(corps, "campaign", CAMPAGNE), "key", n)
        if fl.ajouter(n, corps2):
            neufs.append(n)
        for kj, cj in fj.ou(fame_level=k):
            fj.ajouter(kj.replace(k, n, 1), TableKit.avec(cj, "fame_level", n))
    entree("fame_levels", "campaign", CAMPAGNE)
    entree("fame_level_agent_record_junctions", "fame_level",
           sorted(TableKit.valeurs(c)["key"] for k, c in fl.ou(campaign=CAMPAGNE)) or neufs)

    # 3. Corruption : notre campagne entre dans le groupe `wh3_main_corruption_campaigns`.
    membre = f"wh3_main_corruption_campaigns_{CAMPAGNE}"
    cgm = T("campaign_group_members")
    cgm.ajouter_sur_modele(cgm.modele(id=f"wh3_main_corruption_campaigns_{IE}"), {"id": membre})
    cgc = T("campaign_group_member_criteria_campaigns")
    cgc.ajouter_sur_modele(cgc.modele(member=f"wh3_main_corruption_campaigns_{IE}"),
                           {"member": membre, "campaign": CAMPAGNE})
    entree("campaign_group_member_criteria_campaigns", "campaign", CAMPAGNE)

    # 4. Diplomatie : factions de bataille de quête et factions Waaagh! de WH1 hors de l'écran diplomatique.
    cdx = T("cai_diplomacy_excluded_factions")
    m = cdx.modele(faction="wh2_main_chs_chaos_incursion_def", campaign=IE)
    for f in FACTIONS_QB + FACTIONS_WAAAGH:
        cdx.ajouter_sur_modele(m, {"faction": f, "campaign": CAMPAGNE})
    entree("cai_diplomacy_excluded_factions", "campaign", CAMPAGNE)

    # 5. Caméra bornée à la zone jouable (partie entière, règle de CA) ; chemin de bataille déclaré.
    cb = T("campaign_camera_map_bounds")
    cb.ajouter_sur_modele(cb.modele(campaign=IE), {"campaign": CAMPAGNE, "max_x": "266", "max_y": "338",
                                                   "min_x": "0", "min_y": "0"})
    entree("campaign_camera_map_bounds", "campaign", CAMPAGNE)
    bp = T("campaign_battle_paths")
    bp.ajouter_sur_modele(bp.modele(path="wh3_main_combi_map"), {"path": CARTE})
    entree("campaign_battle_paths", "path", [CARTE])

    # 6. Seigneurs et héros légendaires de la campagne.
    cta = T("campaign_to_agent_subtypes")
    m = cta.modele(campaign_type=IE)
    for s in LEGENDAIRES:
        cta.ajouter_sur_modele(m, {"campaign_type": CAMPAGNE, "agent_subtype": s})
    entree("campaign_to_agent_subtypes", "campaign_type", CAMPAGNE)

    # 7. Vents de magie : un groupe de régions par province (même clé), une zone de vents par province.
    rg, rj, wm = T("region_groups"), T("regions_to_region_groups_junctions"), T("campaign_map_winds_of_magic_areas")
    m_rg = rg.modele(group_key="wh3_main_combi_province_talsyn")
    m_wm = wm.modele(key="wh3_main_combi_province_talsyn")
    for p in provinces:
        rg.ajouter_sur_modele(m_rg, {"group_key": p})
        wm.ajouter_sur_modele(m_wm, {"key": p, "region_group": p, "campaign": CAMPAGNE})
    modele_j = rj.modele(region_group="wh3_main_combi_province_talsyn")
    for r, p in sorted(regions.items()):
        rj.ajouter_sur_modele(modele_j, {"region_group": p, "region": r, "order": "0"})
    entree("region_groups", "group_key", "wh_dlc05_")
    entree("campaign_map_winds_of_magic_areas", "campaign", CAMPAGNE)

    # 8. IA par zone et Elfes sylvains : nos régions rejoignent les groupes de CA qui décrivent le même lieu.
    def zone(p):
        return p.replace("wh_dlc05_", "")
    athel = sorted(r for r, p in regions.items() if zone(p) in PROVINCES_ATHEL_LOREN)
    bret = sorted(r for r, p in regions.items() if zone(p) in PROVINCES_BRETONNIE)
    nains = sorted(r for r, p in regions.items() if zone(p) == "grey_mountains_2")
    cols = sorted(r for r, p in regions.items() if zone(p) == "grey_mountains")
    rattachements = {"cai_region_hint_area_athel_loren": athel, "wh3_wood_elf_forests": athel,
                     "cai_region_hint_area_bretonnia": bret, "cai_region_hint_area_dwarf_empire": nains,
                     "cai_region_hint_sub_area_western_mountains": nains + cols,
                     GROUPE_FORET_ATHEL_LOREN: [CHENE] + LISIERE,
                     }
    # 23.09.2026, 20 h (plantage de Durthu au tour 6, Warhammer3.exe+0x272AE00, erreur 110 par une autre porte) : nos
    # régions ne rejoignent plus le groupe de forêt de CA wh2_dlc16_forest_region_group_main_1, qui garde les régions
    # des Empires (dont leur Chêne des Âges) : l'infobulle des clairières parcourt le groupe et reçoit un objet NUL. Un
    # groupe à nous, cité par saison_foret.lua (Worldroots.forests.athel_loren.region_group) ; nos anciennes lignes
    # dans le groupe de CA sont retirées.
    rg.ajouter_sur_modele(m_rg, {"group_key": GROUPE_FORET_ATHEL_LOREN})
    for k, corps in list(rj.lignes):
        v = rj.valeurs(corps)
        if v.get("region_group") == "wh2_dlc16_forest_region_group_main_1" and v.get("region", "").startswith("wh_dlc05_"):
            rj.retirer(k)
    for g, liste in rattachements.items():
        for r in liste:
            rj.ajouter_sur_modele(modele_j, {"region_group": g, "region": r, "order": "0"})
    entree("regions_to_region_groups_junctions", "region", "wh_dlc05_")
    prr = T("pooled_resource_to_region_junctions")
    prr.ajouter_sur_modele(prr.modele(region="wh3_main_combi_region_the_oak_of_ages"), {"region": CHENE})
    entree("pooled_resource_to_region_junctions", "region", "wh_dlc05_")
    rr = T("rituals_to_regions")
    rr.ajouter_sur_modele(rr.modele(region="wh3_main_combi_region_the_oak_of_ages"), {"region": CHENE})
    entree("rituals_to_regions", "region", "wh_dlc05_")
    # Lisière : options « défricher / occuper la lande » des Elfes sylvains sur les 4 régions qui bordent la forêt.
    cgr, cgs = T("campaign_group_member_criteria_regions"), T("campaign_group_member_criteria_subcultures")
    m_modele = f"{GROUPE_LISIERE}_wh3_main_combi_region_akendorf"
    k_m, k_r, k_s = cgm.modele(id=m_modele), cgr.modele(member=m_modele), cgs.modele(member=m_modele)
    membres = []
    for r in LISIERE:
        m = f"{GROUPE_LISIERE}_{r}"
        membres.append(m)
        cgm.ajouter_sur_modele(k_m, {"id": m})
        cgr.ajouter_sur_modele(k_r, {"member": m, "region": r})
        cgs.ajouter_sur_modele(k_s, {"member": m})
    entree("campaign_group_members", "id", [membre] + membres)
    entree("campaign_group_member_criteria_regions", "region", "wh_dlc05_")
    entree("campaign_group_member_criteria_subcultures", "member", membres)

    # 9. Audio de la carte.
    acm = T("audio_campaign_maps")
    acm.ajouter_sur_modele(acm.modele(key="wh3_main_combi_map_2"), {"key": CARTE})
    entree("audio_campaign_maps", "key", [CARTE])
    for t in ("audio_campaign_environment_static_sounds", "audio_campaign_environment_tree_sound_assignments"):
        T(t).recopier("map", "wh3_main_combi_map_5", CARTE)
        entree(t, "map", CARTE)
    arg = T("audio_campaign_region_group_assignments")
    modele_v = arg.modele(region_group="Region_Group_Vampires")
    for r in sorted(r for r, p in regions.items() if zone(p) == "mousillon"):
        arg.ajouter_sur_modele(modele_v, {"region": r})
    entree("audio_campaign_region_group_assignments", "region", "wh_dlc05_")

    # 10. Réglages de campagne recopiés des Empires (sans l'affichage du Vortex).
    T("campaigns_campaign_variables_junctions").recopier(
        "campaign_name", IE, CAMPAGNE, sauf=lambda d: d.get("variable_key", "").startswith("display_vortex"))
    entree("campaigns_campaign_variables_junctions", "campaign_name", CAMPAGNE)
    for t, c in (("cai_variables_overides", "campaign_key"), ("resources_to_campaign_junctions", "campaign"),
                 ("campaign_difficulty_handicap_effects", "optional_campaign_key"),
                 ("character_experience_skill_tiers", "optional_campaign_key")):
        T(t).recopier(c, IE, CAMPAGNE)
        entree(t, c, CAMPAGNE)

    # 11. Citations des écrans de chargement (celles de la première version de la carte des Empires).
    T("loading_screen_quotes_to_campaigns").recopier("campaign", "wh3_main_combi_map_1", CARTE)
    entree("loading_screen_quotes_to_campaigns", "campaign", CARTE)
    return tables, entrees


ZONE_JOUABLE = "1758400002"          # campaign_map_playable_areas.index de notre carte
GROUPES_NAINS = {                     # groupes lus par grudge_cycle:setup() (préfixe + nom de campagne)
    f"dwarf_historical_legendary_{CAMPAGNE}": [],
    f"dwarf_historical_holds_{CAMPAGNE}": ["wh_dlc05_grey_mountains_2_karak_ziflin"],
    f"dwarf_historical_other_{CAMPAGNE}": ["wh_dlc05_grey_mountains_2_karak_tzor", "wh_dlc05_grey_mountains_2_blackstone_post"],
}


def lot_etape2():
    """Lot 2 (23.09.2026) : verrou du DLC « Realm of the Wood Elves » sur l'écran de campagne, et groupes de régions
    historiques des nains (cycles de rancunes). Rend ({table: TableKit}, [entrées TABLES])."""
    tables, entrees = {}, []

    def T(nom):
        if nom not in tables:
            tables[nom] = TableKit(nom)
        return tables[nom]

    # 1. Notre carte rattachée aux paquets de contenu, comme les cartes de CA (wh3_base_game) : wh1_wood_elves exige
    #    le produit TW_WH1_WOOD_ELVES. Sans lui, l'écran de sélection verrouille la campagne (raison + boutique).
    # 25.09.2026, 17 h 05 (demande de Charles : retenter le verrou de la campagne entière, avec UN SEUL paquet) : les
    # zones de CA n'ont chacune qu'une ligne (kit 9.0 : wh3_base_game ou wh3_roc_update, aucune zone à paquet de DLC) ;
    # nos deux lignes (wh3_base_game + wh1_wood_elves) sont l'hypothèse de la fermeture au démarrage du 23.09 (erreur
    # 107). Seul wh1_wood_elves reste ; notre ligne wh3_base_game est retirée. Essai de démarrage obligatoire.
    oj = T("campaign_map_playable_area_ownership_content_pack_junctions")
    m = oj.modele(campaign_map_playable_area="1024396413", ownership_content_pack="wh3_base_game")
    oj.ajouter_sur_modele(m, {"campaign_map_playable_area": ZONE_JOUABLE, "ownership_content_pack": "wh1_wood_elves"})
    for k, corps in oj.lignes:
        v = oj.valeurs(corps)
        if v.get("campaign_map_playable_area") == ZONE_JOUABLE and v.get("ownership_content_pack") == "wh3_base_game":
            oj.retirer(k)
    entrees.append(("campaign_map_playable_area_ownership_content_pack_junctions",
                    "campaign_map_playable_area_ownership_content_pack_junctions_tables",
                    "campaign_map_playable_area", [ZONE_JOUABLE]))

    # 2. Groupes de régions historiques des nains de notre campagne (sans eux, lookup_regions_from_region_group échoue
    #    ou rend vide) ; les jonctions partent avec l'entrée « région wh_dlc05_ » du lot 1.
    rg, rj = T("region_groups"), T("regions_to_region_groups_junctions")
    m_rg = rg.modele(group_key="dwarf_historical_holds_main_warhammer")
    m_rj = rj.modele(region_group="dwarf_historical_holds_main_warhammer")
    for g, regions in GROUPES_NAINS.items():
        rg.ajouter_sur_modele(m_rg, {"group_key": g})
        for r in regions:
            rj.ajouter_sur_modele(m_rj, {"region_group": g, "region": r, "order": "0"})
    return tables, entrees


MISSION_FINALE = "wh_dlc05_qb_wef_mini_silver_spire"


def lot_etape3():
    """Lot 3 (23.09.2026) : l'histoire de WH1. La mission de la bataille finale du Pic d'Argent, sous sa clé de WH1
    (ses textes français et anglais sont déjà dans nos textes), faite sur celle des Empires Immortels (même bataille
    `wh_dlc05_qb_wef_grand_silver_spire`), à l'emplacement de WH1 (121, 249) ; lignes du directeur de campagne recopiées
    de la « défense du Chêne » des Empires, les mêmes que dans WH1 : durée infinie, sans cible, chance 100, 7 500 or,
    émetteur CLAN_ELDERS. Rend ({table: TableKit}, [entrées TABLES])."""
    tables, entrees = {}, []

    def T(nom):
        if nom not in tables:
            tables[nom] = TableKit(nom)
        return tables[nom]

    mi = T("missions")
    mi.ajouter_sur_modele(mi.modele(key="wh_dlc05_qb_wef_grand_silver_spire"),
                          {"key": MISSION_FINALE, "location_x": "121", "location_y": "249"})

    modele = "wh_dlc05_qb_wef_grand_defense_of_the_oak"
    oj = T("cdir_events_mission_option_junctions")
    pris = {k for k, c in oj.lignes if oj.valeurs(c).get("mission_key") != MISSION_FINALE}
    for option in ("VAR_MISSION_LENGTH_INFINITE", "GEN_TARGET_NONE", "VAR_CHANCE"):
        oj.ajouter_sur_modele(oj.modele(mission_key=modele, option_key=option),
                              {"id": ident_numerique(f"mission_option:{MISSION_FINALE}:{option}", pris),
                               "mission_key": MISSION_FINALE})
    pa = T("cdir_events_mission_payloads")
    pris = {k for k, c in pa.lignes if pa.valeurs(c).get("mission_key") != MISSION_FINALE}
    pa.ajouter_sur_modele(pa.modele(mission_key=modele, status_key="SUCCESS", payload_key="TREASURY"),
                          {"id": ident_numerique(f"mission_payload:{MISSION_FINALE}:SUCCESS:TREASURY", pris),
                           "mission_key": MISSION_FINALE})
    ij = T("cdir_events_mission_issuer_junctions")
    ij.ajouter_sur_modele(ij.modele(mission_key=modele), {"mission_key": MISSION_FINALE})

    for table in ("missions", "cdir_events_mission_option_junctions", "cdir_events_mission_payloads",
                  "cdir_events_mission_issuer_junctions"):
        entrees.append((table, table + "_tables", "key" if table == "missions" else "mission_key", [MISSION_FINALE]))
    return tables, entrees


KIT_WH1 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER\assembly_kit\raw_data\db"
QUETES_WH1 = [  # les 17 missions des quatre chaînes de quêtes de la mini-campagne (la finale du Pic d'Argent : lot 3)
    "wh_dlc05_wef_orion_horn_of_the_wild_stage_1_mini", "wh_dlc05_wef_orion_horn_of_the_wild_stage_2_mini",
    "wh_dlc05_wef_orion_horn_of_the_wild_stage_3a_mini",
    "wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold_mini",
    "wh_dlc05_wef_orion_cloak_of_isha_stage_1_mini", "wh_dlc05_wef_orion_cloak_of_isha_stage_2_mini",
    "wh_dlc05_wef_orion_cloak_of_isha_stage_3a_mini",
    "wh_dlc05_qb_wef_orion_the_cloak_of_isha_stage_3_the_night_glens_mini",
    "wh_dlc05_wef_orion_spear_of_kurnous_stage_1_mini", "wh_dlc05_wef_orion_spear_of_kurnous_stage_2_mini",
    "wh_dlc05_wef_orion_spear_of_kurnous_stage_3a_mini",
    "wh_dlc05_qb_wef_orion_the_spear_of_kurnous_stage_3_the_oak_of_ages_mini",
    "wh_dlc05_wef_durthu_sword_of_daith_stage_1_mini", "wh_dlc05_wef_durthu_sword_of_daith_stage_2_mini",
    "wh_dlc05_wef_durthu_sword_of_daith_stage_3a_mini",
    "wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini",
    "wh_dlc05_wef_durthu_sword_of_daith_stage_4a_mini",
    "wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns_mini",
]
ASHENHALL = "wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini"
BATAILLES_WH3 = {  # bataille de WH1 -> bataille de WH3 (mêmes carte et script ; WH3 a retiré le suffixe _mini)
    "wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold_mini":
        "wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold",
    "wh_dlc05_qb_wef_orion_the_cloak_of_isha_stage_3_the_night_glens_mini":
        "wh_dlc05_qb_wef_orion_the_cloak_of_isha_stage_3_the_night_glens",
    "wh_dlc05_qb_wef_orion_the_spear_of_kurnous_stage_3_the_oak_of_ages_mini":
        "wh_dlc05_qb_wef_orion_the_spear_of_kurnous_stage_3_the_oak_of_ages",
    "wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns_mini":
        "wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns",
    ASHENHALL: ASHENHALL,               # absente de WH3 : recréée par le lot 4 (carte et script sont dans WH3)
}
# colonnes des missions reprises de WH1 (les autres, propres à WH3, viennent de la ligne modèle)
COLONNES_MISSION_WH1 = ["mission_type", "localised_title", "localised_description", "ui_image", "ui_icon", "generate",
                        "prioritised", "event_category", "set_piece_battle", "location_x", "location_y", "quest_mission",
                        "trigger_radius", "quest_character", "quest_mission_final", "sticky_by_default"]
# récompense de WH3 de ces mêmes quêtes aux Empires, à la place de l'ambre-nourriture de WH1 (sans emploi dans WH3)
RECOMPENSE_WH3 = ("EFFECT_BUNDLE", "KEY[wh3_dlc20_payload_effect_casualty_replenishment];DURATION[2]")


def lignes_wh1(table):
    """Lignes (dictionnaires) d'une table du kit de WH1."""
    texte = open(os.path.join(KIT_WH1, table + ".xml"), encoding="utf-8").read()
    return [TableKit.valeurs(m.group(1)) for m in re.finditer(rf"<{table}(?: [^>]*)?>(.*?)</{table}>", texte, re.S)]


def options_wh3(lignes):
    """Options du directeur de WH1 -> WH3 (relevé du 23.09.2026 sur les options employées par WH3) :
    - GEN_CND_REGION_ANY_OF n'existe plus : une seule région, GEN_CND_REGION (la première de la liste de WH1) ;
    - VAR_OBJECTIVE_CHARACTER_ID n'existe plus : « vaincre N armées avec ce personnage » s'écrit dans WH3
      GEN_TARGET_CHARACTER + GEN_CND_CHARACTER_ID + VAR_OBJECTIVE_REQUIRES_VICTORY (quêtes de Kalara) ;
    - les remparts de WH1 (wh_dlc05_wef_walls_3) n'existent plus : la garnison de niveau 3 des Elfes sylvains de WH3,
      constructible dans les colonies majeures d'Athel Loren."""
    par_personnage = any(o == "VAR_OBJECTIVE_CHARACTER_ID" for o, _v in lignes)
    out = []
    for o, v in lignes:
        if o == "GEN_CND_REGION_ANY_OF":
            o, v = "GEN_CND_REGION", v.split(";")[0]
        elif o == "VAR_OBJECTIVE_CHARACTER_ID":
            o = "GEN_CND_CHARACTER_ID"
        elif o == "GEN_TARGET_NONE" and par_personnage:
            o = "GEN_TARGET_CHARACTER"
        elif o == "VAR_OBJECTIVE_BUILDING_LEVEL" and v == "wh_dlc05_wef_walls_3":
            v = "wh_dlc05_wef_garrison_3"
        out.append((o, v))
    if par_personnage:
        out.append(("VAR_OBJECTIVE_REQUIRES_VICTORY", ""))
    return out


def lot_etape4():
    """Lot 4 (23.09.2026) : les quêtes de WH1 (décision de Charles : ses chaînes, pas les batailles seules des Empires).
    17 missions sous leurs clés de WH1 (textes FR et EN déjà dans nos textes), faites sur la mission finale des Empires,
    colonnes reprises de la base de WH1 ; batailles de WH3 (les mêmes sans _mini), Ashenhall recréée (lot 4, batailles) ;
    lignes du directeur de WH1 (options adaptées à WH3 par options_wh3, 1 500 or par étape, objets, suites, émetteur) ;
    l'ambre-nourriture de WH1 remplacée par la récompense de WH3 de ces mêmes quêtes. Rend ({table: TableKit},
    [entrées TABLES])."""
    tables, entrees = {}, []

    def T(nom):
        if nom not in tables:
            tables[nom] = TableKit(nom)
        return tables[nom]

    nos = set(QUETES_WH1) | {MISSION_FINALE}

    def pris_et_vus(t):
        return {k for k, c in t.lignes if t.valeurs(c).get("mission_key") not in nos}

    def nouvel_id(graine, pris, vus):
        n = ident_numerique(graine, pris | vus)
        vus.add(n)
        return n

    w_missions = {l["key"]: l for l in lignes_wh1("missions") if l["key"] in nos}
    manquantes = sorted(set(QUETES_WH1) - set(w_missions))
    if manquantes:
        raise KeyError(f"missions absentes de la base de WH1 : {manquantes}")

    mi = T("missions")
    modele_mission = mi.modele(key="wh_dlc05_qb_wef_grand_silver_spire")
    for cle in QUETES_WH1:
        w = w_missions[cle]
        valeurs = {"key": cle}
        for col in COLONNES_MISSION_WH1:
            valeurs[col] = w.get(col, "")
        if valeurs["set_piece_battle"]:
            valeurs["set_piece_battle"] = BATAILLES_WH3[valeurs["set_piece_battle"]]
        mi.ajouter_sur_modele(modele_mission, valeurs)

    oj = T("cdir_events_mission_option_junctions")
    pris, vus = pris_et_vus(oj), set()
    modele_option = oj.modele(mission_key="wh_dlc05_qb_wef_grand_defense_of_the_oak", option_key="GEN_TARGET_NONE")
    w_options = {}
    for l in lignes_wh1("cdir_events_mission_option_junctions"):
        if l.get("mission_key") in QUETES_WH1:
            w_options.setdefault(l["mission_key"], []).append((l["option_key"], l.get("value", "")))
    for cle in QUETES_WH1:
        for option, valeur in options_wh3(sorted(w_options.get(cle, []))):
            oj.ajouter_sur_modele(modele_option, {"id": nouvel_id(f"mission_option:{cle}:{option}", pris, vus),
                                                  "mission_key": cle, "option_key": option, "value": valeur})

    pa = T("cdir_events_mission_payloads")
    pris, vus = pris_et_vus(pa), set()
    modele_charge = pa.modele(mission_key="wh_dlc05_qb_wef_grand_defense_of_the_oak", status_key="SUCCESS",
                              payload_key="TREASURY")
    for l in lignes_wh1("cdir_events_mission_payloads"):
        if l.get("mission_key") not in QUETES_WH1:
            continue
        charge, valeur = l["payload_key"], l.get("value", "")
        if re.match(r"^wh_dlc05_wood_elves_gain_amber_quests_key_\d$", charge):
            charge, valeur = RECOMPENSE_WH3
        pa.ajouter_sur_modele(modele_charge, {
            "id": nouvel_id(f"mission_payload:{l['mission_key']}:{l['status_key']}:{charge}", pris, vus),
            "mission_key": l["mission_key"], "status_key": l["status_key"], "payload_key": charge, "value": valeur})

    fu = T("cdir_events_mission_followup_missions")
    modele_suite = fu.lignes[0][0]
    for l in lignes_wh1("cdir_events_mission_followup_missions"):
        if l.get("mission_key") in QUETES_WH1:
            fu.ajouter_sur_modele(modele_suite, {"mission_key": l["mission_key"], "status_key": l["status_key"],
                                                 "followup_mission_key": l["followup_mission_key"]})

    ij = T("cdir_events_mission_issuer_junctions")
    modele_emetteur = ij.modele(mission_key="wh_dlc05_qb_wef_grand_defense_of_the_oak")
    for l in lignes_wh1("cdir_events_mission_issuer_junctions"):
        if l.get("mission_key") in QUETES_WH1:
            ij.ajouter_sur_modele(modele_emetteur, {"mission_key": l["mission_key"], "issuer_key": l["issuer_key"]})

    toutes = [MISSION_FINALE] + QUETES_WH1
    for table in ("missions", "cdir_events_mission_option_junctions", "cdir_events_mission_payloads",
                  "cdir_events_mission_issuer_junctions", "cdir_events_mission_followup_missions"):
        entrees.append((table, table + "_tables", "key" if table == "missions" else "mission_key", toutes))
    entrees += bataille_ashenhall(T)
    return tables, entrees


# Ashenhall (1re bataille de la quête de Durthu dans WH1) : retirée de WH3, mais sa carte (terrain/battles/
# qb_dlc05_the_ashenhall, ambiance night_cloudy_02), son script (durthu/daiths_sword_1), son image de chargement et
# toutes ses unités de bataille y sont. Refaite sur les lignes de la bataille des Cairns (même quête, colonnes de WH3),
# avec les valeurs de WH1 ; ce qui n'existe plus dans WH3 est pris chez CA pour le même sous-type.
CAIRNS = "wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns"
SOUS_TYPES_WH3 = {"dlc04_vmp_strigoi_ghoul_king": "wh_dlc04_vmp_strigoi_ghoul_king",
                  "dlc05_wef_glade_lord_fem": "wh_dlc05_wef_glade_lord_fem", "dlc05_wef_durthu": "wh_dlc05_wef_durthu"}
FACTIONS_WH3 = {"wh_dlc05_wef_mini_argwylon": "wh_dlc05_wef_argwylon", "wh_dlc05_wef_mini_wood_elves": "wh_dlc05_wef_wood_elves"}


def bataille_ashenhall(T):
    """Ajoute la bataille d'Ashenhall aux tables battle_set_piece* ; rend les entrées TABLES."""
    w_bataille = next(l for l in lignes_wh1("battle_set_pieces") if l["battle_name"] == ASHENHALL)
    w_jonctions = [l for l in lignes_wh1("battle_set_piece_armies_junctions") if l["battle_name"] == ASHENHALL]
    armees = [l["army_name"] for l in w_jonctions]
    w_armees = {l["army_name"]: l for l in lignes_wh1("battle_set_piece_armies") if l["army_name"] in armees}
    w_pj = [l for l in lignes_wh1("battle_set_piece_armies_characters_junctions") if l["army_name"] in armees]
    persos = [l["character_name"] for l in w_pj]
    w_persos = {l["character_name"]: l for l in lignes_wh1("battle_set_piece_armies_characters") if l["character_name"] in persos}
    w_competences = [l for l in lignes_wh1("battle_set_piece_armies_characters_skills") if l["character_name"] in persos]
    w_unites = [l for l in lignes_wh1("battle_set_piece_armies_units_junctions") if l["army_name"] in armees]

    bs = T("battle_set_pieces")
    bs.ajouter_sur_modele(bs.modele(battle_name=CAIRNS), {
        "battle_name": ASHENHALL, "battle_script": w_bataille["battle_script"],
        "battle_environment": "weather/battle/wh_night_cloudy_02.environment_group",   # environments.csv de la carte
        "localised_name": w_bataille["localised_name"], "localised_description": w_bataille["localised_description"],
        "battlefield_folder": w_bataille["battlefield_folder"], "game_expansion_key": w_bataille["game_expansion_key"],
        "teleport_cost": w_bataille["teleport_cost"], "is_player_attacker": w_bataille["is_player_attacker"],
        "screenshot_path": "ui/frontend ui/battle_map_images/dlc05_ashenhall.png"})

    ja = T("battle_set_piece_armies_junctions")
    m_ja = ja.modele(battle_name=CAIRNS)
    for a in armees:
        ja.ajouter_sur_modele(m_ja, {"battle_name": ASHENHALL, "army_name": a})

    # armées modèles : celles des Cairns (camp du joueur : Argwylon ; ennemi : les vampires), emblèmes de WH3 gardés
    ar = T("battle_set_piece_armies")
    armees_cairns = {ja.valeurs(c)["army_name"] for _k, c in ja.ou(battle_name=CAIRNS)}
    modeles = {}
    for k, c in ar.lignes:
        v = ar.valeurs(c)
        if v["army_name"] in armees_cairns:
            modeles.setdefault(v["faction"] == "wh_dlc05_wef_argwylon", k)
    for a in armees:
        w = w_armees[a]
        joueur = w["faction"] in FACTIONS_WH3 or w["is_allied_to_player"] == "1"
        m = modeles[joueur]
        ar.ajouter_sur_modele(m, {
            "army_name": a, "faction": FACTIONS_WH3.get(w["faction"], w["faction"]),
            "is_allied_to_player": w["is_allied_to_player"], "is_reinforcement_army": w["is_reinforcement_army"],
            "army_onscreen_name": w["army_onscreen_name"], "army_model": w["army_model"],
            "approach_angle": w["approach_angle"], "deployment_zone_id": w["deployment_zone_id"],
            "ai_army_tactic": w.get("ai_army_tactic", ""), "is_frontend_player_army": w["is_frontend_player_army"],
            "use_default_deployment_zones": w["use_default_deployment_zones"], "is_hidden_army": w["is_hidden_army"]})

    pe = T("battle_set_piece_armies_characters")
    for c in persos:
        w = w_persos[c]
        sous_type = SOUS_TYPES_WH3.get(w["agent_subtype"], w["agent_subtype"])
        m = pe.modele(agent_subtype=sous_type)             # portrait et modèle de WH3 du même sous-type
        pe.ajouter_sur_modele(m, {
            "character_name": c, "unit_type": w["unit_type"], "forename": w["forename"], "surname": w["surname"],
            "magic_lore": w.get("magic_lore", ""), "num_men": w["num_men"], "character_level": w["character_level"],
            "agent_type": w["agent_type"], "agent_subtype": sous_type, "character_model": w["character_model"],
            "skillset": w.get("skillset", ""), "male": w["male"]})

    pj = T("battle_set_piece_armies_characters_junctions")
    m_pj = pj.lignes[0][0]
    for l in w_pj:
        pj.ajouter_sur_modele(m_pj, {"army_name": l["army_name"], "character_name": l["character_name"],
                                     "script_name": l.get("script_name", "")})

    co = T("battle_set_piece_armies_characters_skills")
    m_co = co.lignes[0][0]
    for l in w_competences:
        co.ajouter_sur_modele(m_co, {"character_name": l["character_name"], "skill": l["skill"], "level": l["level"]})

    un = T("battle_set_piece_armies_units_junctions")
    m_un = un.lignes[0][0]
    for l in w_unites:
        un.ajouter_sur_modele(m_un, {"army_name": l["army_name"], "unit_name": l["unit_name"],
                                     "script_name": l.get("script_name", ""), "number_of_unit": l["number_of_unit"]})

    return [("battle_set_pieces", "battle_set_pieces_tables", "battle_name", [ASHENHALL]),
            ("battle_set_piece_armies_junctions", "battle_set_piece_armies_junctions_tables", "battle_name", [ASHENHALL]),
            ("battle_set_piece_armies", "battle_set_piece_armies_tables", "army_name", armees),
            ("battle_set_piece_armies_characters", "battle_set_piece_armies_characters_tables", "character_name", persos),
            ("battle_set_piece_armies_characters_junctions", "battle_set_piece_armies_characters_junctions_tables",
             "army_name", armees),
            ("battle_set_piece_armies_characters_skills", "battle_set_piece_armies_characters_skills_tables",
             "character_name", persos),
            ("battle_set_piece_armies_units_junctions", "battle_set_piece_armies_units_junctions_tables", "army_name",
             armees)]


ZONES_CAPTAGE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "captage", "zones.json")


def lot_etape5():
    """Lot 5 (23.09.2026) : cartes de bataille par lieu. Les zones que captage_campagne.py a peintes sur nos 3 cartes de
    captage reçoivent les lignes des Empires Immortels pour ces mêmes zones (même géographie : Bretonnie, Athel Loren,
    Mousillon, Montagnes grises), sous notre chemin de bataille ; sans les lignes qui exigent une amélioration de tuile
    (camps ogres, corruption), absentes de notre carte. La zone par défaut (« Gatekeeper », noir : la mer et tout
    pixel non peint) garde les lignes des Empires (batailles navales, souterraines, embuscades des Hommes-bêtes et des
    Elfes) et reçoit, en repli, les batailles terrestres des prairies bretonnes et les sièges des colonies bretonnes.
    Rend ({table: TableKit}, [entrées TABLES])."""
    tables = {"battle_catchment_override_battle_mappings": TableKit("battle_catchment_override_battle_mappings")}
    t = tables["battle_catchment_override_battle_mappings"]
    zones = set(json.load(open(ZONES_CAPTAGE, encoding="utf-8"))["zones"])
    repli = {"wh3_main_macro_brt_grasslands", "wh3_main_brt_settlement_2"}
    for k, corps in list(t.lignes):
        v = t.valeurs(corps)
        if v.get("battle_path") != "wh3_main_combi_map" or v.get("required_tile_upgrades"):
            continue
        if v["area"] in zones or v["area"] == "Gatekeeper":
            t.ajouter_sur_modele(k, {"battle_path": CARTE})
        if v["area"] in repli and v["attacker"] == "*" and v["defender"] == "*":
            t.ajouter_sur_modele(k, {"area": "Gatekeeper", "battle_path": CARTE})
    return tables, [("battle_catchment_override_battle_mappings", "battle_catchment_override_battle_mappings_tables",
                     "battle_path", [CARTE])]


CITATIONS = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "citations-chargement.json")
TEXTES_PROJET = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "textes")
VIDEO_INTRO = "warhammer/race_intro_wef_mini"
# notre écran de chargement -> (écran de CA recopié, fiche de WH1 dont le récit de chargement devient la citation)
ECRANS_CHARGEMENT = {
    "wh_dlc05_wef_wood_elves_orion_mini": ("wh_dlc05_wef_wood_elves_orion",
                                           "wh_dlc05_political_party_mini_wood_elves_ruler"),
    "wh_dlc05_wef_argwylon_durthu_mini": ("wh_dlc05_wef_argwylon_durthu",
                                          "wh_dlc05_political_party_mini_wood_elves_durthu"),
}


def texte_projet(cle, langue="en"):
    """Un texte de nos .tsv (textes_fr.tsv / textes_en.tsv de la construction)."""
    with open(os.path.join(TEXTES_PROJET, f"textes_{langue}.tsv"), encoding="utf-8", newline="") as f:
        for ligne in f:
            k, _, v = ligne.rstrip("\r\n").partition("\t")
            if k == cle:
                return v
    raise KeyError(cle)


def lot_etape6():
    """Lot 6 (23.09.2026, audit de l'interface `05-journal\\2026-09-22-gameplay-wh3\\audit-interface.md`) :
    - C2 : citations de chargement de notre carte triées (`citations-chargement.json`) : les 436 des Empires moins les 2
      conseils de mécaniques absentes, les 48 fiches d'unités de races absentes de la carte et les 93 citations qui
      parlent d'autres lieux ou races ; restent 293 ;
    - E5 : la vidéo d'intro de la mini-campagne de WH1 (`movies/warhammer/race_intro_wef_mini.ca_vp8`, fichier de WH1
      embarqué par la construction), jouée par `saison_intro.lua` avant la scène Cindy, comme les intros de WH3 ;
    - C1 : écrans de chargement d'Orion et de Durthu, sur ceux de CA (fond `campaign_wood_elves1.png`), avec pour
      citation le récit de chargement de WH1 ; le script de menu `script/frontend/mod/saison_ecrans_de_chargement.lua`
      relie nos seigneurs à ces écrans.
    Rend ({table: TableKit}, [entrées TABLES])."""
    from xml.sax.saxutils import escape
    tables = {n: TableKit(n) for n in ("loading_screen_quotes_to_campaigns", "videos", "custom_loading_screens",
                                       "custom_loading_screen_components")}
    tq = tables["loading_screen_quotes_to_campaigns"]
    a_retirer = set(json.load(open(CITATIONS, encoding="utf-8"))["retirer"])
    for k, corps in tq.lignes:
        v = tq.valeurs(corps)
        if v.get("campaign") == CARTE and v.get("loading_quote") in a_retirer:
            tq.retirer(k)

    tables["videos"].ajouter_sur_modele("Front_end_selection_movies/orion_front_end", {"video_name": VIDEO_INTRO})

    ts, tc = tables["custom_loading_screens"], tables["custom_loading_screen_components"]
    for neuf, (modele, fiche) in ECRANS_CHARGEMENT.items():
        ts.ajouter_sur_modele(modele, {"key": neuf})
        recit = texte_projet(f"frontend_faction_leaders_loading_screen_text_{fiche}")
        for k, corps in tc.ou(custom_loading_screen_key=modele):
            valeurs = {"custom_loading_screen_key": neuf}
            if tc.valeurs(corps).get("component_id") == "custom_quote":
                valeurs["localised_text"] = escape(recit)
            tc.ajouter_sur_modele(k, valeurs)
    return tables, [("videos", "videos_tables", "video_name", [VIDEO_INTRO]),
                    ("custom_loading_screens", "custom_loading_screens_tables", "key", list(ECRANS_CHARGEMENT)),
                    ("custom_loading_screen_components", "custom_loading_screen_components_tables",
                     "custom_loading_screen_key", list(ECRANS_CHARGEMENT))]


TEXTES_GAMEPLAY = os.path.join(TEXTES_PROJET, "textes_gameplay.json")
# seigneurs de WH3 rendus jouables : notre écran de chargement -> (écran de CA recopié, fiche « mini » dont le récit de
# chargement devient la citation)
ECRANS_SEIGNEURS = {
    "wh_main_brt_bordeleaux_alberic_mini": ("wh_dlc07_brt_bordeleaux_alberic",
                                            "wh_dlc05_political_party_mini_bretonnia_alberic"),
    "wh_main_brt_carcassonne_fay_mini": ("wh_dlc07_brt_carcassonne_fay", "wh_dlc05_political_party_mini_bretonnia_fay"),
    "wh_dlc05_bst_morghur_herd_morghur_mini": ("wh_dlc03_bst_beastmen_morghur",
                                               "wh_dlc05_political_party_mini_beastmen_morghur"),
    # le Duc rouge (23.09.2026, 04 h 20) : écran de Mannfred (fond des Comtes vampires), notre récit
    "wh_main_vmp_mousillon_red_duke_mini": ("wh_main_vmp_vampire_counts_mannfred",
                                            "wh_dlc05_political_party_mini_vampire_counts_red_duke"),
    # Drycha, Heinrich Kemmler, Grom la Panse (spec-drycha-kemmler-grom.md, 23.09.2026, 13 h 45) : écrans de CA
    "wh2_dlc16_wef_drycha_drycha_mini": ("wh2_dlc16_wef_drycha_gc", "wh_dlc05_political_party_mini_wood_elves_drycha"),
    "wh2_dlc11_vmp_the_barrow_legion_kemmler_mini": ("wh_main_vmp_vampire_counts_heinrich",
                                                     "wh_dlc05_political_party_mini_vampire_counts_kemmler"),
    "wh2_dlc15_grn_broken_axe_grom_mini": ("wh2_dlc15_grn_grom_gc", "wh_dlc05_political_party_mini_greenskins_grom"),
    # les Sœurs du Crépuscule (24.09.2026, spec-soeurs-du-crepuscule.md) : écran de CA
    "wh2_dlc16_wef_sisters_of_twilight_sisters_mini": ("wh2_dlc16_wef_sisters_gc",
                                                       "wh_dlc05_political_party_mini_wood_elves_sisters"),
}
# vidéos de sélection des seigneurs rendus jouables qui n'ont pas de ligne videos dans WH3 (le fichier y est)
VIDEOS_SEIGNEURS = ["Front_end_selection_movies/red_duke_front_end"]


def lot_etape8():
    """Lot 8 (23.09.2026, 03 h 45) : écrans de chargement d'Alberic, de la Fée Enchanteresse et de Morghur (seigneurs de
    WH3 rendus jouables), sur ceux de CA (fond bretonnien ou des Hommes-bêtes), avec leur récit en citation (textes à
    nous : textes_gameplay.json ; Morghur : son récit de la mini-campagne de WH1). Le script de menu
    saison_ecrans_de_chargement.lua les relie à leurs personnages de départ. Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    tables = {n: TableKit(n) for n in ("custom_loading_screens", "custom_loading_screen_components", "videos")}
    for video in VIDEOS_SEIGNEURS:
        tables["videos"].ajouter_sur_modele("Front_end_selection_movies/orion_front_end", {"video_name": video})
    nos_textes = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    ts, tc = tables["custom_loading_screens"], tables["custom_loading_screen_components"]
    for neuf, (modele, fiche) in ECRANS_SEIGNEURS.items():
        ts.ajouter_sur_modele(modele, {"key": neuf})
        cle_recit = f"frontend_faction_leaders_loading_screen_text_{fiche}"
        recit = nos_textes[cle_recit]["en"] if cle_recit in nos_textes else texte_projet(cle_recit)
        for k, corps in tc.ou(custom_loading_screen_key=modele):
            valeurs = {"custom_loading_screen_key": neuf}
            if tc.valeurs(corps).get("component_id") == "custom_quote":
                valeurs["localised_text"] = escape(recit)
            tc.ajouter_sur_modele(k, valeurs)
    ecrans = list(ECRANS_CHARGEMENT) + list(ECRANS_SEIGNEURS)
    return tables, [("custom_loading_screens", "custom_loading_screens_tables", "key", ecrans),
                    ("custom_loading_screen_components", "custom_loading_screen_components_tables",
                     "custom_loading_screen_key", ecrans)]


# Nos personnages de départ (start_pos_characters, campagne wh_dlc05_wood_elves) -> leur équivalent des Empires
NOS_SEIGNEURS = {
    "2140783885": "2143928621",     # Orion
    "2140783843": "1903835792",     # Durthu
    "2140783911": "1678083818",     # Morghur
    "2140783762": "1699494966",     # Alberic
    "2140783791": "1116564133",     # la Fée Enchanteresse
    "2140784082": "1505417024",     # le Duc rouge
}
POOL_VAMPIRIQUE = "wh_main_vmp_province_pool"


def lot_etape9():
    """Lot 9 (23.09.2026, 04 h) : chantiers 4 et 9 de donnees-campagne-manquantes.md, tables du STARTPOS (à passer aussi
    dans zz_startpos_db.pack, puis régénérer : construction).
    - chantier 4 : la horde de Morghur (start_pos_horde_details : bâtiments de harde et de gors, comme aux Empires) ; les
      traits de départ de nos six seigneurs légendaires (Morghur et Alberic : les leurs ; Orion, Durthu, la Fée, le Duc
      rouge : le trait neutre de CA) ; l'Armure de fortune du Duc rouge ;
    - chantier 9 : « Relever les morts » des Comtes vampires dans nos 26 provinces (province_to_mercenary_set_junctions,
      réserve wh_main_vmp_province_pool, comme chaque province des Empires).
    Rend ({table: TableKit}, [entrées])."""
    tables = {n: TableKit(n) for n in ("start_pos_horde_details", "start_pos_character_traits",
                                       "start_pos_character_ancillaries", "province_to_mercenary_set_junctions")}

    def copie(table, cle_modele, valeurs, cle):
        t = tables[table]
        corps = dict(t.lignes)[cle_modele]
        for c, v in valeurs.items():
            corps = t.avec(corps, c, v)
        t.ajouter(cle, corps)

    th, tt, ta = (tables["start_pos_horde_details"], tables["start_pos_character_traits"],
                  tables["start_pos_character_ancillaries"])
    for nous, ie in NOS_SEIGNEURS.items():
        for k, _ in th.ou(general=ie):
            copie("start_pos_horde_details", k, {"general": nous}, nous)
        for table, t in (("start_pos_character_traits", tt), ("start_pos_character_ancillaries", ta)):
            pris = {v for k, _ in t.lignes for v in (k,)} | {t.valeurs(c).get("id", "") for _, c in t.lignes}
            deja = {t.valeurs(c).get("character_id") for _, c in t.lignes}
            if nous in deja:
                continue
            for k, corps in t.ou(character_id=ie):
                ident = ident_numerique(f"{table}:{nous}:{t.valeurs(corps).get('trait_level') or t.valeurs(corps).get('ancillary')}", pris)
                pris.add(ident)
                copie(table, k, {"id": ident, "character_id": nous}, ident)

    # 24.09.2026 (9.0) : la refonte des Comtes vampires supprime la réserve wh_main_vmp_province_pool (plus aucune
    # ligne de CA ne la cite) ; « Relever les morts » passe par des réserves par FACTION que CA donne déjà à Mousillon et
    # à la Légion des Tertres (wh3_dlc29_vmp_raise_dead_province / _faction / _additional_units), et par les cadavres
    # (scripts wh3_dlc29_vampire_corpses*). Nos 26 lignes vers l'ancienne réserve sont retirées (audit 9.0, point 1).
    tm = tables["province_to_mercenary_set_junctions"]
    for k, corps in tm.ou(mercenary_set=POOL_VAMPIRIQUE):
        if tm.valeurs(corps).get("province", "").startswith("wh_dlc05_"):
            tm.retirer(k)

    persos = list(NOS_SEIGNEURS)
    return tables, [
        ("start_pos_horde_details", "start_pos_horde_details_tables", "general", persos),
        ("start_pos_character_traits", "start_pos_character_traits_tables", "character_id", persos),
        ("start_pos_character_ancillaries", "start_pos_character_ancillaries_tables", "character_id", persos),
        ("province_to_mercenary_set_junctions", "province_to_mercenary_set_junctions_tables", "province", "wh_dlc05_"),
    ]


# Quêtes des seigneurs de WH3 rendus jouables : notre mission -> (mission des Empires recopiée, valeurs changées).
# Emplacements (coordonnées d'affichage, comme location_x / location_y de CA) : centre des régions d'après les calques de
# CAIME (Regions, TownSlots) ; cachette de la harde = point « beastmen_hide » de l'histoire de WH1 (118, 60 logique).
QUETES_SEIGNEURS = {
    "saison_qb_brt_alberic_trident_of_manann": ("wh3_main_ie_qb_brt_alberic_trident_of_bordeleaux", {
        "location_x": "30", "location_y": "199", "quest_character": "2140783762"}),           # tombeau des ducs, près de Bordeleaux (45 ; 258)
    "saison_qb_brt_alberic_braid_of_bordeleaux": ("wh3_main_ie_qb_brt_alberic_braid_of_bordeleaux", {
        "quest_character": "2140783762"}),
    "saison_qb_brt_fay_chalice_of_potions": ("wh3_main_ie_qb_brt_fay_enchantress_chalice_of_potions", {
        "location_x": "17", "location_y": "253", "quest_character": "2140783791"}),           # rivage de Martel, côte nord (25 ; 329)
    "saison_qb_bst_morghur_stave_of_ruinous_corruption": ("wh3_main_ie_qb_bst_morghur_stave_of_ruinous_corruption", {
        "location_x": "79", "location_y": "46", "quest_character": "2140783911"}),            # cachette de la harde
    # Drycha, Kemmler, Grom (23.09.2026, 15 h) : leurs quêtes de CA des Empires (wh_quests.lua), sur des cases
    # franchissables de notre carte (couches de WH1 ; affichage = logique x 0,6661 ; y x 0,7704). Kemmler : les lieux
    # du dossier de lore § 7 (Montagnes Grises, La Maisontaal ; le tombeau de Krell dans les Montagnes Grises [CA-WH3]) ;
    # le tertre de Marbad, au Middenland chez CA, passe aux Montagnes Grises (hors de notre carte sinon : texte adapté).
    "saison_qb_vmp_kemmler_skull_staff": ("wh3_main_ie_qb_vmp_heinrich_kemmler_skull_staff", {
        "location_x": "170", "location_y": "214", "quest_character": "2140784200"}),         # Grunere, (255 ; 278)
    "saison_qb_vmp_kemmler_cloak_of_mists": ("wh3_main_ie_qb_vmp_heinrich_kemmler_cloak_of_mists", {
        "location_x": "107", "location_y": "187", "quest_character": "2140784200"}),         # tertres de Cuileux, Orquemont (160 ; 243)
    "saison_qb_vmp_kemmler_chaos_tomb_blade": ("wh3_main_ie_qb_vmp_heinrich_kemmler_chaos_tomb_blade", {
        "location_x": "129", "location_y": "283", "quest_character": "2140784200"}),         # col de Gragrut, (193 ; 367)
    "saison_qb_grn_grom_axe_of_grom": ("wh3_main_ie_qb_grn_grom_axe_of_grom", {
        "location_x": "90", "location_y": "206", "quest_character": "2140783823"}),          # Massif d'Orquemont, (135 ; 268)
    "saison_qb_grn_grom_lucky_banner": ("wh3_main_ie_qb_grn_grom_lucky_banner", {
        "quest_character": "2140783823"}),                                                   # rituel de Waaagh!, sans lieu
    "saison_qb_wef_drycha_coeddil_unchained": ("wh3_main_ie_qb_wef_drycha_coeddil_unchained", {
        "location_x": "212", "location_y": "48", "quest_character": "2140783871"}),          # Cythral = le Wildwood, (318 ; 62)
    # les Sœurs du Crépuscule (24.09.2026) : « La recherche de Ceithin-Har » de CA (bataille du creux et des pierres des
    # Hardes inchangée), à la cachette de la harde de Morghur (point beastmen_hide de WH1, (118 ; 60)) ; texte de CA
    # adapté (textes_gameplay.json : sans les Elfes noirs, absents de notre carte)
    "saison_qb_wef_sisters_ceithin_har": ("wh3_main_ie_qb_wef_sisters_dragon", {
        "location_x": "79", "location_y": "46", "quest_character": "2140784201"}),
    # Gotrek et Félix (saison_felix.lua) : la bataille de CA, dans la trouée de Gisoreux (Berghres, (158 ; 380)), par où
    # le duo entre en Bretonnie dans « Blood Sport »
    "saison_qb_gotrek_felix_alberic": ("wh3_dlc25_qb_gotrek_felix_ie_alberic", {
        "location_x": "105", "location_y": "293", "quest_character": "2140783762"}),
    "saison_qb_gotrek_felix_fay": ("wh3_dlc25_qb_gotrek_felix_ie_fay_enchantress", {
        "location_x": "105", "location_y": "293", "quest_character": "2140783791"}),
    # « La Chute de l'Homme », bataille finale de la Ruine (Morghur joué, palier 7) : CA la pose en (321, 460), hors de
    # notre carte (audit des scripts de CA, M1). Ici devant Montfort, qui garde le Défilé de la Hache vers l'Empire,
    # là où l'Empire et la Bretonnie peuvent rassembler leur ost (case (162 ; 308), franchissable)
    "saison_qb_bst_chute_de_l_homme": ("wh_dlc03_qb_bst_the_final_battle", {
        "location_x": "108", "location_y": "237"}),
    # Revanche de Dent-Noire (25.09.2026 ; audit de cohérence, point 7) : missions 3 et 4 de CA (scriptées, lancées par
    # saison_grom.lua) sous nos clés, leur texte sans la promesse de Tor Yvresse (textes_gameplay.json)
    "saison_grn_grom_black_toof_3": ("wh2_dlc15_grn_grom_black_toof_3", {}),
    "saison_grn_grom_black_toof_4": ("wh2_dlc15_grn_grom_black_toof_4", {}),
}
# options du directeur de campagne à changer : (mission, option) -> valeur. GEN_CND_CHARACTER_ID suit toujours
# quest_character (lot_etape10) : jusqu'au 23.09.2026, 15 h, le Trident et le Calice gardaient l'identifiant des Empires.
OPTIONS_QUETES = {
    ("saison_qb_brt_alberic_braid_of_bordeleaux", "GEN_CND_REGION"): "wh_dlc05_mousillon_mousillon",
}


def lot_etape10():
    """Lot 10 (23.09.2026, 04 h 10) : les quêtes de CA d'Alberic, de la Fée Enchanteresse et de Morghur (Empires :
    wh_quests.lua), recopiées sous nos clés pour notre carte : le Trident de Manann, la Tresse de Bordeleaux (Mousillon
    au lieu de Sartosa), le Calice des Potions, la Portée de corruption de la Ruine. Batailles de quête de CA inchangées ;
    personnage de quête = le nôtre ; emplacements sur notre carte. Le Miroir de Morgiana (un monument de Carcassonne
    à construire) reste un objet donné au rang. Rend ({table: TableKit}, [entrées : à ajouter à MISSIONS_HISTOIRE])."""
    tables = {n: TableKit(n) for n in ("missions", "cdir_events_mission_option_junctions",
                                       "cdir_events_mission_payloads", "cdir_events_mission_issuer_junctions")}

    def copie(table, cle_modele, valeurs, cle):
        t = tables[table]
        corps = dict(t.lignes)[cle_modele]
        for c, v in valeurs.items():
            corps = t.avec(corps, c, v)
        t.ajouter(cle, corps)

    def option(nous, valeurs, cle_option):
        if (nous, cle_option) in OPTIONS_QUETES:
            return OPTIONS_QUETES[(nous, cle_option)]
        if cle_option == "GEN_CND_CHARACTER_ID" and valeurs.get("quest_character"):
            return valeurs["quest_character"]
        return None

    def ajouter_jonctions(nous, ca, valeurs):
        """Options, récompenses et émetteur de la mission de CA `ca`, recopiés pour la nôtre."""
        for table in ("cdir_events_mission_option_junctions", "cdir_events_mission_payloads"):
            t = tables[table]
            pris = {t.valeurs(c).get("id", "") for _, c in t.lignes} | set(t.cles)
            for k, corps in t.ou(mission_key=ca):
                v = t.valeurs(corps)
                ident = ident_numerique(f"{table}:{nous}:{v.get('option_key') or v.get('payload_key')}:{v.get('value')}",
                                        pris)
                pris.add(ident)
                nouvelles = {"id": ident, "mission_key": nous}
                if table == "cdir_events_mission_option_junctions" and option(nous, valeurs, v.get("option_key")) is not None:
                    nouvelles["value"] = option(nous, valeurs, v["option_key"])
                copie(table, k, nouvelles, ident)
        ti = tables["cdir_events_mission_issuer_junctions"]
        for k, corps in ti.ou(mission_key=ca):
            copie("cdir_events_mission_issuer_junctions", k, {"mission_key": nous}, k.replace(ca, nous, 1))

    for nous, (ca, valeurs) in QUETES_SEIGNEURS.items():
        # quête déjà écrite (lot rejoué) : ses valeurs et options corrigées en place, rien n'est recopié deux fois
        if nous in tables["missions"].cles:
            # textes anglais corrigés dans textes_gameplay.json (refonte « loreful ») : aussi dans le kit
            from xml.sax.saxutils import escape
            nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
            maj = dict(valeurs)
            for col in ("title", "description"):
                texte = (nos.get(f"missions_localised_{col}_{nous}") or {}).get("en")
                if texte:
                    maj[f"localised_{col}"] = escape(texte)
            tables["missions"].modifier(nous, maj)
            t = tables["cdir_events_mission_option_junctions"]
            for k, corps in t.ou(mission_key=nous):
                v = t.valeurs(corps)
                nouvelle = option(nous, valeurs, v.get("option_key"))
                if nouvelle is not None:
                    t.modifier(k, {"value": nouvelle})
            # 24.09.2026 (restauration 9.0) : la mission a pu revenir sans ses jonctions (sauvegardes de tables prises à
            # des heures différentes : la quête des Sœurs avait perdu émetteur, options et récompenses) ; on les refait
            if not tables["cdir_events_mission_option_junctions"].ou(mission_key=nous):
                ajouter_jonctions(nous, ca, valeurs)
            elif not tables["cdir_events_mission_issuer_junctions"].ou(mission_key=nous):
                ti = tables["cdir_events_mission_issuer_junctions"]
                for k, corps in ti.ou(mission_key=ca):
                    copie("cdir_events_mission_issuer_junctions", k, {"mission_key": nous}, k.replace(ca, nous, 1))
            # 25.09.2026 (audit des seigneurs, V1) : les récompenses suivent celles de CA. En 9.0, les trois quêtes de
            # Kemmler donnent 200 de Puissance au lieu des « baisers de sang » de la 8.1 ; nos copies gardaient l'ancienne
            # récompense. Si les récompenses de CA ont changé, les nôtres sont refaites à l'identique des siennes.
            tp = tables["cdir_events_mission_payloads"]

            def recompenses(cle):
                return sorted((tp.valeurs(c).get("payload_key", ""), tp.valeurs(c).get("value", ""))
                              for _, c in tp.ou(mission_key=cle))
            if recompenses(ca) and recompenses(ca) != recompenses(nous):
                for k, _ in list(tp.ou(mission_key=nous)):
                    tp.retirer(k)
                pris = {tp.valeurs(c).get("id", "") for _, c in tp.lignes} | set(tp.cles)
                for k, corps in tp.ou(mission_key=ca):
                    v = tp.valeurs(corps)
                    ident = ident_numerique(f"cdir_events_mission_payloads:{nous}:{v.get('payload_key')}:"
                                            f"{v.get('value')}", pris)
                    pris.add(ident)
                    copie("cdir_events_mission_payloads", k, {"id": ident, "mission_key": nous}, ident)
            continue
        # textes à nous dès la création (sinon ceux de CA, puis les nôtres au passage suivant seulement)
        from xml.sax.saxutils import escape
        nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
        neuves = dict(valeurs, key=nous)
        for col in ("title", "description"):
            texte = (nos.get(f"missions_localised_{col}_{nous}") or {}).get("en")
            if texte:
                neuves[f"localised_{col}"] = escape(texte)
        copie("missions", ca, neuves, nous)
        ajouter_jonctions(nous, ca, valeurs)
    return tables, []


POTENTIEL_MINEUR_IE = "combi_minor"
# Factions majeures : chez CA, toute faction jouable l'est (Empires 104 sur 104, Chaos 25 sur 25, prologue). Alberic et la
# Fée (majeures aux Empires) et le Duc rouge deviennent jouables ; Morghur l'est déjà. Pas les Hommes-bêtes de Khazrak,
# majeurs aux Empires mais sans personnage ni région chez nous.
FACTIONS_MAJEURES = ["wh_main_brt_bordeleaux", "wh_main_brt_carcassonne", "wh_main_vmp_mousillon"]


def lot_etape11():
    """Lot 11 (23.09.2026, 04 h 30) : le potentiel de nos factions (start_pos_factions.faction_potential) comme aux
    Empires Immortels, et le rang de faction majeure (is_major) des seigneurs rendus jouables. Table du STARTPOS : à
    passer aussi dans zz_startpos_db.pack (construction), puis régénérer.
    Nos 39 factions portaient toutes « minor » (valeur par défaut de declare_campaign.DEFAULTS) : -25 + tirage de 0 à
    100. Le potentiel règle ce que l'IA reçoit (faction_potential_handicap_effects, de 0 à 400 : expérience, coût de
    construction et de recrutement, réapprovisionnement, entretien, croissance ; en dessous de 0, +30 % d'entretien).
    Aux Empires : 175 (+0 à 60) pour Orion, Durthu, Alberic, la Fée, Morghur ; combi_minor (20 + 0 à 40) ou
    combi_minor_survivor (Mousillon, les Teef Snatchaz) pour les autres. Donc : la valeur des Empires pour la même
    faction, combi_minor pour nos factions absentes des Empires (clairières, duchés, harde, Waaagh!). Les autres colonnes
    de l'IA (groupe de personnalité, directeur militaire) sont déjà celles des Empires ; le trésor reste celui de WH1."""
    t = TableKit("start_pos_factions")
    ie = {}
    for _, corps in t.lignes:
        v = t.valeurs(corps)
        if v.get("campaign") == IE:
            ie[v.get("faction")] = v
    for k, corps in t.lignes:
        v = t.valeurs(corps)
        if v.get("campaign") != CAMPAGNE:
            continue
        ref = ie.get(v.get("faction"))
        nouvelles = {"faction_potential": ref.get("faction_potential") if ref else POTENTIEL_MINEUR_IE}
        if (json.load(open(ARMEES_DEPART, encoding="utf-8"))["factions"].get(v.get("faction"), {})
                .get("faction_potential")):
            # l'équilibrage du lot 17 (armees-depart.json) prime sur la valeur des Empires : pas de va-et-vient
            nouvelles.pop("faction_potential")
        if not ref and v.get("faction_potential") not in ("", "minor"):
            # 24.09.2026 (9.0) : faction retirée du startpos des Empires (les Skullsmasherz, la harde brayherd) : on garde
            # la valeur des Empires déjà recopiée avant la mise à jour
            nouvelles = {}
        if v.get("faction") in FACTIONS_MAJEURES:
            nouvelles["is_major"] = "1"
        if t.modifier(k, nouvelles):
            print(f"  {v.get('faction'):40s} " + " ; ".join(f"{c} {v.get(c)} -> {x}" for c, x in t.modifiees[k].items()))
    return {"start_pos_factions": t}, []


# Chroniques de la Saison (23.09.2026, demande de Charles) : les quêtes propres aux seigneurs de WH3 rendus jouables,
# posées par script (saison_chroniques.lua, sur le modèle de wh3_dlc27_dechala_narrative.lua de CA). Chaque mission a sa
# ligne du tableau missions (titre, description, image) ; ses objectifs et récompenses viennent du script.
# clé -> (type d'objectif principal, image de l'évènement). Textes : textes_gameplay.json
# (missions_localised_title_<clé>, missions_localised_description_<clé>).
MODELE_MISSION_CHRONIQUE = "wh3_dlc27_mission_sla_narrative_05"
# Chroniques de la Saison (saison_chroniques.lua, 23.09.2026) : mission -> (type d'objectif principal, image de CA)
_BRT, _BST, _VMP, _WEF, _GRN = "brt/generic", "bst/generic", "vmp/generic", "wef/generic", "grn/generic"
_DEF, _SCR, _ELI = "DEFEAT_N_ARMIES_OF_FACTION", "SCRIPTED", "ELIMINATE_CHARACTER_IN_BATTLE"
_RAZ, _CTL, _CON = "RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", "CONTROL_N_REGIONS_INCLUDING", \
    "CONSTRUCT_N_BUILDINGS_INCLUDING"
_ENG = "ENGAGE_FORCE"       # armées posées des finales, des Échos et de Félix (objectif de CA, wh_grudges.lua)
CHRONIQUES = {
    "saison_chronique_alberic_1": (_DEF, _BRT), "saison_chronique_alberic_2": (_DEF, _BRT),
    "saison_chronique_alberic_3": (_SCR, _BRT), "saison_chronique_alberic_4": (_ELI, _BRT),
    "saison_chronique_fee_1": (_DEF, _BRT), "saison_chronique_fee_2": (_SCR, _BRT),
    "saison_chronique_fee_3": (_SCR, _BRT), "saison_chronique_fee_4": (_ELI, _BRT),
    "saison_chronique_morghur_1": (_RAZ, _BST), "saison_chronique_morghur_2": (_DEF, _BST),
    "saison_chronique_morghur_3": (_RAZ, _BST), "saison_chronique_morghur_4": (_RAZ, _BST),
    "saison_chronique_duc_1": (_CTL, _VMP), "saison_chronique_duc_2": (_DEF, _VMP),
    "saison_chronique_duc_3": (_CTL, _VMP), "saison_chronique_duc_4": (_CON, _VMP),
    "saison_chronique_drycha_1": (_DEF, _WEF), "saison_chronique_drycha_2": (_RAZ, _WEF),
    "saison_chronique_drycha_3": (_CTL, _WEF),
    "saison_chronique_kemmler_1": (_DEF, _VMP), "saison_chronique_kemmler_2": (_CTL, _VMP),
    "saison_chronique_kemmler_3": (_CTL, _VMP),
    "saison_chronique_grom_1": (_DEF, _GRN), "saison_chronique_grom_2": (_RAZ, _GRN),
    "saison_chronique_grom_3": (_DEF, _GRN),
    # batailles finales (23.09.2026, 15 h 30) : vaincre le général d'une armée posée à un lieu du lore
    "saison_chronique_alberic_5": (_ENG, _BRT), "saison_chronique_fee_5": (_ENG, _BRT),
    "saison_chronique_morghur_5": (_ENG, _BST), "saison_chronique_duc_5": (_ENG, _VMP),
    "saison_chronique_drycha_4": (_ENG, _WEF), "saison_chronique_kemmler_4": (_ENG, _VMP),
    "saison_chronique_grom_4": (_ENG, _GRN),
    # refonte « loreful » (23.09.2026, 17 h) : étapes neuves
    "saison_chronique_drycha_parravon": (_RAZ, _WEF), "saison_chronique_kemmler_cairns": (_DEF, _VMP),
    "saison_chronique_grom_gragabad": (_RAZ, _GRN),
    # Échos de la Saison (menaces récurrentes après la chronique, même mission réémise)
    "saison_echo_alberic": (_ENG, _BRT), "saison_echo_fee": (_ENG, _BRT), "saison_echo_morghur": (_ENG, _BST),
    "saison_echo_duc": (_ENG, _VMP), "saison_echo_drycha": (_ENG, _WEF), "saison_echo_kemmler": (_ENG, _VMP),
    "saison_echo_grom": (_ENG, _GRN), "saison_echo_orion": (_ENG, _WEF), "saison_echo_durthu": (_ENG, _WEF),
    # les Sœurs du Crépuscule (24.09.2026, saison_chroniques.lua) : chronique, finale, écho
    "saison_chronique_soeurs_1": (_CTL, _WEF), "saison_chronique_soeurs_2": (_SCR, _WEF),
    "saison_chronique_soeurs_3": (_DEF, _WEF), "saison_chronique_soeurs_4": (_ELI, _WEF),
    "saison_chronique_soeurs_5": (_ENG, _WEF), "saison_echo_soeurs": (_ENG, _WEF),
    "saison_chronique_soeurs_enclume": (_CTL, _WEF),
    # Chroniques de Félix (saison_felix.lua)
    "saison_felix_arene": (_SCR, "all/gotrek_felix"), "saison_felix_chapelle": (_ENG, "all/gotrek_felix"),
    "saison_felix_reikguard": (_ELI, "all/gotrek_felix"),
    # le défi du Duc écarlate (mécanique E, 25.09.2026 ; saison_duc.lua, section 7)
    "saison_duc_defi": (_ELI, _VMP),
}
# objectifs scriptés des chroniques (override_text mission_text_text_<clé>) : lignes du tableau mission_text
MODELE_TEXTE_MISSION = "mis_activity_complete_grail_vow_alberic"
TEXTES_OBJECTIFS_CHRONIQUES = ["saison_alberic_pacte_asrai", "saison_fee_quenelles", "saison_fee_ducs", "saison_drycha_addaivoch",
                               "saison_morghur_val_malheur", "saison_felix_arene", "saison_soeurs_porte_du_roi",
                               "saison_duc_defi_en_personne"]
# noms de faction propres à notre campagne (cm:change_localised_faction_name) : Bordeleaux s'affiche « Errants de
# Bordeleaux », son nom des Empires (Alberic en Lustrie) ; chez nous le duché porte le nom de sa capitale, comme les autres
CHAINES_CAMPAGNE = {"saison_nom_bordeleaux": "Bordeleaux",
                    # factions de bataille des boss des Chroniques et des Échos (saison_chroniques.lua, NOMS_QB)
                    "saison_nom_qb_harde": "Beast Warherd",
                    "saison_nom_qb_morts": "The Restless Dead",
                    "saison_nom_qb_peaux_vertes": "Greenskin Warband",
                    "saison_nom_qb_ost": "Bretonnian Host",
                    "saison_nom_qb_esprits": "Wrathful Spirits of Athel Loren",
                    "saison_nom_qb_chasse": "The Wild Hunt",
                    "saison_nom_qb_nains": "Throng of Karak Ziflin",
                    # Gisoreux : CA écrit « Giseroux » en anglais (audit des textes, 23.09.2026)
                    "saison_nom_gisoreux": "Gisoreux"}
# chaînes retirées (23.09.2026) : les noms de CA de ces duchés sont ceux de GW, en anglais comme en français
CHAINES_RETIREES = ["saison_nom_carcassonne", "saison_nom_aquitaine", "saison_nom_bastonne"]


# Illustrations de Charles (24.09.2026 ; session « Écrire les prompts d'illustration de la Saison », contrôle de style et
# de lore) : mission -> image ui/eventpics/saison/<clé>.png du pack (colonne ui_image = « saison/<clé> »). Originaux dans
# 04-projets\saison-des-revelations\illustrations\, images du jeu (380 × 214, taille des images d'évènement de CA) dans
# 04-projets\saison-des-revelations\images-evenements\ui\eventpics\saison\ (illustrations_vers_jeu.py).
ILLUSTRATIONS = {
    "saison_chronique_duc_1": "saison/saison_chronique_duc_1",
    "saison_chronique_alberic_3": "saison/saison_chronique_alberic_3",
    "saison_chronique_fee_5": "saison/saison_chronique_fee_5",
    "saison_chronique_morghur_4": "saison/saison_chronique_morghur_4",
    "saison_chronique_drycha_1": "saison/saison_chronique_drycha_1",
    "saison_chronique_kemmler_cairns": "saison/saison_chronique_kemmler_cairns",
    "saison_chronique_grom_1": "saison/saison_chronique_grom_1",
    "saison_chronique_soeurs_4": "saison/saison_chronique_soeurs_4",
    "saison_chronique_duc_4": "saison/saison_chronique_duc_4",
    "saison_chronique_alberic_1": "saison/saison_chronique_alberic_1",
    "saison_chronique_fee_2": "saison/saison_chronique_fee_2",
    "saison_chronique_morghur_1": "saison/saison_chronique_morghur_1",
    "saison_chronique_drycha_4": "saison/saison_chronique_drycha_4",
    "saison_chronique_kemmler_4": "saison/saison_chronique_kemmler_4",
    "saison_chronique_grom_gragabad": "saison/saison_chronique_grom_gragabad",
    "saison_chronique_soeurs_enclume": "saison/saison_chronique_soeurs_enclume",
    "saison_echo_orion": "saison/saison_echo_orion",
    "saison_echo_durthu": "saison/saison_echo_durthu",
    "saison_echo_alberic": "saison/saison_echo_alberic",  # lot 4, 25.09.2026
    "saison_echo_fee": "saison/saison_echo_fee",
    "saison_echo_morghur": "saison/saison_echo_morghur",
    "saison_duc_galand": "saison/saison_duc_galand",  # incident du lot 32
    "saison_chronique_duc_2": "saison/saison_chronique_duc_2",
    "saison_chronique_alberic_5": "saison/saison_chronique_alberic_5",
    "saison_chronique_fee_1": "saison/saison_chronique_fee_1",
    "saison_chronique_morghur_3": "saison/saison_chronique_morghur_3",
    "saison_chronique_drycha_parravon": "saison/saison_chronique_drycha_parravon",
    "saison_chronique_kemmler_2": "saison/saison_chronique_kemmler_2",
    "saison_felix_arene": "saison/saison_felix_arene",
    "saison_felix_chapelle": "saison/saison_felix_chapelle",
    "saison_felix_reikguard": "saison/saison_felix_reikguard",
    "saison_chronique_grom_4": "saison/saison_chronique_grom_4",
    "saison_chronique_soeurs_2": "saison/saison_chronique_soeurs_2",
    # lot 4 d'illustrations (25.09.2026)
    "saison_chronique_alberic_2": "saison/saison_chronique_alberic_2",
    "saison_chronique_alberic_4": "saison/saison_chronique_alberic_4",
    "saison_chronique_fee_3": "saison/saison_chronique_fee_3",
    "saison_chronique_fee_4": "saison/saison_chronique_fee_4",
    "saison_chronique_morghur_2": "saison/saison_chronique_morghur_2",
    "saison_chronique_morghur_5": "saison/saison_chronique_morghur_5",
    "saison_chronique_duc_3": "saison/saison_chronique_duc_3",
    "saison_chronique_duc_5": "saison/saison_chronique_duc_5",  # v2 (la v1 a été retirée par Charles)
    "saison_chronique_drycha_2": "saison/saison_chronique_drycha_2",
    "saison_chronique_drycha_3": "saison/saison_chronique_drycha_3",
    "saison_chronique_kemmler_1": "saison/saison_chronique_kemmler_1",
    "saison_chronique_kemmler_3": "saison/saison_chronique_kemmler_3",
    "saison_chronique_grom_2": "saison/saison_chronique_grom_2",
    "saison_chronique_grom_3": "saison/saison_chronique_grom_3",
    "saison_chronique_soeurs_1": "saison/saison_chronique_soeurs_1",
    "saison_chronique_soeurs_3": "saison/saison_chronique_soeurs_3",
    "saison_chronique_soeurs_5": "saison/saison_chronique_soeurs_5",
}


def lot_etape12():
    """Lot 12 : les missions des Chroniques de la Saison (tableau missions), sur une mission narrative de CA
    (MODELE_MISSION_CHRONIQUE : évènement militaire, épinglée, non annulable), et les textes de leurs objectifs
    scriptés (tableau mission_text, sur une ligne de CA). Titres, descriptions et textes anglais repris de
    textes_gameplay.json (le français aussi y est). Entrées build_pack : clés des missions dans MISSIONS_HISTOIRE,
    textes dans l'entrée mission_text (tables_gameplay.py), une seule entrée par table du jeu."""
    from xml.sax.saxutils import escape
    t = TableKit("missions")
    tt = TableKit("mission_text")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    for cle, (type_objectif, image) in CHRONIQUES.items():
        image = ILLUSTRATIONS.get(cle, image)
        titre = (nos.get(f"missions_localised_title_{cle}") or {}).get("en")
        desc = (nos.get(f"missions_localised_description_{cle}") or {}).get("en")
        if not titre or not desc:
            raise SystemExit(f"lot 12 : textes de {cle} absents de textes_gameplay.json")
        if cle in t.cles:
            # mission déjà écrite : textes (refonte) et image (illustrations de Charles) mis à jour
            t.modifier(cle, {"mission_type": type_objectif, "localised_title": escape(titre),
                             "localised_description": escape(desc), "ui_image": image})
            continue
        t.ajouter_sur_modele(MODELE_MISSION_CHRONIQUE, {"key": cle, "mission_type": type_objectif, "ui_image": image,
                                                        "localised_title": escape(titre),
                                                        "localised_description": escape(desc)})
    for cle in TEXTES_OBJECTIFS_CHRONIQUES:
        texte = (nos.get(f"mission_text_text_{cle}") or {}).get("en")
        if not texte:
            raise SystemExit(f"lot 12 : texte de l'objectif {cle} absent de textes_gameplay.json")
        if cle in tt.cles:
            tt.modifier(cle, {"text": escape(texte)})
            continue
        tt.ajouter_sur_modele(MODELE_TEXTE_MISSION, {"key": cle, "text": escape(texte)})
    tc = TableKit("campaign_localised_strings")
    for cle in CHAINES_RETIREES:
        if cle in tc.cles:
            tc.retirer(cle)
    for cle, texte in CHAINES_CAMPAGNE.items():
        if cle in tc.cles:
            tc.modifier(cle, {"string": escape(texte)})
            continue
        tc.ajouter_sur_modele("MPC_cannot_construct_not_your_turn", {"key": cle, "string": escape(texte)})
    return {"missions": t, "mission_text": tt, "campaign_localised_strings": tc}, [
        ("missions", "missions_tables", "key", list(CHRONIQUES)),
        ("mission_text", "mission_text_tables", "key", TEXTES_OBJECTIFS_CHRONIQUES),
        ("campaign_localised_strings", "campaign_localised_strings_tables", "key", list(CHAINES_CAMPAGNE))]


RESSOURCE_CA, RESSOURCE = "wef_worldroots_athel_loren", "wef_worldroots_saison_athel_loren"
RITUEL_CA, RITUEL = "wh2_dlc16_ritual_rebirth_athel_loren", "wh2_dlc16_ritual_rebirth_saison_athel_loren"
GROUPE_FORET = "saison_feature_wood_elves"
PALIER_CA = "wh2_dlc16_pooled_resource_world_roots_health_athel_loren_{}"
PALIER = "wh2_dlc16_pooled_resource_world_roots_health_saison_athel_loren_{}"
CHENE = "wh_dlc05_oak_of_ages"


def lot_etape7():
    """Lot 7 (23.09.2026, 03 h 40) : Athel Loren a SES clés de Racines du monde.
    Plantage de 02 h 53 : notre Chêne partageait avec celui des Empires la ressource wef_worldroots_athel_loren et le
    rituel de Renaissance ; l'infobulle du bosquet prenait la région des Empires, absente de notre carte. Remplacer les
    tables de CA (REMPLACE_CA) cassait les bosquets des Empires, mod actif ; Charles veut que toutes les campagnes
    coexistent. Donc, sur le modèle des lignes de CA :
    - ressource wef_worldroots_saison_athel_loren (11 facteurs, effet « revenu désactivé ») et rituel
      wh2_dlc16_ritual_rebirth_saison_athel_loren (coût de 500 santé de NOTRE ressource, charges de CA réutilisées) ;
    - un groupe de campagne saison_feature_wood_elves (culture Elfes sylvains ET notre campagne) qui les donne : aux
      Empires, personne ne les a ;
    - les 5 paliers de santé (groupes, critères de ressource et de valeur), avec les ensembles d'effets de CA ;
    - nos deux jonctions vers le Chêne sous ces clés ; les anciennes (clés de CA -> notre Chêne) sont retirées.
    Rend ({table: TableKit}, [entrées TABLES])."""
    noms = ["pooled_resources", "pooled_resource_factor_junctions", "effect_bonus_value_pooled_resource_junctions",
            "campaign_groups", "campaign_group_members", "campaign_group_member_criteria_cultures",
            "campaign_group_member_criteria_campaigns", "campaign_group_pooled_resources", "campaign_group_rituals",
            "campaign_group_member_criteria_pooled_resources", "campaign_group_member_criteria_numeric_ranges",
            "campaign_group_pooled_resource_effects", "rituals", "resource_costs",
            "resource_cost_pooled_resource_junctions", "pooled_resource_to_region_junctions", "rituals_to_regions"]
    T = {n: TableKit(n) for n in noms}

    def copie(table, cle_modele, valeurs, cle):
        """Ligne neuve de clé `cle` sur le corps de `cle_modele`, colonnes remplacées."""
        t = T[table]
        corps = dict(t.lignes)[cle_modele]
        for c, v in valeurs.items():
            corps = t.avec(corps, c, v)
        t.ajouter(cle, corps)

    # la ressource et ses facteurs
    copie("pooled_resources", RESSOURCE_CA, {"key": RESSOURCE}, RESSOURCE)
    for k, corps in T["pooled_resource_factor_junctions"].ou(resource=RESSOURCE_CA):
        uid = T["pooled_resource_factor_junctions"].valeurs(corps)["unique_id"].replace(RESSOURCE_CA, RESSOURCE, 1)
        copie("pooled_resource_factor_junctions", k, {"resource": RESSOURCE, "unique_id": uid}, uid)
    for k, corps in T["effect_bonus_value_pooled_resource_junctions"].ou(pooled_resource=RESSOURCE_CA):
        v = T["effect_bonus_value_pooled_resource_junctions"].valeurs(corps)
        copie("effect_bonus_value_pooled_resource_junctions", k, {"pooled_resource": RESSOURCE},
              v["effect"] + v["bonus_value_id"] + RESSOURCE)

    # le groupe des Elfes sylvains de NOTRE campagne
    copie("campaign_groups", "wh_dlc05_feature_wood_elves", {"id": GROUPE_FORET}, GROUPE_FORET)
    copie("campaign_group_members", "wh_feature_wood_elves", {"id": GROUPE_FORET, "group": GROUPE_FORET}, GROUPE_FORET)
    k = T["campaign_group_member_criteria_cultures"].modele(member="wh_feature_wood_elves")
    copie("campaign_group_member_criteria_cultures", k, {"member": GROUPE_FORET}, k.replace("wh_feature_wood_elves",
                                                                                           GROUPE_FORET, 1))
    k = T["campaign_group_member_criteria_campaigns"].modele(campaign=CAMPAGNE)
    copie("campaign_group_member_criteria_campaigns", k, {"member": GROUPE_FORET}, GROUPE_FORET + CAMPAGNE)
    k = T["campaign_group_pooled_resources"].modele(campaign_group="wh_dlc05_feature_wood_elves", resource=RESSOURCE_CA)
    copie("campaign_group_pooled_resources", k, {"campaign_group": GROUPE_FORET, "resource": RESSOURCE},
          GROUPE_FORET + RESSOURCE)
    k = T["campaign_group_rituals"].modele(campaign_group="wh_dlc05_feature_wood_elves", ritual=RITUEL_CA)
    copie("campaign_group_rituals", k, {"campaign_group": GROUPE_FORET, "ritual": RITUEL}, GROUPE_FORET + RITUEL)

    # les 5 paliers de santé
    for i in range(5):
        ca, nous = PALIER_CA.format(i), PALIER.format(i)
        copie("campaign_groups", ca, {"id": nous}, nous)
        copie("campaign_group_members", ca, {"id": nous, "group": nous}, nous)
        copie("campaign_group_member_criteria_pooled_resources", ca, {"member": nous, "pooled_resource": RESSOURCE},
              nous)
        copie("campaign_group_member_criteria_numeric_ranges", ca + "VALUE", {"member": nous}, nous + "VALUE")
        copie("campaign_group_pooled_resource_effects", ca, {"campaign_group": nous}, nous)

    # le rituel de Renaissance et son coût
    copie("rituals", RITUEL_CA, {"key": RITUEL, "required_resources": RITUEL}, RITUEL)
    copie("resource_costs", RITUEL_CA, {"id": RITUEL}, RITUEL)
    k = T["resource_cost_pooled_resource_junctions"].modele(resource_cost=RITUEL_CA)
    facteur = RESSOURCE + "_rituals"
    copie("resource_cost_pooled_resource_junctions", k, {"resource_cost": RITUEL, "pooled_resource_factor": facteur},
          RITUEL + facteur)

    # nos jonctions vers le Chêne : sous nos clés seulement
    for table, col_cle, ca, nous in (("pooled_resource_to_region_junctions", "pooled_resource", RESSOURCE_CA, RESSOURCE),
                                     ("rituals_to_regions", "ritual", RITUEL_CA, RITUEL)):
        t = T[table]
        for k, corps in t.ou(**{col_cle: ca, "region": CHENE}):
            t.retirer(k)
            copie(table, k, {col_cle: nous}, k.replace(ca, nous, 1))

    paliers = [PALIER.format(i) for i in range(5)]
    return T, [
        ("pooled_resources", "pooled_resources_tables", "key", [RESSOURCE]),
        ("pooled_resource_factor_junctions", "pooled_resource_factor_junctions_tables", "resource", [RESSOURCE]),
        ("effect_bonus_value_pooled_resource_junctions", "effect_bonus_value_pooled_resource_junctions_tables",
         "pooled_resource", [RESSOURCE]),
        ("campaign_groups", "campaign_groups_tables", "id", [GROUPE_FORET] + paliers),
        ("campaign_group_members", "campaign_group_members_tables", "id", [GROUPE_FORET] + paliers),  # lot 1 à allonger
        ("campaign_group_member_criteria_cultures", "campaign_group_member_criteria_cultures_tables", "member",
         [GROUPE_FORET]),
        ("campaign_group_pooled_resources", "campaign_group_pooled_resources_tables", "campaign_group",
         [GROUPE_FORET]),
        ("campaign_group_rituals", "campaign_group_rituals_tables", "campaign_group", [GROUPE_FORET]),
        ("campaign_group_member_criteria_pooled_resources", "campaign_group_member_criteria_pooled_resources_tables",
         "member", paliers),
        ("campaign_group_member_criteria_numeric_ranges", "campaign_group_member_criteria_numeric_ranges_tables",
         "member", paliers),
        ("campaign_group_pooled_resource_effects", "campaign_group_pooled_resource_effects_tables", "campaign_group",
         paliers),
        ("rituals", "rituals_tables", "key", [RITUEL]),
        ("resource_costs", "resource_costs_tables", "id", [RITUEL]),
        ("resource_cost_pooled_resource_junctions", "resource_cost_pooled_resource_junctions_tables", "resource_cost",
         [RITUEL]),
    ]


def references(table):
    """{colonne: (table source, colonne source)} : les colonnes de `table` qui en référencent une autre, d'après la
    définition du kit (TWaD_<table>.xml ; la première colonne source est la clé, les suivantes l'affichage)."""
    chemin = os.path.join(KIT_DB, "TWaD_" + table + ".xml")
    if not os.path.exists(chemin):
        return {}
    out = {}
    for f in re.findall(r"<field>(.*?)</field>", open(chemin, encoding="utf-8").read(), re.S):
        nom = re.search(r"<name>([^<]*)</name>", f)
        st = re.search(r"<column_source_table>([^<]*)</column_source_table>", f)
        sc = re.search(r"<column_source_column>([^<]*)</column_source_column>", f)
        if nom and st and sc:
            out[nom.group(1)] = (st.group(1), sc.group(1))
    return out


def verifier_references(tables):
    """Chaque valeur non vide des lignes neuves qui référence une autre table doit y exister (kit ou lignes neuves du
    même lot). Rend la liste des manques (table, colonne, valeur, table source)."""
    cache = {}

    def connues(table, colonne):
        if (table, colonne) not in cache:
            chemin = os.path.join(KIT_DB, table + ".xml")
            if not os.path.exists(chemin):
                cache[(table, colonne)] = None
                return None
            # lecture souple (attributs de ligne dans n'importe quel ordre), plus les lignes neuves du lot
            texte = open(chemin, encoding="utf-8").read()
            vals = {TableKit.valeurs(m.group(1)).get(colonne, "")
                    for m in re.finditer(rf"<{table}(?: [^>]*)?>(.*?)</{table}>", texte, re.S)}
            if table in tables:
                vals |= {TableKit.valeurs(n.split(">", 1)[1]).get(colonne, "") for n in tables[table].neuves}
            cache[(table, colonne)] = vals
        return cache[(table, colonne)]

    manques = []
    for nom, t in tables.items():
        refs = references(nom)
        # lignes neuves, et valeurs changées des lignes modifiées
        a_verifier = [t.valeurs(n.split(">", 1)[1]) for n in t.neuves] + list(t.modifiees.values())
        for v in a_verifier:
            for col, (st, sc) in refs.items():
                val = v.get(col, "")
                if not val:
                    continue
                vals = connues(st, sc)
                if vals is not None and val not in vals:
                    manques.append((nom, col, val, f"{st}.{sc}"))
    return manques


def cles_region_groups():
    """Toutes nos clés de `region_groups` (lots 1 et 2) : une seule entrée TABLES par table du jeu, sinon build_pack
    écrirait deux fois `db/region_groups_tables/<pack>` et la seconde effacerait la première. Lot 23 : le groupe de forêt
    à nous y est (oublié au pack de 20 h 24 : jonctions sans leur groupe, pack refusé à la génération du startpos)."""
    return sorted(set(nos_regions().values()) | set(GROUPES_NAINS) | {GROUPE_FORET_ATHEL_LOREN})


# Audit des mécaniques des neuf seigneurs contre les Empires Immortels (23.09.2026, 16 h 30 ; tables du jeu lues dans les
# packs par tables_jeu.py, le kit n'ayant pas toutes les données) :
# - campaign_to_agent_subtypes : chaque seigneur légendaire de la campagne y est déclaré (35 aux Empires) ; Drycha,
#   Kemmler et Grom n'y étaient pas ;
# - province_to_mercenary_set_junctions : chaque province des Empires porte aussi la réserve de Drycha (Dryades
#   malveillantes, loups, chauves-souris, faucons, manticore, araignées : son recrutement propre, faction_requirement
#   wh2_dlc16_wef_drycha) ; table du STARTPOS ;
# - start_pos_characters : aux Empires, chaque seigneur commence avec un héros sur la case voisine ; ici sur une case
#   franchissable voisine (couches de WH1), libre, à plus de 2,5 hex d'une colonie ; pour les seigneurs en garnison
#   (Alberic, la Fée, le Duc rouge), près de leur capitale. Table du STARTPOS. Le second seigneur vampire de Mousillon
#   aux Empires n'est pas repris : Mousillon garde ses armées de WH1.
LEGENDAIRES_NEUFS = ["wh2_dlc16_wef_drycha", "wh_main_vmp_heinrich_kemmler", "wh2_dlc15_grn_grom_the_paunch"]
POOL_DRYCHA = "wh2_dlc16_wef_drycha_province_merc_pool"
# héros des Empires -> (notre faction, x, y)
HEROS_DE_DEPART = {
    "745034115": ("2120137086", 38, 255),     # paladin d'Alberic, près de Bordeleaux (34/254 était une case de la ville,
                                              # dans l'eau : déplacé en 38/255 par la construction le 23.09.2026, 23 h 32 ;
                                              # le lot ne réécrit pas une ligne déjà écrite)
    "1255356656": ("2120137100", 79, 126),    # paladin de la Fée, près du Château de Carcassonne
    "300638816": ("2120137146", 120, 267),    # sorcière troll de rivière de Grom, Massif d'Orquemont
    "1955635223": ("2120137202", 277, 215),   # chanteuse de sorts (Vie) de Durthu, Argwylon
    "1357882269": ("2120137221", 300, 55),    # guetteur de Drycha, Tyr Vanna
    "335546266": ("2120137230", 269, 88),     # guetteur d'Orion, Talsyn
    "1098058496": ("2120137128", 105, 132),   # gorebull de Morghur
    "335785212": ("2120137700", 296, 303),    # nécromancien de Kemmler, Poste de la Pierre Noire
}
# Audit de complétude de la construction (23.09.2026, 14 h 30) : les batailles de quête de CA reprises (Alberic, la Fée,
# Kemmler x 3, Grom, Drycha) citent 16 factions de bataille (*_qb*) ; CA les met dans tous ses startpos (sans personnage
# ni région), et en exclut 4 de la diplomatie. Et le Duc rouge n'avait pas de régiments de renom (Kemmler et les Comtes
# vampires ont wh_dlc04_vmp_units_of_renown_pool).
FACTIONS_DE_BATAILLE = ["wh_main_brt_bretonnia_qb1", "wh_main_brt_bretonnia_qb2", "wh_main_emp_empire_qb1",
                        "wh_main_nor_norsca_qb1", "wh_main_nor_norsca_qb2", "wh_main_nor_norsca_qb3",
                        "wh_main_grn_greenskins_qb1", "wh_main_grn_greenskins_qb2", "wh_main_grn_greenskins_qb3",
                        "wh_main_chs_chaos_qb1", "wh_main_chs_chaos_qb2", "wh_main_chs_chaos_qb3",
                        "wh2_dlc16_wef_wood_elves_qb4", "wh2_dlc16_wef_wood_elves_qb5", "wh2_dlc16_wef_wood_elves_qb6",
                        "wh2_dlc16_wef_wood_elves_qb7",
                        # factions naines de bataille (23.09.2026, 15 h 20) : armées naines des Échos isolées
                        # (saison_chroniques.lua, QB_PAR_ARMEE : qb2, que CA n'emploie dans aucun script)
                        "wh_main_dwf_dwarfs_qb1", "wh_main_dwf_dwarfs_qb2", "wh_main_dwf_dwarfs_qb3"]
RENOM_VAMPIRE = "wh_dlc04_vmp_units_of_renown_pool"


def lot_etape13():
    """Lot 13 : ce que l'audit des mécaniques a trouvé en moins face aux Empires (voir le commentaire ci-dessus). Tables
    province_to_mercenary_set_junctions et start_pos_characters : du STARTPOS (zz_startpos_db.pack, puis régénérer :
    construction). Rend ({table: TableKit}, [entrées])."""
    tables = {n: TableKit(n) for n in ("campaign_to_agent_subtypes", "province_to_mercenary_set_junctions",
                                       "start_pos_characters", "start_pos_factions", "cai_diplomacy_excluded_factions",
                                       "faction_to_mercenary_set_junctions")}
    tc = tables["campaign_to_agent_subtypes"]
    modele = tc.ou(agent_subtype="wh_dlc05_wef_orion", campaign_type=CAMPAGNE)[0][0]
    for st in LEGENDAIRES_NEUFS:
        tc.ajouter_sur_modele(modele, {"agent_subtype": st})

    tm = tables["province_to_mercenary_set_junctions"]
    modele = tm.modele(mercenary_set=POOL_DRYCHA)
    provinces = [v.get("key") for _, v in ((k, TableKit.valeurs(c)) for k, c in TableKit("provinces").lignes)
                 if v.get("key", "").startswith("wh_dlc05_")]
    for pr in provinces:
        corps = dict(tm.lignes)[modele]
        tm.ajouter(pr + POOL_DRYCHA, tm.avec(corps, "province", pr))

    tp = tables["start_pos_characters"]
    pris = set(tp.cles) | {tp.valeurs(c).get("ID") for _, c in tp.lignes}
    deja = {(tp.valeurs(c).get("faction"), tp.valeurs(c).get("subtype")) for _, c in tp.lignes}
    lignes_ie = {tp.valeurs(c).get("ID"): (k, c) for k, c in tp.lignes}
    neufs = []
    for ie, (faction, x, y) in HEROS_DE_DEPART.items():
        if ie not in lignes_ie:
            # 24.09.2026 (9.0) : le modèle des Empires peut disparaître (refonte des Comtes vampires : le nécromancien de
            # Kemmler 335785212 n'est plus dans le startpos des Empires) ; notre héros déjà écrit (faction et case) suffit
            nos = [tp.valeurs(c).get("ID") for _, c in tp.lignes
                   if (tp.valeurs(c).get("faction"), tp.valeurs(c).get("startx"), tp.valeurs(c).get("starty"))
                   == (faction, str(x), str(y))]
            if not nos:
                raise SystemExit(f"lot 13 : modèle des Empires {ie} absent et aucun héros à nous en {faction} ({x}, {y})")
            neufs += nos
            continue
        k, corps = lignes_ie[ie]
        if (faction, tp.valeurs(corps).get("subtype")) in deja:
            # déjà écrit : son identifiant, pour l'entrée build_pack
            neufs += [tp.valeurs(c).get("ID") for _, c in tp.lignes
                      if (tp.valeurs(c).get("faction"), tp.valeurs(c).get("subtype")) == (faction, tp.valeurs(corps).get("subtype"))]
            continue
        ident = ident_numerique(f"heros_de_depart:{ie}", pris)
        pris.add(ident)
        for col, val in (("ID", ident), ("faction", faction), ("startx", str(x)), ("starty", str(y))):
            corps = tp.avec(corps, col, val)
        tp.ajouter(ident, corps)
        neufs.append(ident)
    # factions de bataille de quête : les lignes des Empires, sous notre campagne
    tf = tables["start_pos_factions"]
    pris_f = set(tf.cles) | {tf.valeurs(c).get("ID") for _, c in tf.lignes}
    deja_f = {tf.valeurs(c).get("faction") for _, c in tf.lignes if tf.valeurs(c).get("campaign") == CAMPAGNE}
    ids_qb = []
    for k, corps in list(tf.lignes):
        v = tf.valeurs(corps)
        if v.get("campaign") == CAMPAGNE and v.get("faction") in FACTIONS_DE_BATAILLE:
            ids_qb.append(v.get("ID"))          # déjà écrit
            continue
        if v.get("campaign") != IE or v.get("faction") not in FACTIONS_DE_BATAILLE or v.get("faction") in deja_f:
            continue
        ident = ident_numerique(f"faction_de_bataille:{v['faction']}", pris_f)
        pris_f.add(ident)
        for col, val in (("ID", ident), ("campaign", CAMPAGNE)):
            corps = tf.avec(corps, col, val)
        tf.ajouter(ident, corps)
        ids_qb.append(ident)
    tx = tables["cai_diplomacy_excluded_factions"]
    for k, corps in list(tx.lignes):
        v = tx.valeurs(corps)
        if v.get("campaign") == IE and v.get("faction") in FACTIONS_DE_BATAILLE:
            tx.ajouter(v["faction"] + CAMPAGNE, tx.avec(corps, "campaign", CAMPAGNE))
    tr = tables["faction_to_mercenary_set_junctions"]
    modele = tr.modele(faction="wh2_dlc11_vmp_the_barrow_legion", mercenary_set=RENOM_VAMPIRE)
    tr.ajouter("wh_main_vmp_mousillon" + RENOM_VAMPIRE, tr.avec(dict(tr.lignes)[modele], "faction", "wh_main_vmp_mousillon"))
    return tables, [
        ("campaign_to_agent_subtypes", "campaign_to_agent_subtypes_tables", "campaign_type", CAMPAGNE),
        ("province_to_mercenary_set_junctions", "province_to_mercenary_set_junctions_tables", "province", "wh_dlc05_"),
        ("start_pos_characters", "start_pos_characters_tables", "ID", neufs),
        ("start_pos_factions", "start_pos_factions_tables", "ID", ids_qb),
        ("cai_diplomacy_excluded_factions", "cai_diplomacy_excluded_factions_tables", "campaign", CAMPAGNE),
        ("faction_to_mercenary_set_junctions", "faction_to_mercenary_set_junctions_tables", "faction",
         ["wh_main_vmp_mousillon"]),
    ]


# Noms de lore des ducs de la carte (saison_monde.lua) : noms de famille « de <duché> » et le prénom « Darthon » (Darthon
# Barbe de Fer, citation de chargement de CA). Fréquence 0 : jamais tirés au hasard pour un autre personnage. Identifiants
# stables (ident_numerique, graine « nom:<texte> »), repris tels quels par saison_monde.lua. Textes : textes_gameplay.json.
NOMS_DE_LORE = {
    "578028567": ("names_brt_bretonnia", "family_name", "de Quenelles"),
    "433068992": ("names_brt_bretonnia", "family_name", "de Bastonne"),
    "1496308970": ("names_brt_bretonnia", "family_name", "de Montfort"),
    "412763886": ("names_brt_bretonnia", "family_name", "de Parravon"),
    "593790985": ("names_brt_bretonnia", "family_name", "de Brionne"),
    "375345544": ("names_brt_bretonnia", "family_name", "de Gisoreux"),
    "1293672490": ("names_dwf_dwarfs", "forename", "Darthon"),
    # Tancred II, duc de Quenelles, « vainqueur de La Maisontaal » (le duc régnant, fils de Tancred Ier tombé au pont de
    # Montfort : lore-quetes\morts-kemmler-duc.md) ; nos textes disent « Tancred II » (23.09.2026)
    "645127004": ("names_brt_bretonnia", "forename", "Tancred II"),
    # noms de GW là où le français de CA diffère (clés de CA non surchargeables) : Armand d'Aquitaine, le Duc Rouge
    "167863795": ("names_brt_bretonnia", "family_name", "d'Aquitaine"),
    "1218116301": ("names_vmp_vampire_counts", "forename", "The Red Duke"),
}


# Prologues des seigneurs (saison_prologue.lua) : une réplique par lieu survolé, dite par le seigneur (conseiller
# faction_leader, comme les répliques d'intro de CA) ou par le conseiller de la culture (Morghur, qui ne parle pas).
# Fil de conseil = clé de réplique ; clé de niveau = cle_conseil(fil) ; texte : advice_levels_onscreen_text_<clé de niveau>
# (textes_gameplay.json ; source unique : scratchpad\audit-ui\prologues.py). Sans voix (audio_clip « n », comme CA).
PROLOGUES = [
    ("saison_prologue_alberic_1", "faction_leader"),
    ("saison_prologue_alberic_2", "faction_leader"),
    ("saison_prologue_alberic_3", "faction_leader"),
    ("saison_prologue_alberic_4", "faction_leader"),
    ("saison_prologue_fee_1", "faction_leader"),
    ("saison_prologue_fee_2", "faction_leader"),
    ("saison_prologue_fee_3", "faction_leader"),
    ("saison_prologue_fee_4", "faction_leader"),
    # Morghur parle lui-même, comme CA le fait parler dans son intro des Empires (wh3_dlc21_ie_camp_bst_morghur_intro_01,
    # advisor_name faction_leader) : répliques à la 1re personne (audit des seigneurs, M4 ; décision du 25.09.2026)
    ("saison_prologue_morghur_1", "faction_leader"),
    ("saison_prologue_morghur_2", "faction_leader"),
    ("saison_prologue_morghur_3", "faction_leader"),
    ("saison_prologue_morghur_4", "faction_leader"),
    ("saison_prologue_morghur_5", "faction_leader"),       # le Cromlech de Cadai, première cible (audit, 23.09.2026)
    ("saison_prologue_duc_1", "faction_leader"),
    ("saison_prologue_duc_2", "faction_leader"),
    ("saison_prologue_duc_3", "faction_leader"),
    ("saison_prologue_duc_4", "faction_leader"),
    ("saison_prologue_drycha_1", "faction_leader"),
    ("saison_prologue_drycha_2", "faction_leader"),
    ("saison_prologue_drycha_3", "faction_leader"),
    ("saison_prologue_drycha_4", "faction_leader"),
    ("saison_prologue_kemmler_1", "faction_leader"),
    ("saison_prologue_kemmler_2", "faction_leader"),
    ("saison_prologue_kemmler_3", "faction_leader"),
    ("saison_prologue_kemmler_4", "faction_leader"),
    ("saison_prologue_grom_1", "faction_leader"),
    ("saison_prologue_grom_2", "faction_leader"),
    ("saison_prologue_grom_3", "faction_leader"),
    ("saison_prologue_grom_4", "faction_leader"),
    ("saison_prologue_orion_1", "faction_leader"),
    ("saison_prologue_orion_2", "faction_leader"),
    ("saison_prologue_orion_3", "faction_leader"),
    ("saison_prologue_durthu_1", "faction_leader"),
    ("saison_prologue_durthu_2", "faction_leader"),
    ("saison_prologue_durthu_3", "faction_leader"),
    # les Sœurs du Crépuscule (24.09.2026) : les deux sœurs se répondent (conseiller faction_leader)
    ("saison_prologue_soeurs_1", "faction_leader"),
    ("saison_prologue_soeurs_2", "faction_leader"),
    ("saison_prologue_soeurs_3", "faction_leader"),
    ("saison_prologue_soeurs_4", "faction_leader"),
    ("saison_prologue_soeurs_5", "faction_leader")
]


def cle_conseil(fil):
    """Clé stable (numérique, comme celles de CA) du niveau de conseil d'un fil."""
    return ident_numerique("conseil:" + fil, set())


def lot_etape14():
    """Lot 14 : noms de lore des ducs (tableau names, sur une ligne de CA). Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    t = TableKit("names")
    modele = t.modele(id="2147345510")          # d'Aquitanie : nom de famille bretonnien de CA
    for ident, (groupe, genre_nom, texte) in NOMS_DE_LORE.items():
        corps = dict(t.lignes)[modele]
        for col, val in (("id", ident), ("names_group", groupe), ("type", genre_nom), ("frequency", "0"),
                         ("name", escape(texte))):
            corps = t.avec(corps, col, val)
        if genre_nom == "forename":
            corps = t.avec(corps, "gender", "m")
        t.ajouter(ident, corps)
    # répliques des prologues, sur la réplique d'intro de Grom (CA, conseiller faction_leader, sans voix)
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    th, tl = TableKit("advice_threads"), TableKit("advice_levels")
    mod_th, mod_tl = "wh3_dlc21_ie_camp_grn_grom_intro_01", "552584000"
    niveaux = []
    for fil, conseiller in PROLOGUES:
        cle = cle_conseil(fil)
        texte = (nos.get(f"advice_levels_onscreen_text_{cle}") or {}).get("en")
        if not texte:
            raise SystemExit(f"lot 14 : texte de la réplique {fil} absent de textes_gameplay.json")
        if cle in tl.cles and tl.valeurs(dict(tl.lignes)[cle]).get("advice_thread") != fil:
            raise SystemExit(f"lot 14 : la clé {cle} de {fil} est déjà prise")
        th.ajouter(fil, th.avec(dict(th.lignes)[mod_th], "thread", fil))
        corps = dict(tl.lignes)[mod_tl]
        for col, val in (("key", cle), ("advice_thread", fil), ("advisor_name", conseiller), ("onscreen_text", escape(texte))):
            corps = tl.avec(corps, col, val)
        if cle in tl.cles:
            tl.modifier(cle, {"advisor_name": conseiller, "onscreen_text": escape(texte)})
        else:
            tl.ajouter(cle, corps)
        niveaux.append(cle)
    return {"names": t, "advice_threads": th, "advice_levels": tl}, [
        ("names", "names_tables", "id", list(NOMS_DE_LORE)),
        ("advice_threads", "advice_threads_tables", "thread", [f for f, _ in PROLOGUES]),
        ("advice_levels", "advice_levels_tables", "key", niveaux)]


# Waaagh! de Grom (audit de la construction, 23.09.2026) : l'armée de Waaagh! prend ses renforts dans la réserve de sa
# faction et dans celle de la province (groupes grn_faction_boost_pool_province_*, 216 provinces des Empires, aucune des
# nôtres). Chaque province de notre carte reçoit la réserve de son équivalent des Empires : Montagnes Grises et Massif
# Orcal = Montagnes Grises du nord (Gobelins de la nuit, squigs : grottes du Massif, KotG) ; Carcassonne, Bastonne,
# Châlons (Aquitaine), côte de Lyonesse (Mousillon) = leurs réserves ; le reste = la réserve générique, comme CA pour
# Athel Loren, le Défilé de la Hache et la trouée de Gisoreux.
MODELE_WAAAGH = "grn_faction_boost_pool_province_bastonne"
RESERVES_WAAAGH = {
    "wh_dlc05_grey_mountains": "grn_faction_boost_pool_province_northern_grey_mountains",
    "wh_dlc05_grey_mountains_2": "grn_faction_boost_pool_province_northern_grey_mountains",
    "wh_dlc05_massif_orcal": "grn_faction_boost_pool_province_northern_grey_mountains",
    "wh_dlc05_carcassonne": "grn_faction_boost_pool_province_carcassonne",
    "wh_dlc05_bastonne": "grn_faction_boost_pool_province_bastonne",
    "wh_dlc05_aquitaine": "grn_faction_boost_pool_province_forest_of_chalons",
    "wh_dlc05_mousillon": "grn_faction_boost_pool_province_coast_of_lyonesse",
}
RESERVE_WAAAGH_GENERIQUE = "grn_faction_boost_pool_province_generic"


def lot_etape15():
    """Lot 15 : groupes de réserve de Waaagh! pour nos 26 provinces (5 tableaux, sur le groupe de Bastonne de CA). Hors
    startpos. Rend ({table: TableKit}, [entrées])."""
    noms = {"campaign_groups": "id", "campaign_group_members": "id", "campaign_group_member_criteria_provinces": "member",
            "campaign_group_member_criteria_subcultures": "member",
            "campaign_group_transported_military_force_unit_pools": "campaign_group"}
    tables = {n: TableKit(n) for n in noms}
    provinces = [v.get("key") for _, v in ((k, TableKit.valeurs(c)) for k, c in TableKit("provinces").lignes)
                 if v.get("key", "").startswith("wh_dlc05_")]
    groupes = []
    for pr in provinces:
        groupe = "saison_grn_boost_pool_" + pr
        groupes.append(groupe)
        for t, col in noms.items():
            tk = tables[t]
            for k, _ in tk.ou(**{col: MODELE_WAAAGH}):
                valeurs = {}
                for c, v in tk.valeurs(dict(tk.lignes)[k]).items():
                    if v == MODELE_WAAAGH and c != "transported_military_force_unit_pool":
                        valeurs[c] = groupe
                if t == "campaign_group_member_criteria_provinces":
                    valeurs["province"] = pr
                if t == "campaign_group_transported_military_force_unit_pools":
                    valeurs["transported_military_force_unit_pool"] = RESERVES_WAAAGH.get(pr, RESERVE_WAAAGH_GENERIQUE)
                tk.ajouter_sur_modele(k, valeurs)
    return tables, [(t, t + "_tables", col, "saison_grn_boost_pool_") for t, col in noms.items()]


# Audit des factions (23.09.2026, 05-journal\2026-09-23-audits\audit-factions.md) : tables du STARTPOS (à passer dans
# zz_startpos_db.pack, puis régénérer : construction). Valeurs relevées aux Empires (campagne wh3_main_combi).
ATHEL_LOREN_REGIONS = [
    "wh_dlc05_anmyr_halls_of_anaereth", "wh_dlc05_anmyr_tal_rond", "wh_dlc05_argwylon_waterfall_palace",
    "wh_dlc05_arranoc_tal_esth", "wh_dlc05_atylwyth_tal_amere", "wh_dlc05_cavaroc_halls_of_equos",
    "wh_dlc05_cythral_tyr_vanna", "wh_dlc05_fyr_darric_feast_halls", "wh_dlc05_fyr_darric_threllock",
    "wh_dlc05_modryn_glade_of_eternal_midnight", "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn_tal_eth_ayr",
    "wh_dlc05_talsyn_yn_ecryl_koiran", "wh_dlc05_tirsyth_glade_of_eternal_moonlight", "wh_dlc05_torgovann_cromlech_cadai",
    "wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_crag_halls", "wh_dlc05_wydrioth_tal_jul_finel"]
# rebelles : factions absentes du startpos (Teef Snatchaz, Cythral) remplacées comme aux Empires
REBELLES = {"wh_dlc05_massif_orcal_massif_orcal": "wh2_dlc15_grn_broken_axe",
            "wh_dlc05_massif_orcal_orquemont": "wh2_dlc15_grn_broken_axe",
            "wh_dlc05_cythral_tyr_vanna": "wh2_dlc16_wef_drycha"}


def lot_etape16():
    """Lot 16 : départ des factions (audit des factions, § 2.2, 2.4, 3.2, 3.6, 3.7).
    - start_pos_settlements : Durthu sans bâtiment interdit (wh_dlc05_wef_tree_spirits_1 est désactivé pour Argwylon et
      Drycha : wh_dlc16_wef_tree_spirits_drycha_1, comme l'IE) ; Tyr Vanna au niveau 2 avec l'esprit des arbres de Drycha
      et le tir, comme l'IE ;
    - start_pos_regions : plafond d'emplacements de l'IE (10 pour les colonies majeures d'Athel Loren, 8 pour les autres
      majeures, 2 pour le Chêne ; mineures inchangées à 4) ; rebelles sans nom anglais en dur, factions de rebelles
      présentes ;
    - start_pos_factions : Mousillon a la personnalité et le potentiel d'un grand vampire de l'IE (Mannfred), au lieu
      d'une faction mineure qui ne fait que survivre.
    Kemmler (colonie majeure ou non) : décision de Charles attendue. Rend ({table: TableKit}, [entrées])."""
    tables = {n: TableKit(n) for n in ("start_pos_settlements", "start_pos_regions", "start_pos_factions")}
    ts = tables["start_pos_settlements"]
    for k, corps in ts.lignes:
        if k.startswith("settlement:wh_dlc05_argwylon_waterfall_palace"):
            ts.modifier(k, {"building1": "wh_dlc16_wef_tree_spirits_drycha_1"})
        elif k.startswith("settlement:wh_dlc05_grey_mountains_2_blackstone_post"):
            # Kemmler (décision de Charles, 23.09.2026, 19 h 35, « comme aux Empires ») : capitale majeure de la province
            # des Montagnes Grises, comme le Poste de la Pierre Noire des Empires (major_2, Château Drachenfels bâti) ;
            # le Cercle de liaison du lot 16 gardé. Essais : mineure, pleine au tour 6 (2 emplacements) sur 3 fronts.
            ts.modifier(k, {"primary_building": "wh_main_vmp_settlement_major_2",
                            "building1": "wh2_main_special_castle_drachenfels_1",
                            "building2": "wh_main_vmp_bindingcircle_1"})
        elif k.startswith("settlement:wh_dlc05_grey_mountains_2_karak_ziflin"):
            # Karak Ziflin, « le plus petit fort nain des Montagnes Grises » : mineure, comme aux Empires (minor_1, caserne)
            ts.modifier(k, {"primary_building": "wh_main_dwf_settlement_minor_1", "building1": "wh_main_dwf_barracks_1"})
        elif k.startswith("settlement:wh_dlc05_cythral_tyr_vanna"):
            ts.modifier(k, {"primary_building": "wh_dlc05_wef_settlement_major_main_2",
                            "building1": "wh_dlc16_wef_tree_spirits_drycha_1", "building2": "wh_dlc05_wef_ranged_1"})
    tr = tables["start_pos_regions"]
    for k, corps in tr.lignes:
        v = tr.valeurs(corps)
        if v.get("campaign") != CAMPAGNE:
            continue
        maj = {}
        region = v.get("region")
        if region == "wh_dlc05_oak_of_ages":
            maj["slot_cap"] = "2"
        elif region == "wh_dlc05_grey_mountains_2_blackstone_post":
            maj["slot_cap"] = "8"            # majeure, comme aux Empires (Charles, 19 h 35)
        elif region == "wh_dlc05_grey_mountains_2_karak_ziflin":
            maj["slot_cap"] = "4"            # mineure, comme aux Empires
        elif v.get("slot_cap") == "6":
            maj["slot_cap"] = "10" if region in ATHEL_LOREN_REGIONS else "8"
        if v.get("rebel_faction_name"):
            maj["rebel_faction_name"] = ""
        if region in REBELLES:
            maj["rebel_faction"] = REBELLES[region]
        if any(v.get(c) != val for c, val in maj.items()):
            tr.modifier(k, maj)
    # capitale de la province des Montagnes Grises : le Poste de la Pierre Noire, comme aux Empires (Karak Ziflin mineure) ;
    # table déjà embarquée par build_pack.TABLES (region_to_province_junctions, préfixe wh_dlc05_)
    tp = tables["region_to_province_junctions"] = TableKit("region_to_province_junctions")
    for k, corps in tp.lignes:
        v = tp.valeurs(corps)
        voulu = {"wh_dlc05_grey_mountains_2_blackstone_post": "1",
                 "wh_dlc05_grey_mountains_2_karak_ziflin": "0"}.get(v.get("region"))
        if voulu is not None and v.get("is_capital") != voulu:
            tp.modifier(k, {"is_capital": voulu})
    tf = tables["start_pos_factions"]
    for k, corps in tf.lignes:
        v = tf.valeurs(corps)
        if v.get("campaign") == CAMPAGNE and v.get("faction") == "wh_main_vmp_mousillon":
            # 24.09.2026 (enquête d'équilibrage, C1.3) : les deux colonnes séparément ; avec un seul test sur le groupe,
            # le potentiel n'était jamais écrit (et le lot 11 remettait celui des Empires, combi_minor_survivor)
            tf.modifier(k, {"cai_personality_group": "wh3_combi_personality_group_vampire_mannfred",
                            "faction_potential": "combi_vampire_mannfred"})
    return tables, [("start_pos_settlements", "start_pos_settlements_tables", "settlement_id", "(startpos)"),
                    ("start_pos_regions", "start_pos_regions_tables", "id", "(startpos)"),
                    ("start_pos_factions", "start_pos_factions_tables", "ID", "(startpos)")]


# Monuments de CA (décision de Charles, 23.09.2026, 16 h 15 : « ajoute les monuments et bâtiments ») : état des lieux et
# sources dans 05-journal\2026-09-23-audits\etat-des-lieux-monuments.md. Gabarits de CA quand ils existent à la bonne
# taille ; sinon gabarits à nous (clés wh_dlc05_mini_special_*, déclarées ici : lignes slot_templates et
# slot_template_permitted_building_chains, entrée de tables_gameplay.py) = le gabarit actuel + le monument.
# région -> {type d'emplacement: gabarit}
GABARITS_MONUMENTS = {
    # Tour de l'Enchanteresse (la Fée) : gabarits de CA, mêmes jeux que les nôtres + le monument
    "wh_dlc05_carcassonne_castle_carcassonne": {"primary": "wh_main_special_carcassonne_primary",
                                                "secondary": "wh_main_special_carcassonne_secondary"},
    # Pics de Parravon (pégases)
    "wh_dlc05_parravon_parravon": {"primary": "wh2_main_special_parravon_primary",
                                   "secondary": "wh2_main_special_parravon_secondary"},
    # Massif d'Orquemont (Grom) : colonie spéciale peau-verte et Carrière du Troll de pierre (principal de départ changé)
    "wh_dlc05_massif_orcal_massif_orcal": {"primary": "wh3_main_special_massif_orcal_primary",
                                           "secondary": "wh_main_special_massif_orca_secondary"},
    # Port légendaire de Bordeleaux (Albéric) : Cale sèche de Manann (port de départ changé)
    "wh_dlc05_bordeleaux_bordeleaux": {"port": "wh_main_special_bordeleaux_port"},
    # ressources de CA absentes chez nous : l'or de Tharravil (lore : mine d'or la plus riche du monde, KotG), teintures
    # de Karak Ziflin, pâturages de Quenelles, fourrures de Gisoreux (gabarits de CA de même taille)
    "wh_dlc05_montfort_tharravil": {"secondary": "wh_main_human_minor_secondary_gold"},
    # Karak Ziflin mineure, comme aux Empires (Charles, 19 h 35) : gabarits de CA de l'IE
    "wh_dlc05_grey_mountains_2_karak_ziflin": {"primary": "wh_main_human_minor_primary",
                                               "secondary": "wh_main_human_minor_secondary_dyes"},
    "wh_dlc05_quenelles_quenelles": {"secondary": "wh_main_human_major_secondary_pastures"},
    "wh_dlc05_gisoreux_gisoreux": {"secondary": "wh_main_human_major_secondary_furs"},
    # gabarits à nous
    # Poste de la Pierre Noire majeur, comme aux Empires (Charles, 19 h 35) : principal de CA (Drachenfels) ; secondaire =
    # celui de CA + Tertre de Krell (lot 21, monuments-lore.json)
    "wh_dlc05_grey_mountains_2_blackstone_post": {"primary": "wh2_main_special_castle_drachenfels_primary",
                                                  "secondary": "wh_dlc05_mini_special_blackstone_post_major_secondary"},
    "wh_dlc05_mousillon_mousillon": {"secondary": "wh_dlc05_mini_special_mousillon_secondary"},
    "wh_dlc05_fyr_darric_feast_halls": {"secondary": "wh_dlc05_mini_special_feast_halls_secondary"},
    "wh_dlc05_cythral_tyr_vanna": {"secondary": "wh_dlc05_mini_special_tyr_vanna_secondary"},
    "wh_dlc05_wydrioth_tal_jul_finel": {"secondary": "wh_dlc05_mini_special_tal_jul_finel_secondary"},
    "wh_dlc05_modryn_glade_of_eternal_midnight": {"secondary": "wh_dlc05_mini_special_modryn_secondary"},
    "wh_dlc05_talsyn_tal_eth_ayr": {"secondary": "wh_dlc05_mini_special_tal_eth_ayr_secondary"},
}
# gabarit à nous -> (ressource, gabarit de base dont on reprend les lignes, [(jeu de chaînes, chaîne) ajoutés])
GABARITS_A_NOUS = {
    # Château Drachenfels (Kemmler) : CA l'a au Poste de la Pierre Noire aux Empires, sur une colonie majeure ; la nôtre
    # reste mineure (décision de Charles) : garnison et générique mineurs, fer de CA, monument
    "wh_dlc05_mini_special_blackstone_post_secondary": ("res_rom_iron", "wh_main_human_minor_secondary",
        [("wh3_main_secondary_addon_landmark_castle_drachenfels", ""), ("wh3_main_secondary_addon_res_iron", "")]),
    # Forteresse de Merovech (le Duc Rouge) : les gabarits de CA rétrogradent la ville en mineure ; le nôtre la garde majeure
    "wh_dlc05_mini_special_mousillon_secondary": ("", "wh_main_human_major_secondary",
        [("wh3_main_secondary_addon_landmark_mousillon", "")]),
    # Fyr Darric, terre de Loec et foyer des Danseurs de guerre (WE 8e p. 12) : salle des Danseurs et Bosquet ombragé de Loec
    "wh_dlc05_mini_special_feast_halls_secondary": ("res_rom_wine", "wh_dlc05_elf_major_secondary_wine",
        [("", "wh_dlc05_wef_office_wardancer_feast_halls"), ("", "wh2_dlc16_special_forest_of_gloom_shadow_groves_of_loec")]),
    # Tyr Vanna, dans le Cythral clos de pierres-gardiennes (WE 8e p. 12) : Pierres gardiennes des Bois Sauvages (Drycha)
    "wh_dlc05_mini_special_tyr_vanna_secondary": ("res_rom_marble", "wh_dlc05_elf_major_secondary_marble",
        [("", "wh_dlc05_wef_office_wildwood_waystones")]),
    # temples de WH1 (monuments d'autres régions aux Empires) : Anath Raema aux Pics-aux-Pins (WE 8e p. 43) ; Ereth Khial
    # en Modryn et Kurnous en Talsyn : lieux choisis [extrapolation, état des lieux § 4.3]
    "wh_dlc05_mini_special_tal_jul_finel_secondary": ("", "wh_dlc05_elf_major_secondary",
        [("", "wh_dlc05_wef_temple_anath_raema")]),
    "wh_dlc05_mini_special_modryn_secondary": ("", "wh_dlc05_elf_major_secondary",
        [("", "wh_dlc05_wef_temple_ereth_khial")]),
    "wh_dlc05_mini_special_tal_eth_ayr_secondary": ("", "wh_dlc05_elf_major_secondary",
        [("", "wh_dlc05_wef_temple_kurnous")]),
}
# bâtiments de départ à changer avec le gabarit
DEPART_MONUMENTS = {
    "settlement:wh_dlc05_massif_orcal_massif_orcal": {"primary_building": "wh2_dlc15_special_settlement_massif_orcal_grn_3"},
    "settlement:wh_dlc05_bordeleaux_bordeleaux": {"port_building": "wh_main_brt_legendary_port_1"},
}


def lot_etape18():
    """Lot 18 : monuments (voir GABARITS_MONUMENTS). Tables start_pos_region_slot_templates et start_pos_settlements :
    STARTPOS (synchronisation par la construction, --cle id / settlement_id, puis régénération). Rend ({table: TableKit},
    [entrées])."""
    import tables_jeu as TJ
    tables = {n: TableKit(n) for n in ("slot_templates", "slot_template_permitted_building_chains",
                                       "start_pos_region_slot_templates", "start_pos_settlements")}
    tst, tpc = tables["slot_templates"], tables["slot_template_permitted_building_chains"]
    jeu = TJ.table("slot_template_permitted_building_chains")
    kit_pc = [tpc.valeurs(c) for _, c in tpc.lignes]
    modele_st = tst.lignes[0][0]
    modele_pc = tpc.lignes[0][0]
    for cle, (ressource, base, ajouts) in GABARITS_A_NOUS.items():
        tst.ajouter_sur_modele(modele_st, {"key": cle, "resource": ressource})
        lignes = [(v.get("chain_set") or "", v.get("chain") or "", v.get("super_chain") or "", v.get("remove") or "0")
                  for v in kit_pc if v["slot_template"] == base]
        if not lignes:
            lignes = [(r.get("chain_set") or "", r.get("chain") or "", r.get("super_chain") or "", str(r.get("remove") or 0))
                      for r in jeu if r["slot_template"] == base]
        if not lignes:
            raise SystemExit(f"lot 18 : gabarit de base {base} introuvable")
        for jeu_c, chaine in ajouts:
            lignes.append((jeu_c, chaine, "", "0"))
        for jeu_c, chaine, super_c, retrait in lignes:
            corps = dict(tpc.lignes)[modele_pc]
            for col, val in (("slot_template", cle), ("chain_set", jeu_c), ("chain", chaine), ("super_chain", super_c),
                             ("remove", retrait)):
                corps = tpc.avec(corps, col, val)
            tpc.ajouter(cle + jeu_c + chaine + super_c, corps)
    trs = tables["start_pos_region_slot_templates"]
    for k, corps in trs.lignes:
        v = trs.valeurs(corps)
        voulu = GABARITS_MONUMENTS.get(v.get("region"), {}).get(v.get("slot_type"))
        if v.get("campaign") == CAMPAGNE and voulu and v.get("slot_template") != voulu:
            trs.modifier(k, {"slot_template": voulu})
    ts = tables["start_pos_settlements"]
    for k, corps in ts.lignes:
        for debut, valeurs in DEPART_MONUMENTS.items():
            if k.startswith(debut) and any(ts.valeurs(corps).get(c) != val for c, val in valeurs.items()):
                ts.modifier(k, valeurs)
    return tables, [("slot_templates", "slot_templates_tables", "key", "wh_dlc05_mini_special_"),
                    ("slot_template_permitted_building_chains", "slot_template_permitted_building_chains_tables",
                     "slot_template", "wh_dlc05_mini_special_"),
                    ("start_pos_region_slot_templates", "(startpos)", "id", ""),
                    ("start_pos_settlements", "(startpos)", "settlement_id", "")]


# Racines du monde (décision de Charles, 23.09.2026, 16 h 25) : les rituels de CA (Racines profondes) ne partent que de
# forêts des Empires et visent leur Chêne. Chez nous, cinq grandes clairières d'Athel Loren reliées : une armée elfe qui se
# tient dans l'une rejoint une autre en un instant. Même catégorie et même forme que CA (WORLDROOTS_TELEPORTATION : gratuit,
# délai global) ; délai de 8 tours au lieu de 10 (traversée à pied de la forêt : 5 à 7 tours ; invasions de l'histoire de
# WH1 : tous les 6 tours). Débloqués au tour 10, un par un, par saison_foret.lua (ceux de CA restent fermés).
MODELE_RACINES = "wh2_dlc16_worldroots_teleport_athel_loren"
RACINES_DU_MONDE = {
    "saison_racines_chene": "wh_dlc05_oak_of_ages",
    "saison_racines_clairiere_royale": "wh_dlc05_talsyn_yn_ecryl_koiran",
    "saison_racines_palais_des_chutes": "wh_dlc05_argwylon_waterfall_palace",
    "saison_racines_pics_de_findol": "wh_dlc05_wydrioth_crag_halls",
    "saison_racines_bois_sauvage": "wh_dlc05_cythral_tyr_vanna",
}
DELAI_RACINES = "8"


def lot_etape19():
    """Lot 19 : un rituel par clairière de destination ; le groupe de régions de départ = les quatre autres clairières.
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    noms = ("region_groups", "regions_to_region_groups_junctions", "rituals", "ritual_payloads",
            "ritual_payload_teleport_armies", "ritual_targets", "ritual_military_force_target_criterias",
            "campaign_group_rituals")
    t = {n: TableKit(n) for n in noms}
    m_jonction = t["regions_to_region_groups_junctions"].ou(region_group=MODELE_RACINES)[0][0]
    for cle, region in RACINES_DU_MONDE.items():
        groupe = cle + "_depart"
        t["region_groups"].ajouter_sur_modele(MODELE_RACINES, {"group_key": groupe})
        for autre in RACINES_DU_MONDE.values():
            if autre != region:
                t["regions_to_region_groups_junctions"].ajouter_sur_modele(m_jonction, {"region_group": groupe, "region": autre})
        t["ritual_payloads"].ajouter_sur_modele(MODELE_RACINES, {"key": cle})
        t["ritual_payload_teleport_armies"].ajouter_sur_modele(MODELE_RACINES, {"payload": cle, "region": region})
        t["ritual_military_force_target_criterias"].ajouter_sur_modele(MODELE_RACINES, {"key": cle, "region_group": groupe})
        t["ritual_targets"].ajouter_sur_modele(MODELE_RACINES, {"key": cle, "military_force_criteria": cle})
        titre = (nos.get("rituals_display_name_" + cle) or {}).get("en", cle)
        desc = (nos.get("rituals_description_" + cle) or {}).get("en", "")
        t["rituals"].ajouter_sur_modele(MODELE_RACINES, {"key": cle, "completion_payload": cle, "target": cle,
                                                         "global_cooldown_time": DELAI_RACINES,
                                                         "display_name": escape(titre), "description": escape(desc)})
        deblocage = (nos.get("campaign_group_rituals_unlock_text_saison_feature_wood_elves" + cle) or {}).get("en", "")
        t["campaign_group_rituals"].ajouter_sur_modele("wh_dlc05_feature_wood_elves" + MODELE_RACINES,
                                                       {"campaign_group": "saison_feature_wood_elves", "ritual": cle,
                                                        "initially_unlocked": "0", "unlock_text": escape(deblocage)})
    return t, [("region_groups", "region_groups_tables", "group_key", "saison_racines_"),
               ("regions_to_region_groups_junctions", "regions_to_region_groups_junctions_tables", "region_group",
                "saison_racines_"),
               ("rituals", "rituals_tables", "key", "saison_racines_"),
               ("ritual_payloads", "ritual_payloads_tables", "key", "saison_racines_"),
               ("ritual_payload_teleport_armies", "ritual_payload_teleport_armies_tables", "payload", "saison_racines_"),
               ("ritual_targets", "ritual_targets_tables", "key", "saison_racines_"),
               ("ritual_military_force_target_criterias", "ritual_military_force_target_criterias_tables", "key",
                "saison_racines_"),
               ("campaign_group_rituals", "campaign_group_rituals_tables", "ritual", "saison_racines_")]


# Citations de chargement (décision de Charles, 23.09.2026, 16 h 15) : tri complet et 30 citations à nous
# (05-journal\2026-09-23-audits\citations-chargement.md ; fichier citations-chargement.json : garder, retirer, retablir,
# nouvelles). Les textes des citations à nous sont dans textes_gameplay.json (loading_screen_quotes_title_ / _description_).
MODELE_CITATION = "wh3_dlc23_chd_albrecht_1"


def lot_etape20():
    """Lot 20 : retire les citations de CA hors sujet encore rattachées à notre carte ; rétablit celles retirées à tort ;
    ajoute nos citations (loading_screen_quotes, table neuve pour nous : essai de démarrage avant annonce, erreur 107).
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    c = json.load(open(CITATIONS, encoding="utf-8"))
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    tables = {n: TableKit(n) for n in ("loading_screen_quotes", "loading_screen_quotes_to_campaigns")}
    tq, tl = tables["loading_screen_quotes"], tables["loading_screen_quotes_to_campaigns"]
    a_retirer = set(c["retirer"])
    for k, corps in tl.lignes:
        v = tl.valeurs(corps)
        if v.get("campaign") == CARTE and v.get("loading_quote") in a_retirer:
            tl.retirer(k)
    modele_lien = tl.lignes[0][0]
    for cle in c.get("retablir", []) + c.get("nouvelles", []):
        tl.ajouter_sur_modele(modele_lien, {"loading_quote": cle, "campaign": CARTE})
    for cle in c.get("nouvelles", []):
        titre = (nos.get("loading_screen_quotes_title_" + cle) or {}).get("en", "")
        desc = (nos.get("loading_screen_quotes_description_" + cle) or {}).get("en", "")
        if not titre or not desc:
            raise SystemExit(f"lot 20 : textes de {cle} absents de textes_gameplay.json")
        tq.ajouter_sur_modele(MODELE_CITATION, {"key": cle, "title": escape(titre), "description": escape(desc),
                                                 "first_shown_weighting": "2"})
    return tables, [("loading_screen_quotes", "loading_screen_quotes_tables", "key", "saison_citation_"),
                    ("loading_screen_quotes_to_campaigns", "loading_screen_quotes_to_campaigns_tables", "campaign", CARTE)]


# Armées et trésors de départ (décisions de Charles, 23.09.2026, 16 h 30 ; proposition et contrôle d'équilibre :
# 05-journal\2026-09-23-audits\armees-de-depart.md). Source unique : 04-projets\saison-des-revelations\armees-depart.json
# ({"factions": {faction: {treasury, generaux: {ID: [unités]}, nouveaux_generaux: [...]}}, "difficulte": [lignes]}).
ARMEES_DEPART = os.path.join(os.path.dirname(TEXTES_GAMEPLAY), "..", "armees-depart.json")


def lot_etape17():
    """Lot 17 : start_pos_factions (trésor), start_pos_land_units (armées de nos généraux : lignes à nous remplacées),
    start_pos_characters et start_pos_character_to_settlements (second seigneur de Mousillon, sur la ligne de l'IE),
    faction_potential_difficulty_overrides (table neuve pour nous : essai de démarrage, erreur 107). Tables start_pos_* :
    STARTPOS (synchronisation par la construction, puis régénération). Rend ({table: TableKit}, [entrées])."""
    d = json.load(open(ARMEES_DEPART, encoding="utf-8"))
    noms = ("start_pos_factions", "start_pos_land_units", "start_pos_characters", "start_pos_character_to_settlements",
            "faction_potential_difficulty_overrides")
    t = {n: TableKit(n) for n in noms}
    tf, tu, tc, ts, td = (t[n] for n in noms)
    ident_faction = {}
    for k, corps in tf.lignes:
        v = tf.valeurs(corps)
        if v.get("campaign") == CAMPAGNE:
            ident_faction[v["faction"]] = v["ID"]
            voulu = d["factions"].get(v["faction"], {}).get("treasury")
            if voulu is not None and v.get("treasury") != str(voulu):
                tf.modifier(k, {"treasury": str(voulu)})
            # potentiel de l'IA (catégorie de CA, faction_potential_categories) : Orques et Hommes-bêtes, vraies menaces
            potentiel = d["factions"].get(v["faction"], {}).get("faction_potential")
            if potentiel and v.get("faction_potential") != potentiel:
                tf.modifier(k, {"faction_potential": potentiel})
    nos_generaux = {tc.valeurs(c)["ID"] for _, c in tc.lignes if tc.valeurs(c).get("faction") in ident_faction.values()}
    pris_u = set(tu.cles) | {tu.valeurs(c).get("id") for _, c in tu.lignes}
    modele_u = tu.lignes[0][0]
    ids_unites = []

    def armee(general, unites):
        """Remplace l'armée du général (lignes à nous) par `unites` ; idempotent (clés stables, graine = rang)."""
        actuelles = [(k, tu.valeurs(c)) for k, c in tu.lignes if tu.valeurs(c).get("general") == general]
        cles_voulues = []
        for i, u in enumerate(unites):
            cle = ident_numerique(f"armee_depart:{general}:{i}:{u}", pris_u - {k for k, _ in actuelles})
            cles_voulues.append(cle)
        for k, v in actuelles:
            if k not in cles_voulues:
                tu.retirer(k)
        for cle, u in zip(cles_voulues, unites):
            if cle not in tu.cles:
                tu.ajouter_sur_modele(modele_u, {"id": cle, "unit_type": u, "general": general, "soldiers": "100",
                                                 "unique": "0"})
                pris_u.add(cle)
            ids_unites.append(cle)

    ids_persos, ids_garnisons = [], []
    for faction, e in d["factions"].items():
        for general, unites in e.get("generaux", {}).items():
            if general not in nos_generaux:
                raise SystemExit(f"lot 17 : général {general} ({faction}) absent de notre startpos")
            armee(general, unites)
        for n in e.get("nouveaux_generaux", []):
            # idempotent : nos copies déjà écrites (même modèle, notre faction) ne comptent pas comme prises
            modele_c = tc.valeurs(dict(tc.lignes)[n["modele_ie"]])
            copies = {tc.valeurs(c)["ID"] for _, c in tc.lignes
                      if tc.valeurs(c).get("faction") == ident_faction[faction]
                      and tc.valeurs(c).get("subtype") == modele_c.get("subtype")
                      and tc.valeurs(c).get("Name") == modele_c.get("Name")}
            pris_c = set(tc.cles) | {tc.valeurs(c).get("ID") for _, c in tc.lignes}
            # une copie déjà écrite garde son identifiant (sinon, après le retrait d'une ancienne copie, l'identifiant
            # libéré serait repris et les deux copies alterneraient d'une passe à l'autre)
            ident = sorted(copies)[0] if copies else \
                ident_numerique(f"general_de_depart:{faction}:{n['modele_ie']}", pris_c - copies)
            if ident not in tc.cles:
                valeurs = {"ID": ident, "faction": ident_faction[faction], "startx": str(n.get("x", 0)),
                           "starty": str(n.get("y", 0))}
                tc.ajouter_sur_modele(n["modele_ie"], valeurs)
            # 24.09.2026 (9.0) : CA a changé le nom du modèle (2147353218 -> 2147358143) ; notre ancienne copie (même
            # faction, même sous-type, même case, autre nom) n'est plus reconnue et une seconde a été faite : l'ancienne
            # est retirée avec son armée et son lien de garnison (un seul second seigneur, sur la ligne des Empires)
            for k_old, c_old in list(tc.lignes):
                v_old = tc.valeurs(c_old)
                if (v_old.get("ID") != ident and v_old.get("faction") == ident_faction[faction]
                        and v_old.get("subtype") == modele_c.get("subtype")
                        and (v_old.get("startx"), v_old.get("starty")) == (str(n.get("x", 0)), str(n.get("y", 0)))):
                    tc.retirer(k_old)
                    for k_u, c_u in tu.lignes:
                        if tu.valeurs(c_u).get("general") == v_old.get("ID"):
                            tu.retirer(k_u)
                    for k_s, c_s in ts.lignes:
                        if ts.valeurs(c_s).get("character") == v_old.get("ID"):
                            ts.retirer(k_s)
            ids_persos.append(ident)
            if n.get("garnison"):
                cle_g = ident
                if cle_g not in ts.cles:
                    ts.ajouter_sur_modele(ts.lignes[0][0], {"character": ident, "settlement": n["garnison"],
                                                             "unique": "0"})
                ids_garnisons.append(ident)
            armee(ident, n["unites"])
    modele_d = td.lignes[0][0]
    voulues_d = set()
    for ligne in d.get("difficulte", []):
        # clé du kit : faction + niveau + campagne + faction du joueur + sous-culture du joueur (lignes de CA)
        cle = "".join(str(ligne[c]) for c in ("faction", "faction_difficulty_level", "campaign_key", "player_faction",
                                              "player_subculture"))
        voulues_d.add(cle)
        if cle not in td.cles:
            corps = dict(td.lignes)[modele_d]
            for c, v in ligne.items():
                corps = td.avec(corps, c, str(v))
            td.ajouter(cle, corps)
    # 24.09.2026, 23 h : une ligne retirée d'armees-depart.json (bonus de Grom en normal) se retire aussi du kit ; seules
    # nos lignes (notre campagne) sont concernées
    for k, c in list(td.lignes):
        if td.valeurs(c).get("campaign_key") == CAMPAGNE and k not in voulues_d:
            td.retirer(k)
    return t, [("start_pos_factions", "start_pos_factions_tables", "ID", "(startpos)"),
               ("start_pos_land_units", "start_pos_land_units_tables", "id", "(startpos)"),
               ("start_pos_characters", "start_pos_characters_tables", "ID", "(startpos)"),
               ("start_pos_character_to_settlements", "start_pos_character_to_settlements_tables", "character",
                "(startpos)"),
               ("faction_potential_difficulty_overrides", "faction_potential_difficulty_overrides_tables",
                "campaign_key", CAMPAGNE)]


# Monuments du lore (lot 21, 23.09.2026) : 14 monuments, 17 chaînes (une par culture, comme les Pics de Parravon de CA).
# Fiche, effets de CA et sources : 04-projets\saison-des-revelations\monuments-lore.json. Les gabarits d'emplacement
# des régions passent par le lot 18 (GABARITS_A_NOUS / GABARITS_MONUMENTS, étendus ici depuis la fiche).
MONUMENTS_LORE = json.load(open(os.path.join(os.path.dirname(TEXTES_GAMEPLAY), "..", "monuments-lore.json"),
                                encoding="utf-8"))
for _m in MONUMENTS_LORE:
    _g = _m["gabarit_propose"]
    _ajouts = [("", _ch["chaine"]) for _ch in _m["chaines"].values()]
    if _g["cle"] in GABARITS_A_NOUS:
        _r, _b, _a = GABARITS_A_NOUS[_g["cle"]]
        GABARITS_A_NOUS[_g["cle"]] = (_r, _b, _a + [x for x in _ajouts if x not in _a])
    else:
        GABARITS_A_NOUS[_g["cle"]] = (_g.get("ressource", ""), _g["base"], _ajouts)
    GABARITS_MONUMENTS.setdefault(_m["region"], {})["secondary"] = _g["cle"]
ICONES_MONUMENTS = {_m["icone"]["cle"]: _m["icone"]["source"] for _m in MONUMENTS_LORE
                    if isinstance(_m["icone"], dict) and _m["icone"].get("source")}


def lot_etape21():
    """Lot 21 : définitions des monuments du lore (tables building_* : neuves pour nous, essai de démarrage avant
    annonce, erreur 107). Les gabarits des régions : lot 18 (STARTPOS). Icônes : ICONES_MONUMENTS (dossier du projet ->
    ui/buildings/icons/<clé>.png, par la construction). Rend ({table: TableKit}, [entrées])."""
    noms = ("building_superchains", "building_chains", "building_chain_availability_sets", "building_instances",
            "building_levels", "building_culture_variants", "building_effects_junction",
            "building_set_to_building_junctions", "cai_construction_system_building_values",
            "building_short_description_texts", "building_flavour_texts")
    from xml.sax.saxutils import escape
    t = {n: TableKit(n) for n in noms}
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    m_sch, m_ch = "wh_main_sch_bretonnia_legendary_carcassonne", "wh_main_bretonnia_legendary_carcassonne"
    m_bas = t["building_chain_availability_sets"].ou(building_chain=m_ch)[0][0]
    m_ins, m_lvl = "wh_main_BRETONNIA_legendary", "wh_main_brt_legendary_enchantress_tower"
    m_var = t["building_culture_variants"].ou(building=m_lvl)[0][0]
    m_eff_sans = t["building_effects_junction"].ou(building=m_lvl, context_requirement="")[0][0]
    m_eff_avec = t["building_effects_junction"].ou(building=m_lvl, context_requirement="IsBretonnia")[0][0]
    m_set = t["building_set_to_building_junctions"].ou(building_chain=m_ch)[0][0]
    m_cai = t["cai_construction_system_building_values"].ou(building_chain="wh2_main_special_mousillon_merovech",
                                                          cai_construction_system_category_group="cai_support_group")[0][0]
    for m in MONUMENTS_LORE:
        base = "wh_dlc05_mini_landmark_" + m["nom"]
        icone = m["icone"]["cle"] if isinstance(m["icone"], dict) else m["icone"]
        t["building_superchains"].ajouter_sur_modele(m_sch, {"key": "wh_dlc05_mini_sch_" + m["nom"]})
        t["building_instances"].ajouter_sur_modele(m_ins, {"key": base, "num_instances": "1"})
        for ch in m["chaines"].values():
            chaine, niveau = ch["chaine"], ch["niveau"]
            for cle in ("building_culture_variants_name_" + niveau,
                        "building_short_description_texts_short_description_" + niveau):
                if not (nos.get(cle) or {}).get("en"):
                    raise SystemExit(f"lot 21 : texte {cle} absent de textes_gameplay.json")
            titre_en = escape(nos["building_culture_variants_name_" + niveau]["en"])
            t["building_chains"].ajouter_sur_modele(m_ch, {"key": chaine, "building_superchain": "wh_dlc05_mini_sch_" + m["nom"],
                                                           "in_encyclopedia": "1", "chain_tooltip": "Landmark",
                                                           "encyclopedia_name": titre_en})
            t["building_chain_availability_sets"].ajouter_sur_modele(m_bas, {"building_chain": chaine,
                                                                             "id": ch["availability_set"]})
            t["building_levels"].ajouter_sur_modele(m_lvl, {
                "level_name": niveau, "chain": chaine, "create_cost": str(m["cout"]), "create_time": str(m["tours"]),
                "building_instance_key": base,
                "primary_slot_building_building_level_requirement": str(m["niveau_principal_requis"])})
            t["building_culture_variants"].ajouter_sur_modele(m_var, {
                "building": niveau, "culture": "", "subculture": "", "faction": "", "icon": icone,
                "short_description": niveau, "name": titre_en, "flavour": niveau})
            for e in ch["effets"]:
                modele = m_eff_avec if e.get("context_requirement") else m_eff_sans
                v = e["value"]
                t["building_effects_junction"].ajouter_sur_modele(modele, {
                    "building": niveau, "effect": e["effect"], "effect_scope": e["scope"], "value": str(float(v)),
                    "value_damaged": str(float(v) / 2 if abs(v) > 1 else float(v)), "value_ruined": "0.0",
                    "context_requirement": e.get("context_requirement", "")})
            t["building_set_to_building_junctions"].ajouter_sur_modele(m_set, {"building_chain": chaine})
            t["cai_construction_system_building_values"].ajouter_sur_modele(m_cai, {"building_chain": chaine})
            # textes anglais de repli dans les tables (les textes injectés, FR et EN, sont dans textes_gameplay.json)
            desc = escape(nos["building_short_description_texts_short_description_" + niveau]["en"])
            t["building_short_description_texts"].ajouter_sur_modele(m_lvl, {"key": niveau, "short_description": desc})
            t["building_flavour_texts"].ajouter_sur_modele(m_lvl, {"key": niveau, "flavour": desc})
    p = "wh_dlc05_mini_"
    return t, [("building_superchains", "building_superchains_tables", "key", p),
               ("building_chains", "building_chains_tables", "key", p),
               ("building_chain_availability_sets", "building_chain_availability_sets_tables", "building_chain", p),
               ("building_instances", "building_instances_tables", "key", p),
               ("building_levels", "building_levels_tables", "level_name", p),
               ("building_culture_variants", "building_culture_variants_tables", "building", p),
               ("building_effects_junction", "building_effects_junction_tables", "building", p),
               ("building_set_to_building_junctions", "building_set_to_building_junctions_tables", "building_chain", p),
               ("cai_construction_system_building_values", "cai_construction_system_building_values_tables",
                "building_chain", p),
               ("building_short_description_texts", "building_short_description_texts_tables", "key", p),
               ("building_flavour_texts", "building_flavour_texts_tables", "key", p)]


# Événements de lieux du lore (lot 22, 23.09.2026 ; saison_lieux.lua) : dilemmes et incidents lancés par script
# (create_dilemma_builder / create_incident_builder, comme les convois de CA), paquets d'effets remplis par script.
# Conception sourcée (Knights of the Grail p. 16, 55, 59-60) : scratchpad\lieux-evenements\propositions.md.
LIEUX_DILEMMES = {"saison_lieux_rives_introuvables": "errant_war", "saison_lieux_silence_ile": "wh2_sea_encounters_2"}
LIEUX_INCIDENTS = {"saison_lieux_brumes_noires": "generic", "saison_lieux_rejeton_gouffre": "sea_monster_attack",
                   # compléments sourcés (18 h 55) : brume des lacs sacrés (WD 300, BRT5 p. 81) ; le Gouffre arrête les
                   # razzias des Orques du Massif (Knights of the Grail p. 55)
                   "saison_lieux_brume_blanche": "generic", "saison_lieux_gouffre_barre": "generic"}
LIEUX_PAQUETS = {  # clé -> (modèle de CA, cible, icône)
    "saison_lieux_rives_fouille": ("wh3_dlc23_dilemma_chd_convoy_offence", "force", "campaign_movement.png"),
    "saison_lieux_rives_songe": ("wh3_dlc23_dilemma_chd_convoy_offence", "force", "campaign_movement.png"),
    "saison_lieux_ile_calme": ("wh3_main_payload_stolen_loot", "faction", "public_order.png"),
    "saison_lieux_brumes_noires": ("wh3_dlc23_dilemma_chd_convoy_attrition", "force", "attrition.png"),
    "saison_lieux_rejeton_gouffre": ("wh3_dlc23_dilemma_chd_convoy_attrition", "force", "attrition.png"),
    "saison_lieux_brume_blanche": ("wh3_dlc23_dilemma_chd_convoy_offence", "force", "campaign_movement.png"),
    "saison_lieux_gouffre_barre": ("wh3_dlc23_dilemma_chd_convoy_offence", "force", "campaign_movement.png"),
}


def lot_etape22():
    """Lot 22 : dilemmas, cdir_events_dilemma_choice_details, cdir_events_dilemma_option_junctions, incidents,
    cdir_events_incident_option_junctions, effect_bundles (tables neuves pour nous : essai de démarrage, erreur 107).
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    noms = ("dilemmas", "cdir_events_dilemma_choice_details", "cdir_events_dilemma_option_junctions", "incidents",
            "cdir_events_incident_option_junctions", "effect_bundles")
    t = {n: TableKit(n) for n in noms}
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))

    def en(cle):
        v = (nos.get(cle) or {}).get("en")
        if not v:
            raise SystemExit(f"lot 22 : texte {cle} absent de textes_gameplay.json")
        return escape(v)

    m_dil = "wh3_dlc23_dilemma_chd_convoy_offence_or_defence"
    td, tc, to = t["dilemmas"], t["cdir_events_dilemma_choice_details"], t["cdir_events_dilemma_option_junctions"]
    ti, tio, tb = t["incidents"], t["cdir_events_incident_option_junctions"], t["effect_bundles"]
    pris_o = set(to.cles) | {to.valeurs(c).get("id") for _, c in to.lignes}
    pris_io = set(tio.cles) | {tio.valeurs(c).get("id") for _, c in tio.lignes}
    for cle, image in LIEUX_DILEMMES.items():
        td.ajouter_sur_modele(m_dil, {"key": cle, "localised_title": en("dilemmas_localised_title_" + cle),
                                      "localised_description": en("dilemmas_localised_description_" + cle),
                                      "ui_image": image, "override_icon": ""})
        for choix in ("FIRST", "SECOND"):
            tc.ajouter_sur_modele(m_dil + choix, {
                "dilemma_key": cle, "choice_key": choix,
                "localised_choice_label": en("cdir_events_dilemma_choice_details_localised_choice_label_" + cle + choix),
                "localised_choice_title": en("cdir_events_dilemma_choice_details_localised_choice_title_" + cle + choix)})
        for modele in ("1463397395", "188352853"):
            deja = [k for k, c in to.lignes if to.valeurs(c).get("dilemma_key") == cle
                    and to.valeurs(c).get("option_key") == to.valeurs(dict(to.lignes)[modele]).get("option_key")]
            if not deja:
                ident = ident_numerique(f"lieux:{cle}:{modele}", pris_o)
                pris_o.add(ident)
                to.ajouter_sur_modele(modele, {"id": ident, "dilemma_key": cle})
    for cle, image in LIEUX_INCIDENTS.items():
        ti.ajouter_sur_modele("wh3_main_minor_cult_sartosan_vault", {
            "key": cle, "localised_title": en("incidents_localised_title_" + cle),
            "localised_description": en("incidents_localised_description_" + cle), "ui_image": image})
        for modele in ("878438706", "1602157576"):
            deja = [k for k, c in tio.lignes if tio.valeurs(c).get("incident_key") == cle
                    and tio.valeurs(c).get("option_key") == tio.valeurs(dict(tio.lignes)[modele]).get("option_key")]
            if not deja:
                ident = ident_numerique(f"lieux:{cle}:{modele}", pris_io)
                pris_io.add(ident)
                tio.ajouter_sur_modele(modele, {"id": ident, "incident_key": cle})
    for cle, (modele, cible, icone) in LIEUX_PAQUETS.items():
        tb.ajouter_sur_modele(modele, {"key": cle, "localised_title": en("effect_bundles_localised_title_" + cle),
                                       "localised_description": en("effect_bundles_localised_description_" + cle),
                                       "ui_icon": icone, "bundle_target": cible})
    p = "saison_lieux_"
    return t, [("dilemmas", "dilemmas_tables", "key", p),
               ("cdir_events_dilemma_choice_details", "cdir_events_dilemma_choice_details_tables", "dilemma_key", p),
               ("cdir_events_dilemma_option_junctions", "cdir_events_dilemma_option_junctions_tables", "dilemma_key", p),
               ("incidents", "incidents_tables", "key", p),
               ("cdir_events_incident_option_junctions", "cdir_events_incident_option_junctions_tables", "incident_key", p),
               ("effect_bundles", "effect_bundles_tables", "key", p)]


def lot_etape23():
    """Lot 23 (23.09.2026, 20 h) : plantage de Durthu joué au tour 6 (Warhammer3.exe+0x272AE00, fil principal, fin de
    tour, juste après les premiers raids de l'histoire) : l'infobulle des clairières (tooltip_wood_elf_glade) parcourt le
    groupe de forêt de CA wh2_dlc16_forest_region_group_main_1, où le lot 1 avait AJOUTÉ nos régions (le Chêne et sa
    lisière) à côté de celles des Empires ; elle résout wh3_main_combi_region_the_oak_of_ages, absente de notre carte, en
    objet NUL (vidage : chaînes « wh3_main_combi_region_the_oak_of_ages » et « wh_dlc05_parravon_montlac » dans l'objet
    de l'infobulle). Règle de l'erreur 110 : un groupe à nous. Retire nos 5 lignes du groupe de CA, crée
    GROUPE_FORET_ATHEL_LOREN et y met le Chêne et sa lisière ; saison_foret.lua le cite. NE PAS rejouer le lot 1 (il
    remettrait des lignes retirées depuis : citations, liens de la ressource de CA). Rend ({table: TableKit}, [entrées])."""
    rg, rj = TableKit("region_groups"), TableKit("regions_to_region_groups_junctions")
    rg.ajouter_sur_modele(rg.modele(group_key="wh3_main_combi_province_talsyn"), {"group_key": GROUPE_FORET_ATHEL_LOREN})
    for k, corps in list(rj.lignes):
        v = rj.valeurs(corps)
        if v.get("region_group") == "wh2_dlc16_forest_region_group_main_1" and v.get("region", "").startswith("wh_dlc05_"):
            rj.retirer(k)
    modele_j = rj.modele(region_group="wh3_main_combi_province_talsyn")
    for r in [CHENE] + LISIERE:
        rj.ajouter_sur_modele(modele_j, {"region_group": GROUPE_FORET_ATHEL_LOREN, "region": r, "order": "0"})
    # entrées du pack : celles du lot 1 (region_groups, préfixe wh_dlc05_ ; regions_to_region_groups_junctions, région
    # wh_dlc05_) couvrent déjà ces lignes
    return {"region_groups": rg, "regions_to_region_groups_junctions": rj}, [
        ("region_groups", "region_groups_tables", "group_key", "wh_dlc05_"),
        ("regions_to_region_groups_junctions", "regions_to_region_groups_junctions_tables", "region", "wh_dlc05_")]


def lot_etape24():
    """Lot 24 (23.09.2026, 20 h 10) : erreur 154 (jamais une de nos régions dans un groupe de CA qui garde des régions
    d'une autre carte), groupes du lot 1 revus un par un (qui les lit : tables de l'IA et de la diplomatie de CA) :
    - wh3_main_transfer_settlement_excluded_regions : lu seulement par la manipulation diplomatique de Tzeentch
      (campaign_group_diplomatic_manipulation_category_junctions -> diplomatic_manipulation_excluded_objectives) ; aucune
      faction de Tzeentch sur notre carte : notre Chêne en sort, sans perte (et le plantage de rendu survient aux
      transferts de régions) ;
    - wh3_wood_elf_forests : gardé ; l'IA elfe l'interroge par UNE variable (cai_query_variable_set_junctions, clé =
      jeu + variable : un seul groupe possible) ; un groupe à nous lui ferait perdre Athel Loren ;
    - cai_region_hint_area_athel_loren / _bretonnia / _dwarf_empire / cai_region_hint_sub_area_western_mountains :
      gardés ; lus par cai_personality_region_group_policy_junctions à chaque tour depuis le 21.09 sans plantage, aucune
      interface ni aucun transfert ne les parcourt. Rend ({table: TableKit}, [entrées])."""
    rj = TableKit("regions_to_region_groups_junctions")
    for k, corps in list(rj.lignes):
        v = rj.valeurs(corps)
        if v.get("region_group") == "wh3_main_transfer_settlement_excluded_regions" and v.get("region", "").startswith("wh_dlc05_"):
            rj.retirer(k)
    return {"regions_to_region_groups_junctions": rj}, [
        ("regions_to_region_groups_junctions", "regions_to_region_groups_junctions_tables", "region", "wh_dlc05_")]


# Chefs de faction de départ dont le sous-type n'a JAMAIS d'unité de général imposée chez CA (start_pos_characters des
# Empires et des Royaumes du Chaos : override_general_unit vide pour tous les glade_lord, glade_lord_fem et
# orc_warboss) ; les nôtres la tenaient de WH1. ID -> faction (pour le journal).
CHEFS_SANS_UNITE_IMPOSEE = {
    "2140783834": "wh_dlc05_wef_anmyr", "2140783853": "wh_dlc05_wef_arranoc", "2140783858": "wh_dlc05_wef_atylwyth",
    "2140783864": "wh_dlc05_wef_cavaroc", "2140783876": "wh_dlc05_wef_fyr_darric", "2140783882": "wh_dlc05_wef_modryn",
    "2140783890": "wh_dlc05_wef_torgovann", "2140783900": "wh_dlc05_wef_wydrioth", "2140783907": "wh_dlc05_wef_tirsyth",
    "2140783830": "wh_main_grn_skullsmasherz",
}


def lot_etape25():
    """Lot 25 (23.09.2026, 22 h 10) : plantage du tour 11 (Warhammer3.exe+0x2532B26, 5 fois sur 5 dans les parties
    d'Orion). Chaîne établie par les essais à drapeau de saison_essai_tour11.lua : au tour 7, Arlas (chef de Modryn,
    glade_lord_fem immortel) perd contre une armée de la harde ; il n'est pas blessé en gardant son cqi comme un
    immortel ordinaire, il est REMPLACÉ par un nouveau personnage blessé qui n'est plus chef, et Modryn reste sans chef
    (« CHEF DE MODRYN : aucun », « CQI 14 : introuvable ») ; au retour de ce blessé, au début du tour de Modryn au tour
    11, le jeu plante. Sans ce retour (essai E : le blessé meurt), le tour 11 passe. Seule différence de structure entre
    la ligne d'Arlas et celle de Laurelorn (chef glade_lord_fem immortel de CA) : override_general_unit
    (wh_dlc05_wef_cha_female_glade_lord_0, héritée de WH1). Elle est vidée, comme chez CA, pour les 10 chefs dont le
    sous-type n'en a jamais chez CA. Les légendaires et les seigneurs bretonniens et nains gardent la leur (CA aussi).
    Table du STARTPOS : synchroniser zz_startpos_db.pack puis régénérer. Rend ({table: TableKit}, [entrées])."""
    tp = TableKit("start_pos_characters")
    for ident in CHEFS_SANS_UNITE_IMPOSEE:
        lignes = tp.ou(ID=ident)
        if len(lignes) != 1:
            raise SystemExit(f"lot 25 : start_pos_characters ID {ident} : {len(lignes)} ligne(s)")
        tp.modifier(lignes[0][0], {"override_general_unit": ""})
    return {"start_pos_characters": tp}, [
        ("start_pos_characters", "start_pos_characters_tables", "ID", "(startpos)")]


# Nos factions elfes venues de WH1, absentes des Empires : sans ligne « faction_leader » à elles dans
# ministerial_positions_culture_details (les Elfes sylvains n'ont pas de ligne pour la culture, CA en met une par faction).
FACTIONS_ELFES_SANS_CHEF = ["wh_dlc05_wef_anmyr", "wh_dlc05_wef_arranoc", "wh_dlc05_wef_atylwyth", "wh_dlc05_wef_cavaroc",
                            "wh_dlc05_wef_fyr_darric", "wh_dlc05_wef_modryn", "wh_dlc05_wef_tirsyth"]


def lot_etape26():
    """Lot 26 (23.09.2026, 23 h 06) : CAUSE DE FOND du plantage du tour 11 (Warhammer3.exe+0x2532B26, 6 fois sur 6).
    Le poste de chef de faction est défini, dans ministerial_positions_culture_details, pour la CULTURE chez 25 cultures
    (Bretonnie, Hommes-bêtes, Nains, Peaux-vertes, Comtes vampires...), mais faction par faction chez les Elfes sylvains :
    CA a une ligne « faction_leader » pour chacune de ses 18 factions elfes (Wydrioth, Torgovann, Laurelorn, rebelles,
    qb...). Nos 7 factions elfes de WH1 n'en avaient pas : quand leur chef tombe (Arlas de Modryn au tour 7, battu par
    la harde), la faction ne peut pas en nommer un autre (journal : « CHEF DE MODRYN : aucun », et Cavaroc), un blessé
    non chef le remplace, et à son retour le jeu plante. 7 lignes sur le modèle de celle de Wydrioth (textes
    « placeholder » comme CA, coordonnées 0, unique_id neufs). Table de base lue sans doute à la génération du startpos :
    régénérer. Filet en garde : saison_filet_blesses.lua. Rend ({table: TableKit}, [entrées])."""
    t = TableKit("ministerial_positions_culture_details")
    modele = t.modele(ministerial_position_key="faction_leader", faction_key="wh_dlc05_wef_wydrioth")
    pris = set(TableKit.valeurs(c)["unique_id"] for _, c in t.lignes)
    for f in FACTIONS_ELFES_SANS_CHEF:
        if t.ou(ministerial_position_key="faction_leader", faction_key=f):
            continue
        uid = ident_numerique("chef:" + f, pris)
        pris.add(uid)
        t.ajouter_sur_modele(modele, {"faction_key": f, "unique_id": uid})
    return {"ministerial_positions_culture_details": t}, [
        ("ministerial_positions_culture_details", "ministerial_positions_culture_details_tables", "faction_key",
         FACTIONS_ELFES_SANS_CHEF)]


# Portée de déplacement des armées (demande de Charles, 24.09.2026, 00 h : « toute pâle » ; option A de la session du
# rendu) : variables d'affichage surchargées pour notre campagne seulement, comme CA le fait pour display_vortex_*
# (campaigns_campaign_variables_junctions, clé = variable + campagne + difficulté vide). Valeurs globales de
# campaign_variables : périmètre 0,3, intérieur 0,02.
PORTEE_ARMEES = {"display_movement_extents_perimeter_alpha": "0.5",
                 "display_movement_extents_interior_alpha": "0.05"}


def lot_etape27():
    """Lot 27 (24.09.2026, 00 h 04) : portée des armées plus lisible sur notre carte (PORTEE_ARMEES). L'entrée du pack
    est celle du lot 1 (campaigns_campaign_variables_junctions, campaign_name = notre campagne). Rend ({table: TableKit},
    [entrées])."""
    t = TableKit("campaigns_campaign_variables_junctions")
    modele = t.modele(variable_key="display_vortex_enabled", campaign_name="wh3_main_combi")
    for variable, valeur in PORTEE_ARMEES.items():
        cle = variable + CAMPAGNE
        if cle in t.cles:
            t.modifier(cle, {"value": valeur})
        else:
            t.ajouter_sur_modele(modele, {"campaign_name": CAMPAGNE, "variable_key": variable, "value": valeur})
    return {"campaigns_campaign_variables_junctions": t}, [
        ("campaigns_campaign_variables_junctions", "campaigns_campaign_variables_junctions_tables", "campaign_name",
         CAMPAGNE)]


# Caméra de la carte stratégique (proposition de la session du rendu, 24.09.2026, 04 h ; « parchemin petit dans un grand
# fond », carré du brouillard fin autour de la caméra) : les valeurs globales de campaign_variables sont faites pour les
# Empires (961 u de large ; hauteur maximale 300, début du fondu du parchemin 50, parchemin seul 175) ; notre carte fait
# 266 u. Même mécanisme que PORTEE_ARMEES ; aucun précédent de CA pour les variables camera_* : si le jeu ne les lit pas
# par campagne, rien ne change. Réglage à l'œil par Charles.
CAMERA_CARTE = {"camera_warhammer_maximum_height": "150",
                "camera_warhammer_parchment_blend_start": "35",
                "camera_warhammer_parchment_only_threshold": "90"}


def lot_etape29():
    """Lot 29 (24.09.2026, 04 h 10) : caméra de la carte stratégique à l'échelle de notre carte (CAMERA_CARTE). Entrée du
    pack : celle du lot 1 (campaigns_campaign_variables_junctions, campaign_name = notre campagne). Rend ({table:
    TableKit}, [entrées])."""
    t = TableKit("campaigns_campaign_variables_junctions")
    modele = t.modele(variable_key="display_vortex_enabled", campaign_name="wh3_main_combi")
    for variable, valeur in CAMERA_CARTE.items():
        cle = variable + CAMPAGNE
        if cle in t.cles:
            t.modifier(cle, {"value": valeur})
        else:
            t.ajouter_sur_modele(modele, {"campaign_name": CAMPAGNE, "variable_key": variable, "value": valeur})
    return {"campaigns_campaign_variables_junctions": t}, [
        ("campaigns_campaign_variables_junctions", "campaigns_campaign_variables_junctions_tables", "campaign_name",
         CAMPAGNE)]


def lot_etape30():
    """Lot 30 (24.09.2026, 17 h 30, après la fusion de nos lignes dans le kit 9.0, restaurer_lignes_kit.py) : la 9.0
    ajoute à pooled_resource_factor_junctions une colonne obligatoire sort_order (0 sur les 11 facteurs de CA de
    wef_worldroots_athel_loren). Nos 11 facteurs (lot 7, copies de ceux-là) sont refaits sur le corps 9.0 de leur modèle
    de CA, clé et identifiant inchangés. Rend ({table: TableKit}, [entrées])."""
    t = TableKit("pooled_resource_factor_junctions")
    for k, corps in t.ou(resource=RESSOURCE):
        if re.search(r"<sort_order[ />]", corps):
            continue
        uid = t.valeurs(corps)["unique_id"]
        modeles = t.ou(unique_id=uid.replace(RESSOURCE, RESSOURCE_CA, 1), resource=RESSOURCE_CA)
        if len(modeles) != 1:
            raise SystemExit(f"pooled_resource_factor_junctions : modèle de CA de {uid} introuvable")
        neuf = t.avec(t.avec(modeles[0][1], "resource", RESSOURCE), "unique_id", uid)
        t.retirer(k)
        t.neuves.append(f'<{t.nom} record_uuid="{{{uuid.uuid4()}}}" record_timestamp="{int(time.time() * 1000)}" '
                        f'record_key="{k}">{neuf}</{t.nom}>\n')
    return {"pooled_resource_factor_junctions": t}, [
        ("pooled_resource_factor_junctions", "pooled_resource_factor_junctions_tables", "resource", [RESSOURCE])]


# Refonte des Comtes vampires de la 9.0 (audit 05-journal\2026-09-24-vampires-9.0\audit-systemes-vampires-9.0.md, § 2 et
# § 3) : deux factions de support des Empires, sans personnage ni région, et les héros uniques des vampires.
FACTIONS_SUPPORT_VAMPIRES = ["wh3_main_vmp_vampire_lairs",		# propriétaire de tous les repaires (indispensable)
                             "wh3_main_vmp_remnants"]			# reçoit les factions confédérées par rituel de lignée
HEROS_VAMPIRES_9_0 = ["wh3_dlc29_vmp_krell", "wh3_dlc29_vmp_dieter_helsnicht", "wh3_dlc29_vmp_walach_harkon"]


def lot_etape31():
    """Lot 31 (24.09.2026, 18 h 20) : les vampires de la 9.0 sur notre carte. start_pos_factions : les deux factions de
    support des Empires (lignes de CA sous notre campagne, nos identifiants), comme les factions de bataille du lot 13 ;
    campaign_to_agent_subtypes : Krell, Dieter Helsnicht et Walach Harkon (héros uniques que les scripts vampires font
    apparaître), comme aux Empires. Neferata non (absente de notre carte). start_pos_factions : table du STARTPOS
    (synchronisation par la construction, puis régénération). Rend ({table: TableKit}, [entrées])."""
    tf, tc = TableKit("start_pos_factions"), TableKit("campaign_to_agent_subtypes")
    pris_f = set(tf.cles) | {tf.valeurs(c).get("ID") for _, c in tf.lignes}
    deja_f = {tf.valeurs(c).get("faction"): tf.valeurs(c).get("ID") for _, c in tf.lignes
              if tf.valeurs(c).get("campaign") == CAMPAGNE}
    ids = []
    for k, corps in list(tf.lignes):
        v = tf.valeurs(corps)
        if v.get("campaign") != IE or v.get("faction") not in FACTIONS_SUPPORT_VAMPIRES:
            continue
        if v["faction"] in deja_f:
            ids.append(deja_f[v["faction"]])
            continue
        ident = ident_numerique(f"faction_support_vampires:{v['faction']}", pris_f)
        pris_f.add(ident)
        for col, val in (("ID", ident), ("campaign", CAMPAGNE)):
            corps = tf.avec(corps, col, val)
        tf.ajouter(ident, corps)
        ids.append(ident)
    modele = tc.ou(agent_subtype="wh_dlc05_wef_orion", campaign_type=CAMPAGNE)[0][0]
    for st in HEROS_VAMPIRES_9_0:
        tc.ajouter_sur_modele(modele, {"agent_subtype": st})
    return {"start_pos_factions": tf, "campaign_to_agent_subtypes": tc}, [
        ("start_pos_factions", "start_pos_factions_tables", "ID", ids),
        ("campaign_to_agent_subtypes", "campaign_to_agent_subtypes_tables", "campaign_type", CAMPAGNE)]


INCIDENT_GALAND = "saison_duc_galand"


def lot_etape32():
    """Lot 32 (24.09.2026, 21 h 30) : le tombeau de Galand (saison_duc.lua) passe du message de script à un incident
    illustré, demande de Charles. Incident sans cible ni charge (les dégâts restent au script), sur le modèle de
    wh3_main_incident_wef_deeproots_available (GEN_TARGET_NONE + VAR_CHANCE 100) ; image : ILLUSTRATIONS si l'illustration
    est intégrée, sinon « faction » comme le modèle. Tables neuves dans un pack joué : essai de démarrage (erreur 107).
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    ti, tio = TableKit("incidents"), TableKit("cdir_events_incident_option_junctions")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    cle = INCIDENT_GALAND
    ti.ajouter_sur_modele("wh3_main_incident_wef_deeproots_available", {
        "key": cle, "localised_title": escape(nos["incidents_localised_title_" + cle]["en"]),
        "localised_description": escape(nos["incidents_localised_description_" + cle]["en"]),
        "ui_image": ILLUSTRATIONS.get(cle, "faction"), "override_icon": "event_region_negative.png"})
    # l'illustration arrive après l'incident (24.09, 22 h 40) : la ligne déjà écrite reçoit son image
    if cle in ti.cles and ti.valeurs(dict(ti.lignes)[cle]).get("ui_image") != ILLUSTRATIONS.get(cle, "faction"):
        ti.modifier(cle, {"ui_image": ILLUSTRATIONS.get(cle, "faction")})
    pris = set(tio.cles) | {tio.valeurs(c).get("id") for _, c in tio.lignes}
    for modele in ("1941431223", "1979253375"):  # GEN_TARGET_NONE, VAR_CHANCE 100
        option = tio.valeurs(dict(tio.lignes)[modele]).get("option_key")
        if not [k for k, c in tio.lignes if tio.valeurs(c).get("incident_key") == cle
                and tio.valeurs(c).get("option_key") == option]:
            ident = ident_numerique(f"galand:{cle}:{modele}", pris)
            pris.add(ident)
            tio.ajouter_sur_modele(modele, {"id": ident, "incident_key": cle})
    return {"incidents": ti, "cdir_events_incident_option_junctions": tio}, [
        ("incidents", "incidents_tables", "key", "saison_duc_"),
        ("cdir_events_incident_option_junctions", "cdir_events_incident_option_junctions_tables", "incident_key",
         "saison_duc_")]


HEROS_VAMPIRES_MOUSILLON = HEROS_VAMPIRES_9_0      # Krell, Dieter Helsnicht, Walach Harkon


def lot_etape33():
    """Lot 33 (25.09.2026, 01 h 20 ; audit du Duc écarlate face à la 9.0) : les trois héros uniques des vampires 9.0
    (Krell, Dieter Helsnicht, Walach Harkon, déjà déclarés pour notre campagne au lot 31) permis à Mousillon, comme aux
    factions vampires majeures des Empires (lignes de CA pour wh_main_vmp_vampire_counts, recopiées sous la faction du
    Duc). Sans elles, les techniques qui les donnent ne donnaient rien au Duc joué ; Walach est un Dragon de sang, comme
    lui. Lignes neuves (clé faction + agent + sous-type), aucune ligne de CA modifiée. Rend ({table: TableKit}, [entrées])."""
    t = TableKit("faction_agent_permitted_subtypes")
    cles = []
    for st in HEROS_VAMPIRES_MOUSILLON:
        modeles = t.ou(faction="wh_main_vmp_vampire_counts", subtype=st)
        if not modeles:
            raise SystemExit(f"lot 33 : pas de ligne de CA pour {st} chez wh_main_vmp_vampire_counts")
        k, corps = modeles[0]
        # l'agent de la ligne de CA (champion pour Krell et Walach, wizard pour Dieter Helsnicht)
        cle = "wh_main_vmp_mousillon" + t.valeurs(corps)["agent"] + st
        cles.append(cle)
        if cle not in t.cles:
            t.ajouter(cle, t.avec(corps, "faction", "wh_main_vmp_mousillon"))
    return {"faction_agent_permitted_subtypes": t}, [
        ("faction_agent_permitted_subtypes", "faction_agent_permitted_subtypes_tables", "(clés)", cles)]


# Mécaniques propres au Duc écarlate (lot 34, 25.09.2026 ; choix de Charles : A « le duché perdu » et C « la faveur
# d'Abhorash », 05-journal\2026-09-24-vampires-9.0\duc-ecarlate-9.0-audit-et-propositions.md). Paquets d'effets à nos
# clés, nom, description et icône seulement ; leurs effets (effets de CA) sont posés par saison_duc.lua
# (cm:create_new_custom_effect_bundle), comme les paquets du lot 22. clé -> (modèle de CA, cible, icône de CA)
# Icônes : celles de CA proposées par l'étude du 25.09.2026 (validée par Charles), dont blood_kiss, public_order_happy,
# edict_coc_exploit_vassals, vow_questing_negative ; les Dragons de sang gardent la leur.
PAQUETS_DU_DUC = {
    "saison_duc_depossede": ("wh3_main_payload_stolen_loot", "faction", "vow_questing_negative.png"),
    "saison_duc_reconquete": ("wh3_main_payload_stolen_loot", "faction", "corruption_vampiric.png"),
    "saison_duc_restaure": ("wh3_main_payload_stolen_loot", "faction", "nemesis_crown_sealed.png"),
    "saison_duc_faveur_abhorash": ("wh_dlc07_blessing_of_the_lady", "force", "bloodline_blood_dragon.png"),
    # mécanique B (l'impôt du sang et les vassaux du sang, 25.09.2026)
    "saison_duc_impot_leve": ("wh2_dlc10_power_of_nature", "region", "blood_kiss.png"),
    "saison_duc_vilains_epargnes": ("wh2_dlc10_power_of_nature", "region", "public_order_happy.png"),
    "saison_duc_vassaux_du_sang": ("wh3_main_payload_stolen_loot", "faction", "edict_coc_exploit_vassals.png"),
}

# Dilemmes du Duc écarlate (lot 35, mécanique B) : clé -> image de CA (dossier de culture vampire). Comme ceux du lot 22 :
# lancés par script (create_dilemma_builder), charges posées par le script.
DILEMMES_DU_DUC = {"saison_duc_impot_du_sang": "generic", "saison_duc_serment_du_sang": "generic"}


def lot_etape35():
    """Lot 35 (25.09.2026) : dilemmas, cdir_events_dilemma_choice_details, cdir_events_dilemma_option_junctions du Duc
    écarlate (l'impôt du sang, le serment du sang), recette du lot 22. Tables neuves dans un pack joué : essai de
    démarrage (erreur 107). Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    noms = ("dilemmas", "cdir_events_dilemma_choice_details", "cdir_events_dilemma_option_junctions")
    t = {n: TableKit(n) for n in noms}
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))

    def en(cle):
        v = (nos.get(cle) or {}).get("en")
        if not v:
            raise SystemExit(f"lot 35 : texte {cle} absent de textes_gameplay.json")
        return escape(v)

    m_dil = "wh3_dlc23_dilemma_chd_convoy_offence_or_defence"
    td, tc, to = t["dilemmas"], t["cdir_events_dilemma_choice_details"], t["cdir_events_dilemma_option_junctions"]
    pris_o = set(to.cles) | {to.valeurs(c).get("id") for _, c in to.lignes}
    for cle, image in DILEMMES_DU_DUC.items():
        td.ajouter_sur_modele(m_dil, {"key": cle, "localised_title": en("dilemmas_localised_title_" + cle),
                                      "localised_description": en("dilemmas_localised_description_" + cle),
                                      "ui_image": ILLUSTRATIONS.get(cle, image), "override_icon": ""})
        for choix in ("FIRST", "SECOND"):
            tc.ajouter_sur_modele(m_dil + choix, {
                "dilemma_key": cle, "choice_key": choix,
                "localised_choice_label": en("cdir_events_dilemma_choice_details_localised_choice_label_" + cle + choix),
                "localised_choice_title": en("cdir_events_dilemma_choice_details_localised_choice_title_" + cle + choix)})
        for modele in ("1463397395", "188352853"):
            option = to.valeurs(dict(to.lignes)[modele]).get("option_key")
            if not [k for k, c in to.lignes if to.valeurs(c).get("dilemma_key") == cle
                    and to.valeurs(c).get("option_key") == option]:
                ident = ident_numerique(f"duc:{cle}:{modele}", pris_o)
                pris_o.add(ident)
                to.ajouter_sur_modele(modele, {"id": ident, "dilemma_key": cle})
    p = "saison_duc_"
    return t, [("dilemmas", "dilemmas_tables", "key", p),
               ("cdir_events_dilemma_choice_details", "cdir_events_dilemma_choice_details_tables", "dilemma_key", p),
               ("cdir_events_dilemma_option_junctions", "cdir_events_dilemma_option_junctions_tables", "dilemma_key", p)]


def lot_etape34():
    """Lot 34 : effect_bundles (paquets du Duc écarlate ; table neuve dans un pack joué : essai de démarrage, erreur
    107). Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    tb = TableKit("effect_bundles")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))

    def en(cle):
        v = (nos.get(cle) or {}).get("en")
        if not v:
            raise SystemExit(f"lot 34 : texte {cle} absent de textes_gameplay.json")
        return escape(v)

    for cle, (modele, cible, icone) in PAQUETS_DU_DUC.items():
        tb.ajouter_sur_modele(modele, {"key": cle, "localised_title": en("effect_bundles_localised_title_" + cle),
                                       "localised_description": en("effect_bundles_localised_description_" + cle),
                                       "ui_icon": icone, "bundle_target": cible})
        # ligne déjà écrite : l'icône suit PAQUETS_DU_DUC (changement du 25.09.2026)
        if cle in tb.cles and tb.valeurs(dict(tb.lignes)[cle]).get("ui_icon") != icone:
            tb.modifier(cle, {"ui_icon": icone})
    return {"effect_bundles": tb}, [("effect_bundles", "effect_bundles_tables", "key", "saison_duc_")]


# Incidents du Duc écarlate (lot 37, 25.09.2026) : les messages de script d'avant montraient des images de CA sans rapport
# (l'index 1803 : celle des Hommes-bêtes ; 710 et 711 : la Dame du Lac). clé -> icône de CA (positive ou négative).
INCIDENTS_DU_DUC = {
    "saison_duc_reprise": "event_commander_activity_positive.png",
    "saison_duc_restaure": "event_commander_activity_positive.png",
    "saison_duc_perte": "event_region_negative.png",
    "saison_duc_faveur_gagnee": "event_commander_activity_positive.png",
    "saison_duc_faveur_degre3": "event_commander_activity_positive.png",
    "saison_duc_faveur_perdue": "event_region_negative.png",
    "saison_duc_traque": "event_region_negative.png",
    "saison_duc_vassal_rompt": "event_region_negative.png",
}


def lot_etape37():
    """Lot 37 (25.09.2026 ; étude du Duc, validée par Charles) : les 8 annonces du Duc écarlate en incidents à nos clés,
    illustrés (ILLUSTRATIONS, sinon l'image de culture de CA « generic »), recette du lot 32 (incident sans cible ni
    charge : les effets restent au script). Tables déjà dans le pack (lot 32). Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    ti, tio = TableKit("incidents"), TableKit("cdir_events_incident_option_junctions")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    pris = set(tio.cles) | {tio.valeurs(c).get("id") for _, c in tio.lignes}
    deja = dict(ti.lignes)		# lignes déjà dans le kit (une ligne neuve n'y est pas encore)
    for cle, icone in INCIDENTS_DU_DUC.items():
        image = ILLUSTRATIONS.get(cle, "generic")
        ti.ajouter_sur_modele("wh3_main_incident_wef_deeproots_available", {
            "key": cle, "localised_title": escape(nos["incidents_localised_title_" + cle]["en"]),
            "localised_description": escape(nos["incidents_localised_description_" + cle]["en"]),
            "ui_image": image, "override_icon": icone})
        if cle in deja and ti.valeurs(deja[cle]).get("ui_image") != image:
            ti.modifier(cle, {"ui_image": image})
        for modele in ("1941431223", "1979253375"):  # GEN_TARGET_NONE, VAR_CHANCE 100
            option = tio.valeurs(dict(tio.lignes)[modele]).get("option_key")
            if not [k for k, c in tio.lignes if tio.valeurs(c).get("incident_key") == cle
                    and tio.valeurs(c).get("option_key") == option]:
                ident = ident_numerique(f"duc:{cle}:{modele}", pris)
                pris.add(ident)
                tio.ajouter_sur_modele(modele, {"id": ident, "incident_key": cle})
    return {"incidents": ti, "cdir_events_incident_option_junctions": tio}, [
        ("incidents", "incidents_tables", "key", "saison_duc_"),
        ("cdir_events_incident_option_junctions", "cdir_events_incident_option_junctions_tables", "incident_key",
         "saison_duc_")]


def lot_etape36():
    """Lot 36 (25.09.2026 ; audit de l'avant-campagne, S3 ; décision de Charles, 01 h 55 : « les elfes sylvains, vu que
    c'est leur campagne à la base ») : Orion « recommandé pour une première campagne » (difficulty = easy, comme Tyrion ou
    Balthasar chez CA ; icône icon_recommended). Notre fiche (frontend_faction_leaders, préfixe
    wh_dlc05_political_party_mini_, déjà dans le pack). Lue par la génération du startpos : startpos et essai de
    démarrage ensuite. Rend ({table: TableKit}, [entrées])."""
    t = TableKit("frontend_faction_leaders")
    cle = "wh_dlc05_political_party_mini_wood_elves_ruler"
    if t.valeurs(dict(t.lignes)[cle]).get("difficulty") != "easy":
        t.modifier(cle, {"difficulty": "easy"})
    return {"frontend_faction_leaders": t}, [
        ("frontend_faction_leaders", "frontend_faction_leaders_tables", "key", "wh_dlc05_political_party_mini_")]


def lot_etape28():
    """Lot 28 (24.09.2026, 00 h 16) : les Sœurs du Crépuscule, 10e seigneure jouable (spec-soeurs-du-crepuscule.md) :
    leur sous-type déclaré pour notre campagne dans campaign_to_agent_subtypes, comme chaque seigneur légendaire des
    Empires (lot 13 pour Drycha, Kemmler et Grom). Entrée du pack : celle du lot 13 (campaign_type = notre campagne).
    Rend ({table: TableKit}, [entrées])."""
    tc = TableKit("campaign_to_agent_subtypes")
    modele = tc.ou(agent_subtype="wh_dlc05_wef_orion", campaign_type=CAMPAGNE)[0][0]
    if not tc.ou(agent_subtype="wh2_dlc16_wef_sisters_of_twilight", campaign_type=CAMPAGNE):
        tc.ajouter_sur_modele(modele, {"agent_subtype": "wh2_dlc16_wef_sisters_of_twilight"})
    return {"campaign_to_agent_subtypes": tc}, [
        ("campaign_to_agent_subtypes", "campaign_to_agent_subtypes_tables", "campaign_type", CAMPAGNE)]


def lot_etape38():
    """Lot 38 (25.09.2026 ; audit de cohérence, point 5) : le trait de faction de Grom à notre clé. Celui de CA
    (wh2_dlc15_lord_trait_grn_grom_the_paunch, posé par faction_starting_general_effects à son sous-type, toutes
    campagnes) s'intitule « Waaagh contre Ulthuan ! » et donne −80 avec les Hauts Elfes, absents de notre carte. Le nôtre :
    nom, description et icône (ligne faite sur celle de CA) ; ses effets, ceux de CA sans la diplomatie, sont posés par
    saison_grom.lua (paquet personnalisé, comme ceux du Duc) : pas de table de jonction. Table déjà dans le pack (lot 34),
    entrée TABLES_LOT38. Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    tb = TableKit("effect_bundles")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    cle = "saison_lord_trait_grom"
    tb.ajouter_sur_modele("wh2_dlc15_lord_trait_grn_grom_the_paunch", {
        "key": cle, "localised_title": escape(nos["effect_bundles_localised_title_" + cle]["en"]),
        "localised_description": escape(nos["effect_bundles_localised_description_" + cle]["en"])})
    return {"effect_bundles": tb}, [("effect_bundles", "effect_bundles_tables", "key", [cle])]


# Incidents de la forêt à nos clés (lot 39, 25.09.2026 ; audit de cohérence, points 10 et 11) : clé -> incident modèle
# de CA (image, icône et jonctions reprises ; textes à nous).
INCIDENTS_DE_LA_FORET = {
    "saison_racines_du_monde_ouvertes": "wh3_main_incident_wef_deeproots_available",
    "saison_ariel_arrive": "wh2_dlc16_incident_wef_ariel_arrives",
}


def lot_etape39():
    """Lot 39 (25.09.2026 ; audit de cohérence, points 10 et 11) : « Les Racines du monde s'ouvrent » (tour 10,
    saison_foret.lua) et « La Reine apparaît » (Ariel éveillée par le Chêne, mission_incidents de CA redirigés), à la
    place des incidents de CA dont le texte ne vaut pas sur notre carte. Chaque ligne est faite sur l'incident de CA, ses
    jonctions d'options recopiées sous des identifiants neufs. Tables déjà dans le pack (lot 32), entrée TABLES_LOT39.
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    ti, tio = TableKit("incidents"), TableKit("cdir_events_incident_option_junctions")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))
    pris = set(tio.cles) | {tio.valeurs(c).get("id") for _, c in tio.lignes}
    jonctions_ca = [(k, tio.valeurs(c)) for k, c in tio.lignes]
    for cle, modele in INCIDENTS_DE_LA_FORET.items():
        ti.ajouter_sur_modele(modele, {
            "key": cle, "localised_title": escape(nos["incidents_localised_title_" + cle]["en"]),
            "localised_description": escape(nos["incidents_localised_description_" + cle]["en"])})
        deja = {v.get("option_key") for _, v in jonctions_ca if v.get("incident_key") == cle}
        for k, v in jonctions_ca:
            if v.get("incident_key") == modele and v.get("option_key") not in deja:
                ident = ident_numerique(f"foret:{cle}:{k}", pris)
                pris.add(ident)
                tio.ajouter_sur_modele(k, {"id": ident, "incident_key": cle})
    cles = list(INCIDENTS_DE_LA_FORET)
    return {"incidents": ti, "cdir_events_incident_option_junctions": tio}, [
        ("incidents", "incidents_tables", "key", cles),
        ("cdir_events_incident_option_junctions", "cdir_events_incident_option_junctions_tables", "incident_key", cles)]


# Branche de technologies du Duc écarlate (lot 40, 25.09.2026 ; mécanique F choisie par Charles ; étude
# duc-9.0\technologies\rapport.md). Nœuds de l'arbre des vampires (vmp_mil) réservés à Mousillon ET à notre campagne,
# dans un onglet à nous (tier_offset 80) ; losange de 8 nœuds : racine, deux lignes de trois (chevaliers ; contre la
# Bretonnie), sommet qui exige les deux. Noms et descriptions : dossier de lore (textes_gameplay.json). Effets : clés et
# portées de CA (S = portée employée par CA en technique ; E = à vérifier en jeu) ; coûts en Sang : ceux des techniques de
# CA (wh3_main_vmp_unit_tech_cost_N). Chiffres : choix de conception, à régler en jeu.
# nom -> (tier, indent, points de recherche, coût en Sang (0 : aucun), icône de CA, parents, [(effet, valeur, portée)])
BRANCHE_DU_DUC = {
    "abhorash": (81, 4, 100, 0, "wh_main_vmp_blood", [],
                 [("wh3_main_effect_shyish_per_turn_tech", "25", "faction_to_faction_own_unseen")]),              # S
    "morzillo": (82, 3, 200, 200, "wh3_main_tech_vmp_units_knights_2", ["abhorash"],
                 [("wh_main_effect_force_stat_charge_bonus_black_knights_blood_knights", "10",
                   "faction_to_force_own_unseen")]),                                                                # S
    "bourse": (83, 3, 300, 300, "wh2_def_tech_bloodforged_platemail", ["morzillo"],
               [("wh2_dlc11_effect_force_stat_armour_black_knights_blood_knights", "10",
                 "faction_to_force_own_unseen")]),                                                                  # S
    "epee_du_nord": (84, 3, 300, 400, "wh3_main_tech_vmp_vampires_walach_harkon_1", ["bourse"],
                     [("wh3_unit_cap_vmp_cav_blood_knights", "1", "faction_to_faction_own_unseen")]),               # S
    "usurpateurs": (82, 5, 200, 200, "wh_dlc2_vamp_turn_knightly_orders", ["abhorash"],
                    [("wh_dlc03_effect_force_stat_leadership_vs_bretonnia", "8", "faction_to_force_own")]),         # S
    "ceren": (83, 5, 300, 300, "tech_dlc07_brt_chivalry_vampires_1", ["usurpateurs"],
              [("wh3_dlc27_effect_attribute_enable_charge_defence_vs_bretonnia", "1",
                "faction_to_force_own_unseen")]),                                                                   # S
    "impot": (84, 5, 300, 400, "wh_main_vmp_blood_is_power", ["ceren"],
              [("wh3_main_effect_shyish_per_turn_tech", "25", "faction_to_faction_own_unseen")]),                  # S
    "crac": (85, 4, 500, 600, "wh3_main_tech_vmp_vampires_red_duke_1", ["epee_du_nord", "impot"],
             [("wh3_dlc29_effect_attribute_enable_glorious_charge_black_knights_blood_knights", "1",
               "faction_to_force_own_unseen"),                                                                      # E
              ("wh3_unit_cap_vmp_cav_black_knights", "2", "faction_to_faction_own_unseen")]),                      # S
}
ONGLET_DU_DUC = "saison_duc_vmp_dragons_de_sang"
PREFIXE_TECH_DUC = "saison_duc_tech_"
# décalages de pixels par tier (schéma des nœuds de Neferata : 61 -> 80 px ... 65 -> 0 px)
DECALAGE_PX = {81: "80", 82: "60", 83: "40", 84: "20", 85: "0"}


def lot_etape40():
    """Lot 40 (25.09.2026 ; mécanique F) : la branche de technologies du Duc écarlate (BRANCHE_DU_DUC), faite sur les
    lignes de Neferata (wh3_dlc29_tech_nef_imentet_2, son lien depuis imentet_1, l'onglet vmp_neferata et sa jonction)
    et sur un effet de units_knights_2. Six tables NEUVES dans un pack joué : essai de démarrage obligatoire (erreur 107),
    avec le Duc (onglet visible) puis Kemmler (onglet absent : faction et campagne sur le nœud, jamais vu chez CA).
    Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    noms = ("technologies", "technology_nodes", "technology_node_links", "technology_effects_junction",
            "technology_ui_tabs", "technology_ui_tabs_to_technology_nodes_junctions")
    t = {n: TableKit(n) for n in noms}
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))

    def en(cle):
        v = (nos.get(cle) or {}).get("en")
        if not v:
            raise SystemExit(f"lot 40 : texte {cle} absent de textes_gameplay.json")
        return escape(v)

    tt, tn, tl, te = t["technologies"], t["technology_nodes"], t["technology_node_links"], t["technology_effects_junction"]
    tab, tj = t["technology_ui_tabs"], t["technology_ui_tabs_to_technology_nodes_junctions"]
    modele = "wh3_dlc29_tech_nef_imentet_2"
    lien_modele = tl.ou(parent_key="wh3_dlc29_tech_nef_imentet_1", child_key=modele)[0][0]
    effet_modele = te.ou(technology="wh3_main_tech_vmp_units_knights_2",
                         effect="wh_main_effect_force_stat_charge_bonus_black_knights_blood_knights")[0][0]
    pris_ui = {tt.valeurs(c).get("unique_index") for _, c in tt.lignes}
    tab.ajouter_sur_modele("vmp_neferata", {
        "key": ONGLET_DU_DUC, "localised_name": en("technology_ui_tabs_localised_name_" + ONGLET_DU_DUC),
        "tooltip_string": en("technology_ui_tabs_tooltip_string_" + ONGLET_DU_DUC), "sort_order": "5",
        "tier_offset": "80"})
    enfants = {}
    for nom, (_, _, _, _, _, parents, _) in BRANCHE_DU_DUC.items():
        for p in parents:
            enfants.setdefault(p, []).append(nom)
    for nom, (tier, indent, points, cout, icone, parents, effets) in BRANCHE_DU_DUC.items():
        cle = PREFIXE_TECH_DUC + nom
        ident = ident_numerique(f"tech_duc:{nom}", pris_ui)
        pris_ui.add(ident)
        tt.ajouter_sur_modele(modele, {
            "key": cle, "onscreen_name": en("technologies_onscreen_name_" + cle),
            "short_description": en("technologies_short_description_" + cle), "icon_name": icone,
            "unique_index": ident})
        tn.ajouter_sur_modele(modele, {
            "key": cle, "technology_key": cle, "faction_key": "wh_main_vmp_mousillon", "campaign_key": CAMPAGNE,
            "tier": str(tier), "indent": str(indent), "research_points_required": str(points),
            "resource_cost": f"wh3_main_vmp_unit_tech_cost_{cout}" if cout else "", "required_parents": "0",
            "pixel_offset_x": DECALAGE_PX[tier], "pixel_offset_y": "0", "optional_ui_group": ""})
        tj.ajouter_sur_modele(tj.ou(tab="vmp_neferata", node=modele)[0][0], {"tab": ONGLET_DU_DUC, "node": cle})
        for effet, valeur, portee in effets:
            te.ajouter_sur_modele(effet_modele, {"technology": cle, "effect": effet, "value": valeur,
                                                 "effect_scope": portee})
        # liens : du parent (côté des tiers croissants, 2) à l'enfant (côté des tiers décroissants, 4) ; deux liens qui
        # partent du même côté ou y arrivent sont écartés de ±0,3 (schéma de covens_1 et covens_3)
        for p in parents:
            freres = enfants[p]
            decal_p = "0" if len(freres) == 1 else ("0.30000001192092896" if freres.index(nom) == 0
                                                     else "-0.30000001192092896")
            decal_e = "0" if len(parents) == 1 else ("0.30000001192092896" if parents.index(p) == 0
                                                      else "-0.30000001192092896")
            tl.ajouter_sur_modele(lien_modele, {
                "parent_key": PREFIXE_TECH_DUC + p, "child_key": cle, "parent_link_position": "2",
                "child_link_position": "4", "parent_link_position_offset": decal_p, "child_link_position_offset": decal_e,
                "visible_in_ui": "1", "initial_descent_tiers": "0"})
    return t, [("technologies", "technologies_tables", "key", PREFIXE_TECH_DUC),
               ("technology_nodes", "technology_nodes_tables", "key", PREFIXE_TECH_DUC),
               ("technology_node_links", "technology_node_links_tables", "child_key", PREFIXE_TECH_DUC),
               ("technology_effects_junction", "technology_effects_junction_tables", "technology", PREFIXE_TECH_DUC),
               ("technology_ui_tabs", "technology_ui_tabs_tables", "key", [ONGLET_DU_DUC]),
               ("technology_ui_tabs_to_technology_nodes_junctions",
                "technology_ui_tabs_to_technology_nodes_junctions_tables", "tab", [ONGLET_DU_DUC])]


KRELL, KRELL_IE, KRELL_CASE = "2140784203", "1366449517", ("298", "303")
KEMMLER_FACTION_SP = "2120137700"     # start_pos_factions de la Légion des Tertres, notre campagne


def lot_etape41():
    """Lot 41 (25.09.2026, 17 h 45 ; décision de Charles : « il faut absolument l'ajouter ») : Krell au départ avec Kemmler,
    comme aux Empires, où sa fiche de CA l'annonce (« Commence avec le Héros légendaire Krell »). Personnage de CA
    1366449517 (champion wh3_dlc29_vmp_krell, unique) recopié pour notre faction de départ 2120137700, en (298, 303) : à
    côté de Kemmler (297, 303) et de son nécromancien (296, 303), case franchissable et libre (couches de WH1). Ses deux
    objets de CA (Hache noire de Krell, Armure des Tertres). Règles de seigneur_soeurs.py : unique = 0, identifiants
    d'objets libres dès 1000. Sous-type déjà permis à la faction (lot 31). Tables du STARTPOS : synchroniser
    zz_startpos_db, régénérer, essai Kemmler (construction). Rend ({table: TableKit}, [])."""
    P, AN = TableKit("start_pos_characters"), TableKit("start_pos_character_ancillaries")
    P.ajouter_sur_modele(KRELL_IE, {"ID": KRELL, "faction": KEMMLER_FACTION_SP, "startx": KRELL_CASE[0],
                                    "starty": KRELL_CASE[1], "unique": "0"})
    deja = {AN.valeurs(c).get("ancillary") for _, c in AN.lignes if AN.valeurs(c).get("character_id") == KRELL}
    pris = {AN.valeurs(c).get("id") for _, c in AN.lignes}
    n = 1000
    for k, c in list(AN.lignes):
        v = AN.valeurs(c)
        if v.get("character_id") == KRELL_IE and v.get("ancillary") not in deja:
            while str(n) in pris:
                n += 1
            AN.ajouter_sur_modele(k, {"id": str(n), "character_id": KRELL, "unique": "0"})
            pris.add(str(n))
    return {"start_pos_characters": P, "start_pos_character_ancillaries": AN}, []


# Trait de faction du Duc écarlate (lot 42, 25.09.2026, 17 h 50 ; demande de Charles : « en corrélation avec le lore, avec
# ses mécaniques et avec ce qu'a fait CA avec la 9.0 »). CA ne lui en donne aucun (faction_starting_general_effects n'a pas
# de ligne pour wh_dlc05_vmp_red_duke) ; une ligne de CA vaudrait aux Empires (table sans colonne de campagne) : le
# paquet est posé par saison_duc.lua, dans notre seule campagne. Modèle 9.0 (Neferata, Vlad) : « Vampire légendaire »,
# des lignes « A accès à … » pour les mécaniques propres, puis des effets de CA. Ici les lignes « A accès à … », à nos
# clés : effet -> (icône de CA déjà employée par un effet, is_positive_value_good). Textes : textes_gameplay.json.
EFFETS_DU_TRAIT_DUC = {
    "saison_duc_effect_duche_perdu_dummy": ("nemesis_crown_sealed.png", "1"),
    "saison_duc_effect_faveur_abhorash_dummy": ("bloodline_blood_dragon.png", "1"),
    "saison_duc_effect_impot_du_sang_dummy": ("blood_kiss.png", "1"),
    # la traque : en rouge, comme un malus
    "saison_duc_effect_decret_de_richemont_dummy": ("hunter_effect_icons_wanted_level.png", "0"),
}
TRAIT_DUC = "saison_lord_trait_duc"


def lot_etape42():
    """Lot 42 (25.09.2026) : le trait de faction du Duc écarlate, « Tyran d'Aquitanie » (effect_bundles, ligne faite sur
    le trait de Vlad), et ses quatre lignes « A accès à … » (effects, lignes faites sur wh3_dlc29_effect_web_of_power_dummy).
    Effets posés par saison_duc.lua (paquet personnalisé, comme Grom, lot 38). effects : table NEUVE dans un pack joué,
    essai de démarrage du Duc (erreur 107). Rend ({table: TableKit}, [entrées])."""
    from xml.sax.saxutils import escape
    te, tb = TableKit("effects"), TableKit("effect_bundles")
    nos = json.load(open(TEXTES_GAMEPLAY, encoding="utf-8"))

    def en(cle):
        v = (nos.get(cle) or {}).get("en")
        if not v:
            raise SystemExit(f"lot 42 : texte {cle} absent de textes_gameplay.json")
        return escape(v)

    for cle, (icone, bon) in EFFETS_DU_TRAIT_DUC.items():
        te.ajouter_sur_modele("wh3_dlc29_effect_web_of_power_dummy", {
            "effect": cle, "icon": icone, "icon_negative": icone, "description": en("effects_description_" + cle),
            "is_positive_value_good": bon})
    tb.ajouter_sur_modele("wh_dlc04_lord_trait_vmp_vlad_von_carstein", {
        "key": TRAIT_DUC, "localised_title": en("effect_bundles_localised_title_" + TRAIT_DUC),
        "localised_description": en("effect_bundles_localised_description_" + TRAIT_DUC)})
    return {"effects": te, "effect_bundles": tb}, [
        ("effects", "effects_tables", "effect", list(EFFETS_DU_TRAIT_DUC)),
        ("effect_bundles", "effect_bundles_tables", "key", [TRAIT_DUC])]


# Groupes d'indices de l'IA à nous (lot 43, 25.09.2026, revue du pack de la bêta B1 ; décision de Charles : « corrige
# tous les défauts avant la bêta ») : nos régions étaient DANS quatre groupes de CA qui gardent leurs régions des Empires
# (motif de l'erreur 154) ; aux Empires, mod actif, ces groupes recevaient nos régions absentes. Chaque groupe de CA a
# son double à nous (mêmes régions à nous, mêmes politiques de l'IA : lignes de CA de
# cai_personality_region_group_policy_junctions recopiées vers le double), et nos lignes sortent du groupe de CA.
# Reste dans son groupe de CA, justifié : wh3_wood_elf_forests (18 lignes). Seule la requête d'IA
# queried_domain_target_in_region_group_woodelf_forest le lit (cai_query_variable_set_junctions, clé ensemble + variable :
# une seule valeur possible, un double exigerait de réécrire la ligne de CA) ; aucun script ni aucune interface ne le lit.
GROUPES_IA_A_NOUS = {
    "cai_region_hint_area_bretonnia": "saison_cai_region_hint_area_bretonnia",
    "cai_region_hint_area_athel_loren": "saison_cai_region_hint_area_athel_loren",
    "cai_region_hint_area_dwarf_empire": "saison_cai_region_hint_area_dwarf_empire",
    "cai_region_hint_sub_area_western_mountains": "saison_cai_region_hint_sub_area_western_mountains",
}


def lot_etape43():
    """Lot 43 (25.09.2026) : les quatre groupes d'indices de l'IA à nous (GROUPES_IA_A_NOUS). region_groups (4 lignes
    neuves, faites sur celle de CA), regions_to_region_groups_junctions (nos régions déplacées : lignes neuves vers le
    double, nos lignes retirées du groupe de CA), cai_personality_region_group_policy_junctions (lignes de CA recopiées
    vers le double : TABLE NEUVE dans un pack joué, essai de démarrage, erreur 107). Aucune ligne de CA modifiée ou
    retirée. Rend ({table: TableKit}, [entrées])."""
    rg, rj = TableKit("region_groups"), TableKit("regions_to_region_groups_junctions")
    pol = TableKit("cai_personality_region_group_policy_junctions")
    for ca, nous in GROUPES_IA_A_NOUS.items():
        rg.ajouter_sur_modele(ca, {"group_key": nous})
        for k, c in list(rj.lignes):
            v = rj.valeurs(c)
            if v["region_group"] == ca and v["region"].startswith("wh_dlc05_"):
                rj.ajouter_sur_modele(k, {"region_group": nous})
                rj.retirer(k)
        for k, c in list(pol.lignes):
            if pol.valeurs(c)["region_group_key"] == ca:
                pol.ajouter_sur_modele(k, {"region_group_key": nous})
    # wh3_wood_elf_forests (25.09.2026, 19 h 20 ; règle de verifier_groupes.py, aucune de nos régions dans un groupe de CA) :
    # pas de double possible (voir plus haut), nos 18 lignes sont RETIRÉES. Effet : la requête d'IA des Elfes sylvains
    # « cible dans le domaine forestier » ne voit plus nos forêts ; aucun script ni aucune interface ne lit ce groupe.
    for k, c in list(rj.lignes):
        v = rj.valeurs(c)
        if v["region_group"] == "wh3_wood_elf_forests" and v["region"].startswith("wh_dlc05_"):
            rj.retirer(k)
    doubles = list(GROUPES_IA_A_NOUS.values())
    return {"region_groups": rg, "regions_to_region_groups_junctions": rj,
            "cai_personality_region_group_policy_junctions": pol}, [
        ("region_groups", "region_groups_tables", "group_key", doubles),
        ("cai_personality_region_group_policy_junctions", "cai_personality_region_group_policy_junctions_tables",
         "region_group_key", doubles)]


# Tous les lots lot_etapeN présents dans ce fichier (25.09.2026 : liste calculée, plus de liste à tenir à jour)
LOTS = {nom[4:]: f for nom, f in list(globals().items()) if re.fullmatch(r"lot_etape\d+", nom)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table")
    ap.add_argument("--colonne")
    ap.add_argument("--de")
    ap.add_argument("--vers")
    ap.add_argument("--lot", choices=sorted(LOTS, key=lambda c: int(c[5:])))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    dossier = os.path.join(ATELIER, "05-journal", "db-backups",
                           datetime.now().strftime("%Y%m%d-%H%M%S") + "-donnees-campagne")
    if a.lot:
        tables, entrees = LOTS[a.lot]()
        manques = verifier_references(tables)
        for m in manques[:30]:
            print("  RÉFÉRENCE MANQUANTE :", m)
        if manques and a.apply:
            print(f"{len(manques)} référence(s) manquante(s) : rien n'est écrit")
            return 1
        total = 0
        for nom, t in tables.items():
            print(f"  {nom:62s} {len(t.neuves):4d} neuve(s), {t.deja:3d} déjà là, {len(t.retirees):3d} retirée(s), "
                  f"{len(t.modifiees):3d} modifiée(s)")
            total += len(t.neuves) + len(t.retirees) + len(t.modifiees)
            if a.apply:
                t.ecrire(dossier)
        print(f"{total} ligne(s) {'écrites' if a.apply else 'à écrire'}"
              + (f" ; sauvegarde : {dossier}" if a.apply and total else ""))
        print("\nentrées pour build_pack.TABLES :")
        for e in entrees:
            print(f"    {e!r},")
        if a.apply and total:
            # contrôle d'idempotence (23.09.2026 : le lot 17 recréait son seigneur neuf à chaque passe) : le lot relu
            # depuis le kit qu'on vient d'écrire ne doit plus rien avoir à écrire
            relu, _ = LOTS[a.lot]()
            reste = {nom: len(t.neuves) + len(t.retirees) + len(t.modifiees) for nom, t in relu.items()}
            reste = {nom: n for nom, n in reste.items() if n}
            if reste:
                print(f"\n!!! LOT NON IDEMPOTENT : une nouvelle passe écrirait encore {reste} ; corriger le lot "
                      f"(sauvegarde d'avant : {dossier})")
                return 2
            print("\ncontrôle : nouvelle passe à 0 ligne (lot idempotent)")
        return 0
    if not (a.table and a.colonne and a.de and a.vers):
        ap.error("--table, --colonne, --de et --vers, ou --lot")
    neuves, deja = recopier(a.table, a.colonne, a.de, a.vers, a.apply, dossier)
    for n in neuves:
        print("  ", re.sub(r"\s+", " ", n)[:220])
    print(f"{a.table} : {len(neuves)} ligne(s) {'écrite(s)' if a.apply else 'à écrire'}, {deja} déjà présente(s)")
    print(f'entrée pour build_pack.TABLES : ("{a.table}", "{a.table}_tables", "{a.colonne}", "{a.vers}")')
    return 0


if __name__ == "__main__":
    sys.exit(main())
