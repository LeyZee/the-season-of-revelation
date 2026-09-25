-----------------------------------------------------------------------------------
--	La Saison des Révélations : diagnostic des constructions (journal seulement, aucun effet sur la partie).
--
--	Essais automatiques de la construction (23.09.2026) : Kemmler, joué par l'IA, recrute et conquiert mais ne bâtit
--	presque rien (2 bâtiments en 30 tours, trois fois de suite, 21 819 d'or dormant) ; Mousillon, de la même culture,
--	bâtit. Tous les 5 tours, au début du tour de chaque faction suivie, le journal de script dit pour chacune de ses
--	régions les emplacements actifs, vides ou bâtis (clé du bâtiment), et son or : de quoi voir si l'IA manque de place
--	(colonies de niveau 1, emplacements inactifs) ou d'autre chose. Même lecture que building_logging.lua de CA.
-----------------------------------------------------------------------------------

-- 17 h 40 : aussi les Elfes de l'IA figés sur une région (Durthu, Drycha, Orion : or qui s'accumule) et Grom, très
-- instable d'une partie à l'autre (mort au tour 30 ou 7 régions)
local SUIVIES = {"wh2_dlc11_vmp_the_barrow_legion", "wh_main_vmp_mousillon", "wh_dlc05_wef_argwylon",
	"wh2_dlc16_wef_drycha", "wh_dlc05_wef_wood_elves", "wh2_dlc15_grn_broken_axe"};
local PAS = 5;


local function journal_constructions(faction)
	local regions = faction:region_list();
	-- de quoi s'étendre : ennemis en guerre, ruines voisines (colonisables)
	local guerres = faction:factions_at_war_with();
	local ennemis = {};
	for i = 0, guerres:num_items() - 1 do
		table.insert(ennemis, guerres:item_at(i):name());
	end;
	local ruines = {};
	for i = 0, regions:num_items() - 1 do
		local voisines = regions:item_at(i):adjacent_region_list();
		for j = 0, voisines:num_items() - 1 do
			if voisines:item_at(j):is_abandoned() then
				table.insert(ruines, voisines:item_at(j):name());
			end;
		end;
	end;
	out("[DIAG] constructions " .. faction:name() .. " tour " .. cm:model():turn_number() .. " : or "
		.. tostring(faction:treasury()) .. " ; " .. regions:num_items() .. " region(s) ; en guerre contre "
		.. #ennemis .. " (" .. table.concat(ennemis, ", ") .. ") ; ruines voisines : " .. table.concat(ruines, ", "));
	for i = 0, regions:num_items() - 1 do
		local region = regions:item_at(i);
		local slots = region:slot_list();
		local actifs, vides, batis = 0, 0, {};
		for j = 0, slots:num_items() - 1 do
			local slot = slots:item_at(j);
			if not slot:is_null_interface() and slot:active() then
				actifs = actifs + 1;
				if slot:has_building() then
					table.insert(batis, slot:building():name());
				else
					vides = vides + 1;
				end;
			end;
		end;
		out("[DIAG]   " .. region:name() .. " : " .. actifs .. " actif(s), " .. vides .. " vide(s) ; "
			.. table.concat(batis, ", "));
	end;
end;


function saison_diagnostic_constructions()
	core:add_listener(
		"saison_diagnostic_constructions",
		"FactionBeginTurnPhaseNormal",
		function(context)
			local nom = context:faction():name();
			if cm:model():turn_number() % PAS ~= 1 then
				return false;
			end;
			for i = 1, #SUIVIES do
				if SUIVIES[i] == nom then
					return true;
				end;
			end;
			return false;
		end,
		function(context)
			saison_sur("diagnostic des constructions", journal_constructions, context:faction());
		end,
		true
	);
end;


-- à chaque chargement, comme l'essai de corruption
cm:add_first_tick_callback(function() saison_sur("diagnostic des constructions", saison_diagnostic_constructions) end);
