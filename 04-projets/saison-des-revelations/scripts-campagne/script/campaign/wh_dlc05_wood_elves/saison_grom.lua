-----------------------------------------------------------------------------------
--	La Saison des Révélations : la Revanche de Dent-Noire (Grom la Panse), l'histoire de CA reprise.
--
--	CA (wh2_dlc15_grom_story.lua, chargé par les Empires) : la tête de Dent-Noire en bocal pousse Grom à manger et à
--	cuisiner (missions 1 à 4 : ferraille, un plat, la marchande, des ingrédients), puis trois prophéties qui débloquent
--	les recettes secrètes de la marmite, puis la revanche sur Tor Yvresse. Deux étapes visent des terres absentes de
--	notre carte (audit des scripts de CA : « recettes secrètes non chargées ») :
--	- la prophétie de la Ruine : piller 10 colonies de Hauts Elfes. Le texte de CA dit « les terres des pointues-
--	  oreilles » : chez nous, Athel Loren (6 de ses 18 colonies, même récompense) ;
--	- la dernière mission : prendre Tor Yvresse (Ulthuan). Rien ne la remplace : la chaîne s'arrête après la quatrième
--	  (sa récompense, « Grom est prêt », reste), sans rien inventer au lore de Dent-Noire.
--	Les missions 3 et 4 promettaient justement ce retour à Tor Yvresse : sous nos clés, texte de CA sans la promesse
--	(audit de cohérence du 25.09.2026). Le reste est celui de CA, textes compris. Seulement si Grom est joué (comme CA).
-----------------------------------------------------------------------------------

local GROM = "wh2_dlc15_grn_broken_axe";
local DERNIERE_DE_CA = 6;		-- index de wh2_dlc15_grn_grom_black_toof_5_ME dans BlacktoofMissions (CA)
local RUINE = "wh2_dlc15_grom_blacktoof_prophecy_1";
local RECETTE = "effect_bundle{bundle_key wh2_dlc15_grom_unlock_special_recipe;turns 0;}";
local ATHEL_LOREN = {
	"wh_dlc05_anmyr_halls_of_anaereth", "wh_dlc05_anmyr_tal_rond", "wh_dlc05_argwylon_waterfall_palace",
	"wh_dlc05_arranoc_tal_esth", "wh_dlc05_atylwyth_tal_amere", "wh_dlc05_cavaroc_halls_of_equos",
	"wh_dlc05_cythral_tyr_vanna", "wh_dlc05_fyr_darric_feast_halls", "wh_dlc05_fyr_darric_threllock",
	"wh_dlc05_modryn_glade_of_eternal_midnight", "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_talsyn_yn_ecryl_koiran", "wh_dlc05_tirsyth_glade_of_eternal_moonlight",
	"wh_dlc05_torgovann_cromlech_cadai", "wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_crag_halls",
	"wh_dlc05_wydrioth_tal_jul_finel"
};


-- Le trait de faction de Grom (audit de cohérence du 25.09.2026, point 5) : celui de CA, posé à son sous-type dans
-- toutes les campagnes (faction_starting_general_effects), s'intitule « Waaagh contre Ulthuan ! » et donne -80 avec les
-- Hauts Elfes, absents de notre carte. En partie neuve, il est remplacé par le nôtre (lot 38 : « Le Roi des Gobelins »,
-- la citation de CA) avec les mêmes effets, sans la diplomatie. Sans la ligne du lot 38 dans le pack, celui de CA reste.
local TRAIT_DE_CA = "wh2_dlc15_lord_trait_grn_grom_the_paunch";
local TRAIT = "saison_lord_trait_grom";
local EFFETS_DU_TRAIT = {
	{"wh2_dlc15_effect_upkeep_reduction_grn_chariots", "faction_to_force_own", -20},
	{"wh2_dlc15_faction_trait_grom_feature", "faction_to_faction_own_unseen", 1},
	{"wh3_dlc26_effect_force_unit_stat_charge_bonus_chariot_pump_wagon", "faction_to_force_own", 15},
	{"wh3_dlc26_effect_scrap_cost_increase_hidden", "faction_to_army_own_unseen", 30}
};

