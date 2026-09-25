-----------------------------------------------------------------------------------
--	La Saison des Révélations : Gotrek et Félix (décision de Charles, 23.09.2026 : rang 15 comme CA, lieu le plus juste
--	pour le lore et le jeu, et une petite chaîne « Chroniques de Félix »). Recherche : 05-journal\2026-09-22-gameplay-wh3\
--	lore-quetes\gotrek-felix.md.
--
--	1. Déblocage comme aux Empires (wh3_main_legendary_characters.lua, entrée gotrek_and_felix) : quand Albéric ou la Fée,
--	   joués, atteignent le rang 15, la bataille de CA « Le Cauchemar de la veille de Geheimnisnacht » (Royaume de
--	   Slaanesh : aucun terrain de notre carte). Nos missions (lot 10) la posent dans la trouée de Gisoreux, à Fort Bergbres,
--	   par où le duo entre en Bretonnie dans la nouvelle « Blood Sport » (Josh Reynolds). Sans joueur bretonnien, le plus
--	   fort des deux duchés les reçoit au tour 30 (règle de CA). CA ne les donne ni aux factions non jouables (Karak
--	   Ziflin) ni aux ennemis du duo.
--	2. Chroniques de Félix, pour le joueur qui a recruté le duo, une étape à la fois (lot 12, textes à nous) :
--	   - « Le Sang de l'arène » : Gotrek termine un tour dans la trouée de Gisoreux (Blood Sport : l'hippogriffe de
--	     l'arène, vaincu puis libéré) ;
--	   - « La Chapelle assiégée » : une armée des morts autour de l'Humble Chapelle (le Duc Rouge laissa le duo enfermé
--	     dans une chapelle du Graal cernée de morts et de banshees : The Serpent Queen, selon le wiki) ;
--	   - « Ce que Reikguard n'a pas fini » : vaincre Heinrich Kemmler (Zombieslayer ; vaincu à Reikguard, il erre dans
--	     les Montagnes Grises : The Return of Nagash).
--	3. Deux humeurs du Tueur, une fois chacune : Gotrek en Athel Loren (il hait les arbres : Trollslayer) ; Gotrek à
--	   Karak Ziflin (les Nains saluent un Tueur : relation améliorée).
-----------------------------------------------------------------------------------
-- 23.09.2026 : écouteurs de début de tour sur FactionBeginTurnPhaseNormal (et non FactionTurnStart) : même
-- moment pour le joueur, et seul évènement de début de tour que le mode « l'IA joue tout » des essais
-- automatiques envoie (erreur 143) ; CA l'emploie aussi pour des factions humaines.

local PREFIXE = "saison_felix_";
local CAMPAGNE = "wh_dlc05_wood_elves";
local GOTREK = "wh3_dlc25_neu_gotrek_hero";
local KEMMLER_SOUS_TYPE = "wh_main_vmp_heinrich_kemmler";
local ZIFLIN = "wh_main_dwf_karak_ziflin";
local DEBLOCAGE = {
	wh_main_brt_bordeleaux = "saison_qb_gotrek_felix_alberic",
	wh_main_brt_carcassonne = "saison_qb_gotrek_felix_fay"
};
local TROUEE = {"wh_dlc05_gisoreux_gisoreux", "wh_dlc05_gisoreux_berghres"};
local ATHEL_LOREN = {
	"wh_dlc05_anmyr_halls_of_anaereth", "wh_dlc05_anmyr_tal_rond", "wh_dlc05_argwylon_waterfall_palace",
	"wh_dlc05_arranoc_tal_esth", "wh_dlc05_atylwyth_tal_amere", "wh_dlc05_cavaroc_halls_of_equos",
	"wh_dlc05_cythral_tyr_vanna", "wh_dlc05_fyr_darric_feast_halls", "wh_dlc05_fyr_darric_threllock",
	"wh_dlc05_modryn_glade_of_eternal_midnight", "wh_dlc05_oak_of_ages", "wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_talsyn_yn_ecryl_koiran", "wh_dlc05_tirsyth_glade_of_eternal_moonlight", "wh_dlc05_torgovann_cromlech_cadai",
	"wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_crag_halls", "wh_dlc05_wydrioth_tal_jul_finel"
};
local IMAGE_GOTREK = 1309;		-- image d'évènement de CA pour Gotrek et Félix (wh2_pro08_gotrek_felix.lua)


-- 1. Déblocage : notre campagne dans les listes de CA (avant setup_legendary_hero_unlocking, appelé par saison_start).
-- Sans mission_chain_keys pour notre campagne, la victoire ne serait pas reconnue.
if character_unlocking and is_table(character_unlocking.character_data) then
	local gf = character_unlocking.character_data.gotrek_and_felix;
	if is_table(gf) and is_table(gf.starting_mission_keys) then
		gf.override_allowed_factions = gf.override_allowed_factions or {};
		gf.override_allowed_factions[CAMPAGNE] = {"wh_main_brt_bordeleaux", "wh_main_brt_carcassonne"};
		gf.mission_chain_keys = gf.mission_chain_keys or {};
		gf.mission_chain_keys[CAMPAGNE] = {};
		for faction, cle in pairs(DEBLOCAGE) do
			gf.starting_mission_keys[faction] = gf.starting_mission_keys[faction] or {};
			gf.starting_mission_keys[faction][CAMPAGNE] = cle;
			table.insert(gf.mission_chain_keys[CAMPAGNE], cle);
		end;
	end;
