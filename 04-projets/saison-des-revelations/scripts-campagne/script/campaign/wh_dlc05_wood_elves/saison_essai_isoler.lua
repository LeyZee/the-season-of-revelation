-----------------------------------------------------------------------------------
--	ESSAIS À DRAPEAU : isoler le plantage du tour 11 (Warhammer3.exe+0x2532B26, fil principal ; partie d'Orion, pack de
--	19 h 02, 2 fois sur 2). Juste avant : Drycha (IA) gagne une bataille ET une armée d'invasion de la harde de Morghur
--	(invasion_beastmen_first_invasion_1 / _2, histoire de WH1) est détruite. Sans drapeau, ce fichier ne fait rien.
--
--	Deux drapeaux (fichiers NON VIDES, en vrac dans <jeu>\data\script\campaign\wh_dlc05_wood_elves\), un par essai :
--	- saison_essai_sans_invasions.txt : la harde ne lance aucune invasion (invasion_manager:new_invasion rend nil pour
--	  elle ; l'histoire le prévoit : étape sans armée). Plantage encore -> les invasions ne sont pas en cause.
--	- saison_essai_drycha_paix.txt : Drycha fait la paix avec tous et ne peut plus déclarer de guerre (après les guerres
--	  de départ). Plantage encore -> les batailles de Drycha ne sont pas en cause.
--	Le journal de script dit quel essai est actif. Retirer le drapeau après l'essai.
-----------------------------------------------------------------------------------

local DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local HARDE = "wh_dlc05_bst_morghur_herd";
local DRYCHA = "wh2_dlc16_wef_drycha";


local function drapeau(nom)
	local liste = common.filesystem_lookup(DOSSIER, nom);
	return is_string(liste) and liste ~= "";
end;


-- dès le chargement : l'histoire crée ses invasions pendant la partie, par invasion_manager:new_invasion
if drapeau("saison_essai_sans_invasions.txt") and invasion_manager and is_function(invasion_manager.new_invasion) then
	local ca_new_invasion = invasion_manager.new_invasion;
	invasion_manager.new_invasion = function(self, cle, faction, ...)
		if faction == HARDE then
			out("La Saison des Revelations : ESSAI SANS INVASIONS : invasion " .. tostring(cle) .. " de la harde non creee");
			return nil;
		end;
		return ca_new_invasion(self, cle, faction, ...);
	end;
	out("La Saison des Revelations : ESSAI SANS INVASIONS ACTIF (drapeau saison_essai_sans_invasions.txt)");
end;


local function drycha_en_paix()
	if not drapeau("saison_essai_drycha_paix.txt") then
		return;
	end;
	local drycha = cm:get_faction(DRYCHA);
	if not drycha or drycha:is_dead() then
		return;
	end;
	local guerres = drycha:factions_at_war_with();
	local ennemis = {};
	for i = 0, guerres:num_items() - 1 do
		table.insert(ennemis, guerres:item_at(i):name());
	end;
	for _, e in ipairs(ennemis) do
		cm:force_make_peace(DRYCHA, e);
	end;
	cm:force_diplomacy("faction:" .. DRYCHA, "all", "war", false, false, true);
	out("La Saison des Revelations : ESSAI DRYCHA EN PAIX ACTIF : paix avec " .. table.concat(ennemis, ", "));
end;

-- après les guerres de départ (premier tick d'une partie neuve, enregistré avant ce fichier par saison_start)
cm:add_first_tick_callback(function() saison_sur("essai Drycha en paix (drapeau)", drycha_en_paix) end);
