-----------------------------------------------------------------------------------
--	L'intro de la mini-campagne de WH1, jouée à la manière de WH3.
--
--	WH1 (factions/wh_dlc05_wef_mini_*/..._start.lua de la mini-campagne) : une cinématique de 48 s (Orion) ou 42 s
--	(Durthu), brouillard levé, quatre répliques du conseiller (dlc05.mini.story.orion|durthu.001 à 004, toujours
--	présentes dans la base et l'audio de WH3), et la scène Cindy de WH1 (scenes/we_*_mini_intro.CindyScene, caméra
--	cameras/*_mini_intro.xml : 10 images clés pour Orion, 7 pour Durthu, dans le repère de notre carte). On rejoue
--	cette scène d'origine (fichiers de WH1 recopiés dans nos dossiers de faction, format 21 ; WH3 lit encore les
--	formats 22 et 23). En réserve, sans scène : un vol scripté qui suit le texte (éveil du seigneur, forêt malade,
--	grandes salles tombées, Chêne des Âges, retour au seigneur), avec les positions des colonies lues en jeu.
--	L'outil d'intro de WH3 (cm:setup_campaign_intro_cutscene) gère le fondu, le saut (toutes les répliques s'affichent
--	alors), le brouillard, et déclenche ScriptEventIntroCutsceneFinished : le narratif de WH3 enchaîne « Comment
--	jouer » puis les objectifs.
-----------------------------------------------------------------------------------

local REGIONS_ATHEL_LOREN = {
	"wh_dlc05_anmyr_halls_of_anaereth", "wh_dlc05_anmyr_tal_rond", "wh_dlc05_argwylon_waterfall_palace",
	"wh_dlc05_arranoc_tal_esth", "wh_dlc05_atylwyth_tal_amere", "wh_dlc05_cavaroc_halls_of_equos",
	"wh_dlc05_cythral_tyr_vanna", "wh_dlc05_fyr_darric_feast_halls", "wh_dlc05_fyr_darric_threllock",
	"wh_dlc05_modryn_glade_of_eternal_midnight", "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_talsyn_yn_ecryl_koiran", "wh_dlc05_tirsyth_glade_of_eternal_moonlight", "wh_dlc05_torgovann_cromlech_cadai",
	"wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_crag_halls", "wh_dlc05_wydrioth_tal_jul_finel"
};

-- Les grandes salles abandonnées au départ (sans propriétaire dans le startpos de WH1).
local SALLES_TOMBEES = {
	"wh_dlc05_anmyr_tal_rond", "wh_dlc05_fyr_darric_threllock", "wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_tal_jul_finel"
};

local CHENE = "wh_dlc05_oak_of_ages";


local function position_colonie(region_key)
	local region = cm:get_region(region_key);
	if not region or region:is_null_interface() then
		return nil;
	end;
	local colonie = region:settlement();
	if not colonie or colonie:is_null_interface() then
		return nil;
	end;
	return colonie:display_position_x(), colonie:display_position_y();
end;


local function centre(regions)
	local sx, sy, n = 0, 0, 0;
	for i = 1, #regions do
		local x, y = position_colonie(regions[i]);
		if x then
			sx, sy, n = sx + x, sy + y, n + 1;
		end;
	end;
	if n == 0 then
		return nil;
	end;
	return sx / n, sy / n;
end;


local function plus_proches(regions, x0, y0, n)
	local liste = {};
	for i = 1, #regions do
		local x, y = position_colonie(regions[i]);
		if x then
			table.insert(liste, {x = x, y = y, d = (x - x0) * (x - x0) + (y - y0) * (y - y0)});
		end;
	end;
	table.sort(liste, function(a, b) return a.d < b.d end);
	local out = {};
	for i = 1, math.min(n, #liste) do
		out[i] = liste[i];
	end;
	return out;
end;


-- La vidéo plein écran d'avant la scène (23.09.2026, Charles : « une vidéo qui montre les enjeux de la campagne ») :
-- celle de la mini-campagne de WH1 (race_intro_wef_mini, clé de la table videos, fichier sous movies/), jouée par
-- l'outil d'intro de CA comme les vidéos des seigneurs de WH3. Seulement si le fichier est dans le jeu : sans lui,
-- l'intro part directement sur la scène.
-- posé par le menu quand il avait joué la vidéo avant le chargement. Script du menu retiré le 23.09.2026, 13 h (Charles :
-- Échap ne la passait pas et ouvrait la fenêtre pour quitter le jeu ; après le chargement, Échap la passe) : le drapeau
-- n'est plus posé, la vidéo passe ici après le chargement. Copie du script retiré :
-- 05-journal\2026-09-22-gameplay-wh3\saison_video_avant_chargement.lua.retire
local SVR_VIDEO_AU_MENU = "saison_video_intro_jouee";

local function video_presente(cle)
	if not is_string(cle) then
		return false;
	end;
	local dossier, fichier = string.match(cle, "^(.*/)([^/]+)$");
	if not fichier then
		dossier, fichier = "", cle;
	end;
	local ok, trouve = pcall(function() return common.filesystem_lookup("/movies/" .. dossier, fichier .. ".ca_vp8") end);
	return ok and is_string(trouve) and trouve ~= "";
