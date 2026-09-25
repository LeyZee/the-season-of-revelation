-----------------------------------------------------------------------------------
--	Démarrage de la campagne : points d'entrée et systèmes de Warhammer 3.
--
--	Modèle : les wh_start.lua de CA (Royaumes du Chaos et Empires Immortels), réduits aux systèmes des six cultures de
--	notre carte. Chaque démarrage passe par saison_sur() : dans WH3, une erreur Lua dans un rappel du premier tick
--	saute tous les rappels suivants, y compris celui qui rend la main au joueur (relevé du 23.09.2026,
--	scripts-mecaniques-wh3.md, § 1.6). Une erreur est écrite au journal de script et n'arrête que son système.
-----------------------------------------------------------------------------------

function saison_sur(nom, f, ...)
	if not is_function(f) then
		script_error("La Saison des Revelations : " .. nom .. " : fonction absente");
		return false;
	end;
	local ok, err = pcall(f, ...);
	if not ok then
		script_error("La Saison des Revelations : " .. nom .. " a echoue : " .. tostring(err));
	end;
	return ok;
end;

local sur = saison_sur;


-- Écouteur protégé (audit de fluidité du 24.09.2026, T2 / T3 / S5) : mêmes arguments que core:add_listener. Hors outil de
-- développement, core de CA appelle conditions et rappels sans protection (_lib/lib_core.lua, event_unprotected_callback) :
-- une erreur dans une condition arrête tout l'évènement, pour tous ses écouteurs (ceux de CA compris), à chaque fois.
-- Ici, l'erreur est écrite au journal une seule fois par écouteur, la condition vaut false, et l'évènement continue.
-- Défini dans ce fichier, chargé après saison_chroniques, saison_histoire, saison_felix, saison_foret et
-- saison_victoires_9_0 (required.lua) : ceux-ci ne l'appellent qu'à l'exécution (fonctions de démarrage appelées par
-- saison_demarrage au premier tick, mission émise, réussite d'étape), jamais au chargement de leur fichier.
local saison_erreurs_vues = {};
function saison_ecouteur(nom, evenement, condition, rappel, persistant)
	local function signaler(quoi, err)
		-- une ligne par message distinct (revue de la bêta, I4)
		local cle = nom .. " " .. quoi .. " " .. string.sub(tostring(err), 1, 160);
		if not saison_erreurs_vues[cle] then
			saison_erreurs_vues[cle] = true;
			script_error("La Saison des Revelations : ecouteur " .. tostring(nom) .. " (" .. quoi .. ") : " .. tostring(err));
		end;
	end;
	local cond = condition;
	if is_function(condition) then
		cond = function(context)
			local ok, res = pcall(condition, context);
			if not ok then
				signaler("condition", res);
				return false;
			end;
			return res;
		end;
	end;
	core:add_listener(
		nom,
		evenement,
		cond,
		function(context)
			local ok, err = pcall(rappel, context);
			if not ok then
				signaler("rappel", err);
			end;
		end,
		persistant
	);
end;


-- (La sonde de début de tour du 25.09.2026, 00 h 30, est retirée : la cause de l'erreur 230 est prouvée, erreur 252 ;
-- revue de la bêta, O5.)
-- Écouteurs de CA sans objet sur notre carte (25.09.2026, nommés par les écouteurs protégés de required.lua, erreur
-- 230) : trois conditions de wh3_campaign_bonus_values.lua (l. 2690, 2709, 2765) lisent les tables globales de Mère
-- Ostankya (Kislev) et de Yuan Bo (Cathay), dont notre campagne ne charge pas les systèmes ; elles plantaient à chaque
-- FactionTurnStart et, sans protection, coupaient l'évènement pour tous. Retirés si leur système est absent. Les autres
-- écouteurs du fichier n'emploient pas de table absente (relevé du 25.09.2026).
function saison_retirer_ecouteurs_sans_objet()
	local retires = {};
	if mother_ostankya_features == nil then
		for _, nom in ipairs({"region_gdp_leech_mother_ostankya", "create_disciple_army_mother_ostankya"}) do
			core:remove_listener(nom);
			table.insert(retires, nom);
		end;
	end;
	if matters_of_state == nil then
		core:remove_listener("faction_gdp_leech_yuan_bo");
		table.insert(retires, "faction_gdp_leech_yuan_bo");
	end;
	if #retires > 0 then
		out("La Saison des Revelations : ecouteurs de CA sans objet retires : " .. table.concat(retires, ", "));
	end;
