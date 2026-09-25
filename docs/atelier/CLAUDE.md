# Atelier de modding Total War — « La Saison des Révélations »

Réécrit le 23.09.2026 vers 15 h (ménage demandé par Charles) : ce fichier dit **l'état actuel, qui fait quoi, les
recettes et les règles**. La chronique complète du 20 au 23.09.2026 (ancien `CLAUDE.md`) est dans
`05-journal\historique-documents\CLAUDE-2026-09-23-1500.md` ; ne la lire que pour retrouver l'origine d'une décision.

## 1. Lire d'abord, dans cet ordre

1. Ce fichier en entier.
2. `README.md` (organisation du dossier, rituel de séance, comment consigner une erreur).
3. `ERREURS-ET-LECONS.md` : le sommaire « Règles vivantes » en tête, puis les entrées des deux derniers jours (200 et
   plus : état 9.0) ; le reste à la demande.
4. `GUIDE.md` : § 12.3 (terrain), § 15 (pièges connus, numérotés), le reste au besoin.
5. `04-projets\saison-des-revelations\notes.md` (la fiche du projet : les demandes de Charles dans ses mots).
6. `05-journal\INDEX.md` (ce qui est vivant, ce qui est remplacé), puis le journal de ton chantier. Les passations du
   23.09 (`05-journal\2026-09-24-passations\`) donnent l'origine des chantiers, **pas leur état** : l'état est au § 4.

**À chaque reprise** : relire `%APPDATA%\The Creative Assembly\Warhammer3\crash_report\` et `save_games\` (erreur 69) ;
vérifier que `user.script.txt` ne contient que `mod saison_des_revelations.pack;` (rien qui ferme le jeu).

## 2. Le projet

Transposer dans Warhammer 3 la mini-campagne « La Saison des Révélations » de Warhammer 1 (campagne
`wh_dlc05_wood_elves`, carte `wh_dlc05_wood_elves_map_1`, 400 × 440 hex, 61 régions), à l'échelle de la mini-campagne.
Projet de Charles (francophone, joue et juge en jeu, captures WH1 / WH3 côte à côte = la référence).

Décisions de Charles, à ne pas rediscuter :
- **Refusé** : découper la carte des Empires Immortels. On garde l'échelle et la géographie de WH1.
- **La carte est celle de WH1 à 100 %** (relief, objets, arbres, textures, eau) ; de WH3 seulement ce qui manque, cohérent.
- **Gameplay 100 % WH3 + histoire de WH1** ; bâtiments, monuments, arbres de technologie selon WH3.
- **Les campagnes coexistent, mod actif** : jamais remplacer une table de CA (clés à nous).
- **Dix seigneurs jouables** : Orion, Durthu, Alberic, la Fée Enchanteresse, Morghur, le Duc écarlate (« Duc Rouge »
  avant la 9.0), Drycha, Heinrich Kemmler, Grom la Panse, et les Sœurs du Crépuscule (24.09 ; en armée près de la ruine
  de Tal Jul Finel, paix et accès militaire avec Wydrioth) ; identifiants de départ : `essai_tours_auto.SEIGNEURS`.
- **Victoire (décision du 24.09.2026, format 9.0)** : les dix seigneurs ont une victoire courte et une longue propres
  à la Saison (`05-journal\2026-09-24-vampires-9.0\proposition-victoires-saison.md`, `saison_victoires_9_0.lua`) ; pour
  Orion et Durthu, la victoire de WH1 devient leur longue, enrichie ; ni la courte ni la longue ne finissent la partie,
  seule la domination (27 colonies) y met fin, comme dans la 9.0. La domination reste celle de WH3 même si elle tombe
  avant la victoire longue de Morghur ou de Grom ; après une victoire, on continue à jouer (Charles, 25.09.2026).
- **Équilibrage (25.09.2026)** : « lore d'abord, plus difficile que le jeu de base, grimdark, jouable et fun ». Mousillon
  garde sa menace (revenu de Puissance de l'IA) ; la boule de neige se règle par les guerres (Grom / Aquitanie au tour 15,
  alliance Fée / Aquitanie, précédent : Armand d'Aquitaine et la Fée contre Mallobaude, End Times).
- **Clés de jeu (25.09.2026)** : `saison_` pour tout ce que nous créons, extension à toute la Bretonnie comprise ;
  `wh_dlc05_` seulement pour ce qui vient de WH1. Les clés de l'extension aux noms abandonnés (Thurin, Portsall,
  Saint-Lambert, Euresbourg, Venin-Rouge) sont renommées avant toute table ; la faction L'Anguille passe de `ext_` à
  `saison_`.
- **Noms** : formes officielles de GW (traductions françaises officielles, vérifiées par la session « IA et modding 3D »).
  Dans les textes du jeu : « la Saison de la Révélation » (forme officielle de WH1 en français ; EN « The Season of
  Revelation ») ; l'atelier et le pack gardent le nom de projet « La Saison des Révélations ».
- **Éclairage (25.09.2026)** : zones d'éclairage remises une à une, « à la manière de CA » (pas de teinte, identité par
  LUT, brouillard, soleil, ambiance), chacune montrée en image puis essayée en jeu (erreur 251).
- **Rivières, deltas, côtes : « comme dans Warhammer 1 »** (25.09.2026) : correctifs C1 à C4 validés (matériau d'eau,
  lit sombre, berges basses, mer plus sombre près des côtes).
- **LE PACK CONTIENT DES FICHIERS DE WH1.** Décision de Charles du 25.09.2026 : bêta sur le Workshop, lien donné
  seulement dans le fil Discord des volontaires ; jamais de Workshop public ni de lien publié ailleurs sans nouvelle
  décision de sa part. **Mise à jour du 25.09.2026, 21 h 30 (Charles)** : la page de la Saison
  (id 3807973986) est **« Non classée »** (visible par qui a le lien, sans être ami ; absente des recherches et du
  profil), car les moddeurs testeurs ne sont pas ses amis Steam ; DLC requis déclaré : Realm of the Wood Elves ;
  descripteurs : violence fréquente ou gore. Expanded (id 3807968769) reste masqué. Charles est désabonné de ses deux
  objets (sinon la copie du Workshop se mêle au pack de travail de `data\`). Non commercial. Fiche des testeurs : `05-journal\2026-09-25-beta\FICHE-TESTEURS.md`.
  Présentation publique (site, Discord dédié public créé par Charles) : relecteurs de lore bénévoles, Charles garde le
  dernier mot. **Nouvelle décision de Charles, 25.09.2026, 22 h 20** : « la bêta est out », le site de l'Atlas l'annonce
  et donne le lien Workshop de la Saison pour tester (remplace « bêta privée, sur invitation, sans lien Workshop ») ;
  Expanded reste masqué. Compatibilité avec les autres mods : toujours dite « non testée ». **Langues (Charles, 25.09.2026,
  23 h)** : le jeu charge les textes d'un mod quelle que soit la langue (erreur 47), donc le pack principal est en
  ANGLAIS et la traduction française est un mod à part (`!saison_des_revelations_fr.pack`, objet Workshop publié par
  Charles) ; `!saison_des_revelations_en.pack` n'existe plus (erreur 278).

## 3. Les sessions et leurs domaines (travail en parallèle)

| Session | Domaine (seule à écrire) |
|---|---|
| **Construction** | pack (`build_pack.py`), startpos et `zz_startpos_db.pack`, chaîne du terrain, essais automatiques, `CLAUDE.md`, `GUIDE.md`, `ERREURS-ET-LECONS.md` (**seule rédactrice** : les autres lui envoient leurs erreurs), `README.md`, `notes.md` |
| **IA et modding 3D** | données de jeu (lots de `donnees_campagne.py`, `tables_gameplay.py`), scripts de campagne (`04-projets\...\scripts-campagne\`, dont le Duc écarlate : `saison_duc.lua`), textes (`textes\*.json`), masques et matériau d'eau (`masques_eau_carte.py`), mise des illustrations au format du jeu |
| **Rendu de la carte** (à partir du 23.09) | peaufinage visuel, chaînes du terrain, éclairage (`eclairage_wh1.py`) ; journal et point de reprise : `05-journal\2026-09-23-rendu-carte\journal-rendu.md` |
| **Illustrations** (à partir du 24.09) | prompts, guide de style et suivi des images (`04-projets\...\illustrations\`) ; les images vont dans le pack par la session « IA et modding 3D » |
| **Extension carte Bretonnie est** | carte papier de l'extension et site public de l'Atlas (`05-journal\2026-09-23-extension-carte\`, source des guides : `travail\atelier_v2.py`) ; jamais le startpos ni le pack |

La session « Mise à jour 9.0 et Duc Rouge » (24.09) a fini : suite dans `05-journal\2026-09-24-vampires-9.0\`.

Protocole : **préavis de 5 minutes avant toute écriture dans le kit** (`02-scripts\preavis.py heure`, puis écrire
seulement à cette heure) ; jamais le jeu, Terry ni le startpos sans prévenir
les autres ; **ne pas reconstruire le pack pendant un essai en jeu** ; ranger, jamais supprimer.

## 4. État au 25.09.2026, 20 h 15 (jeu en 9.0 ; version de 03 h 30 : `05-journal\historique-documents\CLAUDE-2026-09-25-2015-avant-maj-etat.md`)

- **Jeu et kit en 9.0** depuis le 24.09 ; lignes de `raw_data\db` restaurées (erreur 206, GUIDE § 15 n° 142).
- **BÊTA : polish et revue avant la sortie** (Charles : « corrige tous les défauts avant la bêta »). Quatre revues en
  lecture seule + audit des cartes de bataille : `05-journal\2026-09-25-revue-beta\` (scripts Lua : 0 bloquant, 4
  importants corrigés par l'IA ; pack et données ; dossier de stabilité ; liste de sortie ; cartes de bataille).
  Corrections faites : hordes, Pic d'Argent différé, journal des erreurs, écouteurs de CA d'Ostankya et Yuan Bo, lot 43
  (nos régions hors des groupes de CA ; contrôle `verifier_groupes.py`), 86 textes, 10 scripts morts hors du pack
  (`SCRIPTS_ECARTES`), minicarte (même teinte, contours lissés : `preparer_minicarte.SIGMA_CONTOURS`). Salles tombées :
  éteintes pour la bêta (décision de Charles). Régiments de renom de Mousillon aux Empires : défaut connu (fiche).
- **Pack du 25.09 à 19 h 05** (pack de zéro + startpos régénéré à 18 h 57, compteur 1, 0 anomalie). Essais des dix
  seigneurs sur 10 tours en cours : Orion, Durthu, Albéric, Fée, Drycha 0 erreur ; Morghur battu au tour 8 (harde immobile
  sous `all_players_ai`, erreur 210) ; Duc et Kemmler bloqués au tour 5 par le tutoriel vampire de CA (le pilote ne
  ferme pas encore la bulle : correctif en essai ; erreur 270 pour la première tentative). Krell présent au départ.
  Verrous des DLC éprouvés (menu grisé ; message et retour au menu en campagne).
- **À faire avant la sortie** : recompilation des cartes de bataille (défilés corrigés par l'IA, erreur 271), pack final,
  startpos, pack, dix seigneurs ; partie de Charles d'au moins une heure (Duc, caméra sur la falaise de Gransette :
  plantage de rendu `+0x1AC7576` non élucidé, GUIDE § 15 n° 150) ; trois batailles jouées (forêt, siège breton,
  montagne) ; accord d'un fondateur de CAIME ; Workshop « privé » (pages préparées par la session « Extension » ; pack
  anglais pas encore). Fiche des testeurs réécrite : `05-journal\2026-09-25-beta\FICHE-TESTEURS.md`.
- **Expanded** (`04-projets\saison-expanded\`, journal `JOURNAL.md`, plan `PLAN.md`) : carte `saison_expanded_map`
  560 × 825 et campagne `saison_expanded` déclarées ; 76 régions et 21 provinces de l'Atlas déclarées (`saison_`,
  décision : l'Atlas l'emporte sur WH1 ; Fort Solstice repris en `saison_glanborielle_fort_solstice`) ; grille CAIME :
  régions, 121 villes, passage, climats, fil de rivière caché sous le voile (conseil de ChaosRobie) ; terrain Terry dans
  le bac à sable (relief de l'Atlas autour de WH1, Bois Rêveur en miroir) ; minicarte (parchemin de l'Atlas + lookup).
  Dépôt GitHub public (liste blanche, rien de WH1). Ni pack ni startpos d'Expanded encore.
- **Éclairage** : Winterheart seule, à la manière de CA (erreur 251) ; les autres zones une à une.
- **Point de reprise** : ce paragraphe, puis `05-journal\2026-09-25-revue-beta\liste-de-sortie.md`.

## 5. Recettes

Prérequis communs : **jeu et Terry fermés**, `rpfm_server` lancé (`02-scripts\lancer-outils.ps1 -Outil rpfm-server`)
et **sous 8 Go** (il fuit à chaque pack ; `build_pack` refuse au-delà ; ce n'est pas la cause du plantage de rendu,
erreur 265),
Steam lancé (sinon le jeu sort en 6 s). **Prévenir Charles avant tout lancement du jeu** (il clique dedans, erreurs 124
et 132) ; ne jamais piloter l'écran sans son accord du moment (erreur 108).

- **Pack** : `python 02-scripts\verifier_textes.py` (0 défaut), `python 02-scripts\verifier_groupes.py` (groupes de
  régions = liste explicite, erreur 156), `python 02-scripts\build_pack.py`, puis
  `python 02-scripts\injecter_textes.py --apply`. Relire le journal :
  chaque table d'un lot neuf doit y figurer avec son nombre de lignes (erreur 131). `build_pack` s'arrête si un de nos
  modèles cite encore un substitut de CA (`modeles_wh1.py --apply` d'abord, erreur 254).
- **Tables de départ → startpos** :
  1. `synchroniser_pack_startpos.py --table <start_pos_...> --cle ID [--apply]` (kit → `zz_startpos_db.pack`) ;
  2. `valider_start_pos.py` (0 cellule à corriger) ;
  3. pack reconstruit (les tables hors `start_pos_*` que la génération lit y sont) ;
  4. garder `user.script.txt` de Charles, puis `startpos_manuel.py --campagne wh_dlc05_wood_elves --pack
     saison_des_revelations.pack --pack zz_startpos_db.pack --sans-working-dir --ai-map-data` (19 s) ; remettre
     `user.script.txt`, supprimer le `.bak` ;
  5. `verifier_compteur_startpos.py <startpos>` (`__save_counter` = 1) ; `comparer_structure_esf.py --esf <nouveau>
     --reference <précédent>` ;
  6. sauvegarder l'ancien dans `05-journal\startpos-backups\`, copier le nouveau dans `04-projets\...\startpos\`,
     reconstruire le pack (le pack passe devant les fichiers en vrac, erreur 58).
- **Terrain** : la chaîne réelle (session du rendu, chaînes 13 à 15) a 8 étapes : `modeles_wh1.py --apply`, générateur,
  masques d'eau, BOB, brouillard, caméra, textures de WH1, `lf_normal_depuis_relief.py --apply` (environ 30 min, 10 Go
  libres, jeu et Terry fermés) ; puis pack, startpos, pack. `02-scripts\chaine_terrain.ps1` n'en a que 6 : à mettre à
  jour avant de s'en servir (GUIDE § 12.3). Terry ne montre ni la mer ni l'eau comme le jeu (erreur 223) : juger en jeu.
- **Essais automatiques** : `python 02-scripts\essai_tours_auto.py --seigneur <alias|tous> --tours N [--sans-ia]`
  (GUIDE § 15 n° 131) ; sorties dans `05-journal\2026-09-23-essais-auto\<horodatage>-<seigneur>\` (`bilan.json`,
  journaux, `cdb.log`, vidages). Pack d'essai séparé, retiré à la fin ; `user.script.txt` remis. Sous `all_players_ai`,
  la faction du joueur ne joue pas (erreur 210) ; un changement du pilote se valide seul par 2 tours sur un pack éprouvé
  (erreur 239) ; le temps d'un tour se lit aux horodatages (erreur 232).
- **Photo avant une mise à jour du jeu** : `instantane_jeu.py --etiquette <version>` ; après : `--comparer <version>`.

## 6. Règles non négociables

- Une erreur comprise se consigne tout de suite dans `ERREURS-ET-LECONS.md`, étiquetée `[évitable]` (avec la règle,
  codée si possible) ou `[découverte]` (avec la preuve, puis reportée dans `GUIDE.md` § 15).
- Sauvegarde dans `05-journal\db-backups\` avant toute écriture dans `raw_data\db`.
- Jamais BOB, Terry ou Tweak lancés avec des arguments devinés ; jamais `sed` avec antislashs sous Git Bash ; jamais
  `Get-Content -Raw` sur un fichier accentué ; pas de fichier Lua, Python ou `.mjs` écrit par heredoc, redirection ou
  PowerShell : toujours l'outil d'écriture (erreurs 129, 217, 237). Depuis le 24.09.2026, un crochet du projet
  (`.claude\hooks\garde_commandes.py`) refuse Python par heredoc, `python -c` composé et `sed` à antislashs (seul le
  segment qui contient `sed` compte) : écrire le script dans un fichier, puis `python fichier.py` (erreur 212).
- Jamais un fichier à nous à un chemin que CA cite ; jamais remplacer un fichier de CA hors des exceptions nommées dans
  `build_pack.py` (erreur 254). Un réglage qui porte un contrôle validé ne change qu'en annonçant le contrôle (erreur 240).
- Jamais `git add -A` dans `01-outils\CampaignMapToolkit` ; commits en anglais, fichiers nommés. Remote `origin` = amont,
  `fork` = `LeyZee/CampaignMapToolkit`.
- Rien n'est posté (Discord CAIME), envoyé en amont ni redistribué sans l'accord de Charles ; rester dans l'univers
  Warhammer ; rien d'inventé sur le lore (sources).
- Une nouvelle table de base = un essai de démarrage avant toute annonce (erreur 107) ; jamais tenir le pack ouvert
  (Terry ouvert le tient) ; un script créé dans `02-scripts` : vérifier que le nom est libre (erreur 121).
- Après tout essai de startpos : `user.script.txt` sans `quit_after_campaign_processing;`.

## 7. Diagnostic (outils qui ont débloqué)

- Tables `start_pos_*` dans un pack de mod : le jeu nomme l'enregistrement fautif dans `crash_report\bad_mods_report.txt` ;
  `valider_start_pos.py` fait la même chose sans le jeu.
- Plantage : `lire_vidage.py <.mdmp>` (sans débogueur), puis `cdb -z` ; jeu sous débogueur : `debug_chargement.py`
  (adresses du patch 8.1 : **à revérifier après la 9.0**) ; lecteur ESF : `lire_esf.py` ; DLL : `lire_dll.py`.
- Journaux du jeu : `script_log_JJMMAA_HHMM.txt` dans le dossier du jeu (les clics y sont journalisés avec leur chemin),
  `%APPDATA%\...\logs\mp_log.txt` (création / destruction de l'environnement de campagne).
- **Écouteurs de script** : `required.lua` protège `core.event_callback` ; une condition ou un rappel qui plante est
  nommé une fois dans le `script_log` (« ecouteur [clé] en erreur sur <évènement> ») et n'arrête plus l'évènement pour
  les autres (erreurs 213, 230, 231, 252 ; GUIDE § 15 n° 148). Adresses mémoire relevées avant le 24.09 à 16 h 07 : 8.1.
- **Ne pas refaire** : le « témoin campagne vanilla » n'est pas un contrôle valide ; sans `--sans-working-dir` la
  génération sort en 9 s sans rien faire (erreur 39) ; dans CAIME, `Impassable = 1` veut dire franchissable (erreur 40) ;
  `frontend.start_campaign` ne lance pas notre campagne (erreur 128).

Exécutable CAIME : `01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe` (`--help`). Outils :
`02-scripts\lancer-outils.ps1 -Outil terry|bob|dave|rpfm|rpfm-server|caime`. `cdb.exe` : paquet WinDbg.
