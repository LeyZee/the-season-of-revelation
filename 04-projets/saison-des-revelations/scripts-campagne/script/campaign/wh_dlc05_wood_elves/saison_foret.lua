-----------------------------------------------------------------------------------
--	Athel Loren dans les mécaniques de WH3 : Chemins-racines (santé de la forêt, rituel de Renaissance, ambre) et
--	missions de confédération des clairières. Pas de téléportation par les Racines profondes : ses rituels ne partent que
--	de forêts des Empires et visent leur Chêne (audit des scripts de CA, H1) ; elle n'est plus annoncée au tour 10.
--
--	Décisions de Charles (23.09.2026) : l'ambre vient des Chemins-racines de WH3 ; le Chêne des Âges suit la chaîne de
--	WH3 et son niveau 5 (la victoire) passe par le rituel de Renaissance ; une seule bataille finale, le Pic d'Argent de
--	WH1 (la « grande défense du Chêne » que le rituel déclenche aux Empires est retirée).
--
--	Les scripts de CA (wh2_dlc16_wef_worldroots.lua, wh2_campaign_confederation_missions.lua) sont chargés tels quels ;
--	on remplace leurs données (dix forêts et rencontres des Empires) par les nôtres avant leur démarrage, et on
--	neutralise trois références à des factions absentes de notre carte (relevé du 23.09.2026) :
--	  - au démarrage : Drycha (diplomatie, ambre de départ) et les Archers d'Oreon (cm:get_faction(...):is_dead() sans
--	    garde, qui arrêterait la pose des écouteurs d'interface et de téléportation) ;
--	  - à chaque tour : le même test des Archers d'Oreon, placé AVANT la mise à jour de la santé de la forêt (sans
--	    correction : jamais de rituel, donc jamais d'ambre) ; et l'invasion d'Avelorn du tour 45.
-----------------------------------------------------------------------------------

local CHENE = "wh_dlc05_oak_of_ages";
local ORION = "wh_dlc05_wef_wood_elves";
local DURTHU = "wh_dlc05_wef_argwylon";
local DRYCHA = "wh2_dlc16_wef_drycha";

-- Les clés de Racines du monde de NOTRE Athel Loren (23.09.2026, lot 7 de donnees_campagne.py) : avec celles de CA,
-- l'infobulle du bosquet prenait le Chêne des Empires, absent de notre carte (plantage de 02 h 53). Les nôtres ne sont
-- données qu'aux Elfes sylvains de cette campagne ; les Empires gardent les leurs.
SAISON_RESSOURCE_FORET = "wef_worldroots_saison_athel_loren";
SAISON_RITUEL_RENAISSANCE = "wh2_dlc16_ritual_rebirth_saison_athel_loren";


