-----------------------------------------------------------------------------------
--	Victoire de la mini-campagne et cinématique de fin.
--
--	WH1 (victory_objectives.txt de la carte, identique pour Orion et Durthu) : mission wh_main_long_victory, type
--	wh_dlc05_victory_type_ultimate, émetteur CLAN_ELDERS, charge game_victory, quatre objectifs : le Chêne au dernier
--	niveau, ne pas perdre le Chêne, la bataille du Pic d'Argent, et un objectif scripté (delay_victory) rempli à la fin
--	de la cinématique. Dans WH3 la victoire n'existe que si le script la crée (start_pos_victory_conditions vide) :
--	mission_manager, comme les victoires des Empires Immortels (victory_objectives.lua de CA).
--
--	Décision de Charles (23.09.2026) : le Chêne au niveau 5 de la chaîne de WH3, verrouillé par le rituel de
--	Renaissance des Chemins-racines : le rituel est affiché comme premier objectif, comme la victoire des Elfes
--	sylvains aux Empires.
--
--	Cinématique (WH1 : Mini_Campaign_Victory) : 43 s, scène Cindy de fin d'Orion (WH1 la jouait aussi pour Durthu),
--	répliques 018 à 021 du personnage joué ; l'objectif scripté est rempli à 39,5 s ou au saut.
--
--	24.09.2026 : en partie neuve, les dix seigneurs ont les victoires au format 9.0 (saison_victoires_9_0.lua) ; pour
--	Orion et Durthu, cette victoire de WH1 y devient leur longue (même mission, même objectif delay_victory rempli par la
--	cinématique ci-dessous), sans game_victory : la partie continue (décision de Charles). La mission ultime ci-dessous ne
--	sert plus qu'aux parties d'avant et en secours, si saison_victoires_9_0 n'a pas pu s'installer.
-----------------------------------------------------------------------------------

local ORION = "wh_dlc05_wef_wood_elves";
local DURTHU = "wh_dlc05_wef_argwylon";
local CHENE = "wh_dlc05_oak_of_ages";
local MISSION_VICTOIRE = "wh_main_long_victory";
local OBJECTIF_FIN = "delay_victory";
local TEXTE_FIN = "mission_text_text_wh_dlc05_mini_delay_victory";
local TYPE_VICTOIRE = "wh_dlc05_victory_type_ultimate";
local SCENE_FIN = "script/campaign/wh_dlc05_wood_elves/factions/wh_dlc05_wef_wood_elves/scenes/we_orion_mini_outro.CindyScene";


-- Seigneurs de WH3 jouables sur notre carte (23.09.2026) : les objectifs propres que CA leur donne aux Empires
-- (victory_objectives.lua de main_warhammer), ramenés à notre carte ; la harde de Morghur en est l'ennemi commun.
-- 24.09.2026 : les parties neuves leur donnent les victoires de la 9.0 (saison_victoires_9_0.lua : courte, longue,
-- domination) ; cette mission ultime ne sert plus qu'en secours, si ce fichier n'a pas pu s'installer. Les parties
-- d'avant gardent la leur (créée à leur premier tour), avec les écouteurs des vœux ci-dessous.
local ALBERIC = "wh_main_brt_bordeleaux";
local FEE = "wh_main_brt_carcassonne";
local HARDE = "wh_dlc05_bst_morghur_herd";

