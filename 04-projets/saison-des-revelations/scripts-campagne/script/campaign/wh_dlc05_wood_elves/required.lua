-----------------------------------------------------------------------------------
--	La Saison des Révélations : scripts de la campagne.
--
--	Gameplay de Warhammer 3 (décision de Charles, 22.09.2026) : on charge les systèmes de CA depuis LEUR dossier, sans
--	en recopier aucun. Ceux de la racine de script/campaign par leur nom, ceux des Empires Immortels par
--	"main_warhammer/<fichier>" (comme CA le fait pour scripted_tours/ et realms/). Le dossier main_warhammer n'est pas
--	ajouté au chemin : ses wh_start, wh_quests et victory_objectives ne doivent jamais remplacer les nôtres.
--	Nos fichiers portent le préfixe saison_. Relevé : 05-journal/2026-09-22-gameplay-wh3/scripts-mecaniques-wh3.md.
-----------------------------------------------------------------------------------

-- scripts de CA à la racine de script/campaign (notre dossier reste devant, ajouté par scripting.lua)
package.path = package.path .. ";" .. cm:get_campaign_folder() .. "/?.lua";

-- Chaque fichier est chargé sous pcall : une erreur au chargement d'un fichier de CA ne doit pas empêcher les suivants,
-- ni les nôtres, de se charger. L'erreur part au journal de script (script/enable_console_logging).
local function charger(nom, force)
	local ok, err = pcall(force and force_require or require, nom);
	if not ok then
		script_error("La Saison des Revelations : chargement de " .. nom .. " impossible : " .. tostring(err));
	end;
	return ok;
end;

