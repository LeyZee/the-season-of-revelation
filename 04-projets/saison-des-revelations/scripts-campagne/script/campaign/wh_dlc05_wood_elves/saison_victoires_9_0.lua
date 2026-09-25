-----------------------------------------------------------------------------------
--	Victoires par seigneur au format de la mise à jour 9.0, dédiées à la Saison, pour les dix seigneurs de notre carte.
--
--	24.09.2026 (1re version, soir) : listes de CA 9.0 ramenées à la carte pour les huit seigneurs de WH3.
--	24.09.2026 (réécriture) : listes de la Saison pour les dix seigneurs, spécification validée par Charles
--	05-journal\2026-09-24-vampires-9.0\proposition-victoires-saison.md (§ 2 : listes, sources de chaque objectif ;
--	§ 2.11 : ce qu'il faut coder). Décisions de Charles (§ 3) : Orion et Durthu passent au modèle de CA, leur victoire de
--	WH1 devient leur victoire LONGUE, qui ne termine pas la partie (la cinématique joue et remplit delay_victory, la partie
--	continue), avec une courte neuve et les postes de rang 15 gardés ; Duc écarlate L3 = l'Aquitanie et Quenelles ; Grom
--	garde « piller Brionne » et « piller Quenelles ». Par défaut (recommandations du document) : Kemmler C4 = Château de
--	Gasconnie seul ; Drycha L3 = Parravon et Quenelles ; nos monuments du lot 21 remplacent les repères de CA ; seuils du
--	tableau ; payloads du Duc = vmp_lair_builder en courte, ceux des vampires de CA en longue.
--	Comme CA : victoire courte et victoire longue récompensées sans finir la partie ; domination (27 colonies sur nos 57,
--	la proportion de CA : 272 sur 572) = seule fin de partie.
--
--	Moteur (règle du projet : les systèmes de CA chargés depuis leur dossier, jamais recopiés) : required.lua charge
--	main_warhammer\victory_objectives_config_utils.lua (générateurs d'objectifs, aides victory_objectives_scripted_listeners)
--	et victory_objectives_config.lua (création des missions, écouteurs, incidents et récompenses) ; ici, au chargement :
--	  - la construction de la table des Empires (écouteur WorldCreated « InitializeVictoryObjectivesIEConfig ») est
--	    retirée : ses régions, provinces et groupes de régions n'existent pas chez nous ;
--	  - _victory_objectives_ie.config est remplacée par nos dix listes (générateurs de CA, payloads de CA) ;
--	  - initialise_victory_missions de CA est enveloppée (pcall : son rappel de premier tour n'est pas protégé, et une
--	    erreur y sauterait tous les rappels suivants) ; rien en multijoueur, comme saison_victoire.lua ;
--	  - écouteurs : ceux de CA pour Albéric et Grom (sans carte), les nôtres pour les huit autres, par les aides de CA
--	    avec nos régions, notre rituel de Renaissance et nos clés de mission ; la finale de la chronique de chaque seigneur
--	    de WH3 (saison_chroniques.lua, dernière étape) est un objectif de sa victoire longue.
--	saison_victoires_9_0_ecouteurs() est appelée à chaque chargement par saison_start.lua.
--
--	Orion et Durthu : leur longue reprend la mission de WH1 (wh_main_long_victory, même clé) ; « La fin de la Saison »
--	(delay_victory) y reste, remplie par saison_cinematique_de_fin (saison_victoire.lua). Le moteur de CA n'ajoute
--	game_victory qu'à la domination et au multijoueur : leur longue ne termine plus la partie.
--
--	Parties commencées avant ce changement : le rappel de CA ne joue qu'en partie neuve et la valeur sauvée
--	IEVictoryConditionUseDLC29Config y manque ; elles gardent leurs missions d'alors (saison_victoire.lua pour les
--	parties d'avant la 9.0 ; première version de ce fichier pour celles du 24.09 au soir).
-----------------------------------------------------------------------------------

local ORION = "wh_dlc05_wef_wood_elves";
local DURTHU = "wh_dlc05_wef_argwylon";
local ALBERIC = "wh_main_brt_bordeleaux";
local FEE = "wh_main_brt_carcassonne";
local HARDE = "wh_dlc05_bst_morghur_herd";
local DUC = "wh_main_vmp_mousillon";
local DRYCHA = "wh2_dlc16_wef_drycha";
local KEMMLER = "wh2_dlc11_vmp_the_barrow_legion";
local GROM = "wh2_dlc15_grn_broken_axe";
local SOEURS = "wh2_dlc16_wef_sisters_of_twilight";

local COURTE = "wh_main_short_victory";
local LONGUE = "wh_main_long_victory";
local CHENE = "wh_dlc05_oak_of_ages";

-- les cinq provinces d'Athel Loren (Yn Edri Eternos = notre province du Chêne)
local PROVINCES_ATHEL_LOREN = {"wh_dlc05_argwylon", "wh_dlc05_wydrioth", "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn",
	"wh_dlc05_torgovann"};

-- les cinq Grandes Salles tombées de WH1 (ruines sans maître au départ)
local SALLES_TOMBEES = {"wh_dlc05_anmyr_tal_rond", "wh_dlc05_fyr_darric_threllock", "wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_tal_jul_finel"};

-- duchés bretons de la carte et leur capitale (réveil des ducs par la Fée ; même liste que saison_chroniques.lua)
local DUCHES = {
	{"wh_dlc05_brt_quenelles", "wh_dlc05_quenelles_quenelles"},
	{"wh_dlc05_brt_brionne", "wh_dlc05_brionne_brionne"},
	{"wh_main_brt_parravon", "wh_dlc05_parravon_parravon"},
	{"wh3_main_brt_aquitaine", "wh_dlc05_aquitaine_chateau_depee"},
	{"wh_main_brt_bastonne", "wh_dlc05_bastonne_castle_bastonne"},
	{"wh_dlc05_brt_montfort", "wh_dlc05_montfort_montfort"},
	{"wh_dlc05_brt_gisoroux", "wh_dlc05_gisoreux_gisoreux"},
	{ALBERIC, "wh_dlc05_bordeleaux_bordeleaux"}
};

-- notre rituel de Renaissance et notre santé de la forêt (saison_foret.lua, chargé avant)
local function rituel_renaissance()
	return SAISON_RITUEL_RENAISSANCE or "wh2_dlc16_ritual_rebirth_saison_athel_loren";
end;
local RESSOURCE_FORET = SAISON_RESSOURCE_FORET or "wef_worldroots_saison_athel_loren";

-- finale de la chronique de chaque seigneur de WH3 (dernière étape de sa chaîne, saison_chroniques.lua) : mission
-- réussie -> objectif scripté de la victoire longue
local FINALES = {
	[ALBERIC] = "saison_chronique_alberic_5",
	[FEE] = "saison_chronique_fee_5",
	[HARDE] = "saison_chronique_morghur_5",
	[DUC] = "saison_chronique_duc_5",
	[DRYCHA] = "saison_chronique_drycha_4",
	[KEMMLER] = "saison_chronique_kemmler_4",
	[GROM] = "saison_chronique_grom_4",
	[SOEURS] = "saison_chronique_soeurs_5"
};
local OBJECTIFS_FINALE = {
	[ALBERIC] = "saison_victoire_finale_alberic",
	[FEE] = "saison_victoire_finale_fee",
	[HARDE] = "saison_victoire_finale_morghur",
	[DUC] = "saison_victoire_finale_duc",
	[DRYCHA] = "saison_victoire_finale_drycha",
	[KEMMLER] = "saison_victoire_finale_kemmler",
	[GROM] = "saison_victoire_finale_grom",
	[SOEURS] = "saison_victoire_finale_soeurs"
};

-- postes de rang 15 (Orion, Durthu) : objectif et texte de CA
local POSTES = {
	[ORION] = {total = 6, cle = "wh3_dlc29_wef_orion_fill_all_offices_with_rank_15_characters",
		texte = "mission_text_text_wh3_dlc29_wef_fill_all_offices_with_rank_15_characters"},
	[DURTHU] = {total = 4, cle = "wh3_dlc29_wef_durthu_fill_all_offices_with_rank_15_characters",
		texte = "mission_text_text_wh3_dlc29_wef_fill_all_durthu_offices_with_rank_15_characters"}
};

local installee = false;
local SAISON_LISTES = {};


-- Les fichiers de CA sont-ils là ? (required.lua les charge sous pcall)
local function ca_present()
	return is_table(_victory_objectives_ie)
		and is_function(_victory_objectives_ie.initialise_victory_missions)
		and is_function(_victory_objectives_ie.add_scripted_victory_listeners)
		and is_table(_victory_objectives_ie.listeners)
		and is_function(generate_SCRIPTED_MISSION_objective)
		and is_table(victory_objectives_scripted_listeners);
end;


-- objectif « finale de la chronique » de la victoire longue
local function objectif_finale(faction_key)
	return generate_SCRIPTED_MISSION_objective(OBJECTIFS_FINALE[faction_key],
		"mission_text_text_" .. OBJECTIFS_FINALE[faction_key]);
end;

-- victoire de domination, la même pour les dix
local function domination()
	return {
		objectives = {
			generate_OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS_objective(27)
		}
	};
end;

-- longue d'Orion et de Durthu : la victoire de WH1 (saison_victoire.lua) et les postes de rang 15
local function longue_wh1(faction_key)
	return {
		objectives = {
			generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
			generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_perform_oak_of_ages_rebirth", "mission_text_text_wh3_dlc29_wef_perform_ritual_of_rebirth_atel_loren_long"),
			generate_CONSTRUCT_BUILDINGS_INCLUDING_objective(1, faction_key, {"wh_dlc05_wef_oak_of_ages_5"}),
			generate_DO_NOT_LOSE_REGION_objective({CHENE}),
			generate_FIGHT_SET_PIECE_BATTLE_objective("wh_dlc05_qb_wef_grand_silver_spire"),
			generate_SCRIPTED_MISSION_objective("delay_victory", "mission_text_text_wh_dlc05_mini_delay_victory"),
			generate_SCRIPTED_MISSION_objective(POSTES[faction_key].cle, POSTES[faction_key].texte, POSTES[faction_key].total, 0, true)
		},
		payloads = {
			effect_bundle = {"wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
				"wh3_dlc29_bundle_ie_victory_objective_wef_forest_builder"}
		}
	};
end;


-- Nos dix listes, au format de CA (config.factions) ; spécification § 2.1 à 2.10. Chaque entrée courte ou longue a au
-- moins un payload (sans payload, la mission de CA ne se génère pas). Payloads de CA.
local function construire_listes()
	return {
		-- § 2.1 Orion
		[ORION] = {
			short = {
				objectives = {
					generate_CONTROL_N_REGIONS_INCLUDING_objective(SALLES_TOMBEES, 3),
					generate_HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective(RESSOURCE_FORET, 200, false, "mission_text_text_saison_victoire_sante_foret_200"),
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold"),
					generate_DEFEAT_N_ARMIES_OF_FACTION_objective(6, nil, "wh_dlc03_sc_bst_beastmen")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_wef_forest_health_boost",
					scripted_reward = "dummy_wh3_dlc29_wef_orion_victory_objective_short"
				}
			},
			long = longue_wh1(ORION),
			domination = domination()
		},

		-- § 2.2 Durthu
		[DURTHU] = {
			short = {
				objectives = {
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_durthu_upgrade_n_forest_spirits_with_aspects",
						"mission_text_text_wh3_dlc29_wef_durthu_upgrade_n_forest_spirits_with_aspects", 15, 0, true),
					generate_HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective(RESSOURCE_FORET, 200, false, "mission_text_text_saison_victoire_sante_foret_200"),
					generate_CONTROL_N_REGIONS_INCLUDING_objective({"wh_dlc05_fyr_darric_threllock", "wh_dlc05_torgovann_vauls_anvil"}, 2),
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_wef_forest_health_boost",
					scripted_reward = "dummy_wh3_dlc29_wef_durthu_victory_objective_short"
				}
			},
			long = longue_wh1(DURTHU),
			domination = domination()
		},

		-- § 2.3 Albéric de Bordeleaux
		[ALBERIC] = {
			short = {
				objectives = {
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_bordeleaux_grail_vow", "mission_text_text_mis_activity_complete_grail_vow_alberic"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_reach_n_chivalry_level_short", "mission_text_text_wh3_dlc29_reach_n_chivalry_level_short"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_alberic_turris", "mission_text_text_saison_victoire_alberic_turris"),
					generate_DEFEAT_N_ARMIES_OF_FACTION_objective(3, nil, "wh_main_sc_vmp_vampire_counts")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_brt_town_crier",
					ancillary = "wh3_dlc29_anc_follower_brt_experienced_sailor"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_bordeleaux_3_grail_vows", "mission_text_text_wh3_dlc29_bordeleaux_3_grail_vows", 3, 0, true),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_reach_n_chivalry_level_long", "mission_text_text_wh3_dlc29_reach_n_chivalry_level_long"),
					generate_DESTROY_FACTION_objective({DUC}, true),
					objectif_finale(ALBERIC)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
						"wh3_dlc29_bundle_ie_victory_objective_brt_dedicated_characters_dummy"}
				}
			},
			domination = domination()
		},

		-- § 2.4 la Fée Enchanteresse
		[FEE] = {
			short = {
				objectives = {
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_carcassonne_virtue_thoth", "mission_text_text_mis_activity_complete_troth_of_virute_vow_enchantress"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_reach_n_chivalry_level_short", "mission_text_text_wh3_dlc29_reach_n_chivalry_level_short"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_brt_construct_landmark_short", "mission_text_text_wh3_dlc29_brt_fay_construct_landmark_short"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_fee_ducs", "mission_text_text_saison_victoire_fee_ducs")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_brt_town_crier",
					scripted_reward = "dummy_wh3_dlc29_brt_fay_victory_objective_short"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_carcassonne_complete_n_virtue_thoths", "mission_text_text_wh3_dlc29_carcassonne_complete_n_virtue_thoths", 3, 0, true),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_reach_n_chivalry_level_long", "mission_text_text_wh3_dlc29_reach_n_chivalry_level_long"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_fee_chapelle", "mission_text_text_saison_victoire_fee_chapelle"),
					generate_DESTROY_FACTION_objective({GROM}, true),
					objectif_finale(FEE)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
						"wh3_dlc29_bundle_ie_victory_objective_brt_dedicated_characters_dummy"}
				}
			},
			domination = domination()
		},

		-- § 2.5 Morghur
		[HARDE] = {
			short = {
				objectives = {
					generate_HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective("bst_ruination", 60, true, "mission_text_text_wh3_dlc29_bst_reach_ruination_tier_short"),
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh_dlc05_qb_bst_morghur_stave_of_ruinous_corruption"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_morghur_val", "mission_text_text_saison_victoire_morghur_val"),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({"wh_dlc05_montfort_montfort"}, 1)
				},
				payloads = {
					scripted_reward = "dummy_wh3_dlc29_bst_morghur_victory_objective_short",
					ancillary = "wh3_dlc29_anc_bst_talisman_of_dark_gods"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective("bst_ruination", 150, true, "mission_text_text_wh3_dlc29_bst_reach_ruination_tier_long"),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({CHENE}, 1),
					generate_DESTROY_FACTION_objective({ORION, DURTHU}, true),
					objectif_finale(HARDE)
				},
				payloads = {
					pooled_resource = {{"bst_herdstone_shard", "wh2_dlc17_bst_herdstone_shard_gain_abandon_settlement", 2}},
					effect_bundle = "wh3_dlc29_ie_victory_conditions_lord_recruit_rank_bundle"
				}
			},
			domination = domination()
		},

		-- § 2.6 le Duc écarlate (CA ne lui donne aucune liste : format et mécaniques des vampires de CA 9.0)
		[DUC] = {
			short = {
				objectives = {
					generate_CONTROL_N_PROVINCES_INCLUDING_objective({"wh_dlc05_aquitaine"}, 1),
					generate_SCRIPTED_MISSION_objective("saison_victoire_duc_tombeau", "mission_text_text_saison_victoire_duc_tombeau"),
					generate_PERFORM_RITUAL_BY_CATEGORY_objective("VAMPIRE_PROVINCE", 5, "mission_text_text_wh3_dlc29_vmp_use_shyish_actions")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_vmp_lair_builder"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_PERFORM_RITUAL_BY_CATEGORY_objective("VAMPIRE_PROVINCE", 10, "mission_text_text_wh3_dlc29_vmp_use_shyish_actions"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_duc_eveil", "mission_text_text_saison_victoire_duc_eveil", 2, 0, true),
					generate_DESTROY_FACTION_objective({"wh3_main_brt_aquitaine", "wh_dlc05_brt_quenelles"}, true, true),
					generate_SCRIPTED_MISSION_objective("saison_victoire_duc_palais", "mission_text_text_saison_victoire_duc_palais"),
					objectif_finale(DUC)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_bundle_ie_victory_objective_vmp_long_victory",
						"wh3_dlc29_ie_victory_conditions_characters_recruit_rank_bundle"}
				}
			},
			domination = domination()
		},

		-- § 2.7 Drycha
		[DRYCHA] = {
			short = {
				objectives = {
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_drycha_unlock_coeddil", "mission_text_text_wh3_dlc29_wef_drycha_unlock_coeddil"),
					generate_RECRUIT_N_UNITS_FROM_objective({"wh2_dlc16_wef_mon_giant_spiders_0", "wh3_main_monster_feral_bears",
						"wh2_dlc16_wef_mon_wolves_0", "wh2_dlc16_wef_mon_cave_bats", "wh2_dlc16_wef_inf_malicious_dryads_0",
						"wh2_dlc16_wef_mon_hawks_0", "wh2_dlc16_wef_mon_feral_manticore"},
						7, false, "mission_text_text_wh3_dlc29_wef_drycha_recruit_n_wild_spirits_short", true),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_construct_landmark_short", "mission_text_text_saison_victoire_drycha_addaivoch"),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({"wh_dlc05_parravon_parravon",
						"wh_dlc05_parravon_montlac", "wh_dlc05_parravon_grunere"}, 2)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_bundle_ie_victory_objective_wef_forest_health_boost",
						"wh3_dlc29_bundle_ie_victory_objective_wef_forest_wild_spirits_rank"}
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_CONTROL_N_PROVINCES_INCLUDING_objective(PROVINCES_ATHEL_LOREN, 5),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_perform_oak_of_ages_rebirth", "mission_text_text_wh3_dlc29_wef_perform_ritual_of_rebirth_atel_loren_long"),
					generate_DESTROY_FACTION_objective({"wh_main_brt_parravon", "wh_dlc05_brt_quenelles"}, true),
					objectif_finale(DRYCHA)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
						"wh3_dlc29_bundle_ie_victory_objective_wef_forest_builder"}
				}
			},
			domination = domination()
		},

		-- § 2.8 Heinrich Kemmler
		[KEMMLER] = {
			short = {
				objectives = {
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh_main_qb_vmp_heinrich_kemmler_skull_staff_stage_3_la_maisontaal_abbey"),
					generate_PERFORM_RITUAL_BY_CATEGORY_objective("VAMPIRE_PROVINCE", 5, "mission_text_text_wh3_dlc29_vmp_use_shyish_actions"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_vmp_kemmler_build_landmark_short", "mission_text_text_saison_victoire_kemmler_krell"),
					generate_CONTROL_N_REGIONS_INCLUDING_objective({"wh_dlc05_carcassonne_castle_carcassonne"}, 1)
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_vmp_vengeful_spirits",
					ancillary = "wh3_dlc29_anc_vmp_follower_wraithbringer"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_PERFORM_RITUAL_BY_CATEGORY_objective("VAMPIRE_PROVINCE", 10, "mission_text_text_wh3_dlc29_vmp_use_shyish_actions"),
					generate_DESTROY_FACTION_objective({"wh_dlc05_brt_quenelles"}, true, true),
					generate_DESTROY_FACTION_objective({DURTHU}, true),
					objectif_finale(KEMMLER)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_bundle_ie_victory_objective_vmp_long_victory",
						"wh3_dlc29_ie_victory_conditions_characters_recruit_rank_bundle"}
				}
			},
			domination = domination()
		},

		-- § 2.9 Grom la Panse
		[GROM] = {
			short = {
				objectives = {
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_grn_grom_unlock_all_ingridient_slots_short", "mission_text_text_wh3_dlc29_grn_grom_unlock_all_ingridient_slots_short"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_grn_grom_win_wagh_short", "mission_text_text_wh3_dlc29_grn_grom_win_wagh_short"),
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh2_dlc15_qb_grn_grom_axe_of_grom_stage_4"),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({"wh_dlc05_brionne_brionne"}, 1)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_ie_victory_conditions_grn_trophy_cabinet", "wh3_dlc29_ie_victory_conditions_grn_old_knives"}
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_grn_grom_cook_unique_recipes_long", "mission_text_text_wh3_dlc29_grn_grom_cook_unique_recipes_long", 15, 0, true),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_grn_grom_win_wagh_1_long", "mission_text_text_wh3_dlc29_mission_win_wagh_of_any_type", 4, 0, true),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({"wh_dlc05_grey_mountains_2_karak_ziflin",
						"wh_dlc05_grey_mountains_2_karak_tzor", "wh_dlc05_grey_mountains_2_blackstone_post"}, 2),
					generate_RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING_objective({"wh_dlc05_quenelles_quenelles"}, 1),
					objectif_finale(GROM)
				},
				payloads = {
					effect_bundle = "wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
					pooled_resource = {{"grn_salvage", "missions", 1000}}
				}
			},
			domination = domination()
		},

		-- § 2.10 les Sœurs du Crépuscule
		[SOEURS] = {
			short = {
				objectives = {
					generate_CONTROL_N_REGIONS_INCLUDING_objective({"wh_dlc05_wydrioth_tal_jul_finel"}, 1),
					generate_CONTROL_N_REGIONS_INCLUDING_objective({"wh_dlc05_torgovann_vauls_anvil"}, 1),
					generate_SPEND_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective(20, "wef_forge_daiths_favour", nil, "forging_items"),
					generate_FIGHT_SET_PIECE_BATTLE_objective("wh2_dlc16_qb_wef_sisters_dragon")
				},
				payloads = {
					effect_bundle = "wh3_dlc29_bundle_ie_victory_objective_wef_forest_health_boost",
					scripted_reward = "dummy_wh3_dlc29_wef_sisters_victory_objective_short"
				}
			},
			long = {
				objectives = {
					generate_SCRIPTED_COMPLETE_SHORT_VICTORY_objective(),
					generate_SPEND_AT_LEAST_X_OF_A_POOLED_RESOURCE_objective(60, "wef_forge_daiths_favour", nil, "forging_items"),
					generate_SCRIPTED_MISSION_objective("wh3_dlc29_wef_perform_oak_of_ages_rebirth", "mission_text_text_wh3_dlc29_wef_perform_ritual_of_rebirth_atel_loren_long"),
					generate_SCRIPTED_MISSION_objective("saison_victoire_soeurs_porte_du_roi", "mission_text_text_saison_victoire_soeurs_porte_du_roi"),
					generate_DESTROY_FACTION_objective({HARDE}, true),
					objectif_finale(SOEURS)
				},
				payloads = {
					effect_bundle = {"wh3_dlc29_ie_victory_conditions_global_recruitement_reward_bundle",
						"wh3_dlc29_bundle_ie_victory_objective_wef_forest_builder"}
				}
			},
			domination = domination()
		}
	};
