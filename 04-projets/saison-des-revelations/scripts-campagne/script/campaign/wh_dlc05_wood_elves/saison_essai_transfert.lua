-----------------------------------------------------------------------------------
--	ESSAI À DRAPEAU : le plantage du tour 11 (série 2, Orion, pack de 18 h 02, Warhammer3.exe+0x2532B26) vient-il d'un
--	changement de propriétaire d'une région portant nos gabarits neufs (lot 18) et nos monuments (lot 21) ? Juste avant,
--	Drycha avait pris Tal Amere (gabarit wh_dlc05_mini_special_tal_amere_secondary, Galerie de glace). Sans drapeau, ce
--	fichier ne fait rien.
--
--	Au premier tour, les régions ci-dessous changent de main (cm:transfer_region_to_faction) ; finir le tour : si le jeu
--	plante à la fin du tour 1 ou au tour 2, la piste gabarits / monuments est confirmée ; sinon, écartée.
--	Drapeau : un fichier NON VIDE saison_essai_transfert.txt dans script/campaign/wh_dlc05_wood_elves/ (en vrac dans
--	<jeu>\data\, pas de pack à refaire). Le journal de script dit chaque transfert. Retirer le drapeau après l'essai.
-----------------------------------------------------------------------------------

local DRAPEAU_DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local DRAPEAU = "saison_essai_transfert.txt";
-- région -> nouvelle propriétaire (une culture différente de l'ancienne quand c'est possible)
local TRANSFERTS = {
	{"wh_dlc05_atylwyth_tal_amere", "wh2_dlc16_wef_drycha"},			-- le cas du plantage (Galerie de glace)
	{"wh_dlc05_quenelles_quenelles", "wh2_dlc15_grn_broken_axe"},		-- Chapelle de l'Enchanteresse, prise par Grom
	{"wh_dlc05_grey_mountains_2_blackstone_post", "wh_main_brt_parravon"},	-- Tertre de Krell et Drachenfels, à la Bretonnie
	{"wh_dlc05_torgovann_cromlech_cadai", "wh_dlc05_bst_morghur_herd"},	-- Cromlech et Forge de Daith (horde : rasée ?)
	{"wh_dlc05_bordeleaux_turris_vigilans", "wh_main_vmp_mousillon"}		-- Turris Vigilans, aux vampires
};


local function drapeau_present()
	local liste = common.filesystem_lookup(DRAPEAU_DOSSIER, DRAPEAU);
	return is_string(liste) and liste ~= "";
end;


function saison_essai_transfert_lancer()
	if not drapeau_present() then
		out("La Saison des Revelations : essai de transfert : pas de drapeau (" .. DRAPEAU .. "), rien a faire");
		return;
	end;
	if not cm:is_new_game() then
		out("La Saison des Revelations : essai de transfert : partie chargee, transferts deja faits");
		return;
	end;
	out("La Saison des Revelations : ESSAI DE TRANSFERT ACTIF (drapeau " .. DRAPEAU .. " trouve)");
	for i = 1, #TRANSFERTS do
		local region, faction = TRANSFERTS[i][1], TRANSFERTS[i][2];
		local r, f = cm:get_region(region), cm:get_faction(faction);
		if r and f and not f:is_dead() then
			cm:transfer_region_to_faction(region, faction);
			out("La Saison des Revelations : essai de transfert : " .. region .. " -> " .. faction);
		else
			out("La Saison des Revelations : essai de transfert : " .. region .. " ou " .. faction .. " introuvable");
		end;
	end;
end;


cm:add_first_tick_callback(function() saison_sur("essai de transfert (drapeau)", saison_essai_transfert_lancer) end);