-- Chemins-racines : une seule forêt, Athel Loren, sur nos régions.
if Worldroots then
	Worldroots.forests = {
		athel_loren = {
			key = "athel_loren",
			pooled_resource = SAISON_RESSOURCE_FORET,
			glade_region_key = CHENE,
			-- les régions d'Athel Loren dont les bâtiments comptent pour la santé de la forêt (les mêmes lieux qu'aux
			-- Empires : Crag Halls of Findol, King's Glade = Yn Ecryl Koiran, Vaul's Anvil, Waterfall Palace)
			additional_regions = {
				"wh_dlc05_wydrioth_crag_halls",
				"wh_dlc05_talsyn_yn_ecryl_koiran",
				"wh_dlc05_torgovann_vauls_anvil",
				"wh_dlc05_argwylon_waterfall_palace"
			},
			rite_key = SAISON_RITUEL_RENAISSANCE,
			-- faction d'invasion présente dans notre startpos (celle des Empires, wh2_dlc13_bst_beastmen_invasion, n'y est pas)
			invasion_faction = "wh_dlc03_bst_beastmen_brayherd",
			invasion_force_key = "athel_loren_beastmen_invasion",
			-- points d'apparition des hardes de la mini-campagne de WH1 (coordonnées logiques, valables chez nous) :
			-- lisière de Summersfall Fort, de Quenelles, et les ruines de l'Enclume de Vaul
			invasion_spawn_coords = {{162, 106}, {160, 85}, {176, 130}, {226, 148}},
			rite_completed = false,
			rite_active = false,
			locked_building = "wh_dlc05_wef_oak_of_ages_5",
			-- groupe de forêt À NOUS (lot 23, 23.09.2026, 20 h) : le Chêne et ses 4 régions de lisière. Celui de CA
			-- (wh2_dlc16_forest_region_group_main_1) garde les régions des Empires : l'infobulle des clairières y
			-- résolvait leur Chêne des Âges en objet nul (plantage de Durthu au tour 6, erreur 110)
			region_group = "wh_dlc05_saison_forest_region_group_athel_loren",
			-- CA : 500 avec ses rencontres de forêt ; les nôtres sont vidées (5 à 11 points par tour : 50 à 100 tours).
			-- 200 (audit des factions, point 4)
			ritual_resource_required_override = 200
		}
	};
	-- Rencontres de la forêt (bilan du 25.09.2026 : sans elles, les Elfes sylvains joués n'avaient aucun dilemme en 30
	-- tours, contre environ 5 aux Empires). Les quatre rencontres d'Athel Loren de CA (wh2_dlc16_wef_worldroots.lua,
	-- l. 405-457), leurs dilemmes et leurs textes, sur NOS régions ; marqueurs sur des cases franchissables à 4 à 7 cases
	-- de la colonie (scratchpad bilan-campagne\cases_rencontres.py). Les Peaux-Vertes d'invasion de CA
	-- (wh2_dlc13_grn_greenskins_invasion) ne sont pas dans notre startpos : wh_main_grn_greenskins_qb1 à la place. Les
	-- deux rencontres d'ouverture de CA (hardes à la Clairière Royale, Nains au Palais des Chutes) ne sont pas reprises :
	-- l'histoire de WH1 tient déjà ce rôle. Mêmes règles que CA : le joueur elfe qui tient le Chêne, un marqueur à la
	-- fois (délai de CA), chaque rencontre une seule fois.
	local function rencontre(cle, tour, region, dilemme, x, y, faction, gabarit, embuscade, general)
		Worldroots.encounters[cle] = {
			spawn_turn = tour,
			forest = "athel_loren",
			spawn_incident = "wh2_dlc16_incident_wef_new_encounter_available",
			region = region,
			setup = function()
				Worldroots:set_up_generic_encounter_marker(cle, dilemme, x, y, "athel_loren");
				out("La Saison des Revelations : rencontre de la foret " .. cle);
			end,
			on_battle_trigger_callback = function(self, character, marker_info)
				Worldroots:set_up_generic_encounter_forced_battle(character, faction, gabarit, embuscade, nil, general);
			end
		};
	end;
	Worldroots.encounters = {};
	rencontre("saison_wydrioth_peaux_vertes", 8, "wh_dlc05_wydrioth_crag_halls",
		"wh2_dlc16_dilemma_wef_encounter_athel_loren_greenskins", 307, 157, "wh_main_grn_greenskins_qb1",
		"wh_main_sc_grn_greenskins", true);
	rencontre("saison_torgovann_bretonniens", 8, "wh_dlc05_torgovann_vauls_anvil",
		"wh2_dlc16_dilemma_wef_encounter_athel_loren_bretonnians", 224, 146, "wh_main_brt_bretonnia_qb1",
		"wh_main_sc_brt_bretonnia", true);
	rencontre("saison_argwylon_nains", 12, "wh_dlc05_argwylon_waterfall_palace",
		"wh2_dlc16_dilemma_wef_encounter_athel_loren_dwarfs", 272, 209, "wh_main_dwf_dwarfs_qb1",
		"wh_main_sc_dwf_dwarfs", false);
	rencontre("saison_talsyn_esprits", 12, "wh_dlc05_talsyn_yn_ecryl_koiran",
		"wh2_dlc16_dilemma_wef_encounter_athel_loren_tree_spirits", 283, 83, "wh_dlc05_wef_wood_elves_qb2",
		"wef_forest_spirits", false, "wh_dlc05_wef_ancient_treeman");
	Worldroots.teleport_rituals_to_regions = {
		["wh2_dlc16_worldroots_teleport_athel_loren"] = CHENE,
		["saison_racines_chene"] = "wh_dlc05_oak_of_ages",
		["saison_racines_clairiere_royale"] = "wh_dlc05_talsyn_yn_ecryl_koiran",
		["saison_racines_palais_des_chutes"] = "wh_dlc05_argwylon_waterfall_palace",
		["saison_racines_pics_de_findol"] = "wh_dlc05_wydrioth_crag_halls",
		["saison_racines_bois_sauvage"] = "wh_dlc05_cythral_tyr_vanna"
	};
	Worldroots.avelorn_invasion_turn = 1000000;