end;


-----------------------------------------------------------------------------------
--	Écouteurs des objectifs scriptés (appelés par add_scripted_victory_listeners de CA, pour le seul humain)
-----------------------------------------------------------------------------------

-- le personnage d'un sous-type dans une faction
local function personnage(faction_key, sous_type)
	local f = cm:get_faction(faction_key);
	if not f or f:is_dead() then
		return false;
	end;
	local liste = f:character_list();
	for i = 0, liste:num_items() - 1 do
		local c = liste:item_at(i);
		if c:character_subtype_key() == sous_type then
			return c;
		end;
	end;
	return false;
end;

-- un objectif rempli une seule fois (valeur sauvée)
local function remplir_une_fois(faction_key, mission, cle)
	local sauve = "saison_victoires_9_0_fait_" .. faction_key .. "_" .. cle;
	if cm:get_saved_value(sauve) then
		return;
	end;
	cm:set_saved_value(sauve, true);
	cm:complete_scripted_mission_objective(faction_key, mission, cle, true);
end;

local function deja_rempli(faction_key, cle)
	return cm:get_saved_value("saison_victoires_9_0_fait_" .. faction_key .. "_" .. cle) == true;
end;

-- finale de la chronique réussie -> objectif de la victoire longue
local function ecouteur_finale(faction_key)
	local mission = FINALES[faction_key];
	local objectif = OBJECTIFS_FINALE[faction_key];
	if not (mission and objectif) then
		return;
	end;
	saison_ecouteur(
		"saison_victoires_9_0_finale_" .. faction_key,
		"MissionSucceeded",
		function(context)
			return context:faction():name() == faction_key and context:mission():mission_record_key() == mission;
		end,
		function()
			cm:complete_scripted_mission_objective(faction_key, LONGUE, objectif, true);
		end,
		true
	);
