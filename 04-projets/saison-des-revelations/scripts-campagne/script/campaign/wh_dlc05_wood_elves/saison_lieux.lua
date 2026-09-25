-----------------------------------------------------------------------------------
--	La Saison des Révélations : quatre lieux du lore (décision de Charles, 23.09.2026, 18 h ; lot 22 des données).
--
--	Conception sourcée : scratchpad\lieux-evenements\propositions.md (Knights of the Grail p. 16, 55, 59-60). Aucun
--	marqueur ni point sur la carte : des ZONES (calage de l'Atlas of the Old World sur notre carte, session de
--	l'extension), et rien ne suppose un lieu trouvé.
--	- Lacrimora, le lac de Gilles, « jamais retrouvé » : dilemme « Les rives introuvables » pour un seigneur bretonnien
--	  joué dont l'armée se tient dans l'ouest de la forêt de Châlons ; le lac n'est trouvé dans aucun des deux choix.
--	- L'Île Silencieuse, au large de Bordeleaux (hors de notre carte) : dilemme « Le silence de l'île » pour Bordeleaux
--	  jouée, quand une de ses armées se tient sur sa côte.
--	- Le Gouffre Noir, au bord nord du Massif d'Orquemont : ses brumes noires glacent les vivants (les morts-vivants en
--	  sont exemptés : choix de conception validé par Charles), ses rejetons, plus rares, dévorent hommes et chevaux ;
--	  pour toutes les armées (pertes par script, comme CA) ; message pour le joueur.
--	Les chiffres (effets, probabilités, délais) sont des choix de conception, à régler en jeu.
-----------------------------------------------------------------------------------

local PREFIXE = "saison_lieux_";
local MORTS_VIVANTS = {wh_main_vmp_vampire_counts = true, wh2_dlc11_cst_vampire_coast = true,
	wh2_dlc09_tmb_tomb_kings = true};
local BRETONNIE = "wh_main_brt_bretonnia";
local BORDELEAUX = "wh_main_brt_bordeleaux";
local COTE_BORDELEAUX = {wh_dlc05_bordeleaux_bordeleaux = true, wh_dlc05_bordeleaux_turris_vigilans = true};
local CAVALERIE = {cav_shk = true, cav_mel = true, cav_mis = true, chariot = true};
local ENNEMIS_DE_LA_BRETONNIE = {wh_dlc03_bst_beastmen = true, wh_main_vmp_vampire_counts = true,
	wh_main_grn_greenskins = true};