end;


-- Ariel (héroïne légendaire, wh3_main_legendary_characters.lua) vient à Orion ou Durthu au premier rituel de
-- Renaissance accompli ; CA ne liste que ses propres rituels : on y ajoute le nôtre.
if character_unlocking and is_table(character_unlocking.character_data) then
	local ariel = character_unlocking.character_data.ariel;
	if is_table(ariel) and is_table(ariel.ritual_keys) then
		table.insert(ariel.ritual_keys, SAISON_RITUEL_RENAISSANCE);
	end;
	-- « La Reine apparaît » à notre clé (lot 39 ; audit de cohérence du 25.09.2026, point 11) : celui de CA parle des
	-- soins aux clairières du monde ; chez nous elle s'éveille avec le Chêne « Bourgeonnant » (ou au tour 25)
	if is_table(ariel) and is_table(ariel.mission_incidents) then
		for faction in pairs(ariel.mission_incidents) do
			ariel.mission_incidents[faction] = "saison_ariel_arrive";
		end;
	end;
	-- Coeddil vient à Drycha jouée quand elle réussit « Coeddil déchaîné » : CA le fait sur la clé des Empires
	-- (wh2_dlc16_wef_worldroots.lua, préfixe wh3_main_ie_qb_) ; notre clé (lot 10) passe par l'écouteur générique
	-- (add_quest_mission_listener). Drycha en IA : au tour 20, comme chez CA.
	local coeddil = character_unlocking.character_data.coeddil;
	if is_table(coeddil) and is_table(coeddil.starting_mission_keys) then
		table.insert(coeddil.starting_mission_keys, "saison_qb_wef_drycha_coeddil_unchained");
	end;
end;


-- Ariel plus tôt (décision de Charles, 24.09.2026, 20 h 40 ; rapport 05-journal\2026-09-24-vampires-9.0\ariel-lore-
-- declencheur.md) : elle s'éveille quand le Chêne des Âges atteint le niveau 3. Texte du Chêne (le même dans WH1 et WH3) :
-- niveau 1 « Endormi », l'hiver, Ariel dort dans le Chêne ; niveau 3 « Bourgeonnant », le printemps. Et elle sort du
-- Chêne quand elle apprend le retour de Morghur (livre d'armée Elfes sylvains 8e, « Ariel Returns »), ce qui tombe au même
-- moment dans notre histoire (étape 2). Filet : tour ARIEL_TOUR_FILET si le Chêne traîne. Le joueur d'abord (Orion,
-- Durthu ou les Sœurs, ses hérautes, qui parlent avec sa voix) ; sinon Orion ou Durthu de l'IA. Jamais Drycha, héraut de
-- Coeddil qu'Ariel a enfermé (CA : Ariel est « recrutable par tous les seigneurs elfes sauf Drycha »). La garde de CA
-- (character_data.ariel.has_spawned, sauvegardée) empêche toujours une seconde Ariel ; le rituel de Renaissance et le
-- don de CA à l'IA au tour 20 restent des voies de secours, sans double don.
local SOEURS = "wh2_dlc16_wef_sisters_of_twilight";
local ARIEL_NIVEAU = 3;
local ARIEL_TOUR_FILET = 25;

