-----------------------------------------------------------------------------------
--	Nos données dans les tables Lua de CA.
--
--	CA range ses données propres à chaque campagne dans des tables globales, indexées par le nom de campagne
--	(cm:get_campaign_name() = nom du dossier, pour nous "wh_dlc05_wood_elves"). Sans entrée pour nous, plusieurs
--	systèmes échouent à la partie neuve (relevé du 23.09.2026, scripts-mecaniques-wh3.md, § 3 et § 5.4). On ajoute nos
--	entrées ici, après le chargement des fichiers de CA et avant leur démarrage (saison_start.lua).
-----------------------------------------------------------------------------------

local CAMPAGNE = "wh_dlc05_wood_elves";

-- Nains (Karak Ziflin) : rancunes de départ. Sans cette entrée, grudge_cycle:setup() parcourt
-- starting_grudges[campagne] = nil et échoue à la partie neuve. Cibles : les deux tribus des Montagnes grises et
-- Mousillon, toutes présentes sur notre carte (valeurs à l'échelle de celles des Empires).
-- 23.09.2026 (spécification Drycha / Kemmler / Grom) : Grom la Panse remplace les Teef Snatchaz au Massif d'Orquemont
-- et Kemmler prend le Poste de la Pierre Noire, forteresse de Karak Ziflin. Une faction absente de la partie est
-- ignorée sans erreur (cm:get_faction rend false, assign_grudges ne fait rien) : anciennes et nouvelles clés coexistent
-- tant que le startpos n'a pas changé.
if grudge_cycle and grudge_cycle.starting_grudges then
	grudge_cycle.starting_grudges[CAMPAGNE] = {
		wh_main_grn_skullsmasherz = 75,
		wh_main_grn_teef_snatchaz = 75,
		wh2_dlc15_grn_broken_axe = 75,
		wh2_dlc11_vmp_the_barrow_legion = 100,
		wh_main_vmp_mousillon = 50
	};
end;

-- Missions de rancunes de départ des seigneurs nains légendaires (seulement si un nain est joué) : aucune ici.
if starting_grudge_missions and starting_grudge_missions.faction_missions then
	starting_grudge_missions.faction_missions[CAMPAGNE] = starting_grudge_missions.faction_missions[CAMPAGNE] or {};
end;

-- Colonies de culture naine de notre carte (le Livre des rancunes les lit par campagne).
if book_of_grudges and book_of_grudges.dwarf_culture_regions then
	book_of_grudges.dwarf_culture_regions[CAMPAGNE] = {
		"wh_dlc05_grey_mountains_2_karak_ziflin",
		"wh_dlc05_grey_mountains_2_karak_tzor",
		"wh_dlc05_grey_mountains_2_blackstone_post"
	};
end;

-- Comtes vampires, refonte de la 9.0 (24.09.2026 ; audit 05-journal\2026-09-24-vampires-9.0\audit-systemes-vampires-9.0.md,
-- § 1.1 et § 1.6). L'ancien bloc des baisers de sang (wh2_vampire_bloodlines, retiré par la 9.0) n'a plus d'objet.
--
-- Repaires : le module de CA les répartit à la première image, au chargement, avec les données des Empires (régions
-- et factions absentes de notre carte : aucun repaire créé, techniques de Kemmler bloquées). Nos deux vampires, une
-- seule réserve par faction à distance illimitée (une réserve vide arrêterait toute la répartition), Athel Loren
-- exclue comme les provinces forestières aux Empires. Premier repaire de Kemmler : le Château de Bastonne, exact
-- équivalent de celui de CA aux Empires (wh3_main_combi_region_castle_bastonne). Celui du Duc écarlate (décision de
-- Charles, 24.09.2026, 18 h 25) : Derrevin Libre, dans l'Aquitaine de son ancien duché, où sa chronique place déjà
-- les ruines du Crac de Sang, sur la colline qui domine la Morceaux et la forêt de Châlons (The Red Duke, C.L. Werner,
-- ch. 6) ; c'est aussi la région de l'étape 1 de sa chronique. Le Champ de Ceren et le tombeau de Galand : saison_duc.lua.
-- Nombres de repaires : choix de conception, à régler en jeu.
if vampire_lairs and vampire_lairs.lair_spawning_data then
	local d = vampire_lairs.lair_spawning_data;
	-- 25.09.2026 (audit du Duc face à la 9.0 ; Charles : « 3 repaires ») : CA ne met qu'un repaire par province
	-- (HAS_LAIR) et écarte les provinces forestières, les provinces d'origine, celles des premiers repaires et les régions
	-- déjà vues du joueur ; il restait 4 provinces, et Kemmler, servi le premier avec 3 repaires, n'en laissait qu'une au
	-- Duc (2 repaires en tout, essai du 24.09 à 18 h 57). Désormais : 2 repaires de plus chacun (3 en tout avec le premier),
	-- et le Duc servi le premier.
	d.factions = {
		{key = "wh_main_vmp_mousillon", first_lair = "wh_dlc05_aquitaine_derrevin_libre",
			lair_pools = {{key = "random", distance = 9999999, lair_count = 2}}},
		{key = "wh2_dlc11_vmp_the_barrow_legion", first_lair = "wh_dlc05_bastonne_castle_bastonne",
			lair_pools = {{key = "random", distance = 9999999, lair_count = 2}}}
	};
	d.ignore_provinces_and_regions = {};
	for _, p in ipairs({"anmyr", "argwylon", "arranoc", "atylwyth", "cavaroc", "cythral", "fyr_darric", "modryn",
		"oak_of_ages", "talsyn", "tirsyth", "torgovann", "wydrioth"}) do
		d.ignore_provinces_and_regions["wh_dlc05_" .. p] = "IGNORE";
	end;
	-- journal détaillé de la répartition (verbose_logging) : laissé à false, valeur de CA (audit de fluidité du 24.09.2026,
	-- T18 / S14 ; les premiers essais sont faits)
end;

-- discover_random_lair rend nil quand tous les repaires sont découverts (6 à 8 sur notre carte) et la technologie de CA
-- passe ce nil à occupy_lair (wh3_dlc29_vampire_technology.lua l. 387-389) : erreur ; on l'écarte
if vampire_lairs and is_function(vampire_lairs.occupy_lair) and not vampire_lairs.saison_occupy_protege then
	local ca_occupy = vampire_lairs.occupy_lair;
	vampire_lairs.occupy_lair = function(self, fsm, ...)
		if not fsm or (is_function(fsm.is_null_interface) and fsm:is_null_interface()) then
			return;
		end;
		return ca_occupy(self, fsm, ...);
	end;
	vampire_lairs.saison_occupy_protege = true;
end;

-- Technologies : listes de CA réduites à nos deux vampires. Kemmler comme aux Empires (techniques « vampires »
-- débloquées par les seigneurs éveillés dans les repaires). Le Duc écarlate, seigneur vampire, comme les seigneurs
-- vampires de CA (Mannfred, Vlad : techniques « nécromanciens » débloquées par les cadavres ; main_1 et main_2 au
-- départ) : décision de Charles (24.09.2026, 18 h 25). Seuils en cadavres divisés par deux (même décision) : notre carte
-- a une dizaine de fois moins de régions et de batailles que les Empires.
if vampire_technology then
	for _, t in ipairs(vampire_technology.locked_techs_necromancers.techs or {}) do
		if is_number(t.corpses) and not t.saison_reduit then
			t.corpses = math.floor(t.corpses / 2);
			t.saison_reduit = true;
		end;
	end;
	vampire_technology.locked_techs_vampires.factions = {"wh2_dlc11_vmp_the_barrow_legion"};
	vampire_technology.locked_techs_necromancers.factions = {"wh_main_vmp_mousillon"};
	vampire_technology.starting_vampire_techs = {
		{faction = "wh2_dlc11_vmp_the_barrow_legion", tech = "wh3_main_tech_vmp_vampires_main_1"},
		{faction = "wh_main_vmp_mousillon", tech = "wh3_main_tech_vmp_vampires_main_1"},
		{faction = "wh_main_vmp_mousillon", tech = "wh3_main_tech_vmp_vampires_main_2"}
	};
	vampire_technology.starting_necromancer_techs = {
		{faction = "wh2_dlc11_vmp_the_barrow_legion", tech = "wh3_main_tech_vmp_necromancers_0"},
		{faction = "wh2_dlc11_vmp_the_barrow_legion", tech = "wh3_main_tech_vmp_necromancers_1"},
		{faction = "wh_main_vmp_mousillon", tech = "wh3_main_tech_vmp_necromancers_0"}
	};
end;


-- Listes de factions de CA à réduire, en jeu, aux factions présentes sur notre carte (appelé par saison_start.lua
-- avant le démarrage des systèmes concernés).
local function factions_presentes(liste)
	local out = {};
	for i = 1, #liste do
		local f = cm:get_faction(liste[i]);
		if f and not f:is_null_interface() then
			table.insert(out, liste[i]);
		end;
	end;
	return out;
end;

-- Snagla (héros légendaire de Grom) : sans entrée pour notre campagne dans mission_chain_keys, la mission réussie ne
-- le donne pas à Grom joué (audit des scripts de CA, H2 ; wh3_main_legendary_characters.lua l. 1706-1731, 1958-1995).
if character_unlocking and is_table(character_unlocking.character_data) then
	local snagla = character_unlocking.character_data.snagla;
	if is_table(snagla) and is_table(snagla.mission_chain_keys) then
		snagla.mission_chain_keys[CAMPAGNE] = {"wh3_dlc26_ie_grn_snagla_stage_1"};
	end;
end;

-- Assujettissement de CA : nos factions de bataille (armées des finales, des Échos, des étapes) ne sont jamais
-- confédérées ni exécutées par un dilemme de Grom vainqueur (audit des scripts de CA, B6).
if subjugation and is_table(subjugation.invalid_factions) then
	for _, qb in ipairs({"wh_main_grn_greenskins_qb1", "wh_main_grn_greenskins_qb2", "wh_main_grn_greenskins_qb3",
		"wh_dlc03_bst_beastmen_qb1", "wh_dlc03_bst_beastmen_qb2", "wh_dlc03_bst_beastmen_qb3", "wh_main_brt_bretonnia_qb1",
		"wh_main_brt_bretonnia_qb2", "wh_main_vmp_vampire_counts_qb1", "wh_main_vmp_vampire_counts_qb2",
		"wh_main_vmp_vampire_counts_qb3", "wh2_dlc16_wef_wood_elves_qb4", "wh2_dlc16_wef_wood_elves_qb5",
		"wh2_dlc16_wef_wood_elves_qb6", "wh2_dlc16_wef_wood_elves_qb7", "wh_main_dwf_dwarfs_qb1", "wh_main_dwf_dwarfs_qb2",
		"wh_main_dwf_dwarfs_qb3"}) do
		subjugation.invalid_factions[qb] = true;
	end;
end;

-- Retour des hordes de CA (wh_horde_reemergence.lua) : la harde de Morghur ne renaît que par l'histoire de WH1
-- (saison_histoire.lua), jamais au hasard (audit des scripts de CA, M2). CA appelle la fonction globale par son nom.
-- La harde de Khazrak non plus (audit de cohérence du 25.09.2026, point 14) : chez nous elle n'a ni chef ni région, et
-- reviendrait sous le nom « Harde de Khazrak le Borgne », seigneur du Drakwald absent de la carte.
-- 25.09.2026 (revue de la bêta, I1) : en 9.0, CA appelle attempt_to_spawn_scripted_army avec une LISTE de factions mortes
-- (wh_horde_reemergence.lua l. 267-268) ; l'ancien filtre sur le nom ne valait donc jamais. On filtre la fonction qui
-- reçoit UN nom (l. 319 : appelée par son nom global pour chaque faction de la liste) : false = « pas faite », et CA
-- essaie la faction suivante.
local HORDES_SANS_RETOUR = {["wh_dlc05_bst_morghur_herd"] = true, ["wh_dlc03_bst_beastmen"] = true};
if is_function(attempt_to_spawn_scripted_army_for_faction) then
	local ca_retour_d_une_horde = attempt_to_spawn_scripted_army_for_faction;
	function attempt_to_spawn_scripted_army_for_faction(faction_name, ...)
		if HORDES_SANS_RETOUR[faction_name] then
			return false;
		end;
		return ca_retour_d_une_horde(faction_name, ...);
	end;
end;


-- Ruine (Morghur joué, palier 7) : la bataille finale de CA est hors de notre carte ; notre copie, devant Montfort
-- (lot 10, audit des scripts de CA, M1)
if Ruination then
	Ruination.ie_final_battle = "saison_qb_bst_chute_de_l_homme";
end;


function saison_reduire_listes_de_factions()
	-- Terres de sang : éclats de pierre de harde offerts au départ à Khazrak, Malagor, Taurox... absents chez nous.
	if Bloodgrounds and is_table(Bloodgrounds.beastmen_factions) then
		Bloodgrounds.beastmen_factions = factions_presentes(Bloodgrounds.beastmen_factions);
	end;
	if Ruination and is_table(Ruination.beastmen_factions) then
		Ruination.beastmen_factions = factions_presentes(Ruination.beastmen_factions);
	end;
end;