end;


--	p = {
--		duree = secondes,
--		video = clé de la table videos jouée en plein écran avant la scène (facultatif),
--		cam_jeu = {x, y, d, b, h} : caméra de jeu à la fin (celle de WH1),
--		conseils = { {clé, début, attente de la voix}, ... } : les temps de WH1,
--		cindy = chemin de la scène Cindy de WH1 (sa caméra d'origine) ; si absent, vol scripté ci-dessous,
--		temps = { eveil = {début, durée}, foret = {...}, salles = {...}, retour = {...} } : le vol scripté
--	}
function saison_jouer_intro(faction_key, p)
	if saison_en_essai_auto() then
		return;
	end;
	local cles = {};
	for i = 1, #p.conseils do
		cles[i] = p.conseils[i][1];
	end;

	local function repliques(c)
		-- les répliques de WH1, aux mêmes instants que dans WH1, et l'attente de la fin de la voix
		for i = 1, #p.conseils do
			local cle, debut, attente = p.conseils[i][1], p.conseils[i][2], p.conseils[i][3];
			c:action(function() cm:show_advice(cle) end, debut);
			c:action(function() c:wait_for_advisor() end, attente);
		end;
	end;

	-- Comme WH1 : la scène Cindy d'origine (scène + fichier de caméra) prend la caméra pendant toute l'intro.
	local function configurer_cindy(c)
		c:action(
			function()
				common.clear_advice_session_history();
				c:cindy_playback(p.cindy, 0, 0);
			end,
			0
		);
		repliques(c);
	end;

	local function configurer(c)
		local jx, jy = p.cam_jeu.x, p.cam_jeu.y;
		local fx, fy = centre(REGIONS_ATHEL_LOREN);
		fx, fy = fx or jx, fy or jy;
		local cx, cy = position_colonie(CHENE);
		cx, cy = cx or fx, cy or fy;
		local salles = plus_proches(SALLES_TOMBEES, jx, jy, 2);

		-- vue haute au-dessus du seigneur, sous le fondu d'ouverture
		c:action(
			function()
				common.clear_advice_session_history();
				cm:set_camera_position(jx, jy, 22, 0, 58);
			end,
			0
		);

		-- l'éveil : on descend vers le seigneur
		c:action(
			function()
				cm:scroll_camera_from_current(false, p.temps.eveil[2], {jx, jy, 12, 0, 15});
			end,
			p.temps.eveil[1]
		);

		-- la forêt malade : vol vers le cœur d'Athel Loren
		c:action(
			function()
				cm:scroll_camera_from_current(false, p.temps.foret[2], {fx, fy, 16, 0.35, 21});
			end,
			p.temps.foret[1]
		);

		-- les grandes salles tombées, puis le Chêne des Âges
		c:action(
			function()
				local points = {};
				for i = 1, #salles do
					table.insert(points, {salles[i].x, salles[i].y, 11, 0.6, 12});
				end;
				table.insert(points, {cx, cy, 9, 0.2, 9});
				cm:scroll_camera_from_current(false, p.temps.salles[2], unpack(points));
			end,
			p.temps.salles[1]
		);

		-- retour au seigneur, à la caméra de jeu de WH1
		c:action(
			function()
				cm:scroll_camera_from_current(true, p.temps.retour[2], {jx, jy, p.cam_jeu.d, p.cam_jeu.b, p.cam_jeu.h});
			end,
			p.temps.retour[1]
		);

		repliques(c);
	end;

	local film = nil;
	if p.video and core:svr_load_bool(SVR_VIDEO_AU_MENU) then
		-- déjà jouée au menu, avant le chargement, comme dans WH1 (script/frontend/mod/saison_video_avant_chargement.lua)
		core:svr_save_bool(SVR_VIDEO_AU_MENU, false);
		out("La Saison des Revelations : video deja jouee au menu, avant le chargement : intro sans video");
	elseif video_presente(p.video) then
		film = p.video;
	elseif p.video then
		out("La Saison des Revelations : video " .. tostring(p.video) .. " absente du jeu, intro sans video");
	end;

	cm:setup_campaign_intro_cutscene(faction_key, p.cam_jeu, p.duree, cles, nil, p.cindy and configurer_cindy or configurer,
		film, false);
end;
