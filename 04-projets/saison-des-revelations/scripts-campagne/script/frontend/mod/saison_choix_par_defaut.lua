-----------------------------------------------------------------------------------
--	La Saison des Révélations : race et seigneur choisis d'office à l'écran « Nouvelle campagne » (demande de Charles,
--	23.09.2026, 23 h 05).
--
--	Quand on choisit notre campagne, l'écran s'ouvre sans race ni seigneur : textes bruts « dy_race_name », « dy_race »,
--	« dy_faction » et un drapeau par défaut qui n'a rien à faire là. Les campagnes de CA s'ouvrent sur un seigneur.
--	Ici, tant que notre campagne est affichée et que la liste des seigneurs est VIDE (rien de choisi), le script clique
--	la race des Elfes sylvains puis Orion, le seigneur de la mini-campagne de WH1. Il ne touche à rien dès qu'un seigneur
--	est listé (choix du joueur, ou retour sur l'écran) ; il se réarme quand on quitte l'écran.
--	Composants (relevés du banc d'essai, saison_essai_menu.txt) : campaign_select_new > culture_list >
--	CcoCultureRecord<culture> > race_button ; lord_select_list > list_box > lord_button (propriété lord_key) ;
--	button_start_parent > button_start_campaign (propriété campaign_key).
--	Aucune fonction globale (le chargeur de mods exécute une fonction homonyme du fichier).
-----------------------------------------------------------------------------------

local CAMPAGNE = "wh_dlc05_wood_elves";
local CULTURE = "CcoCultureRecordwh_dlc05_wef_wood_elves";
local SEIGNEUR = "2140783885";		-- Orion (start_pos_characters)
local PERIODE_MS = 700;

-- seigneurs jouables (identifiant de départ) -> faction et culture : pour remplacer les textes bruts de l'en-tête
local SEIGNEURS = {
	["2140783885"] = {"wh_dlc05_wef_wood_elves", "wh_dlc05_wef_wood_elves"},			-- Orion
	["2140783843"] = {"wh_dlc05_wef_argwylon", "wh_dlc05_wef_wood_elves"},				-- Durthu
	["2140783871"] = {"wh2_dlc16_wef_drycha", "wh_dlc05_wef_wood_elves"},				-- Drycha
	["2140783762"] = {"wh_main_brt_bordeleaux", "wh_main_brt_bretonnia"},				-- Alberic
	["2140783791"] = {"wh_main_brt_carcassonne", "wh_main_brt_bretonnia"},				-- la Fée
	["2140783911"] = {"wh_dlc05_bst_morghur_herd", "wh_dlc03_bst_beastmen"},			-- Morghur
	["2140784082"] = {"wh_main_vmp_mousillon", "wh_main_vmp_vampire_counts"},			-- le Duc rouge
	["2140784200"] = {"wh2_dlc11_vmp_the_barrow_legion", "wh_main_vmp_vampire_counts"},	-- Kemmler
	["2140783823"] = {"wh2_dlc15_grn_broken_axe", "wh_main_grn_greenskins"},				-- Grom
	["2140784201"] = {"wh2_dlc16_wef_sisters_of_twilight", "wh_dlc05_wef_wood_elves"}	-- les Sœurs du Crépuscule
};
-- textes bruts de l'en-tête (le composant affiche son propre nom tant qu'aucun texte ne lui est donné)
local TEXTES_BRUTS = {"dy_race_name", "dy_race", "dy_faction"};
-- textes que NOUS avons posés (le jeu ne remplit jamais ces champs sur notre campagne : l'en-tête doit suivre chaque
-- changement de seigneur, pas seulement remplacer le texte brut ; journal du 24.09.2026, 01 h 36 : « Hommes-bêtes »
-- resté affiché avec Orion choisi)
local poses = {};

local fait = false;		-- déjà choisi pendant cette visite de l'écran
local race_cliquee = false;	-- UN seul clic de race par visite de l'écran (banc d'essai : pendant qu'il fait défiler les
							-- races, la liste des seigneurs peut être vide un instant ; on ne revient jamais aux elfes)


