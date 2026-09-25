-----------------------------------------------------------------------------------
--	Exploration de départ, comme dans Warhammer 1.
--
--	WH1 livrait dans son startpos une zone déjà explorée pour les deux factions jouables (enregistrement
--	CAMPAIGN_SHROUD, arbre quaternaire non décodé) ; le startpos de WH3 n'a rien de tel. Décision de Charles
--	(23.09.2026) : révéler au moins Athel Loren. Au premier tour d'une nouvelle partie, les 18 régions d'Athel Loren
--	(climat de forêt magique de la carte de WH1) sont marquées comme vues pour Orion et pour Durthu, avec la même
--	fonction que les chemins-racines des elfes de CA (cm:make_region_seen_in_shroud). Protégé par saison_sur
--	(saison_start.lua) : une erreur dans un rappel de partie neuve empêcherait le jeu de rendre la main au joueur.
--
--	Les huit autres seigneurs (décision de Charles, 24.09.2026, 03 h 30 : WH1 n'avait que deux factions jouables et ne
--	révélait rien d'autre) : leur terre d'origine, soit toutes les régions des provinces de leurs colonies de départ, la
--	région où se tient leur chef (seule terre des seigneurs sans colonie, Morghur et les Sœurs), et les régions voisines
--	de tout cela. Le reste de la carte reste sous le brouillard. Choix de conception, pas de lore.
-----------------------------------------------------------------------------------

-- Orion, Durthu, et depuis le 24.09.2026 (03 h 55, Charles) les deux figures d'Athel Loren sans colonie de départ, qui
-- ne voyaient que 3 régions : Drycha (esprit de la forêt) et les Sœurs du Crépuscule (Asrai de Wydrioth)
local FACTIONS_JOUABLES = {
	"wh_dlc05_wef_wood_elves",				-- Orion
	"wh_dlc05_wef_argwylon",				-- Durthu
	"wh2_dlc16_wef_drycha",					-- Drycha
	"wh2_dlc16_wef_sisters_of_twilight"		-- les Sœurs du Crépuscule
};

local REGIONS_ATHEL_LOREN = {
	"wh_dlc05_anmyr_halls_of_anaereth",
	"wh_dlc05_anmyr_tal_rond",
	"wh_dlc05_argwylon_waterfall_palace",
	"wh_dlc05_arranoc_tal_esth",
	"wh_dlc05_atylwyth_tal_amere",
	"wh_dlc05_cavaroc_halls_of_equos",
	"wh_dlc05_cythral_tyr_vanna",
	"wh_dlc05_fyr_darric_feast_halls",
	"wh_dlc05_fyr_darric_threllock",
	"wh_dlc05_modryn_glade_of_eternal_midnight",
	"wh_dlc05_oak_of_ages",
	"wh_dlc05_talsyn_tal_eth_ayr",
	"wh_dlc05_talsyn_yn_ecryl_koiran",
	"wh_dlc05_tirsyth_glade_of_eternal_moonlight",
	"wh_dlc05_torgovann_cromlech_cadai",
	"wh_dlc05_torgovann_vauls_anvil",
	"wh_dlc05_wydrioth_crag_halls",
	"wh_dlc05_wydrioth_tal_jul_finel"
};

local AUTRES_SEIGNEURS = {
	"wh_main_brt_bordeleaux",				-- Alberic
	"wh_main_brt_carcassonne",				-- la Fée Enchanteresse
	"wh_dlc05_bst_morghur_herd",			-- Morghur
	"wh_main_vmp_mousillon",				-- le Duc Rouge
	"wh2_dlc16_wef_drycha",					-- Drycha
	"wh2_dlc11_vmp_the_barrow_legion",		-- Heinrich Kemmler
	"wh2_dlc15_grn_broken_axe",				-- Grom la Panse
	"wh2_dlc16_wef_sisters_of_twilight"		-- les Sœurs du Crépuscule
};


-- clés des régions de la terre d'origine d'une faction, triées (même ordre sur toutes les machines)
local function terre_d_origine(faction)
	local vues = {};
	local function ajouter(region)
		if region and not region:is_null_interface() then
			vues[region:name()] = region;
		end;
	end;
	local regions = faction:region_list();
	for i = 0, regions:num_items() - 1 do
		local region = regions:item_at(i);
		ajouter(region);
		local province = region:province();
		if not province:is_null_interface() then
			local de_la_province = province:regions();
			for j = 0, de_la_province:num_items() - 1 do
				ajouter(de_la_province:item_at(j));
			end;
		end;
	end;
	if faction:has_faction_leader() then
		local chef = faction:faction_leader();
		if not chef:is_null_interface() and chef:has_region() then
			ajouter(chef:region());
		end;
	end;
	local noyau = {};
	for _, region in pairs(vues) do
		table.insert(noyau, region);
	end;
	for _, region in ipairs(noyau) do
		local voisines = region:adjacent_region_list();
		for i = 0, voisines:num_items() - 1 do
			ajouter(voisines:item_at(i));
		end;
	end;
	local cles = {};
	for cle in pairs(vues) do
		table.insert(cles, cle);
	end;
	table.sort(cles);
	return cles;
end;


cm:add_first_tick_callback_new(
	function()
		if saison_bloquee then
			return;
		end;
		saison_sur(
			"exploration de depart",
			function()
				for _, faction_key in ipairs(FACTIONS_JOUABLES) do
					for _, region_key in ipairs(REGIONS_ATHEL_LOREN) do
						cm:make_region_seen_in_shroud(faction_key, region_key);
					end;
				end;
				out("La Saison des Revelations : Athel Loren revelee a Orion, Durthu, Drycha et aux Soeurs (" .. #REGIONS_ATHEL_LOREN .. " regions)");
			end
		);
		saison_sur(
			"terres d'origine des autres seigneurs",
			function()
				for _, faction_key in ipairs(AUTRES_SEIGNEURS) do
					local faction = cm:get_faction(faction_key);
					if faction and not faction:is_dead() then
						local cles = terre_d_origine(faction);
						for _, region_key in ipairs(cles) do
							cm:make_region_seen_in_shroud(faction_key, region_key);
						end;
						out("La Saison des Revelations : terre d'origine revelee a " .. faction_key .. " (" .. #cles .. " regions)");
					end;
				end;
			end
		);
	end
);
