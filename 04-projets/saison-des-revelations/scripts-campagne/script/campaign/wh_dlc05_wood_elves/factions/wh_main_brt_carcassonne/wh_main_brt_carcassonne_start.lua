-----------------------------------------------------------------------------------
--	la Fée Enchanteresse (Carcassonne) (wh_main_brt_carcassonne) : script de faction, chargé avant le premier tick par saison_start.lua.
--
--	Seigneur de WH3 jouable sur notre carte (23.09.2026) : l'intro de CA des Empires Immortels (caméra plongeante et
--	réplique doublée d'intro), par le module faction_intro.lua et nos données
--	(faction_intro/wh_dlc05_wood_elves_faction_intro.lua).
-----------------------------------------------------------------------------------

if cm:is_new_game() and not saison_bloquee and not saison_en_essai_auto() then
	saison_sur(
		"intro de la Fee Enchanteresse",
		function()
			faction_intro:perform_intro("wh_dlc05_wood_elves", "wh_main_brt_carcassonne");
		end
	);
end;