-- journal propre (le script_log du menu est écrasé quand une campagne démarre dans la même minute) : fichier
-- saison_choix_menu.txt dans le dossier du jeu, une ligne par décision
local function journal(texte)
	out("La Saison des Revelations : ecran de campagne : " .. texte);
	pcall(function()
		local f = io.open("saison_choix_menu.txt", "a");
		if f then
			f:write(os.date("%Y-%m-%d %H:%M:%S") .. " " .. texte .. "\n");
			f:close();
		end;
	end);
end;

local deja_vu = {};		-- une seule ligne par situation et par visite
local function constat(cle, texte)
	if not deja_vu[cle] then
		deja_vu[cle] = true;
		journal(texte);
	end;
end;


local function visible(uic)
	return uic and uic:Visible() and uic:VisibleFromRoot();
end;


local function notre_campagne_affichee(racine)
	local b = find_uicomponent(racine, "campaign_select_new", "button_start_parent", "button_start_campaign");
	return visible(b) and b:GetProperty("campaign_key") == CAMPAGNE;
end;


local function boutons_seigneurs(racine)
	local out_ = {};
	local liste = find_uicomponent(racine, "campaign_select_new", "lord_select_list", "list_box");
	if not liste then
		return out_;
	end;
	for j = 0, liste:ChildCount() - 1 do
		local b = find_uicomponent(UIComponent(liste:Find(j)), "lord_button");
		-- seulement les vrais seigneurs : sans race choisie, la liste garde un bouton gabarit sans lord_key (journal
		-- de la partie de Charles, 24.09.2026, 02 h 46 : « 1 seigneur(s) listes » alors qu'aucune race n'était choisie,
		-- et le choix d'office s'était retiré)
		local cle = b and b:GetProperty("lord_key");
		if b and visible(b) and is_string(cle) and cle ~= "" then
			table.insert(out_, b);
		end;
	end;
	return out_;
end;


-- Nom de la faction d'Alberic (demande de Charles, 25.09.2026, 05 h : « Bordeleaux » tout court). En 9.0, le nom de
-- faction de la fiche est label_faction_name (campaign_select_new.twui.xml 9.0, relevé du 25.09.2026), lié par contexte
-- à FactionRecordContext.Name, donc au nom de CA « Errants de Bordeleaux » ; dy_faction n'existe plus. Le contexte peut
-- le réécrire : on le repose à chaque passage tant qu'Alberic est choisi.
local CHEMIN_NOM_FACTION = {"right_holder", "tab_lord", "lord_details_panel", "name_and_icon_holder", "name_clip",
	"name_holder", "label_faction_name"};
-- les deux en-têtes de race de 9.0 (même relevé)
local CHEMINS_RACE = {
	{"right_holder", "tab_lord", "lord_details_panel", "lord_info", "tab_lore", "content_holder", "faction_lore",
		"list_clip", "details_subpanel", "dy_race"},
	{"right_holder", "tab_lord", "lord_details_panel", "faction_holder", "button_select_race", "popup_menu", "content",
		"tab_lore", "details_listview", "list_clip", "dy_race"}
};
local ALBERIC = "2140783762";

-- relevé unique (par visite) des composants qui montrent encore « Errants » : pour trouver les restes (infobulles...)
local function chercher_errants(uic, chemin, profondeur)
	if profondeur > 25 then
		return;
	end;
	local ok, texte = pcall(function() return uic:GetStateText() end);
	if ok and is_string(texte) and string.find(texte, "Errant") then
		journal("reste « " .. texte .. " » dans " .. chemin);
	end;
	for i = 0, uic:ChildCount() - 1 do
		local c = UIComponent(uic:Find(i));
		chercher_errants(c, chemin .. " > " .. tostring(c:Id()), profondeur + 1);
	end;
end;

