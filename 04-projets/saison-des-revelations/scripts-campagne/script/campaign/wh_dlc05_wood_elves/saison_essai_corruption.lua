-----------------------------------------------------------------------------------
--	ESSAI À DRAPEAU : les décors de corruption de notre carte basculent-ils ? Sans drapeau, ce fichier ne fait rien.
--
--	Question de la construction (23.09.2026, 04 h 40) : notre corruption_mask est uniforme à 21, alors que CA peint le
--	sien (moyenne 52 ; ses décors de corruption sont posés sur des valeurs médianes de 68 à 71). Le jeu bascule décors et
--	arbres d'une zone vers ceux de sa corruption au-dessus d'une intensité de 50 sur 255 (campaign_variables :
--	min_visual_corruption_prop_value = 50, max_visual_corruption_value = 100). On porte la corruption du Chaos au
--	maximum (100, pooled_resources) dans trois provinces d'Athel Loren riches en décors masqués au Chaos (calques de la
--	construction : Talsyn 1 052 entités, Torgovann 694, Fyr Darric 376) ; au tour suivant, sol, arbres et décors du
--	Chaos doivent y paraître. Sinon, la construction peint le masque plus haut et on refait l'essai.
--
--	Drapeau : un fichier NON VIDE (un fichier vide n'est pas vu) nommé saison_essai_corruption.txt dans
--	script/campaign/wh_dlc05_wood_elves/ : en vrac dans <jeu>\data\ (pas de pack à refaire), ou dans le pack le temps
--	de l'essai. Le journal de script dit si le drapeau est vu et, à chaque tour du joueur, la corruption des provinces
--	d'essai. Après l'essai : retirer le drapeau ; la corruption posée reste dans la sauvegarde de l'essai.
-----------------------------------------------------------------------------------

local DRAPEAU_DOSSIER = "/script/campaign/wh_dlc05_wood_elves/";
local DRAPEAU = "saison_essai_corruption.txt";
-- 24.09.2026 (session du rendu, arbres jaunes à la frontière de Mousillon) : en plus, la corruption VAMPIRIQUE dans les
-- deux voisines de Mousillon, à 100 (Bastogne) et à 50 (Bordeleaux), pour voir si leurs arbres grisent et à quel seuil
local ESSAIS = {
	{province = "wh_dlc05_talsyn", corruption = "wh3_main_corruption_chaos", cible = 100},
	{province = "wh_dlc05_torgovann", corruption = "wh3_main_corruption_chaos", cible = 100},
	{province = "wh_dlc05_fyr_darric", corruption = "wh3_main_corruption_chaos", cible = 100},
	{province = "wh_dlc05_bastonne", corruption = "wh3_main_corruption_vampiric", cible = 100},
	{province = "wh_dlc05_bordeleaux", corruption = "wh3_main_corruption_vampiric", cible = 50}
};
local AUTRES = {"wh3_main_corruption_chaos", "wh3_main_corruption_vampiric", "wh3_main_corruption_khorne", "wh3_main_corruption_nurgle",
	"wh3_main_corruption_slaanesh", "wh3_main_corruption_tzeentch", "wh3_main_corruption_skaven"};


local function drapeau_present()
	local liste = common.filesystem_lookup(DRAPEAU_DOSSIER, DRAPEAU);
	return is_string(liste) and liste ~= "";
end;


local function valeur(prm, cle)
	local r = prm:resource(cle);
	if not r or r:is_null_interface() then
		return nil;
	end;
	return r:value();
end;


-- Porte la corruption de chaque province d'essai à sa cible et écrit les valeurs au journal.
local function porter_au_maximum(moment)
	for _, e in ipairs(ESSAIS) do
		local province = cm:get_province(e.province);
		if not province or province:is_null_interface() then
			script_error("La Saison des Revelations : essai de corruption : province " .. e.province .. " introuvable");
		else
			local prm = province:pooled_resource_manager();
			local avant = valeur(prm, e.corruption);
			if avant and avant < e.cible then
				cm:change_corruption_in_province_by(province, e.corruption, e.cible - avant, "events");
			end;
			local autres = {};
			for j = 1, #AUTRES do
				local v = valeur(prm, AUTRES[j]);
				if AUTRES[j] ~= e.corruption and v and v > 0 then
					table.insert(autres, string.sub(AUTRES[j], 21) .. " " .. tostring(v));
				end;
			end;
			out("La Saison des Revelations : essai de corruption (" .. moment .. ") : " .. e.province .. " "
				.. string.sub(e.corruption, 21) .. " " .. tostring(avant) .. " -> " .. tostring(valeur(prm, e.corruption))
				.. ((#autres > 0) and (" ; autres : " .. table.concat(autres, ", ")) or ""));
		end;
	end;
end;


function saison_essai_corruption_lancer()
	if not drapeau_present() then
		out("La Saison des Revelations : essai de corruption : pas de drapeau (" .. DRAPEAU .. "), rien a faire");
		return;
	end;
	out("La Saison des Revelations : ESSAI DE CORRUPTION ACTIF (drapeau " .. DRAPEAU .. " trouve)");
	porter_au_maximum("chargement, tour " .. cm:model():turn_number());
	core:add_listener(
		"saison_essai_corruption",
		"FactionTurnStart",
		function(context)
			return context:faction():is_human();
		end,
		function()
			saison_sur("essai de corruption", porter_au_maximum, "tour " .. cm:model():turn_number());
		end,
		true
	);
end;


-- Après les démarrages de saison_start.lua (corruption de départ comprise), à chaque chargement.
cm:add_first_tick_callback(function() saison_sur("essai de corruption (drapeau)", saison_essai_corruption_lancer) end);
