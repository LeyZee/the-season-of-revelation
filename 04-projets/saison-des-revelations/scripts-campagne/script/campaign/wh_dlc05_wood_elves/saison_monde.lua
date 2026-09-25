-----------------------------------------------------------------------------------
--	La Saison des Révélations : les ducs de la carte portent leur nom de lore.
--
--	Les chefs des duchés tenus par l'IA sont des seigneurs génériques (startpos de WH1) ; le lore leur donne un nom
--	(livre d'armée de Bretonnie, 6e éd. ; Knights of the Grail) : Tancred II de Quenelles, qui lève sans cesse des osts
--	contre le Massif Orcal ; Armand d'Aquitaine ; Bohémond de Bastonne ; Folcard de Montfort ; Cassyon de Parravon ;
--	Théodoric de Brionne ; Hagen de Gisoreux ; et Darthon Barbe de Fer, seigneur nain des Montagnes Grises (citation de
--	chargement de CA), à Karak Ziflin. Prénoms : table names de CA ; noms de famille « de <duché> » et « Darthon » :
--	nos lignes (lot 14 de donnees_campagne.py, fréquence 0 : jamais tirés au hasard). Une seule fois, au premier tour
--	d'une partie neuve ; seulement si le chef est un seigneur générique (jamais un seigneur légendaire).
-----------------------------------------------------------------------------------

local VIDE = "names_name_2147358938";		-- nom vide de CA (wh3_campaign_character_upgrading.lua)

-- faction -> {sous-type attendu du chef, prénom, nom}
local DUCS = {
	wh_dlc05_brt_quenelles = {"wh_main_brt_lord", "names_name_645127004", "names_name_578028567"},	-- Tancred II de Quenelles (lot 14)
	wh3_main_brt_aquitaine = {"wh_main_brt_lord", "names_name_2147345378", "names_name_167863795"},	-- Armand d'Aquitaine
	wh_main_brt_bastonne = {"wh_main_brt_lord", "names_name_2147345384", "names_name_433068992"},		-- Bohémond de Bastonne
	wh_dlc05_brt_montfort = {"wh_main_brt_lord", "names_name_2147352490", "names_name_1496308970"},		-- Folcard de Montfort
	wh_main_brt_parravon = {"wh_main_brt_lord", "names_name_2147345878", "names_name_412763886"},		-- Cassyon de Parravon
	wh_dlc05_brt_brionne = {"wh_main_brt_lord", "names_name_2147352626", "names_name_593790985"},		-- Théodoric de Brionne
	wh_dlc05_brt_gisoroux = {"wh_main_brt_lord", "names_name_2147352525", "names_name_375345544"},		-- Hagen de Gisoreux
	wh_main_dwf_karak_ziflin = {"wh_main_dwf_lord", "names_name_1293672490", "names_name_2147344288"}		-- Darthon Barbe de Fer
};


-- Le Duc Rouge : « Le Duc écarlate » dans le français de CA ; notre nom (lot 14), joué ou non.
local DUC_ROUGE = "names_name_1218116301";


-- Audit des factions (23.09.2026), point 1 : aucune de nos régions ne démarre avec un point de surplus de population
-- (start_pos_regions.development_points = 0) ; aux Empires, CA en donne 1 aux capitales des grandes factions. Sans lui,
-- une faction d'une seule province (Durthu, Drycha, Kemmler) ne monte pas sa colonie principale de niveau et l'or
-- s'entasse. Partie neuve seulement.
local CAPITALES_JOUABLES = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_argwylon", "wh_main_brt_bordeleaux",
	"wh_main_brt_carcassonne", "wh_main_vmp_mousillon", "wh2_dlc16_wef_drycha", "wh2_dlc11_vmp_the_barrow_legion",
	"wh2_dlc15_grn_broken_axe"};