local function poser(uic, vrai, quoi)
	if uic and is_string(vrai) and vrai ~= "" and uic:GetStateText() ~= vrai then
		uic:SetStateText(vrai);
		constat("pose:" .. quoi .. ":" .. vrai, quoi .. " remplace par « " .. vrai .. " »");
	end;
end;

-- En-tête de l'écran : nom de faction d'Alberic et race du seigneur choisi (le jeu ne les remplit pas toujours sur
-- notre campagne ; journal du 24.09.2026 : « Hommes-bêtes » resté affiché avec Orion). Textes de CA, sauf Bordeleaux.
local function reparer_entete(ecran, seigneurs)
	local choisi = nil;
	for _, b in ipairs(seigneurs) do
		if b:CurrentState() == "selected" or b:CurrentState() == "selected_hover" then
			choisi = b:GetProperty("lord_key");
		end;
	end;
	local s = choisi and SEIGNEURS[choisi];
	if s then
		for _, chemin in ipairs(CHEMINS_RACE) do
			local uic = find_uicomponent(ecran, unpack(chemin));
			poser(uic, common.get_localised_string("cultures_name_" .. s[2]), "race (" .. chemin[#chemin - 3] .. ")");
		end;
		if choisi == ALBERIC then
			local uic = find_uicomponent(ecran, unpack(CHEMIN_NOM_FACTION));
			if not uic then
				constat("sans_label", "label_faction_name introuvable");
			end;
			poser(uic, common.get_localised_string("campaign_localised_strings_string_saison_nom_bordeleaux"),
				"nom de faction d'Alberic");
			if not deja_vu["errants"] then
				deja_vu["errants"] = true;
				pcall(chercher_errants, ecran, "campaign_select_new", 0);
			end;
		end;
	end;
	-- textes bruts restants (écran sans seigneur choisi) : comme avant
	for _, nom in ipairs(TEXTES_BRUTS) do
		local uic = find_uicomponent(ecran, nom);
		if uic then
			local texte = uic:GetStateText();
			constat("texte:" .. nom .. ":" .. tostring(choisi) .. ":" .. tostring(texte),
				"en-tete " .. nom .. " = « " .. tostring(texte) .. " » (seigneur choisi : " .. tostring(choisi) .. ")");
			local s = choisi and SEIGNEURS[choisi];
			if s and (texte == nom or texte == "" or texte == poses[nom]) then
				local cle = (nom == "dy_faction") and ("factions_screen_name_" .. s[1]) or ("cultures_name_" .. s[2]);
				-- Bordeleaux : CA 9.0 la nomme « Errants de Bordeleaux » ; notre nom, celui que la campagne lui donne
				-- (saison_start.lua, change_localised_faction_name) (audit de l'avant-campagne du 25.09.2026, S1)
				if nom == "dy_faction" and s[1] == "wh_main_brt_bordeleaux" then
					cle = "campaign_localised_strings_string_saison_nom_bordeleaux";
				end;
				local vrai = common.get_localised_string(cle);
				if is_string(vrai) and vrai ~= "" and vrai ~= texte then
					uic:SetStateText(vrai);
					poses[nom] = vrai;
					journal("en-tete " .. nom .. " remplace par « " .. vrai .. " » (" .. cle .. ")");
				end;
			end;
		end;
	end;
end;


-- Plan B du verrou du DLC (demande de Charles, 25.09.2026, 17 h 15 : « Realm of the Wood Elves » obligatoire, et visible
-- AVANT le lancement). Le verrou normal est le cadenas de CA par la zone jouable (lot 2 :
-- campaign_map_playable_area_ownership_content_pack_junctions, un seul paquet, wh1_wood_elves) ; s'il fait fermer le jeu,
-- VERROU_MENU = true. Possession lue comme la mise en page de CA (campaign_select_new.twui.xml 9.0 :
-- FactionRecordContext.OwnershipProductRecordList.Any(IsOwned == false)) sur la faction d'Orion, rattachée au paquet
-- wh1_wood_elves (produit TW_WH1_WOOD_ELVES). Si l'évaluation échoue ou ne rend rien : on ne grise rien.
-- 25.09.2026, 18 h : le cadenas par la zone jouable, une seule ligne, fait fermer le jeu 20 s après le lancement
-- (pack de 17 h 54, essais Duc et Kemmler) : plan B allumé.
local VERROU_MENU = true;
local bouton_grise = false;
local etat_avant = nil;			-- état du bouton de lancement avant que nous le grisions (CurrentState de CA)

local function dlc_elfes_possede()
	-- interrupteur d'essai (script de menu du pilote de la construction) : simule un joueur sans le DLC ; il allume
	-- aussi le plan B (VERROU_MENU), pour l'éprouver sans rien changer d'autre
	if _G.saison_essai_menu_sans_dlc == true then
		constat("essai_menu", "essai : DLC Realm of the Wood Elves simule absent (saison_essai_menu_sans_dlc)");
		return false;
	end;
	local ok, manque = pcall(function()
		return common.get_context_value("CcoFactionRecord", "wh_dlc05_wef_wood_elves", "OwnershipProductRecordList.Any(IsOwned == false)");
	end);
	if not ok or manque == nil then
		constat("dlc_inconnu", "possession du DLC illisible (" .. tostring(manque) .. ") : rien de grise");
		return true;
	end;
	return manque ~= true;
end;

local function message_dlc()
	local ok, t = pcall(function() return common.get_localised_string("saison_des_revelations_dlc_requis") end);
	if ok and is_string(t) and t ~= "" then
		return t;
	end;
	return "La Saison de la Révélation nécessite le DLC « Realm of the Wood Elves ».\n\n"
		.. "The Season of Revelation requires the Realm of the Wood Elves DLC.";
end;

-- rend le bouton de lancement tel que CA le laisse, si nous l'avions grisé (autre campagne affichée, écran quitté)
local function rendre_bouton(racine)
	if not bouton_grise then
		return;
	end;
	local b = find_uicomponent(racine, "campaign_select_new", "button_start_parent", "button_start_campaign");
	if b then
		-- l'état d'avant, pas « active » d'office : une campagne que CA verrouille le reste (revue de la bêta, M5)
		local etat = etat_avant or "active";
		pcall(function() b:SetDisabled(etat == "inactive"); b:SetState(etat); end);
	end;
	etat_avant = nil;
	bouton_grise = false;
	journal("bouton de lancement rendu (autre campagne ou ecran quitte)");
end;

local function verrou_menu(racine)
	if not (VERROU_MENU or _G.saison_essai_menu_sans_dlc == true) or dlc_elfes_possede() then
		return;
	end;
	local b = find_uicomponent(racine, "campaign_select_new", "button_start_parent", "button_start_campaign");
	if b then
		pcall(function()
			-- l'état laissé par CA, rendu tel quel en quittant notre campagne (revue de la bêta, M5)
			if not bouton_grise then
				etat_avant = b:CurrentState();
			end;
			b:SetState("inactive");
			b:SetDisabled(true);
			b:SetTooltipText(message_dlc(), true);
		end);
		if not bouton_grise then
			journal("DLC Realm of the Wood Elves absent : bouton de lancement grise");
		end;
		bouton_grise = true;
	end;
	-- le message, une fois par visite de l'écran
	if not deja_vu["verrou_boite"] then
		deja_vu["verrou_boite"] = true;
		pcall(function()
			local boite = UIComponent(racine:CreateComponent("saison_dlc_requis_menu", "UI/Common UI/dialogue_box"));
			local texte = find_uicomponent(racine, "saison_dlc_requis_menu", "DY_text");
			if texte then
				texte:SetStateText(message_dlc(), "saison_dlc_requis_menu");
			end;
			boite:PropagatePriority(1000);
			core:add_listener("saison_dlc_requis_menu_clic", "ComponentLClickUp",
				function(context) return context.string == "button_tick" or context.string == "button_cancel" end,
				function()
					local c = find_uicomponent(core:get_ui_root(), "saison_dlc_requis_menu");
					if c then
						c:Destroy();
					end;
				end,
				false);
		end);
	end;
end;


local function regarder()
	local racine = core:get_ui_root();
	local ecran = find_uicomponent(racine, "campaign_select_new");
	if not visible(ecran) then
		bouton_grise = false;		-- l'écran quitté : le bouton est recréé à la prochaine visite
		if fait or race_cliquee or next(deja_vu) then
			fait, race_cliquee, deja_vu = false, false, {};		-- écran quitté : se réarme
		end;
		return;
	end;
	constat("ecran", "ecran ouvert");
	if _G.saison_essai_auto == true then
		constat("essai", "banc d'essai present : choix d'office quand meme (Charles, 24.09.2026)");
	end;
	local b = find_uicomponent(racine, "campaign_select_new", "button_start_parent", "button_start_campaign");
	constat("campagne:" .. tostring(b and b:GetProperty("campaign_key")), "campagne affichee : " .. tostring(b and b:GetProperty("campaign_key")));
	if not notre_campagne_affichee(racine) then
		rendre_bouton(racine);
		return;
	end;
	verrou_menu(racine);
	local seigneurs = boutons_seigneurs(racine);
	reparer_entete(ecran, seigneurs);		-- aussi pendant le banc d'essai : ne fait que remplacer des textes bruts
	-- Charles (24.09.2026, 01 h 18) : le choix d'office vaut AUSSI pendant les essais automatiques ; le banc choisit
	-- ensuite son seigneur par-dessus (un seul clic de race par visite : son défilement des races n'est jamais contrarié)
	if fait then
		return;
	end;
	if #seigneurs > 0 then
		-- une race est déjà choisie : prendre Orion s'il est là et que rien n'est sélectionné, sinon laisser faire
		for _, b in ipairs(seigneurs) do
			if b:CurrentState() == "selected" or b:CurrentState() == "selected_hover" then
				journal("seigneur deja choisi : " .. tostring(b:GetProperty("lord_key")));
				fait = true;
				return;
			end;
		end;
		for _, b in ipairs(seigneurs) do
			if b:GetProperty("lord_key") == SEIGNEUR then
				b:SimulateLClick();
				journal("Orion choisi d'office");
				fait = true;
				return;
			end;
		end;
		-- en-tête encore brut (« dy_race ») et aucun seigneur sélectionné : aucune race n'est vraiment choisie, la liste
		-- ne montre qu'un bouton gabarit ; on passe au clic de la race des Elfes sylvains
		local entete = find_uicomponent(ecran, "dy_race");
		local brut = entete and (entete:GetStateText() == "dy_race" or entete:GetStateText() == "");
		if not brut then
			journal(#seigneurs .. " seigneur(s) listes, aucun choisi, Orion absent : choix du joueur respecte");
			fait = true;		-- une autre race est choisie : c'est le choix du joueur
			return;
		end;
		constat("gabarit", #seigneurs .. " bouton(s) listes mais en-tete brut : aucune race choisie");
	end;
	-- aucune race : les Elfes sylvains, une seule fois par visite
	if race_cliquee then
		return;
	end;
	local race = find_uicomponent(racine, "campaign_select_new", "culture_list", CULTURE, "race_button");
	if not race then
		constat("sans_race", "aucune race choisie, mais bouton des Elfes sylvains introuvable (culture_list > " .. CULTURE .. " > race_button)");
	end;
	if race then
		race_cliquee = true;
		race:SimulateLClick();
		journal("Elfes sylvains choisis d'office");
	end;
end;


local tic;
tic = function()
	local ok, err = pcall(regarder);
	if not ok then
		out("La Saison des Revelations : choix par defaut : " .. tostring(err));
	end;
	core:get_tm():real_callback(tic, PERIODE_MS);
end;

core:add_ui_created_callback(function()
	core:get_tm():real_callback(tic, PERIODE_MS);
end);
