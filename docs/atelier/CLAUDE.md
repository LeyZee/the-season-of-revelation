# Atelier de modding Total War — « La Saison des Révélations »

Réécrit le 23.09.2026 vers 15 h (ménage demandé par Charles) : ce fichier dit **l'état actuel, qui fait quoi, les
recettes et les règles**. La chronique complète du 20 au 23.09.2026 (ancien `CLAUDE.md`) est dans
`05-journal\historique-documents\CLAUDE-2026-09-23-1500.md` ; ne la lire que pour retrouver l'origine d'une décision.

## 1. Lire d'abord, dans cet ordre

1. Ce fichier en entier.
2. `README.md` (organisation du dossier, rituel de séance, comment consigner une erreur).
3. `ERREURS-ET-LECONS.md` : le sommaire « Règles vivantes » en tête, puis les entrées depuis le n° 287 (jeu en 9.0.2) ;
   le reste à la demande.
4. Les guides de l'Atlas de l'étape du jour (`05-journal\2026-09-23-extension-carte\travail\site\atelier\`, § 6), puis
   `GUIDE.md` : § 12.3 (terrain), § 15 (pièges connus, numérotés), le reste au besoin.
5. `04-projets\saison-des-revelations\notes.md` (la fiche du projet : les demandes de Charles dans ses mots).
6. `05-journal\INDEX.md` (ce qui est vivant, ce qui est remplacé), puis le journal de ton chantier. Les passations du
   23.09 (`05-journal\2026-09-24-passations\`) donnent l'origine des chantiers, **pas leur état** : l'état est au § 4.

**À chaque reprise** : relire `%APPDATA%\The Creative Assembly\Warhammer3\crash_report\` et `save_games\` (erreur 69) ;
vérifier que `user.script.txt` ne contient que `mod !saison_des_revelations_fr.pack;` et `mod saison_des_revelations.pack;`
(depuis le 25.09.2026, 23 h 58 : le principal est en anglais, Charles joue en français ; rien qui ferme le jeu).

## 2. Le projet

Transposer dans Warhammer 3 la mini-campagne « La Saison des Révélations » de Warhammer 1 (campagne
`wh_dlc05_wood_elves`, carte `wh_dlc05_wood_elves_map_1`, 400 × 440 hex, 61 régions), à l'échelle de la mini-campagne.
Projet de Charles (francophone, joue et juge en jeu, captures WH1 / WH3 côte à côte = la référence).
Second projet, **Saison Expanded** : toute la Bretonnie (carte `saison_expanded_map`, 560 × 905, WH1 en x + 120,
y + 330 ; campagne `saison_expanded` ; profil `SAISON_CARTE=expanded` de `02-scripts\carte_config.py`) ; ses packs ne
sont jamais chargés avec ceux de la Saison.

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
- **Fleuves navigables d'Expanded (04.10.2026, confirmé par Charles)** : « il faut vraiment suivre le lore au niveau des
  rivières et des voies navigables, même si ça embête, même si les découpages régionaux, c'est un carnage ». Brienne,
  Grismerie, Sannez suivent le cours du lore (WH1, Atlas, `rivieres_lore.py`) ; villes et régions s'adaptent, jamais
  l'inverse. Expanded seulement, jamais la carte de la Saison. Lot de données : session « Expanded map integration et
  polish », après un démarrage de référence d'Expanded validé par Charles (`04-projets\banc-fleuve\`).
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
  ANGLAIS et la traduction française est un mod à part (`!saison_des_revelations_fr.pack`, objet Workshop 3808029376,
  « Non classée », objet requis : la Saison) ; `!saison_des_revelations_en.pack` n'existe plus (erreur 278). Publiés le
  25.09 vers 23 h 15 : la version de 20 h 47 + textes anglais ; la mise à jour de compatibilité (pack de 21 h 46,
  rangé dans `05-journal\verif-testeur-20260925-2236\`, dossier retiré au ménage du 03.10, remis dans `data\` à 23 h 21
  pour l'essai de Charles) : SOLS
  VALIDÉS par Charles (23 h 35, catalogue séparé) ; RÉGIMENTS DE RENOM du Duc validés par Charles (23 h 50, par
  script, notre campagne seule). Manque trouvé par Charles : l'écran de sélection du Duc n'a pas d'effets de faction
  (aucune ligne `frontend_factions` pour Mousillon) : lot demandé à la session IA. Ensuite reconstruction au format
  anglais + traduction et envoi. Le lanceur cache un pack publié tant qu'on n'est pas abonné
  (erreur 280) : Charles lance `Warhammer3.exe` directement (lit `user.script.txt`).

## 3. Les sessions et leurs domaines (travail en parallèle)

| Session | Domaine (seule à écrire) |
|---|---|
| **Construction** | pack (`build_pack.py`), startpos et `zz_startpos_db.pack`, chaîne du terrain, essais automatiques, `CLAUDE.md`, `GUIDE.md`, `ERREURS-ET-LECONS.md` (**seule rédactrice** : les autres lui envoient leurs erreurs), `README.md`, `notes.md` |
| **IA et modding 3D** | données de jeu (lots de `donnees_campagne.py`, `tables_gameplay.py`), scripts de campagne (`04-projets\...\scripts-campagne\`, dont le Duc écarlate : `saison_duc.lua`), textes (`textes\*.json`), masques et matériau d'eau (`masques_eau_carte.py`), mise des illustrations au format du jeu |
| **Rendu de la carte** (à partir du 23.09) | peaufinage visuel, chaînes du terrain, éclairage (`eclairage_wh1.py`) ; journal et point de reprise : `05-journal\2026-09-23-rendu-carte\journal-rendu.md` |
| **Illustrations** (à partir du 24.09) | prompts, guide de style et suivi des images (`04-projets\...\illustrations\`) ; les images vont dans le pack par la session « IA et modding 3D » |
| **Extension carte Bretonnie est** | carte papier de l'extension et site public de l'Atlas (`05-journal\2026-09-23-extension-carte\`, source des guides : `travail\atelier_v2.py`) ; jamais le startpos ni le pack. **Publication du site (Charles, 05.10)** : toute session peut publier, une à la fois, en le disant aux autres, et selon la règle de l'erreur 340 (partir de la liste complète du déploiement en ligne, comparer tous les fichiers dans les deux sens, avant et après) |
| **Expanded map integration et polish** (03.10) | grille, terrain, kit et départ d'Expanded (`04-projets\saison-expanded\`, journal `JOURNAL.md`) ; factions de l'Atlas (confiées par Charles le 03.10) ; lot de données des fleuves (04.10) |
| **Expanded map avec vaults et détails sud** (03.10) | Voûtes, minicarte d'Expanded, Bois Rêveur, site de l'Atlas pour ces parties |
| **Recherche or et rivières navigables** (04.10) | banc des fleuves (`04-projets\banc-fleuve\`), mesures sur les cartes de CA ; jamais le kit |
| **Lakemen** (deux sessions, 03.10) | passe de test et séries d'essais (`05-journal\2026-10-03-passe-test-dix-seigneurs\`), modèles et lore des Lakemen |
| **Mise à jour miniatures Steam** (04.10) | images et envois du Workshop par le lanceur (`05-journal\2026-10-04-miniatures-steam\`) |

La session « Mise à jour 9.0 et Duc Rouge » (24.09) a fini : suite dans `05-journal\2026-09-24-vampires-9.0\`.
La « Construction » est la session « Saison des Révélations » (même session, deux noms). L'état du § 4 n'est écrit que par
elle : les autres sessions lui envoient le leur.

Protocole : **préavis de 5 minutes avant toute écriture dans le kit** (`02-scripts\preavis.py heure`, puis écrire
seulement à cette heure) ; jamais le jeu, Terry ni le startpos sans prévenir
les autres ; **ne pas reconstruire le pack pendant un essai en jeu** ; ranger ; supprimer seulement avec l'accord de
Charles, liste montrée d'abord, par la corbeille (jamais d'effacement définitif).

## 4. État au 04.10.2026, 23 h (version du 25.09 : `05-journal\historique-documents\CLAUDE-20261004-2252-avant-nettoyage.md`)

- **Jeu et kit en 9.0.2** ; kit réécrit par la mise à jour du 27.09, restauré le 03.10 (erreurs 290, 326). Le
  « téléchargement » Steam du 04.10 à 17 h 16 était une mise à jour d'objets Workshop, pas du jeu (erreur 339).
- **SAISON (bêta)** : `data\` = CANDIDAT du 03.10 (SHA-1 0F3D530A… / FR 1A9DC1A9…, accord de Charles à 13 h 50) ;
  publiés = maj1 du 25.09, 23 h 55 (570C29A5… / 1620A33F…, dans `pack-backups\`). Rien envoyé depuis ; page de la
  Saison en vérification Steam ; miniatures refusées (code Steam « #25 », erreur 339 ; 4 objets vides orphelins créés
  par le lanceur, à supprimer par Charles). Ouverture publique : voulue (02.10), non
  décidée. Bogue du `find` en texte brut corrigé (erreur 287).
- **Plantage de rendu `+0x1AC3FF2`** : cause désignée, montagnes de WH1 au matériau 49 (erreur 327). Conversion au
  matériau 68 FAITE DANS LE KIT (partagé avec Expanded) ; pack `essai68` : 15 parties, 0 plantage (≈ 30 pour trancher).
  **NON validée par Charles : aucun pack de la Saison reconstruit ni envoyé avant sa décision** (décision A5 du
  nettoyage) ; packs `essai68` encore dans `data\`.
- **EXPANDED** (`saison_expanded_map`, 560 × 905, WH1 en x + 120, y + 330 ; session « Expanded map integration et
  polish ») : grille, terrain (BOB du 04.10, 19 h 28 ; 75 tuiles de côte encore manquantes), 16 factions de l'Atlas +
  `saison_hef_tor_soleil`, départ, tout dans le kit ; pack de 20 h 36 + `zz_startpos_db_expanded.pack` : **LA CAMPAGNE
  CHARGE** (Orion, tour 1, aucun plantage ; causes trouvées : erreurs 329 à 338). Pack d'ESSAI : pas de scripts de
  campagne, startpos sans `__save_counter`, rien d'éprouvé après le tour 1. Chaîne du kit relancée le 04.10 à 23 h 46
  (« attaque tout ça » ; routes de l'Atlas, faune, fosses comblées) : startpos et pack à refaire ensuite
  (`chaine_expanded.sh`). À faire : Charles valide le démarrage en jeu ; ambiance de Slaanesh (prête, éteinte :
  `SAISON_ECLAIRAGE_REVES=1`) ; lot des fleuves. Jamais chargé avec la Saison.
- **FLEUVES NAVIGABLES v3** (Brienne, Grismerie + Ois, Sannez) : validés par Charles pour Expanded seulement ; lot après
  le démarrage de référence (`04-projets\banc-fleuve\RAPPORT_v3.md`).
- **RÈGLE DU 04.10** : guides à la lettre dans l'ordre de vérité (§ 6) ; deux lignes du guide CAIME fausses (erreurs 336,
  337), corrections envoyées à la session Extension.
- **GRAND NETTOYAGE** (`05-journal\2026-10-04-grand-nettoyage\`, `RAPPORT.md`) : décisions A1 à A6 prises par Charles
  (ports à la CA, la Saison gardant les siens ; BOB sous cdb assumé ; `tile_map.png` de la Saison laissée ; RPFM 5.1.1 à
  essayer sur copie ; pas de pack de la Saison avant les montagnes ; packs d'essai rangés ensuite) ; corrections B en cours.
- **Reprise** : Expanded → `04-projets\saison-expanded\JOURNAL.md` ; Saison → erreur 327 et
  `05-journal\2026-10-03-passe-test-dix-seigneurs\bilan-serie-candidat-1250-1640.md` ; fleuves → `banc-fleuve\` ; essais
  d'Expanded → `05-journal\2026-10-04-essais-auto-expanded\` (pilote `SAISON_CARTE=expanded`, option `--cdb-avant`).

## 5. Recettes

Prérequis communs : **jeu et Terry fermés**, `rpfm_server` lancé (`02-scripts\lancer-outils.ps1 -Outil rpfm-server`)
et **sous 8 Go** (il fuit à chaque pack : le relancer avant chaque pack ; `build_pack` refuse au-delà ; ce n'est pas la
cause du plantage de rendu, erreur 265 ; RPFM 5.1.x corrige cette fuite, à essayer sur copie, décision A4 du 04.10),
Steam lancé (sinon le jeu sort en 6 s). **Prévenir Charles avant tout lancement du jeu** (il clique dedans, erreurs 124
et 132) ; ne jamais piloter l'écran sans son accord du moment (erreur 108).

- **Pack** : `python 02-scripts\verifier_textes.py` (0 défaut), `python 02-scripts\verifier_groupes.py` (groupes de
  régions = liste explicite, erreur 156), `python 02-scripts\build_pack.py`, puis
  `python 02-scripts\injecter_textes.py --apply`. Relire le journal :
  chaque table d'un lot neuf doit y figurer avec son nombre de lignes (erreur 131). `build_pack` s'arrête si un de nos
  modèles cite encore un substitut de CA (`modeles_wh1.py --apply` d'abord, erreur 254). **Décision A5 (04.10), codée** :
  `build_pack` refuse le pack de jeu de la Saison tant que Charles n'a pas tranché sur les montagnes au matériau 68
  (`SAISON_A5_LEVEE=1` ensuite) ; un pack d'essai sous un autre nom reste permis. **Exception assumée (Charles, 05.10)** :
  `zz_startpos_db.pack` et `zz_startpos_db_expanded.pack` restent dans `data\` (les scripts y écrivent, les recettes les
  y lisent, le jeu les ignore sans ligne `mod` ; le 03.10, `zz_startpos_db.pack` a sauvé 19 lignes de départ), contre le
  guide des outils qui demande de les ranger.
- **Tables de départ → startpos** :
  1. `synchroniser_pack_startpos.py --table <start_pos_...> --cle ID [--apply]` (kit → `zz_startpos_db.pack`) ;
  2. `valider_start_pos.py` (0 cellule à corriger) ;
  3. pack reconstruit (les tables hors `start_pos_*` que la génération lit y sont) ;
  4. créer `data\campaigns\<campagne>\` et `data\campaign_maps\<carte>\` s'ils n'existent pas (sinon ni startpos ni
     données de l'IA, erreur 331) ; garder `user.script.txt` de Charles, puis `startpos_manuel.py --campagne wh_dlc05_wood_elves --pack
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
  Expanded : `SAISON_CARTE=expanded` (sorties dans `05-journal\2026-10-04-essais-auto-expanded\`, amorce de scripts et
  journal de script ajoutés au pack d'essai, `--packs-avant`, `--cdb-avant`). Pour l'instant, le pilote ne fait pas
  passer les tours d'Expanded (pas de scripts de campagne) : il prouve le chargement, pas la suite.
- **Expanded (campagne neuve), en plus des recettes ci-dessus** (erreurs 329 à 338) : `SAISON_CARTE=expanded` pour
  `build_pack.py` et `injecter_textes.py` ; tables de départ par `startpos_db_expanded.py --apply` (→
  `zz_startpos_db_expanded.pack`) puis `valider_start_pos.py --pack …` ; créer `data\campaigns\saison_expanded\` et
  `data\campaign_maps\saison_expanded_map\` AVANT `startpos_manuel.py --campagne saison_expanded --pack saison_expanded.pack
  --pack zz_startpos_db_expanded.pack --sans-working-dir --ai-map-data` (sinon ni startpos ni données de l'IA), puis
  ranger startpos et données de l'IA dans `04-projets\saison-expanded\{startpos,ia-carte}\` ; `campaigns.mask` vide ;
  aperçu au rapport du monde ; jamais de jonction de propriété de DLC pour nos clés ; modèles d'emplacement et bâtiments
  pris tels quels chez CA pour la sous-culture du maître ; pas de colonie pour une faction que CA fait partir en horde ;
  ports en 16 + 3 à la CA, cases de port [mer, mer, plage] (à défaut [mer, mer, mer]) ; CAIME : `generate-region-borders`
  (fork) avant `validate --all` et `process`. Chaîne de la GRILLE d'Expanded (05.10, session Expanded, outils de
  `04-projets\saison-expanded\outils\`) : `chaine_grille_expanded` → `ports_expanded --apply` →
  `integrer_fleuves_expanded.py --apply` (depuis une grille SANS fleuves) → `routes_expanded --apply` → `cols_sprawl
  --apply` → `retouches_cotes --apply` → CAIME `generate-region-borders` → `valider_caime.py` ; une grille changée = tables
  de départ resynchronisées et startpos neuf. Chaîne du TERRAIN d'Expanded (session Expanded, tout avec
  `SAISON_CARTE=expanded`) : `projet_expanded.py` (appelle lui-même `couches_a_jour` en tête, erreur 344,
  `chenaux_fleuves` avant l'écriture du relief, `rivieres_maillages_expanded.ecrire()` à la fin, `camps_expanded` après
  la vie) → `eau_materiau_expanded.py --apply` → (préavis) `kit_expanded.py
  --apply` → CAIME `validate --all` → `process --all` (borné à 5 min, erreur 338) → `compiler_terrain_bob.py --carte
  saison_expanded_map --apply` (contrôle du guide BOB : 12/12, 0 quadtree, trous de côte) → `shroud_heights`,
  `camera_heightmap`, `lf_normal_depuis_relief`, `textures_sol_wh1`, `outils\textures_reves.py`,
  `outils\arbres_expanded.py --apply`, `outils\controle_anomalies.py` ; script de la session :
  `powershell -NoProfile -ExecutionPolicy Bypass -File 04-projets\saison-expanded\outils\chaine_kit_expanded.ps1` (après
  `projet_expanded.py`, `eau_materiau_expanded.py --apply` et le préavis ; il appelle `outils\valider_caime.py`). Chaîne complète du pack
  (rpfm relancé avant chaque pack, `relancer_rpfm.sh`) : `SAISON_ECLAIRAGE_REVES=1 SAISON_ECLAIRAGE_ARDEN=1 bash
  02-scripts\chaine_expanded.sh` (ambiances de CA citées telles quelles : Slaanesh sur le Bois Rêveur, `woodelf` sur
  l'Arden, 2 cylindres, demande de Charles du 05.10 ; éteintes sans ces variables ; à juger en jeu, erreur 251) (journaux dans
  `05-journal\2026-10-04-essais-auto-expanded\`).
- **Photo avant une mise à jour du jeu** : `instantane_jeu.py --etiquette <version>` ; après : `--comparer <version>`.

## 6. Règles non négociables

- **Les guides d'abord (Charles, 04.10.2026 : « qu'on suive à la lettre »)** : avant chaque étape, relire la section du
  guide de l'Atlas (`05-journal\2026-09-23-extension-carte\travail\site\atelier\<caime|terry|bob|rpfm|outils|ia>\index.md`,
  bretonia.dev/atelier) et la documentation officielle de l'outil, et la suivre à la lettre ; tout écart se justifie et se
  consigne (entrée d'`ERREURS-ET-LECONS.md` et liste du nettoyage, `05-journal\2026-10-04-grand-nettoyage\`). Ordre de
  vérité quand ils divergent : documentation officielle et code de l'outil > fait prouvé en jeu > guides de l'Atlas > nos
  fichiers de travail (nos guides ont déjà eu tort : erreurs 336, 337). Avant tout export CAIME : `validate --all`, Error ET Warning des villes lus et corrigés (ville 19 hex ; port
  16 + 3 : 16 hex de terre, 3 hex de port consécutifs de l'anneau 2, deux en mer et un sur la plage, comme CA, erreur 337 ;
  « un en mer » n'est que le minimum du validateur). Un guide qui décrit « ce que fait CA » se vérifie sur les fichiers de
  CA. Le 04.10, des heures de débogueur ont retrouvé une règle déjà écrite dans notre guide CAIME (erreurs 334, 335).

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
  (adresses du patch 8.1 : **à revérifier en 9.0.2**) ; lecteur ESF : `lire_esf.py` ; DLL : `lire_dll.py`. Plantage
  d'un CHARGEMENT de campagne : `essai_tours_auto.py --cdb-avant <fichier>` avec un point d'arrêt qui journalise
  (`dpa @rcx`) à l'entrée de la fonction fautive : il a nommé Bordeleaux, le Poste de la Pierre Noire et Tor Soleil
  (erreur 334 ; fichiers dans `04-projets\saison-des-revelations\essai-auto\cdb\`).
- Journaux du jeu : `script_log_JJMMAA_HHMM.txt` dans le dossier du jeu (les clics y sont journalisés avec leur chemin),
  `%APPDATA%\...\logs\mp_log.txt` (création / destruction de l'environnement de campagne).
- **Écouteurs de script** : `required.lua` protège `core.event_callback` ; une condition ou un rappel qui plante est
  nommé une fois dans le `script_log` (« ecouteur [clé] en erreur sur <évènement> ») et n'arrête plus l'évènement pour
  les autres (erreurs 213, 230, 231, 252 ; GUIDE § 15 n° 148). Adresses mémoire relevées avant le 24.09 à 16 h 07 : 8.1 ; depuis le ~01.10 : 9.0.2 (toute
  adresse porte sa version).
- **Ne pas refaire** : le « témoin campagne vanilla » n'est pas un contrôle valide ; sans `--sans-working-dir` la
  génération sort en 9 s sans rien faire (erreur 39) ; dans CAIME, `Impassable = 1` veut dire franchissable (erreur 40) ;
  `frontend.start_campaign` ne lance pas notre campagne (erreur 128).

Exécutable CAIME : `01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe` (`--help`). Outils :
`02-scripts\lancer-outils.ps1 -Outil terry|bob|dave|rpfm|rpfm-server|caime`. `cdb.exe` : paquet WinDbg.