function saison_surplus_capitales()
	for i = 1, #CAPITALES_JOUABLES do
		local f = cm:get_faction(CAPITALES_JOUABLES[i]);
		if f and not f:is_dead() and f:has_home_region() then
			cm:add_development_points_to_region(f:home_region():name(), 1);
		end;
	end;
	out("La Saison des Revelations : un point de surplus de population aux capitales jouables");
end;


-- Héros de départ collés à leur seigneur (Charles, 24.09.2026 : même case, peu lisible) : nos héros de départ sont posés
-- à 1 ou 2 cases de leur seigneur (lot 13), quand CA les met aux Empires à 3 à 6 cases (médiane 5, relevé de
-- start_pos_characters sur 105 héros). En partie neuve, chaque héros non intégré à une armée, à 2 cases ou moins d'un
-- général de sa faction, est déplacé sur une case franchissable à la distance de CA la plus courte (3), par la
-- recherche de case valide de CA (même région de préférence).
local HEROS_DISTANCE_MIN = 2.5;
local HEROS_DISTANCE_VOULUE = 3;
local FACTIONS_A_HEROS = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_argwylon", "wh_main_brt_bordeleaux",
	"wh_main_brt_carcassonne", "wh_dlc05_bst_morghur_herd", "wh_main_vmp_mousillon", "wh2_dlc16_wef_drycha",
	"wh2_dlc11_vmp_the_barrow_legion", "wh2_dlc15_grn_broken_axe", "wh2_dlc16_wef_sisters_of_twilight"};

function saison_ecarter_les_heros()
	local n = 0;
	for _, cle in ipairs(FACTIONS_A_HEROS) do
		local f = cm:get_faction(cle);
		if f and not f:is_null_interface() and not f:is_dead() then
			local persos = f:character_list();
			local generaux = {};
			for i = 0, persos:num_items() - 1 do
				local c = persos:item_at(i);
				if c:character_type("general") and c:has_military_force() then
					table.insert(generaux, c);
				end;
			end;
			for i = 0, persos:num_items() - 1 do
				local h = persos:item_at(i);
				if cm:char_is_agent(h) and not h:is_embedded_in_military_force() then
					local hx, hy = h:logical_position_x(), h:logical_position_y();
					for _, g in ipairs(generaux) do
						local gx, gy = g:logical_position_x(), g:logical_position_y();
						if math.sqrt((hx - gx) ^ 2 + (hy - gy) ^ 2) <= HEROS_DISTANCE_MIN then
							local x, y = cm:find_valid_spawn_location_for_character_from_position(cle, hx, hy, true,
								HEROS_DISTANCE_VOULUE);
							if x == -1 then
								x, y = cm:find_valid_spawn_location_for_character_from_position(cle, hx, hy, false,
									HEROS_DISTANCE_VOULUE);
							end;
							if x ~= -1 and y ~= -1 and not (x == gx and y == gy) then
								cm:teleport_to(cm:char_lookup_str(h), x, y);
								n = n + 1;
							end;
							break;
						end;
					end;
				end;
			end;
		end;
	end;
	out("La Saison des Revelations : " .. n .. " heros de depart ecartes de leur seigneur");
end;


function saison_nommer_les_ducs()
	for faction, d in pairs(DUCS) do
		local f = cm:get_faction(faction);
		if f and not f:is_dead() and not f:is_human() and f:has_faction_leader() then
			local chef = f:faction_leader();
			if not chef:is_null_interface() and chef:character_subtype_key() == d[1] then
				cm:change_character_localised_name(chef, d[2], d[3], VIDE, VIDE);
			end;
		end;
	end;
	local mousillon = cm:get_faction("wh_main_vmp_mousillon");
	if mousillon and not mousillon:is_dead() then
		local liste = mousillon:character_list();
		for i = 0, liste:num_items() - 1 do
			local c = liste:item_at(i);
			if c:character_subtype_key() == "wh_dlc05_vmp_red_duke" then
				cm:change_character_localised_name(c, DUC_ROUGE, VIDE, VIDE, VIDE);
			end;
		end;
	end;
	out("La Saison des Revelations : ducs nommes selon le lore");
end;
