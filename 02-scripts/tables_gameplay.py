"""
tables_gameplay.py - entrées de build_pack.TABLES pour les données de campagne (gameplay) de la session « IA et modding 3D »
(23.09.2026). Chaque lot est une liste TABLES_LOT<n> au format de TABLES (table du kit, table du jeu, colonne,
préfixe ou liste de clés exactes). Propriétaire : la session d'audit ; build_pack.py les charge toutes.
"""

# Entrées pour build_pack.TABLES : lot 1 des données de campagne (donnees_campagne.py --lot etape1), 23.09.2026, 00 h 40
# 1 313 lignes écrites dans le kit (sauvegarde : 05-journal\db-backups\20260923-003939-donnees-campagne).
# Aucune de ces tables n'est lue à la génération du startpos : une reconstruction du pack suffit.
# lot 7 (forêt à nous, plus bas) : membres de groupe ajoutés à l'entrée du lot 1 (une seule entrée par table)
MEMBRES_FORET = ['saison_feature_wood_elves'] + ['wh2_dlc16_pooled_resource_world_roots_health_saison_athel_loren_%d' % i
                                                for i in range(5)]
# lot 15 (23.09.2026) : groupes de réserve de Waaagh! de nos 26 provinces, dans les entrées existantes
GROUPES_WAAAGH = ['saison_grn_boost_pool_wh_dlc05_%s' % p for p in (
    'anmyr', 'aquitaine', 'argwylon', 'arranoc', 'atylwyth', 'bastonne', 'bordeleaux', 'brionne', 'carcassonne',
    'cavaroc', 'cythral', 'fyr_darric', 'gisoreux', 'grey_mountains', 'grey_mountains_2', 'massif_orcal', 'modryn', 'montfort',
    'mousillon', 'oak_of_ages', 'parravon', 'quenelles', 'talsyn', 'tirsyth', 'torgovann', 'wydrioth')]
