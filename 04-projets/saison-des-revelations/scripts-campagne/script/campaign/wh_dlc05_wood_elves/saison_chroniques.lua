-----------------------------------------------------------------------------------
--	La Saison des Révélations : les Chroniques de la Saison, chaînes de quêtes des seigneurs de WH3 jouables sur notre
--	carte (Alberic, la Fée Enchanteresse, Morghur, le Duc rouge, Drycha, Heinrich Kemmler, Grom la Panse).
--
--	Demande de Charles (23.09.2026) : des quêtes « réalistes, dans le plot » de la Saison de CA, tirées du lore de la
--	région. Dossier : 05-journal\2026-09-22-gameplay-wh3\lore-region-saison.md (§ 6 : seize quêtes ; rien de ce qu'il
--	marque incertain n'est affirmé dans les textes). Modèle de CA : wh3_dlc27_dechala_narrative.lua (missions du tableau
--	missions, objectifs posés par mission_manager, émetteur CLAN_ELDERS, enchaînement sur MissionSucceeded).
--
--	Syntaxe des objectifs relevée chez CA : DEFEAT_N_ARMIES_OF_FACTION (total, subculture) ; ELIMINATE_CHARACTER_IN_BATTLE
--	(character <cqi du personnage>, faction) ; RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING et
--	CONTROL_N_REGIONS_INCLUDING (total, region...) ; CONTROL_N_PROVINCES_INCLUDING (total, province...) ;
--	CONSTRUCT_N_BUILDINGS_INCLUDING (total, faction, building_level) ; SCRIPTED (script_key, override_text), rempli par
--	cm:complete_scripted_mission_objective. Chaque quête a une limite de tours : échouée, la chronique passe à la suivante.
--
--	Missions (tableau missions, lot 12 de donnees_campagne.py) et textes (textes_gameplay.json) : saison_chronique_*.
--	Seulement en solo, pour la faction humaine ; état sauvegardé (saison_chronique_<faction> = étape en cours ; au-delà
--	de la dernière : terminée). Rien n'est écrit au premier tour : la chronique commence au tour 2.
--
--	Batailles finales (demande de Charles, 23.09.2026 : « des batailles finales, dans les localisations importantes liées
--	au lore ») : la dernière étape de chaque chronique pose une armée de premier rang, à un lieu du lore, sur une case
--	franchissable (couches de WH1), sous une faction de la carte qui lui est hostile ; elle y attend le joueur (cible
--	« LOCATION » de l'invasion de CA : l'IA ne la déplace pas). La mission est émise quand l'armée est posée : vaincre son
--	général (ELIMINATE_CHARACTER_IN_BATTLE). Pas de limite de tours : la finale attend le joueur.
--
--	Échos de la Saison (« jouable des centaines de tours ») : la chronique finie, tous les 12 à 18 tours, une armée ennemie
--	paraît à un lieu du lore tiré au sort dans la liste du seigneur (jamais deux fois de suite le même), plus aguerrie à
--	chaque écho ; mission saison_echo_<seigneur> (vaincre son général en 25 tours, récompense croissante). Échouée,
--	l'armée est rendue à l'IA et rôde. La mission n'a ni rappel ni objectif scripté : CA permet de la réémettre.
-----------------------------------------------------------------------------------
-- 23.09.2026 : écouteurs de début de tour sur FactionBeginTurnPhaseNormal (et non FactionTurnStart) : même
-- moment pour le joueur, et seul évènement de début de tour que le mode « l'IA joue tout » des essais
-- automatiques envoie (erreur 143) ; CA l'emploie aussi pour des factions humaines.

local PREFIXE = "saison_chronique_";
local EMETTEUR = "CLAN_ELDERS";

local ALBERIC = "wh_main_brt_bordeleaux";
local FEE = "wh_main_brt_carcassonne";
local HARDE = "wh_dlc05_bst_morghur_herd";
local MOUSILLON = "wh_main_vmp_mousillon";
local DRYCHA = "wh2_dlc16_wef_drycha";
local KEMMLER = "wh2_dlc11_vmp_the_barrow_legion";
local GROM = "wh2_dlc15_grn_broken_axe";
local ORION = "wh_dlc05_wef_wood_elves";
local DURTHU = "wh_dlc05_wef_argwylon";
local SOEURS = "wh2_dlc16_wef_sisters_of_twilight";		-- 10e seigneure (24.09.2026)

local SC_BETES = "wh_dlc03_sc_bst_beastmen";
local SC_VAMPIRES = "wh_main_sc_vmp_vampire_counts";
local SC_BRETONNIE = "wh_main_sc_brt_bretonnia";
local SC_ELFES = "wh_dlc05_sc_wef_wood_elves";
local SC_NAINS = "wh_main_sc_dwf_dwarfs";
local SC_PEAUX_VERTES = "wh_main_sc_grn_greenskins";

-- duchés bretons de la carte, avec leur capitale (Réveil des ducs)
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


-- le personnage d'un sous-type dans une faction (Morghur peut ne plus être chef de faction : saison_histoire.lua)
local function personnage(cle_faction, sous_type)
	local f = cm:get_faction(cle_faction);
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


local function defaite_armees(total, sous_culture)
	return function(mm)
		mm:add_new_objective("DEFEAT_N_ARMIES_OF_FACTION");
		mm:add_condition("total " .. total);
		mm:add_condition("subculture " .. sous_culture);
	end;
end;


local function regions(type_objectif, total, liste)
	return function(mm)
		mm:add_new_objective(type_objectif);
		mm:add_condition("total " .. total);
		for i = 1, #liste do
			mm:add_condition("region " .. liste[i]);
		end;
	end;
end;


local function eliminer(cle_faction, sous_type)
	return function(mm)
		local c = personnage(cle_faction, sous_type);
		if not c then
			-- personnage disparu entre possible() et l'émission : pas d'objectif (mission seule : non créée, étape sautée
			-- par declencher) plutôt qu'une erreur qui laisserait la chronique sans mission (audit de fluidité, T16 / S9)
			out("La Saison des Revelations : objectif d'elimination sans personnage (" .. tostring(sous_type) .. ")");
			return;
		end;
		mm:add_new_objective("ELIMINATE_CHARACTER_IN_BATTLE");
		mm:add_condition("character " .. c:command_queue_index());
		mm:add_condition("faction " .. cle_faction);
	end;
end;


local function scripte(cle_script)
	return function(mm)
		mm:add_new_objective("SCRIPTED");
		mm:add_condition("script_key " .. cle_script);
		mm:add_condition("override_text mission_text_text_" .. cle_script);
	end;
end;


-- plusieurs objectifs dans une même mission
local function et(...)
	local parties = {...};
	return function(mm, faction)
		for i = 1, #parties do
			parties[i](mm, faction);
		end;
	end;
end;


local function vivant(cle_faction, sous_type)
	return function()
		return personnage(cle_faction, sous_type) and true or false;
	end;
end;


local function argent(n)
	return "money " .. n;
end;


local function objet(cle)
	return "add_ancillary_to_faction_pool{ancillary_key " .. cle .. ";}";
end;


local function unite(cle, n)
	return "add_mercenary_to_faction_pool{unit_key " .. cle .. ";amount " .. (n or 1) .. ";}";
end;


-- remplit l'objectif scripté et retire les écouteurs qui le guettaient (un seul remplissage)
local function completer(faction, cle_mission, cle_script, ecouteurs)
	for i = 1, #(ecouteurs or {}) do
		core:remove_listener(ecouteurs[i]);
	end;
	cm:complete_scripted_mission_objective(faction, cle_mission, cle_script, true);
end;


-- Armées des batailles finales (unités de CA ; 18 unités et le général).
local ARMEE_HARDE = "wh_dlc03_bst_inf_bestigor_herd_0,wh_dlc03_bst_inf_bestigor_herd_0,wh_dlc03_bst_inf_minotaurs_1,"
	.. "wh_dlc03_bst_inf_minotaurs_2,wh_dlc03_bst_inf_gor_herd_1,wh_dlc03_bst_inf_gor_herd_1,wh_dlc03_bst_inf_gor_herd_0,"
	.. "wh_dlc03_bst_inf_ungor_raiders_0,wh_dlc03_bst_inf_ungor_raiders_0,wh_dlc03_bst_inf_centigors_1,"
	.. "wh_dlc03_bst_inf_centigors_2,wh_dlc03_bst_cav_razorgor_chariot_0,wh_dlc03_bst_inf_cygor_0,wh_dlc03_bst_mon_giant_0,"
	.. "wh2_dlc17_bst_mon_ghorgon_0,wh2_dlc17_bst_mon_jabberslythe_0,wh_dlc03_bst_mon_chaos_spawn_0,wh_dlc05_bst_mon_harpies_0";
local ARMEE_ESPRITS = "wh_dlc05_wef_mon_treeman_0,wh_dlc05_wef_mon_treeman_0,wh_dlc05_wef_mon_treekin_0,"
	.. "wh_dlc05_wef_mon_treekin_0,wh_dlc05_wef_mon_treekin_0,wh_dlc05_wef_inf_dryads_0,wh_dlc05_wef_inf_dryads_0,"
	.. "wh_dlc05_wef_inf_eternal_guard_0,wh_dlc05_wef_inf_eternal_guard_0,wh_dlc05_wef_inf_wardancers_0,"
	.. "wh_dlc05_wef_inf_wardancers_0,wh_dlc05_wef_cav_wild_riders_0,wh_dlc05_wef_cav_wild_riders_0,"
	.. "wh_dlc05_wef_inf_waywatchers_0,wh_dlc05_wef_inf_waywatchers_0,wh_dlc05_wef_inf_glade_guard_2,"
	.. "wh_dlc05_wef_inf_glade_guard_2,wh_dlc05_wef_forest_dragon_0";
local ARMEE_CHASSE = "wh_dlc05_wef_cav_wild_riders_1,wh_dlc05_wef_cav_wild_riders_1,wh_dlc05_wef_cav_wild_riders_1,"
	.. "wh_dlc05_wef_cav_glade_riders_1,wh_dlc05_wef_cav_glade_riders_1,wh_dlc05_wef_inf_wardancers_1,"
	.. "wh_dlc05_wef_inf_wardancers_1,wh_dlc05_wef_inf_eternal_guard_1,wh_dlc05_wef_inf_eternal_guard_1,"
	.. "wh_dlc05_wef_inf_waywatchers_0,wh_dlc05_wef_inf_waywatchers_0,wh_dlc05_wef_inf_glade_guard_2,"
	.. "wh_dlc05_wef_inf_glade_guard_2,wh_dlc05_wef_inf_deepwood_scouts_1,wh_dlc05_wef_cav_hawk_riders_0,"
	.. "wh_dlc05_wef_mon_great_eagle_0,wh_dlc05_wef_mon_treekin_0,wh_dlc05_wef_cav_sisters_thorn_0";
local ARMEE_CROISADE = "wh_main_brt_cav_grail_knights,wh_main_brt_cav_grail_knights,wh_main_brt_cav_grail_knights,"
	.. "wh_dlc07_brt_cav_questing_knights_0,wh_dlc07_brt_cav_questing_knights_0,wh_main_brt_cav_knights_of_the_realm,"
	.. "wh_main_brt_cav_knights_of_the_realm,wh_main_brt_cav_knights_of_the_realm,wh_main_brt_cav_pegasus_knights,"
	.. "wh_main_brt_cav_pegasus_knights,wh_dlc07_brt_inf_battle_pilgrims_0,wh_dlc07_brt_inf_battle_pilgrims_0,"
	.. "wh_dlc07_brt_inf_men_at_arms_2,wh_dlc07_brt_inf_men_at_arms_2,wh_dlc07_brt_inf_peasant_bowmen_2,"
	.. "wh_dlc07_brt_inf_peasant_bowmen_2,wh_dlc07_brt_art_blessed_field_trebuchet_0,wh_dlc07_brt_inf_grail_reliquae_0";