function saison_grom_trait()
	if not cm:is_new_game() then
		return;
	end;
	local grom = cm:get_faction(GROM);
	if not grom or grom:is_dead() or not grom:has_effect_bundle(TRAIT_DE_CA) then
		out("La Saison des Revelations : trait de Grom de CA absent au demarrage, rien de remplace");
		return;
	end;
	local b = cm:create_new_custom_effect_bundle(TRAIT);
	if not b then
		out("La Saison des Revelations : " .. TRAIT .. " absent du pack, le trait de CA reste");
		return;
	end;
	b:set_duration(0);
	for _, e in ipairs(EFFETS_DU_TRAIT) do
		b:add_effect(e[1], e[2], e[3]);
	end;
	cm:remove_effect_bundle(TRAIT_DE_CA, GROM);
	cm:apply_custom_effect_bundle_to_faction(b, grom);
	out("La Saison des Revelations : trait de Grom remplace (Le Roi des Gobelins, sans Ulthuan)");
end;


-- les trois prophéties de CA (setup_black_toofs_prophecies), la Ruine tournée vers Athel Loren
local function propheties()
	local mm = mission_manager:new(GROM, "wh2_dlc15_grom_blacktoof_prophecy_0");
	mm:add_new_objective("SCRIPTED");
	mm:add_condition("script_key prophecies_0");
	mm:add_condition("override_text mission_text_text_wh2_dlc15_obejctive_grom_mission_extra");
	mm:set_mission_issuer("BLACK_TOOF");
	mm:add_payload(RECETTE);
	mm:add_payload("money 8000");
	mm:set_should_whitelist(false);
	mm:trigger();

	local ruine = mission_manager:new(GROM, RUINE);
	ruine:add_new_objective("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING");
	ruine:add_condition("total 6");
	for _, region in ipairs(ATHEL_LOREN) do
		ruine:add_condition("region " .. region);
	end;
	ruine:set_mission_issuer("BLACK_TOOF");
	ruine:add_payload(RECETTE);
	ruine:add_payload("faction_pooled_resource_transaction{resource grn_salvage;factor grn_salvage_missions;amount 500;context absolute;}");
	ruine:set_should_whitelist(false);
	-- trigger() rend false en cas d'échec, rien quand tout va bien (lib_campaign_mission_manager 9.0)
	if ruine:trigger() == false then
		out("La Saison des Revelations : prophetie de la Ruine (Athel Loren) non emise");
	end;

	cm:trigger_mission(GROM, "wh2_dlc15_grom_blacktoof_prophecy_2", true);
	check_blacktoof_mission_requirement();
end;


-- Missions scriptées 2 à 5 de CA (setup_black_toof_scripted_mission et setup_black_toof_mission_listener, globales ;
-- sa liste de clés BlacktoofMissions est locale) : les missions 3 et 4 promettaient Tor Yvresse (audit de cohérence du
-- 25.09.2026, point 7). Les étapes 3 et 5 (index de CA) passent sous nos clés (lot 10 : copies de CA, texte sans la
-- promesse) ; objectifs, textes d'objectif, charges et évènements sont ceux de CA, recopiés d'elle (l. 5-11, 148-197).
local ETAPES = {
	[2] = {cle = "wh2_dlc15_grn_grom_black_toof_2", objectif = "wh2_dlc15_obejctive_grom_mission_2", evenement = "FactionCookedDish",
		charges = {"faction_pooled_resource_transaction{resource grn_salvage;factor looting;amount 100;context absolute;}", "money 1200"}},
	[3] = {cle = "saison_grn_grom_black_toof_3", objectif = "wh2_dlc15_obejctive_grom_mission_3",
		evenement = "ScriptEventGromsCauldronGromMeetsTheFoodMerchantress",
		charges = {"faction_pooled_resource_transaction{resource grn_salvage;factor looting;amount 150;context absolute;}", "money 1500"}},
	[4] = {cle = "wh2_dlc15_grn_grom_black_toof_3_2", objectif = "wh2_dlc15_obejctive_grom_mission_3_2",
		evenement = "GromHasUnlockedEnoughIngredients",
		charges = {"effect_bundle{bundle_key wh2_dlc15_grom_unlock_special_recipe;turns 0;}", "money 1500"}},
	[5] = {cle = "saison_grn_grom_black_toof_4", objectif = "wh2_dlc15_obejctive_grom_mission_4", evenement = "GromEatenEnoughRecipes",
		charges = {"effect_bundle{bundle_key wh2_dlc15_grn_narration_groms_ready;turns 0;}"}}
};

