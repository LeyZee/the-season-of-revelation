-----------------------------------------------------------------------------------
--	Quêtes des seigneurs : les chaînes de la mini-campagne de WH1 (décision de Charles, 23.09.2026), émises par le
--	système de quêtes de WH3 (set_up_rank_up_listener de wh_campaign_setup.lua, comme q_setup des Empires) : au rang
--	requis, intervention, caméra et mission de la première étape ; les étapes suivantes s'enchaînent par les suites du
--	directeur de campagne (lot 4 des données, 18 missions sous les clés de WH1, bataille d'Ashenhall recréée).
--	Rangs de WH3 (table character_ancillary_quest_ui_details, la fiche de quête du personnage : 7, 12, 17 ; WH1 : 8, 13,
--	18).
--
--	Morghur, Alberic et la Fée Enchanteresse ont leurs quêtes de CA des Empires, recopiées pour notre carte : joués,
--	ils les suivent ; joués par l'IA, ils reçoivent leurs objets au rang voulu, comme aux Empires.
--	De même pour Drycha, Heinrich Kemmler et Grom la Panse (23.09.2026).
-----------------------------------------------------------------------------------

local QUETES = {
	["wh_dlc05_wef_orion"] = {
		{"mission", "wh_dlc05_anc_enchanted_item_horn_of_the_wild_hunt", "wh_dlc05_wef_orion_horn_of_the_wild_stage_1_mini", nil, "war.camp.advice.quests.001"},
		{"mission", "wh_dlc05_anc_talisman_cloak_of_isha", "wh_dlc05_wef_orion_cloak_of_isha_stage_1_mini"},
		{"mission", "wh_dlc05_anc_weapon_spear_of_kurnous", "wh_dlc05_wef_orion_spear_of_kurnous_stage_1_mini"}
	},
	["wh_dlc05_wef_durthu"] = {
		{"mission", "wh_dlc05_anc_weapon_daiths_sword", "wh_dlc05_wef_durthu_sword_of_daith_stage_1_mini", nil, "war.camp.advice.quests.001"}
	},
	-- Seigneurs de WH3 jouables sur notre carte (23.09.2026) : les quêtes de CA des Empires (wh_quests.lua), recopiées
	-- pour notre carte (lot 10 : Mousillon au lieu de Sartosa, nos emplacements, nos personnages). Joués par l'IA, ils
	-- reçoivent l'objet au rang (set_up_rank_up_listener de CA). Le Miroir de Morgiana (monument de Carcassonne à
	-- construire) reste un objet donné au rang (« reward »).
	["wh_dlc05_bst_morghur"] = {
		{"mission", "wh_main_anc_weapon_stave_of_ruinous_corruption", "saison_qb_bst_morghur_stave_of_ruinous_corruption",
			nil, "war.camp.advice.quests.001"}
	},
	["wh_dlc07_brt_alberic"] = {
		{"mission", "wh_dlc07_anc_weapon_trident_of_manann", "saison_qb_brt_alberic_trident_of_manann", nil,
			"war.camp.advice.quests.001"},
		{"mission", "wh2_dlc12_anc_enchanted_item_brt_braid_of_bordeleaux", "saison_qb_brt_alberic_braid_of_bordeleaux"}
	},
	["wh_dlc07_brt_fay_enchantress"] = {
		{"mission", "wh_dlc07_anc_arcane_item_the_chalice_of_potions", "saison_qb_brt_fay_chalice_of_potions", nil,
			"war.camp.advice.quests.001"},
		{"reward", "wh2_dlc12_anc_enchanted_item_brt_morgianas_mirror"}
	},
	-- Drycha, Kemmler, Grom (23.09.2026, 15 h) : leurs quêtes de CA, même ordre et mêmes rangs qu'aux Empires (Kemmler :
	-- Lame au rang 7, Cape au 12, Bâton au 17 ; Grom : Bannière au 7, Hache au 12 ; Drycha : Coeddil au 7). Lieux sur notre
	-- carte (lot 10) : col de Gragrut, Karak Tzor, Grunere ; Massif d'Orquemont ; Cythral, le Wildwood.
	["wh_main_vmp_heinrich_kemmler"] = {
		{"mission", "wh_main_anc_arcane_item_skull_staff", "saison_qb_vmp_kemmler_skull_staff"},
		{"mission", "wh_main_anc_enchanted_item_cloak_of_mists_and_shadows", "saison_qb_vmp_kemmler_cloak_of_mists"},
		{"mission", "wh_main_anc_weapon_chaos_tomb_blade", "saison_qb_vmp_kemmler_chaos_tomb_blade", nil,
			"war.camp.advice.quests.001"}
	},
	["wh2_dlc15_grn_grom_the_paunch"] = {
		{"mission", "wh2_dlc15_anc_weapon_axe_of_grom", "saison_qb_grn_grom_axe_of_grom", nil, "war.camp.advice.quests.001"},
		{"mission", "wh2_dlc15_anc_enchanted_item_lucky_banner", "saison_qb_grn_grom_lucky_banner"}
	},
	["wh2_dlc16_wef_drycha"] = {
		{"mission", "wh2_dlc16_anc_enchanted_item_fang_of_taalroth", "saison_qb_wef_drycha_coeddil_unchained", nil,
			"war.camp.advice.quests.001"}
	},
	-- le Duc écarlate (9.0, 24.09.2026) : ses deux objets de CA, donnés au rang comme aux Empires (wh_quests.lua de la
	-- 9.0 ; character_ancillary_quest_ui_details : Armure de sang au rang 7, Joyau de non-vie au rang 12). Lore : l'Armure
	-- de sang (Circle of Blood, p. 46) et le joyau rouge qui le ramène à la non-vie (The Red Duke, C.L. Werner)
	["wh_dlc05_vmp_red_duke"] = {
		{"reward", "wh3_dlc29_anc_talisman_jewel_of_unlife"},
		{"reward", "wh3_dlc29_anc_armour_armour_of_blood"}
	},
	-- les Sœurs du Crépuscule (24.09.2026) : Ceithin-Har, leur Dragon des Forêts (quête de CA, wh_quests.lua), à la
	-- cachette de la harde
	["wh2_dlc16_wef_sisters_of_twilight"] = {
		{"mission", "wh2_dlc16_anc_mount_wef_cha_sisters_of_twilight_forest_dragon", "saison_qb_wef_sisters_ceithin_har", nil,
			"war.camp.advice.quests.001"}
	}
};