local function niveau_du_chene()
	local r = cm:get_region(CHENE);
	if not r or r:is_null_interface() or r:is_abandoned() then
		return 0;
	end;
	local slot = r:settlement():primary_slot();
	if slot:is_null_interface() or not slot:has_building() then
		return 0;
	end;
	return tonumber(string.match(slot:building():name(), "wh_dlc05_wef_oak_of_ages_(%d)$")) or 0;
end;

local function destinataire_d_ariel()
	local proprietaire = nil;
	local r = cm:get_region(CHENE);
	if r and not r:is_null_interface() and not r:is_abandoned() then
		proprietaire = r:owning_faction():name();
	end;
	local humains, ia = {}, {};
	for _, cle in ipairs({ORION, DURTHU, SOEURS}) do
		local f = cm:get_faction(cle);
		if f and not f:is_null_interface() and not f:is_dead() then
			-- Ariel appartient au DLC « The Twisted & The Twilight » : CA ne la donne qu'aux joueurs qui l'ont
			-- (wh3_main_legendary_characters.lua, require_dlc ; revue de la bêta, 25.09.2026)
			if f:is_human() then
				if cm:faction_has_dlc_or_is_ai("TW_WH2_DLC16_TWILIGHT", cle) then
					table.insert(humains, cle);
				end;
			elseif cle ~= SOEURS then
				table.insert(ia, cle);
			end;
		end;
	end;
	for _, liste in ipairs({humains, ia}) do
		for _, cle in ipairs(liste) do
			if cle == proprietaire then
				return cle;
			end;
		end;
		if liste[1] then
			return liste[1];
		end;
	end;
	return nil;
end;

function saison_ariel_ecouteur()
	local ariel = character_unlocking and character_unlocking.character_data and character_unlocking.character_data.ariel;
	if not is_table(ariel) or ariel.has_spawned then
		return;
	end;
	saison_ecouteur(
		"saison_ariel_eveil",
		"WorldStartRound",
		function()
			return not ariel.has_spawned
				and (niveau_du_chene() >= ARIEL_NIVEAU or cm:model():turn_number() >= ARIEL_TOUR_FILET);
		end,
		function()
			local cle = destinataire_d_ariel();
			if cle then
				character_unlocking:spawn_hero(cle, "ariel");
				out("La Saison des Revelations : Ariel s'eveille (Chene niveau " .. niveau_du_chene() .. ", tour "
					.. cm:model():turn_number() .. ") pour " .. cle);
			end;
			if ariel.has_spawned then
				core:remove_listener("saison_ariel_eveil");
			end;
		end,
		true
	);
end;


-- Missions de confédération des clairières : les quatre de CA qui visent des factions de notre carte, déclenchées par
-- le niveau de NOTRE Chêne (aux Empires : wh3_main_combi_region_the_oak_of_ages). Leurs objectifs ne dépendent pas de
-- la carte (vaincre 3 armées bretonnes, peaux-vertes ou naines ; raser ou piller 10 colonies).
if confed_missions_data and confed_missions then
	local GARDER = {
		wood_elves_talsyn = 3,			-- Durthu confédère Orion
		wood_elves_torgovann = 2,		-- Orion ou Durthu confédère Torgovann
		wood_elves_wydrioth = 2,		-- Orion ou Durthu confédère Wydrioth
		wood_elves_durthu = 3,			-- Orion ou Drycha confédère Durthu
		durthu_drycha = false			-- Durthu confédère Drycha : condition de CA gardée (tour 2, faction connue)
	};
	local nouvelles = {};
	for cle, niveau in pairs(GARDER) do
		local d = confed_missions_data[cle];
		if is_table(d) then
			local factions = is_table(d.factions) and d.factions or {d.factions};
			local presentes = {};
			for i = 1, #factions do
				-- les Sœurs du Crépuscule (24.09.2026) : CA les compte parmi les factions qui confèdèrent Talsyn,
				-- Torgovann et Wydrioth
				if factions[i] == ORION or factions[i] == DURTHU or factions[i] == DRYCHA
					or factions[i] == "wh2_dlc16_wef_sisters_of_twilight" then
					table.insert(presentes, factions[i]);
				end;
			end;
			d.factions = presentes;
			if niveau then
				d.custom_callback = function()
					return confed_missions:is_settlement_primary_building_at_level(CHENE, niveau);
				end;
			end;
			nouvelles[cle] = d;
		end;
	end;
	confed_missions_data = nouvelles;
