-----------------------------------------------------------------------------------
--	La Saison des Révélations : écrans de chargement d'Orion et de Durthu (menu principal).
--
--	Au clic sur « Commencer », frontend_start.lua de CA (set_custom_loading_screen) lit l'identifiant de départ
--	(start_pos_characters) du seigneur choisi et cherche son écran dans custom_loading_screens_no_intro ; sans entrée,
--	erreur de script et écran générique (audit de l'interface du 23.09.2026, C1). Nos écrans (tables
--	custom_loading_screens et custom_loading_screen_components, lot 6) reprennent ceux de CA, avec le récit de
--	chargement de la mini-campagne de WH1.
--
--	Les mods du menu sont chargés par load_script_libraries(), AVANT le require("frontend_custom_loading_screens") qui
--	recrée la table : on ajoute nos lignes une fois l'interface créée.
-----------------------------------------------------------------------------------

local SAISON_ECRANS = {
	["2140783885"] = "wh_dlc05_wef_wood_elves_orion_mini",		-- Orion
	["2140783843"] = "wh_dlc05_wef_argwylon_durthu_mini",		-- Durthu
	-- seigneurs de WH3 rendus jouables (lot 8) ; sans effet tant qu'ils ne sont pas choisissables
	["2140783762"] = "wh_main_brt_bordeleaux_alberic_mini",		-- Alberic
	["2140783791"] = "wh_main_brt_carcassonne_fay_mini",		-- la Fée Enchanteresse
	["2140783911"] = "wh_dlc05_bst_morghur_herd_morghur_mini",	-- Morghur
	["2140784082"] = "wh_main_vmp_mousillon_red_duke_mini",		-- le Duc rouge
	-- Drycha, Kemmler, Grom (23.09.2026, identifiants de départ posés par la construction)
	["2140783871"] = "wh2_dlc16_wef_drycha_drycha_mini",		-- Drycha
	["2140784200"] = "wh2_dlc11_vmp_the_barrow_legion_kemmler_mini",	-- Heinrich Kemmler
	["2140783823"] = "wh2_dlc15_grn_broken_axe_grom_mini",		-- Grom la Panse
	-- les Sœurs du Crépuscule (24.09.2026, identifiant de départ posé par la construction)
	["2140784201"] = "wh2_dlc16_wef_sisters_of_twilight_sisters_mini"
};

-- Sous pcall : core:ui_created appelle les rappels à la suite sans protection ; les nôtres passent avant ceux de
-- frontend_start.lua, qu'une erreur ici ne doit pas empêcher de tourner.
core:add_ui_created_callback(
	function()
		local ok, err = pcall(
			function()
				for id, ecran in pairs(SAISON_ECRANS) do
					if type(custom_loading_screens_no_intro) == "table" then
						custom_loading_screens_no_intro[id] = ecran;
					end;
					if type(custom_loading_screens_with_intro) == "table" then
						custom_loading_screens_with_intro[id] = ecran;
					end;
				end;
			end
		);
		if not ok then
			script_error("La Saison des Revelations (menu) : ecrans de chargement non installes : " .. tostring(err));
		end;
	end
);