-- zones en cases logiques (x vers l'est, y vers le nord) : forêt de Châlons (95 ; 264), Gouffre Noir (117 ; 291) au
-- nord du Massif d'Orquemont (124 ; 272)
local CHALONS_OUEST = {x1 = 70, x2 = 95, y1 = 250, y2 = 280};
local BRUMES = {x = 117, y = 290, rx = 22, ry = 5};
local REJETONS = {x = 117, y = 290, rx = 28, ry = 10};

local MOUVEMENT = "wh_main_effect_force_all_campaign_movement_range";
local COMMANDEMENT = "wh_main_effect_force_stat_leadership";


local function dans_rectangle(z, x, y)
	return x >= z.x1 and x <= z.x2 and y >= z.y1 and y <= z.y2;
end;

local function dans_ellipse(z, x, y)
	local dx, dy = (x - z.x) / z.rx, (y - z.y) / z.ry;
	return dx * dx + dy * dy <= 1;
end;

-- pertes : chaque unité (hors seigneur et héros) retenue par le filtre perd une part de ses hommes
local function affaiblir(mf, part, seulement_cavalerie)
	local unites = mf:unit_list();
	local n = 0;
	for i = 0, unites:num_items() - 1 do
		local u = unites:item_at(i);
		if u:unit_class() ~= "com" and (not seulement_cavalerie or CAVALERIE[u:unit_class()]) then
			local reste = u:percentage_proportion_of_full_strength() / 100 * (1 - part);
			cm:set_unit_hp_to_unary_of_maximum(u, math.max(0.1, reste));
			n = n + 1;
		end;
	end;
	return n;
end;

-- message (incident) pour le joueur, avec un paquet d'effets sur l'armée ; pour l'IA, le paquet seul, sans message
local function incident(cle, faction, mf, effets, duree)
	local paquet = cm:create_new_custom_effect_bundle(cle);
	for _, e in ipairs(effets) do
		paquet:add_effect(e[1], "force_to_force_own", e[2]);
	end;
	paquet:set_duration(duree);
	if not faction:is_human() then
		cm:apply_custom_effect_bundle_to_force(paquet, mf);
		return;
	end;
	local ib = cm:create_incident_builder(cle);
	local pb = cm:create_payload();
	pb:effect_bundle_to_force(mf, paquet);
	ib:set_payload(pb);
	cm:launch_custom_incident_from_builder(ib, faction);
end;


-- 1. Lacrimora
local function rives_introuvables(faction, mf)
	local db = cm:create_dilemma_builder(PREFIXE .. "rives_introuvables");
	local pb = cm:create_payload();
	local fouille = cm:create_new_custom_effect_bundle(PREFIXE .. "rives_fouille");
	fouille:add_effect(MOUVEMENT, "force_to_force_own", -50);
	fouille:set_duration(1);
	pb:effect_bundle_to_force(mf, fouille);
	pb:faction_pooled_resource_transaction("brt_chivalry", "events", 10, false);
	db:add_choice_payload("FIRST", pb);
	pb:clear();
	local songe = cm:create_new_custom_effect_bundle(PREFIXE .. "rives_songe");
	songe:add_effect(MOUVEMENT, "force_to_force_own", 10);
	songe:add_effect(COMMANDEMENT, "force_to_force_own", 5);
	songe:set_duration(3);
	pb:effect_bundle_to_force(mf, songe);
	db:add_choice_payload("SECOND", pb);
	db:add_target("default", mf);
	cm:launch_custom_dilemma_from_builder(db, faction);
end;

-- 2. L'Île Silencieuse
local function silence_de_l_ile(faction, mf)
	local db = cm:create_dilemma_builder(PREFIXE .. "silence_ile");
	local pb = cm:create_payload();
	pb:treasury_adjustment(-300);
	pb:faction_pooled_resource_transaction("brt_chivalry", "events", 10, false);
	db:add_choice_payload("FIRST", pb);
	pb:clear();
	local calme = cm:create_new_custom_effect_bundle(PREFIXE .. "ile_calme");
	calme:add_effect("wh_main_effect_public_order_events", "faction_to_province_own", 3);
	calme:set_duration(5);
	pb:effect_bundle_to_faction(calme);
	db:add_choice_payload("SECOND", pb);
	db:add_target("default", mf);
	cm:launch_custom_dilemma_from_builder(db, faction);
end;


-- une armée au début du tour de sa faction (elle est là où elle a fini le tour précédent)
local function armee(faction, mf, tour)
	local chef = mf:general_character();
	local x, y = chef:logical_position_x(), chef:logical_position_y();
	local nom = faction:name();
	local dilemmes_permis = not (saison_en_essai_auto and saison_en_essai_auto());	-- un essai automatique ne choisit pas

	-- 3. brumes noires : vivants seulement, une nuit sur trois, pas deux fois de suite pour la même armée
	if dans_ellipse(BRUMES, x, y) and not MORTS_VIVANTS[faction:culture()] then
		local cle = PREFIXE .. "brumes_" .. mf:command_queue_index();
		local dernier = cm:get_saved_value(cle);
		if (not is_number(dernier) or tour - dernier >= 3) and cm:model():random_percent(33) then
			cm:set_saved_value(cle, tour);
			affaiblir(mf, 0.08);
			incident(PREFIXE .. "brumes_noires", faction, mf, {{COMMANDEMENT, -3}}, 1);
			out("La Saison des Revelations : brumes noires sur l'armee de " .. nom .. " (" .. x .. " ; " .. y .. ")");
			return;
		end;
	end;

	-- 3 bis. rejeton du Gouffre : rare, surtout la cavalerie (toute armée, morts-vivants compris)
	if dans_ellipse(REJETONS, x, y) then
		local cle = PREFIXE .. "rejeton_" .. nom;
		local dernier = cm:get_saved_value(cle);
		if (not is_number(dernier) or tour - dernier >= 10) and cm:model():random_percent(10) then
			cm:set_saved_value(cle, tour);
			local n = affaiblir(mf, 0.25, true);
			if n == 0 then
				affaiblir(mf, 0.06);
			end;
			incident(PREFIXE .. "rejeton_gouffre", faction, mf, {{COMMANDEMENT, -4}}, 2);
			out("La Saison des Revelations : rejeton du Gouffre contre l'armee de " .. nom);
			return;
		end;
	end;

	-- 1 bis. la brume blanche (brume des lacs sacrés, qui aveugle l'ennemi et épargne les défenseurs du royaume : WD 300,
	-- BRT5 p. 81) : ennemis de la Bretonnie dans l'ouest de Châlons ; une fois tous les 5 tours par faction
	if ENNEMIS_DE_LA_BRETONNIE[faction:culture()] and dans_rectangle(CHALONS_OUEST, x, y) then
		local cle = PREFIXE .. "brume_" .. nom;
		local dernier = cm:get_saved_value(cle);
		if (not is_number(dernier) or tour - dernier >= 5) and cm:model():random_percent(50) then
			cm:set_saved_value(cle, tour);
			incident(PREFIXE .. "brume_blanche", faction, mf, {{MOUVEMENT, -25}}, 2);
			out("La Saison des Revelations : brume blanche sur l'armee de " .. nom);
			return;
		end;
	end;

	-- 3 ter. le Gouffre barre la route aux Orques du Massif (Knights of the Grail p. 55) : une fois tous les 10 tours
	if faction:culture() == "wh_main_grn_greenskins" and dans_ellipse(BRUMES, x, y) then
		local cle = PREFIXE .. "barre_" .. nom;
		local dernier = cm:get_saved_value(cle);
		if not is_number(dernier) or tour - dernier >= 10 then
			cm:set_saved_value(cle, tour);
			incident(PREFIXE .. "gouffre_barre", faction, mf, {{MOUVEMENT, -10}}, 1);
			out("La Saison des Revelations : le Gouffre barre la route a " .. nom);
			return;
		end;
	end;

	if not faction:is_human() or not dilemmes_permis then
		return;
	end;

	-- 1. Lacrimora : une fois par seigneur bretonnien joué
	if faction:culture() == BRETONNIE and tour >= 3 and dans_rectangle(CHALONS_OUEST, x, y)
		and not cm:get_saved_value(PREFIXE .. "rives_" .. nom) then
		cm:set_saved_value(PREFIXE .. "rives_" .. nom, tour);
		rives_introuvables(faction, mf);
		out("La Saison des Revelations : les rives introuvables pour " .. nom);
		return;
	end;

	-- 2. l'Île Silencieuse : une fois, Bordeleaux jouée, armée sur sa côte
	if nom == BORDELEAUX and tour >= 4 and chef:has_region() and COTE_BORDELEAUX[chef:region():name()]
		and not cm:get_saved_value(PREFIXE .. "ile") then
		cm:set_saved_value(PREFIXE .. "ile", tour);
		silence_de_l_ile(faction, mf);
		out("La Saison des Revelations : le silence de l'ile pour " .. nom);
	end;
end;


function saison_lieux_demarrer()
	core:add_listener(
		PREFIXE .. "debut_de_tour",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local f = context:faction();
			return not f:is_rebel() and not f:is_dead();
		end,
		function(context)
			local faction = context:faction();
			local tour = cm:model():turn_number();
			local forces = faction:military_force_list();
			for i = 0, forces:num_items() - 1 do
				local mf = forces:item_at(i);
				if mf:has_general() and not mf:is_armed_citizenry() then
					saison_sur("lieux du lore", armee, faction, mf, tour);
				end;
			end;
		end,
		true
	);
	out("La Saison des Revelations : lieux du lore en place (Lacrimora, Ile Silencieuse, Gouffre Noir)");
end;
