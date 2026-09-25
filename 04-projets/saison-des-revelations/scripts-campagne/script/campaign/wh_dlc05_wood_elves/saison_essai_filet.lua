-----------------------------------------------------------------------------------
--	COPIE D'ESSAI de saison_filet_blesses.lua (même règle), pour le pack d'essai AVANT le prochain pack : chargée par
--	AUCUN required.lua, à mettre dans script\campaign\mod\. Sans drapeau. À retirer quand le pack porte l'original.
--	FILET DE SÉCURITÉ DES CHEFS DE FACTION (23.09.2026, 23 h 05).
--
--	Plantage du tour 11 (Warhammer3.exe+0x2532B26, 6 fois sur 6 dans les parties d'Orion, lot 25 compris) : Arlas,
--	chef de Modryn, battu au tour 7, est remplacé par un nouveau personnage blessé qui n'est PAS chef, et Modryn reste
--	SANS chef (même chose à Cavaroc) ; au retour de ce blessé, au début du tour de Modryn, le jeu plante. Cause de fond :
--	chez les Elfes sylvains, le poste « faction_leader » n'est pas défini pour la culture mais faction par faction
--	(ministerial_positions_culture_details : une ligne pour chaque faction elfe de CA) ; nos 7 factions elfes de WH1
--	n'en avaient pas (lot 26). Essai E (saison_essai_tour11.lua) : si le blessé meurt, le tour 11 passe.
--
--	Règle : à la fin de chaque tour de faction, toute faction elfe sylvaine de l'IA qui n'a PAS de chef voit ses
--	seigneurs blessés perdre leur immortalité et mourir au lieu de revenir ; une ligne au journal à chaque fois. Le jeu
--	fait le reste, comme dans E (13 tours tenus) : la faction continue avec ses colonies et recrute un autre seigneur.
--	Avec le lot 26, une faction elfe a toujours un chef : ce filet ne devrait plus agir ; il reste en garde.
--	Pas les autres cultures : leur poste de chef est défini pour toute la culture (CA) et la succession y marche.
--	Aucune fonction globale (le chargeur de mods exécute une fonction homonyme du fichier).
-----------------------------------------------------------------------------------

local CULTURE_ELFE = "wh_dlc05_wef_wood_elves";


local function filet_blesses()
	local factions = cm:model():world():faction_list();
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		if not f:is_dead() and not f:is_human() and f:culture() == CULTURE_ELFE and not f:has_faction_leader() then
			local persos = f:character_list();
			local blesses = {};
			for j = 0, persos:num_items() - 1 do
				local c = persos:item_at(j);
				if c:is_wounded() and cm:char_is_general(c) then
					table.insert(blesses, {c:command_queue_index(), c:character_subtype_key()});
				end;
			end;
			for _, b in ipairs(blesses) do
				cm:set_character_immortality("character_cqi:" .. b[1], false);
				cm:kill_character(b[1], true);
				out("La Saison des Revelations : filet des chefs : " .. f:name() .. " sans chef, seigneur blesse cqi " .. b[1]
					.. " (" .. b[2] .. ") ne reviendra pas");
			end;
		end;
	end;
end;


core:add_listener(
	"saison_essai_filet",
	"FactionTurnEnd",
	true,
	function()
		local ok, err = pcall(filet_blesses);
		if not ok then
			script_error("La Saison des Revelations : filet des chefs a echoue : " .. tostring(err));
		end;
	end,
	true
);
out("La Saison des Revelations : filet des chefs en place (COPIE D'ESSAI)");
