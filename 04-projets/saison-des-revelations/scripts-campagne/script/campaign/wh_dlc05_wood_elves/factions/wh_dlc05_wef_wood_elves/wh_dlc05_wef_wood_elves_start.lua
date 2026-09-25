-----------------------------------------------------------------------------------
--	Orion (wh_dlc05_wef_wood_elves) : script de faction, chargé avant le premier tick par saison_start.lua.
--
--	L'intro de la mini-campagne de WH1 (factions/wh_dlc05_wef_mini_wood_elves/..._start.lua) : 48 s, sa scène Cindy,
--	quatre répliques aux mêmes instants que dans WH1, caméra de jeu de WH1 (181,344 ; 70,171 ; d 9,527 ; b 0 ; h 10).
-----------------------------------------------------------------------------------

if cm:is_new_game() and not saison_bloquee and not saison_en_essai_auto() then
	saison_sur(
		"intro d'Orion",
		saison_jouer_intro,
		"wh_dlc05_wef_wood_elves",
		{
			duree = 48,
			video = "warhammer/race_intro_wef_mini",
			cindy = "script/campaign/wh_dlc05_wood_elves/factions/wh_dlc05_wef_wood_elves/scenes/we_orion_mini_intro.CindyScene",
			cam_jeu = {x = 181.344, y = 70.171, d = 9.527, b = 0, h = 10},
			conseils = {
				{"dlc05.mini.story.orion.001", 0.5, 10.5},
				{"dlc05.mini.story.orion.002", 11.5, 16},
				{"dlc05.mini.story.orion.003", 17, 28},
				{"dlc05.mini.story.orion.004", 29, 48}
			},
			temps = {eveil = {0.5, 9.5}, foret = {11.5, 5}, salles = {17, 11}, retour = {29, 9}}
		}
	);
end;
