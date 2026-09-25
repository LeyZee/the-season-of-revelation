-----------------------------------------------------------------------------------
--	La campagne exige le DLC « Realm of the Wood Elves » (demande de Charles, 23.09.2026).
--
--	1. Écran de campagne : Orion et Durthu y sont verrouillés par CA elle-même (factions rattachées au paquet
--	   wh1_wood_elves). Le rattachement de la carte au paquet (campaign_map_playable_area_ownership_content_pack_
--	   junctions, deux paquets pour une zone jouable) faisait fermer le jeu au démarrage : retiré le 23.09.2026.
--	2. En jeu (ce fichier) : si le joueur local ne possède pas le produit TW_WH1_WOOD_ELVES (ownership_products de
--	   WH3), aucun système de la campagne ne démarre, un message l'explique et le bouton ramène au menu principal.
--	   Le message est un texte traduit (clé saison_des_revelations_dlc_requis, textes_gameplay.json), avec un texte de
--	   secours dans les deux langues si la clé manque.
-----------------------------------------------------------------------------------

SAISON_DLC_REQUIS = "TW_WH1_WOOD_ELVES";
saison_bloquee = false;

-- Journal propre au verrou (25.09.2026, essai du verrou de la construction) : le retour au menu dans la même minute
-- écrase le script_log de la campagne par celui du menu (même nom). Chaque ligne va AUSSI, en ajout, dans
-- saison_verrou.txt du dossier du jeu (comme journal() de saison_choix_par_defaut.lua), sous pcall.
local function trace(texte)
	out("La Saison des Revelations : " .. texte);
	pcall(function()
		local f = io.open("saison_verrou.txt", "a");
		if f then
			f:write(os.date("%Y-%m-%d %H:%M:%S") .. " " .. texte .. "\n");
			f:close();
		end;
	end);
end;
saison_produit_manquant = nil;		-- produit de CA qui manque (celui de la campagne ou celui du seigneur)

-- 3. Le contenu du seigneur choisi (consigne de Charles, 25.09.2026, 16 h 15 : « je ne veux pas avoir de problème avec
--    CA »). Produit de CA qui débloque la faction jouée, relevé dans le kit 9.0 et vérifié (faction et sous-type donnent
--    le même paquet) : faction_ownership_content_pack_junctions / agent_subtype_ownership_content_pack_junctions ->
--    paquet ; ownership_content_pack_requirements -> ensemble <paquet>_req ; ownership_content_pack_required_products ->
--    produit. Les scripts de campagne ne lisent pas ces tables : table en dur. Nom du produit dans la langue du joueur :
--    le texte de CA ownership_products_description_<produit>.
local PRODUITS_DES_SEIGNEURS = {
	wh_dlc05_wef_wood_elves = "TW_WH1_WOOD_ELVES",				-- Orion (paquet wh1_wood_elves)
	wh_dlc05_wef_argwylon = "TW_WH1_WOOD_ELVES",				-- Durthu
	wh2_dlc16_wef_drycha = "TW_WH1_WOOD_ELVES",					-- Drycha
	wh_main_brt_bordeleaux = "TW_WH1_BRETONNIA_FREE",			-- Alberic (wh1_bretonnia_free)
	wh_main_brt_carcassonne = "TW_WH1_BRETONNIA_FREE",			-- la Fée
	wh_dlc05_bst_morghur_herd = "TW_WH1_BEASTMEN",				-- Morghur (wh1_beastmen)
	wh_main_vmp_mousillon = "TW_WH1_BASE_GAME",					-- le Duc écarlate (wh1_base_game)
	wh2_dlc11_vmp_the_barrow_legion = "TW_WH1_BASE_GAME",		-- Kemmler
	wh2_dlc15_grn_broken_axe = "TW_WH2_DLC15_WARDEN",			-- Grom (wh2_dlc15_warden)
	wh2_dlc16_wef_sisters_of_twilight = "TW_WH2_DLC16_TWILIGHT"	-- les Sœurs (wh2_dlc16_twilight)
};


-- Vrai si le joueur local possède le DLC. En cas d'erreur de l'appel, on ne bloque pas : un défaut de script ne doit
-- pas priver de la campagne quelqu'un qui possède le DLC.
-- Interrupteurs d'essai (25.09.2026) : un pack d'essai qui pose _G.saison_essai_sans_dlc = true simule un joueur sans le
-- DLC de la campagne ; _G.saison_essai_sans_dlc_seigneur = true, sans celui du seigneur joué. Changer une clé de produit
-- ne suffit pas : une clé inconnue fait échouer l'appel, et la campagne n'est alors PAS bloquée (règle ci-dessous).
local function possede(produit, faction_key, essai)
	if essai then
		trace("essai du verrou (" .. produit .. " simule absent, faction " .. tostring(faction_key) .. ")");
		return false;
	end;
	local ok, oui = pcall(function() return cm:is_dlc_flag_enabled(produit, faction_key) end);
	if not ok then
		trace("test du produit " .. produit .. " impossible (" .. tostring(oui) .. "), non bloque");
		return true;
	end;
	trace("produit " .. produit .. " pour " .. tostring(faction_key) .. " : " .. tostring(oui));
	return oui ~= false;