end;


-- Avant le premier tick : le DLC requis (saison_verrou_dlc.lua), puis initiatives, suivants, objets, et le script de la
-- faction jouée (son intro). Sans le DLC, rien de la campagne ne démarre.
cm:add_pre_first_tick_callback(
	function()
		-- AVANT le verrou du DLC (revue de la bêta, 25.09.2026) : une campagne bloquée ne démarre rien, et ces écouteurs de
		-- CA plantaient alors à chaque FactionTurnStart jusqu'au retour au menu (essais --sans-dlc)
		sur("ecouteurs de CA sans objet", saison_retirer_ecouteurs_sans_objet);	-- plus haut (les coupables du 25.09.2026)
		-- saison_verrou_dlc chargé sous pcall : s'il manque, la campagne n'est pas bloquée et ce rappel non protégé ne
		-- saute pas les suivants (audit de fluidité du 24.09.2026, T17 / S8)
		if is_function(saison_verifier_dlc) and saison_verifier_dlc() then
			return;
		end;
		sur("initiatives de personnage", initiative_unlock_listeners);
		sur("initiatives de faction", function() faction_initiatives_unlocker:initiatives_unlocker_listeners() end);
		sur("suivants", load_followers);
		sur("objets rares", load_rare_items);
		sur("fusion d'objets", item_fusing_listener);
		-- script/campaign/wh_dlc05_wood_elves/factions/<faction>/<faction>_start.lua
		sur("scripts de faction", function() cm:load_local_faction_script("_start") end);
	end
);

cm:add_first_tick_callback_new(function() if not saison_bloquee then sur("partie neuve", saison_partie_neuve) end end);
cm:add_first_tick_callback(function() if not saison_bloquee then sur("demarrage", saison_demarrage) end end);


-- Une seule fois, au premier tour d'une partie neuve.
function saison_partie_neuve()
	sur("diplomatie par defaut", apply_default_diplomacy);
	sur("guerres de depart", saison_guerres_de_depart);			-- saison_narratif.lua (Grom, Kemmler, Drycha)
	sur("ennemi initial du narratif", saison_ennemi_initial);		-- avant narrative.start (saison_demarrage)
	sur("voeux de depart", add_starting_vows);
	sur("Chene des Ages a Durthu", saison_chene_a_durthu);
	sur("mission de victoire", saison_creer_victoire);
	sur("noms des ducs", saison_nommer_les_ducs);		-- saison_monde.lua
	sur("surplus des capitales", saison_surplus_capitales);	-- saison_monde.lua (audit des factions, point 1)
	sur("heros ecartes de leur seigneur", saison_ecarter_les_heros);	-- saison_monde.lua (Charles, 24.09.2026)
end;


-- WH1 (wh_start.lua de la mini-campagne, l. 10-31) : si Durthu est joué sans Orion, le Chêne des Âges lui revient.
function saison_chene_a_durthu()
	local durthu = cm:get_faction("wh_dlc05_wef_argwylon");
	local orion = cm:get_faction("wh_dlc05_wef_wood_elves");
	if not (durthu and durthu:is_human()) or (orion and orion:is_human()) then
		return;
	end;
	-- une seule fois : saison_victoires_9_0.lua l'appelle déjà avant de créer la longue de Durthu (24.09.2026)
	local chene = cm:get_region("wh_dlc05_oak_of_ages");
	if chene and not chene:is_abandoned() and chene:owning_faction():name() == "wh_dlc05_wef_argwylon" then
		return;
	end;
	cm:disable_event_feed_events(true, "wh_event_category_conquest", "", "");
	cm:disable_event_feed_events(true, "wh_event_category_diplomacy", "", "");
	cm:transfer_region_to_faction("wh_dlc05_oak_of_ages", "wh_dlc05_wef_argwylon");
	cm:callback(
		function()
			cm:disable_event_feed_events(false, "wh_event_category_conquest", "", "");
			cm:disable_event_feed_events(false, "wh_event_category_diplomacy", "", "");
		end,
		1
	);