local VICTOIRES_WH3 = {
	-- Alberic : son vœu du Graal (CA), et la harde de Morghur détruite
	[ALBERIC] = function(mm)
		mm:add_new_objective("SCRIPTED");
		mm:add_condition("override_text mission_text_text_mis_activity_complete_grail_vow_alberic");
		mm:add_condition("script_key alberic_grail_vow_success");
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. HARDE);
		mm:add_condition("confederation_valid");
	end,
	-- la Fée Enchanteresse : sa Trothe de vertu (CA), et la harde de Morghur détruite
	[FEE] = function(mm)
		mm:add_new_objective("SCRIPTED");
		mm:add_condition("override_text mission_text_text_mis_activity_complete_troth_of_virute_vow_enchantress");
		mm:add_condition("script_key enchantress_virtue_success");
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. HARDE);
		mm:add_condition("confederation_valid");
	end,
	-- Morghur : la Ruine au niveau 6 (CA), et les deux seigneurs d'Athel Loren détruits (CA : Carcassonne, Orion,
	-- Estalie ; la Saison est la guerre de Morghur contre Athel Loren)
	[HARDE] = function(mm)
		mm:add_new_objective("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE");
		mm:add_condition("pooled_resource bst_ruination");
		mm:add_condition("total 220");
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. ORION);
		mm:add_condition("faction " .. DURTHU);
		mm:add_condition("confederation_valid");
	end,
	-- le Duc rouge (CA ne le rend jouable nulle part) : jadis duc d'Aquitaine, il reprend son duché et abat Alberic de
	-- Bordeleaux, sentinelle des frontières de Mousillon
	["wh_main_vmp_mousillon"] = function(mm)
		mm:add_new_objective("CONTROL_N_PROVINCES_INCLUDING");
		mm:add_condition("total 1");
		mm:add_condition("province wh_dlc05_aquitaine");
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. ALBERIC);
		mm:add_condition("faction wh3_main_brt_aquitaine");
		mm:add_condition("confederation_valid");
	end,
	-- Drycha : les cinq provinces clés des Elfes sylvains que CA lui donne aux Empires, qui portent chez nous les mêmes
	-- noms (Argwylon, Wydrioth, Yn Edri Eternos, Talsyn, Torgovann)
	["wh2_dlc16_wef_drycha"] = function(mm)
		mm:add_new_objective("CONTROL_N_PROVINCES_INCLUDING");
		mm:add_condition("total 5");
		mm:add_condition("province wh_dlc05_argwylon");
		mm:add_condition("province wh_dlc05_wydrioth");
		mm:add_condition("province wh_dlc05_oak_of_ages");
		mm:add_condition("province wh_dlc05_talsyn");
		mm:add_condition("province wh_dlc05_torgovann");
	end,
	-- Kemmler : Durthu détruit et trois duchés bretons de la lisière d'Athel Loren (CA : Bastonne, forêt de Châlons,
	-- Carcassonne ; Châlons n'est pas une province chez nous : Quenelles, l'autre duché de la lisière)
	["wh2_dlc11_vmp_the_barrow_legion"] = function(mm)
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. DURTHU);
		mm:add_condition("confederation_valid");
		mm:add_new_objective("CONTROL_N_PROVINCES_INCLUDING");
		mm:add_condition("total 3");
		mm:add_condition("province wh_dlc05_bastonne");
		mm:add_condition("province wh_dlc05_carcassonne");
		mm:add_condition("province wh_dlc05_quenelles");
	end,
	-- Grom : CA lui fait tenir Tor Yvresse, la cité d'Eltharion ; ici la grande cité des Elfes est le Palais des Chutes
	-- de Durthu (Argwylon)
	["wh2_dlc15_grn_broken_axe"] = function(mm)
		mm:add_new_objective("CONTROL_N_REGIONS_FROM");
		mm:add_condition("total 1");
		mm:add_condition("region wh_dlc05_argwylon_waterfall_palace");
	end,
	-- les Sœurs du Crépuscule (24.09.2026) : CA leur fait soigner les forêts (2 rituels de guérison des Racines du monde) ;
	-- notre carte n'a qu'une forêt magique, Athel Loren : notre rituel de Renaissance. S'y ajoutent leur salle des Pics
	-- relevée et tenue, et la harde de Morghur détruite (l'ennemi commun de la Saison, comme pour Alberic et la Fée)
	["wh2_dlc16_wef_sisters_of_twilight"] = function(mm)
		mm:add_new_objective("PERFORM_RITUAL");
		mm:add_condition("ritual " .. (SAISON_RITUEL_RENAISSANCE or "wh2_dlc16_ritual_rebirth_saison_athel_loren"));
		mm:add_new_objective("CONTROL_N_REGIONS_FROM");
		mm:add_condition("total 1");
		mm:add_condition("region wh_dlc05_wydrioth_tal_jul_finel");
		mm:add_new_objective("DESTROY_FACTION");
		mm:add_condition("faction " .. HARDE);
		mm:add_condition("confederation_valid");
	end
};


-- Les victoires de la 9.0 sont-elles en place pour les huit seigneurs de WH3 ? (saison_victoires_9_0.lua)
local function victoires_9_0()
	return is_function(saison_victoires_9_0_pretes) and saison_victoires_9_0_pretes();
end;


-- Partie neuve : la mission de victoire du seigneur joué (appelé par saison_start.lua, sous saison_sur).
function saison_creer_victoire()
	if cm:is_multiplayer() then
		return;				-- victoires coopérative et face à face de WH1 : hors périmètre
	end;
	local humains = cm:get_human_factions();
	for i = 1, #humains do
		local cle = humains[i];
		if (VICTOIRES_WH3[cle] or cle == ORION or cle == DURTHU) and victoires_9_0() then
			-- 24.09.2026 : ses victoires de la 9.0 sont créées par le rappel de CA (saison_victoires_9_0.lua). Orion et
			-- Durthu : la victoire de WH1 y devient leur longue (même mission wh_main_long_victory, delay_victory rempli
			-- par saison_cinematique_de_fin ci-dessous), qui ne termine plus la partie (décision de Charles)
			out("La Saison des Revelations : victoire de " .. cle .. " : listes de la 9.0");
		elseif VICTOIRES_WH3[cle] then
			local mm = mission_manager:new(cle, MISSION_VICTOIRE);
			VICTOIRES_WH3[cle](mm);
			mm:add_payload("game_victory");
			mm:set_victory_type(TYPE_VICTOIRE);
			mm:set_victory_mission(true);
			mm:set_show_mission(false);
			mm:trigger();
		elseif cle == ORION or cle == DURTHU then
			local mm = mission_manager:new(cle, MISSION_VICTOIRE);

			-- notre rituel de Renaissance (lot 7 ; SAISON_RITUEL_RENAISSANCE, saison_foret.lua)
			mm:add_new_objective("PERFORM_RITUAL");
			mm:add_condition("ritual " .. (SAISON_RITUEL_RENAISSANCE or "wh2_dlc16_ritual_rebirth_saison_athel_loren"));

			mm:add_new_objective("CONSTRUCT_N_BUILDINGS_INCLUDING");
			mm:add_condition("total 1");
			mm:add_condition("building_level wh_dlc05_wef_oak_of_ages_5");
			mm:add_condition("faction " .. cle);

			mm:add_new_objective("DO_NOT_LOSE_REGION");
			mm:add_condition("region " .. CHENE);

			mm:add_new_objective("FIGHT_SET_PIECE_BATTLE");
			mm:add_condition("set_piece_battle wh_dlc05_qb_wef_grand_silver_spire");

			mm:add_new_objective("SCRIPTED");
			mm:add_condition("script_key " .. OBJECTIF_FIN);
			mm:add_condition("override_text " .. TEXTE_FIN);

			mm:add_payload("game_victory");
			mm:set_victory_type(TYPE_VICTOIRE);
			mm:set_victory_mission(true);
			mm:set_show_mission(false);
			mm:trigger();
		end;
	end;
