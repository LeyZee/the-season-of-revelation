-----------------------------------------------------------------------------------
--	ESSAIS À DRAPEAU du plantage du tour 11 (Warhammer3.exe+0x2532B26, fil principal, pendant le tour d'IA de Drycha,
--	juste après son début de tour ; 4 fois sur 4 avec les armées de la harde, 0 sans elles ; la guerre Drycha / harde
--	est écartée par l'essai « hors harde » de 21 h 26). 23.09.2026, 21 h 40.
--
--	Drapeaux (fichiers NON VIDES dans <jeu>\data\script\campaign\wh_dlc05_wood_elves\), un essai à la fois :
--	- saison_essai_c1_sans_liberation.txt : l'histoire ne libère PAS invasion_beastmen_first_invasion_2 au tour 10
--	  (should_stop_at_end(false) et remove_target sont ignorés pour elle) : elle reste une invasion menée par le script.
--	  Si le tour 11 passe : l'armée libérée (fin d'invasion, « releasing force ») est en cause.
--	- saison_essai_c2_drycha_sans_armee.txt : à chaque début de tour de Drycha à partir du tour 9, toutes ses armées sont
--	  détruites (kill_all_armies_for_faction ; Drycha, immortelle, n'est que blessée). Si le tour 11 passe : c'est le
--	  tour d'IA de ses armées.
--	- saison_essai_journal_tour11.txt : le journal seul (il est aussi actif avec C1 ou C2).
--	Journal (lignes « [T11] ») à partir du tour 8 : au début du tour de Drycha et de la harde, et à la fin du tour de la
--	harde : chaque général de TOUTES les factions (cqi, faction, sous-type, position, région, posture, unités, points
--	d'action, siège, blessé), puis les colonies assiégées. Les cqi cités par les derniers traits avant le plantage s'y
--	retrouvent.
--
--	Fichier chargé par AUCUN required.lua : la construction le copie dans script\campaign\mod\ du pack d'essai (le
--	chargeur de CA saute un fichier dont le nom est déjà dans package.loaded). Sans drapeau, il ne fait rien. Aucune
--	fonction globale.
-----------------------------------------------------------------------------------

local DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local HARDE = "wh_dlc05_bst_morghur_herd";
local DRYCHA = "wh2_dlc16_wef_drycha";
local INVASION_LIBEREE = "invasion_beastmen_first_invasion_2";
local TOUR_JOURNAL = 8;
local TOUR_C2 = 9;


local function drapeau(nom)
	local liste = common.filesystem_lookup(DOSSIER, nom);
	return is_string(liste) and liste ~= "";
end;

local C1 = drapeau("saison_essai_c1_sans_liberation.txt");
local C2 = drapeau("saison_essai_c2_drycha_sans_armee.txt");
-- E (21 h 55) : dans les 5 plantages, Arlas (chef de Modryn, cqi 14, glade_lord_fem immortel, override_general_unit
-- de WH1) perd contre la harde au tour 7, disparaît, et le jeu plante au DÉBUT DU TOUR DE MODRYN au tour 11 (traits
-- corrupted_chaos sur 134 = sa tisseuse de sorts, juste avant ; « wh_dlc05_wef_modryn » dans le tas près de l'objet
-- fautif). E : tout personnage blessé de Modryn perd son immortalité et meurt, pour qu'il ne revienne jamais.
local E = drapeau("saison_essai_e_sans_retour_arlas.txt");
-- F (24.09.2026, 00 h 30) : preuve du lot 26 (poste de chef des factions elfes de WH1). Au début du tour 5 de Modryn,
-- son chef perd son armée (cm:kill_character, armée détruite : un immortel n'est que blessé). Attendu avec le lot 26 :
-- « CHEF DE MODRYN : cqi 14 ... blesse=true » puis son retour, Modryn jamais sans chef, aucune ligne du filet.
local F = drapeau("saison_essai_f_chef_battu.txt");
local TOUR_F = 5;
local MODRYN = "wh_dlc05_wef_modryn";
local JOURNAL = C1 or C2 or E or F or drapeau("saison_essai_journal_tour11.txt");


local function sans_risque(nom, f, ...)
	local ok, err = pcall(f, ...);
	if not ok then
		out("[T11] ERREUR " .. nom .. " : " .. tostring(err));
	end;
end;


-----------------------------------------------------------------------------------
--	Journal
-----------------------------------------------------------------------------------

local function ligne_general(c)
	local mf = c:military_force();
	local region = c:has_region() and c:region():name() or "-";
	return string.format("[T11]   cqi %d %s %s (%d, %d) %s posture=%s unites=%d pa=%d siege=%s colonie=%s blesse=%s",
		c:command_queue_index(), c:faction():name(), c:character_subtype_key(), c:logical_position_x(), c:logical_position_y(),
		region, tostring(mf:active_stance()), mf:unit_list():num_items(), c:action_points_remaining_percent(),
		tostring(c:is_besieging()), tostring(c:in_settlement()), tostring(c:is_wounded()));
end;


local function photographier(moment)
	out("[T11] ==== " .. moment);
	local factions = cm:model():world():faction_list();
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		if not f:is_dead() then
			local forces = f:military_force_list();
			for j = 0, forces:num_items() - 1 do
				local mf = forces:item_at(j);
				if mf:has_general() and not mf:is_armed_citizenry() then
					sans_risque("general", function() out(ligne_general(mf:general_character())) end);
				end;
			end;
		end;
	end;
	-- chef de Modryn (Arlas au départ, cqi 14 dans tous les essais) : existe-t-il, où, dans quel état
	local modryn = cm:get_faction(MODRYN);
	if modryn and not modryn:is_dead() then
		local chef = modryn:has_faction_leader() and modryn:faction_leader() or nil;
		out("[T11]   CHEF DE MODRYN : " .. (chef and string.format("cqi %d %s blesse=%s armee=%s", chef:command_queue_index(),
			chef:character_subtype_key(), tostring(chef:is_wounded()), tostring(chef:has_military_force())) or "aucun"));
		local arlas = cm:get_character_by_cqi(14);
		out("[T11]   CQI 14 : " .. (arlas and string.format("%s %s blesse=%s armee=%s chef=%s", arlas:faction():name(),
			arlas:character_subtype_key(), tostring(arlas:is_wounded()), tostring(arlas:has_military_force()),
			tostring(arlas:is_faction_leader())) or "introuvable"));
	end;
	-- personnages blessés (sans armée, absents de la liste ci-dessus) des elfes et de la harde
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		if not f:is_dead() and (f:culture() == "wh_dlc05_wef_wood_elves" or f:name() == HARDE) then
			local persos = f:character_list();
			for j = 0, persos:num_items() - 1 do
				local c = persos:item_at(j);
				if c:is_wounded() then
					out(string.format("[T11]   BLESSE cqi %d %s %s chef=%s", c:command_queue_index(), f:name(),
						c:character_subtype_key(), tostring(c:is_faction_leader())));
				end;
			end;
		end;
	end;
	local regions = cm:model():world():region_manager():region_list();
	for i = 0, regions:num_items() - 1 do
		local r = regions:item_at(i);
		if not r:is_abandoned() and r:garrison_residence():is_under_siege() then
			out("[T11]   ASSIEGEE " .. r:name() .. " (" .. r:owning_faction():name() .. ")");
		end;
	end;
end;


local function journal_voulu(faction_name)
	return JOURNAL and cm:model():turn_number() >= (F and TOUR_F or TOUR_JOURNAL)
		and (faction_name == DRYCHA or faction_name == HARDE or faction_name == MODRYN);
end;


local function sans_retour_modryn()
	local f = cm:get_faction(MODRYN);
	if not f or f:is_dead() then
		return;
	end;
	local persos = f:character_list();
	local blesses = {};
	for j = 0, persos:num_items() - 1 do
		local c = persos:item_at(j);
		if c:is_wounded() then
			table.insert(blesses, {c:command_queue_index(), c:character_subtype_key(), tostring(c:is_faction_leader())});
		end;
	end;
	for _, b in ipairs(blesses) do
		cm:set_character_immortality("character_cqi:" .. b[1], false);
		cm:kill_character(b[1], true);
		out("[T11] ESSAI E : blesse de Modryn cqi " .. b[1] .. " (" .. b[2] .. ", chef=" .. b[3] .. ") mis a mort (ne reviendra pas)");
	end;
end;


-----------------------------------------------------------------------------------
--	Armement
-----------------------------------------------------------------------------------

local function armer()
	if C1 and is_table(invasion) then
		local ca_stop = invasion.should_stop_at_end;
		invasion.should_stop_at_end = function(self, stop, ...)
			if self.key == INVASION_LIBEREE and stop == false then
				out("[T11] ESSAI C1 : liberation de " .. INVASION_LIBEREE .. " ignoree (should_stop_at_end)");
				return;
			end;
			return ca_stop(self, stop, ...);
		end;
		local ca_remove_target = invasion.remove_target;
		invasion.remove_target = function(self, ...)
			if self.key == INVASION_LIBEREE and self.stop_at_end ~= false then
				out("[T11] ESSAI C1 : liberation de " .. INVASION_LIBEREE .. " ignoree (remove_target)");
				return;
			end;
			return ca_remove_target(self, ...);
		end;
		out("[T11] ESSAI C1 SANS LIBERATION ACTIF (drapeau saison_essai_c1_sans_liberation.txt)");
	end;

	if C2 then
		out("[T11] ESSAI C2 DRYCHA SANS ARMEE ACTIF (drapeau saison_essai_c2_drycha_sans_armee.txt)");
	end;

	if E then
		-- à la fin de CHAQUE tour de faction : le blessé meurt avant tout début de tour de Modryn
		core:add_listener(
			"saison_essai_tour11_e",
			"FactionTurnEnd",
			true,
			function() sans_risque("essai E", sans_retour_modryn) end,
			true
		);
		out("[T11] ESSAI E SANS RETOUR D'ARLAS ACTIF (drapeau saison_essai_e_sans_retour_arlas.txt)");
	end;

	if F then
		core:add_listener(
			"saison_essai_tour11_f",
			"FactionBeginTurnPhaseNormal",
			function(context) return context:faction():name() == MODRYN and cm:model():turn_number() == TOUR_F end,
			function(context)
				sans_risque("essai F", function()
					local f = context:faction();
					if not f:has_faction_leader() then
						out("[T11] ESSAI F : Modryn n'a deja plus de chef au tour " .. TOUR_F);
						return;
					end;
					local chef = f:faction_leader();
					out("[T11] ESSAI F : chef de Modryn cqi " .. chef:command_queue_index() .. " battu d'office (armee detruite)");
					cm:kill_character(chef:command_queue_index(), true);
				end);
			end,
			false
		);
		out("[T11] ESSAI F CHEF BATTU ACTIF (drapeau saison_essai_f_chef_battu.txt, tour " .. TOUR_F .. ")");
	end;

	if not JOURNAL then
		return;
	end;
	out("[T11] JOURNAL ACTIF a partir du tour " .. TOUR_JOURNAL);

	core:add_listener(
		"saison_essai_tour11_debut",
		"FactionBeginTurnPhaseNormal",
		function(context) return journal_voulu(context:faction():name()) end,
		function(context)
			local nom = context:faction():name();
			local tour = cm:model():turn_number();
			sans_risque("photo", photographier, "tour " .. tour .. ", debut du tour de " .. nom);
			if C2 and nom == DRYCHA and tour >= TOUR_C2 then
				local n = cm:kill_all_armies_for_faction(context:faction());
				out("[T11] ESSAI C2 : armees de Drycha detruites au tour " .. tour .. " : " .. tostring(n));
			end;
		end,
		true
	);
	core:add_listener(
		"saison_essai_tour11_fin",
		"FactionTurnEnd",
		function(context) return journal_voulu(context:faction():name()) end,
		function(context)
			sans_risque("photo", photographier, "tour " .. cm:model():turn_number() .. ", fin du tour de " .. context:faction():name());
		end,
		true
	);
end;


if C1 or C2 or JOURNAL then
	sans_risque("armement", armer);
end;
