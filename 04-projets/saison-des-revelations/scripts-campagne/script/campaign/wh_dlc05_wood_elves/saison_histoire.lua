-----------------------------------------------------------------------------------
--	L'histoire de la mini-campagne de WH1, portée dans WH3.
--
--	Source : wh_dlc05_wood_elves_mini.lua de WH1 (spécification : 05-journal/2026-09-22-gameplay-wh3/
--	histoire-wh1-specification.md, § 3). Un automate à six états (niveau de l'histoire 0 à 5), piloté par le niveau du
--	Chêne des Âges et par l'état de Morghur : gardiens des ruines, premiers raids au tour 6, invasions tous les 6 tours,
--	arrivée de Morghur, sa chute (blessé), son retour au Pic d'Argent, Morghur mortel et la bataille finale.
--
--	Décisions de Charles (23.09.2026) : le Chêne suit la chaîne de WH3 et la victoire est au niveau 5 (verrouillé par le
--	rituel de Renaissance des Chemins-racines) : les étapes passent des niveaux 2 / 3 / 4 de WH1 aux niveaux 3 / 4 / 5.
--	Pas de restrictions de commerce ni de Chasse sauvage de WH1 (celle de WH3 est chargée).
--
--	Portage vers l'API de WH3 (spécification § 4.1) : invasion_manager et random_army_manager (noms en minuscules),
--	cm:whose_turn_is_it_single(), cm:scroll_camera_from_current(corriger, durée, ...), progress_on_advice_finished
--	nommé, force_declare_war à quatre paramètres, kill_character à deux ; écouteurs et état sauvegardé à la place des
--	interventions de WH1 (dans WH1, couper le conseiller coupait l'histoire).
--
--	Morghur est cherché par son sous-type (WH1 prenait le chef de faction) : si sa harde meurt pendant qu'il est blessé
--	puis renaît, le chef de faction n'est plus lui ; il est alors recréé à la tête de l'armée de l'étape.
-----------------------------------------------------------------------------------
-- 23.09.2026 : écouteurs de début de tour sur FactionBeginTurnPhaseNormal (et non FactionTurnStart) : même
-- moment pour le joueur, et seul évènement de début de tour que le mode « l'IA joue tout » des essais
-- automatiques envoie (erreur 143) ; CA l'emploie aussi pour des factions humaines.

local ORION = "wh_dlc05_wef_wood_elves";
local DURTHU = "wh_dlc05_wef_argwylon";
local ELFES = {ORION, DURTHU};
local ELFES_TOUTES = {
	ORION, DURTHU, "wh_dlc05_wef_anmyr", "wh_dlc05_wef_arranoc", "wh_dlc05_wef_atylwyth", "wh_dlc05_wef_cavaroc",
	"wh_dlc05_wef_cythral", "wh_dlc05_wef_fyr_darric", "wh_dlc05_wef_modryn", "wh_dlc05_wef_tirsyth",
	"wh_dlc05_wef_torgovann", "wh_dlc05_wef_wydrioth",
	-- Drycha remplace la clairière de Cythral (spécification du 23.09.2026) ; absente, elle est ignorée comme les autres
	"wh2_dlc16_wef_drycha",
	-- les Sœurs du Crépuscule (24.09.2026) : la harde leur déclare la guerre comme aux autres Asrai
	"wh2_dlc16_wef_sisters_of_twilight"
};
local CHENE = "wh_dlc05_oak_of_ages";
local HARDE = "wh_dlc05_bst_morghur_herd";
SAISON_MISSION_FINALE = "wh_dlc05_qb_wef_mini_silver_spire";

-- Morghur (startpos : personnage 2140783911, chef de la harde, immortel ; noms de la table names)
local MORGHUR_SOUS_TYPE = "wh_dlc05_bst_morghur";
local MORGHUR_PRENOM = "names_name_2147352897";		-- Morghur
local MORGHUR_NOM = "names_name_2147357944";		-- the Shadowgave

-- Niveaux du Chêne (chaîne de WH3) qui déclenchent les étapes ; WH1 : 2, 3, 4.
local NIVEAU_ARRIVEE_MORGHUR = 3;
local NIVEAU_RETOUR_MORGHUR = 4;
local NIVEAU_MORGHUR_MORTEL = 5;

local ENTRETIEN_GRATUIT = "wh_main_bundle_military_upkeep_free_force";
local ENTRETIEN_GRATUIT_INDEMORALISABLE = "wh_main_bundle_military_upkeep_free_force_unbreakable_all";
local CAMERA_ARMEE = {14.768, 0.0, 12.0};			-- distance, cap, hauteur (WH1)


-- État de l'histoire, sauvegardé (WH1 : OAK_INVASION_LEVEL, OAK_INVASION_TURN, MORGHUR_DEAD, LAST_USED_BEASTMEN_SPAWN).
saison_histoire = {
	niveau = 0,
	tour_invasion = -1,
	morghur_mort = false,
	dernier_point = 1
};
local H = saison_histoire;


-----------------------------------------------------------------------------------
--	Outils
-----------------------------------------------------------------------------------

local function est_elfe_jouable(faction_key)
	return faction_key == ORION or faction_key == DURTHU;
end;


local function elfe_humain()
	for i = 1, #ELFES do
		local f = cm:get_faction(ELFES[i]);
		if f and not f:is_dead() and f:is_human() then
			return f;
		end;
	end;
	return nil;
end;


-- Niveau du Chêne des Âges (chaîne de WH3 : wh_dlc05_wef_oak_of_ages_1 à _5), 0 si aucun.
local function niveau_du_chene()
	local region = cm:get_region(CHENE);
	if not region or region:is_null_interface() then
		return 0;
	end;
	for niveau = 5, 1, -1 do
		if region:building_exists("wh_dlc05_wef_oak_of_ages_" .. niveau) then
			return niveau;
		end;
	end;
	return 0;
end;


local function chene_appartient_a(faction_key)
	local region = cm:get_region(CHENE);
	return region and not region:is_null_interface() and not region:is_abandoned()
		and region:owning_faction():name() == faction_key;
end;


-- Morghur (WH1 : Get_Morghur, Is_Morghur_Dead, Is_Morghur_Deployed) : le personnage de son sous-type dans la harde,
-- blessé ou non ; à défaut, le chef de faction, comme dans WH1. nil si la harde est morte.
local function morghur()
	local harde = cm:get_faction(HARDE);
	if not harde or harde:is_dead() then
		return nil;
	end;
	local persos = harde:character_list();
	for i = 0, persos:num_items() - 1 do
		local p = persos:item_at(i);
		if not p:is_null_interface() and p:character_subtype(MORGHUR_SOUS_TYPE) then
			return p;
		end;
	end;
	local chef = harde:faction_leader();
	if chef and not chef:is_null_interface() then
		return chef;
	end;
	return nil;
end;

local function morghur_mort()
	local chef = morghur();
	return chef == nil or chef:is_wounded();
end;

local function morghur_deploye()
	local chef = morghur();
	return chef ~= nil and not chef:is_wounded() and chef:has_military_force();
end;

local function interdire_a_l_ia(chef)
	if chef and not chef:is_null_interface() then
		cm:cai_disable_command_assignment_for_character("character_cqi:" .. chef:command_queue_index());
	end;
end;


-- Essai automatique (saison_en_essai_auto, required.lua) : ni bandes de cinéma, ni fondu, ni caméra, ni réplique ;
-- ce qui suit une réplique s'enchaîne tout de suite.
local function bandes(actif)
	if not saison_en_essai_auto() then
		CampaignUI.ToggleCinematicBorders(actif);
	end;
end;

local function fondu(vers, duree)
	if not saison_en_essai_auto() then
		cm:fade_scene(vers, duree);
	end;
end;

local function camera_glisser(corriger, duree, ...)
	if not saison_en_essai_auto() then
		cm:scroll_camera_from_current(corriger, duree, ...);
	end;
end;

local function camera_poser(x, y, d, b, h)
	if not saison_en_essai_auto() then
		cm:set_camera_position(x, y, d, b, h);
	end;
end;

-- Réplique du conseiller de l'histoire, selon la faction dont c'est le tour (WH1 : Play_Mini_Advice).
local function conseil(numero, sans_bouton)
	if saison_en_essai_auto() then
		return;
	end;
	local tour_de = cm:whose_turn_is_it_single();
	local qui = (tour_de and tour_de:name() == DURTHU) and "durthu" or "orion";
	local cle = "dlc05.mini.story." .. qui .. "." .. numero;
	if sans_bouton then
		cm:show_advice(cle);
	else
		cm:show_advice(cle, true);
	end;
end;

-- Enchaîne une action à la fin de la réplique en cours (WH1 : progress_on_advice_finished sans nom ; dans WH3, un
-- nom unique par processus).
local compteur_conseils = 0;
local function apres_conseil(f)
	if saison_en_essai_auto() then
		f();
		return;
	end;
	compteur_conseils = compteur_conseils + 1;
	cm:progress_on_advice_finished("saison_histoire_conseil_" .. compteur_conseils, f, 1, 5, false);
end;

local function camera_vers(personnage, duree)
	camera_glisser(false, duree,
		{personnage:display_position_x(), personnage:display_position_y(), CAMERA_ARMEE[1], CAMERA_ARMEE[2], CAMERA_ARMEE[3]});
end;


-- Chaque appel met une faction elfe de plus en guerre avec la harde : le joueur d'abord, puis la première
-- clairière qui ne l'est pas encore (WH1 : Beastmen_War_Declaration).
function saison_guerre_de_la_harde()
	local harde = cm:get_faction(HARDE);
	local joueur = elfe_humain();
	if not harde or harde:is_dead() or not joueur then
		return;
	end;
	-- la faction à qui déclarer la guerre : le joueur d'abord, puis la première clairière qui ne l'est pas encore
	local cible = nil;
	if joueur:at_war_with(harde) then
		for i = 1, #ELFES_TOUTES do
			local elfe = cm:get_faction(ELFES_TOUTES[i]);
			if elfe and not elfe:is_dead() and not elfe:at_war_with(harde) then
				cible = ELFES_TOUTES[i];
				break;
			end;
		end;
	else
		cible = joueur:name();
	end;
	-- toutes déjà en guerre : rien à déclarer, le fil d'évènements du joueur n'est pas coupé (audit de fluidité du
	-- 24.09.2026, T4 / S2 : la coupure d'une seconde à chaque tour de la harde pouvait cacher une déclaration de guerre)
	if not cible then
		return;
	end;
	cm:disable_event_feed_events(true, "wh_event_category_diplomacy", "", "");
	cm:force_declare_war(HARDE, cible, false, false);
	cm:callback(function() cm:disable_event_feed_events(false, "wh_event_category_diplomacy", "", "") end, 1);
end;


-----------------------------------------------------------------------------------
--	Points d'apparition et armées (déclarés à chaque chargement, comme dans WH1)
-----------------------------------------------------------------------------------

local POINTS_SUD = {
	{154, 102}, {162, 106},		-- milieu, milieu haut (Summersfall Fort)
	{160, 85}, {162, 78},		-- bas, bas dessous
	{176, 130}, {170, 128}		-- haut, haut dessous (Quenelles)
};
local POINTS_NORD = {
	{196, 255}, {198, 261},		-- milieu, milieu haut (Montlac)
	{189, 244}, {185, 241},		-- gauche, gauche dessous
	{243, 276}, {262, 261}		-- droite haut, droite (Grunere)
};

local function declarer_points()
	-- le côté du joueur passe en premier : le sud pour Orion, le nord pour Durthu
	local orion = cm:get_faction(ORION);
	local premier, second = POINTS_SUD, POINTS_NORD;
	if not (orion and orion:is_human()) then
		premier, second = POINTS_NORD, POINTS_SUD;
	end;
	for i = 1, 6 do
		invasion_manager:new_spawn_location("forest_" .. i, premier[i][1], premier[i][2]);
		invasion_manager:new_spawn_location("forest_" .. (i + 6), second[i][1], second[i][2]);
	end;
	invasion_manager:new_spawn_location("silver_spire_spawn", 181, 322);		-- affichage (121, 249)
	invasion_manager:new_spawn_location("beastmen_hide", 118, 60);
	invasion_manager:new_spawn_location("ruin_threllock", 266, 177);
	invasion_manager:new_spawn_location("ruin_tal_eth_ayr", 250, 97);
end;

local RESERVE = {
	{"wh_dlc03_bst_mon_chaos_spawn_0", 3}, {"wh_dlc03_bst_inf_razorgor_herd_0", 1}, {"wh_dlc03_bst_inf_cygor_0", 1},
	{"wh_dlc03_bst_inf_bestigor_herd_0", 1}, {"wh_dlc03_bst_inf_centigors_0", 1}, {"wh_dlc03_bst_inf_centigors_1", 1},
	{"wh_dlc03_bst_inf_centigors_2", 1}
};

local function declarer_forces()
	local function force(cle, obligatoires, reserve)
		random_army_manager:new_force(cle);
		for i = 1, #obligatoires do
			random_army_manager:add_mandatory_unit(cle, obligatoires[i][1], obligatoires[i][2]);
		end;
		for i = 1, #reserve do
			random_army_manager:add_unit(cle, reserve[i][1], reserve[i][2]);
		end;
	end;
	force("saison_harde_raid",
		{{"wh_dlc03_bst_inf_ungor_herd_1", 4}, {"wh_dlc03_bst_inf_gor_herd_0", 2}, {"wh_dlc03_bst_inf_ungor_raiders_0", 2},
		 {"wh_dlc03_bst_inf_chaos_warhounds_0", 2}},
		{{"wh_dlc03_bst_inf_ungor_herd_1", 2}, {"wh_dlc03_bst_inf_ungor_raiders_0", 1}});
	force("saison_harde_facile",
		{{"wh_dlc03_bst_inf_ungor_herd_1", 4}, {"wh_dlc03_bst_inf_gor_herd_0", 2}, {"wh_dlc03_bst_inf_gor_herd_1", 2},
		 {"wh_dlc03_bst_inf_ungor_raiders_0", 2}},
		RESERVE);
	force("saison_harde_normale",
		{{"wh_dlc03_bst_inf_gor_herd_0", 4}, {"wh_dlc03_bst_inf_gor_herd_1", 4}, {"wh_dlc03_bst_inf_ungor_raiders_0", 2}},
		RESERVE);
	force("saison_harde_forte",
		{{"wh_dlc03_bst_inf_gor_herd_0", 2}, {"wh_dlc03_bst_inf_gor_herd_1", 2}, {"wh_dlc03_bst_inf_bestigor_herd_0", 4},
		 {"wh_dlc03_bst_inf_ungor_raiders_0", 2}},
		RESERVE);
end;

-- Une armée tirée au sort (WH3 plafonne à 19 unités ; WH1 en demandait 20).
local function armee(cle_force, taille)
	return random_army_manager:generate_force(cle_force, taille, false);
end;


-- Point d'apparition libre (WH1 : Get_Beastmen_Spawn) : « ordonné » à partir du dernier point pris, ou tiré au hasard.
local function point_de_harde(aleatoire)
	local function libre(cle)
		local p = invasion_manager:parse_spawn_location(cle);
		return p and p.x and invasion_manager:is_valid_position(p.x, p.y);
	end;
	if aleatoire then
		for i = 1, 10 do
			local cle = "forest_" .. cm:random_number(12);
			if libre(cle) then
				return cle;
			end;
		end;
	else
		for i = H.dernier_point, 12 do
			if libre("forest_" .. i) then
				H.dernier_point = i + 1;
				return "forest_" .. i;
			end;
		end;
	end;
	return "beastmen_hide";
end;


-- Une invasion de la harde (clé unique ; si elle existe déjà, rien : cas d'un rechargement).
local function invasion(cle, force, point, cible_region, cible_faction, effet)
	if invasion_manager:get_invasion(cle) or not force then
		return nil;
	end;
	local inv = invasion_manager:new_invasion(cle, HARDE, force, point);
	if not inv then
		return nil;
	end;
	if cible_region then
		inv:set_target("REGION", cible_region, cible_faction);
	elseif cible_faction then
		inv:set_target("NONE", nil, cible_faction);
	end;
	if effet then
		inv:apply_effect(effet, -1);
	end;
	return inv;
end;


-- Entretien gratuit des armées de la harde rendues à l'IA (audit de fluidité du 24.09.2026, T19 ; décision de Charles,
-- 20 h 05) : nos invasions posent l'entretien gratuit sans limite (apply_effect(..., -1)). Une fois l'invasion finie
-- (cible atteinte, libérée, ou sans cible), l'armée reste à la harde AVEC l'entretien gratuit, pour toujours : des
-- dizaines d'armées de plus sur une longue partie, donc des tours d'IA plus longs. Au début de chaque tour de la harde,
-- une armée qui porte encore cet entretien et qui n'appartient plus à aucune invasion en cours le garde
-- ENTRETIEN_APRES_LIBERATION tours, puis le perd (effet remplacé par le même effet à durée limitée, une seule fois).
local ENTRETIEN_APRES_LIBERATION = 10;

local function generaux_des_invasions_en_cours()
	local cqis = {};
	for _, inv in pairs(invasion_manager.invasions or {}) do
		if is_function(inv.get_general) and is_function(inv.has_started) and inv:has_started() then
			local ok, chef = pcall(function() return inv:get_general() end);
			if ok and chef and not chef:is_null_interface() then
				cqis[chef:command_queue_index()] = true;
			end;
		end;
	end;
	return cqis;
end;

function saison_entretien_des_invasions()
	-- FactionBeginTurnPhaseNormal et non FactionTurnStart (24.09.2026, 23 h 20 : voir saison_foret.lua, Racines du monde)
	saison_ecouteur(
		"saison_entretien_des_invasions",
		"FactionBeginTurnPhaseNormal",
		function(context) return context:faction():name() == HARDE end,
		function(context)
			local en_cours = generaux_des_invasions_en_cours();
			local deja = cm:get_saved_value("saison_entretien_limite") or {};
			local forces = context:faction():military_force_list();
			local n = 0;
			for i = 0, forces:num_items() - 1 do
				local mf = forces:item_at(i);
				local cqi = mf:command_queue_index();
				if mf:has_effect_bundle(ENTRETIEN_GRATUIT) and not deja[cqi] and mf:has_general()
					and not en_cours[mf:general_character():command_queue_index()] then
					cm:remove_effect_bundle_from_force(ENTRETIEN_GRATUIT, cqi);
					cm:apply_effect_bundle_to_force(ENTRETIEN_GRATUIT, cqi, ENTRETIEN_APRES_LIBERATION);
					deja[cqi] = true;
					n = n + 1;
				end;
			end;
			if n > 0 then
				cm:set_saved_value("saison_entretien_limite", deja);
				out("La Saison des Revelations : " .. n .. " armee(s) de la harde rendue(s) a l'IA : entretien gratuit limite a "
					.. ENTRETIEN_APRES_LIBERATION .. " tours");
			end;
		end,
		true
	);
end;


local function liberer(cle)
	local inv = invasion_manager:get_invasion(cle);
	if inv then
		inv:should_stop_at_end(false);
		inv:remove_target();
	end;
end;


-- Morghur prêt à mener une armée : le personnage s'il est là et valide ; true s'il faut le recréer (harde renée sans
-- lui) ; nil s'il est blessé, ou si la harde est morte (un raid à la cachette la relance, comme dans WH1) : l'étape
-- réessaiera au tour suivant.
local function morghur_pret(tour)
	local harde = cm:get_faction(HARDE);
	if not harde then
		return nil;
	end;
	if harde:is_dead() then
		-- comme les scripts de CA de 2025 avant une invasion (absente de la doc de l'interface : protégée)
		local ok_reveil, err_reveil = pcall(function() cm:awaken_faction_from_death(harde) end);
		if not ok_reveil then
			out("La Saison des Revelations : reveil de la harde impossible : " .. tostring(err_reveil));
		end;
		local inv = invasion("morghur_revival_" .. tour, armee("saison_harde_raid", 10), "beastmen_hide");
		if inv then
			inv:start_invasion();
		end;
		return nil;
	end;
	local chef = morghur();
	if chef == nil or not chef:character_subtype(MORGHUR_SOUS_TYPE) then
		return true;
	end;
	if chef:is_wounded() then
		return nil;
	end;
	return chef;
end;

-- Morghur à la tête de l'armée de l'invasion : le personnage existant (WH1), ou recréé, immortel, chef de la harde.
local function confier_a_morghur(inv, chef)
	if chef == true then
		inv:create_general(true, MORGHUR_SOUS_TYPE, MORGHUR_PRENOM, "", MORGHUR_NOM, "");
		inv:set_general_immortal(true);
	else
		inv:assign_general(chef);
	end;
end;


local function reveler_le_pic()
	for i = 1, #ELFES do
		cm:make_region_visible_in_shroud(ELFES[i], "wh_dlc05_montfort_montfort");
		cm:make_region_visible_in_shroud(ELFES[i], "wh_dlc05_grey_mountains_gragrut_pass");
	end;
end;


-----------------------------------------------------------------------------------
--	Mise en place (partie neuve)
-----------------------------------------------------------------------------------

local GARDE = "wh_dlc03_bst_inf_centigors_0,wh_dlc03_bst_inf_ungor_herd_1,wh_dlc03_bst_inf_ungor_herd_1,"
	.. "wh_dlc03_bst_inf_ungor_raiders_0,wh_dlc03_bst_inf_ungor_raiders_0";

local function mise_en_place()
	-- Morghur est retiré (blessé : il est immortel) et son commandement interdit à l'IA. Les gardiens des ruines
	-- apparaissent d'abord : ce sont eux qui gardent la harde en vie (WH1 le tuait avant ; spécification § 6.5 n° 5).
	local function retirer_morghur()
		local chef = morghur();
		if chef and not chef:is_wounded() then
			interdire_a_l_ia(chef);
			cm:kill_character(chef:command_queue_index(), true);
		end;
	end;

	local garde_1 = invasion("ruin_guard_1", GARDE, "ruin_threllock", nil, DURTHU, ENTRETIEN_GRATUIT);
	local garde_2 = invasion("ruin_guard_2", GARDE, "ruin_tal_eth_ayr", nil, ORION, ENTRETIEN_GRATUIT);
	if garde_1 then
		garde_1:should_stop_at_end(true);
		garde_1:start_invasion(function() saison_sur("retrait de Morghur", retirer_morghur) end);
	end;
	if garde_2 then
		garde_2:should_stop_at_end(true);
		garde_2:start_invasion();
	end;
	if not garde_1 then
		retirer_morghur();
	end;
end;


-----------------------------------------------------------------------------------
--	Étape 1 (tour 6) : deux raids sur le Chêne
-----------------------------------------------------------------------------------

local function etape_1(cible)
	out("La Saison des Revelations : etape 1, premiers raids");
	H.niveau = 1;
	H.tour_invasion = cm:model():turn_number();

	local raid_1 = invasion("invasion_beastmen_first_invasion_1", armee("saison_harde_raid", 10), point_de_harde(false),
		CHENE, cible, ENTRETIEN_GRATUIT);
	if raid_1 then
		raid_1:start_invasion(function(inv)
			local chef = inv:get_general();
			if not chef:is_null_interface() then
				if chef:has_region() then
					cm:make_region_visible_in_shroud(cible, chef:region():name());
				end;
				camera_vers(chef, 6);
			end;
			saison_guerre_de_la_harde();
			bandes(true);
			conseil("007", true);
			apres_conseil(function()
				conseil("008", true);
				apres_conseil(function()
					conseil("009");
					apres_conseil(function() bandes(false) end);
				end);
			end);
		end);
	end;

	local raid_2 = invasion("invasion_beastmen_first_invasion_2", armee("saison_harde_raid", 10), point_de_harde(false),
		CHENE, cible, ENTRETIEN_GRATUIT);
	if raid_2 then
		raid_2:start_invasion(function(inv)
			local chef = inv:get_general();
			if not chef:is_null_interface() and chef:has_region() then
				cm:make_region_visible_in_shroud(cible, chef:region():name());
			end;
		end);
	end;
end;


-----------------------------------------------------------------------------------
--	Étape 2 (Chêne au niveau 3) : Morghur arrive avec quatre armées
-----------------------------------------------------------------------------------

local function etape_2(cible, tour)
	local chef_morghur = morghur_pret(tour);
	if not chef_morghur then
		return;
	end;
	out("La Saison des Revelations : etape 2, Morghur arrive");
	H.niveau = 2;

	local armee_morghur = invasion("invasion_morghur_arrives_1", armee("saison_harde_forte", 20), point_de_harde(false),
		CHENE, cible, ENTRETIEN_GRATUIT);
	if armee_morghur then
		confier_a_morghur(armee_morghur, chef_morghur);
		armee_morghur:start_invasion(function(inv)
			local chef = inv:get_general();
			if not chef:is_null_interface() then
				interdire_a_l_ia(chef);
				if chef:has_region() then
					cm:make_region_visible_in_shroud(cible, chef:region():name());
				end;
				camera_vers(chef, 6);
			end;
			saison_guerre_de_la_harde();
			bandes(true);
			conseil("010", true);
			apres_conseil(function()
				conseil("011");
				apres_conseil(function() bandes(false) end);
			end);
		end);
	end;

	local suite = {{"invasion_morghur_arrives_2", "saison_harde_facile"}, {"invasion_morghur_arrives_3", "saison_harde_normale"},
		{"invasion_morghur_arrives_4", "saison_harde_facile"}};
	for i = 1, #suite do
		local inv = invasion(suite[i][1], armee(suite[i][2], 20), point_de_harde(false), CHENE, cible, ENTRETIEN_GRATUIT);
		if inv then
			inv:start_invasion(function(x)
				local chef = x:get_general();
				if not chef:is_null_interface() and chef:has_region() then
					cm:make_region_visible_in_shroud(cible, chef:region():name());
				end;
			end);
		end;
	end;
end;


-----------------------------------------------------------------------------------
--	Étape 3 : Morghur est tombé (blessé) ; les invasions périodiques s'arrêtent
-----------------------------------------------------------------------------------

local function etape_3()
	out("La Saison des Revelations : etape 3, Morghur est tombe");
	H.niveau = 3;
	H.tour_invasion = -1;
	-- les Échos d'Orion et de Durthu s'ouvrent aussi à la chute de Morghur (saison_chroniques.lua ; bêta, 25.09.2026 :
	-- étude du rythme, creux des tours 35 à 50 entre la chute et le Chêne au niveau 4)
	core:trigger_event("ScriptEventSaisonMorghurTombe");
	conseil("012", true);
	apres_conseil(function() conseil("013") end);
end;


-----------------------------------------------------------------------------------
--	Étape 4 (Chêne au niveau 4) : Morghur revient et garde le Pic d'Argent ; il revient tant que le Chêne n'est pas au
--	niveau 5
-----------------------------------------------------------------------------------

local function etape_4(retour)
	local tour = cm:model():turn_number();
	local chef_morghur = morghur_pret(tour);
	if not chef_morghur then
		return;
	end;
	local inv = invasion("invasion_morghur_returns_" .. tour, armee("saison_harde_forte", 20), "silver_spire_spawn", nil, nil,
		ENTRETIEN_GRATUIT_INDEMORALISABLE);
	if not inv then
		return;
	end;
	out("La Saison des Revelations : etape 4, Morghur au Pic d'Argent" .. (retour and " (retour)" or ""));
	H.niveau = 4;
	H.tour_invasion = tour;
	confier_a_morghur(inv, chef_morghur);
	inv:should_stop_at_end(true);
	reveler_le_pic();

	if not retour then
		inv:start_invasion(function(x)
			local chef = x:get_general();
			-- le cqi, pas l'interface, pour après les répliques (plusieurs secondes plus tard : une interface gardée d'un
			-- tick à l'autre peut être périmée ; audit de fluidité du 24.09.2026, T7 / S6)
			local cqi = (not chef:is_null_interface()) and chef:command_queue_index() or nil;
			interdire_a_l_ia(chef);
			saison_guerre_de_la_harde();
			if not chef:is_null_interface() then
				camera_vers(chef, 6);
			end;
			bandes(true);
			conseil("014", true);
			apres_conseil(function()
				cm:callback(function() camera_glisser(false, 12, {125.15, 262.59, 10.49, 0.24, 8.0}) end, 9);
				conseil("015", true);
				apres_conseil(function()
					local c = cqi and cm:get_character_by_cqi(cqi);
					if c and not c:is_null_interface() then
						camera_vers(c, 8);
					end;
					conseil("016");
					apres_conseil(function() bandes(false) end);
				end);
			end);
		end);
	else
		inv:start_invasion(function(x)
			local chef = x:get_general();
			interdire_a_l_ia(chef);
			saison_guerre_de_la_harde();
			cm:show_advice("dlc05.mini.story.all.001", true);
			if not chef:is_null_interface() then
				camera_vers(chef, 6);
			end;
		end);
	end;
end;


-----------------------------------------------------------------------------------
--	Étape 5 (Chêne au niveau 5) : Morghur devient mortel ; la bataille finale du Pic d'Argent est lancée
-----------------------------------------------------------------------------------

local function etape_5(cible)
	out("La Saison des Revelations : etape 5, Morghur devient mortel");
	H.niveau = 5;

	-- le raid « cachette » garde la harde en vie ; Morghur est retiré de la carte à son apparition
	local cache = invasion("morghur_kill_hider", armee("saison_harde_raid", 10), "beastmen_hide");
	if cache then
		cache:start_invasion(function()
			local chef = morghur();
			if chef and chef:character_subtype(MORGHUR_SOUS_TYPE) and not chef:is_wounded() then
				cm:kill_character(chef:command_queue_index(), true);
			end;
		end);
	end;
	reveler_le_pic();

	fondu(0, 1);
	cm:trigger_mission(cible, SAISON_MISSION_FINALE, true);
	bandes(true);
	cm:callback(function() camera_poser(180.177, 85.353, 14.769, 0.0, 12.0) end, 1);
	cm:callback(
		function()
			conseil("017");
			camera_poser(180.177, 85.353, 14.769, 0.0, 12.0);
			fondu(1, 1);
		end,
		1.5
	);
	cm:callback(
		function()
			camera_glisser(false, 17, {121, 249, 14.768, 0.0, 12.0});
			apres_conseil(function() bandes(false) end);
		end,
		3
	);
end;


-----------------------------------------------------------------------------------
--	Invasion périodique : tous les 6 tours, une harde de 11 à 19 unités ; une chance sur deux de viser le Chêne
-----------------------------------------------------------------------------------

local function invasion_periodique(cible, tour)
	H.tour_invasion = tour;
	local point = point_de_harde(true);
	local inv = invasion("beastmen_tree_attack_" .. tour .. "_" .. point, armee("saison_harde_normale", 10 + cm:random_number(10)),
		point, nil, nil, ENTRETIEN_GRATUIT);
	if inv then
		if cm:random_number(100) >= 50 then
			inv:set_target("REGION", CHENE, cible);
		end;
		inv:start_invasion(function() saison_guerre_de_la_harde() end);
	end;
end;


-----------------------------------------------------------------------------------
--	La Saison vue de Bretonnie (Alberic ou la Fée Enchanteresse joués, 23.09.2026) : pas d'histoire des elfes, Morghur
--	reste à la tête de sa harde (IA) ; tous les 6 tours à partir du tour 6, une harde sort des lisières d'Athel Loren et
--	marche sur une région du joueur, plus forte à mesure que la Saison avance (8 unités, puis 2 de plus tous les 6 tours,
--	19 au plus).
-----------------------------------------------------------------------------------

local BRETONS = {"wh_main_brt_bordeleaux", "wh_main_brt_carcassonne"};

function breton_humain()
	for i = 1, #BRETONS do
		local f = cm:get_faction(BRETONS[i]);
		if f and not f:is_dead() and f:is_human() then
			return f;
		end;
	end;
	return nil;
end;

local function raid_breton(joueur, tour)
	local harde = cm:get_faction(HARDE);
	local regions = joueur:region_list();
	if not harde or regions:is_empty() then
		return;
	end;
	-- harde morte (bilan d'équilibrage du 25.09.2026 : 5 parties longues sur 6 avant le tour 30) : les raids cessaient
	-- avec elle, et Alberic ou la Fée n'avaient plus de menace. Elle est réveillée comme dans l'histoire des elfes
	-- (morghur_pret, plus haut) ; l'invasion ci-dessous lui rend une armée. Les raids cessent toujours à l'étape de
	-- Morghur de la chronique (saison_saison_bretonne).
	if harde:is_dead() then
		local ok_reveil, err_reveil = pcall(function() cm:awaken_faction_from_death(harde) end);
		if not ok_reveil then
			out("La Saison des Revelations : reveil de la harde impossible (raid breton) : " .. tostring(err_reveil));
		end;
		harde = cm:get_faction(HARDE);
	end;
	local cible = regions:item_at(cm:random_number(regions:num_items()) - 1):name();
	if not harde:is_dead() and not harde:at_war_with(joueur) then
		cm:force_declare_war(HARDE, joueur:name(), false, false);
	end;
	local taille = math.min(19, 8 + 2 * math.floor(tour / 6));
	-- le nom, pas l'interface, dans le rappel de l'invasion (audit de fluidité du 24.09.2026, T8 / S6)
	local nom_joueur = joueur:name();
	local inv = invasion("saison_raid_breton_" .. tour, armee("saison_harde_normale", taille), point_de_harde(true), cible,
		nom_joueur, ENTRETIEN_GRATUIT);
	if not inv then
		return;
	end;
	inv:start_invasion(function(x)
		local chef = x:get_general();
		if not chef:is_null_interface() and chef:has_region() then
			cm:make_region_visible_in_shroud(nom_joueur, chef:region():name());
		end;
		cm:show_message_event(nom_joueur, "saison_des_revelations_raid_titre", "saison_des_revelations_raid_primaire",
			"saison_des_revelations_raid_secondaire", true, 1803);
	end);
end;

-- Morghur revient (bêta, 25.09.2026 ; ligne de Charles : lore d'abord, plus dur, grimdark). Lore : Morghur ne meurt pas,
-- il renaît ailleurs et sa harde avec lui (Wood Elves 8e ; notre prologue le dit : « quand on l'abat, il revient
-- ailleurs, et sa harde avec lui »). Aux essais, la harde de l'IA mourait avant le tour 30 dans 5 parties sur 6, et la
-- menace des Hommes-bêtes disparaissait pour le reste de la partie. Parties SANS l'histoire des elfes (qui a son propre
-- retour, morghur_pret) et sans Morghur joué : RETOUR_HARDE tours après sa mort, la harde est réveillée et une armée
-- sort de sa cachette, de la taille des raids bretons (8 unités, 2 de plus tous les 6 tours, 19 au plus).
local RETOUR_HARDE = 8;

local function retour_de_morghur()
	local harde = cm:get_faction(HARDE);
	if not harde or harde:is_human() then
		return;
	end;
	local tour = cm:model():turn_number();
	if not harde:is_dead() then
		cm:set_saved_value("saison_harde_morte_depuis", false);
		return;
	end;
	local depuis = cm:get_saved_value("saison_harde_morte_depuis");
	if not depuis then
		cm:set_saved_value("saison_harde_morte_depuis", tour);
		return;
	end;
	if tour - depuis < RETOUR_HARDE then
		return;
	end;
	local ok_reveil, err_reveil = pcall(function() cm:awaken_faction_from_death(harde) end);
	if not ok_reveil then
		out("La Saison des Revelations : reveil de la harde impossible (retour de Morghur) : " .. tostring(err_reveil));
	end;
	local taille = math.min(19, 8 + 2 * math.floor(tour / 6));
	local inv = invasion("saison_retour_de_morghur_" .. tour, armee("saison_harde_normale", taille), point_de_harde(true),
		nil, nil, ENTRETIEN_GRATUIT);
	if inv then
		inv:start_invasion();
		cm:set_saved_value("saison_harde_morte_depuis", false);
		out("La Saison des Revelations : Morghur revient, sa harde avec lui (" .. taille .. " unites, tour " .. tour .. ")");
	end;
end;

function saison_retour_de_morghur_demarrer()
	saison_ecouteur("saison_retour_de_morghur", "WorldStartRound", true,
		function() saison_sur("histoire : retour de Morghur", retour_de_morghur) end, true);
end;


function saison_saison_bretonne()
	saison_ecouteur(
		"saison_bretonne_debut_de_tour",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local f = context:faction();
			return f:is_human() and (f:name() == BRETONS[1] or f:name() == BRETONS[2]);
		end,
		function(context)
			local tour = cm:model():turn_number();
			-- les raids cessent quand Morghur est tombé (étape 4 de la chronique d'Albéric ou de la Fée passée,
			-- saison_chroniques.lua) : place aux Échos (audit de gameplay, point 9)
			local etape = cm:get_saved_value("saison_chronique_" .. context:faction():name()) or 0;
			if etape <= 4 and tour >= 6 and (tour - 6) % 6 == 0 then
				saison_sur("histoire : raid breton", raid_breton, context:faction(), tour);
			end;
		end,
		true
	);
end;


-----------------------------------------------------------------------------------
--	Conseil du Chêne (WH1 : dès que l'ambre suffisait à le faire grandir, 6 puis 9). Dans WH3 le Chêne coûte de l'or
--	(building_levels : niveaux 2, 3, 4 à 2 500, 5 000, 10 000) : le conseil vient quand le trésor suffit au niveau
--	suivant, une fois par niveau. Le niveau 5 passe par le rituel de Renaissance, que « Comment jouer » et la victoire
--	annoncent.
-----------------------------------------------------------------------------------

local COUT_NIVEAU_CHENE = {[2] = 2500, [3] = 5000, [4] = 10000};

local function conseil_du_chene(faction, chene)
	local suivant = chene + 1;
	local cout = COUT_NIVEAU_CHENE[suivant];
	local deja = "saison_conseil_chene_" .. suivant;
	if cout and faction:treasury() >= cout and not cm:get_saved_value(deja) then
		cm:set_saved_value(deja, true);
		cm:show_advice("dlc05.camp.advice.wef.oak_of_ages.001", true);
	end;
end;


-----------------------------------------------------------------------------------
--	Début de tour
-----------------------------------------------------------------------------------

local function debut_de_tour(context)
	local faction = context:faction();
	local nom = faction:name();

	-- la harde : commandement de Morghur toujours interdit à l'IA, et une faction elfe de plus en guerre
	if nom == HARDE then
		-- victoire au Pic d'Argent (saison_victoire_finale) : ses armées sont détruites ici, au début de SON tour, et non
		-- pendant le tour du joueur (revue de la bêta, I2 ; règle du plantage de Durthu, 23.09.2026)
		if cm:get_saved_value("saison_harde_a_detruire") then
			cm:set_saved_value("saison_harde_a_detruire", false);
			local forces = faction:military_force_list();
			for i = 0, forces:num_items() - 1 do
				local force = forces:item_at(i);
				if not force:is_null_interface() and force:has_general() then
					cm:kill_character(force:general_character():command_queue_index(), true);
				end;
			end;
			out("La Saison des Revelations : harde detruite apres la victoire du Pic d'Argent (" .. forces:num_items() .. " armee(s))");
			return;
		end;
		-- seulement Morghur lui-même : morghur() rend le chef de faction à défaut (revue de la bêta, M7)
		local m = morghur();
		if m and m:character_subtype(MORGHUR_SOUS_TYPE) then
			interdire_a_l_ia(m);
		end;
		saison_guerre_de_la_harde();
		return;
	end;

	if not est_elfe_jouable(nom) or not faction:is_human() then
		return;
	end;

	H.dernier_point = 1;
	local tour = cm:model():turn_number();
	local chene = niveau_du_chene();
	local niveau_avant = H.niveau;
	local parle = false;			-- une réplique ce tour-ci : pas de conseil du Chêne par-dessus

	-- ce qui n'arrive que si le joueur tient le Chêne (WH1 : WoodElves_FactionTurnStart)
	if chene_appartient_a(nom) then
		if tour == 6 then
			liberer("ruin_guard_1");
			liberer("ruin_guard_2");
		elseif tour == 10 then
			liberer("invasion_beastmen_first_invasion_2");
		elseif tour == 15 or tour == 45 then
			cm:show_advice("dlc05.camp.advice.wef.invasion.after.x.turns.001", true);
			parle = true;
		elseif tour == 30 or tour == 60 then
			cm:show_advice("dlc05.camp.advice.wef.invasion.after.x.turns.002", true);
			parle = true;
		end;

		if tour == 3 then
			conseil("005", true);
			apres_conseil(function() conseil("006") end);
			parle = true;
		end;

		if chene < NIVEAU_MORGHUR_MORTEL and H.niveau == 4 and not morghur_deploye() then
			etape_4(true);
			parle = true;
		end;

		if H.tour_invasion > -1 and tour == H.tour_invasion + 6 then
			invasion_periodique(nom, tour);
		end;
	end;

	-- les cinq étapes (WH1 : interventions), une par tour au plus
	if H.niveau == 0 and tour >= 6 then
		etape_1(nom);
	elseif H.niveau == 1 and chene >= NIVEAU_ARRIVEE_MORGHUR then
		etape_2(nom, tour);
	elseif H.niveau == 2 and (morghur_mort() or H.morghur_mort) then
		etape_3();
	elseif H.niveau == 3 and chene >= NIVEAU_RETOUR_MORGHUR then
		etape_4(false);
	elseif H.niveau == 4 and chene >= NIVEAU_MORGHUR_MORTEL then
		etape_5(nom);
	end;

	if not parle and H.niveau == niveau_avant and chene_appartient_a(nom) then
		conseil_du_chene(faction, chene);
	end;
end;


-----------------------------------------------------------------------------------
--	Démarrage (appelé par saison_start.lua à chaque chargement, sous saison_sur)
-----------------------------------------------------------------------------------

function saison_histoire_demarrer()
	if cm:is_multiplayer() then
		return;				-- l'histoire de WH1 est solo seulement
	end;

	declarer_points();
	declarer_forces();

	-- la harde ne fait jamais la paix avec les Asrai (après apply_default_diplomacy, qui l'autorise aux hommes-bêtes),
	-- sauf si c'est le joueur. 24.09.2026 (enquête d'équilibrage C2.2) : l'interdit valait pour « all », et la Gasconnie de
	-- l'IA restait en guerre perpétuelle contre une horde immortelle ; dans l'histoire de WH1, la harde n'est l'ennemie
	-- que des Asrai. Les raids de la Saison vue de Bretonnie déclarent eux-mêmes leur guerre au Breton joué.
	local harde = cm:get_faction(HARDE);
	if not (harde and harde:is_human()) then
		cm:force_diplomacy("faction:" .. HARDE, "culture:wh_dlc05_wef_wood_elves", "peace", false, false, true);
		cm:force_diplomacy("faction:" .. HARDE, "all", "war", true, true, true);
	end;

	-- Aucun elfe joué (enquête d'équilibrage C3.4) : la harde n'entrait jamais en guerre contre Orion et Durthu de l'IA,
	-- qui n'avaient alors aucun ennemi. Partie neuve : la harde leur déclare la guerre (l'histoire de WH1 les oppose).
	if cm:is_new_game() and not elfe_humain() and harde and not harde:is_dead() and not harde:is_human() then
		for _, cle in ipairs({ORION, DURTHU}) do
			local f = cm:get_faction(cle);
			if f and not f:is_dead() and not f:is_human() and not harde:at_war_with(f) then
				cm:force_declare_war(HARDE, cle, false, false);
				out("La Saison des Revelations : la harde en guerre contre " .. cle .. " (IA)");
			end;
		end;
	end;

	-- L'histoire de WH1 est celle d'Orion et de Durthu (23.09.2026) : Alberic ou la Fée jouent la Saison vue de
	-- Bretonnie ; Morghur joué n'a pas d'histoire scriptée, sa victoire en tient lieu (saison_victoire.lua).
	if not elfe_humain() then
		if breton_humain() then
			saison_saison_bretonne();
		end;
		saison_retour_de_morghur_demarrer();
		return;
	end;

	if cm:is_new_game() then
		mise_en_place();
	end;

	-- seules la harde et l'elfe joué intéressent debut_de_tour (audit de fluidité du 24.09.2026, T5 / S3 : plus de pcall
	-- pour chaque faction de la carte à chaque tour) ; debut_de_tour garde son test is_human()
	core:add_listener(
		"saison_histoire_debut_de_tour",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local nom = context:faction():name();
			return nom == HARDE or est_elfe_jouable(nom);
		end,
		function(context) saison_sur("histoire : debut de tour", debut_de_tour, context) end,
		true
	);

	-- WH1 ne le faisait que pour Orion : ici pour l'elfe joué, quel qu'il soit
	saison_ecouteur(
		"saison_histoire_fin_de_tour",
		"FactionAboutToEndTurn",
		function(context)
			local faction = context:faction();
			return est_elfe_jouable(faction:name()) and faction:is_human() and H.niveau == 2;
		end,
		function() H.morghur_mort = morghur_mort() end,
		true
	);

	saison_ecouteur(
		"saison_histoire_bataille_finale",
		"MissionSucceeded",
		function(context)
			return context:mission():mission_record_key() == SAISON_MISSION_FINALE;
		end,
		function(context)
			saison_sur("histoire : victoire au Pic d'Argent", saison_victoire_finale, context:faction():name());
		end,
		true
	);
end;


-- Bataille finale gagnée : fin des invasions, la harde détruite au début de son tour (debut_de_tour ; revue de la
-- bêta, I2 : jamais pendant le tour du joueur), cinématique de fin (saison_victoire.lua).
function saison_victoire_finale(faction_key)
	H.tour_invasion = -1;
	local harde = cm:get_faction(HARDE);
	if harde and not harde:is_dead() then
		cm:set_saved_value("saison_harde_a_detruire", true);
	end;
	saison_cinematique_de_fin(faction_key);
end;


-----------------------------------------------------------------------------------
--	Sauvegarde
-----------------------------------------------------------------------------------

cm:add_saving_game_callback(
	function(context)
		cm:save_named_value("saison_histoire_niveau", H.niveau, context);
		cm:save_named_value("saison_histoire_tour_invasion", H.tour_invasion, context);
		cm:save_named_value("saison_histoire_morghur_mort", H.morghur_mort, context);
		cm:save_named_value("saison_histoire_dernier_point", H.dernier_point, context);
	end
);

cm:add_loading_game_callback(
	function(context)
		H.niveau = cm:load_named_value("saison_histoire_niveau", 0, context);
		H.tour_invasion = cm:load_named_value("saison_histoire_tour_invasion", -1, context);
		H.morghur_mort = cm:load_named_value("saison_histoire_morghur_mort", false, context);
		H.dernier_point = cm:load_named_value("saison_histoire_dernier_point", 1, context);
	end
);