local ARMEE_OST = "wh_main_brt_cav_knights_of_the_realm,wh_dlc07_brt_cav_royal_hippogryph_knights_0,"
	.. "wh_main_brt_cav_knights_of_the_realm,wh_dlc07_brt_cav_questing_knights_0,wh_main_brt_cav_grail_knights,"
	.. "wh_main_brt_cav_grail_knights,wh_dlc07_brt_cav_knights_errant_0,wh_dlc07_brt_cav_knights_errant_0,"
	.. "wh_main_brt_cav_pegasus_knights,wh_dlc07_brt_inf_men_at_arms_1,wh_dlc07_brt_inf_men_at_arms_1,"
	.. "wh_main_brt_inf_spearmen_at_arms,wh_main_brt_inf_spearmen_at_arms,wh_dlc07_brt_inf_peasant_bowmen_1,"
	.. "wh_dlc07_brt_inf_peasant_bowmen_1,wh_main_brt_art_field_trebuchet,wh_dlc07_brt_inf_battle_pilgrims_0,"
	.. "wh_dlc07_brt_inf_grail_reliquae_0";

local BRETONS = {"wh_main_brt_bordeleaux", "wh3_main_brt_aquitaine", "wh_main_brt_bastonne", "wh_main_brt_carcassonne",
	"wh_dlc05_brt_quenelles", "wh_main_brt_parravon", "wh_dlc05_brt_montfort", "wh_dlc05_brt_brionne",
	"wh_dlc05_brt_gisoroux"};
local ASRAI = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_argwylon", "wh_dlc05_wef_torgovann", "wh_dlc05_wef_wydrioth"};

local ARMEE_MORTS = "wh_main_vmp_inf_grave_guard_1,wh_main_vmp_inf_grave_guard_1,wh_main_vmp_inf_grave_guard_0,"
	.. "wh_main_vmp_inf_grave_guard_0,wh_main_vmp_inf_skeleton_warriors_1,wh_main_vmp_inf_skeleton_warriors_1,"
	.. "wh_main_vmp_inf_crypt_ghouls,wh_main_vmp_inf_crypt_ghouls,wh_main_vmp_cav_black_knights_3,"
	.. "wh_main_vmp_cav_black_knights_3,wh_main_vmp_cav_hexwraiths,wh_main_vmp_inf_cairn_wraiths,wh_main_vmp_mon_vargheists,"
	.. "wh_main_vmp_mon_crypt_horrors,wh_main_vmp_mon_crypt_horrors,wh_main_vmp_mon_terrorgheist,wh_main_vmp_mon_varghulf,"
	.. "wh_main_vmp_veh_black_coach";
local ARMEE_PEAUX_VERTES = "wh_main_grn_inf_black_orcs,wh_main_grn_inf_black_orcs,wh_main_grn_inf_black_orcs,"
	.. "wh_main_grn_inf_orc_big_uns,wh_main_grn_inf_orc_big_uns,wh_main_grn_inf_orc_big_uns,wh_main_grn_inf_night_goblins,"
	.. "wh_main_grn_inf_night_goblins,wh_main_grn_inf_night_goblin_fanatics,wh_main_grn_inf_orc_arrer_boyz,"
	.. "wh_main_grn_inf_orc_arrer_boyz,wh_main_grn_cav_orc_boar_boy_big_uns,wh_main_grn_cav_orc_boar_boy_big_uns,"
	.. "wh_main_grn_mon_trolls,wh_main_grn_mon_trolls,wh_main_grn_mon_giant,wh_main_grn_mon_arachnarok_spider_0,"
	.. "wh_main_grn_art_doom_diver_catapult";
local ARMEE_NAINS = "wh_main_dwf_inf_hammerers,wh_main_dwf_inf_hammerers,wh_main_dwf_inf_ironbreakers,"
	.. "wh_main_dwf_inf_ironbreakers,wh_main_dwf_inf_longbeards_1,wh_main_dwf_inf_longbeards_1,wh_main_dwf_inf_dwarf_warrior_1,"
	.. "wh_main_dwf_inf_dwarf_warrior_1,wh_main_dwf_inf_thunderers_0,wh_main_dwf_inf_thunderers_0,"
	.. "wh_main_dwf_inf_quarrellers_1,wh_main_dwf_inf_quarrellers_1,wh_main_dwf_inf_slayers,wh_main_dwf_inf_irondrakes_0,"
	.. "wh_main_dwf_art_cannon,wh_main_dwf_art_organ_gun,wh_main_dwf_art_flame_cannon,wh_main_dwf_veh_gyrocopter_1";

-- Adversaires des étapes « brisez N armées » (audit de gameplay, point 6) : l'ennemi du texte, posé à son lieu du lore,
-- plus léger que les armées des finales (ces étapes viennent tôt) ; il compte pour l'objectif (même sous-culture).
local ARMEE_MORTS_LEGERE = "wh_main_vmp_inf_skeleton_warriors_0,wh_main_vmp_inf_skeleton_warriors_0,"
	.. "wh_main_vmp_inf_skeleton_warriors_0,wh_main_vmp_inf_zombie,wh_main_vmp_inf_zombie,wh_main_vmp_inf_crypt_ghouls,"
	.. "wh_main_vmp_inf_crypt_ghouls,wh_main_vmp_mon_dire_wolves,wh_main_vmp_mon_fell_bats,wh_main_vmp_inf_grave_guard_0,"
	.. "wh_main_vmp_cav_black_knights_0";
local ARMEE_HARDE_LEGERE = "wh_dlc03_bst_inf_ungor_herd_1,wh_dlc03_bst_inf_ungor_herd_1,wh_dlc03_bst_inf_ungor_raiders_0,"
	.. "wh_dlc03_bst_inf_ungor_raiders_0,wh_dlc03_bst_inf_gor_herd_0,wh_dlc03_bst_inf_gor_herd_0,wh_dlc03_bst_inf_gor_herd_1,"
	.. "wh_dlc03_bst_inf_chaos_warhounds_0,wh_dlc03_bst_inf_centigors_0,wh_dlc03_bst_inf_bestigor_herd_0,"
	.. "wh_dlc03_bst_inf_minotaurs_0";
-- bande de la harde au camp de Tal Jul-Finel, première étape des Sœurs (bêta, 25.09.2026 : l'armée légère entière,
-- bestigors et minotaure compris, rayait au tour 4 leur armée unique, sans colonie ; ici des Ungors, des Gors et des
-- chiens, la harde qui campe dans la salle tombée)
local ARMEE_HARDE_SOEURS = "wh_dlc03_bst_inf_ungor_herd_1,wh_dlc03_bst_inf_ungor_herd_1,wh_dlc03_bst_inf_ungor_raiders_0,"
	.. "wh_dlc03_bst_inf_gor_herd_0,wh_dlc03_bst_inf_gor_herd_0,wh_dlc03_bst_inf_chaos_warhounds_0";
local ARMEE_OST_LEGER ="wh_dlc07_brt_inf_men_at_arms_1,wh_dlc07_brt_inf_men_at_arms_1,wh_main_brt_inf_spearmen_at_arms,"
	.. "wh_main_brt_inf_spearmen_at_arms,wh_dlc07_brt_inf_peasant_bowmen_1,wh_main_brt_inf_peasant_bowmen,"
	.. "wh_main_brt_cav_mounted_yeomen_0,wh_dlc07_brt_cav_knights_errant_0,wh_dlc07_brt_cav_knights_errant_0,"
	.. "wh_main_brt_cav_knights_of_the_realm,wh_main_brt_art_field_trebuchet";
local ARMEE_ASRAI_LEGERE = "wh_dlc05_wef_inf_glade_guard_0,wh_dlc05_wef_inf_glade_guard_0,wh_dlc05_wef_inf_glade_guard_0,"
	.. "wh_dlc05_wef_inf_eternal_guard_0,wh_dlc05_wef_inf_eternal_guard_0,wh_dlc05_wef_inf_dryads_0,wh_dlc05_wef_inf_dryads_0,"
	.. "wh_dlc05_wef_cav_glade_riders_0,wh_dlc05_wef_inf_wardancers_0,wh_dlc05_wef_inf_deepwood_scouts_0,"
	.. "wh_dlc05_wef_mon_treekin_0";
local ARMEE_NAINS_LEGERE = "wh_main_dwf_inf_dwarf_warrior_0,wh_main_dwf_inf_dwarf_warrior_0,wh_main_dwf_inf_dwarf_warrior_0,"
	.. "wh_main_dwf_inf_quarrellers_0,wh_main_dwf_inf_quarrellers_0,wh_main_dwf_inf_thunderers_0,wh_main_dwf_inf_longbeards,"
	.. "wh_main_dwf_inf_ironbreakers,wh_main_dwf_inf_miners_0,wh_main_dwf_art_cannon";

-- les morts du Duc Rouge autour d'une chapelle du Graal (Chroniques de Félix, saison_felix.lua) : spectres en nombre
local ARMEE_SPECTRES = "wh_main_vmp_inf_cairn_wraiths,wh_main_vmp_inf_cairn_wraiths,wh_main_vmp_inf_cairn_wraiths,"
	.. "wh_main_vmp_cav_hexwraiths,wh_main_vmp_cav_hexwraiths,wh_main_vmp_cav_black_knights_3,wh_main_vmp_cav_black_knights_3,"
	.. "wh_dlc02_vmp_cav_blood_knights_0,wh_dlc02_vmp_cav_blood_knights_0,wh_main_vmp_inf_grave_guard_1,"
	.. "wh_main_vmp_inf_grave_guard_1,wh_main_vmp_inf_skeleton_warriors_1,wh_main_vmp_inf_skeleton_warriors_1,"
	.. "wh_main_vmp_mon_terrorgheist,wh_dlc04_vmp_veh_mortis_engine_0,wh_main_vmp_veh_black_coach,"
	.. "wh_dlc04_vmp_veh_corpse_cart_1,wh_main_vmp_cav_hexwraiths";

local ENTRETIEN_GRATUIT = "wh_main_bundle_military_upkeep_free_force";

-- Les armées des finales et des Échos sont posées dans des factions de bataille de CA (« _qb », présentes dans notre
-- startpos, lot 13, et qu'aucun script de CA n'emploie), comme CA pour la quête de Coeddil
-- (wh2_dlc16_drycha_coeddil_unchained.lua : invasion dans wh2_dlc16_emp_empire_qb8, diplomacie fermée) : en guerre avec
-- le seul joueur, elles ne sont ni confédérées ni détruites par une IA (audit du code, G5 et G6). Chacune porte un nom
-- à nous (campaign_localised_strings, lot 12). Nains : wh_main_dwf_dwarfs_qb2 (lot 13, startpos à régénérer) ; tant
-- qu'elle manque au startpos, Karak Ziflin (liste de la menace).
local QB_PAR_ARMEE = {
	[ARMEE_HARDE] = "wh_dlc03_bst_beastmen_qb2",
	[ARMEE_HARDE_SOEURS] = "wh_dlc03_bst_beastmen_qb2",
	[ARMEE_MORTS] = "wh_main_vmp_vampire_counts_qb2",
	[ARMEE_SPECTRES] = "wh_main_vmp_vampire_counts_qb2",
	[ARMEE_PEAUX_VERTES] = "wh_main_grn_greenskins_qb2",
	[ARMEE_OST] = "wh_main_brt_bretonnia_qb2",
	[ARMEE_CROISADE] = "wh_main_brt_bretonnia_qb2",
	[ARMEE_ESPRITS] = "wh2_dlc16_wef_wood_elves_qb6",
	[ARMEE_CHASSE] = "wh2_dlc16_wef_wood_elves_qb7",
	[ARMEE_NAINS] = "wh_main_dwf_dwarfs_qb2",
	[ARMEE_MORTS_LEGERE] = "wh_main_vmp_vampire_counts_qb2",
	[ARMEE_HARDE_LEGERE] = "wh_dlc03_bst_beastmen_qb2",
	[ARMEE_OST_LEGER] = "wh_main_brt_bretonnia_qb2",
	[ARMEE_ASRAI_LEGERE] = "wh2_dlc16_wef_wood_elves_qb7",
	[ARMEE_NAINS_LEGERE] = "wh_main_dwf_dwarfs_qb2"
};
local NOMS_QB = {
	wh_dlc03_bst_beastmen_qb2 = "saison_nom_qb_harde",
	wh_main_vmp_vampire_counts_qb2 = "saison_nom_qb_morts",
	wh_main_grn_greenskins_qb2 = "saison_nom_qb_peaux_vertes",
	wh_main_brt_bretonnia_qb2 = "saison_nom_qb_ost",
	wh2_dlc16_wef_wood_elves_qb6 = "saison_nom_qb_esprits",
	wh2_dlc16_wef_wood_elves_qb7 = "saison_nom_qb_chasse",
	wh_main_dwf_dwarfs_qb2 = "saison_nom_qb_nains"
};
-- rayon d'agression (carré de la distance en hex logiques, invasion:find_aggro_target) : une armée du joueur à moins de
-- 9 hex est attaquée ; poursuite de 2 tours au plus, puis retour au lieu
local AGRESSION = {81, 1, 2};


