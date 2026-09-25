-----------------------------------------------------------------------------------
--	ESSAI À DRAPEAU « Drycha hors harde » (23.09.2026, 21 h 25) : isoler le plantage du tour 11 (Warhammer3.exe+0x2532B26,
--	fil principal, pendant le tour de Drycha ; 3 fois sur 3 avec les armées de la harde, 0 sans elles).
--	Les armées de la harde existent, mais Drycha n'est JAMAIS en guerre contre la harde :
--	(1) cm.force_declare_war ne lie plus la paire (les invasions déclarent leurs guerres par lui, au fil de la partie) ;
--	(2) la guerre entre elles est interdite dans les deux sens (force_diplomacy) ;
--	(3) au premier tick et au début du tour de chacune, une guerre qui existerait quand même est close (force_make_peace).
--	Toutes les autres guerres restent.
--
--	Fichier À PART de saison_essai_isoler.lua : le pack de 20 h 42 charge déjà saison_essai_isoler par required.lua, et
--	le chargeur de mods de CA saute tout fichier dont le nom est déjà dans package.loaded (« Failed to load mod » sans
--	autre ligne, script_log_230926_2114). Ce fichier n'est chargé par AUCUN required.lua : la construction le copie dans
--	script\campaign\mod\ du pack d'essai. Drapeau (fichier NON VIDE) : <jeu>\data\script\campaign\wh_dlc05_wood_elves\
--	saison_essai_drycha_hors_harde.txt. Sans drapeau, ce fichier ne fait rien. Aucune fonction globale.
-----------------------------------------------------------------------------------

local DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local HARDE = "wh_dlc05_bst_morghur_herd";
local DRYCHA = "wh2_dlc16_wef_drycha";
local PREFIXE = "La Saison des Revelations : ESSAI DRYCHA HORS HARDE : ";


local function drapeau(nom)
	local liste = common.filesystem_lookup(DOSSIER, nom);
	return is_string(liste) and liste ~= "";
end;


local function paire_drycha_harde(a, b)
	return (a == DRYCHA and b == HARDE) or (a == HARDE and b == DRYCHA);
end;


local function separer(moment)
	local drycha, harde = cm:get_faction(DRYCHA), cm:get_faction(HARDE);
	if not drycha or not harde or drycha:is_dead() then
		return;
	end;
	cm:force_diplomacy("faction:" .. DRYCHA, "faction:" .. HARDE, "war", false, false, true);
	if drycha:at_war_with(harde) then
		cm:force_make_peace(DRYCHA, HARDE);
		out(PREFIXE .. "paix forcee (" .. moment .. ")");
	end;
end;


local function separer_sans_risque(moment)
	local ok, err = pcall(separer, moment);
	if not ok then
		out(PREFIXE .. "ERREUR (" .. moment .. ") : " .. tostring(err));
	end;
end;


local function armer()
	local ca_force_declare_war = cm.force_declare_war;
	cm.force_declare_war = function(self, attaquant, defenseur, ...)
		if paire_drycha_harde(attaquant, defenseur) then
			out(PREFIXE .. "guerre " .. tostring(attaquant) .. " -> " .. tostring(defenseur) .. " non declaree");
			return;
		end;
		return ca_force_declare_war(self, attaquant, defenseur, ...);
	end;

	cm:add_first_tick_callback(function() separer_sans_risque("premier tick") end);
	core:add_listener(
		"saison_essai_drycha_hors_harde",
		"FactionBeginTurnPhaseNormal",
		function(context) local n = context:faction():name(); return n == DRYCHA or n == HARDE end,
		function(context) separer_sans_risque("tour " .. cm:model():turn_number() .. ", " .. context:faction():name()) end,
		true
	);
	out(PREFIXE .. "ACTIF (drapeau saison_essai_drycha_hors_harde.txt)");
end;


if drapeau("saison_essai_drycha_hors_harde.txt") then
	local ok, err = pcall(armer);
	if not ok then
		out(PREFIXE .. "ERREUR a l'armement : " .. tostring(err));
	end;
end;