end;

-- Rend le produit qui manque au joueur local (celui de la campagne d'abord, puis celui de son seigneur), ou nil.
local function produit_manquant()
	local faction_key = cm:get_local_faction_name(true);
	if not faction_key then
		-- aucun joueur local (partie sans humain) : rien à bloquer, sauf essai
		if _G.saison_essai_sans_dlc == true then
			return SAISON_DLC_REQUIS;
		end;
		if _G.saison_essai_sans_dlc_seigneur == true then
			trace("essai du verrou du seigneur sans joueur local (produit des Soeurs pris pour exemple)");
			return PRODUITS_DES_SEIGNEURS.wh2_dlc16_wef_sisters_of_twilight;
		end;
		return nil;
	end;
	if not possede(SAISON_DLC_REQUIS, faction_key, _G.saison_essai_sans_dlc == true) then
		return SAISON_DLC_REQUIS;
	end;
	local du_seigneur = PRODUITS_DES_SEIGNEURS[faction_key];
	if du_seigneur and not possede(du_seigneur, faction_key, _G.saison_essai_sans_dlc_seigneur == true) then
		return du_seigneur;
	end;
	return nil;
end;


-- Appelée en tête du rappel d'avant le premier tick (saison_start.lua).
function saison_verifier_dlc()
	trace("verification des DLC (campagne " .. SAISON_DLC_REQUIS .. ", faction locale "
		.. tostring(cm:get_local_faction_name(true)) .. ")");
	saison_produit_manquant = produit_manquant();
	saison_bloquee = saison_produit_manquant ~= nil;
	if saison_bloquee then
		trace("le DLC " .. saison_produit_manquant .. " manque, campagne bloquee : aucun systeme de la Saison ne demarre");
	else
		trace("DLC presents, campagne non bloquee");
	end;
	return saison_bloquee;
end;


function saison_retour_au_menu()
	local ok = pcall(function() core:get_ui_root():InterfaceFunction("QuitForScript") end);
	if not ok then
		local ok2 = pcall(function() common.call_context_command("QuitToMainMenu") end);
		trace("retour au menu demande : QuitForScript en echec, QuitToMainMenu " .. (ok2 and "appele" or "en echec"));
	else
		trace("retour au menu demande (QuitForScript)");
	end;
end;


-- Message bloquant (boîte de dialogue de WH3, comme wh2_dlc17_bloodgrounds.lua) : ses deux boutons ramènent au menu.
local function afficher_blocage()
	local ui_root = core:get_ui_root();
	local boite = UIComponent(ui_root:CreateComponent("saison_dlc_requis", "UI/Common UI/dialogue_box"));
	local texte = find_uicomponent(ui_root, "saison_dlc_requis", "DY_text");
	local message = "La Saison de la Révélation nécessite le DLC « Realm of the Wood Elves ».\n\n"
		.. "The Season of Revelation requires the Realm of the Wood Elves DLC.";
	local cle_texte = "saison_des_revelations_dlc_requis";
	if saison_produit_manquant and saison_produit_manquant ~= SAISON_DLC_REQUIS then
		-- le contenu du seigneur : son nom de CA, dans la langue du joueur, à la place de {produit}
		local ok_nom, nom = pcall(function()
			return common.get_localised_string("ownership_products_description_" .. saison_produit_manquant)
		end);
		if not (ok_nom and is_string(nom) and nom ~= "") then
			nom = saison_produit_manquant;
		end;
		message = "Ce seigneur nécessite le contenu « " .. nom .. " ».\n\nThis lord requires the \"" .. nom
			.. "\" content.";
		local ok_t, t = pcall(function() return common.get_localised_string("saison_des_revelations_dlc_seigneur_requis") end);
		if ok_t and is_string(t) and t ~= "" then
			message = string.gsub(t, "{produit}", function() return nom end);
		end;
		cle_texte = nil;
	end;
	local ok, traduit = pcall(function() return cle_texte and common.get_localised_string(cle_texte) end);
	if ok and is_string(traduit) and traduit ~= "" then
		message = traduit;
	end;
	if texte then
		texte:SetStateText(message, "saison_dlc_requis");
	end;
	trace("message affiche (" .. (texte and "DY_text trouve" or "DY_text INTROUVABLE") .. ") : "
		.. string.gsub(message, "\n", " / "));
	boite:PropagatePriority(1000);
	boite:LockPriority();

	core:add_listener(
		"saison_dlc_requis_clic",
		"ComponentLClickUp",
		function(context)
			return context.string == "button_tick" or context.string == "button_cancel";
		end,
		function(context)
			trace("bouton " .. tostring(context.string) .. " clique");
			saison_retour_au_menu();
		end,
		true
	);
end;


cm:add_first_tick_callback(
	function()
		trace("premier tick : campagne " .. (saison_bloquee and "BLOQUEE" or "non bloquee"));
		if saison_bloquee then
			local ok, err = pcall(afficher_blocage);
			if not ok then
				trace("message du DLC impossible : " .. tostring(err));
				script_error("La Saison des Revelations : message du DLC impossible : " .. tostring(err));
				saison_retour_au_menu();
			end;
		end;
	end
);
