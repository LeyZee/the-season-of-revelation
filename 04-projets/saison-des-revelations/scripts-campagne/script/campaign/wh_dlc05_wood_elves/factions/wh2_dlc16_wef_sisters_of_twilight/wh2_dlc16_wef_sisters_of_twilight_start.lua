-----------------------------------------------------------------------------------
--	Les Sœurs du Crépuscule (wh2_dlc16_wef_sisters_of_twilight) : script de faction, chargé avant le premier tick par
--	saison_start.lua (load_local_faction_script : sans ce fichier, erreur de script et aucune intro, donc aucun prologue).
--
--	10e seigneure jouable (spec-soeurs-du-crepuscule.md, 24.09.2026) : l'intro de CA des Empires Immortels (caméra
--	plongeante et réplique « Les Sœurs du Crépuscule, prêtes à tout ! »), par le module faction_intro.lua et nos données
--	(faction_intro/wh_dlc05_wood_elves_faction_intro.lua) ; à sa fin, leur prologue (saison_prologue.lua).
-----------------------------------------------------------------------------------

if cm:is_new_game() and not saison_bloquee and not saison_en_essai_auto() then
	saison_sur(
		"intro des Soeurs du Crepuscule",
		function()
			faction_intro:perform_intro("wh_dlc05_wood_elves", "wh2_dlc16_wef_sisters_of_twilight");
		end
	);
end;