-- nom de nos factions de bataille et diplomatie fermée (à chaque chargement et avant chaque armée)
local function preparer_qb(qb)
	if cm:get_faction(qb) then
		cm:change_localised_faction_name(qb, "campaign_localised_strings_string_" .. NOMS_QB[qb]);
		cm:force_diplomacy("all", "faction:" .. qb, "all", false, false, true);
		cm:force_diplomacy("faction:" .. qb, "all", "all", false, false, true);
	end;
end;

-- Échos de la Saison : les menaces (lieu en hex logique, case franchissable des couches de WH1, à plus de 3,5 hex d'une
-- colonie), par seigneur. Lieux et adversaires tirés du lore (recherches du 23.09.2026, scratchpad\lore-quetes\ :
-- Knights of the Grail, livres d'armée de Bretonnie et des Elfes sylvains 8e, White Dwarf 309).
local function menace(lieu, factions, armee, general)
	return {lieu = lieu, factions = factions, armee = armee, general = general};
end;
local PEAUX_VERTES = {"wh_main_grn_skullsmasherz", GROM};
local MORTS = {MOUSILLON, KEMMLER};
local M = {
	-- hardes : le Pic d'Argent (WH1) ; la cachette de St Jacques (WH1) ; la lisière de la forêt de Châlons, dont les hardes
	-- razzient les villages de Bordeleaux (KotG) ; le Val du Malheur en Anmyr, où Morghur fut tué et où les hardes
	-- grossissent chaque année (Elfes sylvains 8e)
	harde_pic = menace({181, 322}, {HARDE}, ARMEE_HARDE, "wh_dlc03_bst_beastlord"),
	harde_cachette = menace({118, 60}, {HARDE}, ARMEE_HARDE, "wh_dlc03_bst_beastlord"),
	harde_chalons = menace({86, 243}, {HARDE}, ARMEE_HARDE, "wh_dlc03_bst_beastlord"),
	harde_val_malheur = menace({202, 198}, {HARDE}, ARMEE_HARDE, "wh_dlc03_bst_beastlord"),
	-- morts : Mousillon ; les tertres de Cuileux, gardés par leurs morts (KotG) ; les Cairns, relevés par Kemmler en
	-- 2495 près de Modryn et Cavaroc (Elfes sylvains 8e)
	morts_mousillon = menace({48, 303}, MORTS, ARMEE_MORTS, "wh_main_vmp_lord"),
	morts_cuileux = menace({100, 180}, MORTS, ARMEE_MORTS, "wh_main_vmp_lord"),
	morts_cairnost = menace({203, 70}, {KEMMLER, MOUSILLON}, ARMEE_MORTS, "wh_main_vmp_lord"),
	-- peaux-vertes : le Massif Orcal ; Fort Solstice, dont le fantôme ne réclame que du sang d'Orque (KotG) ; les basses
	-- terres de Parravon sur la Grismerie, où la Chasse d'Orion écrasa la Waaagh! Gashrak (Elfes sylvains 8e)
	peaux_vertes_massif = menace({135, 268}, PEAUX_VERTES, ARMEE_PEAUX_VERTES, "wh_main_grn_orc_warboss"),
	peaux_vertes_solstice = menace({146, 96}, PEAUX_VERTES, ARMEE_PEAUX_VERTES, "wh_main_grn_orc_warboss"),
	peaux_vertes_grismerie = menace({178, 226}, PEAUX_VERTES, ARMEE_PEAUX_VERTES, "wh_main_grn_orc_warboss"),
	-- nains de Karak Ziflin
	nains_tzor = menace({319, 320}, {"wh_main_dwf_karak_ziflin"}, ARMEE_NAINS, "wh_main_dwf_lord"),
	-- Asrai : le Chêne des Âges et la Clairière du Roi (Talsyn) ; Argwylon (Durthu chez CA) ; les Forêts profondes de
	-- Durthu, où sa rage écrasa les Peaux-vertes (Elfes sylvains 8e)
	asrai_chene = menace({269, 97}, ASRAI, ARMEE_ESPRITS, "wh_dlc05_wef_ancient_treeman"),
	asrai_talsyn = menace({288, 100}, ASRAI, ARMEE_CHASSE, "wh_dlc05_wef_glade_lord"),
	esprits_cascade = menace({266, 218}, {DURTHU, ORION}, ARMEE_ESPRITS, "wh_dlc05_wef_ancient_treeman"),
	esprits_durthu = menace({278, 153}, {DURTHU, ORION, "wh_dlc05_wef_torgovann", "wh_dlc05_wef_wydrioth"}, ARMEE_ESPRITS,
		"wh_dlc05_wef_ancient_treeman"),
	-- ducs bretons : Quenelles (Tancred, ennemi juré de Kemmler) ; l'Aquitaine (décret de Richemont) ; Turris Vigilans,
	-- vigie de Verena face à Mousillon ; Grunere, aux confins de La Maisontaal ; Montfort, dont le duc cherche le repaire
	-- orque de Garban ; Gisoreux, dont les chevaliers furent anéantis par Morghur en Arden (KotG, Elfes sylvains 8e)
	bretons_quenelles = menace({151, 158}, {"wh_dlc05_brt_quenelles", "wh_main_brt_parravon", "wh_dlc05_brt_montfort"},
		ARMEE_OST, "wh_main_brt_lord"),
	bretons_gien = menace({108, 219}, {"wh3_main_brt_aquitaine", "wh_main_brt_bastonne", "wh_main_brt_carcassonne"},
		ARMEE_OST, "wh_main_brt_lord"),
	bretons_turris = menace({65, 276}, BRETONS, ARMEE_CROISADE, "wh_main_brt_lord"),
	bretons_grunere = menace({255, 278}, {"wh_main_brt_parravon", "wh_dlc05_brt_quenelles", "wh_dlc05_brt_montfort"},
		ARMEE_OST, "wh_main_brt_lord"),
	bretons_montfort = menace({162, 308}, {"wh_dlc05_brt_montfort", "wh_main_brt_parravon", "wh_dlc05_brt_quenelles"},
		ARMEE_OST, "wh_main_brt_lord"),
	bretons_gisoreux = menace({97, 355}, {"wh_dlc05_brt_gisoroux", "wh_dlc05_brt_montfort", "wh_main_brt_parravon"},
		ARMEE_OST, "wh_main_brt_lord")
};
SAISON_ECHOS = {
	[ALBERIC] = {cle = "saison_echo_alberic", M.harde_chalons, M.harde_pic, M.morts_mousillon, M.peaux_vertes_massif},
	[FEE] = {cle = "saison_echo_fee", M.peaux_vertes_solstice, M.morts_cuileux, M.harde_pic, M.harde_cachette},
	[HARDE] = {cle = "saison_echo_morghur", M.asrai_chene, M.asrai_talsyn, M.bretons_quenelles, M.bretons_gisoreux},
	[MOUSILLON] = {cle = "saison_echo_duc", M.bretons_turris, M.bretons_quenelles, M.bretons_gien, M.harde_pic},
	[DRYCHA] = {cle = "saison_echo_drycha", M.asrai_talsyn, M.asrai_chene, M.harde_val_malheur, M.bretons_grunere},
	[KEMMLER] = {cle = "saison_echo_kemmler", M.bretons_quenelles, M.nains_tzor, M.esprits_cascade, M.bretons_grunere},
	[GROM] = {cle = "saison_echo_grom", M.esprits_durthu, M.nains_tzor, M.bretons_quenelles, M.bretons_montfort},
	-- les Sœurs (24.09.2026) : les ennemis d'Athel Loren que le lore leur donne (la harde, les Peaux-Vertes des Montagnes
	-- Grises) et les morts des Cairns, près des clairières
	[SOEURS] = {cle = "saison_echo_soeurs", M.harde_val_malheur, M.peaux_vertes_grismerie, M.harde_cachette, M.morts_cairnost},
	-- Orion et Durthu n'ont pas de chronique : leurs échos s'ouvrent quand la bataille du Pic d'Argent est gagnée (fin de
	-- l'histoire de WH1)
	[ORION] = {cle = "saison_echo_orion", ouverture = "wh_dlc05_qb_wef_mini_silver_spire", M.harde_cachette, M.harde_pic,
		M.morts_cairnost, M.peaux_vertes_grismerie},
	[DURTHU] = {cle = "saison_echo_durthu", ouverture = "wh_dlc05_qb_wef_mini_silver_spire", M.harde_val_malheur, M.harde_pic,
		M.morts_cairnost, M.bretons_quenelles}
};
local ECHO_INTERVALLE = {12, 18};
local ECHEANCE_FINALE = 15;		-- tours d'attente d'une armée de finale avant qu'elle ne marche sur le joueur
local ECHO_TOURS = 25;