end;


-- À chaque chargement (saison_start.lua) : les vœux de Bretonnie remplissent les objectifs d'Alberic et de la Fée, comme
-- aux Empires (écouteurs IEVictoryCondition* de victory_objectives.lua, sur notre mission de victoire).
-- 24.09.2026 : seulement pour la mission ultime (parties d'avant, ou secours) ; avec les victoires de la 9.0, ce sont
-- les écouteurs de saison_victoires_9_0.lua.
function saison_victoire_ecouteurs()
	if victoires_9_0() and cm:get_saved_value("IEVictoryConditionUseDLC29Config") then
		return;
	end;
	local function voeu(nom, evenement, sous_type, faction_key, cle_script)
		local f = cm:get_faction(faction_key);
		if not (f and f:is_human()) then
			return;
		end;
		core:add_listener(
			nom,
			evenement,
			function(context)
				return context:character():character_subtype(sous_type);
			end,
			function()
				cm:complete_scripted_mission_objective(faction_key, MISSION_VICTOIRE, cle_script, true);
			end,
			true
		);
	end;
	voeu("saison_victoire_voeu_alberic", "ScriptEventBretonniaGrailVowCompleted", "wh_dlc07_brt_alberic", ALBERIC,
		"alberic_grail_vow_success");
	voeu("saison_victoire_trothe_fee", "ScriptEventBretonniaVirtueTrothCompleted", "wh_dlc07_brt_fay_enchantress", FEE,
		"enchantress_virtue_success");
end;


-- Après la bataille finale (saison_histoire.lua) : la fin de la Saison, puis la victoire.
function saison_cinematique_de_fin(faction_key)
	local qui = (faction_key == DURTHU) and "durthu" or "orion";
	local function replique(numero, sans_bouton)
		local cle = "dlc05.mini.story." .. qui .. "." .. numero;
		if sans_bouton then
			cm:show_advice(cle);
		else
			cm:show_advice(cle, true);
		end;
	end;

	local victoire_donnee = false;
	local function victoire()
		if not victoire_donnee then
			victoire_donnee = true;
			cm:complete_scripted_mission_objective(faction_key, MISSION_VICTOIRE, OBJECTIF_FIN, true);
		end;
	end;

	-- essai automatique (saison_en_essai_auto, required.lua) : la victoire sans la cinématique
	if saison_en_essai_auto() then
		victoire();
		return;
	end;

	local c = campaign_cutscene:new("saison_fin_de_la_saison", 43);

	c:set_skippable(
		true,
		function()
			cm:fade_scene(1, 1);
			cm:show_shroud(true);
			CampaignUI.ToggleCinematicBorders(false);
			victoire();
		end
	);

	c:action(function()
		CampaignUI.ToggleCinematicBorders(true);
		cm:fade_scene(0, 1);
	end, 0);

	-- le Pic d'Argent vu de haut, puis la scène de WH1
	c:action(function()
		cm:show_shroud(false);
		cm:set_camera_position(125.48, 258.25, 5.59, -2.47, 4.0);
		c:cindy_playback(SCENE_FIN, 0, 0);
	end, 1);

	c:action(function() cm:fade_scene(1, 1) end, 1.1);

	-- Orion : « Victoire ! Morghur est relégué dans l'oubli... » ; Durthu : « La rage bat-elle encore dans ton cœur ? »
	c:action(function() replique("018", true) end, 2);
	c:action(function() c:wait_for_advisor() end, 9);
	c:action(function() replique("019", true) end, 10);
	c:action(function() c:wait_for_advisor() end, 18);
	c:action(function() replique("020", true) end, 19);
	c:action(function() c:wait_for_advisor() end, 28);
	c:action(function() replique("021") end, 29);
	c:action(function() c:wait_for_advisor() end, 39);
	c:action(victoire, 39.5);

	c:action(function()
		cm:show_shroud(true);
		CampaignUI.ToggleCinematicBorders(false);
	end, 42);

	c:start();
end;
