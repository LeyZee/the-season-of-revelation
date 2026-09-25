-----------------------------------------------------------------------------------
--	Événements narratifs de WH3 (les objectifs du début de partie) pour notre campagne.
--
--	Même amorce que celle des Empires Immortels (main_warhammer/wh3_ie_narrative_events.lua), sans leurs données
--	propres : après l'intro (événement ScriptEventIntroCutsceneFinished), « Comment jouer », puis les chaînes communes
--	(vaincre l'ennemi initial, prendre une colonie, recruter, améliorer, rechercher, héros, finances, armées,
--	diplomatie). Les chaînes propres aux Elfes sylvains sont vides chez CA. L'ennemi initial est celui de l'histoire de
--	WH1 (saison_ennemi_initial, plus bas) : CA le cherche parmi les ennemis du tour 1, et la Saison n'en a pas.
--
--	« Comment jouer » (23.09.2026) : pour Orion et Durthu, celui de WH3 est remplacé par celui de la mini-campagne de
--	WH1 (objectifs de l'histoire), suivi du texte de WH3 des Elfes sylvains ({{tr:how_they_play_wood_elves}}, traduit
--	par le jeu). Même moment, même image, même enchaînement : l'évènement de CA est désactivé par sa donnée
--	« suppress_how_they_play_event » et le nôtre écoute et renvoie les mêmes messages. Le texte de CA n'est pas
--	touché (il servirait aussi aux Empires).
-----------------------------------------------------------------------------------

package.path = package.path .. ";" .. cm:get_campaign_folder() .. "/_narrative/?.lua";
require("wh3_narrative_loader");

local ELFES_JOUABLES = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_argwylon"};
local COMMENT_JOUER = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_secondary_detail";
local HARDE = "wh_dlc05_bst_morghur_herd";

