-----------------------------------------------------------------------------------
--	Intros des seigneurs de WH3 jouables sur notre carte (Alberic, la Fée Enchanteresse, Morghur), pour le module de
--	CA faction_intro.lua (faction_intro:perform_intro("wh_dlc05_wood_elves", faction), appelé par leur script de
--	faction). Orion et Durthu gardent l'intro de la mini-campagne de WH1 (saison_intro.lua).
--
--	Même mise en scène qu'aux Empires Immortels (main_warhammer_faction_intro.lua) : « zoom_in_and_speak », la caméra
--	part de haut et plonge sur le seigneur pendant sa réplique doublée d'intro de WH3 (wh3_dlc21_ie_camp_*_intro_01 :
--	« Je jure de chercher le Graal... », « Les heures sont sombres... », « Ils vont voir notre puissance... »), puis
--	« Comment jouer » de CA. Les positions ne sont pas relevées à la main : ce fichier est lu au premier tour, et la
--	caméra vise le chef de la faction (sa capitale s'il y tient garnison, son armée sinon).
-----------------------------------------------------------------------------------

local data = {
	load_order = 0,
	map_ui = {"campaign_3d_ui", "parchment_overlay", "campaign_flags", "campaign_flags_strength_bars"},
	factions_using_lord_as_variant_key = {},
	variant_key_getters = {}
};

data.intro_presets = {
	standard = {
		how_they_play = true
	}
};

-- La caméra de CA au-dessus du chef de faction : vue haute de départ, vue de jeu d'arrivée (valeurs moyennes des
-- intros des Empires : d 22 / h 63 au départ, d 8,5 / h 10 à l'arrivée).
local function cameras(faction_key)
	local faction = cm:get_faction(faction_key);
	if not faction or faction:is_dead() then
		return nil, nil;
	end;
	local chef = faction:faction_leader();
	if not chef or chef:is_null_interface() then
		return nil, nil;
	end;
	local x, y = chef:display_position_x(), chef:display_position_y();
	return {x = x, y = y - 4, d = 22, b = 0, h = 63}, {x = x, y = y, d = 8.5, b = 0, h = 10};
end;

data.cutscene_styles = {
	-- recopie de celle de CA (main_warhammer_faction_intro.lua)
	zoom_in_and_speak = function(self)
		if not (self.cam_cutscene_start and self.cam_gameplay_start and self.advice_line) then
			script_error("La Saison des Revelations : intro sans camera ni replique, faction introuvable ?");
			return false, "cam_cutscene_start, cam_gameplay_start, advice_line";
		end;

		local new_configurator = function(cutscene)
			cutscene:set_relative_mode(true);
			cutscene:action_fade_scene(0, 1, 3.5);
			cutscene:action_override_ui_visibility(0, false, data.map_ui);
			cutscene:action_set_camera_position(0, {self.cam_cutscene_start.x, self.cam_cutscene_start.y,
				self.cam_cutscene_start.d, self.cam_cutscene_start.b, self.cam_cutscene_start.h});
			cutscene:action_scroll_camera_to_position(1, 8, true, {self.cam_gameplay_start.x, self.cam_gameplay_start.y,
				self.cam_gameplay_start.d, self.cam_gameplay_start.b, self.cam_gameplay_start.h});
			cutscene:action_show_advice(5, self.advice_line);
			cutscene:action(
				function()
					cutscene:wait_for_advisor();
				end,
				2
			);
			cutscene:action_end_cutscene(0);
			cutscene:prepend_end_cutscene(
				function()
					for u = 1, #data.map_ui do
						cm:get_campaign_ui_manager():override(data.map_ui[u]):set_allowed(true);
					end;
				end
			);
		end;

		return new_configurator;
	end
};

-- Le Duc rouge n'a pas de réplique d'intro dans WH3 (il n'est jouable nulle part chez CA) : la même plongée, sans
-- parole.
data.cutscene_styles.zoom_in = function(self)
	if not (self.cam_cutscene_start and self.cam_gameplay_start) then
		script_error("La Saison des Revelations : intro sans camera, faction introuvable ?");
		return false, "cam_cutscene_start, cam_gameplay_start";
	end;

	local new_configurator = function(cutscene)
		cutscene:set_relative_mode(true);
		cutscene:action_fade_scene(0, 1, 3.5);
		cutscene:action_override_ui_visibility(0, false, data.map_ui);
		cutscene:action_set_camera_position(0, {self.cam_cutscene_start.x, self.cam_cutscene_start.y,
			self.cam_cutscene_start.d, self.cam_cutscene_start.b, self.cam_cutscene_start.h});
		cutscene:action_scroll_camera_to_position(1, 8, true, {self.cam_gameplay_start.x, self.cam_gameplay_start.y,
			self.cam_gameplay_start.d, self.cam_gameplay_start.b, self.cam_gameplay_start.h});
		cutscene:action_end_cutscene(1);
		cutscene:prepend_end_cutscene(
			function()
				for u = 1, #data.map_ui do
					cm:get_campaign_ui_manager():override(data.map_ui[u]):set_allowed(true);
				end;
			end
		);
	end;

	return new_configurator;
end;

local function intro(faction_key, replique)
	local depart, arrivee = cameras(faction_key);
	return faction_intro_data:new{
		preset = data.intro_presets.standard,
		cam_cutscene_start = depart,
		cam_gameplay_start = arrivee,
		advice_line = replique,
		cutscene_style = replique and data.cutscene_styles.zoom_in_and_speak or data.cutscene_styles.zoom_in
	};
end;

data.faction_intros = {
	wh_main_brt_bordeleaux = intro("wh_main_brt_bordeleaux", "wh3_dlc21_ie_camp_brt_alberic_intro_01"),
	wh_main_brt_carcassonne = intro("wh_main_brt_carcassonne", "wh3_dlc21_ie_camp_brt_fay_enchantress_intro_01"),
	wh_dlc05_bst_morghur_herd = intro("wh_dlc05_bst_morghur_herd", "wh3_dlc21_ie_camp_bst_morghur_intro_01"),
	wh_main_vmp_mousillon = intro("wh_main_vmp_mousillon", nil),
	-- Drycha, Kemmler, Grom (23.09.2026, spec-drycha-kemmler-grom.md) : Kemmler et Grom partent aux Empires des mêmes
	-- lieux que chez nous (Poste de la Pierre Noire, Massif d'Orquemont), leur réplique de CA leur va ; Drycha y part
	-- d'une forêt de l'Empire : plongée sans parole, comme le Duc rouge
	wh2_dlc16_wef_drycha = intro("wh2_dlc16_wef_drycha", nil),
	wh2_dlc11_vmp_the_barrow_legion = intro("wh2_dlc11_vmp_the_barrow_legion", "wh3_dlc21_ie_camp_vmp_kemmler_intro_01"),
	wh2_dlc15_grn_broken_axe = intro("wh2_dlc15_grn_broken_axe", "wh3_dlc21_ie_camp_grn_grom_intro_01"),
	-- les Sœurs du Crépuscule (24.09.2026) : leur réplique de CA ne cite aucun lieu (« Les Sœurs du Crépuscule, prêtes à
	-- tout ! », niveau de conseil 1223628519) : elle leur va ; puis leur prologue (saison_prologue.lua) dit leur situation
	wh2_dlc16_wef_sisters_of_twilight = intro("wh2_dlc16_wef_sisters_of_twilight", "wh3_dlc21_ie_camp_wef_sisters_of_twilight_intro_01")
};

return data;