TABLES_LOT1 = [
    ('faction_agent_permitted_subtypes', 'faction_agent_permitted_subtypes_tables', 'faction', ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc', 'wh_dlc05_wef_cythral', 'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth', 'wh_dlc05_brt_brionne', 'wh_dlc05_brt_gisoroux', 'wh_dlc05_brt_montfort', 'wh_dlc05_brt_quenelles', 'wh_dlc03_bst_beastmen_brayherd']),
    ('faction_rebellion_units_junctions', 'faction_rebellion_units_junctions_tables', 'faction_key', ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc', 'wh_dlc05_wef_cythral', 'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth', 'wh_dlc05_brt_brionne', 'wh_dlc05_brt_gisoroux', 'wh_dlc05_brt_montfort', 'wh_dlc05_brt_quenelles', 'wh_dlc03_bst_beastmen_brayherd']),
    ('faction_to_faction_groups_junctions', 'faction_to_faction_groups_junctions_tables', 'faction_key', ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc', 'wh_dlc05_wef_cythral', 'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth', 'wh_dlc05_brt_brionne', 'wh_dlc05_brt_gisoroux', 'wh_dlc05_brt_montfort', 'wh_dlc05_brt_quenelles', 'wh_dlc03_bst_beastmen_brayherd']),
    ('campaign_map_attrition_faction_immunities', 'campaign_map_attrition_faction_immunities_tables', 'faction', ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc', 'wh_dlc05_wef_cythral', 'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth', 'wh_dlc05_brt_brionne', 'wh_dlc05_brt_gisoroux', 'wh_dlc05_brt_montfort', 'wh_dlc05_brt_quenelles', 'wh_dlc03_bst_beastmen_brayherd']),
    ('climbing_ladders_meshes_definitions', 'climbing_ladders_meshes_definitions_tables', 'faction_key', ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc', 'wh_dlc05_wef_cythral', 'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth', 'wh_dlc05_brt_brionne', 'wh_dlc05_brt_gisoroux', 'wh_dlc05_brt_montfort', 'wh_dlc05_brt_quenelles', 'wh_dlc03_bst_beastmen_brayherd']),
    ('fame_levels', 'fame_levels_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('fame_level_agent_record_junctions', 'fame_level_agent_record_junctions_tables', 'fame_level', ['1016495656', '136168048', '1553501306', '156577004', '1669491314', '1749887527', '1836338542', '1866692445', '1936055580', '1987643387', '270936577', '282226068', '295329471', '322575778', '347654302', '438809984', '457068870', '904952743', '946879511']),
    ('campaign_group_member_criteria_campaigns', 'campaign_group_member_criteria_campaigns_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('cai_diplomacy_excluded_factions', 'cai_diplomacy_excluded_factions_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('campaign_camera_map_bounds', 'campaign_camera_map_bounds_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('campaign_battle_paths', 'campaign_battle_paths_tables', 'path', ['wh_dlc05_wood_elves_map_1']),
    ('campaign_to_agent_subtypes', 'campaign_to_agent_subtypes_tables', 'campaign_type', 'wh_dlc05_wood_elves'),
    ('region_groups', 'region_groups_tables', 'group_key', ['dwarf_historical_holds_wh_dlc05_wood_elves', 'dwarf_historical_legendary_wh_dlc05_wood_elves', 'dwarf_historical_other_wh_dlc05_wood_elves', 'wh_dlc05_anmyr', 'wh_dlc05_aquitaine', 'wh_dlc05_argwylon', 'wh_dlc05_arranoc', 'wh_dlc05_atylwyth', 'wh_dlc05_bastonne', 'wh_dlc05_bordeleaux', 'wh_dlc05_brionne', 'wh_dlc05_carcassonne', 'wh_dlc05_cavaroc', 'wh_dlc05_cythral', 'wh_dlc05_fyr_darric', 'wh_dlc05_gisoreux', 'wh_dlc05_grey_mountains', 'wh_dlc05_grey_mountains_2', 'wh_dlc05_massif_orcal', 'wh_dlc05_modryn', 'wh_dlc05_montfort', 'wh_dlc05_mousillon', 'wh_dlc05_oak_of_ages', 'wh_dlc05_parravon', 'wh_dlc05_quenelles', 'wh_dlc05_talsyn', 'wh_dlc05_tirsyth', 'wh_dlc05_torgovann', 'wh_dlc05_wydrioth', 'wh_dlc05_saison_forest_region_group_athel_loren']),  # lots 1, 2 et 23 (une seule entrée par table)
    ('campaign_map_winds_of_magic_areas', 'campaign_map_winds_of_magic_areas_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('regions_to_region_groups_junctions', 'regions_to_region_groups_junctions_tables', 'region', 'wh_dlc05_'),
    ('pooled_resource_to_region_junctions', 'pooled_resource_to_region_junctions_tables', 'region', 'wh_dlc05_'),
    ('rituals_to_regions', 'rituals_to_regions_tables', 'region', 'wh_dlc05_'),
    ('campaign_group_members', 'campaign_group_members_tables', 'id', MEMBRES_FORET + GROUPES_WAAAGH + ['wh3_main_corruption_campaigns_wh_dlc05_wood_elves', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_carcassonne_summersfall_fort', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_parravon_grunere', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_parravon_montlac', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_quenelles_quenelles']),
    ('campaign_group_member_criteria_regions', 'campaign_group_member_criteria_regions_tables', 'region', 'wh_dlc05_'),
    ('campaign_group_member_criteria_subcultures', 'campaign_group_member_criteria_subcultures_tables', 'member', GROUPES_WAAAGH + ['wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_carcassonne_summersfall_fort', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_parravon_grunere', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_parravon_montlac', 'wh2_main_sc_wef_wood_elves_occupation_decision_raze_without_occupy_forest_border_wh_dlc05_quenelles_quenelles']),
    ('audio_campaign_maps', 'audio_campaign_maps_tables', 'key', ['wh_dlc05_wood_elves_map_1']),
    ('audio_campaign_environment_static_sounds', 'audio_campaign_environment_static_sounds_tables', 'map', 'wh_dlc05_wood_elves_map_1'),
    ('audio_campaign_environment_tree_sound_assignments', 'audio_campaign_environment_tree_sound_assignments_tables', 'map', 'wh_dlc05_wood_elves_map_1'),
    ('audio_campaign_region_group_assignments', 'audio_campaign_region_group_assignments_tables', 'region', 'wh_dlc05_'),
    ('campaigns_campaign_variables_junctions', 'campaigns_campaign_variables_junctions_tables', 'campaign_name', 'wh_dlc05_wood_elves'),
    ('cai_variables_overides', 'cai_variables_overides_tables', 'campaign_key', 'wh_dlc05_wood_elves'),
    ('resources_to_campaign_junctions', 'resources_to_campaign_junctions_tables', 'campaign', 'wh_dlc05_wood_elves'),
    ('campaign_difficulty_handicap_effects', 'campaign_difficulty_handicap_effects_tables', 'optional_campaign_key', 'wh_dlc05_wood_elves'),
    ('character_experience_skill_tiers', 'character_experience_skill_tiers_tables', 'optional_campaign_key', 'wh_dlc05_wood_elves'),
    ('loading_screen_quotes_to_campaigns', 'loading_screen_quotes_to_campaigns_tables', 'campaign', 'wh_dlc05_wood_elves_map_1'),
]


# Lot 2 (donnees_campagne.py --lot etape2), 23.09.2026, 01 h 10 : verrou du DLC « Realm of the Wood Elves » sur l'écran
# de campagne (notre carte rattachée aux paquets wh3_base_game et wh1_wood_elves, comme les cartes de CA), et groupes
# de régions historiques des nains (leurs lignes region_groups passent par l'entrée du lot 1, leurs jonctions par
# l'entrée « région wh_dlc05_ »). Aucune table du startpos.
# 23.09.2026, 02 h 40 : la jonction du verrou d'écran (campaign_map_playable_area_ownership_content_pack_junctions, zone
# 1758400002 -> wh3_base_game, wh1_wood_elves) est RETIRÉE : le jeu la refuse au démarrage et se ferme seul, 8 s après
# le lancement, sans message (session de construction, sous cdb). Le verrou du DLC reste en jeu (saison_verrou_dlc.lua).
# Cause probable (non prouvée) : DEUX paquets pour une même zone jouable ; chez CA, chaque zone jouable (10 sur 10) et
# chaque bataille (144 sur 144) n'a qu'UNE ligne, alors que factions, sous-types et unités en ont parfois plusieurs.
# Variante à essayer, si Charles veut le verrou d'écran : une seule ligne, 1758400002 -> wh1_wood_elves.
# 25.09.2026, 17 h 55 (demande de Charles à 17 h 05, relayée par la construction) : la variante, UNE seule ligne,
# 1758400002 -> wh1_wood_elves, a été essayée (pack de 17 h 54). ÉCHEC : le jeu se ferme 20 s après le lancement, code 0
# (essais Duc et Kemmler), comme le 23.09. La cause n'est donc pas le double paquet : une zone jouable liée à un paquet de
# contenu est refusée telle quelle. Table remise dans TABLES_EXCLUES (build_pack) ; le verrou visible avant la partie
# passe par le menu (saison_choix_par_defaut.lua, VERROU_MENU = true) et le verrou en jeu par saison_verrou_dlc.lua.
TABLES_LOT2 = []


# Lot 3 (donnees_campagne.py --lot etape3), 23.09.2026, 01 h 33 : l'histoire de WH1, mission de la bataille finale du Pic
# d'Argent (clé de WH1, bataille de WH3 wh_dlc05_qb_wef_grand_silver_spire, emplacement de WH1) et ses lignes du
# directeur de campagne. 6 lignes (sauvegarde : 05-journal\db-backups\20260923-013306-donnees-campagne). Les quêtes de
# WH1 (lot 4) iront dans les MÊMES entrées (listes allongées) : une seule entrée par table du jeu.
MISSIONS_HISTOIRE = ['wh_dlc05_qb_wef_mini_silver_spire',
                     # lot 4 (donnees_campagne.py --lot etape4), 23.09.2026, 01 h 55 : les 18 missions des quêtes de WH1
                     'wh_dlc05_wef_orion_horn_of_the_wild_stage_1_mini', 'wh_dlc05_wef_orion_horn_of_the_wild_stage_2_mini',
                     'wh_dlc05_wef_orion_horn_of_the_wild_stage_3a_mini',
                     'wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold_mini',
                     'wh_dlc05_wef_orion_cloak_of_isha_stage_1_mini', 'wh_dlc05_wef_orion_cloak_of_isha_stage_2_mini',
                     'wh_dlc05_wef_orion_cloak_of_isha_stage_3a_mini',
                     'wh_dlc05_qb_wef_orion_the_cloak_of_isha_stage_3_the_night_glens_mini',
                     'wh_dlc05_wef_orion_spear_of_kurnous_stage_1_mini', 'wh_dlc05_wef_orion_spear_of_kurnous_stage_2_mini',
                     'wh_dlc05_wef_orion_spear_of_kurnous_stage_3a_mini',
                     'wh_dlc05_qb_wef_orion_the_spear_of_kurnous_stage_3_the_oak_of_ages_mini',
                     'wh_dlc05_wef_durthu_sword_of_daith_stage_1_mini', 'wh_dlc05_wef_durthu_sword_of_daith_stage_2_mini',
                     'wh_dlc05_wef_durthu_sword_of_daith_stage_3a_mini',
                     'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini',
                     'wh_dlc05_wef_durthu_sword_of_daith_stage_4a_mini',
                     'wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns_mini',
                     # lot 10 (23.09.2026, 04 h 10) : quêtes de CA d'Alberic, de la Fée et de Morghur, pour notre carte
                     'saison_qb_brt_alberic_trident_of_manann', 'saison_qb_brt_alberic_braid_of_bordeleaux',
                     'saison_qb_brt_fay_chalice_of_potions', 'saison_qb_bst_morghur_stave_of_ruinous_corruption',
                     # lot 10 complété (23.09.2026, 15 h) : quêtes de CA de Kemmler, Grom et Drycha
                     'saison_qb_vmp_kemmler_skull_staff', 'saison_qb_vmp_kemmler_cloak_of_mists',
                     'saison_qb_vmp_kemmler_chaos_tomb_blade', 'saison_qb_grn_grom_axe_of_grom', 'saison_qb_grn_grom_lucky_banner',
                     'saison_qb_wef_drycha_coeddil_unchained', 'saison_qb_wef_sisters_ceithin_har',
                     'saison_qb_gotrek_felix_alberic', 'saison_qb_gotrek_felix_fay', 'saison_qb_bst_chute_de_l_homme',
                     'saison_felix_arene', 'saison_felix_chapelle', 'saison_felix_reikguard',
                     # lot 12 (23.09.2026, 13 h 45) : les 25 missions des Chroniques de la Saison (saison_chroniques.lua)
                     'saison_chronique_alberic_1', 'saison_chronique_alberic_2', 'saison_chronique_alberic_3',
                     'saison_chronique_alberic_4', 'saison_chronique_fee_1', 'saison_chronique_fee_2',
                     'saison_chronique_fee_3', 'saison_chronique_fee_4', 'saison_chronique_morghur_1',
                     'saison_chronique_morghur_2', 'saison_chronique_morghur_3', 'saison_chronique_morghur_4',
                     'saison_chronique_duc_1', 'saison_chronique_duc_2', 'saison_chronique_duc_3', 'saison_chronique_duc_4',
                     'saison_chronique_drycha_1', 'saison_chronique_drycha_2', 'saison_chronique_drycha_3',
                     'saison_chronique_kemmler_1', 'saison_chronique_kemmler_2', 'saison_chronique_kemmler_3',
                     'saison_chronique_grom_1', 'saison_chronique_grom_2', 'saison_chronique_grom_3',
                     # batailles finales des chroniques (23.09.2026, 15 h 30)
                     'saison_chronique_alberic_5', 'saison_chronique_fee_5', 'saison_chronique_morghur_5',
                     'saison_chronique_duc_5', 'saison_chronique_drycha_4', 'saison_chronique_kemmler_4',
                     'saison_chronique_grom_4',
                     # Échos de la Saison (23.09.2026, 16 h)
                     'saison_echo_alberic', 'saison_echo_fee', 'saison_echo_morghur', 'saison_echo_duc',
                     'saison_echo_drycha', 'saison_echo_kemmler', 'saison_echo_grom',
                     # refonte « loreful » (23.09.2026, 17 h)
                     'saison_chronique_drycha_parravon', 'saison_chronique_kemmler_cairns', 'saison_chronique_grom_gragabad',
                     'saison_echo_orion', 'saison_echo_durthu',
                     # les Sœurs du Crépuscule (24.09.2026)
                     'saison_chronique_soeurs_1', 'saison_chronique_soeurs_2', 'saison_chronique_soeurs_3',
                     'saison_chronique_soeurs_4', 'saison_chronique_soeurs_5', 'saison_echo_soeurs',
                     'saison_chronique_soeurs_enclume',
                     # Revanche de Dent-Noire, missions 3 et 4 sans Tor Yvresse (lot 10, 25.09.2026)
                     'saison_grn_grom_black_toof_3', 'saison_grn_grom_black_toof_4',
                     # le défi du Duc écarlate (lot 12, mécanique E, 25.09.2026)
                     'saison_duc_defi']
# textes des objectifs scriptés des chroniques (lot 12)
TEXTES_OBJECTIFS_CHRONIQUES = ['saison_alberic_pacte_asrai', 'saison_fee_quenelles', 'saison_fee_ducs', 'saison_drycha_addaivoch',
                               'saison_morghur_val_malheur',
                               # 24.09.2026 : l'arène de Félix manquait ici (présente dans donnees_campagne.py) ; les Sœurs
                               'saison_felix_arene', 'saison_soeurs_porte_du_roi',
                               # le défi du Duc écarlate (mécanique E, 25.09.2026)
                               'saison_duc_defi_en_personne']
TABLES_LOT3 = [
    ('missions', 'missions_tables', 'key', MISSIONS_HISTOIRE),
    # (25.09.2026) plus d'entrée mission_text : WH3 n'a pas de table mission_text_tables (schéma RPFM 9.0) ; la table
    # mission_text du kit ne sert qu'aux textes, et « override_text mission_text_text_<clé> » lit la clé de texte seule,
    # comme les objectifs de Grom chez CA. Nos textes d'objectifs passent par textes_gameplay.json (injecter_textes).
    ('campaign_localised_strings', 'campaign_localised_strings_tables', 'key', 'saison_nom_'),  # lot 12 : noms de faction
    ('names', 'names_tables', 'id', ['578028567', '433068992', '1496308970', '412763886', '593790985',
                                     '375345544', '1293672490', '167863795', '1218116301']),  # lot 14 : noms de lore
    ('advice_threads', 'advice_threads_tables', 'thread', 'saison_prologue_'),  # lot 14 : prologues
    ('advice_levels', 'advice_levels_tables', 'advice_thread', 'saison_prologue_'),  # lot 14 : prologues
    ('campaign_group_member_criteria_provinces', 'campaign_group_member_criteria_provinces_tables', 'member', 'saison_grn_boost_pool_'),  # lot 15 : Waaagh!
    ('campaign_group_transported_military_force_unit_pools', 'campaign_group_transported_military_force_unit_pools_tables', 'campaign_group', 'saison_grn_boost_pool_'),  # lot 15 : Waaagh!
    ('cdir_events_mission_option_junctions', 'cdir_events_mission_option_junctions_tables', 'mission_key', MISSIONS_HISTOIRE),
    ('cdir_events_mission_payloads', 'cdir_events_mission_payloads_tables', 'mission_key', MISSIONS_HISTOIRE),
    ('cdir_events_mission_issuer_junctions', 'cdir_events_mission_issuer_junctions_tables', 'mission_key', MISSIONS_HISTOIRE),
]


# Lot 4 (donnees_campagne.py --lot etape4), 23.09.2026, 01 h 55 : quêtes de WH1 (236 lignes, sauvegarde
# 05-journal\db-backups\20260923-015458-donnees-campagne ; références vérifiées d'après les TWaD du kit). Les missions
# passent par les entrées du lot 3 (MISSIONS_HISTOIRE) ; ici les suites de missions et la bataille d'Ashenhall, retirée
# de WH3 et recréée (sa carte, son script et ses unités y sont). Aucune table du startpos.
ARMEES_ASHENHALL = ['wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_attacker_1',
                    'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_attacker_2',
                    'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_player_ally',
                    'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_player_mini']
PERSONNAGES_ASHENHALL = ['wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_attacker_1_general',
                         'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_player_ally_general',
                         'wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_player_branchwraith']
TABLES_LOT4 = [
    ('cdir_events_mission_followup_missions', 'cdir_events_mission_followup_missions_tables', 'mission_key', MISSIONS_HISTOIRE),
    ('battle_set_pieces', 'battle_set_pieces_tables', 'battle_name',
     ['wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini']),
    ('battle_set_piece_armies_junctions', 'battle_set_piece_armies_junctions_tables', 'battle_name',
     ['wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini']),
    ('battle_set_piece_armies', 'battle_set_piece_armies_tables', 'army_name', ARMEES_ASHENHALL),
    ('battle_set_piece_armies_characters', 'battle_set_piece_armies_characters_tables', 'character_name',
     PERSONNAGES_ASHENHALL),
    ('battle_set_piece_armies_characters_junctions', 'battle_set_piece_armies_characters_junctions_tables', 'army_name',
     ARMEES_ASHENHALL),
    ('battle_set_piece_armies_characters_skills', 'battle_set_piece_armies_characters_skills_tables', 'character_name',
     PERSONNAGES_ASHENHALL),
    ('battle_set_piece_armies_units_junctions', 'battle_set_piece_armies_units_junctions_tables', 'army_name',
     ARMEES_ASHENHALL),
]

# Tables de CA REMPLACÉES par les nôtres (23.09.2026, 03 h 10) : le fichier du pack porte le nom du fichier de db.pack,
# qu'il masque, au lieu de s'y ajouter. Plantage de Charles à 02 h 53 (tour 1, infobulle du bosquet des Racines du
# monde, `tooltip_wood_elf_glade`) : ces deux tables ne contiennent chez CA que les dix liens forêt -> bosquet des
# Empires Immortels (ressource wef_worldroots_* -> région, rituel de Renaissance -> région), plus notre ligne. La forêt
# d'Athel Loren avait donc deux bosquets, le Chêne des Empires d'abord ; l'infobulle prend une région absente de notre
# carte et lit le nom d'un objet nul (session de construction, désassemblage du vidage). Chez nous, une seule ligne
# chacune : notre Chêne. Effet de bord : pack activé dans les Empires, leurs bosquets perdraient ces liens.
REMPLACE_CA = {}   # vidé le 23.09.2026, 03 h 45 : clés à nous (lot 7), les Empires gardent leurs bosquets


# Lot 5 (23.09.2026) : cartes de bataille par lieu. Les correspondances « zone de captage -> cartes » de CA recopiées
# pour notre carte (battle_path), plus deux replis sur « Gatekeeper » (le noir des images). Les images de captage
# (`04-projets\saison-des-revelations\captage\`, `02-scripts\captage_campagne.py`) vont dans le terrain de bataille,
# compilées par BOB. Aucune table du startpos. Images compilées par la construction le 23.09.2026 à 03 h 02 (trois
# .compressed_map FASTBIN0 800 x 881 dans terrain/battles/wh_dlc05_wood_elves_map_1/) : l'entrée entre dans le pack,
# avec l'essai de démarrage (erreur 107).
TABLES_LOT5 = [
    ('battle_catchment_override_battle_mappings', 'battle_catchment_override_battle_mappings_tables', 'battle_path',
     ['wh_dlc05_wood_elves_map_1']),
]


# Lot 6 (donnees_campagne.py --lot etape6), 23.09.2026, 03 h 11 : interface (audit-interface.md). Vidéo d'intro de WH1
# (fichier movies/warhammer/race_intro_wef_mini.ca_vp8 embarqué par la construction), écrans de chargement d'Orion et de
# Durthu (récit de WH1 ; script de menu script/frontend/mod/saison_ecrans_de_chargement.lua). Les citations de
# chargement triées (293 sur 436) passent par l'entrée du lot 1. Sauvegarde : db-backups\20260923-031131-donnees-campagne.
# Tables de base neuves : essai de démarrage avant d'annoncer le pack (erreur 107).
# lot 8 (donnees_campagne.py --lot etape8), 23.09.2026, 03 h 50 : écrans de chargement d'Alberic, de la Fée et de Morghur
# (seigneurs de WH3 rendus jouables), ajoutés aux entrées du lot 6 (une seule entrée par table)
ECRANS_DE_CHARGEMENT = ['wh_dlc05_wef_wood_elves_orion_mini', 'wh_dlc05_wef_argwylon_durthu_mini',
                        'wh_main_brt_bordeleaux_alberic_mini', 'wh_main_brt_carcassonne_fay_mini',
                        'wh_dlc05_bst_morghur_herd_morghur_mini', 'wh_main_vmp_mousillon_red_duke_mini',
                        # Drycha, Kemmler, Grom (lot 8 étendu, 23.09.2026)
                        'wh2_dlc16_wef_drycha_drycha_mini', 'wh2_dlc11_vmp_the_barrow_legion_kemmler_mini',
                        'wh2_dlc15_grn_broken_axe_grom_mini',
                        # les Sœurs du Crépuscule (24.09.2026)
                        'wh2_dlc16_wef_sisters_of_twilight_sisters_mini']
TABLES_LOT6 = [
    ('videos', 'videos_tables', 'video_name', ['warhammer/race_intro_wef_mini',
                                              'Front_end_selection_movies/red_duke_front_end']),  # + Duc rouge (lot 8)
    ('custom_loading_screens', 'custom_loading_screens_tables', 'key', ECRANS_DE_CHARGEMENT),
    ('custom_loading_screen_components', 'custom_loading_screen_components_tables', 'custom_loading_screen_key',
     ECRANS_DE_CHARGEMENT),
]


# Lot 7 (donnees_campagne.py --lot etape7), 23.09.2026, 03 h 20 : Athel Loren a SES clés de Racines du monde, pour que
# toutes les campagnes coexistent mod actif (Charles). Ressource wef_worldroots_saison_athel_loren, rituel
# wh2_dlc16_ritual_rebirth_saison_athel_loren, groupe saison_feature_wood_elves (Elfes sylvains ET notre campagne), 5
# paliers de santé ; nos jonctions vers le Chêne sous ces clés (entrées du lot 1, préfixe de région). 51 lignes,
# sauvegarde db-backups60923-031959-donnees-campagne. Essai de démarrage avant d'annoncer le pack (erreur 107).
PALIERS_FORET = MEMBRES_FORET[1:]
TABLES_LOT7 = [
    ('pooled_resources', 'pooled_resources_tables', 'key', ['wef_worldroots_saison_athel_loren']),
    ('pooled_resource_factor_junctions', 'pooled_resource_factor_junctions_tables', 'resource',
     ['wef_worldroots_saison_athel_loren']),
    ('effect_bonus_value_pooled_resource_junctions', 'effect_bonus_value_pooled_resource_junctions_tables',
     'pooled_resource', ['wef_worldroots_saison_athel_loren']),
    ('campaign_groups', 'campaign_groups_tables', 'id', MEMBRES_FORET + GROUPES_WAAAGH),
    ('campaign_group_member_criteria_cultures', 'campaign_group_member_criteria_cultures_tables', 'member',
     ['saison_feature_wood_elves']),
    ('campaign_group_pooled_resources', 'campaign_group_pooled_resources_tables', 'campaign_group',
     ['saison_feature_wood_elves']),
    ('campaign_group_rituals', 'campaign_group_rituals_tables', 'campaign_group', ['saison_feature_wood_elves']),
    ('campaign_group_member_criteria_pooled_resources', 'campaign_group_member_criteria_pooled_resources_tables',
     'member', PALIERS_FORET),
    ('campaign_group_member_criteria_numeric_ranges', 'campaign_group_member_criteria_numeric_ranges_tables', 'member',
     PALIERS_FORET),
    ('campaign_group_pooled_resource_effects', 'campaign_group_pooled_resource_effects_tables', 'campaign_group',
     PALIERS_FORET),
    ('rituals', 'rituals_tables', 'key', ['wh2_dlc16_ritual_rebirth_saison_athel_loren']),
    ('resource_costs', 'resource_costs_tables', 'id', ['wh2_dlc16_ritual_rebirth_saison_athel_loren']),
    ('resource_cost_pooled_resource_junctions', 'resource_cost_pooled_resource_junctions_tables', 'resource_cost',
     ['wh2_dlc16_ritual_rebirth_saison_athel_loren']),
]


# Lot 9 (donnees_campagne.py --lot etape9), 23.09.2026, 04 h : chantiers 4 et 9 (tables du STARTPOS, à passer dans
# zz_startpos_db.pack par la construction, puis régénérer : même startpos que la minicarte et les seigneurs jouables).
# 34 lignes, sauvegarde db-backups\<date>-donnees-campagne. Horde de Morghur, traits et objet de départ des 6 seigneurs
# légendaires, « Relever les morts » des Comtes vampires dans nos 26 provinces.
SEIGNEURS_DE_DEPART = ['2140783885', '2140783843', '2140783911', '2140783762', '2140783791', '2140784082']
STARTPOS_LOT9 = [
    ('start_pos_horde_details', 'start_pos_horde_details_tables', 'general', SEIGNEURS_DE_DEPART),
    ('start_pos_character_traits', 'start_pos_character_traits_tables', 'character_id', SEIGNEURS_DE_DEPART),
    ('start_pos_character_ancillaries', 'start_pos_character_ancillaries_tables', 'character_id', SEIGNEURS_DE_DEPART),
    ('province_to_mercenary_set_junctions', 'province_to_mercenary_set_junctions_tables', 'province', 'wh_dlc05_'),
]
# la réserve de « Relever les morts » est aussi lue en jeu : dans le pack principal
TABLES_LOT9 = [STARTPOS_LOT9[3]]

# Lot 13 (23.09.2026, 14 h 25, ajout de la session de construction) : régiments de renom du Duc rouge, ligne du kit
# `faction_to_mercenary_set_junctions` (Mousillon -> wh_dlc04_vmp_units_of_renown_pool, comme Kemmler chez CA), lue à la
# génération du startpos (pack principal chargé avec zz_startpos_db) et en jeu. Sans cette entrée, elle n'entrait pas.
# 25.09.2026 (audit de compatibilité) : le filtre « faction = Mousillon » prenait aussi trois lignes que CA livre elle-même
# en 9.0 (wh3_dlc29_vmp_additional_units, _raise_dead_faction, _raise_dead_province ; absentes du kit, présentes dans son
# db) : doublons de clés de CA dans notre pack. Seule notre ligne, les régiments de renom, part désormais.
# 25.09.2026, 21 h (première mise à jour de la bêta, compatibilité ; Charles : « que tout cohabite ») : la ligne sort du
# pack. faction_to_mercenary_set_junctions n'a pas de colonne de campagne : elle donnait ces régiments à Mousillon AUX
# EMPIRES aussi. Ils sont désormais donnés par script dans notre seule campagne (saison_duc.lua, section 9). La ligne
# reste dans le kit (et dans zz_startpos_db.pack jusqu'à sa prochaine synchronisation, construction).
TABLES_LOT13 = []


# Lot 18 (23.09.2026, 16 h 30) : monuments ; gabarits à nous (clés wh_dlc05_mini_special_*, donnees_campagne.lot_etape18).
# build_pack réunit plusieurs entrées d'une même table (celle de declarer_gabarits_elfes et celle-ci) dans un seul fichier.
TABLES_LOT18 = [
    ('slot_templates', 'slot_templates_tables', 'key', 'wh_dlc05_mini_special_'),
    ('slot_template_permitted_building_chains', 'slot_template_permitted_building_chains_tables', 'slot_template',
     'wh_dlc05_mini_special_'),
]


# Lot 19 (23.09.2026, 16 h 30) : Racines du monde (rituels de téléportation entre nos clairières, donnees_campagne.lot_etape19)
TABLES_LOT19 = [
    ('region_groups', 'region_groups_tables', 'group_key', 'saison_racines_'),
    ('regions_to_region_groups_junctions', 'regions_to_region_groups_junctions_tables', 'region_group', 'saison_racines_'),
    ('rituals', 'rituals_tables', 'key', 'saison_racines_'),
    ('ritual_payloads', 'ritual_payloads_tables', 'key', 'saison_racines_'),
    ('ritual_payload_teleport_armies', 'ritual_payload_teleport_armies_tables', 'payload', 'saison_racines_'),
    ('ritual_targets', 'ritual_targets_tables', 'key', 'saison_racines_'),
    ('ritual_military_force_target_criterias', 'ritual_military_force_target_criterias_tables', 'key', 'saison_racines_'),
]


# Lot 20 (23.09.2026, 16 h 45) : nos citations de chargement (donnees_campagne.lot_etape20) ; leur rattachement à notre
# carte passe par l'entrée loading_screen_quotes_to_campaigns du lot 1
TABLES_LOT20 = [
    ('loading_screen_quotes', 'loading_screen_quotes_tables', 'key', 'saison_citation_'),
]


# Lot 17 (23.09.2026) : bonus d'IA selon la difficulté, à notre campagne (donnees_campagne.lot_etape17) ;
# les tables start_pos_* du lot vont au startpos (construction)
TABLES_LOT17 = [
    ('faction_potential_difficulty_overrides', 'faction_potential_difficulty_overrides_tables', 'campaign_key', 'wh_dlc05_wood_elves'),
]


# Lot 21 (23.09.2026) : monuments du lore (donnees_campagne.lot_etape21) ; tables building_* neuves pour nous
TABLES_LOT21 = [
    ('building_superchains', 'building_superchains_tables', 'key', 'wh_dlc05_mini_'),
    ('building_chains', 'building_chains_tables', 'key', 'wh_dlc05_mini_'),
    ('building_chain_availability_sets', 'building_chain_availability_sets_tables', 'building_chain', 'wh_dlc05_mini_'),
    ('building_instances', 'building_instances_tables', 'key', 'wh_dlc05_mini_'),
    ('building_levels', 'building_levels_tables', 'level_name', 'wh_dlc05_mini_'),
    ('building_culture_variants', 'building_culture_variants_tables', 'building', 'wh_dlc05_mini_'),
    ('building_effects_junction', 'building_effects_junction_tables', 'building', 'wh_dlc05_mini_'),
    ('building_set_to_building_junctions', 'building_set_to_building_junctions_tables', 'building_chain', 'wh_dlc05_mini_'),
    ('cai_construction_system_building_values', 'cai_construction_system_building_values_tables', 'building_chain', 'wh_dlc05_mini_'),
    ('building_short_description_texts', 'building_short_description_texts_tables', 'key', 'wh_dlc05_mini_'),
    ('building_flavour_texts', 'building_flavour_texts_tables', 'key', 'wh_dlc05_mini_'),
]


# Lot 40 (donnees_campagne.py --lot etape40), 25.09.2026 : la branche de technologies du Duc écarlate (mécanique F), 42
# lignes dans SIX tables neuves pour notre pack. EN ATTENTE : le nom sans préfixe TABLES_LOT les tient hors de build_pack
# jusqu'à un essai de démarrage dédié (erreur 107), à renommer TABLES_LOT40 par la Construction quand elle le fait. Essai :
# le Duc (onglet « Les Dragons de Sang », 8 nœuds), puis Kemmler (onglet absent), puis les Empires (aucun nœud chez
# Mousillon). Nœuds à faction ET campagne : jamais vu chez CA.
EN_ATTENTE_TABLES_LOT40 = [
    ('technologies', 'technologies_tables', 'key', 'saison_duc_tech_'),
    ('technology_nodes', 'technology_nodes_tables', 'key', 'saison_duc_tech_'),
    ('technology_node_links', 'technology_node_links_tables', 'child_key', 'saison_duc_tech_'),
    ('technology_effects_junction', 'technology_effects_junction_tables', 'technology', 'saison_duc_tech_'),
    ('technology_ui_tabs', 'technology_ui_tabs_tables', 'key', ['saison_duc_vmp_dragons_de_sang']),
    ('technology_ui_tabs_to_technology_nodes_junctions', 'technology_ui_tabs_to_technology_nodes_junctions_tables', 'tab',
     ['saison_duc_vmp_dragons_de_sang']),
]


# Lot 22 (23.09.2026) : événements des lieux du lore (donnees_campagne.lot_etape22, saison_lieux.lua)
# EN ATTENTE (24.09.2026, restauration 9.0) : saison_lieux.lua n'est pas chargé par required.lua et ces tables n'ont
# jamais été dans un pack joué ; le nom sans préfixe TABLES_LOT les tient hors de build_pack jusqu'à leur essai de
# démarrage (erreur 107). Les lignes restent dans le kit.
EN_ATTENTE_TABLES_LOT22 = [
    ('dilemmas', 'dilemmas_tables', 'key', 'saison_lieux_'),
    ('cdir_events_dilemma_choice_details', 'cdir_events_dilemma_choice_details_tables', 'dilemma_key', 'saison_lieux_'),
    ('cdir_events_dilemma_option_junctions', 'cdir_events_dilemma_option_junctions_tables', 'dilemma_key', 'saison_lieux_'),
    ('incidents', 'incidents_tables', 'key', 'saison_lieux_'),
    ('cdir_events_incident_option_junctions', 'cdir_events_incident_option_junctions_tables', 'incident_key', 'saison_lieux_'),
    ('effect_bundles', 'effect_bundles_tables', 'key', 'saison_lieux_'),
]

# Lot 26 (donnees_campagne.py --lot etape26), 23.09.2026, 23 h 06 : poste de chef de faction de nos 7 factions elfes de
# WH1 (plantage du tour 11). Une seule entrée pour cette table.
TABLES_LOT26 = [
    ('ministerial_positions_culture_details', 'ministerial_positions_culture_details_tables', 'faction_key',
     ['wh_dlc05_wef_anmyr', 'wh_dlc05_wef_arranoc', 'wh_dlc05_wef_atylwyth', 'wh_dlc05_wef_cavaroc',
      'wh_dlc05_wef_fyr_darric', 'wh_dlc05_wef_modryn', 'wh_dlc05_wef_tirsyth']),
]

# Lot 32 (donnees_campagne.py --lot etape32), 24.09.2026, 21 h 30 : incident illustré du tombeau de Galand
# (saison_duc.lua). Premières tables d'incidents dans un pack joué : essai de démarrage au premier pack (erreur 107).
# Lot 33 (donnees_campagne.py --lot etape33), 25.09.2026 : Krell, Dieter Helsnicht et Walach Harkon permis à Mousillon
# (lignes neuves, clé faction + agent + sous-type). Filtre par ligne entière (4e forme de build_pack.kit_rows, ajoutée
# par la construction le 25.09) : seulement nos trois lignes, jamais celles de CA pour Mousillon.
HEROS_MOUSILLON_LOT33 = {'wh3_dlc29_vmp_krell', 'wh3_dlc29_vmp_dieter_helsnicht', 'wh3_dlc29_vmp_walach_harkon'}
TABLES_LOT33 = [
    ('faction_agent_permitted_subtypes', 'faction_agent_permitted_subtypes_tables', 'faction',
     lambda d: d.get('faction') == 'wh_main_vmp_mousillon' and d.get('subtype') in HEROS_MOUSILLON_LOT33),
]

# Lot 34 (donnees_campagne.py --lot etape34), 25.09.2026 : paquets d'effets du Duc écarlate (le duché perdu, la faveur
# d'Abhorash ; saison_duc.lua). Table effect_bundles neuve dans un pack joué : essai de démarrage (erreur 107).
TABLES_LOT34 = [
    ('effect_bundles', 'effect_bundles_tables', 'key', 'saison_duc_'),
]

# Lot 35 (donnees_campagne.py --lot etape35), 25.09.2026 : dilemmes du Duc écarlate (l'impôt du sang, le serment du
# sang ; saison_duc.lua), recette du lot 22. Tables neuves dans un pack joué : essai de démarrage (erreur 107).
TABLES_LOT35 = [
    ('dilemmas', 'dilemmas_tables', 'key', 'saison_duc_'),
    ('cdir_events_dilemma_choice_details', 'cdir_events_dilemma_choice_details_tables', 'dilemma_key', 'saison_duc_'),
    ('cdir_events_dilemma_option_junctions', 'cdir_events_dilemma_option_junctions_tables', 'dilemma_key',
     'saison_duc_'),
]

# Lot 38 (donnees_campagne.py --lot etape38), 25.09.2026 : trait de faction de Grom à notre clé (sans « Waaagh contre
# Ulthuan ! » ; effets posés par saison_grom.lua). Réunie avec l'entrée du lot 34 par build_pack.
TABLES_LOT38 = [
    ('effect_bundles', 'effect_bundles_tables', 'key', ['saison_lord_trait_grom']),
]

# Lot 43 (donnees_campagne.py --lot etape43), 25.09.2026 : les quatre groupes d'indices de l'IA à nous
# (saison_cai_region_hint_*, revue du pack B1). Nos régions y passent : l'entrée du lot 1 (regions_to_region_groups,
# région wh_dlc05_) les porte déjà. cai_personality_region_group_policy_junctions : TABLE NEUVE, essai de démarrage.
TABLES_LOT43 = [
    ('region_groups', 'region_groups_tables', 'group_key', ['saison_cai_region_hint_area_bretonnia',
                                                            'saison_cai_region_hint_area_athel_loren',
                                                            'saison_cai_region_hint_area_dwarf_empire',
                                                            'saison_cai_region_hint_sub_area_western_mountains']),
    ('cai_personality_region_group_policy_junctions', 'cai_personality_region_group_policy_junctions_tables',
     'region_group_key', 'saison_cai_'),
]

# Lot 42 (donnees_campagne.py --lot etape42), 25.09.2026 : trait de faction du Duc écarlate, « Tyran d'Aquitanie »
# (effets posés par saison_duc.lua, section 8) et ses quatre lignes « A accès à … ». effects : table NEUVE dans un pack
# joué, essai de démarrage du Duc avant toute annonce (erreur 107). effect_bundles : réunie avec les lots 34 et 38.
TABLES_LOT42 = [
    ('effects', 'effects_tables', 'effect', ['saison_duc_effect_duche_perdu_dummy',
                                             'saison_duc_effect_faveur_abhorash_dummy',
                                             'saison_duc_effect_impot_du_sang_dummy',
                                             'saison_duc_effect_decret_de_richemont_dummy']),
    ('effect_bundles', 'effect_bundles_tables', 'key', ['saison_lord_trait_duc']),
]

# Lot 39 (donnees_campagne.py --lot etape39), 25.09.2026 : « Les Racines du monde s'ouvrent » et « La Reine apparaît »
# à nos clés (saison_foret.lua). Réunies avec les entrées du lot 32 par build_pack.
INCIDENTS_LOT39 = ['saison_racines_du_monde_ouvertes', 'saison_ariel_arrive']
TABLES_LOT39 = [
    ('incidents', 'incidents_tables', 'key', INCIDENTS_LOT39),
    ('cdir_events_incident_option_junctions', 'cdir_events_incident_option_junctions_tables', 'incident_key',
     INCIDENTS_LOT39),
]

TABLES_LOT32 = [
    ('incidents', 'incidents_tables', 'key', 'saison_duc_'),
    ('cdir_events_incident_option_junctions', 'cdir_events_incident_option_junctions_tables', 'incident_key',
     'saison_duc_'),
]
