-----------------------------------------------------------------------------------
--	Le Duc rouge (wh_main_vmp_mousillon) : script de faction, chargé avant le premier tick par saison_start.lua.
--
--	Seigneur de WH3 rendu jouable sur notre carte (23.09.2026, demande de Charles) : intro à la manière des Empires
--	(caméra plongeante sur Mousillon, sans réplique : le Duc rouge n'en a pas dans WH3), par le module faction_intro.lua et
--	nos données (faction_intro/wh_dlc05_wood_elves_faction_intro.lua).
-----------------------------------------------------------------------------------

if cm:is_new_game() and not saison_bloquee and not saison_en_essai_auto() then
	saison_sur(
		"intro du Duc rouge",
		function()
			faction_intro:perform_intro("wh_dlc05_wood_elves", "wh_main_vmp_mousillon");
		end
	);
end;