-- La faction de la finale : la première de la liste, vivante, autre que le joueur, ni alliée ni vassale ; à défaut, la
-- première qui existe, réveillée (comme la harde de l'histoire, saison_histoire.lua).
local function faction_de_finale(joueur, candidates)
	local j = cm:get_faction(joueur);
	local function amie(f)
		return j and (j:allied_with(f) or f:is_ally_vassal_or_client_state_of(j) or j:is_ally_vassal_or_client_state_of(f));
	end;
	for i = 1, #candidates do
		local f = cm:get_faction(candidates[i]);
		if f and candidates[i] ~= joueur and not f:is_dead() and not amie(f) then
			return candidates[i];
		end;
	end;
	for i = 1, #candidates do
		local f = cm:get_faction(candidates[i]);
		if f and candidates[i] ~= joueur and f:is_dead() and not f:was_confederated() then
			local ok_reveil, err_reveil = pcall(function() cm:awaken_faction_from_death(f) end);
			if not ok_reveil then
				out("La Saison des Revelations : reveil de " .. candidates[i] .. " impossible : " .. tostring(err_reveil));
			end;
			return candidates[i];
		end;
	end;
	return nil;
end;


-----------------------------------------------------------------------------------
--	Écouteurs des objectifs scriptés (remis à chaque chargement pour l'étape en cours)
-----------------------------------------------------------------------------------

-- Alberic : un pacte avec Orion ou Durthu (non-agression ou alliance), ou l'alliance déjà nouée à un début de tour
local function ecouteur_pacte_asrai(faction, cle)
	-- Albéric part sans contact avec les Asrai : leurs capitales découvertes, la diplomatie ouverte (audit de gameplay,
	-- point 5)
	for _, elfe in ipairs({ORION, DURTHU}) do
		local e = cm:get_faction(elfe);
		if e and not e:is_dead() then
			cm:make_diplomacy_available(faction, elfe);
			if e:has_home_region() then
				cm:make_region_visible_in_shroud(faction, e:home_region():name());
			end;
		end;
	end;
	local function allie()
		local a = cm:get_faction(faction);
		if not a then
			return false;
		end;
		for _, elfe in ipairs({ORION, DURTHU}) do
			local e = cm:get_faction(elfe);
			if e and not e:is_dead() and (a:allied_with(e) or a:non_aggression_pact_with(e)) then
				return true;
			end;
		end;
		return false;
	end;
	saison_ecouteur(
		PREFIXE .. "pacte_asrai",
		"PositiveDiplomaticEvent",
		function(context)
			local p, r = context:proposer():name(), context:recipient():name();
			local autre = (p == faction and r) or (r == faction and p) or nil;
			if autre ~= ORION and autre ~= DURTHU then
				return false;
			end;
			local ok, pacte = pcall(function() return context:is_non_aggression_pact() or context:is_military_alliance() end);
			return ok and pacte;
		end,
		function()
			completer(faction, cle, "saison_alberic_pacte_asrai", {PREFIXE .. "pacte_asrai_tour"});
		end,
		false
	);
	saison_ecouteur(
		PREFIXE .. "pacte_asrai_tour",
		"FactionBeginTurnPhaseNormal",
		function(context)
			return context:faction():name() == faction and allie();
		end,
		function()
			completer(faction, cle, "saison_alberic_pacte_asrai", {PREFIXE .. "pacte_asrai"});
		end,
		false
	);
end;


-- les Sœurs : « À la porte du Roi » (lore : le conseil les tint à l'écart de la Clairière du Roi jusqu'à ce qu'Orion
-- reconnaisse en elles l'essence de sa reine ; Elfes sylvains 8e éd., pp. 15-27) : les sœurs à la Clairière Royale, et un
-- pacte (non-agression ou alliance) avec Orion
local function ecouteur_soeurs_porte_du_roi(faction, cle)
	local orion = cm:get_faction(ORION);
	if orion and not orion:is_dead() then
		cm:make_diplomacy_available(faction, ORION);
	end;
	cm:make_region_visible_in_shroud(faction, "wh_dlc05_talsyn_yn_ecryl_koiran");
	saison_ecouteur(
		PREFIXE .. "soeurs_porte_du_roi",
		"FactionBeginTurnPhaseNormal",
		function(context)
			if context:faction():name() ~= faction then
				return false;
			end;
			local o = cm:get_faction(ORION);
			if not o or o:is_dead() or not (context:faction():allied_with(o) or context:faction():non_aggression_pact_with(o)) then
				return false;
			end;
			local soeurs = personnage(faction, "wh2_dlc16_wef_sisters_of_twilight");
			return soeurs and soeurs:has_region() and soeurs:region():name() == "wh_dlc05_talsyn_yn_ecryl_koiran";
		end,
		function()
			completer(faction, cle, "saison_soeurs_porte_du_roi");
		end,
		false
	);
end;


-- la Fée : conduite à Quenelles
local function ecouteur_fee_quenelles(faction, cle)
	saison_ecouteur(
		PREFIXE .. "fee_quenelles",
		"FactionBeginTurnPhaseNormal",
		function(context)
			if context:faction():name() ~= faction then
				return false;
			end;
			local fee = personnage(faction, "wh_dlc07_brt_fay_enchantress");
			return fee and fee:has_region() and fee:region():name() == "wh_dlc05_quenelles_quenelles";
		end,
		function()
			completer(faction, cle, "saison_fee_quenelles");
		end,
		false
	);
end;


-- la Fée : trois duchés alliés, vassaux, ou rattachés (faction disparue et capitale à elle)
local function ecouteur_fee_ducs(faction, cle)
	saison_ecouteur(
		PREFIXE .. "fee_ducs",
		"FactionBeginTurnPhaseNormal",
		function(context)
			if context:faction():name() ~= faction then
				return false;
			end;
			local fee = context:faction();
			local n = 0;
			for i = 1, #DUCHES do
				local cle_duche, capitale = DUCHES[i][1], DUCHES[i][2];
				if cle_duche ~= faction then
					local d = cm:get_faction(cle_duche);
					if d and not d:is_dead() then
						if fee:allied_with(d) or d:is_ally_vassal_or_client_state_of(fee) then
							n = n + 1;
						end;
					else
						local r = cm:get_region(capitale);
						if r and not r:is_abandoned() and r:owning_faction():name() == faction then
							n = n + 1;
						end;
					end;
				end;
			end;
			return n >= 3;
		end,
		function()
			completer(faction, cle, "saison_fee_ducs");
		end,
		false
	);
end;


-- Objectif scripté : un personnage d'un sous-type termine un tour du joueur dans l'une des régions données (le lieu
-- d'une quête, sans forcer à le prendre).
local function presence(sous_type, liste, cle_script)
	return function(faction, cle)
		saison_ecouteur(
			PREFIXE .. "presence_" .. cle_script,
			"FactionBeginTurnPhaseNormal",
			function(context)
				if context:faction():name() ~= faction then
					return false;
				end;
				local c = personnage(faction, sous_type);
				if not c or not c:has_region() then
					return false;
				end;
				local r = c:region():name();
				for i = 1, #liste do
					if liste[i] == r then
						return true;
					end;
				end;
				return false;
			end,
			function()
				completer(faction, cle, cle_script);
			end,
			false
		);
	end;
end;


-- les prêtres de Verena scrutent Mousillon depuis Turris Vigilans (Knights of the Grail) : le duché maudit révélé
local REGIONS_MOUSILLON = {"wh_dlc05_mousillon_mousillon", "wh_dlc05_mousillon_castle_rachard", "wh_dlc05_mousillon_martel",
	"wh_dlc05_mousillon_yremy"};
local function reveler_mousillon(faction)
	for i = 1, #REGIONS_MOUSILLON do
		cm:make_region_visible_in_shroud(faction, REGIONS_MOUSILLON[i]);
	end;
end;


-----------------------------------------------------------------------------------
--	Les chroniques. Pour chaque étape : cle (mission), objectifs(mm, faction), recompenses, tours (limite), et au
--	besoin possible() (sinon l'étape est sautée), ecouteurs(faction, cle), apres(faction) (à la réussite), finale.
--	Refonte du 23.09.2026 (demande de Charles : « tout loreful ») : chaque étape suit un fait sourcé des recherches
--	scratchpad\lore-quetes\ (bretonnie-grom.md, foret-drycha-morghur.md, morts-kemmler-duc.md) ; les extrapolations y
--	sont signalées. Aucune année n'est écrite dans les textes (les sources divergent).
-----------------------------------------------------------------------------------

SAISON_CHRONIQUES = {
	-- Alberic de Bordeleaux : la vigie de Turris Vigilans face à Mousillon, les villages de la lisière de Châlons, le
	-- pacte de Loren (Gaston de Galliard), Morghur, l'Humble Chapelle
	[ALBERIC] = {
		tour_debut = 2,
		{cle = "saison_chronique_alberic_1", adversaire = {lieu = {48, 303}, factions = MORTS, armee = ARMEE_MORTS_LEGERE, general = "wh_main_vmp_lord"},
		 objectifs = et(defaite_armees(2, SC_VAMPIRES),
		                regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_bordeleaux_turris_vigilans"})),
		 tours = 25, recompenses = {argent(1500)}, apres = reveler_mousillon},
		{cle = "saison_chronique_alberic_2", adversaire = {lieu = {86, 243}, factions = {HARDE}, armee = ARMEE_HARDE_LEGERE, general = "wh_dlc03_bst_beastlord"},
		 objectifs = et(defaite_armees(2, SC_BETES),
		                regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_bordeleaux_bordeleaux"})),
		 tours = 25, recompenses = {argent(2000)}},
		{cle = "saison_chronique_alberic_3", objectifs = scripte("saison_alberic_pacte_asrai"), tours = 40,
		 recompenses = {argent(1500)}, ecouteurs = ecouteur_pacte_asrai},
		{cle = "saison_chronique_alberic_4", objectifs = eliminer(HARDE, "wh_dlc05_bst_morghur"), tours = 40,
		 possible = vivant(HARDE, "wh_dlc05_bst_morghur"),
		 recompenses = {argent(3000), unite("wh_main_brt_cav_grail_knights", 1)}},
		-- finale : les morts de Mousillon devant l'Humble Chapelle, bâtie par des paysans à l'ouest de Château Bastonne
		{cle = "saison_chronique_alberic_5",
		 finale = {lieu = {75, 300}, factions = {MOUSILLON, KEMMLER}, armee = ARMEE_MORTS, general = "wh_main_vmp_lord"},
		 recompenses = {argent(6000), unite("wh_dlc07_brt_cav_grail_guardians_0", 1), unite("wh_main_brt_cav_grail_knights", 1)}}
	},

	-- la Fée Enchanteresse : purger la Gasconnie, la Chapelle de l'Enchanteresse près de Château Quenelles, réveiller les
	-- ducs (son rôle canonique), Morghur, le Pic d'Argent (Corrigyn, la Dame du Lac)
	[FEE] = {
		tour_debut = 2,
		{cle = "saison_chronique_fee_1", adversaire = {lieu = {118, 60}, factions = {HARDE}, armee = ARMEE_HARDE_LEGERE, general = "wh_dlc03_bst_beastlord"},
		 objectifs = et(defaite_armees(2, SC_BETES),
		                regions("CONTROL_N_REGIONS_INCLUDING", 4, {"wh_dlc05_carcassonne_castle_carcassonne",
		                        "wh_dlc05_carcassonne_ferignac", "wh_dlc05_carcassonne_st_jacques",
		                        "wh_dlc05_carcassonne_summersfall_fort"})),
		 tours = 25, recompenses = {argent(1500), unite("wh_dlc07_brt_cav_questing_knights_0", 1)}},
		{cle = "saison_chronique_fee_2", objectifs = et(scripte("saison_fee_quenelles"), defaite_armees(1, SC_BETES)),
		 tours = 25, recompenses = {argent(1500)}, ecouteurs = ecouteur_fee_quenelles,
		 apres = function(faction) cm:trigger_dilemma(faction, "wh_dlc07_brt_gifted_children") end},
		{cle = "saison_chronique_fee_3", objectifs = scripte("saison_fee_ducs"), tours = 40,
		 recompenses = {argent(3000)}, ecouteurs = ecouteur_fee_ducs},
		{cle = "saison_chronique_fee_4", objectifs = eliminer(HARDE, "wh_dlc05_bst_morghur"), tours = 40,
		 possible = vivant(HARDE, "wh_dlc05_bst_morghur"),
		 recompenses = {argent(3000), unite("wh_main_brt_cav_grail_knights", 1)}},
		-- finale : le Pic d'Argent
		{cle = "saison_chronique_fee_5",
		 finale = {lieu = {181, 322}, factions = {HARDE}, armee = ARMEE_HARDE, general = "wh_dlc03_bst_beastlord"},
		 recompenses = {argent(6000), unite("wh_dlc07_brt_cav_royal_hippogryph_knights_0", 1),
		                unite("wh_main_brt_cav_grail_knights", 1)}}
	},

	-- Morghur : les totems de la Ruine (quête de CA), le Val du Malheur où il fut tué, le Pic d'Argent, le Chêne
	[HARDE] = {
		tour_debut = 2,
		-- un repaire peau-vert, une forteresse naine et la pierre levée du Cromlech de Cadai : les trois ingrédients de CA
		{cle = "saison_chronique_morghur_1",
		 objectifs = et(regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_massif_orcal_massif_orcal",
		                        "wh_dlc05_massif_orcal_orquemont", "wh_dlc05_grey_mountains_axe_bite_pass",
		                        "wh_dlc05_grey_mountains_gragrut_pass"}),
		                regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_grey_mountains_2_karak_ziflin",
		                        "wh_dlc05_grey_mountains_2_karak_tzor", "wh_dlc05_grey_mountains_2_blackstone_post"}),
		                regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_torgovann_cromlech_cadai"})),
		 tours = 60, recompenses = {argent(1500)}},
		{cle = "saison_chronique_morghur_2", adversaire = {lieu = {202, 198}, factions = ASRAI, armee = ARMEE_ASRAI_LEGERE, general = "wh_dlc05_wef_glade_lord"},
		 objectifs = et(defaite_armees(3, SC_ELFES), scripte("saison_morghur_val_malheur")),
		 ecouteurs = presence("wh_dlc05_bst_morghur", {"wh_dlc05_anmyr_tal_rond"}, "saison_morghur_val_malheur"),
		 possible = vivant(HARDE, "wh_dlc05_bst_morghur"),
		 tours = 35, recompenses = {argent(2000), objet("wh_dlc03_anc_armour_pelt_of_the_shadowgave")}},
		{cle = "saison_chronique_morghur_3",
		 objectifs = regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_montfort_montfort"}),
		 tours = 35, recompenses = {argent(2500)}},
		{cle = "saison_chronique_morghur_4",
		 objectifs = et(regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_oak_of_ages"}),
		                defaite_armees(2, SC_ELFES)),
		 tours = 40, recompenses = {argent(4000)}},
		-- finale : au pied du Chêne, là où Durthu l'abattit jadis
		{cle = "saison_chronique_morghur_5",
		 finale = {lieu = {269, 97}, factions = ASRAI, armee = ARMEE_ESPRITS, general = "wh_dlc05_wef_ancient_treeman"},
		 recompenses = {argent(6000), unite("wh2_dlc17_bst_mon_ghorgon_0", 1), unite("wh_dlc03_bst_inf_cygor_0", 1)}}
	},

	-- le Duc rouge : le Crac de Sang au-dessus de la Morceaux et de Châlons, le sang d'Aquitaine (les deux Champs de
	-- Ceren, le décret de Richemont), la vigie de Verena, le palais scellé de Mousillon, la croisade
	[MOUSILLON] = {
		tour_debut = 2,
		{cle = "saison_chronique_duc_1",
		 objectifs = regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_aquitaine_derrevin_libre"}), tours = 25,
		 recompenses = {argent(1000), unite("wh3_main_vmp_blood_knights_sword_shield", 1),
		                objet("wh2_main_anc_weapon_blade_of_leaping_gold")}},
		{cle = "saison_chronique_duc_2", adversaire = {lieu = {108, 219}, factions = {"wh3_main_brt_aquitaine"}, armee = ARMEE_OST_LEGER, general = "wh_main_brt_lord"},
		 objectifs = et(defaite_armees(2, SC_BRETONNIE),
		                regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_aquitaine_chateau_depee"})),
		 tours = 35, recompenses = {argent(2500), unite("wh3_main_vmp_blood_knights_sword_shield", 1)}},
		{cle = "saison_chronique_duc_3",
		 objectifs = et(regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_bordeleaux_turris_vigilans"}),
		                eliminer(ALBERIC, "wh_dlc07_brt_alberic")),
		 possible = vivant(ALBERIC, "wh_dlc07_brt_alberic"), tours = 40, recompenses = {argent(3000)}},
		{cle = "saison_chronique_duc_4",
		 objectifs = function(mm, faction)
			mm:add_new_objective("CONSTRUCT_N_BUILDINGS_INCLUDING");
			mm:add_condition("total 1");
			mm:add_condition("faction " .. faction);
			mm:add_condition("building_level wh_main_vmp_settlement_major_5");
		 end,
		 tours = 50, recompenses = {argent(3000)}},
		-- finale : une croisade à Turris Vigilans, comme celles qui marchèrent contre Merovech et Maldred
		{cle = "saison_chronique_duc_5",
		 finale = {lieu = {65, 276}, factions = BRETONS, armee = ARMEE_CROISADE, general = "wh_main_brt_lord"},
		 recompenses = {argent(6000), unite("wh3_main_vmp_blood_knights_sword_shield", 2), unite("wh_main_vmp_mon_terrorgheist", 1)}}
	},

	-- Drycha : la cour d'Addaivoch au Val du Malheur, les reliques de la Brienne, le carnage de Parravon (la dernière
	-- relique), le Bosquet de guerre du Malheur (sa victoire de CA), la seconde Trahison à la Clairière du Roi
	[DRYCHA] = {
		tour_debut = 2,
		{cle = "saison_chronique_drycha_1", adversaire = {lieu = {202, 198}, factions = {HARDE}, armee = ARMEE_HARDE_LEGERE, general = "wh_dlc03_bst_beastlord"},
		 objectifs = et(defaite_armees(2, SC_BETES), scripte("saison_drycha_addaivoch")),
		 ecouteurs = presence("wh2_dlc16_wef_drycha", {"wh_dlc05_anmyr_tal_rond"}, "saison_drycha_addaivoch"),
		 tours = 30, recompenses = {argent(1500), unite("wh2_dlc16_wef_inf_malicious_dryads_0", 2)}},
		{cle = "saison_chronique_drycha_2", adversaire = {lieu = {151, 158}, factions = {"wh_dlc05_brt_quenelles"}, armee = ARMEE_OST_LEGER, general = "wh_main_brt_lord"},
		 objectifs = et(defaite_armees(2, SC_BRETONNIE),
		                regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_quenelles_quenelles",
		                        "wh_dlc05_quenelles_brusse", "wh_dlc05_quenelles_laguiller", "wh_dlc05_brionne_muret",
		                        "wh_dlc05_carcassonne_ferignac"})),
		 tours = 30, recompenses = {argent(2000)}},
		{cle = "saison_chronique_drycha_parravon",
		 objectifs = regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 2, {"wh_dlc05_parravon_parravon",
		             "wh_dlc05_parravon_montlac", "wh_dlc05_parravon_grunere"}),
		 tours = 35, recompenses = {argent(2000), unite("wh2_dlc16_wef_mon_malicious_treeman_0", 1)}},
		{cle = "saison_chronique_drycha_3",
		 objectifs = regions("CONTROL_N_REGIONS_INCLUDING", 3, {"wh_dlc05_argwylon_waterfall_palace",
		             "wh_dlc05_wydrioth_crag_halls", "wh_dlc05_torgovann_cromlech_cadai", "wh_dlc05_talsyn_yn_ecryl_koiran",
		             "wh_dlc05_oak_of_ages"}),
		 tours = 50, recompenses = {argent(3000)}},
		-- finale : la Chasse rassemblée à la Clairière du Roi, là où Coeddil massacra jadis les Chevaucheurs sauvages
		{cle = "saison_chronique_drycha_4",
		 finale = {lieu = {288, 100}, factions = ASRAI, armee = ARMEE_CHASSE, general = "wh_dlc05_wef_glade_lord"},
		 recompenses = {argent(6000), unite("wh2_dlc16_wef_mon_malicious_treeman_0", 1),
		                unite("wh2_dlc16_wef_inf_malicious_dryads_0", 2)}}
	},

	-- Heinrich Kemmler : le Livre des Rancunes (Krell), le Défilé de la Hache, le duc de Parravon, les Cairns d'Athel Loren,
	-- le Pont de Montfort contre Tancred II de Quenelles (White Dwarf 309, Elfes sylvains 8e). Ses trois objets viennent de
	-- ses batailles de quête de CA (saison_quetes.lua) : les chroniques donnent des troupes.
	[KEMMLER] = {
		tour_debut = 2,
		{cle = "saison_chronique_kemmler_1", adversaire = {lieu = {319, 320}, factions = {"wh_main_dwf_karak_ziflin"}, armee = ARMEE_NAINS_LEGERE, general = "wh_main_dwf_lord"}, objectifs = defaite_armees(2, SC_NAINS), tours = 25,
		 recompenses = {argent(1000), unite("wh_main_vmp_inf_grave_guard_0", 2)}},
		{cle = "saison_chronique_kemmler_2",
		 objectifs = regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_grey_mountains_axe_bite_pass"}), tours = 30,
		 recompenses = {argent(1000), unite("wh_main_vmp_cav_black_knights_0", 2)}},
		{cle = "saison_chronique_kemmler_3",
		 objectifs = regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_parravon_parravon"}), tours = 40,
		 recompenses = {argent(2000), unite("wh_main_vmp_mon_vargheists", 2)}},
		{cle = "saison_chronique_kemmler_cairns", adversaire = {lieu = {203, 70}, factions = ASRAI, armee = ARMEE_ASRAI_LEGERE, general = "wh_dlc05_wef_glade_lord"}, objectifs = defaite_armees(2, SC_ELFES), tours = 35,
		 recompenses = {argent(2500), unite("wh_main_vmp_mon_terrorgheist", 1), unite("wh_main_vmp_inf_cairn_wraiths", 2)}},
		-- finale : le Pont de Montfort, où un duc de Quenelles est déjà tombé sous la hache de Krell
		{cle = "saison_chronique_kemmler_4",
		 finale = {lieu = {162, 308}, factions = {"wh_dlc05_brt_quenelles", "wh_dlc05_brt_montfort", "wh_main_brt_parravon",
		           "wh_dlc05_brt_brionne", "wh3_main_brt_aquitaine"}, armee = ARMEE_OST, general = "wh_main_brt_lord"},
		 recompenses = {argent(6000), unite("wh_main_vmp_inf_grave_guard_1", 2), unite("wh_main_vmp_veh_black_coach", 1)}}
	},

	-- Grom la Panse, revenu d'outre-mer (sa flotte fit naufrage près des côtes bretonniennes) et rejoint par les tribus du
	-- Massif Orcal : la Vallée de Quenelles, la hache de Gragabad à Brionne, la statue de Grungni, le garde-manger d'Athel
	-- Loren, la lisière en flammes (Quatrième Grande Bataille). Le cadre est une extrapolation, les faits sont du lore.
	[GROM] = {
		tour_debut = 2,
		{cle = "saison_chronique_grom_1", adversaire = {lieu = {151, 158}, factions = {"wh_dlc05_brt_quenelles"}, armee = ARMEE_OST_LEGER, general = "wh_main_brt_lord"},
		 objectifs = et(defaite_armees(3, SC_BRETONNIE),
		                regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_quenelles_quenelles"})),
		 tours = 30, recompenses = {argent(1000), unite("wh_main_grn_mon_giant", 1), unite("wh_main_grn_inf_orc_big_uns", 2)}},
		{cle = "saison_chronique_grom_gragabad",
		 objectifs = regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 1, {"wh_dlc05_brionne_brionne"}),
		 tours = 30, recompenses = {argent(2000)}},
		{cle = "saison_chronique_grom_2",
		 objectifs = regions("RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING", 2, {"wh_dlc05_grey_mountains_2_karak_ziflin",
		             "wh_dlc05_grey_mountains_2_karak_tzor", "wh_dlc05_grey_mountains_2_blackstone_post"}),
		 tours = 45, recompenses = {argent(1000), unite("wh2_dlc15_grn_mon_stone_trolls_0", 2)}},
		{cle = "saison_chronique_grom_3", adversaire = {lieu = {278, 153}, factions = ASRAI, armee = ARMEE_ASRAI_LEGERE, general = "wh_dlc05_wef_glade_lord"}, objectifs = defaite_armees(3, SC_ELFES), tours = 40,
		 recompenses = {argent(3000)}},
		-- finale : la lisière en flammes aux portes de Quenelles
		{cle = "saison_chronique_grom_4",
		 finale = {lieu = {178, 165}, factions = ASRAI, armee = ARMEE_ESPRITS, general = "wh_dlc05_wef_ancient_treeman"},
		 recompenses = {argent(6000), unite("wh_main_grn_mon_giant", 1), unite("wh2_dlc15_grn_mon_stone_trolls_0", 2)}}
	},

	-- les Sœurs du Crépuscule (24.09.2026 ; lore-quetes\soeurs-du-crepuscule.md) : relever leur Grande Salle tombée des
	-- Pics des Pins (Tal Jul Finel, intro de WH1), se faire reconnaître d'Orion à la Clairière du Roi, tenir contre les
	-- Peaux-Vertes des Montagnes Grises (Wydrioth assailli, Elfes sylvains 8e p. 12), vaincre Morghur comme en Arden,
	-- défendre le Chêne. Elles partent sans colonie : l'étape 1 commence au tour 4, et non au tour 2 comme les autres
	-- (24.09.2026, 23 h, partie de comparaison : sans région, elles ne recrutent rien avant d'avoir relevé la salle ; la
	-- harde de l'étape 1, onze unités, patrouille autour d'elle ; deux tours de plus pour s'y installer et recruter).
	[SOEURS] = {
		tour_debut = 4,
		-- bêta (25.09.2026) : aux essais, l'adversaire apparaissait au repli (316, 134), sur la case voisine du départ des
		-- Sœurs (316, 135), et rayait au tour 4 leur armée unique, sans colonie (partie perdue). Camp à 10,8 cases
		-- (328, 132 : case franchissable et entourée, à 8 cases du lieu de lore 326 ; 124), recherche de case courte
		-- (2 et 4 cases), rayon d'agression de 4 cases au lieu de 9 (les Sœurs choisissent le moment), bande plus légère
		-- et chef de niveau 4
		{cle = "saison_chronique_soeurs_1", adversaire = {lieu = {328, 132}, repli = {{328, 133}}, recherche = {2, 4},
		  agression = {16, 1, 1}, niveau = 4, factions = {HARDE}, armee = ARMEE_HARDE_SOEURS, general = "wh_dlc03_bst_beastlord"},
		 objectifs = et(regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_wydrioth_tal_jul_finel"}),
		                defaite_armees(1, SC_BETES)),
		 tours = 20, recompenses = {argent(1500), unite("wh_dlc05_wef_cav_hawk_riders_0", 1)}},
		{cle = "saison_chronique_soeurs_2", objectifs = scripte("saison_soeurs_porte_du_roi"), tours = 35,
		 possible = vivant(ORION, "wh_dlc05_wef_orion"),
		 recompenses = {argent(2000), unite("wh_dlc05_wef_cav_wild_riders_1", 1)}, ecouteurs = ecouteur_soeurs_porte_du_roi},
		{cle = "saison_chronique_soeurs_3", adversaire = {lieu = {178, 226}, factions = PEAUX_VERTES, armee = ARMEE_PEAUX_VERTES, general = "wh_main_grn_orc_warboss"},
		 objectifs = et(defaite_armees(2, SC_PEAUX_VERTES),
		                regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_wydrioth_tal_jul_finel"})),
		 tours = 30, recompenses = {argent(2000), unite("wh_dlc05_wef_mon_great_eagle_0", 1)}},
		-- l'Enclume de Vaul (lore : Daith y forge leurs arcs et leurs lames, Elfes sylvains 8e p. 58) est une autre Grande
		-- Salle tombée de l'hiver (intro de WH1) : la relever rend à Daith son enclume ; sa faveur nourrit leur Forge
		{cle = "saison_chronique_soeurs_enclume",
		 objectifs = regions("CONTROL_N_REGIONS_INCLUDING", 1, {"wh_dlc05_torgovann_vauls_anvil"}),
		 tours = 35, recompenses = {argent(1500)},
		 apres = function(faction)
			cm:faction_add_pooled_resource(faction, "wef_forge_daiths_favour", "battles", 2);
			out("La Saison des Revelations : l'Enclume de Vaul relevee : 2 faveurs de Daith pour " .. faction);
		 end},
		{cle = "saison_chronique_soeurs_4", objectifs = eliminer(HARDE, "wh_dlc05_bst_morghur"), tours = 40,
		 possible = vivant(HARDE, "wh_dlc05_bst_morghur"),
		 recompenses = {argent(3000), unite("wh_dlc05_wef_cav_hawk_riders_0", 2)}},
		-- finale : la harde devant le Chêne des Âges, où réside la reine qu'elles servent
		{cle = "saison_chronique_soeurs_5",
		 finale = {lieu = {269, 97}, factions = {HARDE}, armee = ARMEE_HARDE, general = "wh_dlc03_bst_beastlord"},
		 recompenses = {argent(6000), unite("wh_dlc05_wef_mon_great_eagle_0", 2), unite("wh_dlc05_wef_mon_treekin_0", 1)}}
	}
};


-----------------------------------------------------------------------------------
--	Moteur
-----------------------------------------------------------------------------------

local function etat(faction)
	return cm:get_saved_value(PREFIXE .. faction) or 0;
end;


local function poser_etat(faction, n)
	cm:set_saved_value(PREFIXE .. faction, n);
end;


-- émet la mission d'une étape : ses objectifs, et au besoin un objectif en plus (le général d'une finale). Tous les
-- objectifs sont principaux (comme CA, wh3_cp1_iron_favour.lua) : sinon construct_mission_string exige une récompense
-- par objectif et la mission n'est pas créée (audit du code, B1). Rend false si la mission n'est pas créée (B2).
local function emettre(faction, n, etape, en_plus)
	local mm = mission_manager:new(faction, etape.cle);
	if not mm then
		return false;
	end;
	mm:set_mission_issuer(EMETTEUR);
	mm:set_all_objectives_are_primary();
	local objectifs = etape.objectifs;
	if objectifs then
		objectifs(mm, faction);
	end;
	local ajout = en_plus;
	if ajout then
		ajout(mm, faction);
	end;
	for i = 1, #(etape.recompenses or {}) do
		mm:add_payload(etape.recompenses[i]);
	end;
	if etape.tours then
		mm:set_turn_limit(etape.tours);
	end;
	if mm:trigger() == false then
		script_error("La Saison des Revelations : mission " .. etape.cle .. " non creee");
		return false;
	end;
	-- les écouteurs de l'étape APRÈS une mission créée (revue de la bêta, M2 : posés avant, ils restaient pour une mission
	-- refusée) ; tous attendent un évènement à venir (début de tour, accord diplomatique), rien n'est manqué
	local ecouter = etape.ecouteurs;
	if ecouter then
		ecouter(faction, etape.cle);
	end;
	cm:set_saved_value(PREFIXE .. "emise_" .. faction, cm:model():turn_number());
	out("La Saison des Revelations : chronique " .. faction .. " : etape " .. n .. " (" .. etape.cle .. ")");
	return true;