local function ecouter_etape(index)
	local e = ETAPES[index];
	if not e then
		return;
	end;
	core:add_listener(
		"balcktoof_listerner" .. index,
		e.evenement,
		true,
		function()
			cm:complete_scripted_mission_objective(GROM, e.cle, "grom_mission_" .. tostring(index), true);
		end,
		true
	);
end;

local function lancer_etape(index)
	local e = ETAPES[index];
	if not e then
		return;
	end;
	local mm = mission_manager:new(GROM, e.cle);
	mm:add_new_objective("SCRIPTED");
	mm:add_condition("script_key grom_mission_" .. tostring(index));
	mm:add_condition("override_text mission_text_text_" .. e.objectif);
	mm:set_mission_issuer("BLACK_TOOF");
	for _, charge in ipairs(e.charges) do
		mm:add_payload(charge);
	end;
	mm:set_should_whitelist(false);
	cm:callback(function() mm:trigger() end, 0.2);
	ecouter_etape(index);
end;


function saison_grom_histoire()
	local grom = cm:get_faction(GROM);
	if not grom or not grom:is_human() then
		return;
	end;
	-- les fonctions de CA sont globales et appelées par leur nom : on remplace les étapes hors carte
	setup_black_toofs_prophecies = propheties;
	setup_black_toof_scripted_mission = lancer_etape;
	setup_black_toof_mission_listener = ecouter_etape;
	-- l'écouteur de suite de CA ne connaît que ses clés : après nos missions 3 et 4, la suite est donnée ici
	saison_ecouteur(
		"saison_grom_suite_dent_noire",
		"MissionSucceeded",
		function(context)
			local cle = context:mission():mission_record_key();
			return context:faction():name() == GROM and (cle == ETAPES[3].cle or cle == ETAPES[5].cle);
		end,
		function(context)
			if context:mission():mission_record_key() == ETAPES[3].cle then
				trigger_black_toof_mission(4);
			else
				trigger_black_toof_mission(6);
			end;
		end,
		true
	);
	local suivante_de_ca = trigger_black_toof_mission;
	trigger_black_toof_mission = function(index)
		if index >= DERNIERE_DE_CA then
			out("La Saison des Revelations : Revanche de Dent-Noire achevee (Tor Yvresse hors de la carte)");
			return;
		end;
		suivante_de_ca(index);
	end;
	add_grom_story_listeners();
	out("La Saison des Revelations : Revanche de Dent-Noire (histoire de Grom de CA, adaptee)");
	-- l'Aigle de la marmite (audit de cohérence du 25.09.2026) : CA le donne à la réussite de SA quête de la Hache aux
	-- Empires (wh3_main_ie_qb_grn_grom_axe_of_grom, wh2_dlc15_grom_cauldron.lua l. 255-257) ; notre copie de la quête
	-- a sa propre clé, et la réussir ne débloquait rien
	saison_ecouteur(
		"saison_grom_aigle",
		"MissionSucceeded",
		function(context)
			return context:faction():name() == GROM and context:mission():mission_record_key() == "saison_qb_grn_grom_axe_of_grom";
		end,
		function()
			if is_function(unlock_ingredient) then
				unlock_ingredient("wh2_dlc15_eagle");
				out("La Saison des Revelations : Aigle debloque dans la marmite de Grom (quete de la Hache)");
			end;
		end,
		false
	);
end;