end;


local function dans(region, liste)
	for i = 1, #liste do
		if liste[i] == region then
			return true;
		end;
	end;
	return false;
end;


local function gotrek_de(faction)
	local f = cm:get_faction(faction);
	if not f then
		return nil;
	end;
	local liste = f:character_list();
	for i = 0, liste:num_items() - 1 do
		local c = liste:item_at(i);
		if c:character_subtype_key() == GOTREK then
			return c;
		end;
	end;
	return nil;
end;


-- 2. Chroniques de Félix : les étapes (construites au démarrage, avec les pièces du moteur des chroniques)
local ETAPES = nil;
local function etapes()
	if ETAPES or not SAISON_MOTEUR then
		return ETAPES;
	end;
	local M = SAISON_MOTEUR;
	local scripte, presence, eliminer, vivant = M.scripte, M.presence, M.eliminer, M.vivant;
	local argent, unite = M.argent, M.unite;
	ETAPES = {
		{cle = "saison_felix_arene", tours = 30, objectifs = scripte("saison_felix_arene"),
		 ecouteurs = presence(GOTREK, TROUEE, "saison_felix_arene"),
		 recompenses = {argent(1500), unite("wh_dlc07_brt_cav_royal_hippogryph_knights_0", 1)}},
		{cle = "saison_felix_chapelle",
		 armee = {lieu = {85, 298}, factions = {"wh_main_vmp_mousillon"}, armee = M.ARMEE_SPECTRES, general = "wh_main_vmp_lord"},
		 recompenses = {argent(4000)}},
		{cle = "saison_felix_reikguard", tours = 40, objectifs = eliminer(M.KEMMLER, KEMMLER_SOUS_TYPE),
		 possible = vivant(M.KEMMLER, KEMMLER_SOUS_TYPE),
		 recompenses = {argent(5000)}}
	};
	return ETAPES;
end;


local function etat(faction)
	return cm:get_saved_value(PREFIXE .. faction) or 0;
end;


local function emettre(faction, e, en_plus)
	local mm = mission_manager:new(faction, e.cle);
	if not mm then
		return false;
	end;
	mm:set_mission_issuer(SAISON_MOTEUR.EMETTEUR);
	mm:set_all_objectives_are_primary();
	local objectifs = e.objectifs;
	if objectifs then
		objectifs(mm, faction);
	end;
	local ajout = en_plus;
	if ajout then
		ajout(mm, faction);
	end;
	for i = 1, #e.recompenses do
		mm:add_payload(e.recompenses[i]);
	end;
	if e.tours then
		mm:set_turn_limit(e.tours);
	end;
	if mm:trigger() == false then
		script_error("La Saison des Revelations : chronique de Felix " .. e.cle .. " non creee");
		return false;
	end;
	-- écouteurs après une mission créée (revue de la bêta, M2), comme les chroniques
	local ecouter = e.ecouteurs;
	if ecouter then
		ecouter(faction, e.cle);
	end;
	out("La Saison des Revelations : chronique de Felix " .. e.cle .. " pour " .. faction);
	return true;
end;


-- déclenche l'étape n ou la première possible ensuite ; une étape impossible est sautée
local function declencher(faction, n)
	local liste = etapes();
	while liste and liste[n] do
		local e = liste[n];
		local peut = e.possible;
		if not peut or peut() then
			cm:set_saved_value(PREFIXE .. faction, n);
			if not e.armee then
				if emettre(faction, e) then
					return;
				end;
			else
				local tour = cm:model():turn_number();
				local niveau = math.min(math.max(20, 12 + math.floor(tour / 5)), 40);
				local rang = math.min(math.max(4, 2 + math.floor(tour / 18)), 9);
				local poser = SAISON_MOTEUR.poser_armee;
				local vaincre = SAISON_MOTEUR.vaincre;
				-- garde (revue de la bêta, M3) : l'armée attendue depuis ce tour ; sans elle deux tours plus tard, l'étape
				-- est sautée (écouteur de tour, plus bas), comme la finale_garde des chroniques
				cm:set_saved_value(PREFIXE .. "attente_" .. faction, tour);
				if poser(faction, PREFIXE .. "armee_" .. faction, e.armee, niveau, rang, function(cqi_force)
					cm:set_saved_value(PREFIXE .. "attente_" .. faction, false);
					if not emettre(faction, e, vaincre(cqi_force)) then
						local retirer = SAISON_MOTEUR.retirer_armee;
						retirer(PREFIXE .. "armee_" .. faction);
					end;
				end) then
					return;
				end;
				cm:set_saved_value(PREFIXE .. "attente_" .. faction, false);
			end;
		end;
		n = n + 1;
	end;
	cm:set_saved_value(PREFIXE .. faction, n);
	out("La Saison des Revelations : chroniques de Felix terminees pour " .. faction);
