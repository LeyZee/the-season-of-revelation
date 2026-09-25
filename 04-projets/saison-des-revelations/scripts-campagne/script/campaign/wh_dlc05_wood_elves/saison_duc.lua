-----------------------------------------------------------------------------------
--	La Saison des Révélations : le Duc écarlate (décision de Charles, 24.09.2026, 18 h 40), en plus des systèmes
--	vampires de la 9.0 (repaires, cadavres, technologies, lignées : saison_donnees_ca.lua, saison_start.lua), de ses
--	objets de CA (saison_quetes.lua), de sa chronique et de sa liste de victoire.
--
--	Lore (dossier 05-journal\2026-09-22-gameplay-wh3\lore-quetes\morts-kemmler-duc.md, § 1.4) :
--	- Baiser d'Abhorash : blessé au siège de Lashiek, il reçoit le Baiser de sang d'Abhorash, lignée des Dragons de sang
--	  (The Red Duke, C.L. Werner, ch. 2 et 19). Sa faction commence avec un niveau de la lignée des Dragons de sang : le
--	  rituel de lignée de CA (wh2_dlc11_ritual_bloodlines_blood_dragon), accompli une fois, gratuitement, au début.
--	- Traque de Richemont : après le second Pré de Ceren, Richemont d'Aquitaine ordonne qu'on le traque dans toute la
--	  Bretonnie, ordre toujours valable ; des chevaliers de Quête le cherchent (The Red Duke, ch. 19 ; Knights of the
--	  Grail, p. 20). Duc écarlate joué et maître d'au moins une région d'Aquitaine : tous les TRAQUE_DELAI tours, une
--	  armée de chevaliers de Quête vient reprendre la région (moteur des chroniques, SAISON_MOTEUR.poser_armee).
--	- Tombeau de Galand : au second Pré de Ceren, le tombeau béni de Galand, son propre fils, disperse son armée
--	  (The Red Duke, ch. 19 ; livre d'armée Comtes Vampires 7e, p. 26). Le Pré de Ceren est en Aquitaine, mais aucune
--	  source ne le situe par rapport à nos colonies : sa zone (CHAMP_DE_CEREN) est un CHOIX DE PLACEMENT, autour de Gien
--	  (114 ; 220), là où le monument « Tombeau du Duc » (lot 21, monuments-lore.json) place déjà la tour de marbre sur
--	  la colline qui domine le Champ. Une armée du Duc écarlate qui commence son tour dans la zone perd une part de ses
--	  morts-vivants (message pour le joueur).
--	Noms : « Pré de Ceren » / « Ceren Field » (édition française du roman, 2013) ; le tombeau de Galand est une chapelle du
--	Graal bâtie sur le pré même ; seul indice de lieu : le village de Mercal, « tout proche », que l'Atlas place à l'ouest
--	de Château d'Épée (lien probable) : zone et monument gardés à Gien, emplacement estimé.
--	Les chiffres (délais, parts, tailles) sont des choix de conception, à régler en jeu.
-----------------------------------------------------------------------------------

local PREFIXE = "saison_duc_";
local MOUSILLON = "wh_main_vmp_mousillon";
local AQUITAINE = {"wh_dlc05_aquitaine_chateau_depee", "wh_dlc05_aquitaine_derrevin_libre", "wh_dlc05_aquitaine_gien"};

local RITUEL_DRAGONS_DE_SANG = "wh2_dlc11_ritual_bloodlines_blood_dragon";

local TRAQUE_PREMIER_TOUR = 8;
local TRAQUE_DELAI = 10;
-- les traqueurs : d'abord l'Aquitaine de Richemont, puis ses voisins bretonniens
local TRAQUEURS = {"wh3_main_brt_aquitaine", "wh_dlc05_brt_quenelles", "wh_main_brt_bordeleaux", "wh_main_brt_bastonne",
	"wh_main_brt_carcassonne", "wh_main_brt_parravon", "wh_dlc05_brt_brionne", "wh_dlc05_brt_gisoroux",
	"wh_dlc05_brt_montfort"};
local ARMEE_QUETE = "wh_dlc07_brt_cav_questing_knights_0,wh_dlc07_brt_cav_questing_knights_0,"
	.. "wh_dlc07_brt_cav_questing_knights_0,wh_dlc07_brt_cav_questing_knights_0,wh_main_brt_cav_grail_knights,"
	.. "wh_dlc07_brt_cav_knights_errant_0,wh_dlc07_brt_cav_knights_errant_0,wh_main_brt_cav_knights_of_the_realm,"
	.. "wh_main_brt_cav_knights_of_the_realm,wh_dlc07_brt_inf_battle_pilgrims_0,wh_dlc07_brt_inf_battle_pilgrims_0,"
	.. "wh_dlc07_brt_inf_men_at_arms_2,wh_dlc07_brt_inf_men_at_arms_2,wh_dlc07_brt_inf_peasant_bowmen_2";
-- tailles selon le tour (25.09.2026) : les 10 premières unités, puis les 14, puis 18 (chevaliers de la Quête et du Graal,
-- pèlerins et archers de plus)
local ARMEE_QUETE_10 = "wh_dlc07_brt_cav_questing_knights_0,wh_dlc07_brt_cav_questing_knights_0,"
	.. "wh_dlc07_brt_cav_questing_knights_0,wh_dlc07_brt_cav_questing_knights_0,wh_main_brt_cav_grail_knights,"
	.. "wh_dlc07_brt_cav_knights_errant_0,wh_dlc07_brt_cav_knights_errant_0,wh_main_brt_cav_knights_of_the_realm,"
	.. "wh_main_brt_cav_knights_of_the_realm,wh_dlc07_brt_inf_battle_pilgrims_0";
local ARMEE_QUETE_18 = ARMEE_QUETE .. ",wh_dlc07_brt_cav_questing_knights_0,wh_main_brt_cav_grail_knights,"
	.. "wh_dlc07_brt_inf_battle_pilgrims_0,wh_dlc07_brt_inf_peasant_bowmen_2";
local TRAQUE_ALERTE = 3;	-- tours entre la prise d'un domaine d'Aquitaine et l'arrivée des chevaliers

local CHAMP_DE_CEREN = {x = 110, y = 226, rx = 10, ry = 7};	-- choix de placement, au pied de Gien (voir l'en-tête)
local PART_DISPERSEE = 0.15;

-- Annonces au joueur : incidents à nos clés, illustrés (lot 37, 25.09.2026 ; les messages de script d'avant montraient
-- des images de CA sans rapport : celle des Hommes-bêtes pour l'index 1803, la Dame du Lac pour 710 et 711).
local function annoncer(cle)
	local f = cm:get_faction(MOUSILLON);
	if f and not f:is_null_interface() and f:is_human() then
		cm:trigger_incident(MOUSILLON, cle, true);
	end;
end;


-- 1. Baiser d'Abhorash : une fois par partie, dès que les lignées de la 9.0 écoutent (appelé après elles)
local function baiser_d_abhorash()
	if cm:get_saved_value(PREFIXE .. "baiser") then
		return;
	end;
	local f = cm:get_faction(MOUSILLON);
	if not f or f:is_null_interface() or f:is_dead() then
		return;
	end;
	cm:set_saved_value(PREFIXE .. "baiser", true);
	cm:perform_ritual(MOUSILLON, "", RITUEL_DRAGONS_DE_SANG);
	out("La Saison des Revelations : Baiser d'Abhorash, lignee des Dragons de sang pour " .. MOUSILLON);
end;


-- 2. Traque de Richemont
local function region_d_aquitaine_du_duc()
	for _, cle in ipairs(AQUITAINE) do
		local r = cm:get_region(cle);
		if r and not r:is_null_interface() and not r:is_abandoned() and r:owning_faction():name() == MOUSILLON then
			return r;
		end;
	end;
	return nil;
end;

local function lancer_traque(duc)
	local region = region_d_aquitaine_du_duc();
	if not region or not SAISON_MOTEUR or not is_function(SAISON_MOTEUR.poser_armee) then
		return;
	end;
	local s = region:settlement();
	-- des noms, pas des interfaces, dans le rappel de l'armée (joué à la création de la force, possiblement après ce
	-- tick ; audit de fluidité du 24.09.2026, T8 / S6)
	local nom_region = region:name();
	-- l'armée paraît à quelques cases de la colonie, du côté de la Bretonnie (au sud-est de l'Aquitaine)
	local lieu = {s:logical_position_x() + 6, s:logical_position_y() - 6};
	local tour = cm:model():turn_number();
	-- force selon le tour (étude d'équilibrage du 25.09.2026, validée par Charles) : 10 unités, niveau 10, rang 1 au tour
	-- 10 ; 14 unités, niveau 15, rang 3 au tour 20 ; 18 unités, niveau 20, rang 5 au tour 30
	local armee = (tour < 15 and ARMEE_QUETE_10) or (tour < 25 and ARMEE_QUETE) or ARMEE_QUETE_18;
	-- cible_region : les chevaliers marchent sur la terre d'Aquitaine du Duc et l'attaquent (revue de la bêta, 25.09.2026)
	local F = {lieu = lieu, factions = TRAQUEURS, armee = armee, general = "wh_main_brt_lord", cible_region = nom_region};
	local niveau = math.min(math.max(10, 10 + math.floor((tour - 10) / 2)), 30);
	local rang = math.min(math.max(1, 1 + math.floor((tour - 10) / 5)), 7);
	local ok = SAISON_MOTEUR.poser_armee(duc:name(), PREFIXE .. "traque", F, niveau, rang, function(cqi_force, boss)
		-- l'ordre de Richemont vaut guerre contre le Duc écarlate
		local traqueur, cible = boss and cm:get_faction(boss), cm:get_faction(MOUSILLON);
		if traqueur and cible and not traqueur:at_war_with(cible) then
			cm:force_declare_war(boss, MOUSILLON, false, false);
		end;
		annoncer("saison_duc_traque");
		out("La Saison des Revelations : traque de Richemont (" .. tostring(boss) .. ") vers " .. nom_region);
	end);
	if ok then
		cm:set_saved_value(PREFIXE .. "traque_tour", tour);
		cm:set_saved_value(PREFIXE .. "traque_prevue", false);
		-- les chevaliers de la Quête passent : les vassaux du sang reprennent courage (mécanique B, plus bas)
		if saison_duc_serments_ebranles then
			saison_duc_serments_ebranles(30);
		end;
	end;
end;


-- 3. Tombeau de Galand, sur le Pré de Ceren
local function dans_le_champ(x, y)
	local dx, dy = (x - CHAMP_DE_CEREN.x) / CHAMP_DE_CEREN.rx, (y - CHAMP_DE_CEREN.y) / CHAMP_DE_CEREN.ry;
	return dx * dx + dy * dy <= 1;
end;

local function tombeau_de_galand(faction)
	local forces = faction:military_force_list();
	local touchees = 0;
	for i = 0, forces:num_items() - 1 do
		local mf = forces:item_at(i);
		if mf:has_general() and not mf:is_armed_citizenry() then
			local chef = mf:general_character();
			if dans_le_champ(chef:logical_position_x(), chef:logical_position_y()) then
				local unites = mf:unit_list();
				for j = 0, unites:num_items() - 1 do
					local u = unites:item_at(j);
					if u:unit_class() ~= "com" then
						local reste = u:percentage_proportion_of_full_strength() / 100 * (1 - PART_DISPERSEE);
						cm:set_unit_hp_to_unary_of_maximum(u, math.max(0.1, reste));
					end;
				end;
				touchees = touchees + 1;
				-- la sainteté du lieu brise aussi la faveur d'Abhorash (plus bas)
				if saison_duc_retirer_faveur then
					saison_duc_retirer_faveur(chef, true);
				end;
			end;
		end;
	end;
	if touchees > 0 then
		if faction:is_human() then
			-- incident illustré (lot 32, 24.09.2026) ; l'ancien message saison_duc_galand_* reste dans les textes
			cm:trigger_incident(MOUSILLON, "saison_duc_galand", true);
		end;
		out("La Saison des Revelations : tombeau de Galand, " .. touchees .. " armee(s) du Duc ecarlate dispersee(s)");
	end;
end;


-- Paquet d'effets à notre clé (lot 34 : nom, description, icône), rempli d'effets de CA. Sans la ligne du lot 34 dans
-- le pack, create_new_custom_effect_bundle rend nil (CA le teste, corruption_swing.lua l. 348) : rien n'est posé.
local function paquet(cle, effets)
	local b = cm:create_new_custom_effect_bundle(cle);
	if not b then
		return nil;
	end;
	b:set_duration(0);
	for _, e in ipairs(effets) do
		b:add_effect(e[1], e[2], e[3]);
	end;
	return b;
end;


-- 4. Le duché perdu (choix de Charles, 25.09.2026 ; 05-journal\2026-09-24-vampires-9.0\duc-ecarlate-9.0-audit-et-
--	propositions.md, mécanique A). Lore : duc d'Aquitaine, il se croit dans son droit et reprend son duché à ceux qu'il
--	nomme les usurpateurs (The Red Duke ; dossier duc-9.0\lore, G1, H1). Selon le nombre des trois domaines d'Aquitaine
--	qu'il tient : dépossédé (aucun), reconquête (un ou deux), restauré (les trois). Joué ou non. Chiffres : choix de
--	conception, à régler en jeu.
local PAQUETS_DUCHE = {"saison_duc_depossede", "saison_duc_reconquete", "saison_duc_restaure"};
local EFFETS_DUCHE = {
	saison_duc_depossede = {{"wh_main_effect_force_stat_leadership", "faction_to_force_own", -4},
		{"wh_main_effect_public_order_faction", "faction_to_province_own", -2}},
	saison_duc_reconquete = {{"wh_main_effect_force_stat_leadership", "faction_to_force_own", -2}},
	saison_duc_restaure = {{"wh_main_effect_force_stat_leadership", "faction_to_force_own", 6},
		{"wh_main_effect_economy_gdp_mod_all", "faction_to_region_own", 10},
		{"wh_main_effect_force_all_campaign_replenishment_rate", "faction_to_force_own", 10}}
};

local function domaines_tenus()
	local n = 0;
	for _, cle in ipairs(AQUITAINE) do
		local r = cm:get_region(cle);
		if r and not r:is_null_interface() and not r:is_abandoned() and r:owning_faction():name() == MOUSILLON then
			n = n + 1;
		end;
	end;
	return n;
end;

-- Paliers (étude d'équilibrage du 25.09.2026, validée par Charles) : aucun domaine, dépossédé (−4 / −2) ; un domaine,
-- reconquête (−2) ; deux domaines, plus aucun malus ; les trois, restauré (+6, +10 %, +10 %).
local function paquet_du_duche(n)
	if n >= #AQUITAINE then
		return "saison_duc_restaure";
	elseif n == 2 then
		return "aucun";
	elseif n == 1 then
		return "saison_duc_reconquete";
	end;
	return "saison_duc_depossede";
end;

local function mettre_a_jour_duche(faction)
	local n = domaines_tenus();
	local voulu = paquet_du_duche(n);
	if cm:get_saved_value(PREFIXE .. "duche_paquet") ~= voulu then
		local b = EFFETS_DUCHE[voulu] and paquet(voulu, EFFETS_DUCHE[voulu]);
		if b or voulu == "aucun" then
			for _, cle in ipairs(PAQUETS_DUCHE) do
				cm:remove_effect_bundle(cle, MOUSILLON);
			end;
			if b then
				cm:apply_custom_effect_bundle_to_faction(b, faction);
			end;
			cm:set_saved_value(PREFIXE .. "duche_paquet", voulu);
			out("La Saison des Revelations : duche du Duc ecarlate : " .. voulu .. " (" .. n .. " domaine(s))");
		end;
	end;
	local avant = cm:get_saved_value(PREFIXE .. "duche_tenus");
	if avant and n ~= avant then
		annoncer((n >= #AQUITAINE and "saison_duc_restaure") or (n > avant and "saison_duc_reprise") or "saison_duc_perte");
		-- un domaine repris : Richemont l'apprend, ses chevaliers arrivent TRAQUE_ALERTE tours plus tard (sauf traque
		-- déjà prévue plus tôt)
		if n > avant and faction:is_human() then
			local dans = cm:model():turn_number() + TRAQUE_ALERTE;
			local prevue = cm:get_saved_value(PREFIXE .. "traque_prevue");
			if not prevue or prevue > dans then
				cm:set_saved_value(PREFIXE .. "traque_prevue", dans);
			end;
		end;
	end;
	cm:set_saved_value(PREFIXE .. "duche_tenus", n);
end;


-- 5. La faveur d'Abhorash (choix de Charles, 25.09.2026, mécanique C) : la Bénédiction de la Dame de CA
--	(wh_dlc07_blessing_of_the_lady.lua), retournée. Lore : le code des Dragons de sang (toujours lancer et accepter le
--	défi, Vampire Counts 6e p. 52 ; El Syf « ne redoute aucun duel », texte de CA) ; la sainteté le brise (Pré de Ceren).
--	Le Duc lui-même, joué, qui gagne une bataille qu'il mène : victoire héroïque sûre, victoire décisive une fois sur
--	trois ; perdue s'il recule, s'il perd, ou au Pré de Ceren. Chiffres : choix de conception, à régler en jeu.
-- Trois degrés (décision du 25.09.2026, sur la recommandation de la construction, validée par Charles) :
-- - degré 1 (+6 attaque, +6 commandement) : une victoire du Duc qu'il mène, avec les chances de la Bénédiction de CA
--   (héroïque 100 %, décisive 20 %, serrée 10 %) ;
-- - degrés 2 (+8/+8) et 3 (+10/+10) : chacun par une nouvelle victoire HÉROÏQUE contre une armée menée par un seigneur
--   (pas une garnison : les Dragons de sang cherchent des adversaires dignes) ; au degré 3, un incident ;
-- - usure : un degré de moins si le Duc ne mène aucune bataille pendant USURE_FAVEUR tours ;
-- - bris total s'il recule, s'il perd, ou au Pré de Ceren. Seulement l'armée du Duc.
local FAVEUR = "saison_duc_faveur_abhorash";
local DEGRES_FAVEUR = {6, 8, 10};
local CHANCES_FAVEUR = {heroic_victory = 100, decisive_victory = 20, close_victory = 10};
local USURE_FAVEUR = 5;
local DEFAITES = {close_defeat = true, decisive_defeat = true, crushing_defeat = true, valiant_defeat = true};
local RUPTURE_DEFAITE_DUC = 25;		-- chance (%), par vassal du sang, qu'il brise son serment (mécanique B)

local function est_le_duc(c)
	return c and not c:is_null_interface() and c:character_subtype_key() == "wh_dlc05_vmp_red_duke"
		and c:faction():name() == MOUSILLON and c:faction():is_human() and c:has_military_force();
end;

local function degre_faveur()
	return cm:get_saved_value(PREFIXE .. "faveur_degre") or 0;
end;

-- pose le paquet du degré voulu sur l'armée du Duc (0 : retire tout)
local function poser_faveur(chef, degre)
	local force = chef:military_force();
	local cqi = force:command_queue_index();
	local ancienne = cm:get_saved_value(PREFIXE .. "faveur_force");
	if ancienne then
		cm:remove_effect_bundle_from_force(FAVEUR, ancienne);
	end;
	if degre <= 0 then
		cm:set_saved_value(PREFIXE .. "faveur_force", false);
		cm:set_saved_value(PREFIXE .. "faveur_degre", 0);
		cm:remove_character_vfx(chef:command_queue_index(), "scripted_effect");
		return true;
	end;
	local v = DEGRES_FAVEUR[math.min(degre, #DEGRES_FAVEUR)];
	local b = paquet(FAVEUR, {{"wh_main_effect_force_stat_melee_attack", "force_to_force_own", v},
		{"wh_main_effect_force_stat_leadership", "force_to_force_own", v}});
	if not b then
		return false;
	end;
	cm:apply_custom_effect_bundle_to_force(b, force);
	cm:set_saved_value(PREFIXE .. "faveur_force", cqi);
	cm:set_saved_value(PREFIXE .. "faveur_degre", degre);
	return true;
end;

local function monter_faveur(chef, contre_un_seigneur, resultat)
	local d = degre_faveur();
	local nouveau;
	if d == 0 then
		if cm:model():random_percent(CHANCES_FAVEUR[resultat] or 0) then
			nouveau = 1;
		end;
	elseif resultat == "heroic_victory" and contre_un_seigneur and d < #DEGRES_FAVEUR then
		nouveau = d + 1;
	end;
	if nouveau and poser_faveur(chef, nouveau) then
		if nouveau == 1 then
			cm:add_character_vfx(chef:command_queue_index(), "scripted_effect", false);
		end;
		annoncer((nouveau == #DEGRES_FAVEUR and "saison_duc_faveur_degre3") or "saison_duc_faveur_gagnee");
		out("La Saison des Revelations : faveur d'Abhorash, degre " .. nouveau);
	end;
end;

-- globale : appelée aussi par le tombeau de Galand, plus haut ; le bris est total
function saison_duc_retirer_faveur(chef, avec_message)
	if not est_le_duc(chef) or degre_faveur() <= 0 then
		return;
	end;
	poser_faveur(chef, 0);
	if avec_message then
		annoncer("saison_duc_faveur_perdue");
	end;
	out("La Saison des Revelations : faveur d'Abhorash perdue");
end;

-- au tour du Duc joué : l'usure, un degré de moins après USURE_FAVEUR tours sans bataille qu'il mène
local function user_la_faveur(duc)
	local d = degre_faveur();
	if d <= 0 then
		return;
	end;
	local derniere = cm:get_saved_value(PREFIXE .. "faveur_bataille") or cm:model():turn_number();
	if cm:model():turn_number() - derniere >= USURE_FAVEUR then
		local chef = duc:faction_leader();
		if est_le_duc(chef) then
			poser_faveur(chef, d - 1);
			cm:set_saved_value(PREFIXE .. "faveur_bataille", cm:model():turn_number());	-- le compte repart
			if d - 1 == 0 then
				annoncer("saison_duc_faveur_perdue");
			end;
			out("La Saison des Revelations : faveur d'Abhorash usee, degre " .. (d - 1));
		end;
	end;
end;

local function bataille_finie()
	local pb = cm:model():pending_battle();
	local ra, rd = pb:attacker_battle_result(), pb:defender_battle_result();
	if not ra or not rd or (ra == "close_defeat" and rd == "close_defeat") then
		return;	-- une retraite, pas une bataille (comme CA)
	end;
	-- le défi (section 7) relevé aussi quand le Duc combat en RENFORT et que son camp gagne (revue de la bêta,
	-- 25.09.2026 : seuls les deux chefs principaux étaient regardés)
	local mousillon = cm:get_faction(MOUSILLON);
	local duc = mousillon and not mousillon:is_dead() and mousillon:faction_leader();
	local principal = (pb:has_attacker() and est_le_duc(pb:attacker())) or (pb:has_defender() and est_le_duc(pb:defender()));
	if duc and est_le_duc(duc) and not principal and saison_duc_defi_releve then
		local resultat = (cm:pending_battle_cache_char_is_attacker(duc) and ra)
			or (cm:pending_battle_cache_char_is_defender(duc) and rd);
		if resultat and not DEFAITES[resultat] then
			saison_duc_defi_releve();
		end;
	end;
	for i, cote in ipairs({{pb:has_attacker() and pb:attacker(), ra}, {pb:has_defender() and pb:defender(), rd}}) do
		local chef, resultat = cote[1], cote[2];
		if est_le_duc(chef) then
			cm:set_saved_value(PREFIXE .. "faveur_bataille", cm:model():turn_number());
			if DEFAITES[resultat] then
				saison_duc_retirer_faveur(chef, true);
				-- la peur ne tient plus ses vassaux (mécanique B, plus bas)
				if saison_duc_serments_ebranles then
					saison_duc_serments_ebranles(RUPTURE_DEFAITE_DUC);
				end;
			else
				-- l'adversaire était-il mené par un seigneur ? (une garnison seule n'a pas de sous-type de général dans le
				-- cache des batailles de CA)
				local ok, sous_type;
				if i == 1 then
					ok, sous_type = pcall(function() return cm:pending_battle_cache_get_defender_subtype(1) end);
				else
					ok, sous_type = pcall(function() return cm:pending_battle_cache_get_attacker_subtype(1) end);
				end;
				monter_faveur(chef, ok and is_string(sous_type) and sous_type ~= "", resultat);
				-- le défi (section 7) : relevé si le défieur était dans cette bataille
				if saison_duc_defi_releve then
					saison_duc_defi_releve();
				end;
			end;
		end;
	end;
end;


-- 6. L'impôt du sang et le serment du sang (choix de Charles, 25.09.2026, mécanique B). Lore : l'impôt du sang de son
--	premier règne sur l'Aquitaine (The Red Duke ; dossier duc-9.0\lore, G1). Les vassaux du sang sont une mécanique
--	INSPIRÉE du lore (la noblesse corrompue qui le sert, R1, L1), pas une scène des livres. Le Duc joué seulement (des
--	dilemmes). Garde-fous voulus par Charles (« pas overcheaté ») : 2 vassaux au plus (3 une fois le duché restauré),
--	jamais l'Aquitanie (décret de Richemont), un vassal peut briser son serment (défaite du Duc, passage de la traque),
--	chaque vassal coûte de l'ordre public au Duc. Chiffres : choix de conception, à régler en jeu.
local POUVOIR, CADAVRES = "wh3_dlc29_vmp_power", "wh3_dlc29_vmp_corpses";
local CULTURE_BRETONNE = "wh_main_brt_bretonnia";
-- valeurs de l'étude d'équilibrage du 25.09.2026, validée par Charles : l'impôt vaut un Décret de sang (300) et environ six
-- unités de Zombies en cadavres ; épargner recule la traque de 2 tours ; la dîme pèse environ un cinquième du revenu au
-- tour 10 avec deux vassaux
local IMPOT = {sang = 300, cadavres = 1000, ordre = -6, duree = 5, traque = 3};
local EPARGNE = {ordre = 4, duree = 5, traque = 2};
local DIME = {sang = 40, cadavres = 60};
local VASSAUX_MAX, VASSAUX_MAX_RESTAURE = 2, 3;
local VASSAL_ORDRE = -1;			-- par vassal, dans les provinces du Duc
-- chances (%), par vassal, qu'il brise son serment : 25 à une défaite du Duc (RUPTURE_DEFAITE_DUC, section 5), 30 au
-- passage de la traque (lancer_traque, section 2)
local SERMENT_DELAI = 10;			-- tours avant de proposer de nouveau le même seigneur

-- avance (n < 0) ou recule (n > 0) la prochaine traque : la traque périodique et, s'il y en a une, la traque prévue après
-- la prise d'un domaine
local function decaler_traque(n)
	local dernier = cm:get_saved_value(PREFIXE .. "traque_tour") or (TRAQUE_PREMIER_TOUR - TRAQUE_DELAI);
	cm:set_saved_value(PREFIXE .. "traque_tour", dernier + n);
	local prevue = cm:get_saved_value(PREFIXE .. "traque_prevue");
	if prevue then
		cm:set_saved_value(PREFIXE .. "traque_prevue", prevue + n);
	end;
end;

local function duc_joue()
	local f = cm:get_faction(MOUSILLON);
	return f and not f:is_null_interface() and not f:is_dead() and f:is_human() and f or nil;
end;

local function ajouter_cadavres(faction, province, n)
	local prm = cm:get_or_create_faction_province_persistent_pooled_resource_manager(faction, province);
	if prm and not prm:is_null_interface() then
		local pr = prm:resource(CADAVRES);
		if pr and not pr:is_null_interface() then
			cm:pooled_resource_factor_transaction(pr, "hidden", n);
		end;
	end;
end;

local function liste_vassaux()
	local l = {};
	for cle in string.gmatch(cm:get_saved_value(PREFIXE .. "vassaux") or "", "[^,]+") do
		table.insert(l, cle);
	end;
	return l;
end;

local function poser_liste_vassaux(l)
	cm:set_saved_value(PREFIXE .. "vassaux", table.concat(l, ","));
	-- le prix des serments : l'ordre public du Duc, par vassal
	cm:remove_effect_bundle("saison_duc_vassaux_du_sang", MOUSILLON);
	if #l > 0 then
		local b = paquet("saison_duc_vassaux_du_sang",
			{{"wh_main_effect_public_order_faction", "faction_to_province_own", VASSAL_ORDRE * #l}});
		if b then
			cm:apply_custom_effect_bundle_to_faction(b, cm:get_faction(MOUSILLON));
		end;
	end;
end;

local function rompre_serment(cle)
	local l, reste = liste_vassaux(), {};
	for _, v in ipairs(l) do
		if v ~= cle then
			table.insert(reste, v);
		end;
	end;
	poser_liste_vassaux(reste);
	local f = cm:get_faction(cle);
	if f and not f:is_null_interface() and not f:is_dead() then
		cm:force_declare_war(cle, MOUSILLON, false, false);
		annoncer("saison_duc_vassal_rompt");
	end;
	out("La Saison des Revelations : serment du sang brise par " .. cle);
end;

-- globale : appelée à la défaite du Duc (faveur, plus haut) et au passage de la traque
function saison_duc_serments_ebranles(chance)
	for _, v in ipairs(liste_vassaux()) do
		if cm:model():random_percent(chance) then
			rompre_serment(v);
		end;
	end;
end;

-- l'impôt du sang : une région bretonnienne prise par le Duc joué
local function proposer_impot(region)
	local duc = duc_joue();
	if not duc then
		return;
	end;
	local db = cm:create_dilemma_builder("saison_duc_impot_du_sang");
	local pb = cm:create_payload();
	local leve = paquet("saison_duc_impot_leve",
		{{"wh_main_effect_public_order_events", "region_to_province_own_unseen", IMPOT.ordre}});
	if not db or not leve then
		return;	-- lots 34 et 35 absents du pack
	end;
	leve:set_duration(IMPOT.duree);
	pb:faction_pooled_resource_transaction(POUVOIR, "events", IMPOT.sang, false);
	pb:effect_bundle_to_region(region, leve);
	db:add_choice_payload("FIRST", pb);
	pb:clear();
	local epargne = paquet("saison_duc_vilains_epargnes",
		{{"wh_main_effect_public_order_events", "region_to_province_own_unseen", EPARGNE.ordre}});
	if not epargne then
		return;
	end;
	epargne:set_duration(EPARGNE.duree);
	pb:effect_bundle_to_region(region, epargne);
	db:add_choice_payload("SECOND", pb);
	db:add_target("default", region);
	-- une FILE des régions en attente de choix (revue de la bêta, M4 : deux prises au même tour, deux dilemmes ; la
	-- seconde écrasait la première et les cadavres du premier choix partaient dans la mauvaise province)
	local file = cm:get_saved_value(PREFIXE .. "impot_regions") or "";
	cm:set_saved_value(PREFIXE .. "impot_regions", file == "" and region:name() or (file .. ";" .. region:name()));
	cm:launch_custom_dilemma_from_builder(db, duc);
end;

-- le serment du sang : un seigneur bretonnien en guerre contre le Duc, réduit à une seule terre
local function proposer_serment(duc)
	local l = liste_vassaux();
	local max = (cm:get_saved_value(PREFIXE .. "duche_paquet") == "saison_duc_restaure") and VASSAUX_MAX_RESTAURE
		or VASSAUX_MAX;
	if #l >= max or not paquet("saison_duc_vassaux_du_sang", {}) then
		return;	-- plafond atteint, ou lots 34 et 35 absents du pack
	end;
	local tour = cm:model():turn_number();
	local factions = cm:model():world():faction_list();
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		local cle = f:name();
		if f:culture() == CULTURE_BRETONNE and not f:is_dead() and not f:is_human() and f:at_war_with(duc)
			and cle ~= "wh3_main_brt_aquitaine" and f:region_list():num_items() == 1
			and tour - (cm:get_saved_value(PREFIXE .. "serment_offert_" .. cle) or -99) >= SERMENT_DELAI then
			local db = cm:create_dilemma_builder("saison_duc_serment_du_sang");
			if not db then
				return;
			end;
			local pb = cm:create_payload();
			pb:text_display("dummy_vampire_lair_discovered");
			db:add_choice_payload("FIRST", pb);
			db:add_choice_payload("SECOND", pb);
			db:add_target("default", f:region_list():item_at(0));
			cm:set_saved_value(PREFIXE .. "serment_offert_" .. cle, tour);
			cm:set_saved_value(PREFIXE .. "serment_faction", cle);
			cm:launch_custom_dilemma_from_builder(db, duc);
			return;
		end;
	end;
end;

-- la première région de la file des impôts (proposer_impot), retirée de la file ; l'ancienne valeur unique
-- (parties d'avant le 25.09.2026, 19 h) est encore lue
local function region_d_impot_suivante()
	local file = cm:get_saved_value(PREFIXE .. "impot_regions") or "";
	if file == "" then
		return cm:get_saved_value(PREFIXE .. "impot_region") or "";
	end;
	local premiere, reste = file:match("^([^;]+);?(.*)$");
	cm:set_saved_value(PREFIXE .. "impot_regions", reste or "");
	return premiere or "";
end;

local function choix_fait(context)
	local dilemme, choix = context:dilemma(), context:choice();
	-- chaque dilemme d'impôt consomme sa région, quel que soit le choix
	local region_impot = dilemme == "saison_duc_impot_du_sang" and region_d_impot_suivante() or "";
	if dilemme == "saison_duc_impot_du_sang" and choix == 0 then
		local r = cm:get_region(region_impot);
		if r and not r:is_null_interface() then
			ajouter_cadavres(context:faction(), r:province(), IMPOT.cadavres);
		end;
		-- la traque de Richemont se hâte
		decaler_traque(-IMPOT.traque);
		out("La Saison des Revelations : impot du sang leve");
	elseif dilemme == "saison_duc_impot_du_sang" and choix == 1 then
		-- les vilains épargnés : la traque de Richemont s'attarde
		decaler_traque(EPARGNE.traque);
		out("La Saison des Revelations : vilains epargnes");
	elseif dilemme == "saison_duc_serment_du_sang" and choix == 0 then
		local cle = cm:get_saved_value(PREFIXE .. "serment_faction");
		local f = cle and cm:get_faction(cle);
		if f and not f:is_null_interface() and not f:is_dead() then
			cm:force_make_peace(MOUSILLON, cle);
			cm:force_make_vassal(MOUSILLON, cle, false);
			local l = liste_vassaux();
			table.insert(l, cle);
			poser_liste_vassaux(l);
			out("La Saison des Revelations : serment du sang, " .. cle .. " vassal du Duc ecarlate");
		end;
	end;
end;

-- au tour du Duc joué : la dîme des vassaux (et le retrait de ceux qui ne le sont plus), puis un serment à proposer
local function tour_des_vassaux(duc)
	local l, restent = liste_vassaux(), {};
	for _, cle in ipairs(l) do
		local f = cm:get_faction(cle);
		if f and not f:is_null_interface() and not f:is_dead() and f:is_vassal_of(duc) then
			table.insert(restent, cle);
			cm:faction_add_pooled_resource(MOUSILLON, POUVOIR, "events", DIME.sang);
			if duc:has_home_region() then
				ajouter_cadavres(duc, duc:home_region():province(), DIME.cadavres);
			end;
		end;
	end;
	if #restent ~= #l then
		poser_liste_vassaux(restent);
	end;
	proposer_serment(duc);
end;


-- 7. Le défi (choix de Charles, 25.09.2026, mécanique E ; étude duc-9.0\duel\rapport.md, voie A + B). Lore : le code des
--	Dragons de sang, toujours lancer et accepter les défis (Vampire Counts 6e, p. 52) ; au second Pré de Ceren, le Duc
--	refusa celui du duc Gilon (dossier duc-9.0\lore). Un seigneur bretonnien en armée, en guerre contre le Duc joué et
--	proche de lui, le défie : mission à deux objectifs, sa chute (ELIMINATE_CHARACTER_IN_BATTLE, qui le montre au
--	joueur) et une victoire du Duc EN PERSONNE contre lui (SCRIPTED, complété ici). Relevé : or (charge de la mission) et
--	Puissance ; dérobé (délai passé) : la faveur d'Abhorash brisée et les serments des vassaux ébranlés. Le défieur tombé
--	sous d'autres coups : défi annulé, sans peine. En 9.0, la mission (objectif SCRIPTED) s'enregistre au déclenchement :
--	l'enregistrement du défi précédent est retiré avant d'en émettre un autre (même clé). Chiffres : choix de
--	conception, à régler en jeu.
local DEFI, DEFI_OBJECTIF = "saison_duc_defi", "saison_duc_defi_en_personne";
local DEFI_PREMIER_TOUR = 6;
local DEFI_DELAI = 8;			-- tours pour relever le défi
local DEFI_REPOS = 10;			-- tours entre la fin d'un défi et le suivant
local DEFI_PORTEE = 25;			-- distance (cases) du défieur au Duc
local DEFI_OR, DEFI_SANG = 1500, 150;
local DEFI_RUPTURE = 25;		-- chance (%), par vassal du sang, qu'il brise son serment quand le Duc se dérobe

local function cible_dans_la_bataille(cqi)
	for i = 1, cm:pending_battle_cache_num_attackers() do
		if cm:pending_battle_cache_get_attacker(i) == cqi then
			return true;
		end;
	end;
	for i = 1, cm:pending_battle_cache_num_defenders() do
		if cm:pending_battle_cache_get_defender(i) == cqi then
			return true;
		end;
	end;
	return false;
end;

-- globale : appelée par bataille_finie (section 5, plus haut) quand le Duc a gagné une bataille
function saison_duc_defi_releve()
	local cible = cm:get_saved_value(PREFIXE .. "defi_cible");
	if cible and cible_dans_la_bataille(cible) then
		cm:set_saved_value(PREFIXE .. "defi_releve", true);
		cm:complete_scripted_mission_objective(MOUSILLON, DEFI, DEFI_OBJECTIF, true);
		out("La Saison des Revelations : defi releve par le Duc en personne");
	end;
end;

local function chercher_defieur(duc, chef)
	local x, y = chef:logical_position_x(), chef:logical_position_y();
	local meilleur, meilleure_d;
	local factions = cm:model():world():faction_list();
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		if f:culture() == CULTURE_BRETONNE and not f:is_dead() and f:at_war_with(duc) and not string.find(f:name(), "_qb") then
			local persos = f:character_list();
			for j = 0, persos:num_items() - 1 do
				local c = persos:item_at(j);
				if cm:char_is_general_with_army(c) and not c:is_wounded() then
					local dx, dy = c:logical_position_x() - x, c:logical_position_y() - y;
					local d = dx * dx + dy * dy;
					if d <= DEFI_PORTEE * DEFI_PORTEE and (not meilleure_d or d < meilleure_d) then
						meilleur, meilleure_d = c, d;
					end;
				end;
			end;
		end;
	end;
	return meilleur;
end;

local function fin_du_defi()
	cm:set_saved_value(PREFIXE .. "defi_cible", false);
	cm:set_saved_value(PREFIXE .. "defi_fin", cm:model():turn_number());
end;

-- au tour du Duc joué : le défi en cours (défieur tombé sous d'autres coups : annulé), sinon peut-être un nouveau
local function tour_du_defi(duc)
	local cible = cm:get_saved_value(PREFIXE .. "defi_cible");
	if cible then
		local c = cm:get_character_by_cqi(cible);
		-- défieur tombé SOUS D'AUTRES COUPS : annulé ; s'il a été battu par le Duc en personne (relevé), la mission
		-- suit son cours (revue de la bêta : un défieur seulement blessé par le Duc annulait le défi relevé)
		local releve = cm:get_saved_value(PREFIXE .. "defi_releve");
		if not releve and (not c or c:is_null_interface() or c:is_wounded() or not c:has_military_force()) then
			cm:cancel_custom_mission(MOUSILLON, DEFI);
			fin_du_defi();
			out("La Saison des Revelations : defi annule (le defieur n'est plus en campagne)");
		end;
		return;
	end;
	local tour = cm:model():turn_number();
	if tour < DEFI_PREMIER_TOUR or tour - (cm:get_saved_value(PREFIXE .. "defi_fin") or -99) < DEFI_REPOS then
		return;
	end;
	local chef = duc:faction_leader();
	if not est_le_duc(chef) then
		return;
	end;
	local defieur = chercher_defieur(duc, chef);
	if not defieur then
		return;
	end;
	-- revue de la bêta (25.09.2026) : en 9.0, trigger() enregistre toute mission à objectif SCRIPTED
	-- (lib_campaign_mission_manager.lua) ; le défi précédent reste enregistré sous la même clé, et un second
	-- enregistrement est refusé : on le retire d'abord
	local ancien = cm:get_mission_manager(MOUSILLON, DEFI);
	if ancien then
		cm:unregister_mission_manager(ancien);
	end;
	local mm = mission_manager:new(MOUSILLON, DEFI);
	if not mm then
		return;
	end;
	-- deux objectifs, une récompense : CA refuse une mission dont un objectif n'a pas de récompense, sauf si tous sont
	-- principaux (comme emettre, saison_chroniques.lua ; erreur B1 du 23.09.2026)
	mm:set_all_objectives_are_primary();
	mm:add_new_objective("ELIMINATE_CHARACTER_IN_BATTLE");
	mm:add_condition("character " .. defieur:command_queue_index());
	mm:add_condition("faction " .. defieur:faction():name());
	mm:add_new_objective("SCRIPTED");
	mm:add_condition("script_key " .. DEFI_OBJECTIF);
	mm:add_condition("override_text mission_text_text_" .. DEFI_OBJECTIF);
	mm:add_payload("money " .. DEFI_OR);
	mm:set_turn_limit(DEFI_DELAI);
	mm:set_should_whitelist(false);
	if mm:trigger() == false then
		out("La Saison des Revelations : defi non emis (mission refusee)");
		return;
	end;
	cm:set_saved_value(PREFIXE .. "defi_cible", defieur:command_queue_index());
	cm:set_saved_value(PREFIXE .. "defi_releve", false);
	out("La Saison des Revelations : defi lance par " .. defieur:faction():name() .. " (cqi "
		.. defieur:command_queue_index() .. ")");
end;

local function defi_fini(context, reussi)
	if reussi then
		cm:faction_add_pooled_resource(MOUSILLON, POUVOIR, "events", DEFI_SANG);
	else
		-- le Duc s'est dérobé : le code des Dragons de sang est rompu
		local duc = cm:get_faction(MOUSILLON);
		if duc and not duc:is_null_interface() then
			saison_duc_retirer_faveur(duc:faction_leader(), true);
		end;
		saison_duc_serments_ebranles(DEFI_RUPTURE);
	end;
	fin_du_defi();
	out("La Saison des Revelations : defi " .. (reussi and "remporte" or "derobe"));
end;


-- 8. Le trait de faction « Tyran d'Aquitanie » (demande de Charles, 25.09.2026, 17 h 50 ; lot 42). CA ne donne aucun trait
-- au Duc, et une ligne de faction_starting_general_effects vaudrait aux Empires : le paquet est posé ici, une fois par
-- partie, dans notre seule campagne. Modèle des traits vampires de la 9.0 (Neferata, Vlad) : « Vampire légendaire », des
-- lignes « A accès à … » (lot 42), puis des effets de CA. Lore (duc-9.0\lore\dossier.md) : haine de la Bretonnie et
-- décret de Richemont (L3, R6) ; « légions sans mort », morts relevés, chauves-souris en avant-garde au second Pré de
-- Ceren (L2) ; chevaliers noirs et garde des cryptes, unités que CA lui attache (L4). Le Duc de l'IA n'a que les lignes
-- des mécaniques qui valent pour lui (le duché perdu).
local TRAIT = "saison_lord_trait_duc";
local EFFETS_DU_TRAIT = {
	{"wh3_main_vmp_effect_legendary_vampire_dummy", "faction_to_faction_own_unseen", 1},
	{"saison_duc_effect_duche_perdu_dummy", "faction_to_faction_own_unseen", 1},
	{"saison_duc_effect_faveur_abhorash_dummy", "faction_to_faction_own_unseen", 1, joueur = true},
	{"saison_duc_effect_impot_du_sang_dummy", "faction_to_faction_own_unseen", 1, joueur = true},
	{"saison_duc_effect_decret_de_richemont_dummy", "faction_to_faction_own_unseen", 1, joueur = true},
	-- effet de WH1 (Royaume des Elfes sylvains), valeur et portée de CA
	{"wh_dlc05_faction_political_diplomacy_mod_bretonnia", "faction_to_faction_own", -20},
	-- portée de CA (bâtiment de Merovech, Mousillon : −5) ; valeur : choix de conception
	{"wh_main_effect_tech_upkeep_reduction_black_knights_grave_guard", "faction_to_force_own", -10},
	-- attribut de la 9.0 ; portée à vérifier en jeu (celle des attributs des traits de CA)
	{"wh3_dlc29_effect_attribute_enable_stalk_carrions_bats", "faction_to_force_own", 1},
};

local function trait_du_duc(f)
	if cm:get_saved_value(PREFIXE .. "trait") or f:is_dead() then
		return;
	end;
	local b = cm:create_new_custom_effect_bundle(TRAIT);
	if not b then
		out("La Saison des Revelations : trait du Duc absent du pack (lot 42), rien de pose");
		return;
	end;
	b:set_duration(0);
	for _, e in ipairs(EFFETS_DU_TRAIT) do
		if f:is_human() or not e.joueur then
			b:add_effect(e[1], e[2], e[3]);
		end;
	end;
	cm:apply_custom_effect_bundle_to_faction(b, f);
	cm:set_saved_value(PREFIXE .. "trait", true);
	out("La Saison des Revelations : trait du Duc pose (Tyran d'Aquitanie, " .. (f:is_human() and "joueur" or "IA") .. ")");
end;


-- 9. Les Régiments de Renom des Comtes vampires pour Mousillon, par script (première mise à jour de la bêta, 25.09.2026 ;
-- Charles : « que tout cohabite »). Avant : une ligne de faction_to_mercenary_set_junctions (lot 13) donnait la réserve
-- wh_dlc04_vmp_units_of_renown_pool à Mousillon dans TOUTES les campagnes, Empires compris. Désormais, dans notre seule
-- campagne, une fois par partie, les dix groupes de cette réserve (mercenary_pool_to_groups_junctions de CA : unité,
-- groupe, 1 exemplaire), avec la source et le réapprovisionnement de CA (mercenary_unit_groups : max 1, 0,1 par tour,
-- 100 %), par la fonction que CA emploie pour ses propres réserves (wh3_campaign_kislev_motherland.lua l. 345,
-- wh2_twa03_rakarth.lua l. 639). Le niveau de seigneur requis est porté par l'unité
-- (campaign_mercenary_unit_character_level_restrictions) : il vaut toujours. À VOIR EN JEU : le panneau des Régiments de
-- Renom du Duc joué (unités, coût, niveau requis).
local RESERVE_RENOM = "wh_dlc04_vmp_units_of_renown_pool";
local REGIMENTS_DE_RENOM = {
	"wh_dlc04_vmp_cav_chillgheists_0", "wh_dlc04_vmp_cav_vereks_reavers_0", "wh_dlc04_vmp_inf_feasters_in_the_dusk_0",
	"wh_dlc04_vmp_inf_konigstein_stalkers_0", "wh_dlc04_vmp_inf_sternsmen_0", "wh_dlc04_vmp_inf_tithe_0",
	"wh_dlc04_vmp_mon_devils_swartzhafen_0", "wh_dlc04_vmp_veh_claw_of_nagash_0", "wh_dlc04_vmp_mon_direpack_0",
	"wh2_dlc11_cst_mon_mournguls_ror_0",
};

local function regiments_de_renom(f)
	if cm:get_saved_value(PREFIXE .. "regiments_de_renom") or f:is_dead() then
		return;
	end;
	cm:set_saved_value(PREFIXE .. "regiments_de_renom", true);
	for _, unite in ipairs(REGIMENTS_DE_RENOM) do
		-- (faction, unité, source, nombre, chance de réapprovisionnement, maximum, par tour, restrictions de faction,
		-- de sous-culture, de technologie, réapprovisionnement partiel, groupe) : ordre de CA
		cm:add_unit_to_faction_mercenary_pool(f, unite, RESERVE_RENOM, 1, 100, 1, 0.1, "", "", "", true, unite);
	end;
	out("La Saison des Revelations : " .. #REGIMENTS_DE_RENOM .. " Regiments de Renom donnes a " .. MOUSILLON);
end;


-- Appelé par saison_start.lua à chaque chargement, après les systèmes vampires de la 9.0.
function saison_duc_demarrer()
	local f = cm:get_faction(MOUSILLON);
	if not f or f:is_null_interface() then
		return;
	end;
	baiser_d_abhorash();
	saison_sur("trait du Duc", trait_du_duc, f);
	saison_sur("regiments de renom de Mousillon", regiments_de_renom, f);
	-- le duché perdu : dès le chargement, puis à chaque changement de main d'un domaine d'Aquitaine
	saison_sur("duche perdu", mettre_a_jour_duche, f);
	saison_ecouteur(PREFIXE .. "duche_change", "RegionFactionChangeEvent",
		function(context)
			local r = context:region():name();
			for _, cle in ipairs(AQUITAINE) do
				if cle == r then
					return true;
				end;
			end;
			return false;
		end,
		function()
			local duc = cm:get_faction(MOUSILLON);
			if duc and not duc:is_null_interface() and not duc:is_dead() then
				mettre_a_jour_duche(duc);
			end;
		end,
		true);
	-- l'impôt du sang (région bretonnienne prise par le Duc joué) et le serment du sang (choix des dilemmes)
	saison_ecouteur(PREFIXE .. "impot", "RegionFactionChangeEvent",
		function(context)
			local r, avant = context:region(), context:previous_faction();
			return duc_joue() ~= nil and not r:is_abandoned() and r:owning_faction():name() == MOUSILLON
				and avant and not avant:is_null_interface() and avant:culture() == CULTURE_BRETONNE;
		end,
		function(context) proposer_impot(context:region()) end,
		true);
	saison_ecouteur(PREFIXE .. "dilemmes", "DilemmaChoiceMadeEvent",
		function(context) return context:faction():name() == MOUSILLON end,
		choix_fait,
		true);
	-- la faveur d'Abhorash
	saison_ecouteur(PREFIXE .. "faveur_bataille", "BattleCompleted", true, bataille_finie, true);
	saison_ecouteur(PREFIXE .. "faveur_retraite", "CharacterWithdrewFromBattle",
		function(context) return est_le_duc(context:character()) end,
		function(context) saison_duc_retirer_faveur(context:character(), true) end,
		true);
	-- le défi (section 7)
	saison_ecouteur(PREFIXE .. "defi_reussi", "MissionSucceeded",
		function(context) return context:mission():mission_record_key() == DEFI and context:faction():name() == MOUSILLON end,
		function(context) defi_fini(context, true) end,
		true);
	saison_ecouteur(PREFIXE .. "defi_echoue", "MissionFailed",
		function(context) return context:mission():mission_record_key() == DEFI and context:faction():name() == MOUSILLON end,
		function(context) defi_fini(context, false) end,
		true);
	-- FactionBeginTurnPhaseNormal et non FactionTurnStart (24.09.2026, 23 h 20 : voir saison_foret.lua, Racines du monde)
	core:add_listener(
		PREFIXE .. "tour",
		"FactionBeginTurnPhaseNormal",
		function(context) return context:faction():name() == MOUSILLON end,
		function(context)
			local faction = context:faction();
			saison_sur("tombeau de Galand", tombeau_de_galand, faction);
			if faction:is_human() then
				-- interrupteur d'essai (revue de la bêta, M10 : payload_builder:effect_bundle_to_region et
				-- dilemma_builder:add_target ne sont employés par aucun script de CA) : _G.saison_essai_impot_duc, posé
				-- par le pack d'essai de la construction, propose l'impôt du sang au tour 2 sur une région bretonne,
				-- sans la prendre ; le journal dit ce qui passe
				if _G.saison_essai_impot_duc == true and cm:model():turn_number() >= 2
					and not cm:get_saved_value(PREFIXE .. "essai_impot_fait") then
					cm:set_saved_value(PREFIXE .. "essai_impot_fait", true);
					saison_sur("essai de l'impot du sang", function()
						local regions = cm:model():world():region_manager():region_list();
						for i = 0, regions:num_items() - 1 do
							local r = regions:item_at(i);
							if not r:is_abandoned() and r:owning_faction():culture() == CULTURE_BRETONNE then
								out("La Saison des Revelations : [ESSAI IMPOT] dilemme propose sur " .. r:name());
								proposer_impot(r);
								return;
							end;
						end;
						out("La Saison des Revelations : [ESSAI IMPOT] aucune region bretonne");
					end);
				end;
				saison_sur("vassaux du sang", tour_des_vassaux, faction);
				saison_sur("usure de la faveur", user_la_faveur, faction);
				saison_sur("defi", tour_du_defi, faction);
				local tour = cm:model():turn_number();
				-- 25.09.2026 : sans traque passée, la « dernière » valait 0 et la première partait au tour 10 au lieu du 8
				local dernier = cm:get_saved_value(PREFIXE .. "traque_tour") or (TRAQUE_PREMIER_TOUR - TRAQUE_DELAI);
				local prevue = cm:get_saved_value(PREFIXE .. "traque_prevue");
				if (tour >= TRAQUE_PREMIER_TOUR and tour - dernier >= TRAQUE_DELAI) or (prevue and tour >= prevue) then
					saison_sur("traque de Richemont", lancer_traque, faction);
				end;
			end;
		end,
		true
	);
end;