-- « Comment jouer » propres à la Saison : texte et image de l'évènement. Orion et Durthu : celui de la mini-campagne de
-- WH1 ; le Duc rouge (23.09.2026) : CA n'en a pas pour Mousillon, jamais jouable chez lui (show_how_to_play_event ne
-- connaît pas la faction : erreur de script et aucun message) ; le nôtre finit par le texte de CA des Comtes vampires
-- ({{tr:how_they_play_vampires_undead}}), image des vampires de CA (594). Les dix seigneurs ont désormais le leur (Morghur, Kemmler et Grom : plus bas).
-- Alberic et la Fée (audit de cohérence du 25.09.2026) : celui de CA ({{tr:how_they_play_bretonnia}}, images 752 et 753
-- comme wh_campaign_setup.lua de WH3, l. 1455-1461) suivi de notre carte (pas de Guerre d'errance, raids de la harde, Vœu de quête, armoiries des
-- duchés absents) ; sous-titre de Bordeleaux : notre nom (« Errants de Bordeleaux » de CA ne vaut pas sur notre carte).
local COMMENT_JOUER_SAISON = {
	["wh_main_brt_bordeleaux"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_bordeleaux_secondary_detail", image = 752,
		sous_titre = "campaign_localised_strings_string_saison_nom_bordeleaux"},
	["wh_main_brt_carcassonne"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_carcassonne_secondary_detail", image = 753},
	-- Morghur, Kemmler, Grom (bêta, 25.09.2026) : le texte de CA ({{tr:how_they_play_…}}) et leurs images de CA
	-- (wh_campaign_setup.lua : 596 Hommes-bêtes, 594 vampires, 797 Grom), suivis de ce que notre carte change
	["wh_dlc05_bst_morghur_herd"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_morghur_secondary_detail", image = 596},
	["wh2_dlc11_vmp_the_barrow_legion"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_kemmler_secondary_detail", image = 594},
	["wh2_dlc15_grn_broken_axe"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_grom_secondary_detail", image = 797},
	["wh_dlc05_wef_wood_elves"] = {texte = COMMENT_JOUER, image = 605},
	["wh_dlc05_wef_argwylon"] = {texte = COMMENT_JOUER, image = 605},
	["wh_main_vmp_mousillon"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_mousillon_secondary_detail", image = 594},
	-- Drycha (audit des scripts de CA, M3) : celui de CA promettait les Racines profondes et la victoire par le rituel
	["wh2_dlc16_wef_drycha"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_drycha_secondary_detail", image = 605},
	-- les Sœurs (24.09.2026) : la Forge de Daith (texte de CA) et notre carte (salle à relever, Racines, victoire de la 9.0)
	["wh2_dlc16_wef_sisters_of_twilight"] = {texte = "event_feed_strings_text_wh_dlc05_saison_comment_jouer_soeurs_secondary_detail", image = 798}
};


-- Ennemi initial du narratif (23.09.2026, journal de Charles de 03 h 37 : « get_initial_enemy_keys() ... could not find
-- any enemies ») : le narratif de CA choisit au tour 1 l'ennemi le plus proche, puis enchaîne « vaincre son armée »,
-- « prendre sa colonie », « tenir la province ». Au tour 1 de la Saison, personne n'est en guerre avec les elfes (la
-- harde ne déclare la guerre qu'à son premier tour), et la harde n'a pas de colonie. On donne donc au narratif, AVANT son
-- démarrage (valeurs sauvegardées que get_initial_enemy_keys lit en premier), l'ennemi de l'histoire de WH1 : la harde,
-- dont les gardiens campent dans la grande salle tombée voisine du seigneur ; la colonie à prendre est cette salle, à
-- reconquérir, et la province à tenir est la sienne.
local SALLES_DE_DEPART = {
	["wh_dlc05_wef_wood_elves"] = "wh_dlc05_talsyn_tal_eth_ayr",		-- Orion : les gardiens de Tal Eth Ayr
	["wh_dlc05_wef_argwylon"] = "wh_dlc05_fyr_darric_threllock",		-- Durthu : les gardiens de Threllock
	-- les Sœurs (24.09.2026) : elles partent sans colonie ; la colonie « à prendre » du narratif est leur salle tombée,
	-- Tal Jul Finel, à relever
	["wh2_dlc16_wef_sisters_of_twilight"] = "wh_dlc05_wydrioth_tal_jul_finel"
};

-- Guerres de départ (23.09.2026, 17 h ; essai du Duc Rouge : sans elles, aucun seigneur n'a d'ennemi au tour 1, alors
-- qu'aux Empires CA en donne un à chacun dans le startpos). Toute partie neuve, joueur ou IA ; ennemi du narratif pour le
-- joueur (sa colonie la plus proche, sa province) :
-- - Grom contre l'Aquitanie : la guerre de départ de CA aux Empires ;
-- - Kemmler contre Parravon : aux Empires, contre l'Artois (absent) ; le lore : « il voulait d'abord marcher sur le duc
--   de Parravon » (05-journal\2026-09-22-gameplay-wh3\lore-quetes\morts-kemmler-duc.md, point 5) ;
-- - Drycha contre la clairière d'Atylwyth, sa voisine : elle « hait les Elfes » (textes de CA de Drycha).
-- - le Duc écarlate contre l'Aquitanie (24.09.2026, enquête d'équilibrage C1.1 et C1.2) : ancien duc d'Aquitaine,
--   traqué par décret de Richemont, « ordre toujours valable » (morts-kemmler-duc.md § 1.4, F24-F28 ; The Red Duke,
--   ch. 19) ; sa chronique 1 et son premier repaire y sont déjà. La guerre de Bastogne (startpos de WH1) reste.
local ENNEMIS_DE_DEPART = {
	["wh2_dlc15_grn_broken_axe"] = {faction = "wh3_main_brt_aquitaine", region = "wh_dlc05_aquitaine_derrevin_libre"},
	["wh2_dlc11_vmp_the_barrow_legion"] = {faction = "wh_main_brt_parravon", region = "wh_dlc05_parravon_grunere"},
	["wh2_dlc16_wef_drycha"] = {faction = "wh_dlc05_wef_atylwyth", region = "wh_dlc05_atylwyth_tal_amere"},
	["wh_main_vmp_mousillon"] = {faction = "wh3_main_brt_aquitaine", region = "wh_dlc05_aquitaine_derrevin_libre"}
};

-- Elfes tenus par l'IA seulement (enquête d'équilibrage C3.1 : Orion et Durthu de l'IA n'avaient aucun ennemi et ne se
-- battaient jamais) ; joués, ils gardent l'histoire de WH1 telle quelle. Guerres de départ de CA aux Empires, ramenées à
-- notre carte :
-- - Orion contre Parravon : sa guerre de départ aux Empires ; lore, la Chasse dans les basses terres de Parravon
--   (foret-drycha-morghur.md, F38) ;
-- - Durthu contre la Légion des Tertres : la bataille des Cairns, où Durthu repousse Kemmler (Wood Elves 8e p. 32 ;
--   foret-drycha-morghur.md F31) ; aux Empires, Karak Norn (absent de notre carte).
local ENNEMIS_DE_DEPART_IA = {
	["wh_dlc05_wef_wood_elves"] = {faction = "wh_main_brt_parravon"},
	["wh_dlc05_wef_argwylon"] = {faction = "wh2_dlc11_vmp_the_barrow_legion"}
};

-- Paix interdite (enquête d'équilibrage C1.1) : le décret de Richemont (lore, voir plus haut) interdit pour toujours la
-- paix entre Mousillon et l'Aquitanie. Choix de conception, sans lore : les guerres de départ des vampires contre
-- Bastogne et Parravon ne peuvent pas finir en paix avant PAIX_BLOQUEE_TOURS tours (l'IA signait la paix vers le tour 6
-- et ne se battait plus du tout).
local PAIX_BLOQUEE_TOURS = 15;
local PAIX_INTERDITE = {{"wh_main_vmp_mousillon", "wh3_main_brt_aquitaine"}};
local PAIX_BLOQUEE = {{"wh_main_vmp_mousillon", "wh_main_brt_bastonne"},
	{"wh2_dlc11_vmp_the_barrow_legion", "wh_main_brt_parravon"}};

-- Guerre retardée (choix de conception, 24.09.2026, 23 h, partie de comparaison Drycha 29 tours) : Grom et le Duc
-- écarlate, tous deux de l'IA, attaquaient Bordeleaux le même tour (12) et l'avaient rayée avant le tour 20 ; la
-- Bretonnie est au cœur de l'histoire. Entre factions de l'IA seulement (un joueur reste libre, et Alberic joué garde
-- ses ennemis), la déclaration de guerre contre Bordeleaux est fermée jusqu'au tour PAIX_BLOQUEE_TOURS.
-- Grom contre l'Aquitanie (bilan d'équilibrage du 25.09.2026) : aux parties de 30 tours, Grom de l'IA prend l'Aquitanie
-- entre les tours 4 et 7, soit la victoire courte du Duc écarlate et le départ de sa traque ; aux essais de 10 tours de
-- la bêta (25.09.2026, 14 h 22), Grom 2 → 5 régions et Mousillon 4 → 6, l'Aquitanie prise des deux côtés dès le tour
-- 1. Grom de l'IA : sa guerre de départ contre l'Aquitanie n'est pas déclarée et reste fermée jusqu'au tour
-- PAIX_BLOQUEE_TOURS (si = "grom_ia"). Grom joué la garde.
local GUERRE_RETARDEE = {{"wh_main_vmp_mousillon", "wh_main_brt_bordeleaux"},
	{"wh2_dlc15_grn_broken_axe", "wh_main_brt_bordeleaux"},
	{"wh2_dlc15_grn_broken_axe", "wh3_main_brt_aquitaine", si = "grom_ia"}};

-- valeur sauvée d'une guerre retardée : par paire de factions, pas par rang dans GUERRE_RETARDEE (revue de la bêta,
-- M8 : une entrée insérée plus tard rouvrirait sinon la mauvaise guerre dans les parties en cours)
local function cle_guerre_retardee(p)
	return "saison_guerre_retardee_" .. p[1] .. "_" .. p[2];
end;

local function grom_ia()
	local grom = cm:get_faction("wh2_dlc15_grn_broken_axe");
	return grom and not grom:is_human();
end;

-- La Fée et l'Aquitanie alliées (bêta, 25.09.2026). Lore : à la Fin des Temps, le duc Armand d'Aquitaine et la Fée
-- Enchanteresse marchent ensemble contre Mallobaude (Lexicanum « Mallobaude », d'après The End Times : Nagash ; une seule
-- source, dossier duc-9.0\lore, M3) ; Armand d'Aquitaine est un seigneur de la Saison de WH1. Aux essais, la Fée de l'IA
-- gardait 6 armées sans une bataille pendant que l'Aquitanie tombait. Alliance militaire entre IA seulement, et pas quand le Duc est joué (son
-- duché à reprendre resterait trop gardé pour un seigneur déjà très difficile).
local ALLIANCE_BRETONNE = {"wh_main_brt_carcassonne", "wh3_main_brt_aquitaine"};

local function paix(a, b, permise)
	cm:force_diplomacy("faction:" .. a, "faction:" .. b, "peace", permise, permise, true);
end;

local function guerre_permise(a, b, permise)
	cm:force_diplomacy("faction:" .. a, "faction:" .. b, "war", permise, permise, true);
end;

-- Appelée par saison_partie_neuve (saison_start.lua), avant saison_ennemi_initial.
function saison_guerres_de_depart()
	cm:disable_event_feed_events(true, "wh_event_category_diplomacy", "", "");
	-- l'alliance d'abord : une guerre déclarée ensuite contre l'Aquitanie appelle son alliée, la Fée
	local fee, aq, duc = cm:get_faction(ALLIANCE_BRETONNE[1]), cm:get_faction(ALLIANCE_BRETONNE[2]),
		cm:get_faction("wh_main_vmp_mousillon");
	local alliance = fee and aq and not fee:is_human() and not aq:is_human() and not (duc and duc:is_human());
	if alliance then
		cm:force_alliance(ALLIANCE_BRETONNE[1], ALLIANCE_BRETONNE[2], true);
		out("La Saison des Revelations : alliance " .. ALLIANCE_BRETONNE[1] .. " / " .. ALLIANCE_BRETONNE[2]);
	end;
	local function guerre(seigneur, cible)
		local a, b = cm:get_faction(seigneur), cm:get_faction(cible);
		if a and b and not a:is_dead() and not b:is_dead() and not a:at_war_with(b) then
			cm:force_declare_war(seigneur, cible, false, alliance and cible == ALLIANCE_BRETONNE[2]);
			out("La Saison des Revelations : guerre de depart " .. seigneur .. " / " .. cible);
		end;
	end;
	for seigneur, e in pairs(ENNEMIS_DE_DEPART) do
		if not (seigneur == "wh2_dlc15_grn_broken_axe" and grom_ia()) then
			guerre(seigneur, e.faction);
		end;
	end;
	for seigneur, e in pairs(ENNEMIS_DE_DEPART_IA) do
		local a = cm:get_faction(seigneur);
		if a and not a:is_human() then
			guerre(seigneur, e.faction);
		end;
	end;
	for _, p in ipairs(PAIX_INTERDITE) do
		paix(p[1], p[2], false);
	end;
	for _, p in ipairs(PAIX_BLOQUEE) do
		paix(p[1], p[2], false);
	end;
	for i, p in ipairs(GUERRE_RETARDEE) do
		local a, b = cm:get_faction(p[1]), cm:get_faction(p[2]);
		-- 25.09.2026, 18 h (essais de 17 h 19 à 17 h 42) : Grom et l'Aquitanie sont DÉJÀ en guerre au départ (startpos) ;
		-- la fermeture ne vaut que pour une déclaration, et Grom prenait Gien, Derrevin Libre et Château d'Épée avant le
		-- tour 10. Pour cette paire seulement, la guerre de départ est close, puis fermée comme les autres.
		-- (l'interface peut dire « en guerre » jusqu'au tick suivant : la paix faite vaut « pas en guerre »)
		local paix_faite = false;
		if p.si == "grom_ia" and grom_ia() and a and b and not b:is_human() and a:at_war_with(b) then
			cm:force_make_peace(p[1], p[2]);
			paix_faite = true;
			out("La Saison des Revelations : paix de depart " .. p[1] .. " / " .. p[2]);
		end;
		if a and b and not a:is_human() and not b:is_human() and (paix_faite or not a:at_war_with(b))
			and (p.si ~= "grom_ia" or grom_ia()) then
			guerre_permise(p[1], p[2], false);
			cm:set_saved_value(cle_guerre_retardee(p), true);
			out("La Saison des Revelations : guerre retardee " .. p[1] .. " / " .. p[2]);
		end;
	end;
	cm:callback(function() cm:disable_event_feed_events(false, "wh_event_category_diplomacy", "", "") end, 1);
end;

-- À chaque chargement : la paix bloquée des guerres de départ se rouvre au tour PAIX_BLOQUEE_TOURS (une seule fois).
function saison_paix_rouverte()
	if cm:get_saved_value("saison_paix_rouverte") then
		return;
	end;
	saison_ecouteur(
		"saison_paix_rouverte",
		"WorldStartRound",
		function() return cm:model():turn_number() >= PAIX_BLOQUEE_TOURS end,
		function()
			for _, p in ipairs(PAIX_BLOQUEE) do
				paix(p[1], p[2], true);
			end;
			for i, p in ipairs(GUERRE_RETARDEE) do
				-- clé par paire ; l'ancienne clé par rang reste lue pour les parties commencées avant le 25.09.2026, 19 h
				if cm:get_saved_value(cle_guerre_retardee(p)) or cm:get_saved_value("saison_guerre_retardee_" .. i) then
					guerre_permise(p[1], p[2], true);
					out("La Saison des Revelations : guerre rouverte " .. p[1] .. " / " .. p[2]);
				end;
			end;
			cm:set_saved_value("saison_paix_rouverte", true);
			core:remove_listener("saison_paix_rouverte");
			out("La Saison des Revelations : paix rouverte entre les vampires et Bastogne / Parravon");
		end,
		true
	);
end;

-- Seigneurs sans ennemi de départ dans la Saison (Alberic, la Fée, Morghur) : ces deux chaînes sont coupées, comme CA le
-- fait pour Golgfag ; les autres objectifs de WH3 (recrutement, améliorations, technologies, héros, finances, armées,
-- diplomatie) restent.
local EVENEMENTS_SANS_ENNEMI = {
	"shared_defeat_initial_army_query_is_enemy_army_closer_than_settlement", "shared_event_defeat_initial_enemy",
	"shared_settlement_capture_query_can_capture_territory", "shared_settlement_capture_query_advice",
	"shared_settlement_capture_query_full_province_ownership", "shared_settlement_capture_query_territorial_holdings",
	"shared_settlement_capture_event_capture_settlement", "shared_settlement_capture_event_control_province",
	"shared_settlement_capture_query_pre_enact_commandment", "shared_settlement_capture_event_enact_commandment",
	"shared_settlement_capture_query_two_provinces_owned", "shared_settlement_capture_event_control_two_provinces",
	"shared_settlement_capture_mark_advice_history",
	"shared_settlement_capture_trigger_pre_control_provinces_turn_countdown",
	"shared_settlement_capture_trigger_pre_control_provinces_turn_countdown_transition",
	"shared_settlement_capture_event_control_provinces"
};

-- Appelée par saison_partie_neuve (saison_start.lua), avant le démarrage du narratif.
function saison_ennemi_initial()
	local humains = cm:get_human_factions();
	local harde = cm:get_faction(HARDE);
	for i = 1, #humains do
		local cle = humains[i];
		local salle = (not cm:is_multiplayer()) and SALLES_DE_DEPART[cle];	-- l'histoire (et ses gardiens) est solo
		local region = salle and cm:get_region(salle);
		if region and not region:is_null_interface() and harde and not harde:is_dead() then
			cm:set_saved_value(cle .. "_narrative_initial_faction", HARDE);
			cm:set_saved_value(cle .. "_narrative_initial_region", salle);
			cm:set_saved_value(cle .. "_narrative_initial_province", region:province_name());
			if not harde:at_war_with(cm:get_faction(cle)) then
				cm:disable_event_feed_events(true, "wh_event_category_diplomacy", "", "");
				cm:force_declare_war(HARDE, cle, false, false);
				cm:callback(function() cm:disable_event_feed_events(false, "wh_event_category_diplomacy", "", "") end, 1);
			end;
		elseif not cm:is_multiplayer() and ENNEMIS_DE_DEPART[cle] and cm:get_region(ENNEMIS_DE_DEPART[cle].region)
			and not cm:get_region(ENNEMIS_DE_DEPART[cle].region):is_abandoned()
			and cm:get_region(ENNEMIS_DE_DEPART[cle].region):owning_faction():name() == ENNEMIS_DE_DEPART[cle].faction then
			-- guerre de départ (saison_guerres_de_depart) : sa colonie la plus proche du seigneur et sa province
			local e = ENNEMIS_DE_DEPART[cle];
			cm:set_saved_value(cle .. "_narrative_initial_faction", e.faction);
			cm:set_saved_value(cle .. "_narrative_initial_region", e.region);
			cm:set_saved_value(cle .. "_narrative_initial_province", cm:get_region(e.region):province_name());
		else
			-- une valeur pour que get_initial_enemy_keys ne cherche pas (chaînes coupées plus bas)
			cm:set_saved_value(cle .. "_narrative_initial_faction", cle == HARDE and ELFES_JOUABLES[1] or HARDE);
		end;
	end;
end;

-- Réglages valables pour toutes les factions de la campagne (ceux des Empires).
narrative.add_data_setup_callback(
	function()
		narrative.add_data_for_campaign("shared_event_defeat_initial_enemy_completed_messages", {"StartSettlementCaptureChain"});
		narrative.add_data_for_campaign("shared_settlement_capture_query_can_capture_territory_positive_messages", {"StartSettlementCapturedCaptureSettlement"});

		-- les données narratives n'existent que pour la faction jouée
		for cle in pairs(COMMENT_JOUER_SAISON) do
			local f = cm:get_faction(cle);
			if f and f:is_human() then
				narrative.add_data_for_faction(cle, "suppress_how_they_play_event", true);
			end;
		end;

		-- seigneurs sans ennemi de départ : chaînes « ennemi initial » et « prise de colonie » coupées
		local humains = cm:get_human_factions();
		for i = 1, #humains do
			if cm:is_multiplayer() or not (SALLES_DE_DEPART[humains[i]] or ENNEMIS_DE_DEPART[humains[i]]) then
				for j = 1, #EVENEMENTS_SANS_ENNEMI do
					narrative.add_data_for_faction(humains[i], EVENEMENTS_SANS_ENNEMI[j] .. "_block", true);
				end;
			end;
		end;
	end
);

-- Le « Comment jouer » de la Saison (modèle : construct_narrative_event_how_they_play de CA).
narrative.add_loader(
	function(faction_key)
		local propre = COMMENT_JOUER_SAISON[faction_key];
		if not propre then
			return;
		end;

		local ne = narrative_event:new("saison_comment_jouer", faction_key);
		if not ne then
			return;
		end;

		ne:add_trigger_condition("StartHowTheyPlay", true, "StartHowTheyPlay");
		ne:add_message_on_issued("StartPostHowTheyPlay");

		ne:set_trigger_callback(
			function(triggering_message, allow_issue_completed_callback)
				allow_issue_completed_callback(false);

				-- essai automatique (saison_en_essai_auto, required.lua) : pas de message qui attend un clic
				if saison_en_essai_auto() then
					allow_issue_completed_callback(true);
					return;
				end;


				cm:show_message_event(
					faction_key,
					"event_feed_strings_text_wh2_scripted_event_how_they_play_title",
					propre.sous_titre or ("factions_screen_name_" .. faction_key),
					propre.texte,
					true,
					propre.image,
					function()
						if cm:is_multiplayer() then
							allow_issue_completed_callback(true);
						else
							cm:progress_on_events_dismissed(
								"saison_comment_jouer",
								function()
									allow_issue_completed_callback(true);
								end
							);
						end;
					end
				);
			end
		);

		ne:start();
	end
);

-- Appelée par saison_start.lua à chaque chargement.
function start_narrative_events()
	narrative.start();
end;