-- Si une étape ne peut pas être émise (région devenue invalide, par exemple), la chaîne passe à l'étape suivante
-- (set_up_backup_mission de CA). WH1 le faisait pour le raid de Bastonne annulé.
local SECOURS = {
	{"wh_dlc05_wef_orion_horn_of_the_wild_stage_2_mini", "wh_dlc05_wef_orion_horn_of_the_wild_stage_3a_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_orion_horn_of_the_wild_stage_3a_mini", "wh_dlc05_qb_wef_orion_the_horn_of_the_wild_stage_3_witherhold_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_orion_cloak_of_isha_stage_2_mini", "wh_dlc05_wef_orion_cloak_of_isha_stage_3a_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_orion_cloak_of_isha_stage_3a_mini", "wh_dlc05_qb_wef_orion_the_cloak_of_isha_stage_3_the_night_glens_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_orion_spear_of_kurnous_stage_2_mini", "wh_dlc05_wef_orion_spear_of_kurnous_stage_3a_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_orion_spear_of_kurnous_stage_3a_mini", "wh_dlc05_qb_wef_orion_the_spear_of_kurnous_stage_3_the_oak_of_ages_mini", "wh_dlc05_wef_orion"},
	{"wh_dlc05_wef_durthu_sword_of_daith_stage_2_mini", "wh_dlc05_wef_durthu_sword_of_daith_stage_3a_mini", "wh_dlc05_wef_durthu"},
	{"wh_dlc05_wef_durthu_sword_of_daith_stage_3a_mini", "wh_dlc05_qb_wef_durthu_daiths_sword_stage_3_the_ashenhall_mini", "wh_dlc05_wef_durthu"},
	{"wh_dlc05_wef_durthu_sword_of_daith_stage_4a_mini", "wh_dlc05_qb_wef_durthu_daiths_sword_stage_4_battle_of_cairns_mini", "wh_dlc05_wef_durthu"}
};

-- Même texte d'aide que les Empires à la première quête.
local AIDE = {
	"wh2.camp.advice.quests.info_001",
	"wh2.camp.advice.quests.info_002",
	"wh2.camp.advice.quests.info_003"
};


-- Appelé par saison_start.lua à chaque chargement, après setup_wh_campaign() (écouteur des quêtes annulées, armées de
-- bataille de quête sans entretien).
function saison_quetes_demarrer()
	-- un seigneur à la fois : une fiche manquante n'arrête que les siennes (audit du code, M5)
	for sous_type, quetes in pairs(QUETES) do
		saison_sur("quetes de " .. sous_type, set_up_rank_up_listener, quetes, sous_type, AIDE);
	end;
	for i = 1, #SECOURS do
		saison_sur("quete de secours " .. i, set_up_backup_mission, SECOURS[i][1], SECOURS[i][2], SECOURS[i][3]);
	end;
end;