end;


-- Retrait différé d'une armée posée (plantage de l'essai de Durthu, 23.09.2026 : une notification de fin de tour citait
-- une armée détruite par script un round plus tôt) : l'armée est marquée (valeur sauvegardée), puis détruite au début du
-- tour de sa propre faction, jamais pendant le tour du joueur.
local A_RETIRER = PREFIXE .. "a_retirer";

local function retirer_armee(cle)
	if not invasion_manager:get_invasion(cle) then
		return;
	end;
	local liste = cm:get_saved_value(A_RETIRER) or "";
	if not (";" .. liste .. ";"):find(";" .. cle .. ";", 1, true) then
		cm:set_saved_value(A_RETIRER, liste == "" and cle or (liste .. ";" .. cle));
	end;
end;

local function ecouteur_retraits()
	core:add_listener(
		A_RETIRER,
		"FactionBeginTurnPhaseNormal",
		function()
			return (cm:get_saved_value(A_RETIRER) or "") ~= "";
		end,
		function(context)
			local faction = context:faction():name();
			local reste = {};
			for cle in string.gmatch(cm:get_saved_value(A_RETIRER), "[^;]+") do
				local inv = invasion_manager:get_invasion(cle);
				if inv and inv.faction == faction then
					local ok_retrait, err_retrait = pcall(function() inv:kill(false) end);
					if ok_retrait then
						out("La Saison des Revelations : armee " .. cle .. " retiree (tour de " .. faction .. ")");
					else
						script_error("La Saison des Revelations : retrait de l'armee " .. cle .. " : " .. tostring(err_retrait));
					end;
				elseif inv then
					table.insert(reste, cle);
				end;
			end;
			cm:set_saved_value(A_RETIRER, table.concat(reste, ";"));
		end,
		true
	);