end;


-- Démarrage des Chemins-racines (appelé par saison_start.lua, sous saison_sur).
-- Ambre (audit des factions, point 5) : CA la donne quand une forêt est guérie, par ses rencontres de forêt, vidées
-- chez nous ; 10 des 35 technologies elfes coûtent 1 ambre. Ici : 1 ambre à chaque niveau du Chêne des Âges achevé
-- (2 à 5), et 1 tous les 10 tours à chaque seigneur elfe jouable encore en vie (Racines du monde qui se referment).
local AMBRE, FACTEUR_AMBRE = "wef_amber", "wh2_dlc16_resource_factor_worldroots_healed";
local ELFES_AMBRE = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_argwylon", "wh2_dlc16_wef_drycha"};

-- Conseil des invasions du rituel de Renaissance (audit des scripts de CA, C1) : CA centre la caméra sur
-- wh3_main_combi_region_the_oak_of_ages, absent de notre carte ; l'intervention sort en erreur sans se terminer et fige le
-- conseiller jusqu'au rechargement. Redéfinie avec notre Chêne (wh_campaign_interventions.lua l. 18152-18163).
if in_worldroots_invasions then
	function trigger_in_worldroots_invasions()
		local x, y = cm:log_to_dis(in_worldroots_invasions.x, in_worldroots_invasions.y);
		in_worldroots_invasions:scroll_camera_for_intervention(CHENE, x, y, "wh2_dlc16.camp.advice.wef.worldroots.008.ritual_begun");
	end;
end;


-- Racines du monde (lot 19, donnees_campagne.RACINES_DU_MONDE)
SAISON_RACINES_DU_MONDE = {"saison_racines_chene", "saison_racines_clairiere_royale", "saison_racines_palais_des_chutes", "saison_racines_pics_de_findol", "saison_racines_bois_sauvage"};


function saison_ambre_ecouteurs()
	core:add_listener(
		"saison_ambre_chene",
		"BuildingCompleted",
		function(context)
			local b = context:building();
			return b:name():find("^wh_dlc05_wef_oak_of_ages_[2-5]$") ~= nil and not b:faction():is_null_interface()
				and b:faction():culture() == "wh_dlc05_wef_wood_elves";
		end,
		function(context)
			cm:faction_add_pooled_resource(context:building():faction():name(), AMBRE, FACTEUR_AMBRE, 1);
		end,
		true
	);
	core:add_listener(
		"saison_ambre_tours",
		"WorldStartRound",
		function()
			return cm:model():turn_number() % 10 == 0;
		end,
		function()
			for i = 1, #ELFES_AMBRE do
				local f = cm:get_faction(ELFES_AMBRE[i]);
				if f and not f:is_dead() then
					cm:faction_add_pooled_resource(ELFES_AMBRE[i], AMBRE, FACTEUR_AMBRE, 1);
				end;
			end;
		end,
		true
	);
end;


