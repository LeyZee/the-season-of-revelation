-----------------------------------------------------------------------------------
--	Durthu (wh_dlc05_wef_argwylon) : script de faction, chargé avant le premier tick par saison_start.lua.
--
--	L'intro de la mini-campagne de WH1 (factions/wh_dlc05_wef_mini_argwylon/..._start.lua) : 42 s, sa scène Cindy,
--	quatre répliques aux mêmes instants que dans WH1, caméra de jeu de WH1 (181,7 ; 164,3 ; d 10 ; b 0 ; h 10).
-----------------------------------------------------------------------------------

if cm:is_new_game() and not saison_bloquee and not saison_en_essai_auto() then
	saison_sur(
		"intro de Durthu",
		saison_jouer_intro,
		"wh_dlc05_wef_argwylon",
		{
			duree = 42,
			video = "warhammer/race_intro_wef_mini",
			cindy = "script/campaign/wh_dlc05_wood_elves/factions/wh_dlc05_wef_argwylon/scenes/we_durthu_mini_intro.CindyScene",
			cam_jeu = {x = 181.7, y = 164.3, d = 10, b = 0, h = 10},
			conseils = {
				{"dlc05.mini.story.durthu.001", 0.5, 6},
				{"dlc05.mini.story.durthu.002", 10, 14},
				{"dlc05.mini.story.durthu.003", 18, 25},
				{"dlc05.mini.story.durthu.004", 30, 35}
			},
			temps = {eveil = {0.5, 8}, foret = {10, 6}, salles = {18, 10}, retour = {30, 8}}
		}
	);
end;