end;


-- Une armée posée à un lieu, sous une faction hostile au joueur, qui y attend (invasion de CA, cible « LOCATION ») ;
-- pret(cqi du général, faction, général) quand elle existe. Rend false si rien ne peut être posé.
local function poser_armee(faction, cle, F, niveau, rang, pret)
	local qb = QB_PAR_ARMEE[F.armee];
	local boss = (qb and cm:get_faction(qb) and qb) or faction_de_finale(faction, F.factions);
	if not boss then
		return false;
	end;
	local ancienne = invasion_manager:get_invasion(cle);
	if ancienne then
		-- armée à cible de région (traque de Richemont) : l'ancienne est rendue à l'IA (release réactive son mouvement)
		-- au lieu de rester figée sans invasion (revue de la bêta, 25.09.2026, lib_campaign_invasion_manager l. 1252)
		if F.cible_region then
			pcall(function() ancienne:release() end);
		end;
		if invasion_manager:get_invasion(cle) then
			invasion_manager:remove_invasion(cle);
		end;
	end;
	-- case d'apparition franchissable : l'invasion de CA ne cherche qu'à courte distance du lieu (essai des Sœurs du
	-- 24.09.2026 : « could not find a valid spawn position » en 326 ; 124) ; on élargit la recherche, comme le récit de
	-- Middenland de CA (distance croissante), et l'on garde le lieu du lore comme cible
	-- 24.09.2026, 22 h 50 : la recherche a encore échoué deux fois sur trois en 326 ; 124 (essais du soir), une fois
	-- réussie en 316 ; 134 : cela dépend de l'état de la carte. Secours : les points de repli du lieu (F.repli), puis la
	-- même recherche faite pour la faction du joueur (case libre pour lui, donc franchissable ; l'invasion de CA vérifie
	-- ensuite pour la faction qui pose)
	local function chercher(qui, x, y)
		for _, distance in ipairs(F.recherche or {3, 8, 15, 25}) do
			local vx, vy = cm:find_valid_spawn_location_for_character_from_position(qui, x, y, false, distance);
			if vx ~= -1 and vy ~= -1 then
				return vx, vy;
			end;
		end;
	end;
	local points = {F.lieu};
	for _, p in ipairs(F.repli or {}) do
		table.insert(points, p);
	end;
	local sx, sy;
	for _, qui in ipairs({boss, faction}) do
		for _, p in ipairs(points) do
			sx, sy = chercher(qui, p[1], p[2]);
			if sx then
				break;
			end;
		end;
		if sx then
			break;
		end;
	end;
	if not sx then
		out("La Saison des Revelations : " .. cle .. " : aucune case libre autour de " .. F.lieu[1] .. ", " .. F.lieu[2]);
		return false;
	end;
	local inv = invasion_manager:new_invasion(cle, boss, F.armee, {sx, sy});
	if not inv then
		return false;
	end;
	if boss == qb then
		-- gardienne du lieu : patrouille sur place, attaque les armées du joueur qui approchent, puis revient
		preparer_qb(qb);
		local lieu = {x = F.lieu[1], y = F.lieu[2]};
		inv:set_target("PATROL", {lieu, lieu});
		inv:should_stop_at_end(false);
		local agr = F.agression or AGRESSION;
		inv:add_aggro_radius(agr[1], {faction}, agr[2], agr[3]);
	elseif F.cible_region then
		-- marche sur une région du joueur et l'attaque (cible REGION de CA, comme finale_en_marche) ; au bout, l'armée
		-- est rendue à l'IA (stop_at_end faux : mouvement réactivé), au lieu d'être figée (revue de la bêta : la traque
		-- de Richemont visait son propre point d'apparition et restait plantée)
		inv:set_target("REGION", F.cible_region, faction);
		inv:should_stop_at_end(false);
	else
		inv:set_target("LOCATION", {x = F.lieu[1], y = F.lieu[2]}, faction);
		inv:should_stop_at_end(true);
	end;
	inv:create_general(false, F.general, "", "", "", "");
	inv:add_character_experience(niveau, true);
	inv:add_unit_experience(rang);
	inv:apply_effect(ENTRETIEN_GRATUIT, -1);
	local ok = inv:start_invasion(
		function(x)
			local chef = x:get_general();
			if chef:is_null_interface() then
				script_error("La Saison des Revelations : armee " .. cle .. " posee sans general");
				return;
			end;
			if boss == qb then
				-- en guerre avec le seul joueur, alliés de personne (comme CA pour Coeddil)
				cm:force_declare_war(qb, faction, false, false);
			end;
			local suite_prete = pret;
			suite_prete(chef:military_force():command_queue_index(), boss, chef);
			if chef:has_region() then
				cm:make_region_visible_in_shroud(faction, chef:region():name());
			end;
			local locale = cm:get_local_faction(true);
			if not saison_en_essai_auto() and locale and locale:name() == faction and locale:is_factions_turn() then
				cm:scroll_camera_from_current(false, 3, {chef:display_position_x(), chef:display_position_y(), 14.768, 0.0, 12.0});
			end;
		end,
		boss ~= qb, false, false
	);
	return ok ~= false;
end;


-- contre une armée posée : l'objectif de CA pour une force précise (wh_grudges.lua) ; cqi de la force
local function vaincre(cqi_force)
	return function(mm)
		mm:add_new_objective("ENGAGE_FORCE");
		mm:add_condition("cqi " .. cqi_force);
		mm:add_condition("requires_victory");
	end;
end;


-- Finale : l'armée posée au lieu du lore ; la mission part quand son général existe. Rend false si rien n'est posé.
local suite;		-- plus bas

local function lancer_finale(faction, n, etape)
	local F = etape.finale;
	cm:set_saved_value(PREFIXE .. "finale_attente_" .. faction, cm:model():turn_number());
	-- force selon le tour (audit de gameplay, point 7) : niveau 20 et rang 4 vers le tour 40, 40 et 9 vers le tour 150
	local tour = cm:model():turn_number();
	local niveau = F.niveau or math.min(math.max(20, 12 + math.floor(tour / 5)), 40);
	local rang = F.rang or math.min(math.max(4, 2 + math.floor(tour / 18)), 9);
	local ok = poser_armee(faction, PREFIXE .. "finale_" .. faction, F, niveau, rang, function(cqi_force)
		cm:set_saved_value(PREFIXE .. "finale_attente_" .. faction, false);
		cm:set_saved_value(PREFIXE .. "finale_tour_" .. faction, cm:model():turn_number());
		cm:set_saved_value(PREFIXE .. "finale_marche_" .. faction, false);
		if not emettre(faction, n, etape, vaincre(cqi_force)) then
			retirer_armee(PREFIXE .. "finale_" .. faction);
			suite(faction, false);
		end;
	end);
	if not ok then
		cm:set_saved_value(PREFIXE .. "finale_attente_" .. faction, false);
	end;
	return ok;
end;


-- Échos : le prochain dans 12 à 18 tours
local function planifier_echo(faction)
	if SAISON_ECHOS[faction] then
		cm:set_saved_value(PREFIXE .. "echo_prochain_" .. faction,
			cm:model():turn_number() + cm:random_number(ECHO_INTERVALLE[2], ECHO_INTERVALLE[1]));
		cm:set_saved_value(PREFIXE .. "echo_en_cours_" .. faction, false);
	end;
end;


-- Échos : une menace tirée au sort (pas la même que la précédente), plus aguerrie à chaque fois
local function lancer_echo(faction)
	local liste = SAISON_ECHOS[faction];
	local k = (cm:get_saved_value(PREFIXE .. "echo_nombre_" .. faction) or 0) + 1;
	local dernier = cm:get_saved_value(PREFIXE .. "echo_dernier_" .. faction) or 0;
	local i = cm:random_number(#liste);
	if i == dernier and #liste > 1 then
		i = i % #liste + 1;
	end;
	cm:set_saved_value(PREFIXE .. "echo_nombre_" .. faction, k);
	cm:set_saved_value(PREFIXE .. "echo_dernier_" .. faction, i);
	cm:set_saved_value(PREFIXE .. "echo_en_cours_" .. faction, cm:model():turn_number());
	-- plus aguerrie à chaque écho, et jamais en dessous de ce que vaut le tour
	local tour = cm:model():turn_number();
	local niveau = math.min(math.max(20 + 2 * k, 12 + math.floor(tour / 5)), 40);
	local rang = math.min(math.max(3 + k, 2 + math.floor(tour / 18)), 9);
	local ok = poser_armee(faction, PREFIXE .. "echo_" .. faction .. "_" .. k, liste[i], niveau, rang,
		function(cqi_force, boss)
			cm:set_saved_value(PREFIXE .. "echo_en_cours_" .. faction, true);
			local mm = mission_manager:new(faction, liste.cle);
			mm:set_mission_issuer(EMETTEUR);
			mm:set_all_objectives_are_primary();
			vaincre(cqi_force)(mm);
			mm:add_payload(argent(math.min(2000 + 500 * k, 8000)));
			mm:set_turn_limit(ECHO_TOURS);
			if mm:trigger() == false then
				script_error("La Saison des Revelations : echo " .. liste.cle .. " non cree");
				retirer_armee(PREFIXE .. "echo_" .. faction .. "_" .. k);
				planifier_echo(faction);
				return;
			end;
			out("La Saison des Revelations : echo " .. k .. " de " .. faction .. " (menace " .. i .. ", " .. boss .. ")");
		end);
	if not ok then
		planifier_echo(faction);
	end;
end;


-- Échéance douce d'une finale (audit de gameplay, point 7) : l'armée qui attend depuis ECHEANCE_FINALE tours marche sur
-- la colonie du joueur la plus proche d'elle (cible REGION de CA : elle l'attaque) ; une seule fois.
local function finale_en_marche(faction)
	local inv = invasion_manager:get_invasion(PREFIXE .. "finale_" .. faction);
	local f = cm:get_faction(faction);
	if not inv or not f then
		return false;
	end;
	local chef = inv:get_general();
	if chef:is_null_interface() then
		return false;
	end;
	local x, y = chef:logical_position_x(), chef:logical_position_y();
	local regions = f:region_list();
	local cible, meilleure = nil, nil;
	for i = 0, regions:num_items() - 1 do
		local r = regions:item_at(i);
		local s = r:settlement();
		if not s:is_null_interface() then
			local d = (s:logical_position_x() - x) ^ 2 + (s:logical_position_y() - y) ^ 2;
			if not meilleure or d < meilleure then
				cible, meilleure = r:name(), d;
			end;
		end;
	end;
	if not cible then
		return false;
	end;
	inv:set_target("REGION", cible, faction);
	cm:set_saved_value(PREFIXE .. "finale_marche_" .. faction, true);
	cm:show_message_event(faction, "saison_finale_marche_titre", "saison_finale_marche_primaire",
		"saison_finale_marche_secondaire", true, 1803);
	out("La Saison des Revelations : finale de " .. faction .. " en marche sur " .. cible);
	return true;
end;


-- l'adversaire d'une étape « brisez N armées » : posé à son lieu, force selon le tour (plus léger qu'une finale)
local function poser_adversaire(faction, etape)
	local A = etape.adversaire;
	if not A then
		return;
	end;
	local tour = cm:model():turn_number();
	local niveau = A.niveau or math.min(math.max(8, 4 + math.floor(tour / 5)), 30);
	local rang = math.min(math.max(1, math.floor(tour / 25)), 6);
	local ok, pose = pcall(poser_armee, faction, PREFIXE .. "adversaire_" .. etape.cle, A, niveau, rang, function() end);
	if not ok or not pose then
		out("La Saison des Revelations : adversaire de " .. etape.cle .. " non pose");
	end;
end;


-- déclenche l'étape n (ou la première possible à partir de n) ; rend l'indice déclenché, ou nil (chronique finie)
local function declencher(faction, n)
	local chaine = SAISON_CHRONIQUES[faction];
	while chaine[n] do
		local etape = chaine[n];
		local peut = etape.possible;
		if not peut or peut(faction) then
			poser_etat(faction, n);
			if not etape.finale then
				if emettre(faction, n, etape) then
					poser_adversaire(faction, etape);
					return n;
				end;
			elseif lancer_finale(faction, n, etape) then
				out("La Saison des Revelations : chronique " .. faction .. " : finale " .. etape.cle .. " en place");
				return n;
			end;
		end;
		out("La Saison des Revelations : chronique " .. faction .. " : etape " .. n .. " impossible, sautee");
		n = n + 1;
	end;
	poser_etat(faction, n);
	out("La Saison des Revelations : chronique " .. faction .. " : terminee");
	if not cm:get_saved_value(PREFIXE .. "echo_prochain_" .. faction) then
		planifier_echo(faction);
	end;
	return nil;
end;


-- écouteurs des objectifs scriptés (retirés à la fin de chaque étape, remis par l'étape suivante qui en a)
local ECOUTEURS_SCRIPTES = {"pacte_asrai", "pacte_asrai_tour", "fee_quenelles", "fee_ducs", "presence_saison_drycha_addaivoch",
	"soeurs_porte_du_roi",
	"presence_saison_morghur_val_malheur"};

-- à la fin d'une étape (réussie, échouée ou annulée) : la suivante, tout de suite (un appel différé n'est pas
-- sauvegardé : audit du code, G1)
suite = function(faction, reussie)
	local chaine = SAISON_CHRONIQUES[faction];
	local n = etat(faction);
	local etape = chaine[n];
	for i = 1, #ECOUTEURS_SCRIPTES do
		core:remove_listener(PREFIXE .. ECOUTEURS_SCRIPTES[i]);
	end;
	cm:set_saved_value(PREFIXE .. "emise_" .. faction, false);
	cm:set_saved_value(PREFIXE .. "finale_tour_" .. faction, false);
	-- l'adversaire de l'étape close quitte la carte (au début du tour de sa faction)
	if etape then
		retirer_armee(PREFIXE .. "adversaire_" .. etape.cle);
	end;
	if etape and etape.finale then
		local inv = invasion_manager:get_invasion(PREFIXE .. "finale_" .. faction);
		if reussie then
			-- les restes de l'armée vaincue quittent la carte (au début du tour de sa faction)
			retirer_armee(PREFIXE .. "finale_" .. faction);
		else
			-- finale perdue sans bataille (armée disparue) : relancée deux fois au plus (audit du code, G5)
			local essais = cm:get_saved_value(PREFIXE .. "finale_essais_" .. faction) or 0;
			-- revue de la bêta (I2) : jamais détruire une armée encore sur la carte pendant le tour du joueur. Sans
			-- général, kill n'efface que la fiche de l'invasion ; avec un général, l'armée part au début du tour de sa
			-- faction (retirer_armee), et la finale n'est pas relancée sous la même clé.
			local general = inv and inv:get_general();
			local armee_presente = general and not general:is_null_interface();
			if armee_presente then
				retirer_armee(PREFIXE .. "finale_" .. faction);
				essais = 2;
			elseif inv then
				inv:kill(false);
			end;
			if essais < 2 then
				cm:set_saved_value(PREFIXE .. "finale_essais_" .. faction, essais + 1);
				local ok, posee = pcall(lancer_finale, faction, n, etape);
				if ok and posee then
					out("La Saison des Revelations : finale de " .. faction .. " relancee");
					return;
				end;
			end;
		end;
	end;
	if reussie and etape and etape.apres then
		saison_sur("chronique " .. faction .. " : suite de l'etape " .. n, etape.apres, faction);
	end;
	saison_sur("chronique " .. faction, declencher, faction, n + 1);
end;


-- Échos de la Saison d'une faction humaine : une menace à l'échéance quand ouvert() ; l'armée d'un écho échoué est
-- rendue à l'IA.
local function installer_echos(faction, condition)
	local ouvert = condition;
	local echos = SAISON_ECHOS[faction];
	if echos then
		if ouvert() and not cm:get_saved_value(PREFIXE .. "echo_prochain_" .. faction) then
			planifier_echo(faction);
		end;
		saison_ecouteur(
			PREFIXE .. "echo_tour_" .. faction,
			"FactionBeginTurnPhaseNormal",
			function(context)
				if context:faction():name() ~= faction or not ouvert() then
					return false;
				end;
				local en_cours = cm:get_saved_value(PREFIXE .. "echo_en_cours_" .. faction);
				local prochain = cm:get_saved_value(PREFIXE .. "echo_prochain_" .. faction);
				local tour = cm:model():turn_number();
				-- armée jamais parue : on replanifie
				if is_number(en_cours) and tour >= en_cours + 2 then
					planifier_echo(faction);
					return false;
				end;
				return not en_cours and is_number(prochain) and tour >= prochain;
			end,
			function()
				saison_sur("echo de " .. faction, lancer_echo, faction);
			end,
			true
		);
		for _, evenement in ipairs({"MissionSucceeded", "MissionFailed", "MissionCancelled"}) do
			saison_ecouteur(
				PREFIXE .. "echo_" .. evenement .. "_" .. faction,
				evenement,
				function(context)
					return context:faction():name() == faction and context:mission():mission_record_key() == echos.cle;
				end,
				function()
					local k = cm:get_saved_value(PREFIXE .. "echo_nombre_" .. faction) or 0;
					local inv = invasion_manager:get_invasion(PREFIXE .. "echo_" .. faction .. "_" .. k);
					if inv then
						if evenement == "MissionSucceeded" then
							retirer_armee(PREFIXE .. "echo_" .. faction .. "_" .. k);
						else
							-- menace ignorée : l'armée, en guerre avec le seul joueur, part à sa rencontre ; sans
							-- l'entretien gratuit, elle vit et s'use comme une armée ordinaire (audit de gameplay, point 2)
							local ok_liberation, err_liberation = pcall(function()
								local force = inv:get_force();
								if force and not force:is_null_interface() then
									cm:remove_effect_bundle_from_force(ENTRETIEN_GRATUIT, force:command_queue_index());
								end;
								inv:release();
							end);
							if not ok_liberation then
								script_error("La Saison des Revelations : liberation de l'echo " .. k .. " de " .. faction .. " : "
									.. tostring(err_liberation));
							end;
						end;
					end;
					planifier_echo(faction);
				end,
				true
			);
		end;
	end;
end;


-- Pièces du moteur prêtées aux autres chaînes de quêtes (saison_felix.lua)
SAISON_MOTEUR = {
	poser_armee = poser_armee, retirer_armee = retirer_armee, vaincre = vaincre, presence = presence, scripte = scripte, eliminer = eliminer,
	vivant = vivant, argent = argent, unite = unite, objet = objet, preparer_qb = preparer_qb,
	EMETTEUR = EMETTEUR, ENTRETIEN_GRATUIT = ENTRETIEN_GRATUIT, ARMEE_SPECTRES = ARMEE_SPECTRES, KEMMLER = KEMMLER
};


-- Essai des armées (drapeau _G.saison_essai_armees, posé par le pilote d'essai de la construction, option --armees ;
-- inerte sans lui) : les missions n'existent pas pour une IA (mission_manager:new), mais les armées des finales et des
-- Échos se posent. Tous les 2 rounds (WorldStartRound : sous all_players_ai, FactionTurnStart de la faction locale
-- n'arrive pas aux scripts), l'armée précédente est retirée et la suivante posée contre la faction locale, à chaque
-- lieu tour à tour, sous sa faction de bataille ; journal : « ESSAI ARMEE <lieu> <faction> ok|echec|jamais parue ».
local function essai_armees()
	if _G.saison_essai_armees ~= true then
		return;
	end;
	local lieux = {};
	local factions = {};
	for f, _ in pairs(SAISON_CHRONIQUES) do
		table.insert(factions, f);
	end;
	table.sort(factions);
	for _, f in ipairs(factions) do
		for n, etape in ipairs(SAISON_CHRONIQUES[f]) do
			if etape.finale then
				table.insert(lieux, {nom = etape.cle, F = etape.finale});
			end;
		end;
	end;
	local menaces = {};
	for nom, _ in pairs(M) do
		table.insert(menaces, nom);
	end;
	table.sort(menaces);
	for _, nom in ipairs(menaces) do
		table.insert(lieux, {nom = nom, F = M[nom]});
	end;
	table.insert(lieux, {nom = "felix_chapelle", F = {lieu = {85, 298}, factions = {MOUSILLON}, armee = ARMEE_SPECTRES,
		general = "wh_main_vmp_lord"}});
	local CLE = PREFIXE .. "essai_armee";
	core:add_listener(
		CLE,
		"WorldStartRound",
		function()
			return cm:model():turn_number() % 2 == 0;
		end,
		function()
			local locale = cm:get_local_faction_name(true);
			local precedent = cm:get_saved_value(CLE .. "_en_cours");
			if is_string(precedent) then
				out("ESSAI ARMEE " .. precedent .. " jamais parue");
			end;
			local i = (cm:get_saved_value(CLE .. "_indice") or 0) + 1;
			retirer_armee(CLE .. "_" .. (i - 1));
			cm:set_saved_value(CLE .. "_indice", i);
			cm:set_saved_value(CLE .. "_en_cours", false);
			local l = lieux[i];
			if not l then
				if i == #lieux + 1 then
					out("ESSAI ARMEE fin (" .. #lieux .. " lieux)");
				end;
				return;
			end;
			cm:set_saved_value(CLE .. "_en_cours", l.nom);
			local ok, pose = pcall(poser_armee, locale, CLE .. "_" .. i, l.F, 20, 4, function(cqi_force, boss)
				cm:set_saved_value(CLE .. "_en_cours", false);
				out("ESSAI ARMEE " .. l.nom .. " " .. boss .. " ok (force " .. tostring(cqi_force) .. ")");
			end);
			if not ok or not pose then
				cm:set_saved_value(CLE .. "_en_cours", false);
				out("ESSAI ARMEE " .. l.nom .. " echec" .. (ok and "" or (" : " .. tostring(pose))));
			end;
		end,
		true
	);
	out("ESSAI ARMEE : " .. #lieux .. " lieux, un tous les 2 tours de " .. tostring(cm:get_local_faction_name(true)));
end;


-- Essai automatique (saison_en_essai_auto) : état de la harde de Morghur à chacun de ses tours, pour les essais en mode
-- IA de la construction (« ESSAI HARDE ... » : humain ou non, trésor, forces, et pour chaque force son général, sa
-- position logique, ses points d'action, sa posture, son entretien, s'il est caché).
local function essai_harde()
	if not saison_en_essai_auto() then
		return;
	end;
	-- FactionBeginTurnPhaseNormal : sous all_players_ai, FactionTurnStart n'arrive pas aux scripts (essai du 23.09.2026,
	-- 15 h 38 ; les invasions de CA avancent sur cet évènement-ci)
	core:add_listener(
		PREFIXE .. "essai_harde",
		"FactionBeginTurnPhaseNormal",
		function(context)
			return context:faction():name() == HARDE;
		end,
		function(context)
			local f = context:faction();
			local forces = f:military_force_list();
			out("ESSAI HARDE tour " .. cm:model():turn_number() .. " humain=" .. tostring(f:is_human()) .. " tresor="
				.. f:treasury() .. " forces=" .. forces:num_items() .. " elfe_humain=" .. tostring(ORION and cm:get_faction(ORION)
				and cm:get_faction(ORION):is_human()));
			for i = 0, forces:num_items() - 1 do
				local force = forces:item_at(i);
				if force:has_general() then
					local g = force:general_character();
					out("ESSAI HARDE   " .. g:character_subtype_key() .. " (" .. g:logical_position_x() .. ", "
						.. g:logical_position_y() .. ") pa=" .. g:action_points_remaining_percent() .. " posture="
						.. tostring(force:active_stance()) .. " entretien=" .. tostring(force:upkeep()) .. " cache="
						.. tostring(g:is_hidden()) .. " unites=" .. force:unit_list():num_items());
				end;
			end;
		end,
		true
	);
end;


-- À chaque chargement (saison_start.lua, sous saison_sur).
function saison_chroniques_demarrer()
	if cm:is_multiplayer() then
		return;
	end;
	saison_sur("retraits differes", ecouteur_retraits);
	saison_sur("essai des armees", essai_armees);
	saison_sur("essai de la harde", essai_harde);
	for qb, _ in pairs(NOMS_QB) do
		preparer_qb(qb);
	end;
	for faction, chaine in pairs(SAISON_CHRONIQUES) do
		local f = cm:get_faction(faction);
		if f and not f:is_dead() and f:is_human() then
			local n = etat(faction);
			if n == 0 then
				saison_ecouteur(
					PREFIXE .. "debut_" .. faction,
					"FactionBeginTurnPhaseNormal",
					function(context)
						return context:faction():name() == faction and cm:model():turn_number() >= (chaine.tour_debut or 2);
					end,
					function()
						saison_sur("chronique " .. faction, declencher, faction, 1);
					end,
					false
				);
			elseif chaine[n] and chaine[n].ecouteurs then
				-- quête en cours à la reprise d'une sauvegarde : ses écouteurs scriptés
				local ecouter = chaine[n].ecouteurs;
				ecouter(faction, chaine[n].cle);
			end;

			-- Chronique finie (étape au-delà de la dernière) : ni finale ni mission d'étape possibles, ces écouteurs ne
			-- serviraient à rien ; seuls les Échos restent (audit de fluidité du 24.09.2026, T11 / S11)
			local chronique_en_cours = etat(faction) <= #chaine;

			-- une finale dont l'armée n'a jamais paru (aucune case libre) : on passe au-delà deux tours plus tard
			if chronique_en_cours then
				saison_ecouteur(
					PREFIXE .. "finale_garde_" .. faction,
					"FactionBeginTurnPhaseNormal",
					function(context)
						if context:faction():name() ~= faction then
							return false;
						end;
						local attente = cm:get_saved_value(PREFIXE .. "finale_attente_" .. faction);
						return is_number(attente) and cm:model():turn_number() >= attente + 2;
					end,
					function()
						cm:set_saved_value(PREFIXE .. "finale_attente_" .. faction, false);
						script_error("La Saison des Revelations : finale de " .. faction .. " jamais posee : sautee");
						saison_sur("chronique " .. faction, declencher, faction, etat(faction) + 1);
					end,
					true
				);
			end;

			-- Échos de la Saison : la chronique finie
			installer_echos(faction, function() return etat(faction) > #chaine end);

			if chronique_en_cours then
				-- finale qui attend depuis trop longtemps : elle marche sur le joueur
				saison_ecouteur(
					PREFIXE .. "finale_echeance_" .. faction,
					"FactionBeginTurnPhaseNormal",
					function(context)
						if context:faction():name() ~= faction then
							return false;
						end;
						local depuis = cm:get_saved_value(PREFIXE .. "finale_tour_" .. faction);
						local en_cours = chaine[etat(faction)];
						return is_number(depuis) and en_cours and en_cours.finale
							and not cm:get_saved_value(PREFIXE .. "finale_marche_" .. faction)
							and cm:model():turn_number() >= depuis + ECHEANCE_FINALE;
					end,
					function()
						saison_sur("finale en marche", finale_en_marche, faction);
					end,
					true
				);

				-- mission refusée par le moteur (audit du code, B2 ; comme CA, wh_campaign_setup.lua) : étape suivante
				saison_ecouteur(
					PREFIXE .. "echec_generation_" .. faction,
					"MissionGenerationFailed",
					function(context)
						local en_cours = chaine[etat(faction)];
						return en_cours ~= nil and context:mission() == en_cours.cle;
					end,
					function()
						script_error("La Saison des Revelations : generation de " .. chaine[etat(faction)].cle .. " refusee");
						suite(faction, false);
					end,
					true
				);

				-- mission d'étape disparue sans évènement (émise un tour précédent, plus active) : étape suivante
				saison_ecouteur(
					PREFIXE .. "mission_disparue_" .. faction,
					"FactionBeginTurnPhaseNormal",
					function(context)
						-- le nom de faction d'abord (audit de fluidité du 25.09.2026, R8)
						if context:faction():name() ~= faction then
							return false;
						end;
						local emise = cm:get_saved_value(PREFIXE .. "emise_" .. faction);
						local en_cours = chaine[etat(faction)];
						if not is_number(emise) or not en_cours or cm:model():turn_number() <= emise then
							return false;
						end;
						local ok, active = pcall(function() return cm:mission_is_active_for_faction(context:faction(), en_cours.cle) end);
						-- échec de l'appel : écrit une fois par partie (sinon la détection serait coupée en silence ; T15 / S10)
						if not ok and not cm:get_saved_value(PREFIXE .. "mission_active_erreur") then
							cm:set_saved_value(PREFIXE .. "mission_active_erreur", true);
							script_error("La Saison des Revelations : mission_is_active_for_faction : " .. tostring(active));
						end;
						return ok and active == false;
					end,
					function()
						script_error("La Saison des Revelations : mission " .. chaine[etat(faction)].cle .. " disparue : etape suivante");
						suite(faction, false);
					end,
					true
				);

				for _, evenement in ipairs({"MissionSucceeded", "MissionFailed", "MissionCancelled"}) do
					saison_ecouteur(
						PREFIXE .. evenement .. "_" .. faction,
						evenement,
						function(context)
							local en_cours = chaine[etat(faction)];
							return context:faction():name() == faction and en_cours ~= nil
								and context:mission():mission_record_key() == en_cours.cle;
						end,
						function()
							suite(faction, evenement == "MissionSucceeded");
						end,
						true
					);
				end;
			end;
			out("La Saison des Revelations : chroniques de " .. faction .. " en place (etape " .. etat(faction) .. ")");
		end;
	end;

	-- échos sans chronique (Orion, Durthu) : ouverts par la réussite de leur mission d'ouverture
	for faction, echos in pairs(SAISON_ECHOS) do
		local f = cm:get_faction(faction);
		if not SAISON_CHRONIQUES[faction] and echos.ouverture and f and not f:is_dead() and f:is_human() then
			local cle_ouvert = PREFIXE .. "echo_ouvert_" .. faction;
			if not cm:get_saved_value(cle_ouvert) then
				saison_ecouteur(
					PREFIXE .. "echo_ouverture_" .. faction,
					"MissionSucceeded",
					function(context)
						return context:faction():name() == faction and context:mission():mission_record_key() == echos.ouverture;
					end,
					function()
						cm:set_saved_value(cle_ouvert, true);
						planifier_echo(faction);
					end,
					false
				);
				-- ouverts aussi dès la chute de Morghur (étape 3 de l'histoire de WH1, saison_histoire.lua) : ses hardes
				-- ne disparaissent pas avec lui (bêta, 25.09.2026 : creux des tours 35 à 50, étude du rythme)
				saison_ecouteur(
					PREFIXE .. "echo_chute_morghur_" .. faction,
					"ScriptEventSaisonMorghurTombe",
					true,
					function()
						if not cm:get_saved_value(cle_ouvert) then
							cm:set_saved_value(cle_ouvert, true);
							planifier_echo(faction);
							out("La Saison des Revelations : echos de " .. faction .. " ouverts a la chute de Morghur");
						end;
					end,
					false
				);
			end;
			installer_echos(faction, function() return cm:get_saved_value(cle_ouvert) == true end);
			out("La Saison des Revelations : echos de " .. faction .. " en place");
		end;
	end;
end;