end;

-- notre rituel de Renaissance au Chêne (aide de CA, région et rituel à nous)
local function ecouteur_renaissance_chene(faction_key)
	victory_objectives_scripted_listeners.add_listener_SCRIPTED_PERFORM_RITUALS_IN_REGIONS(
		"saison_victoires_9_0_renaissance_chene",
		LONGUE,
		"wh3_dlc29_wef_perform_oak_of_ages_rebirth",
		faction_key,
		{{region_key = CHENE, ritual_key = rituel_renaissance()}},
		1,
		false
	);
end;

-- monument à bâtir dans une de nos régions (aide de CA)
local function ecouteur_monument(nom, mission, cle, faction_key, region, batiment)
	victory_objectives_scripted_listeners.add_listener_SCRIPTED_CONSTRUCT_BUILDINGS_IN_REGION(nom, mission, cle, faction_key,
		region, {batiment});
end;

-- aspects de la forêt achetés par SA faction (CA compte ceux de toute faction)
local function ecouteur_aspects(faction_key)
	saison_ecouteur(
		"saison_victoires_9_0_aspects",
		"UnitEffectPurchased",
		function(context)
			return context:effect():record_key():starts_with("wh2_dlc16_wef_upgrade_aspect_")
				and context:unit():faction():name() == faction_key;
		end,
		function()
			cm:increase_scripted_mission_count(COURTE, "wh3_dlc29_wef_durthu_upgrade_n_forest_spirits_with_aspects", 1);
		end,
		true
	);