function saison_demarrer_foret()
	-- Drycha est sur la carte depuis le 23.09.2026 (spécification Drycha / Kemmler / Grom) : seuls les Archers d'Oreon
	-- restent absents (audit des mécaniques de la construction, 23.09.2026, 13 h 50)
	local absentes = {
		wh2_main_wef_bowmen_of_oreon = true
	};
	-- faction absente vue comme morte : le seul usage au démarrage est « if not ...:is_dead() then »
	local absente = {
		is_dead = function() return true end,
		is_human = function() return false end,
		is_null_interface = function() return true end
	};
	local ajouter_ressource = cm.faction_add_pooled_resource;

	cm.get_faction = function(self, faction, erreur)
		if absentes[faction] then
			return absente;
		end;
		return campaign_manager.get_faction(self, faction, erreur);
	end;
	cm.force_diplomacy = function(self, source, cible, ...)
		for _, s in ipairs({source, cible}) do
			local cle = is_string(s) and string.match(s, "^faction:(.+)$");
			if cle and absentes[cle] then
				return;
			end;
		end;
		return campaign_manager.force_diplomacy(self, source, cible, ...);
	end;
	cm.faction_add_pooled_resource = function(self, faction, ...)
		if absentes[faction] then
			return;
		end;
		return ajouter_ressource(self, faction, ...);
	end;

	local ok, err = pcall(function() Worldroots:add_worldroots_listeners() end);

	-- retour aux fonctions de la bibliothèque, quoi qu'il arrive
	cm.get_faction = nil;
	cm.force_diplomacy = nil;
	cm.faction_add_pooled_resource = nil;

	if not ok then
		error(err);
	end;

	-- L'écouteur de début de tour de CA, sans les Archers d'Oreon ni l'invasion d'Avelorn (même logique sinon :
	-- wh2_dlc16_wef_worldroots.lua, « WorldrootsUpdateFactionTurnStart »).
	-- Écouteur protégé (saison_ecouteur, saison_start.lua ; audit de fluidité du 24.09.2026, T2 / S4) :
	-- update_worldroots_health de CA lit le bâtiment principal du Chêne sans le tester ; Chêne rasé, l'erreur reviendrait à
	-- chaque tour du joueur et couperait tous les écouteurs FactionTurnStart de ce tour.
	-- 24.09.2026, 23 h 20 : sur FactionBeginTurnPhaseNormal, comme l'histoire et les chroniques. Les essais de 30 tours
	-- n'ont vu arriver AUCUN FactionTurnStart aux scripts de mod (sonde de la construction ; cause à trancher : mode
	-- all_players_ai, ou un écouteur de CA qui plante avant les nôtres, erreur 213) ; celui-ci arrive dans tous les cas.
	core:remove_listener("WorldrootsUpdateFactionTurnStart");
	saison_ecouteur(
		"WorldrootsUpdateFactionTurnStart",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local faction = context:faction();
			return faction:is_human() and faction:culture() == "wh_dlc05_wef_wood_elves";
		end,
		function(context)
			local faction = context:faction();
			local faction_name = faction:name();

			if cm:get_factions_bonus_value(faction, "provides_vision_on_all_glade_regions") > 0 then
				for _, forest in pairs(Worldroots.forests) do
					cm:make_region_visible_in_shroud(faction_name, forest.glade_region_key);
				end;
			end;

			Worldroots:generate_encounter(faction);

			if faction_name == Worldroots.primary_player_key then
				-- chacun sous protection (revue de la bêta, M1) : ces fonctions de CA lisent le Chêne sans garde ; s'il est
				-- rasé ou abandonné, leur erreur ne doit plus empêcher l'ouverture des Racines du monde au tour 10
				saison_sur("sante des Chemins-racines", function() Worldroots:update_worldroots_health() end);
				saison_sur("puissance des invasions de la foret", function() Worldroots:calculate_invasion_power() end);

				-- Racines du monde (lot 19) : nos cinq rituels de téléportation entre les clairières, au tour 10, un par
				-- un (ceux de CA, qui partent de forêts des Empires, restent fermés)
				if cm:turn_number() == 10 then
					local human_factions = cm:get_human_factions();
					for i = 1, #human_factions do
						local elfe = cm:get_faction(human_factions[i]);
						if elfe:culture() == "wh_dlc05_wef_wood_elves" then
							for _, rituel in ipairs(SAISON_RACINES_DU_MONDE) do
								cm:unlock_ritual(elfe, rituel, -1);
							end;
							-- notre annonce (lot 39 ; audit de cohérence du 25.09.2026, point 10) : celle de CA parle
							-- des Racines profondes entre les Forêts magiques du monde
							cm:trigger_incident(human_factions[i], "saison_racines_du_monde_ouvertes", true);
							out("La Saison des Revelations : Racines du monde ouvertes pour " .. human_factions[i]
								.. " (" .. #SAISON_RACINES_DU_MONDE .. " rituels)");
						end;
					end;
					core:trigger_event("ScriptEventDeeprootsUnlocked");
				end;

			end;
		end,
		true
	);
end;
