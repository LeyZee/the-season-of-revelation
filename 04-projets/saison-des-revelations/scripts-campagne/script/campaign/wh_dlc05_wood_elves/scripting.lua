-----------------------------------------------------------------------------------
--	La Saison des Révélations (mini-campagne de Warhammer 1 portée dans Warhammer 3)
--
--	Amorce de la campagne, identique à celle des campagnes de CA dans WH3 (wh3_main_chaos, wh3_main_prologue) :
--	bibliothèques, nom de campagne tiré du dossier, dossier de la campagne ajouté au chemin des require, puis
--	required.lua, qui liste les scripts de la campagne.
-----------------------------------------------------------------------------------

load_script_libraries();

cm:set_campaign_name(get_folder_name_and_shortform());

cm:require_path_to_campaign_folder();

require("required");