end;

-- postes des Élus d'Orion / du Rassemblement des Anciens tenus par des personnages de rang 15 (logique de l'écouteur de
-- CA, wef_shared_objective_listeners, sans ses rituels aux régions des Empires)
local function ecouteur_postes(faction_key)
	local P = POSTES[faction_key];
	if not P or deja_rempli(faction_key, P.cle) then
		return;
	end;
	local prefixe = "wh_dlc05_minister_wef_";
	local function mettre_a_jour(faction)
		if deja_rempli(faction_key, P.cle) then
			return;
		end;
		local n = 0;
		local liste = faction:character_list();
		for i = 0, liste:num_items() - 1 do
			local c = liste:item_at(i);
			if c:ministerial_position():starts_with(prefixe) and c:rank() >= 15 then
				n = n + 1;
			end;
		end;
		cm:set_scripted_mission_text(LONGUE, P.cle, P.texte, n, P.total);
		if n >= P.total then
			remplir_une_fois(faction_key, LONGUE, P.cle);
		end;
	end;
	local function de_la_faction(context)
		return context:character():faction():name() == faction_key;
	end;
	local function sur_evenement(context)
		mettre_a_jour(context:character():faction());
	end;
	saison_ecouteur("saison_victoires_9_0_postes_attribution", "CharacterAssignedToPost", de_la_faction, sur_evenement, true);
	saison_ecouteur("saison_victoires_9_0_postes_rang", "CharacterRankUp", de_la_faction, sur_evenement, true);
	saison_ecouteur("saison_victoires_9_0_postes_retrait", "CharacterRemovedFromPost", de_la_faction, sur_evenement, true);
