-----------------------------------------------------------------------------------
--	La Saison des Révélations : le prologue de chaque seigneur, juste après son intro (demande de Charles, 23.09.2026 :
--	« des scripts au début… qui bougent la caméra et t'indiquent les menaces, les objectifs… avec de jolis textes »).
--
--	Une cinématique de campagne de CA (campaign_cutscene, passable par Échap) : bandes de cinéma, brouillard levé le temps
--	du survol, la caméra vole d'un lieu à l'autre ; à chaque lieu, une réplique du conseiller (advice_levels,
--	conseiller « faction_leader » : le seigneur lui-même parle, comme les répliques d'intro de CA des Empires ; textes
--	advice_levels_onscreen_text_<clé>, lot 14 de donnees_campagne.py), puis retour sur le seigneur. Joué une seule fois
--	par partie (valeur sauvegardée), après ScriptEventCampaignIntroComplete (intros de CA, faction_intro.lua) ou
--	ScriptEventIntroCutsceneFinished (intros de WH1, saison_intro.lua). Rien en multijoueur ni en essai automatique.
--
--	Données : SAISON_PROLOGUES[faction] = { {x, y, d, b, h, conseil = fil de conseil, region = région à révéler,
--	vol = durée du vol, duree = temps de lecture}, ... } ; x, y en coordonnées d'affichage (logique x 0,6661 ; y x 0,7704) ;
--	{chef = true, ...} : l'étape se fait au-dessus du seigneur (sautée si sa position est inconnue).
--
--	Survol doublé fusionné (Charles, 24.09.2026, 22 h 30, à la manière des survols d'introduction de la 9.0) : pour les
--	huit seigneurs hors Orion et Durthu, des répliques DOUBLÉES de WH1 et WH2 (conseiller standard, voix française ou
--	anglaise selon la langue du jeu ; fils déjà dans la base du jeu) s'intercalent entre nos répliques écrites, aux lieux
--	dont elles parlent ; « duree » = voix la plus longue (EN ou FR) + 1,5 s. Le Duc écarlate n'a aucune réplique doublée :
--	son prologue reste muet (choix de Charles). Répliques écartées (lore) : morghur 002 et 004, drycha 001 et 003, sisters
--	001 à 003, grom 003 et 004, alberic 003 et 004, fay 004 et 005, kemmler 001 (lieux hors carte ou contexte faux) ;
--	laissées pour tenir environ 90 s : alberic 006, fay 003 et 006, morghur 005, kemmler 004. Voix de la 9.0 non reprises
--	(anglais seulement). Étude : scratchpad survols-9.0\rapport-survols.md.
-----------------------------------------------------------------------------------

local PREFIXE = "saison_prologue_";
local VOL = 4;			-- secondes de vol entre deux lieux
local LECTURE = 9;		-- secondes de lecture d'une réplique

SAISON_PROLOGUES = SAISON_PROLOGUES or {};	-- remplie en fin de fichier


local function position_du_chef(faction)
	local f = cm:get_faction(faction);
	if f and f:has_faction_leader() then
		local chef = f:faction_leader();
		if not chef:is_null_interface() then
			if chef:has_military_force() or not chef:has_region() then
				return chef:display_position_x(), chef:display_position_y();
			end;
			local ville = chef:region():settlement();
			return ville:display_position_x(), ville:display_position_y();
		end;
	end;
	return nil;
end;


-- Rend true si la cinématique a démarré (sinon rien n'est marqué : saison_prologue_essayer réessaie).
function saison_jouer_prologue(faction)
	local etapes = SAISON_PROLOGUES[faction];
	if not etapes or #etapes == 0 or cm:get_saved_value(PREFIXE .. faction) then
		return true;
	end;
	if cm:is_any_cutscene_running() then
		return false;
	end;

	local x0, y0 = position_du_chef(faction);
	local duree = 1;
	for i = 1, #etapes do
		if x0 or not etapes[i].chef then
			duree = duree + (etapes[i].vol or VOL) + (etapes[i].duree or LECTURE);
		end;
	end;
	duree = duree + VOL + 1;
	-- Brouillard de guerre comme aux Empires (Charles, 24.09.2026, 01 h 05 : « quand je dézoome, on n'est pas censé voir
	-- le reste ») : le brouillard est levé le temps du vol (set_disable_shroud) et remis par CA à la fin de la cinématique
	-- (restore_shroud) ; les lieux montrés ne restent PLUS découverts (jusqu'au 24.09, make_region_visible_in_shroud les
	-- laissait vus pour toute la partie)
	local c = campaign_cutscene:new(PREFIXE .. faction, duree, function() end);
	c:set_skippable(true, function() cm:dismiss_advice() end);
	c:set_use_cinematic_borders(true);
	c:set_disable_shroud(true);
	c:set_dismiss_advice_on_end(true);
	if x0 then
		c:set_restore_camera(2, x0, y0, 14.768, 0.0, 12.0);
		c:set_skip_camera(x0, y0, 14.768, 0.0, 12.0);
	end;

	-- les répliques doublées de WH1 et WH2 ont pu être entendues dans une autre partie : l'historique du conseil est vidé
	-- pour qu'elles repartent (comme saison_intro.lua)
	c:action(function() common.clear_advice_session_history() end, 0);

	local t = 0.5;
	for i = 1, #etapes do
		local e = etapes[i];
		local x, y = e[1], e[2];
		if e.chef then
			x, y = x0, y0;
		end;
		if x then
			local vol = e.vol or VOL;
			c:action_scroll_camera_to_position(t, vol, false, {x, y, e[3] or 14.768, e[4] or 0.0, e[5] or 12.0});
			c:action_show_advice(t + vol, e.conseil);
			t = t + vol + (e.duree or LECTURE);
		end;
	end;
	if x0 then
		c:action_scroll_camera_to_position(t, VOL, true, {x0, y0, 14.768, 0.0, 12.0});
	end;
	if c:start() == false then
		return false;
	end;
	cm:set_saved_value(PREFIXE .. faction, true);
	out("La Saison des Revelations : prologue de " .. faction .. " (" .. #etapes .. " lieux, " .. duree .. " s)");
	return true;
end;


-- G4 : le prologue attend que les panneaux d'évènement soient fermés (« Comment jouer » de CA ou le nôtre, missions
-- du narratif) ; s'il ne peut pas partir (autre cinématique), nouvel essai, dix au plus.
function saison_prologue_essayer(faction, essai)
	essai = essai or 1;
	cm:progress_on_events_dismissed(PREFIXE .. "attente", function()
		local ok, parti = pcall(saison_jouer_prologue, faction);
		if not ok then
			script_error("La Saison des Revelations : prologue a echoue : " .. tostring(parti));
		elseif not parti and essai < 10 then
			cm:callback(function() saison_prologue_essayer(faction, essai + 1) end, 2);
		end;
	end, 1);
end;


-- Un seul Échap passe tout (Charles, 24.09.2026, 03 h : « je pensais avoir fait Échap pour y échapper et puis ça
-- revient ») : si le joueur passe l'intro de sa faction (notre intro de WH1 ou celle de CA, deux campaign_cutscene dont
-- le nom contient « intro »), le prologue est tenu pour vu et ne part pas. Le prologue lui-même est une seule
-- cinématique : Échap la passe en entier. Hors cinématique, rien ne bloque l'armée du joueur.
local function passer_le_prologue_avec_l_intro(faction)
	if not (campaign_cutscene and is_function(campaign_cutscene.skip)) or campaign_cutscene.saison_skip_enveloppe then
		return;
	end;
	local ca_skip = campaign_cutscene.skip;
	campaign_cutscene.skip = function(self, ...)
		local tournait = self.is_running;
		local res = ca_skip(self, ...);
		if tournait and not cm:get_saved_value(PREFIXE .. faction) and is_string(self.name)
			and string.find(string.lower(self.name), "intro") then
			cm:set_saved_value(PREFIXE .. faction, true);
			out("La Saison des Revelations : intro passee par le joueur (" .. self.name .. ") : prologue passe aussi");
		end;
		return res;
	end;
	campaign_cutscene.saison_skip_enveloppe = true;
end;


-- À chaque chargement (saison_start.lua) : attend la fin de l'intro de la faction jouée, une seule fois par partie.
function saison_prologue_ecouteurs()
	if cm:is_multiplayer() or saison_en_essai_auto() then
		return;
	end;
	local faction = cm:get_local_faction_name(true);
	if not faction or not SAISON_PROLOGUES[faction] or cm:get_saved_value(PREFIXE .. faction) then
		return;
	end;
	passer_le_prologue_avec_l_intro(faction);
	for _, evenement in ipairs({"ScriptEventCampaignIntroComplete", "ScriptEventIntroCutsceneFinished"}) do
		core:add_listener(
			PREFIXE .. evenement,
			evenement,
			true,
			function()
				core:remove_listener(PREFIXE .. "ScriptEventCampaignIntroComplete");
				core:remove_listener(PREFIXE .. "ScriptEventIntroCutsceneFinished");
				if not cm:get_saved_value(PREFIXE .. faction) then
					-- « Comment jouer » s'ouvre vers 1 s après la fin de l'intro (narratif de CA) : on le laisse paraître
					cm:callback(function() saison_sur("prologue", saison_prologue_essayer, faction) end, 2.5);
				end;
			end,
			false
		);
	end;
end;


-- Les prologues (données : scratchpad\audit-ui\prologues.py, textes au lot 14 de donnees_campagne.py).
SAISON_PROLOGUES = {
	-- Alberic : 001 (salut, la côte), 002 (« directement au nord, Mousillon » : remplace notre réplique 1, même lieu,
	-- même sens), 005 (Peaux-Vertes et Nains des montagnes), au-dessus du Massif d'Orquemont ; environ 90 s
	wh_main_brt_bordeleaux = {
		{chef = true, vol = 1, conseil = "dlc07.camp.flyby.brt.alberic.001", duree = 13.2},
		{36.0, 233.4, conseil = "dlc07.camp.flyby.brt.alberic.002", duree = 14.9, region = "wh_dlc05_mousillon_mousillon"},
		{41.3, 216.6, conseil = "saison_prologue_alberic_2", region = "wh_dlc05_bordeleaux_turris_vigilans"},
		{57.3, 187.2, conseil = "saison_prologue_alberic_3", region = "wh_dlc05_aquitaine_derrevin_libre"},
		{82.4, 209.7, conseil = "dlc07.camp.flyby.brt.alberic.005", duree = 12.9, region = "wh_dlc05_massif_orcal_massif_orcal"},
		{54.5, 231.5, conseil = "saison_prologue_alberic_4", region = "wh_dlc05_bastonne_humble_chapel"}
	},
	-- la Fée : 001 (bénédictions, royaume en péril), 002 (les Elfes d'Athel Loren sortent de la forêt), à Quenelles ;
	-- environ 85 s
	wh_main_brt_carcassonne = {
		{chef = true, vol = 1, conseil = "dlc07.camp.flyby.brt.fay.001", duree = 13.9},
		{52.8, 61.2, conseil = "saison_prologue_fee_1", region = "wh_dlc05_carcassonne_st_jacques"},
		{102.2, 126.0, conseil = "saison_prologue_fee_2", region = "wh_dlc05_quenelles_quenelles"},
		{102.2, 126.0, vol = 1, conseil = "dlc07.camp.flyby.brt.fay.002", duree = 13.9},
		{179.0, 79.4, conseil = "saison_prologue_fee_3", region = "wh_dlc05_oak_of_ages"},
		{120.6, 248.1, conseil = "saison_prologue_fee_4", region = "wh_dlc05_montfort_montfort"}
	},
	-- Morghur : 001 (agent éternel du changement), 003 (les Elfes Sylvains et leurs arbres-sanctuaires), au Chêne ;
	-- environ 95 s
	wh_dlc05_bst_morghur_herd = {
		{chef = true, vol = 1, conseil = "dlc05.mini.story.morghur.001", duree = 13.9},
		{78.6, 46.2, conseil = "saison_prologue_morghur_1", region = "wh_dlc05_carcassonne_st_jacques"},
		{140.8, 87.9, conseil = "saison_prologue_morghur_5", region = "wh_dlc05_torgovann_cromlech_cadai"},
		{134.6, 152.5, conseil = "saison_prologue_morghur_2", region = "wh_dlc05_anmyr_tal_rond"},
		{179.0, 79.4, conseil = "saison_prologue_morghur_3", region = "wh_dlc05_oak_of_ages"},
		{179.0, 79.4, vol = 1, conseil = "dlc05.mini.story.morghur.003", duree = 17.9},
		{120.6, 248.1, conseil = "saison_prologue_morghur_4", region = "wh_dlc05_montfort_montfort"}
	},
	wh_main_vmp_mousillon = {
		{36.0, 233.4, conseil = "saison_prologue_duc_1", region = "wh_dlc05_mousillon_mousillon"},
		{58.4, 189.6, conseil = "saison_prologue_duc_2", region = "wh_dlc05_aquitaine_derrevin_libre"},
		{42.0, 172.0, conseil = "saison_prologue_duc_3", region = "wh_dlc05_aquitaine_chateau_depee"},
		{41.3, 216.6, conseil = "saison_prologue_duc_4", region = "wh_dlc05_bordeleaux_turris_vigilans"}
	},
	-- Drycha : 002 (les Asrai, l'œuvre de Coeddil), aux pierres gardiennes ; 004 (Ronce de Malheur, vrais gardiens), sur
	-- elle pour finir ; environ 95 s
	wh2_dlc16_wef_drycha = {
		{203.8, 42.2, conseil = "saison_prologue_drycha_1", region = "wh_dlc05_cythral_tyr_vanna"},
		{203.8, 42.2, vol = 1, conseil = "wh2_dlc16.camp.drycha.intro.002", duree = 20.1},
		{134.6, 152.5, conseil = "saison_prologue_drycha_2", region = "wh_dlc05_anmyr_tal_rond"},
		{138.5, 223.5, conseil = "saison_prologue_drycha_3", region = "wh_dlc05_parravon_parravon"},
		{195.3, 74.6, conseil = "saison_prologue_drycha_4", region = "wh_dlc05_talsyn_yn_ecryl_koiran"},
		{chef = true, conseil = "wh2_dlc16.camp.drycha.intro.004", duree = 20.3}
	},
	-- Kemmler : 002 (« ici résident les Nains de Karak Ziflin »), au-dessus de Karak Ziflin ; 003 (par-delà les montagnes,
	-- les pâturages et Athel Loren), aux confins de Parravon ; 005 (frappez au cœur de la Bretonnie), sur lui ; environ 95 s
	wh2_dlc11_vmp_the_barrow_legion = {
		{202.8, 231.3, conseil = "saison_prologue_kemmler_1", region = "wh_dlc05_grey_mountains_2_blackstone_post"},
		{228.7, 236.7, conseil = "wh2_dlc11.camp.kemmler.intro.002", duree = 14.7, region = "wh_dlc05_grey_mountains_2_karak_ziflin"},
		{170.0, 241.0, conseil = "saison_prologue_kemmler_2", region = "wh_dlc05_grey_mountains_axe_bite_pass"},
		{165.0, 206.8, conseil = "saison_prologue_kemmler_3", region = "wh_dlc05_parravon_grunere"},
		{165.0, 206.8, vol = 1, conseil = "wh2_dlc11.camp.kemmler.intro.003", duree = 13.9},
		{107.9, 237.3, conseil = "saison_prologue_kemmler_4", region = "wh_dlc05_montfort_montfort"},
		{chef = true, conseil = "wh2_dlc11.camp.kemmler.intro.005", duree = 10.1}
	},
	-- Grom : 001 (Grom la Panse, le moral des boyz), au Massif ; 002 (les Bretonniens vous entourent), à Quenelles ;
	-- environ 90 s
	wh2_dlc15_grn_broken_axe = {
		{82.4, 209.7, conseil = "wh2_dlc15.camp.grom.intro.001", duree = 15.7},
		{82.4, 209.7, vol = 1, conseil = "saison_prologue_grom_1", region = "wh_dlc05_massif_orcal_massif_orcal"},
		{102.2, 126.0, conseil = "saison_prologue_grom_2", region = "wh_dlc05_quenelles_quenelles"},
		{102.2, 126.0, vol = 1, conseil = "wh2_dlc15.camp.grom.intro.002", duree = 17.8},
		{228.7, 236.7, conseil = "saison_prologue_grom_3", region = "wh_dlc05_grey_mountains_2_karak_ziflin"},
		{118.6, 127.1, conseil = "saison_prologue_grom_4", region = "wh_dlc05_quenelles_quenelles"}
	},
	wh_dlc05_wef_wood_elves = {
		{179.0, 79.4, conseil = "saison_prologue_orion_1", region = "wh_dlc05_oak_of_ages"},
		{78.6, 46.2, conseil = "saison_prologue_orion_2", region = "wh_dlc05_carcassonne_st_jacques"},
		{120.6, 248.1, conseil = "saison_prologue_orion_3", region = "wh_dlc05_montfort_montfort"}
	},
	wh_dlc05_wef_argwylon = {
		{179.0, 79.4, conseil = "saison_prologue_durthu_1", region = "wh_dlc05_oak_of_ages"},
		{78.6, 46.2, conseil = "saison_prologue_durthu_2", region = "wh_dlc05_carcassonne_st_jacques"},
		{120.6, 248.1, conseil = "saison_prologue_durthu_3", region = "wh_dlc05_montfort_montfort"}
	},
	-- les Sœurs du Crépuscule (24.09.2026, 10e seigneure, lore-quetes\soeurs-du-crepuscule.md) : leur salle tombée des
	-- Pics des Pins, la Clairière du Roi (Orion doit les reconnaître), le Défilé de la Hache (les Peaux-Vertes sur les
	-- Pics), la cachette de la harde (Ceithin-Har), le Chêne (la reine) ; les deux sœurs se répondent
	wh2_dlc16_wef_sisters_of_twilight = {
		{212.5, 98.6, conseil = "saison_prologue_soeurs_1", region = "wh_dlc05_wydrioth_tal_jul_finel"},
		{195.2, 74.7, conseil = "saison_prologue_soeurs_2", region = "wh_dlc05_talsyn_yn_ecryl_koiran"},
		{169.9, 241.1, conseil = "saison_prologue_soeurs_3", region = "wh_dlc05_grey_mountains_axe_bite_pass"},
		{78.6, 46.2, conseil = "saison_prologue_soeurs_4", region = "wh_dlc05_carcassonne_st_jacques"},
		{179.0, 79.4, conseil = "saison_prologue_soeurs_5", region = "wh_dlc05_oak_of_ages"},
		-- 004 (la Saison du Renouveau, au nom d'Ariel), au Chêne ; environ 90 s au total
		{179.0, 79.4, vol = 1, conseil = "wh2_dlc16.camp.sisters.intro.004", duree = 23.3}
	}
};
