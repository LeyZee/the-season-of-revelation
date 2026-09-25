-----------------------------------------------------------------------------------
--	ESSAI À DRAPEAU « sortie des garnisons côtières » (23.09.2026, 22 h 55, demande de Charles) : à Bordeleaux, la
--	façade de la ville paraît posée sur l'eau, Alberic en garnison au-dessus de l'eau. Est-il BLOQUÉ ?
--
--	Drapeau (fichier NON VIDE) : <jeu>\data\script\campaign\wh_dlc05_wood_elves\saison_essai_sortie.txt.
--	Une fois, au premier tick + 3 s (à défaut au premier WorldStartRound) :
--	1) pour CHAQUE général en garnison dans une colonie PORTUAIRE (toutes factions ; Bordeleaux, Mousillon, Château
--	   d'Épée, les ports elfes...) : 8 cases de terre candidates à 4 hex autour de la colonie (valides pour la faction,
--	   par find_valid_spawn_location_for_character_from_position) ; pour chacune, le modèle dit si le général peut
--	   l'atteindre un jour (character_can_ever_reach_position) et ce tour-ci (character_can_reach_position). Ligne
--	   « [SORTIE] ... ATTEIGNABLE n/8 » ou « ... AUCUNE CASE ATTEIGNABLE » ;
--	2) pour les généraux DU JOUEUR : ordre réel de sortie vers la première case atteignable (cm:move_to), puis au bout de
--	   8 s : position avant / après, points d'action, « SORTIE OK » (déplacé) ou « SORTIE BLOQUEE » (pas bougé).
--	Journal : lignes « [SORTIE] ». Fichier chargé par AUCUN required.lua : à copier dans script\campaign\mod\ du pack
--	d'essai. Tout est sous pcall. Aucune fonction globale.
-----------------------------------------------------------------------------------

local DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local RAYON = 4;
local DIRECTIONS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}, {1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
local ATTENTE_S = 8;


local function drapeau(nom)
	local liste = common.filesystem_lookup(DOSSIER, nom);
	return is_string(liste) and liste ~= "";
end;


local function sans_risque(nom, f, ...)
	local ok, res = pcall(f, ...);
	if not ok then
		out("[SORTIE] ERREUR " .. nom .. " : " .. tostring(res));
		return nil;
	end;
	return res;
end;


local function peut(methode, c, x, y)
	local model = cm:model();
	local ok, res = pcall(function() return model[methode](model, c, x, y) end);
	if not ok then
		return "erreur(" .. tostring(res) .. ")";
	end;
	return res;
end;


-- cases de terre candidates autour de (sx, sy), valides pour la faction du général
local function candidates(c, sx, sy)
	local out_ = {};
	local vues = {};
	for _, d in ipairs(DIRECTIONS) do
		local x, y = cm:find_valid_spawn_location_for_character_from_position(c:faction():name(), sx + d[1] * RAYON, sy + d[2] * RAYON, false);
		if x and x ~= -1 and not vues[x .. "," .. y] then
			vues[x .. "," .. y] = true;
			table.insert(out_, {x, y});
		end;
	end;
	return out_;
end;


local function examiner(c, bouger)
	local region = c:region();
	local s = region:settlement();
	local sx, sy = s:logical_position_x(), s:logical_position_y();
	local cx, cy = c:logical_position_x(), c:logical_position_y();
	local cqi = c:command_queue_index();
	local tete = string.format("[SORTIE] cqi %d %s %s a %s (colonie %d,%d ; general %d,%d) pa=%d",
		cqi, c:faction():name(), c:character_subtype_key(), region:name(), sx, sy, cx, cy, c:action_points_remaining_percent());
	local cases = candidates(c, sx, sy);
	local premiere = nil;
	local n_jamais, n_tour = 0, 0;
	for _, p in ipairs(cases) do
		local jamais = peut("character_can_ever_reach_position", c, p[1], p[2]);
		local tour = peut("character_can_reach_position", c, p[1], p[2]);
		out(string.format("[SORTIE]     case %d,%d : un_jour=%s ce_tour=%s", p[1], p[2], tostring(jamais), tostring(tour)));
		if jamais == true then
			n_jamais = n_jamais + 1;
		end;
		if tour == true then
			n_tour = n_tour + 1;
			premiere = premiere or p;
		end;
	end;
	if n_jamais == 0 then
		out(tete .. " : AUCUNE CASE ATTEIGNABLE (" .. #cases .. " candidates)");
	else
		out(tete .. string.format(" : ATTEIGNABLE un jour %d/%d, ce tour %d/%d", n_jamais, #cases, n_tour, #cases));
	end;

	if not bouger then
		return;
	end;
	if not premiere then
		out(string.format("[SORTIE] cqi %d : SORTIE BLOQUEE (aucune case atteignable ce tour ; aucun ordre donne)", cqi));
		return;
	end;
	local lookup = "character_cqi:" .. cqi;
	cm:enable_movement_for_character(lookup);
	cm:move_to(lookup, premiere[1], premiere[2]);
	out(string.format("[SORTIE] cqi %d : ordre de sortie vers %d,%d", cqi, premiere[1], premiere[2]));
	cm:callback(function()
		sans_risque("constat", function()
			local c2 = cm:get_character_by_cqi(cqi);
			if not c2 then
				out(string.format("[SORTIE] cqi %d : introuvable apres l'ordre", cqi));
				return;
			end;
			local ax, ay = c2:logical_position_x(), c2:logical_position_y();
			local bouge = ax ~= cx or ay ~= cy;
			out(string.format("[SORTIE] cqi %d : avant %d,%d ; apres %d,%d ; cible %d,%d ; pa=%d ; en colonie=%s : %s",
				cqi, cx, cy, ax, ay, premiere[1], premiere[2], c2:action_points_remaining_percent(), tostring(c2:in_settlement()),
				bouge and "SORTIE OK" or "SORTIE BLOQUEE"));
		end);
	end, ATTENTE_S);
end;


local function passer_en_revue(joueur)
	local factions = cm:model():world():faction_list();
	for i = 0, factions:num_items() - 1 do
		local f = factions:item_at(i);
		if not f:is_dead() then
			local forces = f:military_force_list();
			for j = 0, forces:num_items() - 1 do
				local mf = forces:item_at(j);
				if mf:has_general() and not mf:is_armed_citizenry() then
					local c = mf:general_character();
					if c:has_region() and c:in_settlement() and c:region():settlement():is_port() then
						sans_risque("examen " .. c:command_queue_index(), examiner, c, f:name() == joueur);
					end;
				end;
			end;
		end;
	end;
	out("[SORTIE] revue finie");
end;


-- une seule revue par partie ; déclencheurs : premier tick + 3 s, et à défaut WorldStartRound (FactionTurnStart
-- n'arrive pas aux scripts au tour 1 : erreur 143 ; essai de 23 h, aucune ligne [SORTIE])
local revue_faite = false;

local function lancer_revue(origine)
	if revue_faite then
		return;
	end;
	revue_faite = true;
	local joueurs = cm:get_human_factions();
	local joueur = joueurs and joueurs[1] or "";
	out("[SORTIE] revue lancee (" .. origine .. ", joueur " .. tostring(joueur) .. ", tour " .. cm:model():turn_number() .. ")");
	sans_risque("revue", passer_en_revue, joueur);
end;

if drapeau("saison_essai_sortie.txt") then
	cm:add_first_tick_callback(function()
		cm:callback(function() lancer_revue("premier tick + 3 s") end, 3);
	end);
	core:add_listener(
		"saison_essai_sortie",
		"WorldStartRound",
		true,
		function() cm:callback(function() lancer_revue("WorldStartRound") end, 1) end,
		false
	);
	out("[SORTIE] ESSAI DE SORTIE ACTIF (drapeau saison_essai_sortie.txt)");
end;