end;


-- Écouteurs de CA, par leur clé dans sa table (fonctions partagées par culture comprises) ; ceux d'Albéric et de Grom
-- sont gardés ici avant que l'installation ne mette nos enveloppes à leur place.
local ECOUTEURS_CA = {};
if is_table(_victory_objectives_ie) and is_table(_victory_objectives_ie.listeners) then
	ECOUTEURS_CA[ALBERIC] = _victory_objectives_ie.listeners[ALBERIC];
	ECOUTEURS_CA[GROM] = _victory_objectives_ie.listeners[GROM];
	ECOUTEURS_CA.brt_shared_objective_listeners = _victory_objectives_ie.listeners.brt_shared_objective_listeners;
end;

local function ecouteur_de_ca(cle, faction_key)
	local f = ECOUTEURS_CA[cle];
	if not is_function(f) then
		script_error("La Saison des Revelations : victoires 9.0 : ecouteur de CA absent : " .. tostring(cle));
		return;
	end;
	local ok, err = pcall(f, faction_key);
	if not ok then
		script_error("La Saison des Revelations : victoires 9.0 : ecouteur de CA " .. tostring(cle) .. " : " .. tostring(err));
	end;
end;


-- Orion : postes de rang 15 et Renaissance au Chêne (le reste de sa liste : objectifs non scriptés, et delay_victory
-- rempli par la cinématique de fin)
local function ecouteurs_orion(faction_key)
	ecouteur_renaissance_chene(faction_key);
	ecouteur_postes(faction_key);