end;


local function suite(faction)
	local n = etat(faction);
	core:remove_listener("saison_chronique_presence_saison_felix_arene");
	-- au début du tour de sa faction (retrait différé, saison_chroniques.lua)
	local retirer = SAISON_MOTEUR.retirer_armee;
	retirer(PREFIXE .. "armee_" .. faction);
	saison_sur("chroniques de Felix", declencher, faction, n + 1);
end;


-- 3. Humeurs du Tueur
local function humeurs(faction)
	local g = gotrek_de(faction);
	if not g or not g:has_region() then
		return;
	end;
	local region = g:region():name();
	if dans(region, ATHEL_LOREN) and not cm:get_saved_value(PREFIXE .. "arbres_" .. faction) then
		cm:set_saved_value(PREFIXE .. "arbres_" .. faction, true);
		cm:show_message_event(faction, "saison_felix_arbres_titre", "saison_felix_arbres_primaire",
			"saison_felix_arbres_secondaire", true, IMAGE_GOTREK);
	end;
	local z = cm:get_faction(ZIFLIN);
	if region == "wh_dlc05_grey_mountains_2_karak_ziflin" and z and not z:is_dead() and not z:at_war_with(cm:get_faction(faction))
		and not cm:get_saved_value(PREFIXE .. "dawi_" .. faction) then
		cm:set_saved_value(PREFIXE .. "dawi_" .. faction, true);
		cm:apply_dilemma_diplomatic_bonus(faction, ZIFLIN, 3);
		cm:show_message_event(faction, "saison_felix_dawi_titre", "saison_felix_dawi_primaire",
			"saison_felix_dawi_secondaire", true, IMAGE_GOTREK);
	end;
end;


-- À chaque chargement (saison_start.lua), pour le joueur bretonnien qui peut recevoir le duo.
function saison_felix_demarrer()
	if cm:is_multiplayer() or not SAISON_MOTEUR then
		return;
	end;
	for faction, cle_deblocage in pairs(DEBLOCAGE) do
		local f = cm:get_faction(faction);
		if f and not f:is_dead() and f:is_human() then
			local liste = etapes();
			-- le duo recruté : les chroniques commencent au tour suivant
			saison_ecouteur(
				PREFIXE .. "deblocage_" .. faction,
				"MissionSucceeded",
				function(context)
					return context:faction():name() == faction and context:mission():mission_record_key() == cle_deblocage;
				end,
				function()
					if etat(faction) == 0 then
						cm:set_saved_value(PREFIXE .. "debut_" .. faction, cm:model():turn_number() + 1);
					end;
				end,
				true
			);
			saison_ecouteur(
				PREFIXE .. "tour_" .. faction,
				"FactionBeginTurnPhaseNormal",
				function(context)
					return context:faction():name() == faction;
				end,
				function()
					local debut = cm:get_saved_value(PREFIXE .. "debut_" .. faction);
					if etat(faction) == 0 and is_number(debut) and cm:model():turn_number() >= debut then
						saison_sur("chroniques de Felix", declencher, faction, 1);
					end;
					-- l'armée d'une étape jamais parue (aucune case libre) : l'étape est sautée (revue de la bêta, M3)
					local attente = cm:get_saved_value(PREFIXE .. "attente_" .. faction);
					if is_number(attente) and cm:model():turn_number() >= attente + 2 then
						cm:set_saved_value(PREFIXE .. "attente_" .. faction, false);
						local retirer = SAISON_MOTEUR.retirer_armee;
						saison_sur("chroniques de Felix : armee jamais posee", retirer, PREFIXE .. "armee_" .. faction);
						script_error("La Saison des Revelations : chronique de Felix, armee de l'etape " .. etat(faction)
							.. " jamais posee : etape sautee");
						saison_sur("chroniques de Felix", declencher, faction, etat(faction) + 1);
					end;
					saison_sur("humeurs du Tueur", humeurs, faction);
					-- chroniques de Félix finies et les deux humeurs passées : plus rien à faire à chaque tour (audit de
					-- fluidité du 24.09.2026, T13 / S12)
					if etat(faction) > #(etapes() or {}) and cm:get_saved_value(PREFIXE .. "arbres_" .. faction)
						and cm:get_saved_value(PREFIXE .. "dawi_" .. faction) then
						core:remove_listener(PREFIXE .. "tour_" .. faction);
					end;
				end,
				true
			);
			for _, evenement in ipairs({"MissionSucceeded", "MissionFailed", "MissionCancelled"}) do
				saison_ecouteur(
					PREFIXE .. evenement .. "_" .. faction,
					evenement,
					function(context)
						local e = liste and liste[etat(faction)];
						return context:faction():name() == faction and e ~= nil and context:mission():mission_record_key() == e.cle;
					end,
					function()
						suite(faction);
					end,
					true
				);
			end;
			-- étape en cours à la reprise d'une sauvegarde : ses écouteurs scriptés
			local e = liste and liste[etat(faction)];
			local ecouter = e and e.ecouteurs;
			if ecouter then
				ecouter(faction, e.cle);
			end;
		end;
	end;
end;
