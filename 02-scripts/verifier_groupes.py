"""Contrôle avant le pack : chaque groupe de régions cité par une jonction du pack existe (dans le pack ou dans le jeu).

Erreur du 23.09.2026, 20 h 25 : le lot 23 a créé le groupe wh_dlc05_saison_forest_region_group_athel_loren dans le kit,
mais l'entrée `region_groups` du pack (tables_gameplay.py, lot 1) filtre sur une LISTE EXPLICITE de clés : les 5
jonctions du groupe sont entrées dans le pack (préfixe de région wh_dlc05_), pas le groupe. Le jeu a refusé le pack à la
génération du startpos (bad_mods_report : regions_to_region_groups_junctions_tables).

Le contrôle refait la sélection de build_pack.py (mêmes entrées TABLES, même kit_rows) pour les deux tables, puis
compare aux groupes de base du jeu (tables_jeu.py, nos packs exclus).

    python 02-scripts\\verifier_groupes.py        -> 0 si tout est couvert, 1 sinon (liste des groupes manquants)

Lecture seule.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pack as BP  # noqa: E402
import tables_jeu as TJ  # noqa: E402


def lignes_du_pack(table_kit):
    """Lignes du kit que build_pack mettrait dans le pack pour cette table (toutes les entrées TABLES réunies)."""
    out = []
    for table, table_jeu, colonne, valeur in BP.TABLES:
        if table == table_kit and table_jeu not in BP.TABLES_EXCLUES:
            out.extend(BP.kit_rows(table, colonne, valeur))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    groupes_pack = {r.get("group_key", "") for r in lignes_du_pack("region_groups")}
    jonctions = lignes_du_pack("regions_to_region_groups_junctions")
    groupes_jeu = {str(r.get("group_key", "")) for r in TJ.table("region_groups")}
    cites = {}
    for r in jonctions:
        cites.setdefault(r.get("region_group", ""), []).append(r.get("region", ""))
    manquants = {g: rs for g, rs in cites.items() if g not in groupes_pack and g not in groupes_jeu}
    print(f"{len(jonctions)} jonctions du pack citent {len(cites)} groupes : {len(set(cites) & groupes_pack)} dans le "
          f"pack, {len((set(cites) - groupes_pack) & groupes_jeu)} du jeu, {len(manquants)} introuvable(s)")
    for g, rs in sorted(manquants.items()):
        print(f"  MANQUANT {g} ({len(rs)} jonction(s), ex. {rs[0]}) : ajouter la clé à l'entrée region_groups du pack "
              f"(donnees_campagne.cles_region_groups / tables_gameplay.py)")
    # Revue du pack avant la bêta (25.09.2026, 19 h 20) : nos régions ne doivent entrer dans AUCUN groupe de CA (76 lignes
    # dans 5 groupes lus par l'IA, cai_region_hint_area_bretonnia, wh3_wood_elf_forests… : effet sur les Empires, motif de
    # l'erreur 154). Nos groupes : clé à nous (lot 43, saison_cai_region_hint_*). Exception seulement si nommée ici, avec
    # sa raison.
    groupes_ca_permis = {}
    dans_ca = {g: rs for g, rs in cites.items() if g in groupes_jeu and g not in groupes_pack and g not in groupes_ca_permis}
    for g, rs in sorted(dans_ca.items()):
        print(f"  GROUPE DE CA {g} : {len(rs)} de nos régions (ex. {rs[0]}) ; à remplacer par un groupe à nous")
    print(f"nos régions dans des groupes de CA : {sum(len(v) for v in dans_ca.values())} ligne(s), {len(dans_ca)} groupe(s)")
    return 1 if manquants or dans_ca else 0


if __name__ == "__main__":
    sys.exit(main())