end;

-- Durthu : aspects de la forêt, Renaissance au Chêne, postes de rang 15
local function ecouteurs_durthu(faction_key)
	ecouteur_aspects(faction_key);
	ecouteur_renaissance_chene(faction_key);
	ecouteur_postes(faction_key);
end;

-- Albéric : les écouteurs de CA (vœux du Graal, chevalerie ; la partie « guerre d'errance » reste inerte), Turris
-- Vigilans, sa finale
local function ecouteurs_alberic(faction_key)
	-- vœux du Graal : comme pour la Fée, les écouteurs de CA (victory_objectives_config.lua l. 6784-6808) comptaient les
	-- vœux de TOUTE faction, IA comprises (audit des seigneurs du 25.09.2026, M2) ; les nôtres ne comptent que les siens.
	-- La chevalerie (aide partagée de CA) reste celle de CA.
	saison_ecouteur(
		"saison_victoires_9_0_voeu_alberic",
		"ScriptEventBretonniaGrailVowCompleted",
		function(context)
			local c = context:character();
			return c:faction():name() == faction_key and c:character_subtype("wh_dlc07_brt_alberic");
		end,
		function()
			cm:complete_scripted_mission_objective(faction_key, COURTE, "wh3_dlc29_bordeleaux_grail_vow", true);
		end,
		true
	);
	saison_ecouteur(
		"saison_victoires_9_0_voeux_alberic",
		"ScriptEventBretonniaGrailVowCompleted",
		function(context)
			local c = context:character();
			return c:faction():name() == faction_key and not c:character_subtype("wh_dlc07_brt_alberic");
		end,
		function()
			cm:increase_scripted_mission_count(LONGUE, "wh3_dlc29_bordeleaux_3_grail_vows", 1);
		end,
		true
	);
	ecouteur_de_ca("brt_shared_objective_listeners", faction_key);
	ecouteur_monument("saison_victoires_9_0_alberic_turris", COURTE, "saison_victoire_alberic_turris", faction_key,
		"wh_dlc05_bordeleaux_turris_vigilans", "wh_dlc05_mini_landmark_turris_vigilans_1");
	ecouteur_finale(faction_key);
end;

-- la Fée : Trothe de vertu (la sienne en courte, trois autres de SA faction en longue ; CA compte celles de toute
-- faction) ; chevalerie (aide partagée de CA) ; Tour de l'Enchanteresse ; réveil des ducs ; Chapelle de l'Enchanteresse ;
-- sa finale
local function ecouteurs_fee(faction_key)
	saison_ecouteur(
		"saison_victoires_9_0_trothe_fee",
		"ScriptEventBretonniaVirtueTrothCompleted",
		function(context)
			local c = context:character();
			return c:faction():name() == faction_key and c:character_subtype("wh_dlc07_brt_fay_enchantress");
		end,
		function()
			cm:complete_scripted_mission_objective(faction_key, COURTE, "wh3_dlc29_carcassonne_virtue_thoth", true);
		end,
		true
	);
	saison_ecouteur(
		"saison_victoires_9_0_trothes_fee",
		"ScriptEventBretonniaVirtueTrothCompleted",
		function(context)
			local c = context:character();
			return c:faction():name() == faction_key and not c:character_subtype("wh_dlc07_brt_fay_enchantress");
		end,
		function()
			cm:increase_scripted_mission_count(LONGUE, "wh3_dlc29_carcassonne_complete_n_virtue_thoths", 1);
		end,
		true
	);
	ecouteur_de_ca("brt_shared_objective_listeners", faction_key);
	ecouteur_monument("saison_victoires_9_0_fee_tour", COURTE, "wh3_dlc29_brt_construct_landmark_short", faction_key,
		"wh_dlc05_carcassonne_castle_carcassonne", "wh_main_brt_legendary_enchantress_tower");
	-- réveil des ducs : trois duchés alliés, vassaux, ou rattachés (faction disparue et capitale à elle) ; logique de
	-- ecouteur_fee_ducs (saison_chroniques.lua)
	if not deja_rempli(faction_key, "saison_victoire_fee_ducs") then
		saison_ecouteur(
			"saison_victoires_9_0_fee_ducs",
			"FactionBeginTurnPhaseNormal",
			function(context)
				if context:faction():name() ~= faction_key or deja_rempli(faction_key, "saison_victoire_fee_ducs") then
					return false;
				end;
				local fee = context:faction();
				local n = 0;
				for i = 1, #DUCHES do
					local cle_duche, capitale = DUCHES[i][1], DUCHES[i][2];
					if cle_duche ~= faction_key then
						local d = cm:get_faction(cle_duche);
						if d and not d:is_dead() then
							if fee:allied_with(d) or d:is_ally_vassal_or_client_state_of(fee) then
								n = n + 1;
							end;
						else
							local r = cm:get_region(capitale);
							if r and not r:is_abandoned() and r:owning_faction():name() == faction_key then
								n = n + 1;
							end;
						end;
					end;
				end;
				return n >= 3;
			end,
			function()
				remplir_une_fois(faction_key, COURTE, "saison_victoire_fee_ducs");
				core:remove_listener("saison_victoires_9_0_fee_ducs");		-- rempli : plus rien à guetter (T12 / S12)
			end,
			true
		);
	end;
	ecouteur_monument("saison_victoires_9_0_fee_chapelle", LONGUE, "saison_victoire_fee_chapelle", faction_key,
		"wh_dlc05_quenelles_quenelles", "wh_dlc05_mini_landmark_chapelle_de_l_enchanteresse_1");
	ecouteur_finale(faction_key);
end;

-- Morghur : il termine un tour à Tal Rond (logique de presence(), saison_chroniques.lua ; cherché par sous-type, car
-- l'histoire le tue et le recrée) ; sa finale
local function ecouteurs_morghur(faction_key)
	if not deja_rempli(faction_key, "saison_victoire_morghur_val") then
		saison_ecouteur(
			"saison_victoires_9_0_morghur_val",
			"FactionBeginTurnPhaseNormal",
			function(context)
				if context:faction():name() ~= faction_key or deja_rempli(faction_key, "saison_victoire_morghur_val") then
					return false;
				end;
				local c = personnage(faction_key, "wh_dlc05_bst_morghur");
				return c and c:has_region() and c:region():name() == "wh_dlc05_anmyr_tal_rond";
			end,
			function()
				remplir_une_fois(faction_key, COURTE, "saison_victoire_morghur_val");
				core:remove_listener("saison_victoires_9_0_morghur_val");		-- rempli : plus rien à guetter (T12 / S12)
			end,
			true
		);
	end;
	ecouteur_finale(faction_key);
end;

-- le Duc écarlate : Tombeau à Gien ; deux seigneurs de lignée éveillés dans des repaires (évènement de CA,
-- wh3_dlc29_vampire_lairs.lua ; écouteur de Mannfred chez CA) ; palais de Mousillon (colonie au plus haut rang) ; sa finale
local function ecouteurs_duc(faction_key)
	ecouteur_monument("saison_victoires_9_0_duc_tombeau", COURTE, "saison_victoire_duc_tombeau", faction_key,
		"wh_dlc05_aquitaine_gien", "wh_dlc05_mini_landmark_tombeau_du_duc_rouge_vmp_1");
	saison_ecouteur(
		"saison_victoires_9_0_duc_eveil",
		"ScriptEventVampireLairAwakened",
		function(context)
			return context:faction():name() == faction_key;
		end,
		function()
			cm:increase_scripted_mission_count(LONGUE, "saison_victoire_duc_eveil", 1);
		end,
		true
	);
	ecouteur_monument("saison_victoires_9_0_duc_palais", LONGUE, "saison_victoire_duc_palais", faction_key,
		"wh_dlc05_mousillon_mousillon", "wh_main_vmp_settlement_major_5");
	ecouteur_finale(faction_key);
end;

-- Drycha : Coeddil par notre quête ; Addaivoch et la Clairière du Malheur à Tal Rond ; Renaissance au Chêne ; sa finale
local function ecouteurs_drycha(faction_key)
	saison_ecouteur(
		"saison_victoires_9_0_drycha_coeddil",
		"MissionSucceeded",
		function(context)
			return context:faction():name() == faction_key
				and context:mission():mission_record_key() == "saison_qb_wef_drycha_coeddil_unchained";
		end,
		function()
			cm:complete_scripted_mission_objective(faction_key, COURTE, "wh3_dlc29_wef_drycha_unlock_coeddil", true);
		end,
		true
	);
	ecouteur_monument("saison_victoires_9_0_drycha_addaivoch", COURTE, "wh3_dlc29_wef_construct_landmark_short", faction_key,
		"wh_dlc05_anmyr_tal_rond", "wh_dlc05_mini_landmark_addaivoch_chene_des_malheurs_1");
	ecouteur_renaissance_chene(faction_key);
	ecouteur_finale(faction_key);
end;

-- Kemmler : Tertre de Krell au Poste de la Pierre Noire ; sa finale
local function ecouteurs_kemmler(faction_key)
	ecouteur_monument("saison_victoires_9_0_kemmler_krell", COURTE, "wh3_dlc29_vmp_kemmler_build_landmark_short", faction_key,
		"wh_dlc05_grey_mountains_2_blackstone_post", "wh_dlc05_mini_landmark_tertre_de_krell_1");
	ecouteur_finale(faction_key);
end;

-- Grom : les écouteurs de CA (marmite, ingrédients, trophées de Waaagh!), sa finale
local function ecouteurs_grom(faction_key)
	ecouteur_de_ca(GROM, faction_key);
	ecouteur_finale(faction_key);
end;

-- les Sœurs : Renaissance au Chêne ; pacte (non-agression) ou alliance avec Orion, vu en début de leur tour ; leur finale
local function ecouteurs_soeurs(faction_key)
	ecouteur_renaissance_chene(faction_key);
	if not deja_rempli(faction_key, "saison_victoire_soeurs_porte_du_roi") then
		saison_ecouteur(
			"saison_victoires_9_0_soeurs_porte_du_roi",
			"FactionBeginTurnPhaseNormal",
			function(context)
				if context:faction():name() ~= faction_key or deja_rempli(faction_key, "saison_victoire_soeurs_porte_du_roi") then
					return false;
				end;
				local o = cm:get_faction(ORION);
				return o and not o:is_dead()
					and (context:faction():allied_with(o) or context:faction():non_aggression_pact_with(o));
			end,
			function()
				remplir_une_fois(faction_key, LONGUE, "saison_victoire_soeurs_porte_du_roi");
				core:remove_listener("saison_victoires_9_0_soeurs_porte_du_roi");		-- rempli : plus rien à guetter (T12 / S12)
			end,
			true
		);
	end;
	ecouteur_finale(faction_key);
end;

-- chaque écouteur sous pcall : add_scripted_victory_listeners de CA ne protège pas ses appels, et une erreur ici
-- empêcherait ses écouteurs d'incident de victoire
local function protege(nom, f)
	return function(faction_key)
		local ok, err = pcall(f, faction_key);
		if not ok then
			script_error("La Saison des Revelations : victoires 9.0 : ecouteurs de " .. nom .. " : " .. tostring(err));
		end;
	end;
end;


-----------------------------------------------------------------------------------
--	Installation, au chargement du fichier (avant WorldCreated et avant le premier tour)
-----------------------------------------------------------------------------------

local function installer()
	-- 1. le rappel de premier tour de CA passe par cette enveloppe : jamais d'erreur, rien en multijoueur, rien pour une
	--    faction hors de nos listes
	local ca_initialiser = _victory_objectives_ie.initialise_victory_missions;
	function _victory_objectives_ie:initialise_victory_missions(faction_key, multiplayer)
		-- campagne bloquée (DLC absent) : rien à créer avant le retour au menu (revue de la bêta, M6)
		if not installee or saison_bloquee or cm:is_multiplayer() or not SAISON_LISTES[faction_key] then
			return;
		end;
		-- Durthu joué sans Orion : le Chêne lui revient AVANT sa longue (« Ne perdez pas le Chêne des Âges ») ; ce rappel
		-- de CA passe avant saison_partie_neuve, qui le faisait avant la mission ultime (saison_start.lua)
		if faction_key == DURTHU and is_function(saison_chene_a_durthu) then
			local ok_chene, err_chene = pcall(saison_chene_a_durthu);
			if not ok_chene then
				script_error("La Saison des Revelations : victoires 9.0 : Chene a Durthu : " .. tostring(err_chene));
			end;
		end;
		local ok, err = pcall(ca_initialiser, self, faction_key, multiplayer);
		if not ok then
			script_error("La Saison des Revelations : victoires 9.0 : missions de " .. faction_key .. " : " .. tostring(err));
		else
			cm:set_saved_value("saison_victoires_9_0_listes_" .. faction_key, true);
			out("La Saison des Revelations : victoires 9.0 creees pour " .. faction_key);
		end;
	end;

	-- 2. pas de table des Empires
	core:remove_listener("InitializeVictoryObjectivesIEConfig");

	-- 3. notre table (types de victoire recopiés de CA)
	SAISON_LISTES = construire_listes();
	_victory_objectives_ie_config = {
		victory_types = {
			short = {mission_key = COURTE, victory_type_key = "wh3_combi_victory_type_faction"},
			long = {mission_key = LONGUE, victory_type_key = "wh3_combi_victory_type_subculture"},
			domination = {mission_key = "wh_main_domination_victory", victory_type_key = "wh3_combi_victory_type_domination"},
			multiplayer = {mission_key = "wh3_main_mp_victory", victory_type_key = "wh3_combi_victory_type_multiplayer"}
		},
		factions = SAISON_LISTES
	};
	_victory_objectives_ie.config = _victory_objectives_ie_config;

	-- 4. écouteurs : on remplace nos entrées dans la table de CA (ses fonctions partagées y restent : celles d'Albéric et
	--    de Grom les appellent par cette table)
	local L = _victory_objectives_ie.listeners;
	L[ORION] = protege("Orion", ecouteurs_orion);
	L[DURTHU] = protege("Durthu", ecouteurs_durthu);
	L[ALBERIC] = protege("Alberic", ecouteurs_alberic);
	L[FEE] = protege("la Fee", ecouteurs_fee);
	L[HARDE] = protege("Morghur", ecouteurs_morghur);
	L[DUC] = protege("le Duc", ecouteurs_duc);
	L[DRYCHA] = protege("Drycha", ecouteurs_drycha);
	L[KEMMLER] = protege("Kemmler", ecouteurs_kemmler);
	L[GROM] = protege("Grom", ecouteurs_grom);
	L[SOEURS] = protege("les Soeurs", ecouteurs_soeurs);

	installee = true;
end;

if ca_present() then
	local ok, err = pcall(installer);
	if not ok then
		installee = false;
		script_error("La Saison des Revelations : victoires 9.0 : installation impossible : " .. tostring(err));
	end;
else
	script_error("La Saison des Revelations : victoires 9.0 : fichiers de CA absents (victory_objectives_config)");
end;


-- Vrai si nos listes sont en place (saison_victoire.lua : sinon, ancienne mission ultime en secours).
function saison_victoires_9_0_pretes()
	return installee;
end;


-- À chaque chargement (saison_start.lua) : les écouteurs de CA (objectifs scriptés, incidents et récompenses de
-- victoire) et les nôtres, si l'humain est un de nos dix seigneurs et la partie commencée avec ce système.
function saison_victoires_9_0_ecouteurs()
	if not installee or cm:is_multiplayer() then
		return;
	end;
	if not cm:get_saved_value("IEVictoryConditionUseDLC29Config") then
		return;			-- partie d'avant : mission ultime de saison_victoire.lua
	end;
	local humains = cm:get_human_factions();
	for i = 1, #humains do
		local cle = humains[i];
		-- Orion et Durthu : seulement si leurs missions de la 9.0 ont été créées (une partie commencée avec la première
		-- version de ce fichier leur a donné la mission ultime de WH1, que les écouteurs de CA ne doivent pas toucher :
		-- ils coupent les récompenses de mission, game_victory compris)
		local ok_wh1 = (cle ~= ORION and cle ~= DURTHU) or cm:get_saved_value("saison_victoires_9_0_listes_" .. cle);
		if SAISON_LISTES[cle] and ok_wh1 then
			_victory_objectives_ie:add_scripted_victory_listeners();
			out("La Saison des Revelations : victoires 9.0 : ecouteurs de " .. cle);
			return;
		end;
	end;
end;
