-----------------------------------------------------------------------------------
--	La Saison des Révélations : les Asrai relèvent leurs salles (décision de Charles, 23.09.2026, 19 h).
--
--	Essais automatiques : les Elfes sylvains de l'IA (Durthu, les clairières, Orion non joué) restent sur leurs terres,
--	ce qui est leur lore (ils gardent Athel Loren et n'en sortent guère), mais ne reprennent jamais les cinq salles
--	tombées de LEUR forêt (Threllock, Tal Rond, l'Enclume de Vaul, Tal Jul-finel, Tal Eth Ayr), et l'or s'entasse.
--	Ici, une faction elfe de l'IA qui a de quoi payer, et aucune armée ennemie près de la salle, la relève : la région
--	lui revient contre de l'or (le prix d'une colonisation). Jamais hors d'Athel Loren, jamais pour Drycha (esprit
--	hostile aux Asrai), jamais pour un joueur. Une salle à la fois, au plus tous les 8 tours par faction, dès le tour 8.
--	Choix de conception (pas de lore) : prix, délais, rayon.
-----------------------------------------------------------------------------------

local PREFIXE = "saison_salles_";
local CULTURE = "wh_dlc05_wef_wood_elves";
local EXCLUES = {wh2_dlc16_wef_drycha = true};
local SALLES = {"wh_dlc05_fyr_darric_threllock", "wh_dlc05_anmyr_tal_rond", "wh_dlc05_torgovann_vauls_anvil",
	"wh_dlc05_wydrioth_tal_jul_finel", "wh_dlc05_talsyn_tal_eth_ayr"};
local PRIX = 2500;
local OR_MINIMUM = 4000;
local TOUR_MINIMUM = 8;
local DELAI = 8;
local RAYON = 12;		-- aucune armée ennemie à moins de 12 cases de la colonie
-- Salles gardées pour un seigneur JOUÉ (bilan d'équilibrage du 25.09.2026) : celles de ses objectifs, que l'IA ne relève
-- jamais à sa place (saison_victoires_9_0.lua : Durthu Threllock et l'Enclume de Vaul, les Sœurs Tal Jul-Finel, leur
-- capitale à relever, et l'Enclume ; Drycha Tal Rond, pour Addaivoch ; Orion Tal Eth Ayr, sa salle de départ, et 3 salles
-- sur 5 à sa longue). Si un seigneur joué a besoin de salles, l'IA attend aussi le tour TOUR_MINIMUM_JOUEUR.
local RESERVEES = {
	-- Orion : les cinq, car sa victoire en exige 3 sur 5 (revue de la bêta, 25.09.2026 : avec la seule Tal Eth Ayr
	-- gardée, les elfes de l'IA relevaient les quatre autres dès le tour 20)
	wh_dlc05_wef_wood_elves = {"wh_dlc05_talsyn_tal_eth_ayr", "wh_dlc05_fyr_darric_threllock", "wh_dlc05_anmyr_tal_rond",
		"wh_dlc05_torgovann_vauls_anvil", "wh_dlc05_wydrioth_tal_jul_finel"},
	wh_dlc05_wef_argwylon = {"wh_dlc05_fyr_darric_threllock", "wh_dlc05_torgovann_vauls_anvil"},
	wh2_dlc16_wef_sisters_of_twilight = {"wh_dlc05_wydrioth_tal_jul_finel", "wh_dlc05_torgovann_vauls_anvil"},
	wh2_dlc16_wef_drycha = {"wh_dlc05_anmyr_tal_rond"}
};
local TOUR_MINIMUM_JOUEUR = 20;

-- vrai si un seigneur joué garde cette salle (cle), ou, sans cle, si un seigneur joué a des salles gardées
local function gardee(cle)
	local humains = cm:get_human_factions();
	for i = 1, #humains do
		local liste = RESERVEES[humains[i]];
		if liste then
			if not cle then
				return true;
			end;
			for _, c in ipairs(liste) do
				if c == cle then
					return true;
				end;
			end;
		end;
	end;
	return false;
end;


local function ennemi_proche(faction, region)
	local s = region:settlement();
	if s:is_null_interface() then
		return true;
	end;
	local sx, sy = s:logical_position_x(), s:logical_position_y();
	local guerres = faction:factions_at_war_with();
	for i = 0, guerres:num_items() - 1 do
		local forces = guerres:item_at(i):military_force_list();
		for j = 0, forces:num_items() - 1 do
			local mf = forces:item_at(j);
			if mf:has_general() then
				local c = mf:general_character();
				local dx, dy = c:logical_position_x() - sx, c:logical_position_y() - sy;
				if dx * dx + dy * dy <= RAYON * RAYON then
					return true;
				end;
			end;
		end;
	end;
	return false;
end;


-- une salle tombée voisine d'une région de la faction
local function salle_voisine(faction)
	local regions = faction:region_list();
	for _, cle in ipairs(SALLES) do
		local salle = cm:get_region(cle);
		if salle and salle:is_abandoned() and not gardee(cle) then
			local voisines = salle:adjacent_region_list();
			for i = 0, voisines:num_items() - 1 do
				local v = voisines:item_at(i);
				if not v:is_abandoned() and v:owning_faction():name() == faction:name() then
					return salle;
				end;
			end;
		end;
	end;
	return nil;
end;


local function relever(faction)
	local nom = faction:name();
	local tour = cm:model():turn_number();
	local dernier = cm:get_saved_value(PREFIXE .. nom);
	local minimum = gardee() and TOUR_MINIMUM_JOUEUR or TOUR_MINIMUM;
	if tour < minimum or (is_number(dernier) and tour - dernier < DELAI) or faction:treasury() < OR_MINIMUM then
		return;
	end;
	local salle = salle_voisine(faction);
	if not salle or ennemi_proche(faction, salle) then
		return;
	end;
	cm:set_saved_value(PREFIXE .. nom, tour);
	cm:transfer_region_to_faction(salle:name(), nom);
	cm:treasury_mod(nom, -PRIX);
	out("La Saison des Revelations : " .. nom .. " releve la salle tombee " .. salle:name() .. " (" .. PRIX .. " or)");
end;


function saison_salles_demarrer()
	core:add_listener(
		PREFIXE .. "debut_de_tour",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local f = context:faction();
			return not f:is_human() and f:culture() == CULTURE and not EXCLUES[f:name()] and not f:is_dead();
		end,
		function(context)
			saison_sur("salles des Asrai", relever, context:faction());
		end,
		true
	);
	out("La Saison des Revelations : les Asrai relevent leurs salles (IA elfe seulement)");
end;