end;


-- À chaque chargement : les systèmes de WH3 des factions de la carte.
function saison_demarrage()
	out("La Saison des Revelations : demarrage des systemes de Warhammer 3");
	out.inc_tab();

	sur("listes de factions", saison_reduire_listes_de_factions);

	-- socle, narratif (objectifs), systèmes généraux
	sur("socle", setup_wh_campaign);
	sur("narratif", start_narrative_events);
	sur("batailles de quete", function() set_piece_battle_abilities:initialise() end);
	-- 9.0 : le retour des hordes de CA lit d'abord fervour.middenland_faction (module de Boris Todbringer, Middenland,
	-- absent de notre carte : cm:get_faction() rendrait false, puis false:is_human(), erreur, et aucun retour des hordes ;
	-- essai d'Orion du 24.09.2026, 18 h 29). Seul ce script de CA que nous chargeons lit fervour : on lui donne une
	-- faction de bataille de notre startpos, jamais humaine (Khazrak peut donc revenir, comme sans Boris joué)
	if fervour == nil then
		fervour = {middenland_faction = "wh_main_vmp_vampire_counts_qb1"};
	end;
	sur("retour des hordes", add_horde_reemergence_listeners);
	sur("seigneurs par technologie", add_tech_tree_lords_listeners);
	sur("batailles forcees", function() Forced_Battle_Manager:load_listeners() end);
	-- le Chêne des Âges ne paie ni taxe ni ordre public, comme aux Empires Immortels
	sur("Chene sans taxe", disable_tax_and_public_order_for_regions, {"wh_dlc05_oak_of_ages"});
	if cm:is_new_game() then
		sur("corruption de depart", add_starting_corruption);
	end;
	sur("bascule de corruption", function() corruption_swing:setup() end);

	-- Hommes-bêtes
	sur("Lune de Morrslieb", function() beastmen_moon:add_moon_phase_listeners() end);
	sur("technologies des hommes-betes", add_beast_tech_lock_listeners);
	sur("terres de sang", function() Bloodgrounds:setup() end);
	sur("Ruine", function() Ruination:add_ruination_listeners() end);

	-- Elfes sylvains
	sur("Elfes sylvains", Add_Wood_Elves_Listeners);
	-- Drycha IA peut faire la guerre aux Asrai (audit des factions, point 6 ; CA la lui interdit, comme à toute IA elfe)
	sur("Drycha contre les Asrai", function()
		local drycha = cm:get_faction("wh2_dlc16_wef_drycha");
		if drycha and not drycha:is_dead() and not drycha:is_human() then
			cm:force_diplomacy("faction:wh2_dlc16_wef_drycha", "culture:wh_dlc05_wef_wood_elves", "war", true, true, false);
		end;
	end);
	-- Sœurs du Crépuscule (24.09.2026) : la Forge de Daith de CA, seulement si leur faction est dans la partie (le script
	-- de CA lit leur faction sans vérifier qu'elle existe)
	sur("Forge de Daith", function()
		local soeurs = cm:get_faction("wh2_dlc16_wef_sisters_of_twilight");
		if soeurs and not soeurs:is_dead() then
			add_sisters_forge_listeners();
		end;
	end);
	sur("Chemins-racines", saison_demarrer_foret);
	sur("ambre", saison_ambre_ecouteurs);			-- saison_foret.lua (audit des factions, point 5)
	sur("missions de confederation", function() confed_missions:setup() end);

	-- Bretonnie
	-- La guerre d'errance de CA (palier 4 de chevalerie, wh_dlc07_bretonnia.lua) lance un dilemme puis une bataille aux
	-- coordonnées des Empires (421 ; 264 ou 550 ; 623), hors de notre carte : mission impossible. C'est la croisade de Louen
	-- hors de notre région ; nos chroniques ont leurs finales. On la marque déjà lancée, comme CA une fois le dilemme posé.
	sur("pas de guerre d'errance", function()
		for _, f in ipairs({"wh_main_brt_bordeleaux", "wh_main_brt_carcassonne"}) do
			if not cm:get_saved_value("bretonnia_final_battle_issued_" .. f) then
				cm:set_saved_value("bretonnia_final_battle_issued_" .. f, true);
			end;
		end;
	end);
	sur("Bretonnie", Add_Bretonnia_Listeners);
	sur("Benediction de la Dame", Add_Lady_Blessing_Listeners);
	sur("heraldique", Add_Bretonnia_Technology_Listeners);
	sur("economie paysanne", Add_Peasant_Economy_Listeners);
	sur("vertus", Add_Virtues_and_Traits_Listeners);
	sur("chevalerie", Add_Chivalry_Listeners);
	sur("Chevalier vert", add_green_knight_listeners);

	-- Comtes vampires, refonte de la 9.0 (24.09.2026 ; audit 05-journal\2026-09-24-vampires-9.0\audit-systemes-vampires-9.0.md) :
	-- dans l'ordre de CA (wh_start.lua, bloc dlc29), sans les modules de Neferata. Données des repaires et des
	-- technologies adaptées au chargement (saison_donnees_ca.lua).
	sur("trait inne (9.0)", function() innate_trait_reset:initialise() end);
	sur("repaires de vampires", function() vampire_lairs:initialise() end);
	sur("lignees vampiriques (9.0)", function()
		-- missions de confédération de CA : seulement celles dont la cible est sur notre carte (Kemmler) ; les écouteurs
		-- de CA qui lisent une mission absente par sa clé sont retirés (sinon une erreur à chaque technologie, unité,
		-- tour...). Ne jamais retirer RitualCompletedEventBloodlinesEffects : le même nom sert aux cadavres.
		local absentes, presentes = {}, {};
		for cle, d in pairs(vampire_bloodlines.confederation_missions) do
			local f = cm:get_faction(d.target_faction);
			if f and not f:is_null_interface() then
				presentes[cle] = d;
			else
				absentes[cle] = true;
			end;
		end;
		vampire_bloodlines.confederation_missions = presentes;
		vampire_bloodlines:initialise();
		local ecouteurs = {
			wh3_dlc29_vmp_mission_confederate_lord_vlad_isabella = {"VampireBloodlinesVladVassalizeFaction",
				"VampireBloodlinesVladResearchVampirismTechnology"},
			wh3_dlc29_vmp_mission_confederate_lord_mannfred = {"VampireBloodlinesMannfredAwakenBloodlineLord",
				"VampireBloodlinesMannfredConvertProvinceClimate"},
			wh3_dlc29_vmp_mission_confederate_lord_ghorst = {"VampireBloodlinesGhorstRankedUnit",
				"VampireBloodlinesGhorstUnitCreated", "VampireBloodlinesGhorstResearchNecromancyTechnology",
				"VampireBloodlinesGhorstTurnStartUpdate"},
			wh3_dlc29_vmp_mission_confederate_lord_neferata = {"VampireBloodlinesNeferataRankedUnit",
				"VampireBloodlinesNeferataUnitCreated", "VampireBloodlinesNeferataTurnStartUpdate"}
		};
		for cle, noms in pairs(ecouteurs) do
			if absentes[cle] then
				for _, n in ipairs(noms) do
					core:remove_listener(n);
				end;
			end;
		end;
	end);
	sur("cadavres (9.0)", function() vampire_corpses:initialise() end);
	sur("technologies vampiriques (9.0)", function()
		vampire_technology:initialise();
		-- faille de CA (Mousillon n'est pas jouable aux Empires) : le Duc écarlate joué qui recherche la technique de
		-- confédération du Duc écarlate ferait absorber SA faction par wh3_main_vmp_remnants ; verrouillée pour lui
		if cm:is_new_game() then
			local duc = cm:get_faction("wh_main_vmp_mousillon");
			if duc and not duc:is_null_interface() then
				cm:lock_one_technology_node("wh_main_vmp_mousillon", vampire_technology.feature_unlocks.confederate_red_duke);
			end;
		end;
	end);
	sur("cadavres des batailles (9.0)", function() vampire_corpses_distribution:initialise() end);
	-- techniques exclusives l'une de l'autre (nécromanciens misc_4/5 et misc_9/10, zombies 3a/b/c), comme aux Empires
	-- (main_warhammer/wh_start.lua l. 317) : sans elles, le Duc et Kemmler pouvaient tout rechercher (audit du Duc,
	-- 25.09.2026)
	sur("techniques exclusives (9.0)", function() mutually_exclusive_techs:initialise() end);
	-- le Duc écarlate (saison_duc.lua) : après les lignées, dont il emprunte le rituel des Dragons de sang
	sur("Duc ecarlate", saison_duc_demarrer);
	-- Krell au départ avec Kemmler (lot 41, 25.09.2026) : preuve au journal, une fois, en partie neuve (lecture seule)
	if cm:is_new_game() then
		sur("Krell au depart", function()
			local legion = cm:get_faction("wh2_dlc11_vmp_the_barrow_legion");
			if not legion or legion:is_null_interface() then
				return;
			end;
			local vu = false;
			local liste = legion:character_list();
			for i = 0, liste:num_items() - 1 do
				local c = liste:item_at(i);
				if c:character_subtype_key() == "wh3_dlc29_vmp_krell" then
					vu = true;
					out("La Saison des Revelations : Krell au depart avec Kemmler (" .. c:logical_position_x() .. ", "
						.. c:logical_position_y() .. ")");
				end;
			end;
			if not vu then
				out("La Saison des Revelations : Krell ABSENT de la Legion des Tertres au depart");
			end;
		end);
	end;

	-- Peaux-vertes
	sur("ferraille", function() salvage:initialise() end);
	sur("Waaagh!", function() waaagh:add_waaagh_listeners() end);
	-- marmite de Grom la Panse (spécification Drycha / Kemmler / Grom, 23.09.2026) : add_grom_food_listeners de CA lit le
	-- chef de sa faction sans vérifier qu'elle existe ; appelé seulement si Grom est dans la partie. Le marchand paraît
	-- près de ses colonies (aucune coordonnée des Empires). L'histoire de Grom (Revanche de Dent-Noire) : saison_grom
	-- (23.09.2026), sans Tor Yvresse ; « Coeddil déchaîné » de Drycha (armée posée à des coordonnées des Empires) n'est
	-- pas repris tel quel.
	if cm:get_faction("wh2_dlc15_grn_broken_axe") then
		sur("marmite de Grom", add_grom_food_listeners);
		sur("Revanche de Dent-Noire", saison_grom_histoire);
		-- son trait de faction sans « Waaagh contre Ulthuan ! » (audit de cohérence du 25.09.2026, saison_grom.lua)
		sur("trait de Grom", saison_grom_trait);
	end;

	-- Nains
	sur("cycles de rancunes", function() grudge_cycle:initialise() end);
	sur("rancunes de depart", function() starting_grudge_missions:initialise() end);
	-- pas de Forge des Nains : elle ne sert qu'à un Nain joué, et aucun ne l'est sur notre carte (audit de fluidité du
	-- 24.09.2026, T10 / S15 ; son écouteur PooledResourceChanged tournait pour rien)
	sur("Profondeurs", add_underdeep_listeners);

	-- systèmes communs
	sur("sante des recrues", function() recruited_unit_health:initialise() end);
	sur("options d'occupation", function() scripted_occupation_options:initialise() end);
	sur("technologies scriptees", function() scripted_technology_tree:start_technology_listeners() end);
	-- Revenus de fond de l'IA de CA (enquête d'équilibrage du 24.09.2026, C1.4) : aux Empires, wh_start.lua les lance en
	-- partie neuve (start_background_incomes) ; la 9.0 y donne aux vampires majeurs de l'IA la Puissance (repaires,
	-- rituels, cadavres). Mousillon, mineure aux Empires, n'est pas dans la liste de CA : on l'ajoute (même levier,
	-- réservé à l'IA ; l'écouteur de CA relit la liste tous les 10 tours).
	-- Bêta (25.09.2026) : retiré un moment contre la boule de neige de Mousillon, puis RENDU sur la ligne de Charles
	-- (« plus difficile que le jeu de base », lore d'abord, grimdark) : le Duc est le Fléau d'Aquitaine, Mousillon une
	-- terre maudite qui menace ses voisins (dossier duc-9.0\lore, G1, M2). La boule de neige se règle par les guerres et
	-- l'alliance de saison_narratif.lua, pas en affaiblissant la menace.
	local MOUSILLON_REVENU_IA = true;
	sur("revenus de fond de l'IA (liste)", function()
		local vmp = campaign_ai_script.difficulty_scaled_background_incomes
			and campaign_ai_script.difficulty_scaled_background_incomes.vmp_power;
		if MOUSILLON_REVENU_IA and vmp and is_table(vmp.factions) then
			local present = false;
			for _, f in ipairs(vmp.factions) do
				if f == "wh_main_vmp_mousillon" then
					present = true;
				end;
			end;
			if not present then
				table.insert(vmp.factions, "wh_main_vmp_mousillon");
			end;
		end;
	end);
	if cm:is_new_game() then
		sur("revenus de fond de l'IA", function() campaign_ai_script:start_background_incomes() end);
	end;
	sur("IA de campagne", function() campaign_ai_script:setup_listeners() end);
	sur("assujettissement", function() subjugation:initialise() end);
	sur("amelioration des personnages", function() CUS:initialise() end);
	sur("heros legendaires", function() character_unlocking:setup_legendary_hero_unlocking() end);
	sur("defis d'avant-bataille", function() pre_battle_challenges:initialise() end);

	-- l'histoire de la mini-campagne de WH1 (après la diplomatie par défaut de la partie neuve), et ses quêtes
	sur("histoire de la mini-campagne", saison_histoire_demarrer);
	sur("entretien des invasions rendues a l'IA", saison_entretien_des_invasions);	-- saison_histoire.lua (T19)
	sur("paix des guerres de depart rouverte", saison_paix_rouverte);	-- saison_narratif.lua (équilibrage, C1.1)
	sur("eveil d'Ariel", saison_ariel_ecouteur);	-- saison_foret.lua (Chêne au niveau 3 ; Charles, 24.09.2026)
	sur("quetes des seigneurs", saison_quetes_demarrer);
	sur("voeux et victoire", saison_victoire_ecouteurs);
	-- victoires au format 9.0 des dix seigneurs (saison_victoires_9_0.lua) : écouteurs de CA et les nôtres
	sur("victoires 9.0", saison_victoires_9_0_ecouteurs);
	-- Chroniques de la Saison des seigneurs de WH3 (saison_chroniques.lua) : aucune écriture avant le tour 2
	sur("chroniques de la Saison", saison_chroniques_demarrer);
	-- Chroniques de Félix (saison_felix.lua) : après le recrutement de Gotrek et Félix par Albéric ou la Fée
	sur("chroniques de Felix", saison_felix_demarrer);
	-- prologue du seigneur joué après son intro (saison_prologue.lua), une fois par partie
	sur("prologue", saison_prologue_ecouteurs);
	-- Nom de faction propre à notre campagne (campaign_localised_strings, lot 12), à chaque chargement, sans effet sur
	-- les autres campagnes : Bordeleaux (« Errants de Bordeleaux » aux Empires, Alberic en Lustrie). Les autres duchés
	-- gardent leur nom de CA, qui est celui de GW (Gasconnie, Aquitanie, Bastogne en français).
	sur("nom de Bordeleaux", function()
		if cm:get_faction("wh_main_brt_bordeleaux") then
			cm:change_localised_faction_name("wh_main_brt_bordeleaux", "campaign_localised_strings_string_saison_nom_bordeleaux");
			out("La Saison des Revelations : nom de Bordeleaux pose (" .. tostring(common.get_localised_string(
				"campaign_localised_strings_string_saison_nom_bordeleaux")) .. ")");
		end;
	end);
	-- Gisoreux : CA écrit « Giseroux » en anglais (factions_screen_name_wh_dlc05_brt_gisoroux) ; notre nom, dans les deux
	-- langues (audit des textes, 23.09.2026)
	sur("nom de Gisoreux", function()
		if cm:get_faction("wh_dlc05_brt_gisoroux") then
			cm:change_localised_faction_name("wh_dlc05_brt_gisoroux", "campaign_localised_strings_string_saison_nom_gisoreux");
		end;
	end);

	out.dec_tab();
end;