-- Écouteurs d'évènements protégés pour TOUTE notre campagne (25.09.2026, 01 h ; erreur 230). En jeu publié, core de CA
-- évalue les conditions de tous les écouteurs d'un évènement, puis leurs rappels, sans protection (_lib/lib_core.lua,
-- core_object:event_callback, evt_callback = event_unprotected_callback) : une seule condition qui plante annule
-- l'évènement pour tous, un rappel qui plante annule les suivants, et rien n'est écrit au journal. Constaté : aucun
-- FactionTurnStart n'arrivait aux scripts de mod, même pour un joueur (sonde du 25.09.2026, 00 h 52).
-- ERREUR 231 : la première version remplaçait evt_callback, crue globale ; elle est LOCALE à lib_core (l. 19,
-- `local evt_callback = nil`) : sans effet. La bonne prise (audit de fluidité du 25.09, § 2 R1) : le moteur appelle
-- self:event_callback(eventname, context) à chaque évènement (lib_core l. 2067, méthode cherchée à chaque appel) ; on pose
-- sur l'objet core une méthode event_callback, copie de la boucle de CA (l. 1967-2008, sans le rapport de performance
-- des outils de CA), où chaque condition et chaque rappel passent par la version protégée ci-dessous (comme le réglage
-- USE_PROTECTED_EVENT_CALLBACKS de CA, sans son texte rouge à l'écran). L'écouteur fautif est nommé au journal une fois,
-- avec la pile qui l'a posé ; une condition en erreur vaut false ; l'évènement continue pour les autres. Ce fichier
-- n'est chargé que par notre campagne : les campagnes de CA n'en sont pas touchées.
local saison_evenements_en_erreur = {};
local function saison_evt_callback_protege(evenement, ecouteur, context, condition)
	local fonction = condition and ecouteur.condition or ecouteur.callback;
	local ok, res = pcall(fonction, context);
	if ok then
		return res;
	end;
	-- le début du message dans la clé (revue de la bêta, I4) : tous les cm:callback passent par UN écouteur de CA
	-- (lib_timer_manager.lua l. 136-147) ; sans lui, seule la première erreur d'un rappel différé arrivait au journal
	local cle = tostring(evenement) .. "|" .. tostring(ecouteur.name) .. "|" .. (condition and "condition" or "rappel")
		.. "|" .. string.sub(tostring(res), 1, 160);
	if not saison_evenements_en_erreur[cle] then
		saison_evenements_en_erreur[cle] = true;
		script_error("La Saison des Revelations : ecouteur [" .. tostring(ecouteur.name) .. "] en erreur sur "
			.. tostring(evenement) .. " (" .. (condition and "condition" or "rappel") .. ") : " .. tostring(res)
			.. "\nPose par :\n" .. tostring(ecouteur.callstack));
	end;
	return false;
end;
if core and is_table(core.event_listeners) and is_function(core.event_callback) then
	core.event_callback = function(self, eventname, context)
		local listeners = self.event_listeners[eventname];
		if not listeners then
			return;
		end;
		local callbacks_to_call = {};
		local should_rebuild = false;
		for i = 1, #listeners do
			local current_listener = listeners[i];
			if current_listener.condition == true
				or saison_evt_callback_protege(eventname, current_listener, context, true) then
				table.insert(callbacks_to_call, current_listener);
				if not current_listener.persistent then
					current_listener.to_remove = true;
					should_rebuild = true;
				end;
			end;
		end;
		if should_rebuild then
			local new_listeners = {};
			for i = 1, #listeners do
				if not listeners[i].to_remove then
					table.insert(new_listeners, listeners[i]);
				end;
			end;
			self.event_listeners[eventname] = new_listeners;
		end;
		for i = 1, #callbacks_to_call do
			saison_evt_callback_protege(eventname, callbacks_to_call[i], context, false);
		end;
	end;
	out("La Saison des Revelations : ecouteurs d'evenements proteges (core.event_callback)");
else
	script_error("La Saison des Revelations : protection des ecouteurs impossible (core.event_callback absent)");
end;

-- Essai automatique (banc de stabilité de la session de construction, 23.09.2026) : son script d'essai pose
-- _G.saison_essai_auto = true au chargement des scripts de mod, avant le premier tick. Alors rien de ce qui attend un
-- joueur ne se joue (intros, caméras et bandes de cinéma de l'histoire, répliques du conseiller de l'histoire,
-- cinématique de fin, « Comment jouer ») ; missions, chroniques, invasions et systèmes de CA tournent normalement.
function saison_en_essai_auto()
	return _G.saison_essai_auto == true;
end;

-- socle de campagne de WH3 (valeurs de bonus scriptées comprises), conseiller, pages d'aide, visites guidées
charger("wh_campaign_setup", true);
charger("wh_campaign_interventions", true);
charger("wh_campaign_help_pages", true);
charger("scripted_tours/campaign_tours");
charger("wh3_campaign_payload_remapping");

-- systèmes communs à toutes les campagnes (sans clé de carte)
charger("wh2_campaign_traits");
charger("wh2_campaign_random_armies");
charger("wh_campaign_ror_recruitment");
charger("wh3_campaign_set_piece_battle_abilities");
charger("wh2_campaign_forced_battle_manager");
charger("wh3_campaign_character_initiative_unlocks");
charger("wh3_campaign_faction_initiative_unlocks");
charger("wh3_campaign_recruited_unit_health");
charger("wh2_campaign_generated_constants");
charger("wh2_campaign_quest_battle_helper");
charger("wh3_campaign_followers");
charger("wh3_campaign_rare_items");
charger("wh3_campaign_item_fusing");
charger("wh3_campaign_corruption");
charger("corruption_swing");
charger("wh3_campaign_ai");
charger("wh3_campaign_character_upgrading");
charger("wh3_campaign_scripted_occupation_options");
charger("wh2_campaign_tech_tree_lords");
charger("wh3_main_legendary_characters");
charger("wh3_campaign_subjugation");
charger("wh3_dlc27_pre_battle_challenges");
charger("wh3_campaign_sally_out_garrisons");	-- sorties des garnisons (points de mouvement des colonels), comme aux Empires
-- intros des seigneurs de WH3 jouables sur notre carte (Alberic, la Fée, Morghur), comme aux Empires
-- (main_warhammer/required.lua) ; nos données : faction_intro/wh_dlc05_wood_elves_faction_intro.lua
charger("faction_intro");

-- Elfes sylvains : Chasse sauvage d'Orion, IA des clairières, Chemins-racines, missions de confédération
charger("main_warhammer/wh_dlc05_wood_elves");
charger("wh2_dlc16_wef_worldroots");
charger("wh2_dlc16_wef_sisters_forge");		-- Forge de Daith des Sœurs du Crépuscule (24.09.2026) ; démarrée par saison_start
charger("wh2_campaign_confederation_missions");

-- Bretonnie (ordre de CA : économie paysanne et chevalerie avant les vertus)
charger("main_warhammer/wh_dlc07_bretonnia");
charger("main_warhammer/wh_dlc07_blessing_of_the_lady");
charger("main_warhammer/wh_dlc07_diplomatic_tech");
charger("main_warhammer/wh_dlc07_peasant_economy");
charger("wh_campaign_bretonnia_chivalry");
charger("main_warhammer/wh_dlc07_virtues_and_traits");
charger("main_warhammer/wh_dlc07_the_green_knight");
charger("main_warhammer/wh_dlc07_vows");

-- Hommes-bêtes : Lune, technologies, pierres de harde et terres de sang, Ruine, retour des hordes
charger("main_warhammer/wh_dlc03_beastmen_moon");
charger("wh2_dlc17_beastmen_tech");
charger("wh2_dlc17_bloodgrounds");
charger("wh2_dlc17_bst_ruination_progression");
charger("main_warhammer/wh_horde_reemergence");

-- Comtes vampires, refonte de la 9.0 (24.09.2026 ; audit 05-journal\2026-09-24-vampires-9.0\audit-systemes-vampires-9.0.md) :
-- wh2_vampire_bloodlines n'existe plus. Utilitaires neufs de la 9.0 d'abord (sans clé de carte), puis les modules des
-- vampires dans l'ordre de CA (main_warhammer/required.lua). Démarrés par saison_start, données adaptées par
-- saison_donnees_ca. Chargés sans être démarrés : covens (lu par les lignées) et mortarques de Nagash (lus par les
-- lignées). Pas chargés : servantes, dissimulation, toile d'influence (Neferata seule, absente de notre carte).
charger("wh3_campaign_climate_change_manager");
charger("wh3_campaign_innate_trait_reset");
charger("main_warhammer/victory_objectives_config_utils");
-- victoires par seigneur de la 9.0 (moteur de CA ; ses listes des Empires remplacées par les nôtres dans
-- saison_victoires_9_0, qui retire aussi leur construction). Jamais main_warhammer/victory_objectives (l'ancien système).
charger("main_warhammer/victory_objectives_config");
charger("main_warhammer/wh3_dlc29_nag_mortarchs");
charger("wh3_dlc29_vampire_lairs");
charger("wh3_dlc29_vampire_covens");
charger("wh3_dlc29_vampire_bloodlines");
charger("wh3_dlc29_vampire_technology");
charger("wh3_dlc29_vampire_corpses");
charger("wh3_dlc29_vampire_corpses_distribution");
charger("wh3_campaign_mutually_exclusive_techs");	-- techniques exclusives (générique, par sous-culture ; 25.09.2026)

-- Peaux-vertes : Waaagh! et ferraille
charger("wh2_dlc15_waaagh");
charger("wh2_dlc15_salvage");
charger("wh2_dlc15_grom_cauldron");	-- marmite de Grom (appelée par saison_start si sa faction existe)
charger("wh2_dlc15_grom_story");	-- Revanche de Dent-Noire (adaptée par saison_grom, appelée par saison_start)

-- Nains : cycles de rancunes, Profondeurs. Pas la Forge (wh3_campaign_forge) : elle ne sert qu'à un Nain joué, et
-- aucun ne l'est sur notre carte (audit de fluidité du 24.09.2026, T10 / S15)
charger("wh3_campaign_grudges");
charger("wh3_campaign_grudges_starting_missions");
charger("wh3_dlc25_grudge_cycles");
charger("wh3_campaign_underdeep");

-- La Saison des Révélations (après les fichiers de CA dont elle complète les tables)
charger("saison_verrou_dlc");
charger("saison_donnees_ca");
charger("saison_foret");
charger("saison_narratif");
charger("saison_intro");
charger("saison_histoire");
charger("saison_victoire");
charger("saison_victoires_9_0");	-- victoires au format 9.0 des dix seigneurs (cinématique de fin : saison_victoire)
charger("saison_quetes");
charger("saison_chroniques");		-- chaînes de quêtes des seigneurs de WH3 (Chroniques de la Saison)
charger("saison_duc");				-- le Duc écarlate : Baiser d'Abhorash, traque de Richemont, tombeau de Galand
charger("saison_felix");			-- Gotrek et Félix : déblocage au rang 15 (comme CA) et Chroniques de Félix
charger("saison_grom");				-- Revanche de Dent-Noire : l'histoire de Grom de CA, sans Tor Yvresse
charger("saison_prologue");			-- prologue des seigneurs après leur intro (caméra, menaces, objectifs)
charger("saison_monde");			-- les ducs de la carte portent leur nom de lore
charger("saison_start");
charger("saison_exploration_depart");
-- saison_essai_corruption (essai des décors de corruption, à drapeau) : plus chargé en jeu normal (audit de fluidité du
-- 25.09.2026, R5 ; comme saison_essai_transfert) ; pour l'essai, le copier dans script\campaign\mod\ du pack d'essai.
-- Hors du jeu normal depuis l'audit de fluidité du 24.09.2026 (T6, T14 / S13), fichiers gardés dans ce dossier ; pour un
-- essai, les copier dans script\campaign\mod\ du pack d'essai : saison_diagnostic (journal des constructions tous les
-- 5 tours), saison_essai_transfert et saison_essai_isoler (essais à drapeau du plantage du tour 11).
charger("saison_filet_blesses");			-- chefs des factions elfes : un blesse d'une faction sans chef ne revient pas (plantage du tour 11)
