# Atelier de modding Total War — guide de travail

Version 2, 20 septembre 2026. Écrit pour Charles et pour toute IA (Claude, Codex, autre) qui
reprend ce dossier. Il dit **ce que sont les outils, comment on s'en sert ici, et comment produire
des cartes de campagne fonctionnelles, puis belles**. Tout ce qui suit a été lu dans les
documentations officielles, dans le code source, ou vérifié sur cette machine ; ce qui ne l'a pas
été porte la mention « à confirmer ». Une IA qui reprend commence par `CLAUDE.md` (point d'entrée), puis revient ici.

Sources primaires :
[documentation CAIME](https://tw-campaign-map-modding-team.github.io/CampaignMapToolkit/) (14 guides,
copie locale dans `01-outils\CampaignMapToolkit\docs\`), [dépôt CAIME](https://github.com/TW-Campaign-Map-Modding-Team/CampaignMapToolkit),
[manuel RPFM](https://frodo45127.github.io/rpfm/manual/) et [son chapitre serveur](https://frodo45127.github.io/rpfm/manual/server/overview.html),
[RPFM For Dummies](https://tw-modding.com/wiki/Tutorial:RPFM_For_Dummies),
[Map Making for WH3](https://tw-modding.com/wiki/Tutorial:Map_Making_for_WH3),
[Terry intro](https://wiki.totalwar.com/w/TWW_Assembly_Kit_Terry_Intro), [Rules.bob](https://wiki.totalwar.com/w/Rules.bob_Documentation.html).

---

## 1. Cadre et licence

**Ce que produit la chaîne.** Une carte de campagne Total War est faite de deux moitiés :

- la **moitié logique** : sur une grille hexagonale, le type de sol, les régions, les climats, les
  rivières, les routes, les plages, les ponts, les emplacements de villes, les zones
  infranchissables ; convertie en fichiers binaires que le moteur lit. C'est le travail de **CAIME**.
- la **moitié visuelle** : relief, textures, végétation, eau, éclairage. C'est le travail de
  **Terry** (éditeur de terrain) et de **BOB** (le bâtisseur qui transforme les données brutes en
  fichiers du jeu).

Autour : **Dave** ou **RPFM** pour les tables de la base de données, **RPFM** pour les packs, le
startpos et la fin du pathfinding, un peu de **Lua** si la campagne le demande.

**Jeux couverts par CAIME** : tous les Total War depuis Rome II inclus (Rome 2, Attila, Thrones
of Britannia, Warhammer 1/2/3, Three Kingdoms, Troy, Pharaoh, Pharaoh Dynasties). Shogun 2 : non.
CAIME est **le seul moyen** de produire `map_data.esf`, `pathfinding.ppd`, `borders.pbd`,
`dynamic_resources.esf`, `trade_routes.ptd` ; il aide à produire `tile_map.png` et les images
`lookup_*` / `lookup_minimap_*`.

**Licences.** Code de CAIME : « Non-Commercial Open Source License » (modification autorisée,
aucun usage commercial, partage à l'identique si redistribué, copyright conservé). EULA de
CAIME : interdit « tout pipeline automatisé ou service produisant du contenu pour des tiers contre
rémunération ». README de CAIME : « les fichiers générés par CAIME ne peuvent être donnés sans
l'accord exprès d'un fondateur du projet » et usage commercial interdit « y compris les dons ».
RPFM : MIT. Outils CA : EULA du jeu. **Cet atelier est personnel et non commercial.**

**Univers.** L'équipe CAIME demande, au titre de son EULA, de **ne pas faire de carte d'un
autre univers (Terre du Milieu, etc.) pour un jeu Warhammer** ; pour ce genre de projet, prendre
Troy ou Pharaoh comme base : même moteur, et leurs packs contiennent la plupart des squelettes et
animations des créatures WH. Réutiliser des modèles d'un autre jeu CA dans un jeu Warhammer n'est
pas permis (restrictions Games Workshop) : il faut ses propres assets. Source : Discord CAIME,
20.09.2026 (`05-journal\discord-caime-20-09-2026.md`).

---

## 2. L'atelier sur cette machine

```
C:\TotalWar-CampaignMap\       (état au 23.09.2026 ; organisation : README.md § 2)
├── CLAUDE.md, README.md, GUIDE.md, ERREURS-ET-LECONS.md, AGENTS.md
├── 01-outils\
│   ├── CampaignMapToolkit\               ← fork git de CAIME
│   │   ├── CAIME\bin\Debug\CAIME.exe     ← L'EXÉCUTABLE CAIME À UTILISER (verbes ajoutés, correctif culture)
│   │   ├── CAIME\Tools\Debug\MapDataBuilder.x64.exe   ← convertisseur C++ (aussi en Release\)
│   │   ├── Templates\                    ← 15 gabarits (voir § 13)
│   │   └── docs\                         ← les 14 guides officiels
│   ├── RPFM\rpfm-v5.0.6-x86_64-pc-windows-msvc\   ← rpfm_ui.exe, rpfm_server.exe (MCP)
│   └── caime-installeur-officiel\        ← CampaignMapToolkit-win-Setup.exe v1.0.0
├── 02-scripts\                           ← un script = un travail, mode d'emploi en tête (≈ 85 scripts ; entrées
│                                           principales : CLAUDE.md § 5 ; lancer-outils.ps1 -Outil terry|bob|dave|rpfm|rpfm-server|caime)
├── 03-references\saison-des-revelations\ ← couches, textes et fichiers de WH1 ; instantane-wh3-8.1\ (photo du jeu)
├── 04-projets\saison-des-revelations\    ← le projet (notes.md = la fiche)
├── 05-journal\                           ← journaux datés, sauvegardes (db-backups, startpos-backups, terrain-backups)
└── 99-archives\                          ← ce qui ne sert plus, rangé (INDEX.md)
```

**Installé et vérifié le 20.09.2026 :**

| Élément | Où | Remarque |
|---|---|---|
| Jeux Steam | `C:\Program Files (x86)\Steam\steamapps\common\` | Attila, Rome II, WARHAMMER III, PHARAOH DYNASTIES. Shogun 2 : hors périmètre |
| Assembly Kit WH3 (Steam) | `...\Total War WARHAMMER III\assembly_kit\` | app 1880380. `binaries\bob.modder.x64.exe`, `binaries\tweak.modder.x64.exe` (Tweak **et Terry**), `dave\DaVE.retail.x64.exe`, `raw_data\`, `working_data\` |
| Assembly Kit WH3 (Store) | `C:\Program Files\WindowsApps\18793CreativeAssemblyLtd.TotalWarWARHAMMERIII-Asse_1.3.4908.0_x64__ry6v8xxqmygx8\assembly_kit\` | paquet gratuit `9PBN49FBQX7S`, mêmes exécutables, **ses propres** `raw_data`/`working_data` (conteneur MSIX, non relocalisable). Lancement : `explorer.exe shell:AppsFolder\18793CreativeAssemblyLtd.TotalWarWARHAMMERIII-Asse_ry6v8xxqmygx8!Terry` (ou `!BOB`, `!DaVE`) |
| RPFM 5.0.6 | `01-outils\RPFM\rpfm-v5.0.6-...\` | `rpfm_ui.exe` (interface), `rpfm_server.exe` (WebSocket + MCP). **Plus de `rpfm_cli.exe` depuis la 5.0.0** |
| RPFM 4.2.7 | **absent de l'atelier** (23.09.2026) | seul binaire (`rpfm_cli.exe`) que CAIME accepte comme « source RPFM » ; à réinstaller si ce besoin revient |
| CAIME officiel | `%LOCALAPPDATA%\CampaignMapToolkit\` | v1.0.0, sans Templates ni MapDataBuilder, et **sans le correctif culture** (§ 15) |
| Préférences CAIME | `%APPDATA%\CampaignMapToolkit\Caime\preferences.json` | chemins d'Assembly Kit par jeu, posés par `config` |
| Build Tools 2022 | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\` | ateliers .NET desktop + C++ ; MSBuild dans `MSBuild\Current\Bin\` |
| Python 3.12 | `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` | Pillow, numpy |

Pour un autre jeu : installer son Assembly Kit depuis Steam (Bibliothèque → Outils), puis
`CAIME.exe config --game <Jeu> --asskit <dossier assembly_kit>`.

---

## 3. Vocabulaire

- **Assembly Kit (AKit)** : outillage officiel de Creative Assembly, un par jeu. `raw_data\` = ce
  que les outils lisent et éditent (tables `db\*.xml`, `terrain\`, `art\`,
  `EmpireDesignData\campaign_maps\<carte>\` avec le `map.hex` vanilla et ses lookups) ;
  `working_data\` = ce que les outils produisent, à empaqueter ensuite.
- **Dave** : éditeur de tables de la base. **Tweak** : application « Assembly Kit » ; **Terry**
  est son mode « TerrainMetadataEditor ». **BOB** : bâtisseur (textures, modèles, terrain,
  arbres, packs, startpos) piloté par des fichiers `rules.bob`.
- **RPFM** : Rusted PackFile Manager, outil communautaire pour les `.pack` (archives du jeu :
  tables, textes, textures, modèles, scripts). Depuis la 5.0 : une interface (`rpfm_ui`) et un
  serveur sans fenêtre (`rpfm_server`) qui expose un **MCP** pour les IA.
- **Hex** : case du damier. **Couche** : un type de donnée par hex. **Swatch** : valeur peignable.
  **`map.hex`** : projet CAIME. **`.hex_layer`** : une couche exportée/importable. **Gabarit** :
  dossier `Templates\<nom>\` avec un `map.hex` et ses fichiers d'appui.
- **startpos** : `startpos.esf` (dans `campaigns\<campagne>\`), l'état de départ d'une campagne ; généré par BOB/Tweak ou par
  RPFM (`build_starpos`), hors CAIME.
- **pack** : le mod livré, posé dans `<jeu>\data\`.

---

## 4. Les outils, un par un

### 4.1 CAIME

Un « Photoshop de données » : on choisit une couche, un swatch, un outil, on peint ; puis le menu
**Process** « développe » les couches en fichiers du jeu. Lit la base de l'Assembly Kit à
l'ouverture du projet (ou via RPFM), **n'y écrit jamais**. Détails : § 8 (ligne de commande),
§ 9 (format des couches), § 10 (règles), § 13 (gabarits).

Règle d'or (doc « Modifying an Existing Map ») : repeindre avec des swatches existants ne touche
pas la base ; **créer, renommer ou supprimer** un type de sol, un climat, une attrition, une région
ou une zone d'intérêt depuis le panneau Actions exige la modification correspondante dans la base,
puis **File → Reload** (Ctrl+R).

### 4.2 RPFM

**Interface** (`rpfm_ui.exe`, version 5.0.6 de l'atelier ; libellés relevés dans son `locale\English_en.ftl` le
24.09.2026 par la session de l'extension) : **PackFile → Settings** : dossier du jeu (celui de l'exe), dossier de
l'Assembly Kit, dossier **MyMod** (hors Program Files), jeu par défaut ; vérifier le menu déroulant **Game Selected** ;
puis **Game Selected → Generate Dependencies Cache** (une minute ; à refaire après une mise à jour du jeu) ;
**About → Check Updates**, puis le bouton de la ligne **Schema Updates**. La 5.0.6 a six menus (PackFile, MyMod,
View, Game Selected, Tools, About) et **plus de menu Special Stuff** ; les anciens libellés (« PackFile →
Preferences », « Special Stuff → Warhammer 3 ») sont ceux du tutoriel de la v2.3.2. Le manuel en ligne décrit bien la
5.0.6, parfois avec d'autres libellés (relecture du code de RPFM à l'étiquette v5.0.6 par la session de l'extension,
24.09.2026, 03 h 45). En cas d'écart, la palette de commandes (**Ctrl+Maj+P**) retrouve l'action. Créer un
mod : **MyMod → New MyMod** (nom `auteur_description`, underscores) ; le pack est créé en
`<MyMod>\warhammer_3\<nom>.pack`, **à côté** du dossier `<nom>\`, pas dedans. Chercher une donnée : **View →
Toggle Global Search Window**, onglet **db**, double-clic pour ouvrir la table, clic droit →
**Go To Definition** pour suivre une clé. Ajouter une table : clic droit sur le dossier du mod →
**Create… → Create DB**, choisir le nom de table (ex. `land_units`), nommer le fichier `auteur_nom` sans
espace ; copier une ligne vanilla : filtrer par clé, sélectionner la ligne, **Copy**, puis dans le
mod **Paste as New Row**. Sauver : Ctrl+S. **Install / Uninstall** (dans `data\`), **Save Pack For Release…**
(optimiseur) et **Build Startpos** sont au **clic droit sur la racine du pack**, pas dans un menu. Diagnostics,
traducteur et éditeur ESF (donc `startpos.esf`) sont aussi dans l'interface. **Retirer une ligne du jeu** : table
`twad_key_deletes` (depuis le patch 6.3) ; la colonne `mod_disabled` n'existe que dans deux tables.
**MCP et startpos** : après `build_starpos`, attendre la fermeture du jeu puis appeler `build_starpos_post`, sinon
`user.script.txt` garde `quit_after_campaign_processing;`.

**Serveur** (`rpfm_server.exe`, vérifié le 20.09.2026) : se lance sans argument (pas d'option
`--help`, il démarre aussitôt), écoute sur `127.0.0.1:45127`, journalise sur stderr, s'arrête quand
plus aucune session n'est ouverte. Trois points d'entrée :

| Point d'entrée | Usage |
|---|---|
| `POST http://127.0.0.1:45127/mcp` | **MCP** en Streamable HTTP, JSON-RPC 2.0, protocole `2025-06-18`. Une session RPFM par connexion (en-tête `Mcp-Session-Id` renvoyé à l'`initialize`). |
| `GET http://127.0.0.1:45127/ws` | WebSocket, même surface de commandes que l'interface (`?session_id=` pour rattacher une session). Référence : chapitres `ws-protocol`, `ws-commands`, `ws-responses`, `client-example` du manuel. |
| `GET http://127.0.0.1:45127/sessions` | liste des sessions actives. |

**Brancher une IA sur le MCP.** Claude Desktop : dans `claude_desktop_config.json`,
`{"mcpServers": {"rpfm": {"url": "http://127.0.0.1:45127/mcp"}}}`. Claude Code :
`claude mcp add --transport http rpfm http://127.0.0.1:45127/mcp`. Tout client Streamable HTTP
fonctionne. Le serveur doit tourner avant (`lancer-outils.ps1 -Outil rpfm-server`).

**Inventaire du 20.09.2026** (fichiers dans `05-journal\rpfm-mcp-20-09-2026\`) : 150 outils,
11 invites (`create_new_mod`, `edit_db_table`, `file_operations`, `manage_dependencies`,
`open_and_inspect_pack`, `run_diagnostics`, `schema_operations`, `search_and_replace`,
`translation_workflow`, `troubleshooting`, `tsv_workflow`), 11 ressources (`games`, `Initialization
guide`, `Path conventions`, `SupportedFormats`, `GlobalSearch example`, `OptimizerOptions
example`…). Familles d'outils : cycle de vie des packs, fichiers, tables (décodage, définitions,
`fields_processed`), dépendances et schémas, recherche globale, diagnostics, optimiseur, notes,
réglages, **startpos** (`build_starpos`, `build_starpos_get_campaign_ids`,
`build_starpos_check_victory_conditions`, `build_starpos_post`, `build_starpos_cleanup`),
`assembly_kit_path`, animations, traductions.

**Séquence recommandée par le manuel** : `set_game_selected` (avec `rebuild_dependencies: true`)
→ `open_packfiles` → `open_pack_info` (arbre) → `decode_packed_file` (ex. `{"pack_key": "...",
"path": "db/units_tables/data", "source": "PackFile"}`) → `save_packed_file_from_view` →
`save_packfile`. Règles : les arguments complexes (`Definition`, `GlobalSearch`) se passent en
**chaîne JSON sérialisée** ; appeler `fields_processed` sur une définition avant de construire une
ligne ; `pack_key` vient de `open_packfiles` ou `list_open_packs`. Lire d'abord la ressource
`Initialization guide` et `instructions.md` du journal.

**RPFM dans CAIME.** CAIME peut lire ses tables depuis un `.pack` au lieu de `raw_data\db`
(Settings → Preferences → Database source = RPFM). Il exige alors le dossier contenant
**`rpfm_cli.exe`** (validé en lançant `rpfm_cli.exe help`), un **pack vanilla par jeu** (WH3 :
`db.pack`), et le chemin AKit reste obligatoire ; packs moddés optionnels **par projet** via
Settings → RPFM Workflow, mémorisés dans `caime_metadata.json` ; fusion par fragment de table, le
nom qui trie en premier gagne. Comme la 5.0 a supprimé `rpfm_cli.exe`, il faut la 4.2.7, **absente de l'atelier
depuis le 23.09.2026** (tableau du § 2) : la réinstaller dans un dossier daté si ce besoin revient. Le changement de
source prend effet à la prochaine ouverture.

### 4.3 Assembly Kit : Dave, Tweak, BOB, Terry

- **Dave** (`dave\DaVE.retail.x64.exe`) : édite les tables `raw_data\db\*.xml`. C'est ce que lit
  CAIME. Alternative sans fenêtre : éditer ces XML par script, ou passer par RPFM et un pack.
- **Tweak** (`binaries\tweak.modder.x64.exe`) : doit être **fermé** pendant les exports Map Data
  et Dynamic Resources de CAIME. Génère le startpos (doc CAIME : « BOB / Tweak.AssemblyKit »).
- **Terry** : `tweak.modder.x64.exe /standalone TerrainMetadataEditor` depuis `binaries\`
  (vérifié : fenêtre « TWeak - Terry », 490 Mo, en 25 s). Éditeur de terrain 3D : tuiles,
  relief, peinture de textures, végétation, objets, zones logiques, éclairage, sons. La doc CA
  dit : « dans la version actuelle de l'Assembly Kit, seule la création de tuiles de bataille
  est prise en charge » ; la fiche Store dit « Battle Map Editor ». Voir § 12.
- **BOB** (`binaries\bob.modder.x64.exe`) : bâtisseur. Se pilote par l'interface (arbre de
  `raw_data`, cases à cocher, Start, journal) ou depuis Terry (**File → Process with BOB**), et
  par les fichiers **`rules.bob`** posés dans les dossiers de `raw_data` et `working_data`.
  **Pas d'aide en ligne de commande** : `-h`, `--help`, `-help` ouvrent une boîte « Illegal option
  format » ; `/?` démarre normalement ; l'option connue est `-no_console` (celle du Store). Format
  d'un `rules.bob` (doc CA + fichiers présents dans l'AKit) :

  ```
  [Pack]
      <Files>  = -*.pack                          ; filtres : inclusions, exclusions avec « - », jokers
      PackFile = <retail>/data/mod.pack           ; pack de destination
      PackType = mod
      BasePath = ...                              ; dans un sous-dossier : rediriger vers un autre pack
  [Terrain]
      PrefabRoot          = art/prefabs/battle
      save_meta_data_map  = false
      save_final_tile_map = true
  ```
  Les modules chargés par BOB dans l'AKit WH3 : `bob_terrain`, `bob_tile`, `bob_vegetation`,
  `bob_campaign`, `bob_texture`, `bob_pack`, `bob_dbexport`, `bob_lua`, `bob_localisation`…
  Donc BOB sait traiter le **terrain de campagne** (module `bob_campaign`) ; le point d'entrée
  côté données brutes reste à établir (§ 12).

**Piloter ces outils depuis une IA.** Dave, Tweak, Terry et BOB sont des applications à fenêtre :
une IA les conduit par capture d'écran et clics (outils « computer-use » de Claude), ou évite la
fenêtre : XML de `raw_data\db` par script à la place de Dave, `rules.bob` + un seul clic Start à la
place de la navigation dans BOB, MCP RPFM à la place de l'interface RPFM. CAIME se pilote
entièrement en ligne de commande (§ 8).

---

## 5. La chaîne complète pour une carte neuve

1. **Concept.** Références dans `03-references\<projet>\` : croquis, liste des régions et
   provinces, villes, ports, chokepoints. Taille : largeur **paire**, ≤ 731 520 hex recommandé
   (défaut 1016 × 720 ; WH3 vanilla 1440 × 970). Nom de carte : lettres, chiffres, underscore ;
   CAIME **nettoie** silencieusement les autres caractères ; la correspondance avec la base est
   **sensible à la casse** ; il devient le nom du dossier projet et du dossier de sortie.
2. **Base de données** (Dave, XML par script, ou RPFM), avec ce nom exact :
   - `campaign_maps` : la carte ;
   - `regions` : une ligne par région neuve, `is_sea`, **couleur RGB unique** (sert aux lookups) ;
   - `campaign_map_regions` : lie chaque région à la carte (Pharaoh : champ `index`, terre puis
     mer, sans trou) ;
   - `region_to_province_junctions` : **une ligne par région** vers sa province ; province neuve
     → table `provinces` ;
   - `campaigns` : la campagne dont `map_name` est la carte (**sinon l'export Lookup refuse** :
     « no campaign uses the map ») ;
   - `campaign_map_roads` : coûts de route par campagne et type ;
   - `campaign_map_playable_areas` : limites caméra et zone jouable (à mettre à jour si la
     taille change, avant Map Data) ;
   - `campaign_map_areas_of_interest` (3K, WH3) : filtrée par nom de carte, sinon couche vide.
   Tables globales déjà remplies : `campaign_ground_types`, `climates`, `campaign_map_attritions`.
   L'ordre des régions compte (terrestres puis maritimes, ordre de `regions.xml`) ; après tout
   changement, rouvrir le projet.
   **Par script** : `02-scripts\declare_map.py --spec <projet>\map_spec.json --asskit <AKit> [--apply|--undo]`
   écrit ces neuf tables comme Dave (uuid, timestamp, clé), avec sauvegarde des XML dans
   `05-journal\db-backups\`, idempotent. Modèle de fiche : `04-projets\saison-des-revelations\map_spec.json` (le projet `ile_claude` n'est plus dans l'atelier).
3. **CAIME — créer le projet** : `create --name <carte> --game <Jeu> --width W --height H --out <AKit>\raw_data\EmpireDesignData\campaign_maps`
   (ou `--template <gabarit>`). Le nom du dossier = le nom de carte, à cet emplacement précis :
   c'est ce que Map Data exige. Puis **`sync-names -m <map.hex>`** : un `map.hex` neuf ne connaît
   aucun nom ; ce verbe y enregistre les régions, sols, climats, attritions et zones que la base
   déclare pour cette carte (mêmes actions que l'éditeur), et `info --names` donne alors les index
   que les couches doivent utiliser. Poser aussi les quatre fichiers d'appui (§ 13) : images vides
   aux proportions du prologue (arbres 7,04 × 7,37 px par hex, ressources 2,54 × 2,40) et les deux
   XML copiés de `wh3_main_prologue_map`.
4. **CAIME — remplir les couches** : à la souris, ou par script (§ 9) puis `import-layer`.
   Chaque hex a besoin d'une **région, d'un type de sol et d'un climat** ; `is_sea` de la région =
   catégorie du type de sol (terre/mer), sinon avertissement. Contrôle : `export-layer --format png`.
5. **CAIME — valider** : `validate --all` (§ 10). Sauver.
6. **CAIME — exporter** (`process`) : `--pathfinding`, `--borders` (sans effet pour Troy et
   Pharaoh), `--lookup`, `--trade-routes` (Rome 2, Attila, Thrones, 3K), `--dynamic-resources`,
   `--map-data`. Les deux derniers exigent : projet enregistré sous
   `<AKit>\raw_data\EmpireDesignData\campaign_maps\<carte>\map.hex`, aucune modification en
   attente, **Tweak fermé**, et les **fichiers d'appui dans le dossier projet** : `trees.png`,
   `tree_database.xml`, `dynamic_resources.png`, `dynamic_resources_database.xml` (§ 13 ; leur
   absence est la cause n° 1 d'échec). Sorties dans `<AKit>\working_data\campaign_maps\<carte>\`.
7. **Startpos** : BOB/Tweak (doc CAIME) ou RPFM (`Build Startpos`, outils MCP `build_starpos*`).
   RPFM finit aussi le pathfinding restant (info Charles, à confirmer sur pièce).
8. **Moitié visuelle** : Terry/BOB (§ 12), avec `tile_map.png` et `trees.png` comme calques.
9. **Lua** si besoin, **pack** avec RPFM, test en jeu.

### 5.1 Qui lit quoi, qui produit quoi

| Export CAIME | Lit | Produit |
|---|---|---|
| Map Data | toutes les couches, base AKit, `binaries\` de l'AKit (MapDataBuilder), fichiers d'appui du projet, `caime_metadata.json` → `map_data_config.xml` si auto-patch | `map_data.esf` |
| Pathfinding | Ground Types, Regions, Rivers, Roads, Bridges, Beaches, Impassable, Town Slots, Trade Routes | `pathfinding.ppd` (la doc dit parfois `.bin`) |
| Borders | Regions ; en interface, une matrice « Select borders to export » (Land–Land, Land–Sea, Sea–Sea…, TI = theatre island, MI = Mediterranean island) | `display\borders\borders.pbd` |
| Dynamic Resources | `dynamic_resources.png` + `dynamic_resources_database.xml` du projet, base AKit | `dynamic_resources.esf` (pas pour 3K) |
| Trade Routes | Trade Routes, Regions, terre/mer | `trade_routes.ptd` |
| Lookup & Minimap | toutes, surtout Regions ; `campaigns` doit citer la carte | `lookup_*`, `minimap_*` (TGA : Rome 2, Attila, Thrones, Pharaoh ; BMP : Warhammer, 3K). **Warhammer III** (code de v1.0.1) : un seul `<campagne>_lookup.bmp`, sans minicarte |
| SVG Borders | Regions | `.svg` |
| Baseline Tilemap | Roads, Rivers, Cliffs, Beaches | `tile_map.png` |

---

## 6. Modifier une carte existante

Ordre : valider (Regions, Ground Types, Town Slots + concernés) → Ctrl+S → ré-exporter → régénérer
le startpos. `--all` en ligne de commande exécute Map Data → Dynamic Resources → Pathfinding →
Borders → Trade Routes → Lookup, dans cet ordre quoi qu'on tape.

| Modification | Base ? | Tables | Exports à relancer |
|---|---|---|---|
| Repeindre types de sol existants | non | — | Pathfinding, Map Data |
| Repeindre climats existants | non | — | Map Data |
| Repeindre attritions existantes | non | — | Map Data (et Pathfinding selon la section) |
| Créer / renommer / supprimer un type de sol | oui | `campaign_ground_types` (`type`, `is_sea`, `movement_cost`) | Pathfinding, Map Data |
| Créer / renommer / supprimer un climat | oui | `climates` (`climate_type`) | Map Data |
| Créer / renommer / supprimer une attrition | oui | `campaign_map_attritions` (`key`, `type` ∈ {`terrain_land`, `terrain_sea`}) | Map Data |
| Impassable, Restrictions | non | — | Pathfinding, Map Data |
| Redessiner des frontières | non | — | Borders (sauf Troy/Pharaoh), Pathfinding, Map Data, Lookup |
| **Ajouter une région** (base d'abord, puis Reload, puis peindre + sprawl + slot) | oui | `regions`, `campaign_map_regions`, `region_to_province_junctions`, `provinces` si neuve | tous |
| **Supprimer une région** (CAIME d'abord : repeindre, effacer sprawl/slots, valider, sauver ; puis base ; Pharaoh : renuméroter `index`) | oui | `campaign_map_regions`, `region_to_province_junctions`, `regions` si non partagée | tous |
| Renommer une région | oui | `regions.key`, `campaign_map_regions.region`, `region_to_province_junctions.region`, toute table du mod citant la clé | tous |
| Slots et sprawl | non | — | Pathfinding, Map Data |
| Rivières, plages, ponts | non | — | Pathfinding, Map Data |
| Routes | non (nouveau coût : `campaign_map_roads`) | — | Pathfinding, Map Data |
| Trade Routes | non | — | Trade Routes |
| Zone d'intérêt (3K, WH3) | oui | `campaign_map_areas_of_interest` (`campaign_map`, `key`) | Map Data |
| **Resize** (Ctrl+Shift+R) | `campaign_map_playable_areas` si la zone jouable change | — | tous ; **les hex neufs sont vides** : leur peindre région et type de sol. Resize agrandit ou rogne le canevas avec un padding, il ne met **pas** le dessin à l'échelle |
| Ressources | — | — | Dynamic Resources seulement si `dynamic_resources.png` a changé |

---

## 7. Différences par jeu

| | Rome II | Attila / Thrones | WH1 / WH2 / Troy | Three Kingdoms | WH3 | Pharaoh / Dynasties |
|---|---|---|---|---|---|---|
| Format `map.hex` (mineur) | 0x0D | 0x0F | 0x12 | 0x13 | 0x14 | 0x12 (WH1) / 0x14 + combiné (Pharaoh) |
| Trade Routes | oui | oui | non | oui | non | non |
| Restrictions | non | oui | oui | oui | oui | oui |
| Region Borders (+ Auto-generate) | non | oui | oui | oui | oui | oui |
| Areas of Interest | non | non | non | oui | oui | non |
| `borders.pbd` | actif | actif | actif (WH), **sans effet** (Troy) | actif | actif | **sans effet** |
| Taille des slots (validateur) | ≥ 7 hex + hex central à 6 voisins | idem | WH : slot 0 = 19 (intérieur) / 16 (port) ; Troy : libre | libre | 19/16 « non strict » (la doc se contredit ; croire le validateur) | libre |
| Index de régions combiné | non | non | non | non | non | **oui** |
| Images lookup | TGA | TGA | BMP | BMP | BMP | TGA |
| Map Data Editor (Ctrl+M) | oui | oui | refusé | refusé | refusé | refusé |
| `dynamic_resources.*` | requis | requis | requis | non utilisé | requis | requis |
| Shader Resolution Corrector | — | — | — | seul | — | — |

WH3 en particulier : les gabarits CAIME `wh3_main_combi_map_1` et `wh3_main_chaos_map_2` sont
**des versions anciennes** ; les cartes vanilla actuelles de l'AKit sont `wh3_main_combi_map_5` et
`wh3_main_chaos_map_4` (625 régions liées pour `_map_1` contre 641 pour `_map_5`), et seul
`wh3_main_prologue_map` est livré avec ses quatre fichiers d'appui.

---

## 8. Ligne de commande de CAIME (fork)

Lancé **sans** argument, `CAIME.exe` ouvre l'éditeur ; **avec** arguments, il travaille en console
sans fenêtre. Codes de sortie : `0` succès, `1` arguments invalides, `2` échec. Build Debug : chaque
ligne de journal est imprimée deux fois, c'est normal.

```
CAIME.exe process  --map <map.hex> (--all | --map-data --dynamic-resources --pathfinding --borders --trade-routes --lookup)
CAIME.exe validate --map <map.hex> (--all | --rivers --town-slots --roads --bridges --beaches --regions --attritions --climates --ground-types --impassable --town-sprawl)
CAIME.exe config (--game <Jeu> --asskit <dossier>) [--show]
CAIME.exe create --name <carte> (--game <Jeu> [--width W] [--height H] | --template <nom|dossier>) [--out <dossier>] [--overwrite]
CAIME.exe import-layer --map <map.hex> (--layer <Couche> --file <x.hex_layer>)... [--no-save]
CAIME.exe export-layer --map <map.hex> --out <dossier> (--all | --layer <Couche> ...) [--format png|binary]
CAIME.exe info --map <map.hex> [--names]
CAIME.exe sync-names --map <map.hex> [--no-save]
CAIME.exe --help
```

- `--game` (casse et séparateurs ignorés) : Rome2, Attila, Thrones_Of_Britannia, Warhammer,
  Warhammer2, Warhammer3, Three_Kingdoms, Troy, Pharaoh, Pharaoh_Dynasties.
- `--layer` : GroundTypes, Rivers, Climates, Attritions, Regions, RegionBorders, Beaches,
  Bridges, TownSprawl, TownSlots, Roads, TradeRoutes, Impassable (Restrictions et AreasOfInterest
  n'ont pas de format d'import/export).
- `config` écrit `preferences.json` ; un chemin d'AKit changé prend effet à la prochaine
  ouverture. `validate` ne demande pas d'AKit mais les validateurs Regions, Ground Types, Climates,
  Attritions comparent à la base : sans AKit, ils tournent en aveugle.
- `create --template` copie **tous les fichiers de premier niveau** du gabarit (comme l'éditeur),
  garde le nom de carte du gabarit, et exige donc que la base connaisse ce nom.
- `import-layer` refuse tout fichier dont la taille ne correspond pas à la carte, puis sauvegarde
  le `map.hex` (moitié « fichier » du Ctrl+S ; la base n'est pas touchée).
- `--all` de `process` est exclusif des drapeaux individuels ; zéro tâche = rejet.

Séquence vérifiée le 20.09.2026 :

```powershell
$exe = "C:\TotalWar-CampaignMap\01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe"
& $exe config --game Warhammer3 --asskit "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit"
& $exe create --name proof_wh3 --template wh3_main_combi_map_1 --out C:\TotalWar-CampaignMap\04-projets --overwrite
& $exe info -m C:\TotalWar-CampaignMap\04-projets\proof_wh3\map.hex --names
& $exe validate -m C:\TotalWar-CampaignMap\04-projets\proof_wh3\map.hex --all
& $exe process  -m C:\TotalWar-CampaignMap\04-projets\proof_wh3\map.hex --pathfinding
```

Recompiler (racine du dépôt) :

```powershell
$msb = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
$sln = "C:\TotalWar-CampaignMap\01-outils\CampaignMapToolkit\"
& $msb "CAIME\CAIME.csproj" -t:Restore -p:RestorePackagesConfig=true "-p:SolutionDir=$sln"
& $msb "CAIME\CAIME.csproj" -p:Configuration=Debug -p:Platform=AnyCPU "-p:SolutionDir=$sln"
& $msb "MapDataBuilder\MapDataBuilder.vcxproj" -p:Configuration=Debug -p:Platform=x64 "-p:SolutionDir=$sln"
```

Le fork (branche `cli-create-import`) contient : les cinq verbes (`CAIME\Cli\CliRunner.Authoring.cs`),
une surcharge sans boîte de dialogue de `ProjectManager.CreateProject`, et **la culture invariante
posée dans `App.Main`** (sans elle, sur un Windows en français, la base refuse de charger et tout
projet s'ouvre en lecture seule, éditeur officiel compris). Candidats à une pull request amont
(README : brancher depuis `main`, relecteurs @victimized0, @robert-d-schultz, @MrJox).

---

## 9. Produire des couches par script

### 9.1 Le format `.hex_layer`

```
4 octets   int32 little-endian : identifiant de couche
N octets   1 octet par hex, ligne par ligne (index = ligne × largeur + colonne) ; Regions : 2 octets par hex
```

| Id | Couche | Valeur sur disque |
|---|---|---|
| 0 | Impassable | **1 = franchissable**, 0 = infranchissable |
| 1 | TradeRoutes | ≠ 0 = présent (masques **gardés tels quels** par CAIME v1.0.1, d'après son code ; relecture de la session de l'extension, 24.09.2026) |
| 2 | Roads | ≠ 0 = présent (masques recalculés) |
| 3 | TownSlots | index + 1 ; 0 = aucun. Index 0 = slot principal (« Main Settlement ») ; le port et les slots secondaires suivent l'ordre des swatches (« Port, Slot 2, Slot 3… ») ; à confirmer sur une carte vanilla avec `export-layer --format binary` |
| 4 | TownSprawl | 1 = oui |
| 5 | Bridges | 1 = oui |
| 6 | Rivers | ≠ 0 = présent (masques recalculés) |
| 7 | Beaches | 1 = oui |
| 8 | RegionBorders | 1 = oui ; **recalculé par CAIME depuis Regions** (v1.0.1) : ce qu'on y écrit est remplacé |
| 9 | Regions | id + 1 sur 2 octets : `bas = (v & 0x1F) << 3`, `haut = v >> 5` |
| 10 | Attritions | index + 1 |
| 11 | Climates | index + 1 |
| 12 | GroundTypes | index + 1 |

- GroundTypes et Regions vivent dans un espace plat **[terre…, mer…]** : un type maritime
  d'index j vaut `nb_types_terre + j` ; idem pour les régions. `info --names` donne ces listes.
- **La ligne 0 du damier est en BAS de la carte.** L'export PNG de CAIME retourne l'image pour
  ressembler au jeu ; toute image dessinée haut en haut doit être retournée avant encodage
  (`caime_layers.py` le fait).
- Le drapeau terre/mer de l'hex, l'`is_sea` de la région et celui du type de sol doivent
  concorder ; le validateur signale chaque désaccord. L'action « Align Ground/Region Type » de
  l'éditeur déduit les types de sol des régions.
- **bridge-cliff** est un **type de sol**, pas une couche : c'est l'hex de rive qui autorise un pont.

### 9.2 `02-scripts\caime_layers.py`

```
python caime_layers.py names      --caime CAIME.exe --map map.hex
python caime_layers.py from-image --image design.png --legend legend.json --width W --height H --out DIR
python caime_layers.py demo       --caime CAIME.exe --map map.hex --out DIR [--seed N] [--regions K]
```

`from-image` : une image peinte (une couleur = une valeur) + `legend.json`
(`{"GroundTypes": {"_default": 2, "#143278": 15}, "Impassable": {"_default": 1, "#3c3737": 0}, ...}`)
→ un `.hex_layer` par couche. `demo` : île procédurale (mer, plages, plaines, forêts, collines,
montagnes infranchissables, désert, une rivière, K régions terrestres + 1 maritime) calée sur les
noms de la carte cible, avec `design.png` + `legend.json`. Le script ne produit **ni slots, ni
sprawl, ni ponts, ni climats** : à ajouter avant de viser un export Map Data (§ 10).

Workflow à partir d'une référence : image → carte de couleurs à aplats nets → `legend.json` →
`from-image` → `import-layer` → `export-layer --format png` → `validate --all` → corriger l'image →
recommencer. `design.png` et `legend.json` sont la source de vérité ; `map.hex` en est le produit.

---

## 10. Règles pour une carte fonctionnelle

Ce que remontent les onze validateurs de CAIME. **Error** = désaccord entre la base et la carte
(comptes ou noms de régions, types de sol, climats, attritions ; index invalide ; pont sur terre ;
slot hors plage) : le jeu ou le startpos cassera. **Warning** = règle de jeu violée, à lire.
**Info** = remarque. CAIME **n'empêche pas** d'exporter avec des erreurs ; en ligne de commande,
`validate` sort en 2 mais `process` tourne quand même. Repère : la carte vanilla de WH3 remonte
des centaines de Warning et son pathfinding s'exporte.

**Chaque hex** : une région, un type de sol, un climat. Région vide (zéro hex) = Warning
« startpos ». Hex de terre isolé entouré de mer = Warning.

**Routes, rivières, routes commerciales : aucun anneau fermé.** Pas seulement le triangle : tout
circuit sans extrémité (un périphérique de province, par exemple) fait **boucler l'export à
l'infini**. Un réseau est un arbre avec des impasses ; couper tout anneau en un point.

**Rivières** : sur terre seulement, connectées, jamais un bord vers la mer ou hors carte ; une
rivière isolée est probablement une erreur.

**Routes** : connectées ; pas sur la mer sauf pont ; pas sur falaise ou plage sauf approche de
pont ; route + infranchissable = Info ; carrefour en T = Info (moche en jeu).

**Ponts** : **sur des hex de mer** (sur terre = Error) ; relient deux rives distinctes ; au moins
un hex **bridge-cliff** sur l'approche de chaque rive ; une rivière (masque de bord sur terre) ne
se ponte pas, un bras de mer oui. Plage + falaise sur le même hex = Warning.

**Slots de ville** : chaque région franchissable a au moins un slot, sinon la marquer entièrement
infranchissable (friche). Tailles : § 7. Un slot = un seul groupe connexe ; un slot non-port n'est
pas en mer ; **le slot Port touche lui-même un hex de mer** ; index hors plage = Error.

**Sprawl** : **un seul blob par région**, sous le slot ; pas sur infranchissable, rivière ou
falaise ; ne déborde pas dans une autre région terrestre (déborder sur une région de mer pour un
port est admis) ; un terrain « hazard » (infranchissable, plage, rivière, falaise) doit **soit
toucher le blob, soit rester à 3 hex ou plus** (à 2 hex = Warning) ; un blob touchant **plus d'un**
patch de hazard = Warning (« pinch »). L'action « Align Town Sprawl/Slot » pose le sprawl sous
chaque slot et, pour Warhammer, Troy et 3K, retire le sprawl hors slot.

**Régions** : d'un seul tenant (morcelée = startpos en danger) ; une région de mer touche au plus
5 régions de terre, au-delà de 9 l'IA ralentit ; couleur RGB unique dans `regions.xml`.

**Infranchissable** : « Plug holes » bouche les trous ; laisser des cols si les armées doivent
passer.

**Géométrie** : largeur paire ; **2048 hex maximum par dimension** (au-delà, les fichiers
hlp/spd du pathfinding ne se traitent pas, et CAIME refuse) ; le plafond de 731 520 hex de la doc
n'est plus une limite dure mais tout ralentit au-delà ; le jeu est figé dans le `map.hex`.

**Tout changement impose de tout retraiter** : un seul hex modifié = relancer les exports (seuls
`borders.pbd` et les images lookup sont purement visuels et peuvent être refaits seuls). Un
rapport d'aspect inhabituel casse surtout l'interface du menu (sélection de seigneur), corrigeable
par un script d'UI. Une région sans colonie devient une **friche** (à peindre infranchissable) :
c'est la méthode pour resserrer une carte sur une zone. Source : Discord CAIME, 20.09.2026.

**Exports Map Data / Dynamic Resources** : projet sous `raw_data\EmpireDesignData\campaign_maps\<carte>\map.hex`,
rien en attente, Tweak fermé, fichiers d'appui présents (§ 13). Message de succès : « Finished
creating map » ; refus : « Map Data Process denied », « Please close Tweak.AssemblyKit ».

---

## 11. Concevoir une carte qui se joue bien

Jugement de conception, à valider projet par projet.

- Partir du gameplay : chokepoints (cols, gués, détroits), voisinages de factions, axes
  d'invasion. Couloirs et bastions, pas une plaine uniforme.
- Biomes par zones : massifs continus avec deux ou trois cols, forêts en bloc, un désert d'un
  tenant. Les types de sol pilotent les coûts de mouvement et l'aspect.
- Rivières crédibles : source en montagne, confluences, delta ; un bras de mer avec pont et
  bridge-cliff là où une route doit franchir.
- Routes en arbre : villes d'une province reliées, puis provinces entre elles ; jamais de boucle,
  peu de carrefours en T.
- Régions compactes et de taille comparable ; ports là où le commerce a un sens ; mers découpées
  pour rester sous 5 voisins terrestres.
- Marges de mer ou d'infranchissable sur les bords ; rien ne pointe hors carte.
- Prototyper petit (200 × 150), valider, exporter le pathfinding, **puis régénérer à la taille
  finale** : Resize ajoute du canevas vide, il n'agrandit pas le dessin.
- Préparer la moitié visuelle dès maintenant : `tile_map.png`, PNG des couches, images de
  référence à l'échelle exacte du damier (chargeables en fond dans l'éditeur, jamais exportées).

---

## 12. La moitié visuelle : Terry et BOB

**Ce qui est établi.** Terry et BOB pour Warhammer III sont sur cette machine (§ 2), Terry se
lance et ouvre son éditeur. BOB charge un module `bob_campaign`. La carte de campagne de WH3 **a
été agrandie par des moddeurs** : « Immortal Empires Expanded » (ChaosRobie, avec l'équipe CAIME)
ajoute 184 colonies et 74 provinces avec de nouvelles terres. La faisabilité ne fait donc pas de
doute.

**Ce qui n'est pas documenté publiquement** : la méthode exacte pour le terrain de campagne. La
doc CA parle de tuiles de bataille ; `raw_data\terrain\` de l'AKit ne contient que `battles\` et
`tiles\battle\` ; le `raw_data\EmpireDesignData\campaign_maps\<carte>\` vanilla ne contient que
`map.hex` et les lookups. Lu sur le Discord CAIME le 20.09.2026 : pour **Rome 2**, l'auteur de
CAIME dit qu'« aucun outil ne permet de modifier la carte visuelle de campagne pour le moment »,
et les archives de données brutes que CA a fournies pour Rome 2, Attila et Thrones ne contiennent
pas le visuel.

**Réponse de ChaosRobie sur WH3 (20.09.2026, 16 h 28), à la question posée depuis ce dossier.**
Mot pour mot : « I reverse engineered every part of the visual map, turning it into a
campaign-type Terry project », puis « Why yes that did take a while ». Trois enseignements :

1. **Terry sait ouvrir un projet de type campagne**, pas seulement des tuiles de bataille.
   La limite annoncée par CA n'est donc pas une limite de l'outil, c'est l'absence de données.
2. **Les données brutes du terrain de campagne ne sont pas livrées** avec l'Assembly Kit de WH3 :
   il a fallu les reconstituer par rétro-ingénierie, format par format.
3. **C'est long.** Une personne seule y a passé un temps considérable, sans méthode publiée.

Conséquence pour un projet : si la carte visée existe déjà dans un jeu dont l'Assembly Kit livre,
lui, des données de terrain de campagne (à vérifier pour Warhammer 1, dont la documentation CA de
l'époque présentait Terry comme éditant « height-map, lighting and props » de la carte de
campagne), on part d'un projet Terry de campagne existant au lieu de le reconstruire. C'est le
premier point à trancher dans l'inventaire du projet en cours.

### 12.1 Anatomie d'un projet Terry **de campagne** (établie le 20.09.2026)

ChaosRobie a partagé sur le Discord le projet Terry complet d'Immortal Empires Expanded, publié
de longue date sur Google Drive (archive de 366 Mo, 0,7 Go décompressée, 651 entrées). Il a été
ouvert et disséqué ; voici la structure, qui est le plan à suivre pour en fabriquer un.

**Emplacement** : `assembly_kit\raw_data\terrain\campaigns\<nom de la carte>\`. Ce dossier
`campaigns` **n'existe pas** dans le kit livré par CA, ni pour WH3 ni pour WH1 : c'est lui qu'il
faut créer.

**Contenu du dossier de la carte** (ici `wh3_main_combi_map_1`, 1440 × 970 hex) :

| Fichier | Rôle |
|---|---|
| `<carte>.terry` | le projet, en XML, `version="27"` |
| `<carte>.terry.user` | réglages de l'utilisateur, non essentiel |
| `rules.bob` | recette BOB locale, voir plus bas |
| `tile_map.png` | la tilemap |
| 10 fichiers `.tif` | les rasters du terrain, un par couche |
| 635 fichiers `.layer` | un par région, même compte que les entités du projet |

**Le fichier `.terry`** contient trois blocs :

- `QTU::ProjectTileMap` : `terrain_setup="terrain/campaigns/<carte>/"`, `world_width="961.3"`,
  `global_lighting="terrain/campaigns/<carte>/lighting/default.environment"`,
  `water_plane_material="materials/environment/campaign_sea/….xml.material"`.
- `QTU::Scene` : **une entité par région**, nommée exactement comme la clé de la base
  (`wh3_main_combi_region_aarnau`), chacune portant `<ECFileLayer export="true" bmd_export_type=""/>`.
  635 entités pour 635 régions : le projet Terry est donc lié à la liste des régions.
- `QTU::Terrain` : dix `QTU::TerrainMap`, chacune avec son type, sa taille et une
  `QTU::TerrainMapLayer` nommée `base`.

**Les dix rasters et leur résolution**, rapportées aux 1440 × 970 hex de la carte. Tout est un
multiple entier du nombre d'hex, ce qui permet de dimensionner n'importe quelle autre carte :

| Type | Taille | Pixels par hex |
|---|---|---|
| `Height`, `HeightSea`, `BlendCampaign`, `ColorOverlay`, `ColorOverlaySea` | 11520 × 7764 | **8** |
| `HeightShroud` | 5760 × 3882 | **4** |
| `CampaignTree`, `CorruptionMask`, `SnowMask` | 2880 × 1941 | **2** |
| `PatchVisibilityMask` | 125 × 84 | une case par **parcelle** de 23 px de carte de tuiles (§ 15, n° 70) |

Le raster de hauteur pèse à lui seul 165 Mo. La couche `ColorOverlay` a une opacité de 0,5, les
autres 1.

**Les deux `rules.bob`.** Celui du dossier `campaigns\` porte la recette du terrain de campagne :

```
[Terrain]
    PrefabRoot          = art\prefabs\campaign
    save_meta_data_map  = true
    save_final_tile_map = true
    generate_global_mesh = true
    TileDatabase        = terrain\tiles\campaign\_tile_database
    HeightPatch         = true
[Prop] / [Entity] / [Mesh]
    HeightPatch = true
[Texture]
    <Files> = ..._normal.*    CompressionFormat = dxt5n    NormalMap = true
```

Celui du dossier de la carte ne fait que recopier vers le kit :

```
[Copy]
    TargetPath = <retail>/assembly_kit/raw_data/terrain/campaigns/<carte>/
[+AssetGraph]
    Create = true    IncludeInRetail = true
```

Noter `PrefabRoot = art\prefabs\campaign`, à comparer au `art/prefabs/battle` des tuiles de
bataille : c'est ce qui distingue un projet de campagne d'un projet de bataille côté BOB.

**Deux dépendances référencées mais absentes** de l'archive et du kit CA, à trouver ailleurs,
sans doute à extraire des `.pack` du jeu : `terrain\tiles\campaign\_tile_database` (cité par
`rules.bob`, et déjà vu cité par BOB à son démarrage) et le dossier `lighting\` contenant
`default.environment` (cité par le `.terry`). **À confirmer.**

**Dimensionner un projet pour une autre carte.** Les résolutions étant proportionnelles au
nombre d'hex, pour la carte des Elfes sylvains de WH1 (400 × 440 hex) il faut :
**3200 × 3524** pour les cinq grands rasters (8 px par hex **plus 4 lignes**, comme 7764 =
970 × 8 + 4), 1600 × 1762 pour `HeightShroud`, 800 × 881 pour les trois masques et
`tile_map.png`, et **114 × 125** pour `PatchVisibilityMask` : une case par parcelle, la parcelle
faisant plafond(plus grand côté de la carte de tuiles / 128) px, ici 7 (§ 15, n° 70). *(Écrit
d'abord « 34 × 38, une case par 7,68 unités du monde » : règle fausse, tirée des seuls Empires,
erreur 70.)*

**Conventions établies le 21.09.2026** (preuves au journal `2026-09-21-phase-3-terrain\terrain.md`) :
rasters du nord vers le sud ; hauteurs en unités du monde, plan d'eau à 0 ; **la mer est déclarée
par `tile_map.png`** (type de tuile `sea`, couleur (83, 141, 213)), pas par la hauteur, et
`sea_height` porte le fond sous l'eau ; la légende des couleurs de `tile_map.png` est dans
`working_data\terrain\tiles\campaign\_tile_database\_settings.bin` (terre `generic`, mer, côtes,
routes, falaises, **rivières en maillage** `river_mesh*`) ; `blend.tif` porte directement le numéro
de texture de WH3 (0 à 143). Générateur pour notre carte : `02-scripts\terrain_wh1_vers_terry.py`.

### 12.2 Ce qui est documenté par ailleurs : une tuile de bataille avec Terry (tw-modding, WH3) :

1. Terry → **File → Save As…** : nom du jeu de tuiles, nom de carte, taille (8x8 pour rester
   compatible WH2), climat (jeu de textures) ; cocher la case du bas.
2. Relief, textures, objets : les modes de Terry (« intuitif », dit la doc ; pas de liste de
   raccourcis publiée). Végétation : outil de peinture de végétation ; zones d'exclusion
   procédurale : **Tools → Entity Creation → Visual**.
3. Logique : **Tools → Entity Creation (Logical)** : zones de déploiement (une par camp,
   « additive deployment zone region », Alliance ID 0 attaquant / 1 défenseur), zone jouable
   (« between 2x2 and 3x3 »), points de capture (« domination 1/2/3 », importance « score », 80x80
   à 180x180), lignes de renfort (AI hint « teleport reinforcement line » : une ligne courte de deux points suffit ; une
   vingtaine d'unités de long en cas de souci).
4. **Tools → Create battle for tile…** (une fois) crée `raw_data\terrain\battles\<carte>\` ; y
   poser `tile_map.png` et `climate_map.png`, éditer `explicit_tiles` (coordonnées de la tuile).
5. **File → Process with BOB** sur la tile map, puis sur la tuile ; « Legacy vegetation
   generation » désactivé ; recharger pour vérifier.
6. RPFM : ajouter dans le pack `working_data\terrain\...`, une ligne dans `battles_tables`
   (`key`, `type` domination/classic, `specification` = `terrain/battles/<carte>/`, capture
   d'écran `ui/frontend ui/battle_map_images/<img>.png`, environnement), un texte
   `battles_localised_name_<key>`. Pack dans `<jeu>\data\`.

**Piloter depuis une IA** : Terry n'a ni ligne de commande ni API connue ; une IA le conduit par
capture d'écran et clics (Claude : outils « computer-use », après `request_access` sur
« TWeak »). BOB se déclenche depuis Terry ou par son bouton Start, avec des `rules.bob` écrits par
script. Tout ce qui peut être préparé hors fenêtre doit l'être : `tile_map.png`, `climate_map.png`,
`explicit_tiles`, `trees.png`, tables RPFM par MCP.

### 12.3 Compiler le terrain d'une carte de campagne **neuve** (établi le 21.09.2026)

**La référence à jour est la chaîne automatisée** `02-scripts\chaine_terrain.ps1` (fin de cette section) ; les étapes
numérotées ci-dessous expliquent ce qu'elle fait. Depuis la chaîne 12, `lf_normal.dds` est recalculée depuis notre
relief par `lf_normal_depuis_relief.py --apply` (lissage de 12 px depuis le 25.09.2026 : stries des Montagnes Grises),
dernière étape de chaque chaîne (§ 15 n° 139) ; `lf_normal_wh1_vers_wh3.py` et `lf_normal_a_la_taille_du_relief.py`
(étapes 2 et 3 ci-dessous) ne servent plus.

« Process with BOB » dans Terry ne lance, pour une carte neuve, que **6 actions** (Terry file +
5 masques) : ni relief, ni textures, ni carte logique, ni brouillard. Cause lue dans
`bob_terrain.modder.x64.dll` et vérifiée sous `cdb` : pour une campagne, BOB cherche **le nom du
dossier de terrain** dans la table `campaign_map_playable_areas` de sa base, qui est celle du jeu
(`db.pack`) ; une carte absente de `db.pack` ne reçoit qu'une action d'erreur muette. Rien de ce
qu'on ajoute au kit ou dans un pack n'y entre (journal de phase 3, § 7).

Méthode qui marche : **`python 02-scripts\compiler_terrain_bob.py --carte <carte> --apply`**,
Terry fermé. Le script lance BOB avec la commande exacte de Terry, sous `cdb`, et fournit à la
recherche l'enregistrement de la carte (seuls `minx` et `maxx` sont lus, pris dans le kit). Il
vérifie l'empreinte de la DLL (table `VERSIONS_DLL` : après chaque mise à jour du kit, relever les décalages de la
nouvelle DLL et ajouter son empreinte avant la première chaîne ; § 15 n° 147) et garde les journaux dans `05-journal\2026-09-21-phase-3-terrain\
compilations\`. Pour ouvrir le projet en vue 3D, Terry exige qu'un terrain compilé existe déjà
dans `working_data\terrain\campaigns\<carte>\` (sinon il plante) : compiler d'abord, ou ouvrir
avec « 3D View » décoché.

**Recette complète du terrain compilé (21.09.2026, 17 h 50)**, dans l'ordre :
1. `compiler_terrain_bob.py --carte <carte> --apply` : relief (`full_height_map.dds` BC6H, rangé du
   sud au nord), carte logique, textures, brouillard, tuiles, masques, liste d'arbres. La compilation
   complète prend une minute (53 à 64 s le 22.09.2026 ; 25 min notées le 21.09.2026) ;
   `--sans full_height_map.dds,full_logic_map.compressed_map` saute le relief quand seul le reste a
   changé. L'étape « Generate Camera Height Map » est toujours sautée (elle plante).
   En amont, le relief vient de `relief_maillages_wh1.py --apply` (sol de WH1, § 15, n° 75).
2. `lf_normal_depuis_relief.py --apply` (depuis la chaîne 12) : l'éclairage lointain du relief, recalculé depuis notre
   relief lissé (§ 15 n° 139). Jusqu'au 24.09 : normal map de WH1 au vert inversé
   (`lf_normal_wh1_vers_wh3.py`), puis ramenée à la taille du relief (`lf_normal_a_la_taille_du_relief.py`).
3. (fusionnée dans l'étape 2)
4. `shroud_heights.py --carte <carte> --apply` (22.09.2026) : BOB écrit le brouillard plat à 1,0 ;
   règle de CA : max 2 × 2 du relief + calque `HeightShroud` (§ 15, n° 72).
5. `camera_heightmap.py --apply` : la carte de hauteur de la caméra (recette relevée sur les Empires).
6. `textures_sol_wh1.py --apply` (22.09.2026) : les 19 textures de sol de WH1 dans la liste compilée et
   dans le mélange (§ 15, n° 79) ; BOB réécrit les deux à chaque compilation. Une fois pour toutes,
   avant : `textures_sol_wh1.py --convertir` (57 textures au format de CA, 3 min).
7. `build_pack.py` : embarque le tout (liste des Empires, fichiers plus récents que le `.terry`) ; refuse
   un terrain dont la liste compilée ne cite pas les textures de WH1.

L'éclairage (`eclairage_wh1.py`) est installé par `terrain_wh1_vers_terry.py --apply` : fichiers `.environment`
dans `lighting\` ; éclairage global, plus des zones en cylindres remises **une à une, à la manière de CA** (25.09.2026 :
Winterheart seule, `eclairage_wh1.ZONES_REMISES` ; § 15 n° 144, erreur 251) ; collection `environment_collection.xml`
écrite par `build_pack.py`.

En amont, quand les objets ou les arbres de WH1 changent : `modeles_wh1.py --apply` (fichiers de WH1,
décalques convertis compris), puis `terrain_wh1_vers_terry.py --apply` (projet), puis BOB. Si le
relief n'a pas changé, `--sans full_height_map.dds,full_logic_map.compressed_map` à l'étape 1.

**La chaîne réelle (état du 25.09.2026, chaînes 13 à 15, session du rendu)** : `modeles_wh1.py --apply`, générateur,
masques d'eau, BOB, brouillard, caméra, textures de WH1, `lf_normal_depuis_relief.py --apply` ; environ 30 min
(générateur : 17 à 28 min) ; puis `build_pack.py`, `injecter_textes.py --apply`, et l'essai de démarrage
`essai_tours_auto.py --seigneur orion --tours 3` (Charles prévenu). `chaine_terrain.ps1` est EN RETARD sur cette liste
(ni `modeles_wh1` ni `lf_normal`) : le mettre à jour avant de s'en servir. Ce qui suit est l'état du 23.09 :

**La chaîne automatisée (état du 23.09.2026, 06 h 20)** : `powershell -File 02-scripts\chaine_terrain.ps1 -Journal
<log> [-SansPack]`, Terry et le jeu fermés, `rpfm_server` lancé, en tâche de fond (moins de 12 min) : générateur
(`terrain_wh1_vers_terry.py --apply` : projet Terry, rivières lisses, `relief-wh1\mer_finale.npy`, `eau_rivieres.npy`,
`flux_rivieres.npy`), **masques d'eau** (`masques_eau_carte.py --apply`, session d'audit : matériau d'eau de notre carte
et ses masques), BOB, brouillard, caméra, textures de WH1, `build_pack.py`. Ensuite, toujours : `injecter_textes.py
--apply`, puis l'**essai de démarrage** (`debug_chargement.py --arret-apres 45`) **après avoir prévenu Charles** (il ne
doit pas toucher au jeu ouvert), et relire le `script_log` de l'essai et `crash_report\`. Si seuls les masques d'eau, les
scripts ou les textes changent : `masques_eau_carte.py --apply` puis `build_pack.py` suffisent. Si `fichiers_wh1` change :
`modeles_wh1.py --apply` d'abord.

---

## 13. Les gabarits

Un gabarit = `Templates\<nom>\` (à côté de `CAIME\`, `Projects\`, `Tools\`) avec, **à plat** :

| Fichier | Rôle | Qui le lit |
|---|---|---|
| `map.hex` | **requis** : jeu, taille, toutes les couches, couleurs de régions | CAIME |
| `trees.png` | positions des arbres ; sans lui, carte sans arbres | BOB (terrain / tilemap / trees) |
| `tree_database.xml` | essences et règles de distribution | BOB |
| `dynamic_resources.png` | zones de ressources (« lié aux fermes ») ; inutile pour 3K | MapDataBuilder (Dynamic Resources) |
| `dynamic_resources_database.xml` | couleur → type de ressource | MapDataBuilder |

À exclure : `caime_metadata.json` (chemin absolu vers `map_data_config.xml`), `<nom>_autosave.hex`
(toutes les 5 min), `backups\` (toutes les 10 min). `create` copie tous les fichiers de premier
niveau, jamais les sous-dossiers ; jeu et taille sont lus dans `map.hex` ; les swatches viennent de
l'AKit du destinataire, pas du gabarit.

Sur disque : 10 gabarits sur 15 sont complets (Rome, 4 Attila, 2 WH1, 3 Troy) ;
`wh2_main_great_vortex_map_7` n'a pas les arbres ; `3k_dlc07_main_map` n'a que `map.hex` +
`trees.png` ; `wh3_main_combi_map_1`, `wh3_main_chaos_map_2`, `phar_main` n'ont **que `map.hex`**.
Pour fabriquer un gabarit WH3 complet : copier `map.hex` et les quatre fichiers d'appui depuis
`<AKit>\raw_data\EmpireDesignData\campaign_maps\wh3_main_prologue_map\` (seul dossier vanilla
complet), ou depuis `_map_5` pour le `map.hex` actuel.

---

## 14. État des preuves de la chaîne CAIME (20.09.2026)

| Étape | Résultat | Détail |
|---|---|---|
| Compilation du fork, MapDataBuilder | ✅ | Debug AnyCPU ; C++ Debug/Release x64 |
| `config`, `create`, `info`, `export-layer`, `import-layer` | ✅ | Attila et WH3 |
| Design procédural → couches → import → PNG | ✅ | `05-journal\preuve-20-09-2026\` : PNG de CAIME identique au dessin |
| Base WH3 chargée | ✅ après correctif | échouait sur la culture française |
| `validate --all` (gabarit vanilla WH3) | ✅ tourne | attritions, climats, sols, ponts, plages OK ; rivières 117, routes 442, impassable 221, slots 5, sprawl 6 avertissements, régions 109 |
| `process --pathfinding` | ✅ | `pathfinding.ppd` 16,9 Mo en 12 s + 12 images de debug |
| `process --lookup` | ❌ attendu | « no campaign uses the map » : `campaigns.map_name` = `wh3_main_combi_map_5`, pas `_map_1`. Comportement documenté, pas un bug |
| `process --borders` | ✅ après correctif | les options par jeu n'étaient posées que par la fenêtre ; le fork les pose aussi sans fenêtre (commit d18d90b) |
| Prologue vanilla (`wh3_main_prologue_map`, 800 × 600, projet complet) | ✅ | `validate` : 10/11 (une région vanilla sans slot) ; `process --all` : Map Data 2,9 Mo, pathfinding, borders, trade routes, lookup OK ; **Dynamic Resources plante** MapDataBuilder (code −1073741819, fonction absente ou changée dans `tooldatabuilderdll.modder.x64.dll`), non résolu |
| **Carte inventée `ile_claude_map`** (240 × 160, 8 régions + 1 mer, 3 provinces) | ✅ | déclarée par `declare_map.py`, créée sous `raw_data\EmpireDesignData`, `sync-names`, 8 couches générées et importées, `validate` : 10/11 propres (régions : avertissements de forme), `process` : **map_data.esf, pathfinding.ppd, borders.pbd, trade_routes.ptd, lookup.bmp** produits |
| Gabarit WH3 complet | ✅ | `Templates\wh3_main_prologue_map\` (5 fichiers) fabriqué depuis l'AKit ; sauvegarde du dossier vanilla dans `05-journal\` |
| Terry (Steam) se lance | ✅ | `tweak.modder.x64.exe /standalone TerrainMetadataEditor` → « TWeak - Terry » |
| Paquet Store installé | ✅ | v1.3.4908.0 ; Terry, BOB, Dave |
| RPFM 5.0.6 installé, MCP répond | ✅ | 150 outils, 11 invites, 11 ressources inventoriés |
| RPFM : startpos, packs, Dave, en jeu | ⏳ | non abordés |
| **Kit Warhammer 1** installé, `config --game Warhammer` | ✅ (20.09, 16 h 30) | cartes `wh_dlc05_wood_elves_map_1` (400 × 440) et `wh_dlc03_beastmen_map_1` (414 × 250) ; pas de terrain de campagne brut dans le kit |
| Cartes de mini-campagne WH1 dans CAIME | ✅ après correctif | le bloc « 3 inconnus » du map.hex est une liste (§ 15 n° 15) ; `info --names`, 13 PNG, aller-retour identique hors horodatage et CRC |
| `rpfm_server` sur les packs WH1 (dépendances `warhammer`) | ✅ | scripts (2 769 lignes Lua), `startpos.esf`, `map_data.esf`, terrain compilé (172 fichiers) listés et extraits : `05-journal\2026-09-20-inventaire-wh1\` |
| Projet Terry de campagne (IE, ChaosRobie) installé dans le kit WH3 | ✅ | `raw_data\terrain\campaigns\wh3_main_combi_map_1\` : 635 `.layer`, tif à 8 px par hex, `rules.bob` ; pas encore ouvert dans Terry |
| PR #10 (culture invariante) | ✅ fusionnée | 20.09.2026 16 h 29, `origin/main` = `0bc207a` |
| **Carte `wh_dlc05_wood_elves_map_1` transposée en WH3** (400 × 440, 61 régions, 26 provinces) | ✅ 10/11 | chaîne complète dans `02-scripts\build_saison_map.py` ; seul `town-sprawl` échoue (2 colonies en col, contre 5 sur la carte de CA) |
| **Les cinq fichiers de jeu de cette carte** | ✅ | `map_data.esf` 1,2 Mo, `pathfinding.ppd` 1,5 Mo, `borders.pbd`, `trade_routes.ptd`, lookup 13 Mo ; journal `05-journal\2026-09-20-inventaire-wh1\phase-1-carte-logique.md` |
| Filtre d'exception dans MapDataBuilder | ✅ | un plantage de la DLL de CA donne maintenant code, adresse, sens de l'accès et module |
| **Témoin du startpos** (prologue vanilla, pack vide, notre pack écarté) | ❌ **plante pareil** | la cause n'est donc pas dans nos données (20.09, 20 h 29) |
| **Export BOB de la base** (`database` → `<All>`) | ✅ | 3 788 actions en 109 s, zéro erreur ; **1 694 fichiers** dans `working_data\db\`, 54 fichiers + un `.pack` par campagne dans `raw_data\EmpireDesignData\campaigns\` (20.09, 21 h 00) |
| `build_starpos` après l'export BOB | ❌ **rien ne change** | l'adresse du plantage dépend de la **campagne**, pas de l'export : notre carte `+0x234ACF8` (lecture de `0x24`) avant comme après, prologue `+0x27A9A9C` (lecture de `0x0`) avant comme après (témoin refait à 21 h 20) |
| `Campaign / Process start pos` de **BOB** (l'outil officiel) | ❌ | « Startpos file not found after running the game! » — même échec que RPFM (20.09, 21 h 13) |
| **Startpos d'une campagne vanilla** (prologue), kit installé, base exportée, aucun mod chargé | ❌ | plante pareil : **la génération de startpos ne marche pas sur cette installation**, indépendamment de nos données |

---

## 15. Pièges connus

Le journal complet des erreurs commises, avec la règle qui évite chacune, est dans
**`ERREURS-ET-LECONS.md`** à la racine : à lire en entier avant d'agir, à compléter le jour même.

1. **Windows en français** : sans le correctif de culture du fork, la base ne charge pas et tout
   est en lecture seule, éditeur officiel compris.
2. **L'installeur officiel ne livre ni `Templates\` ni `Tools\MapDataBuilder`**.
3. **Ligne 0 en bas** ; retourner les images avant encodage.
4. **Impassable = passabilité** : 1 signifie franchissable.
5. **Nom de carte** : nettoyé silencieusement, sensible à la casse, c'est aussi le dossier de
   sortie ; `create --template` garde le nom du gabarit ; renommer = Ctrl+Shift+N dans l'éditeur,
   et la base doit connaître le nouveau nom (`campaign_map_regions`, `campaigns`, `areas_of_interest`).
6. **Gabarits WH3 périmés** (`_map_1` vs `_map_5`) et **sans fichiers d'appui**.
7. **Un changement de base ou de chemin AKit** ne prend effet qu'après Reload / réouverture.
8. **RPFM 5 n'a plus de CLI** : CAIME veut `rpfm_cli.exe` (4.2.7) ; les IA veulent le MCP (5.0.6).
9. **BOB n'a pas d'aide** en ligne de commande ; ses options inconnues ouvrent une boîte modale
   qui bloque le processus : ne jamais lancer BOB avec des arguments depuis un script sans
   surveiller.
10. **MSBuild** : restaurer avec `-p:RestorePackagesConfig=true -p:SolutionDir=<racine\>`.
11. **PowerShell 5.1** : dans une fonction, le pipeline devient la valeur de retour (`Write-Host`
    pour afficher) ; un `.ps1` sans BOM est lu en ANSI (pas d'accents) ; `Get-Content -Raw`
    détruit les accents d'un UTF-8 sans BOM.
12. **Git Bash + `sed`** : un motif avec antislashs est converti en chemin MSYS. Éditer avec un
    outil, pas avec `sed`.
13. **La doc CAIME se contredit** par endroits (`.bin`/`.ppd`, tailles de slots WH3, couleurs
    des avertissements, `.json`/`.xml` du Map Data Editor) : croire le validateur et le disque.
14. **Auto-mises à jour** : l'installation officielle (Velopack) se met à jour seule, le fork non ;
    refusionner `main` amont de temps en temps.
15. **`map.hex` : le bloc entre les listes de noms et les couleurs n'est pas « 1, 0, 0 »** mais
    `N` puis N × (chaîne, uint32), et le bloc de fin `N` puis N × (taille, octets) — un bit par
    hex, lignes complétées à l'octet. Les cartes vanilla ont une entrée, les mini-campagnes WH1
    en ont deux ; CAIME amont les lit de travers (« 20 × 0 hex », exception). Corrigé dans le fork
    (`MapHexFile.cs`, 20.09.2026) ; candidat à une PR amont.
    **La chaîne est la valeur `campaigns.mask` de la campagne qui utilise la carte** (établi le
    20.09.2026 au soir dans `raw_data\db\campaigns.xml` du kit WH1 : `wh_dlc05_wood_elves` → `mask = 32`,
    `wh_dlc03_beastmen` → `mask = 8`, `main_warhammer` → vide). Chaque entrée porte donc un masque
    de campagne, et le bloc de fin qui lui répond est le masque hex par hex (tous à zéro dans les
    22 fichiers de référence : lecture plausible, non vérifiée sur données non nulles). Les cartes
    vanilla n'ont que l'entrée vide, la carte d'une mini-campagne a l'entrée vide **et** la sienne.
15 bis. **Deux documentations de référence** (données par Charles le 20.09.2026) :
    le **wiki de modding Total War**, <https://tw-modding.com>, et le **hub de documentation de
    script** de Chad Vandy, <https://chadvandy.github.io/tw_modding_resources/>. Pages utiles :
    - `wiki/Tutorial:Campaign_Map_Making_for_Warhammer_III` — la seule description publique de
      notre chaîne : carte « logique » dans CAIME, carte « visuelle » dans Terry, puis BOB. Elle
      dit que **« Build Startpos » de RPFM sert à produire `spd_data.esf` et `hlp_data.esf`**, les
      fichiers de pathfinding d'une carte neuve, et que **`spd_data.esf` est critique dès qu'on
      touche aux données de carte** (`hlp_data.esf` tolère d'être périmé, mais le pathfinding
      devient absurde). Elle donne aussi l'ordre de traitement BOB du terrain (hauteur d'abord,
      puis tuiles, puis `global_props.bin` — **à refaire à chaque région ajoutée ou retirée**).
    - `wiki/Startpos` — **« there can be only one startpos »** : un seul mod de startpos à la fois.
      La page liste ce qui **exige** un startpos (factions jouables, `faction_potential`, types
      d'agents par culture, emplacements de hauts lieux, diplomatie de non-agression, CQI du chef
      de faction, groupes de noms) et ce qui se fait **au script ou en base** (régions, seigneurs,
      objets, unités et bâtiments de départ, viviers de mercenaires, associations de régions).
      Utile pour décider quoi mettre où dans les phases 5 et 6.
    - Le standard communautaire est **MIXER** (Mixu's Unlocker), un mod de startpos pour les
      campagnes **existantes** — il ne fabrique pas de startpos pour une carte neuve.

16. **`rpfm_server` : une session MCP = un état** (jeu, packs ouverts). Tout dans un script,
    `set_game_selected` en tête ; le pack d'un DLC WH1 ne contient pas le contenu du DLC, chercher
    par les dépendances (`get_packed_files_names_starting_with_path_from_all_sources`,
    `extract_packed_files` avec la source `GameFiles`).
17. **Arguments officiels des outils WH1** (lus dans `assembly_kit\msix\config.json`) : Terry =
    `tweak.assemblykit.x64.exe /standalone TerrainMetadataEditor`, BOB = `bob.assemblykit.x64.exe
    -no_console`, DaVE sans argument (`-platform=ms` en plus dans le conteneur Store).
18. **Ce que le projet Terry de campagne référence sans le livrer est dans les packs WH3** :
    `terrain\tiles\campaign\_tile_database\` (`_settings.bin` + `tiles\`, 321 fichiers, avec les
    tuiles `roads*`, `river*`, `sea*`, `cliff_gen*`, `generic` : 2 404 fichiers, 216 Mo),
    `terrain\campaigns\<carte>\lighting\*.environment` (27 pour la carte IE) et
    `materials\environment\campaign_sea\*.material`. Extraits le 20.09.2026 dans
    `working_data\` du kit WH3 par `rpfm_mcp.py` (source `GameFiles`). Le terrain compilé WH3 se
    compose de `full_height_map.dds`, `full_logic_map.compressed_map`, `global_props.bin`,
    `tile_list.bin`, `tile_mask.dds`, `patch_mask.dds`, `shroud_heights.dds`, `snow_mask.dds`,
    `colour_overlay.dds`, `corruption_mask.dds`, `lf_normal.dds`, `lf_sea_colour.dds`,
    `global_map\`, `lighting\`, `models\` (412 `.wsmodel` de rivières et props pour IE).
19. **`git rebase --onto <base> <réf> <branche>` ne rejoue que `<réf>..<branche>`** : pour retirer
    un commit du milieu, partir de la base amont complète avec `--empty=drop` (vérifier d'abord
    `git log --oneline <réf>..<branche>`).
20. **Les emplacements de colonie ne se transposent pas tels quels entre jeux** : Warhammer 1 en
    peint 7 hex (4 en port), le validateur de Warhammer 3 en exige **19 de terre, 16 pour un port**,
    comptés par région et sur la terre seulement (le type de sol décide, pas la région).
    `02-scripts\grow_town_slots.py` fait pousser l'emplacement en disque autour de son centre et
    étend l'étalement urbain, puis règle le contour du danger.
21. **Le validateur `town-sprawl` est plus strict que les données de CA** : un terrain difficile à
    deux hex d'une colonie doit la toucher, et une colonie ne peut toucher qu'une seule zone de
    terrain difficile. La carte des Empires Immortels de CA échoue sur 5 colonies. Un échec de ce
    type sur une colonie en col n'est pas un défaut de transposition.
22. **Les index de couches ne survivent pas à un changement de jeu** : 13 sols de terre et 24
    climats en WH1, 15 et 40 en WH3. Recaler **par nom** (`caime_layers.py remap`), jamais par
    index ; les listes de régions, elles, gardent leur ordre si les clés sont identiques.
23. **`declare_map.py --undo` ne se lance qu'avec la fiche qui a servi à `--apply`.** Il retire ce
    que la fiche courante déclare, et `regions` comme `provinces` sont des tables **globales** :
    une fiche modifiée supprime des lignes utilisées par d'autres cartes. Symptôme en aval :
    `sync-names` annonce 0 région et **MapDataBuilder plante sur un pointeur nul**. Contrôle avant
    tout `process` : `sync-names` doit annoncer le bon nombre de régions.
24. **Un plantage de la DLL de CA se lit avec le filtre d'exception de MapDataBuilder** (fork) :
    code, adresse, sens de l'accès et module. « reading 0x8 » = pointeur nul, donc une donnée
    manquante côté base, pas un problème de format.
25. **MapDataBuilder plante si la zone jouable de la carte traitée est la DERNIÈRE ligne de
    `campaign_map_playable_areas`.** Vérifié quatre fois dans les deux sens le 20.09.2026 : même
    contenu de lignes, seul l'ordre change ; la nôtre en dernier → `0xC0000005` (lecture de
    l'adresse 8) dans `empireutility.modder.x64.dll+0x318ead` ; une ligne après la nôtre → le
    fichier se produit. Les sept autres tables de la déclaration se réordonnent sans conséquence.
    **Règle codée : `02-scripts\fix_playable_area_order.py`, appelé par `build_saison_map.py`
    juste après `declare_map --apply`.** Comme `declare_map` ajoute toujours en fin de fichier,
    toute carte neuve tombe dans le piège tant qu'une autre ligne ne la suit pas.
26. **Les clés de faction changent de préfixe d'un opus à l'autre** : `wh_dlc05_brt_mini_bastonne`
    en WH1 est `wh_main_brt_bastonne` en WH3, Gisoreux s'y écrit `gisoroux`. Apparier sur la
    culture et la fin de la clé (`02-scripts\build_correspondances.py`), jamais sur le préfixe.
28. **Écrire une table dans un pack avec RPFM** : les lignes doivent être au format **« traité »**
    (`fields_processed`), pas au format brut de la définition. Les colonnes `r`, `g`, `b` d'une
    région y deviennent **une seule valeur `ColourRGB` placée en fin de ligne** ; sinon
    l'enregistrement refuse (« expected a row with 6 fields, but we got a row with 8 »). La
    charge utile de `save_packed_file_from_view` est `{"DB": <objet renvoyé par decode>}`.
29. **`build_starpos` (RPFM)** : le pack doit être **dans `<jeu>\data\`** et **ouvert par son
    chemin en barres obliques**, sinon « The Pack needs to be in /data ». La campagne n'apparaît
    dans `build_starpos_get_campaign_ids` que si le **pack** contient sa ligne `campaigns_tables`
    (la déclarer dans le kit ne suffit pas). La génération elle-même **demande que le jeu tourne**.
30. **`campaign_maps_tables` est absente des packs de Warhammer 3** (le pack la saute : « absente de Warhammer 3,
    ignorée ») : une carte s'y déclare par `campaigns.map_name` et par `campaign_map_playable_areas`. Le kit 8.1 a
    pourtant encore `TWaD_campaign_maps.xml` (avec `requires_startpos_reprocess`) : la table existe côté kit, pas
    côté jeu.
27. **Une campagne neuve dans WH3, telle que la fait « The Old World Campaign »** : une ligne
    `campaigns`, une ligne `campaign_map_playable_areas` (avec `frontend_image`, `video`,
    `sort_order`, trois `campaign_overlay_*` en `.dds`), les lignes `campaign_victory_conditions`,
    les tables `regions` / `provinces` / `campaign_map_regions` / `campaign_map_settlements`, les
    cinq fichiers produits par CAIME plus le lookup en `.tga` **et** `.dds`, le terrain compilé,
    les scripts, et **un seul `startpos.esf`** dans `campaigns\<campagne>\`. Aucune table
    `start_pos_*` ne part dans le pack : ce sont des entrées de l'Assembly Kit.
31. **L'écran « Nouvelle campagne » se lit dans sa mise en page**
    (`ui/frontend ui/campaign_select_new.twui.xml`, à extraire des fichiers du jeu) : fond plein
    écran = `frontend_image` ; bouton = même nom + **`_button`** (278 × 128) ; carte verticale =
    même nom + **`_vertical`** (380 × 735, 660 px d'image puis une bande unie) ; titre et
    description = loc **`campaign_map_playable_areas_onscreen_name_<index>`** et
    `..._onscreen_description_<index>` (le **numéro** de la zone jouable, pas la clé de campagne) ;
    onglet Carte = `radar_file` ; ordre de la liste = `sort_order`. Script :
    `preparer_images_campagne.py`, vérification dans `build_pack.py`.
32. **Le jeu charge les `.loc` d'un mod quelle que soit la langue du joueur.** Un mod ne doit donc
    poser **que les clés que le jeu ne connaît pas** : toute clé du jeu qu'il redéfinit remplace le
    texte à jour, dans toutes les langues et dans toutes les campagnes (erreur 47). Deux langues =
    deux packs : le second ne contient que son `.loc`, **sous le même chemin**, et passe devant
    (`!` en tête du nom). Scripts : `extraire_textes_wh1.py --langue`, `injecter_textes.py`.
33. **Sans `start_pos_starting_general_options`, aucun seigneur n'est choisissable** : la table
    relie un personnage du startpos (`general`) à une fiche de `frontend_faction_leaders`, dont la
    clé est libre. Une campagne peut avoir ses propres fiches (Warhammer 1 le faisait pour ses
    mini-campagnes : `..._political_party_mini_...`). Script : `ajouter_seigneurs_jouables.py`.
34. **La génération du startpos grave un aperçu de la minicarte** (`SAVE_GAME_HEADER` > `MAPS`,
    RGBA) à la taille `preview_width` × `preview_height` de la zone jouable : régénérer le startpos
    après tout changement de minicarte ou de ces colonnes, et donner à l'aperçu les proportions de
    la carte (472 × 600 ici, la valeur de Warhammer 1).
35. **Images de correspondance de Warhammer 3** : TGA à palette, **16 bits par pixel**, palette BGRA
    32 bits, origine en bas, une couleur par région ; la minicarte (`radar_file`) est un parchemin
    RGBA à la moitié de la résolution, la correspondance de la minicarte au quart. Script :
    `preparer_minicarte.py`.
    **[Précision du 25.09.2026 (erreur 253) : CA écrit ses lookups ligne 0 au NORD (octet 17 = 0x10) et le jeu lit les lignes dans l'ordre du fichier ; nos lookups sont écrits ainsi depuis (`preparer_minicarte.py`).]** [25.09.2026, ménage]
36. **BOB ne compile le terrain d'une campagne que si sa base (`db.pack`) connaît la carte** (§ 12.3).
    Symptôme : 6 actions au lieu de 15, aucune erreur. Le témoin qui le montre : le projet de
    ChaosRobie copié sous un autre nom échoue pareil. Script : `compiler_terrain_bob.py`.
37. **Terry ouvert verrouille `working_data`** (les packs qu'on y pose, notamment) : le fermer avant
    d'y écrire ou d'y lancer BOB (erreur 51).
38. **Quand un outil de CA ne fait rien sans erreur**, lire la condition dans sa DLL avant d'essayer
    des fichiers : `02-scripts\lire_dll.py` (références aux chaînes, fonctions, tables virtuelles,
    annotation du désassemblage de `cdb -z`), puis vérifier sous `cdb` (erreur 50).
39. **« Generate Camera Height Map » fait planter BOB** (DirectX, puis pointeur nul) alors que
    `camera_heightmap.png` est indispensable : `camera_heightmap.py` le fabrique (§ 12.3).
40. **`lf_normal.dds` de WH1 se reprend en inversant le vert** (Y de signe opposé entre WH1 et WH3) :
    `lf_normal_wh1_vers_wh3.py`. BOB n'en produit pas pour une campagne.
41. **Chaque fichier compilé a son sens de rangement** : `full_height_map.dds` du sud au nord,
    `lf_normal.dds` et `camera_heightmap.png` du nord au sud (comme les rasters de Terry). Le
    vérifier par corrélation avec les hauteurs, fichier par fichier, avant d'en fabriquer un.
42. **Chaque colonie doit avoir un emplacement `primary`** (`start_pos_region_slot_templates`) :
    sans lui le startpos se génère quand même, et le jeu plante au tout début du chargement de la
    campagne (`Warhammer3.exe+0x27A7DFF`, lecture de 0x30). Les régions de forêt elfes de WH3 en
    ont un : `wh_main_special_waterfall_palace_primary` est le gabarit générique de CA (erreur 54).
43. **Un startpos se contrôle par sa structure** : `comparer_structure_esf.py --esf <le nôtre>
    --reference <un startpos qui charge>` décompresse les deux (LZMA) et signale les enfants ou
    les blocs que la référence a toujours et que nous n'avons pas. À passer après chaque
    génération, avant l'essai en jeu.
44. **Lire un vidage du jeu** : `cdb -z <vidage>` (le code vient de l'exe sur disque) ; la
    fonction qui rend nul et son prédicat disent ce qui était cherché (ici la chaîne « primary ») ;
    `lire_dll.py refs <exe> "texte"` et `chaines_de_fonctions.py` trouvent qui cite une chaîne. Le
    code de Warhammer3.exe est dans `.sbss` et `.shared` (noms brouillés, `.text` = 512 octets) ;
    pas de RTTI lisible (erreurs 55, 56).
45. **Une ligne ajoutée au kit n'existe pour la génération du startpos qu'une fois dans
    `zz_startpos_db.pack`** : `synchroniser_pack_startpos.py --table <start_pos_...>` (`--maj` pour
    réécrire aussi les lignes qui diffèrent).
46. **Une campagne neuve exige les données de carte de l'IA** (`hlp_data.esf`, `spd_data.esf` dans
    `campaign_maps\<carte>\`) : générer le startpos avec `startpos_manuel.py ... --ai-map-data`.
    Sans elles, plantage au réglage du joueur humain (`+0x255EF20`), erreur 59.
47. **Chaque faction doit avoir un groupe d'IA qui contient une personnalité** : le groupe de
    l'Empire Immortel, sinon le mineur de sa culture (`groupes_ia.py`). Sinon plantage à
    `+0x27A863F` (erreur 57).
48. **Dans `<jeu>\data\`, le pack passe devant les fichiers en vrac** : un startpos régénéré ne compte
    qu'une fois le pack reconstruit (erreur 58).
49. **Voir ce que fait le jeu pendant un chargement** : `debug_chargement.py` (le jeu sous `cdb`,
    points d'arrêt qui journalisent ; `--commandes <fichier>` pour les siens, `--arret-apres N`).
    Module `warhammer3_retail_x64` dans un processus vivant. Quelqu'un doit faire le chemin du menu.
50. **Un gabarit d'emplacement se juge à ce qu'il permet, pas au fait que le jeu charge** :
    `comparer_batiments_wh1_wh3.py` compare, région par région, les chaînes permises en WH1
    (superchaînes) et en WH3 (jeux de chaînes, parents, retraits), et classe monuments et chaînes
    abandonnées par CA. Code de sortie 1 si une région perd un bâtiment de base (erreur 60).
51. **Recette d'un secondaire de forêt de WH3** (13 régions de l'Empire Immortel sur 13) :
    `wh3_main_secondary_addon_garrison_major` + `wh3_main_secondary_core_generic_major_variant_wef_forest`
    + `wh3_main_secondary_addon_res_<ressource>` + le jeu `*_landmark_*` de la région. Les secondaires
    humains (`wh3_main_secondary_core_generic_major`) ne donnent aux elfes que les avant-postes.
    Un gabarit mal choisi fait aussi **écarter en silence les bâtiments de départ** de la colonie
    (12 bâtiments de WH1 revenus dans le startpos une fois corrigé). `declarer_gabarits_elfes.py`.
52. **`building_instances.num_instances` est une limite par colonie** (1 426 bâtiments ordinaires
    sur 1 431 y valent 1), pas une unicité dans le monde (erreur 61).
53. **Diplomatie de départ** : `start_pos_diplomacy`, une ligne par paire ; dans le startpos elle
    donne les chaînes `war`, `NON_AGGRESSION_PACT`, `INITIAL_NON_AGGRESSION_PACT` et des
    enregistrements de posture de l'IA (`CAI_FACTION_STANCE_...`).
54. **Arbres de campagne** : la palette de `tree.tif` (projet Terry, 2 px par hex, 255 = rien) **est**
    la table `campaign_tree_ids` (couleur -> famille d'essences, 4 variantes chacune) ; BOB en tire
    `campaign_maps\<carte>\display\trees\trees.campaign_tree_list`. L'apparence d'une famille suit la
    culture qui possède la région (`campaign_tree_type_cultures` : elfes sylvains -> chênes
    `wef_tree_oak_*`). Le `trees.png` de WH1 se traduit famille par famille (`terrain_wh1_vers_terry.arbres`).
55. **Routes dans `tile_map.png`** : chaque hex de route est un bloc 2 x 2 plein (grammaire des
    Empires, 30 283 hex sur 30 400) ; un tracé aminci laisse des trous que BOB signale (erreur 63).
    Compter les « Failed to find tile » de `bob_warnings.log` après chaque compilation.
56. **Rivières de WH3** : les Empires et Old World n'ont aucune tuile de rivière ; les grandes
    rivières sont des chenaux `sea` bordés d'un pixel `sea_coast` (255, 255, 0) ou `cliff_gen`
    (253, 3, 1), les autres des modèles posés comme objets (`models/river_*.wsmodel`). La base de
    tuiles n'a qu'une tuile `river` ; les types `river_mesh*` existent dans la légende.
57. **Une compilation BOB du terrain prend moins d'une minute** (relief compris, 21.09.2026 soir) :
    on peut itérer sur le terrain et lire les avertissements de BOB sans passer par le jeu.
58. **Objets du terrain de WH1** (`global_props.bin`) : index de lots `bmd_objects.<région>.<a>[.<b>]`
    (BMD « FASTBIN0 » v21 ; WH3 : v27) ; un objet = modèle + matrice 3 x 3 (échelle par lignes) +
    position, 30 octets de drapeaux (octet 0 = décalque), mode `BHM_CLASSIC`. Les positions sont en
    **espace des hex : z × √3/2** pour le monde (écart médian au relief 1,20 -> 0,26). Variantes :
    bit 0 = habillage naturel, masque nul et bits 6, 8 = Chaos, bit 12 = Vampires. Lecteur :
    `lire_props_wh1.py` ; conversion en calques Terry : `props_wh1_vers_layers.py`.
    **[Corrigé par l'erreur 89 (22.09.2026) : l'espace des hex EST le monde de WH3 pour les entités ; voir n° 98.]** [25.09.2026, ménage]
59. **Rotation dans un calque Terry** : `rotation="rx ry rz"` (degrés) vaut la matrice compilée
    Rx(-rx)·Ry(-ry)·Rz(-rz) (12 objets inclinés des Empires, écart 1e-5). Décalques : entité `ECDecal`.
60. **Modèles de WH1 dans WH3** : 335 modèles de campagne sur 519 n'existent plus sous leur chemin
    (dossier `ruins\` vide, pics nordiques, arbustes réorganisés) ; ceux de WH1 sont en RMV2 v7 à
    matériaux spéculaires, ceux de WH3 en v8 PBR : les reprendre demande une conversion. WH3 a
    presque tous les rôles en objets préfixés par culture (`vegetation\shrubs\<culture>_shrubs_*`,
    `grass\<culture>_grass_*`, `trees\<culture>_tree_oak_*`, `generic_props\ruins\gen_ruin_*`...) :
    table de substitution `props_wh1_vers_layers.SUBSTITUTS` (15 557 objets, 101 sans équivalent).
    **Mais WH3 lit encore RMV2 v7** (41 % d'un échantillon de ses propres modèles, et du v6) : la
    fidélité passe par les fichiers de WH1 eux-mêmes (`modeles_wh1.py`), jamais sous un chemin qui
    existe dans WH3 (le pack remplacerait le fichier de CA dans toutes les campagnes). Substituts
    désactivés (Charles : « ce n'est pas du tout ceux de WH1 », erreur 67).
61. **La neige de WH1 n'est pas dans son masque de neige** (vide) : ce sont des textures (6 à 9) et
    des arbres d'hiver au même endroit (clairière d'hiver de la Saison des Révélations). WH3 fait sa
    neige par `SnowMask` (Empires : 255 au coeur, 240 à 254 aux bords) sans texture de neige dessous.
62. **Terry de WH3 montre tous les objets sans appliquer les masques de culture** ; les décalques y
    sont des sphères blanches. Il repère les objets mal posés ; la visibilité se juge en jeu. Le kit
    de WH1 n'a pas de projet Terry de campagne : la référence de WH1 est le jeu WH1. Pour piloter
    Terry : `lancer-outils.ps1 -Outil terry`, puis `request_access` sur `tweak.modder.x64.exe`.
63. **Une campagne a DEUX terrains** (22.09.2026) : celui de la campagne (`terrain/campaigns/<carte>/`)
    et un **terrain de bataille** dans `terrain_folder` de la zone jouable (`terrain/battles/<dossier>/`),
    que le jeu lit dès la première bataille terrestre, IA comprise. Sans lui : plantage en fin de tour
    (`Warhammer3.exe+0x1497949`, lecture du masque des lieux de bataille, pointeur nul ; la pile porte
    `land_normal` et la position normalisée de la bataille). CA y livre 12 fichiers : carte des lieux
    de bataille (`battle_locations_map.bin/.xml`, `blm_primary_mask.dds`, `blm_secondary_mask.dds`,
    16 bits à la taille de la carte de tuiles), `full_lf_logic_map.compressed_map` et `lf_normal.dds`
    (4 × la carte de tuiles), `tile_map.bmd/.index/.tiles`, et trois cartes de captage.
64. **Ce terrain de bataille est un support** : une seule tuile factice
    (`terrain\tiles\battle\dummy_set_bca_gen\dummy_4_x_4`, couleur 255,120,200), un seul climat
    (`default` aux Empires, `hef` au prologue et au Chaos), relief plat. Recette :
    `dossier_bataille_campagne.py --apply` (projet dans `raw_data\terrain\battles\<carte>\`), puis
    `compiler_terrain_bob.py --bataille --apply` (≈ 1 min 40 ; branche « bataille » de BOB : Tilemap,
    Heights & Normals, Battle Locations Map), puis `build_pack.py`. Deux pièges : un `[Terrain]` local
    dans `rules.bob` remplace celui du dossier parent (y remettre `PrefabRoot`), et le dossier
    `raw_data\art\prefabs\battle\` doit être dans la configuration (règle `[Prefab] TargetPath`).
65. **Les cartes de bataille se choisissent par captage** : cartes `blm_catchment_override*.png`
    peintes (une couleur = une zone de `battle_catchment_override_areas`), puis
    `battle_catchment_override_battle_mappings` (zone, cultures, type de bataille, **`battle_path`** =
    dossier de bataille de la campagne) vers des groupes de cartes (`..._group_battles`). La couleur
    noire est la zone `Gatekeeper` (par défaut). **Fait depuis le 23.09.2026** (session « IA et modding 3D »,
    `dossier_bataille_campagne.py --captage`) : 12 fichiers `blm_catchment_override*`, 119 lignes
    `battle_catchment_override_battle_mappings` ; les 57 colonies tombent dans une zone de leur culture (18 elfes,
    15 + 12 Bretonnie nord et sud, 4 Mousillon, 5 peaux-vertes, 3 nains) ; seuls 340 pixels de petits lacs en noir.
66. **L'exploration de départ n'est pas dans le startpos de WH3** (aucun `CAMPAIGN_SHROUD` ; celui de
    WH1 en portait un pour ses deux factions jouables) : ce que WH1 montrait exploré au tour 1 se
    refait par script (fonctions `make_region_*_in_shroud` du gestionnaire de campagne ; nom exact à
    relever dans les scripts de WH3 avant usage).
67. **Reprendre un fichier de WH1 sans jamais écraser WH3** (`fichiers_wh1.Relocateur`) : absent de
    WH3 -> son chemin ; identique octet pour octet -> rien ; différent -> `<racine>/_wh1/...` et chaque
    fichier qui le cite est corrigé (RMV2 : champs de chemin de taille fixe, place vérifiée). Sur notre
    carte, 219 fichiers de WH1 sur 937 ont une autre version dans WH3 au même chemin. Les packs de WH3
    sont compressés en zstd : `contenu_pack.SourcePacks` les lit (bibliothèque zstd de RPFM).
    **[Sauf si des modèles de CA citent ce chemin : un fichier posé là est lu par CA dans toutes les campagnes ; copie sous un chemin à nous (`fichiers_wh1.SUBSTITUTS_A_NOUS`), et `build_pack` refuse un modèle qui cite encore l'ancien (erreur 254).]** [25.09.2026, ménage]
68. **Arbres de campagne** : `trees.campaign_tree_list` garde des **identifiants** (en-tête version 4 et
    bornes, puis par identifiant : nom, nombre, enregistrements de 15 octets x/hauteur/z + 3 octets) ;
    le modèle se choisit au chargement (`campaign_tree_variants` × `campaign_tree_type_cultures`). BOB
    ne connaît que les identifiants de `db.pack` : pour des arbres neufs, peindre une famille porteuse
    et renommer après BOB (`arbres_wh1.py`, recomposition dans `build_pack.py`). Le nombre d'arbres
    ne dépend pas de la famille peinte.
69. **Le terrain de WH1 est surtout fait de tuiles** : son `tile_list.bin` (FASTBIN0 v1, lu par WH3 pour
    son prologue) pose 480 tuiles (falaises sur mesure, montagnes, rivières, sol), dont 407 absentes de
    WH3 ; ses tuiles ont la structure de celles de WH3. Son `global_blend.dds` a le format du nôtre (un
    octet par pixel = rang de texture dans `texture_arrays.xml`).
70. **Le sol n'est dessiné que sur les parcelles couvertes par `PatchVisibilityMask`** (22.09.2026).
    Le terrain se découpe en parcelles de p = plafond(plus grand côté de la carte de tuiles / 128) px ;
    la grille compte (largeur // p) × (hauteur // p) parcelles : Empires 125 × 84 (p = 23), prologue
    123 × 92 (p = 13), notre carte 114 × 125 (p = 7). C'est la taille du `patch_mask.dds` compilé, et
    celle que le `.terry` doit déclarer pour `PatchVisibilityMask` (255 partout aux Empires). Avec une
    grille trop petite (34 × 38 chez nous jusqu'au 22.09.2026), Terry ne dessine le sol générique que
    dans ce coin de la carte : ailleurs n'apparaissent que les tuiles spéciales (routes), et le ciel au
    travers. Garde : `terrain_wh1_vers_terry.controle_pvm`.
71. **Les drapeaux de `patch_mask.dds`** (R8_UINT, une case par parcelle) : 0x10 terre, 0x20 mer,
    0x40 parcelle contenant des tuiles spéciales (routes, côtes, falaises : 70 % aux Empires, 15 % chez
    nous). Ce n'est pas la visibilité.
72. **`shroud_heights.dds`** (R32F, moitié de la résolution du relief, rangé du sud vers le nord) vaut
    le maximum 2 × 2 du relief plus le calque `HeightShroud`. BOB l'écrit plat (1,0 partout) pour une
    carte neuve : `shroud_heights.py` le recalcule après BOB.
73. **`lf_normal.dds` a la taille de `full_height_map.dds`** (4 × la carte de tuiles : Empires
    11 520 × 7 764, prologue 6 400 × 4 804). Celui repris de WH1 faisait le double :
    `lf_normal_a_la_taille_du_relief.py` garde son deuxième niveau comme niveau principal.
74. **Les textures d'un décalque de campagne se trouvent par suffixe** (22.09.2026). Le modèle (RMV2 de
    576 octets, matériau 100 : une boîte de projection) ne cite aucune texture, seulement un chemin de
    base sans extension (champ de 256 octets). WH3 y ajoute `_base_colour` (DX10 BC3 sRGB, la forme du
    décalque dans l'alpha), `_material_map` (DX10 BC3 : G = rugosité, B = 0, A = 255) et `_parallax`
    ou `_normal` (DXT5) ; WH1 y ajoutait `_diffuse` (DXT5, forme dans l'alpha), `_specgloss`
    (brillance dans l'alpha) et `_parallax` ou `_normal`. Un décalque de WH1 dans WH3 sans ses textures
    converties s'affiche en carré opaque. Conversion : `decalques_wh1.py` (le `_diffuse` devient
    `_base_colour` sans réencodage ; rugosité = 255 - brillance moyenne, contrôlée sur la roche de CA).
    Les modèles v7 de WH1 (textures de types 0, 1, 3, 11, 12) restent lisibles : les Empires posent plus
    de 200 000 objets v7.
75. **Le sol de WH1 = ses maillages, pas `lf_height_map`** (22.09.2026). WH1 dessine son terrain avec
    `global_meshes\land_mesh_N` (72 morceaux de 36,65 unités, 64 % de la carte) et, ailleurs, avec les
    maillages propres de ses tuiles de montagne, de falaise et de rivière. `lf_height_map` est un relief de
    base, 0,26 plus bas en moyenne : un objet de WH1 y flotte. `relief_maillages_wh1.py` rastérise les
    maillages de terrain ; `terrain_wh1_vers_terry.sol_wh1` s'en sert (objets posés à 0,03 près).
76. **Format CHMF v5** (cartes de hauteur compressées de WH1 : `hf_height_map.data` des tuiles,
    `.logic_heights`, `lf_*.data`) : `02-scripts\chmf.py` (blocs de 16 × 16 : constant, palette, écarts
    sur 1 à 15 bits, brut ; hauteur = min + (max − min) × v / 65535).
77. **`tile_list.bin`** (v1 de WH1, v2 de BOB, même disposition) : enregistrements de 21 octets
    `<HHBBffHIB>` à la suite des noms, des climats et de l'en-tête : x, y en cases (**y compté depuis le
    sud**), code de rotation (0x10, 0x20, 0x40, 0x80), masque de climats, min et max du sol sur l'emprise
    élargie de 2 cases (coin sud-ouest, W × H cases), indice de tuile. Pose exacte des `custom_mesh` de
    montagne : en cours (journal `2026-09-22-phase-4\relief-tuiles-wh1.md` § 6).
78. **Terry montre toutes les variantes de culture à la fois** : les éclats d'obsidienne, crânes et
    décors du Chaos (masque « Démons, Hommes-bêtes, Norsca, Chaos ») y apparaissent partout, alors qu'en
    jeu, comme dans WH1, ils n'apparaissent que dans les régions de ces cultures. Juger la fidélité en jeu,
    au tour 1.
79. **Textures de sol d'une carte de campagne** (22.09.2026, journal `2026-09-22-phase-4\
    eclairage-textures-wh1.md`). La liste compilée `global_map\texture_arrays.xml` (v2) cite les 144 groupes
    de WH3 (couleur, matière, climat, normale) ; `global_blend.dds` porte un octet par pixel = numéro du
    groupe, celui de `blend.tif`. Le jeu lit les chemins de cette liste ; **Terry ni cette liste ni une
    texture en vrac dans `working_data` au chemin de CA** (deux essais) : une texture propre à la carte ne
    se voit qu'en jeu. Formats de CA : couleur BC7 sRGB 1024², 11 niveaux, alpha 255 ; matière BC7, G =
    rugosité (herbe ≈ 200 à 224), R ≈ 0, B 0, A 255 ; normale DXT5 1024², 10 niveaux, R 255, B 0, G/A
    normale (disposition de WH1). WH1 : DXT5 2048², `_spec_gloss` (brillance dans l'alpha ; rugosité =
    255 − brillance). `02-scripts\bc7.py` encode le BC7 (mode 6).
80. **Éclairage de campagne** : `environment_collection.xml` a le même format (v2, sphères en
    coordonnées du monde) dans WH1 et WH3 ; les `.environment` passent de la v5 à la v11 (soleil et ciel ×
    1000, `legacy_fog` et `legacy_hdr` gardent les formats de WH1) : `eclairage_wh1.py`. **BOB écrit
    `environment_collection.xml`** (c'est une de ses sorties, `compiler_terrain_bob.SORTIES`) d'après le
    projet : `global_lighting` du `.terry` et les entités `ECEnvironmentVolume lighting_file="…"` munies d'une
    forme (`ECDoubleSphere inner_radius outer_radius` -> SPHERE ; `ECInfiniteDoubleCylinder` -> CYLINDER) ;
    toute collection posée à la main est effacée. Il ne touche pas `lighting\`. Attribut XML d'une propriété
    Terry = son nom affiché en minuscules, espaces -> `_` (« Lighting File » -> `lighting_file`, « Visible In
    Shroud » -> `visible_in_shroud`).
    **[Depuis le 23.09.2026, c'est `build_pack.py` qui écrit la collection (cylindres, format compilé de CA) ; n° 102 et 144.]** [25.09.2026, ménage]
81. **La côte d'une carte de campagne se peint en types de côte** (22.09.2026). Aux Empires, toute la mer est
    bordée, côté terre, d'une bande de 2 px de `tile_map.png` (un hex) : `cliff_gen` (253, 3, 1), `sea_coast`
    (255, 255, 0), quelques blocs `cliff_gen_ends` (84, 230, 84) ; BOB en fait falaises et rivages. Sans elle,
    côte en escalier d'hex. Types et couleurs : `working_data\terrain\tiles\campaign\_tile_database\
    _settings.bin` (aussi `sea_rock_coast`, `sea_coast_sand`, `cliff_base`, `river_mesh*`, `canals`...) ; seules
    les familles présentes dans `working_data\terrain\tiles\campaign\` ont des tuiles. Générateur :
    `terrain_wh1_vers_terry.cotes` (falaise ou rivage selon la côte de WH1).
82. **Caméra de Terry au point près** : `CopyCamera` / `PasteCamera` (sans raccourci par défaut ; F9 / F10 dans
    `working_data\Terry\local\keyboard.xml`) échangent par le presse-papiers `camv3;œil x;y;z;cible x;y;z`, en
    coordonnées du monde (x est, y haut, z nord).
83. **WH1 faisait une partie de son relief avec des objets** (matériau 86 : collines `wef_climate_hill`,
    tertres, fissures ; textures factices `test_*`, l'aspect du sol). Mesurer un objet « volant » avec le bas de
    sa boîte tournée et en cherchant un support parmi les autres objets (erreur 77).
84. **`tile_list.bin` v1 de WH1** : [u16, u32 indice du nom, u8] puis [u16 x, u16 y (depuis le sud), u8 code,
    u8 climats, f32 min, f32 max] ; emprise [x, x + W) × [y, y + H), 0x20 et 0x80 échangent W et H ;
    `02-scripts\tuiles_wh1.py`. La bande de côte se peint **par hex entiers** (hex de terre voisins d'un hex de
    mer) : tracée en pixels, 148 « Failed to find tile » ; par hex, zéro.
85. **Feuillage de WH1 dans WH3** (RMV2 v7, matériau 97 : arbres, herbes) : la couleur doit être sous le type de
    texture **27** (`base_colour`), pas 0 (`diffuse`) ; sinon triangles plats sans texture, en jeu comme dans
    Terry. `fichiers_wh1.feuillage_wh3` change ce seul champ. Les matériaux 68, 86, 100 de WH1 s'affichent tels
    quels.
86. **Émission de WH1 -> WH3** : `emissive_intensity` WH3 = 0,4631 × (WH1)^(5/9), loi que CA a suivie pour ses
    propres matériaux du Chêne des Âges (`fichiers_wh1.emission_wh3`).
87. **Variantes de décor de WH1** : naturel (visible de tous), occupant (masque de culture, comme WH3), corruption
    (Chaos, vampires : montrée selon la corruption de la région, présente dans presque toutes les régions). Au
    tour 1 de la mini-campagne, seule Mousillon est vampirisée (`REGIONS_VAMPIRIQUES_DEPART`).
88. **Les montagnes de WH1 ont le format des falaises de côte de WH3** (22.09.2026, journal `2026-09-22-phase-4\
    montagnes-wh1.md`) : `custom_mesh.rigid_model_v2`, matériau 49 `rigid_default`, chemin de texture de base (champ de
    256 octets à +80 de chaque morceau), sommets de 36 octets, boîte englobante à +24 ; WH3 y ajoute `_base_colour`,
    `_material_map`, `_normal`. 4 niveaux de détail de 1 ou 2 morceaux : lire tous les morceaux
    (`sommets_rmv2.maillage`).
89. **Pose des maillages de montagne de WH1** : coin sud-ouest de l'emprise, u = x / 128 (est), n = z / 128 + H (nord),
    codes = quarts de tour, **drapés** : y = relief de base + 0,2546 + (case / 128) × y local ; leur anneau de base est à
    y local 0, à la hauteur des maillages de terrain qui les bordent. Confirmé sur la hauteur de caméra de WH1 (23
    plus grandes montagnes). Réalisation : objets drapés d'avance, `02-scripts\montagnes_wh1.py`.
90. **`global_map\tile_list.bin`** liste les tuiles « spéciales » que la carte dessine (WH1 : montagnes, rivières,
    falaises, routes, rivages ; WH3 : falaises de côte, routes, rivages), au format de § 15 n° 77 ; le `tile_list.bin`
    de la racine liste toutes les tuiles. `tile_map.index` = (11, 800, 881) ; `tile_map.tiles` = données par case.
91. **`lf_normal.dds` de WH1** (6 400 × 7 048, DXT5, R 255, B 0, normale dans G et A) porte tout le relief fin de la
    carte (crêtes, ravines), sans les montagnes des tuiles.
92. **Terry ne dessine pas les forêts de la carte des arbres** de notre projet (option `show_campaign_tree_map`
    désactivée, et familles porteuses de WH3 remplacées par les arbres de WH1 seulement dans le pack) : les forêts se
    jugent en jeu. Terry a ses propres outils de pose au sol (« Snap Vertically », « Toggle project to ground »).
93. **`<carte>.terry.user`** (à côté du `.terry`) : réglages d'aperçu de Terry — `water_plane` (plan d'eau),
    `show_vegetation` (arbres), `culture` (culture de l'aperçu : variantes d'arbres et décors), `season`,
    `corruption_type`, filtres. Sans lui, pas d'eau ni d'arbres dans Terry. `terrain_wh1_vers_terry.ecrire_terry_user`
    l'écrit d'après celui des Empires. Terry ne dessine un arbre que si sa famille a une variante dans la base du
    kit (une famille « porteuse » n'en a pas).
94. **`trees.campaign_tree_list` de WH1 = format de WH3** (version 4, bornes 266,53 × 339,77, z en espace des hex,
    enregistrements de 15 octets : x, y, z, 0, octet 13 de 0 à 5, 255) : les arbres de WH1 s'embarquent à leurs
    positions (`arbres_wh1.liste_wh1`), essences renommées, hauteurs recalées.
    **[Octet 12 = 1, comme BOB et CA ; une variante BASE pour chaque identifiant (erreurs 187, 192).]** [25.09.2026, ménage]
95. **Fond marin de WH1** : `lf_sea_height_map.dds` (u16, grille du relief) ; lf ≈ 1,0058 × fond + 340 sur la
    terre ; en mer vers −0,68 (−0,52 près des côtes). En mer, le sol visible d'un objet est `sea_height`.
96. **Les montagnes des Empires sont des objets** (3 044 poses de `generic_props/mountains/<culture>/`, réglés
    `visible_in_tactical_view="True"`, `apply_height_patch="True"`, `visible_in_shroud="True"`) : poser celles de
    WH1 en objets est la méthode de CA (§ 15, n° 88 et 89).
97. **Les tuiles de côte de WH3 (`cliff_gen`, `sea_coast`) ne couvrent qu'une bande régulière** : chaque hex de terre
    de la bande doit avoir **une seule série de un à trois voisins de mer**. Une pointe de terre d'un hex (quatre ou
    cinq voisins de mer) ou un hex entre deux bras de mer donne « Failed to find tile » dans BOB, donc un trou dans
    le rivage (28 échecs pour 27 hex de ce genre, 22.09.2026). La mer logique de WH1 respecte la règle ; sa mer
    visuelle non. `terrain_wh1_vers_terry.regulariser_cote` retouche au moindre écart et le générateur s'arrête s'il
    reste un défaut (erreur 87).
98. **Le monde de campagne de WH3 est l'espace des hex** : positions des entités de Terry, caméra (`camv3`), zone
    jouable (profondeur = celle des rasters × 2/√3 : 338,9 chez nous, 748 aux Empires). Terry étire les rasters (Height,
    fond, masques, pixels carrés) de 2/√3 en z : **un point du monde (x, z) lit un raster à la ligne de z × √3/2**. Les
    objets et la liste des arbres de WH1 sont déjà dans cet espace (z gardé tel quel) ; ses maillages de sol et ses
    tuiles sont dans celui des rasters. Preuves : essais terre / mer à la caméra de Terry, et herbes des Empires sur
    leur sol à z × √3/2 (erreur 89).
99. **RMV2 v8 (WH3) : position en demi-flottants = (x, y, z) × w** (w de 1 à 2 ; en v7, w = 1). Mesuré sur la pierre de
    lien `wef_waystone01`, présente dans les deux jeux (mêmes 202 sommets dans un autre ordre, écart 5e-4). La boîte
    englobante de l'en-tête reste la vraie. Code : `sommets_rmv2.maillage`.
100. **Personnages de départ en (0, 0)** : le jeu les place sur la colonie que leur donne
    `start_pos_character_to_settlements` (colonnes character, settlement), en garnison ; sans ce lien, en case (1, 1),
    dans le coin de la carte. CA lie ainsi 198 des 202 personnages liés (erreur 95).
101. **Les rivières de WH3 sont des maillages** : aux Empires, `terrain/campaigns/<carte>/models/river_<id>.wsmodel`
    (RMV2 v8, un LOD, matériau 68 `rigid_default`, morceau « River », sommets de 48 octets, pente comprise dans le
    maillage), qui portent le matériau d'eau de la mer (`wh3_main_combi_campaign_water_plane`, shader
    `rigid_campaign_sea`), posés en `ECMesh`. WH3 n'a presque plus de tuiles de rivière. Chez WH1, une tuile `river*`
    porte son sol (morceau 0, matériau 96, sommets de 8 octets en demi-flottants, 0 à 128 × cases, lit à y −10) et son
    ruban d'eau (morceau 1, matériau 90, flottants, **au quart de l'unité de la tuile**, y ≈ 0,1), dont la ligne est
    aussi dans `bmd_data.bin` (`SST_RIVER` : x, y, z, largeur, 0,5, puis 6 valeurs ; 44 octets par point).
    **[Corrigé par le n° 133 : points de 22 octets.]** [25.09.2026, ménage]
102. **Éclairage de campagne de WH3** : `environment_collection.xml` compilé (un par campagne chez CA : éclairage global
    + zones). Les zones de CA sont des **cylindres infinis** (`ECInfiniteDoubleCylinder` : Realm of Chaos, prologue) ; les
    Empires n'ont qu'une petite sphère (Skavenblight). Une sphère est évaluée à la position de la caméra : en zoomant, on
    en sort (la luminosité change). Sans aucune zone, BOB n'écrit pas la collection : `build_pack.py` l'écrit (éclairage
    global seul). **La neige** est un post-traitement déclaré dans le `.environment` (`post_processes`) dont le matériau
    porte le masque d'une carte (`combi_campaign_snow` -> masque des Empires) : il en faut un par carte (erreurs 96, 97).
    **[En 9.0, le matériau de neige de CA ne cite plus de masque : le jeu lie le `snow_mask.dds` de la campagne (erreur 216) ; zones d'éclairage : n° 144.]** [25.09.2026, ménage]
103. **Textures d'un modèle v7 dans WH3** : le moteur cherche, à côté de la texture citée `X_diffuse` (`_specular`,
    `_gloss_map`...), `X_base_colour` et `X_material_map` ; s'ils existent (objets de WH1 convertis par CA), il les prend.
    Un modèle de WH1 doit donc citer un chemin où CA n'a rien (`_wh1/`). Le feuillage (matériau 97) ne lie la couleur
    qu'en type 27, morceau par morceau (erreurs 99, 100). **Rivières** : l'eau de CA est à ~5 cm au-dessus du lit (le
    matériau d'eau de la mer s'estompe avec la profondeur) ; `rivieres_wh1.PROFONDEUR`. **Étiquette de colonie** :
    `campaign_map_settlements.citybar_height_offset` (0 partout chez CA) ; relevée à 3 pour le Chêne des Âges, dont
    l'arbre de WH3 cachait le nom (`etiquette_chene.py`).
    **[Remplacé par l'erreur 222 : 13 colonies reprises de WH1, le Chêne à 7 (`etiquettes_colonies.py`, valeurs aussi dans `map_spec.json`) ; `etiquette_chene.py` ne sert plus.]** [25.09.2026, ménage]
104. **La côte de WH1** : ses plages (`sea_coast`, 95 poses de 2 × 2 cases, sol presque plat : y local de −10 à 0) et ses
    tuiles de mer sont fondues dans ses maillages de terre et de mer (0 % de leur emprise hors de ces maillages). Sa côte
    est donc la frontière des deux maillages, au pixel (bords de case et diagonales des tuiles `*_tri`) : une berge raide
    de la terre (≥ 0) au fond (−0,1 à −0,5). Par-dessus, 233 falaises sculptées `cliff_custom` (repère des falaises
    intérieures ; face jusqu'à −1,1 sous le sol). Sous l'eau, WH1 garde son `global_blend` (`grass_a2` à 99 %). `cliff_base`
    (5 072 poses) : sol plat drapé sur le relief de base + 0,2546, hors des maillages. Une mer d'hex et les tuiles de côte
    de WH3 font des marches et des carrés : `terrain_wh1_vers_terry.COTE_WH1` (erreur 102).
    **[Lecture complétée le 24-25.09 (erreur 223) : la donnée est la même que chez WH1, c'est le rendu qui diffère ; voir n° 145.]** [25.09.2026, ménage]
105. **Des objets de WH1 flottent** : 961 de ses 45 354 objets sont de 0,03 à 0,3 au-dessus de ses maillages de sol, tous en
    `BHM_CLASSIC` (aucun ancrage au sol à l'exécution) : assemblages de décor recopiés sur un sol inégal. Pour ne rien
    faire voler sans s'écarter de WH1 : les descendre juste au contact (`props_wh1_vers_layers.CONTACT_SOL`). Les
    « prefab_as_mesh » de WH1 centrent chaque morceau sur sa propre boîte (`sommets_rmv2`, erreur 101).
106. **Scripts et contenu payant de WH3** (session « IA et modding 3D », 23.09.2026) : le verrou d'un DLC =
    `ownership_products` -> `ownership_content_pack_required_products` / `_requirements` -> `ownership_content_packs`,
    avec des jonctions par faction, sous-type, bataille, bâtiment et zone jouable
    (`campaign_map_playable_area_ownership_content_pack_junctions` verrouille la campagne à l'écran de sélection ; mise
    dans notre pack, le jeu se fermait au démarrage, erreur 107 ; hypothèse non prouvée de la session « IA et modding
    3D » : notre zone y avait deux paquets, `wh3_base_game` et `wh1_wood_elves`, quand CA n'en donne jamais qu'un par
    zone jouable ni par bataille) ; en
    script, `cm:is_dlc_flag_enabled(produit, faction)`. Une erreur Lua dans un rappel du premier tick saute tous les
    suivants (mods et déblocage de l'interface compris) : chaque démarrage sous `pcall`. L'ambre ne vient que des
    incidents des Chemins-racines. `script/startpos.lua` existe dans `data_script.pack`. `cm:get_campaign_name()` rend
    le nom du dossier, `campaign_name_key()` la clé de base. Les conseils de CA connaissent `wh_dlc05_wood_elves` et
    `wh_dlc05_oak_of_ages` (ceux du Chêne sont dans un bloc commenté de `wh_campaign_interventions.lua`, l. 6342-6663).
    Syntaxe : `02-scripts\verifier_lua.py` (Lua 5.1 du kit, `luaL_loadbuffer`), appelé par `build_pack.py`.
107. **`mission_text` est une table du kit seulement** (session « IA et modding 3D », 23.09.2026) : aucun
    `db/mission_text_tables` dans les packs du jeu ; ses textes vivent dans `text/db/mission_text__.loc` (il contient
    `ie_attain_faction_victory`). Un objectif scripté de victoire (`override_text` = `mission_text_text_<clé>`) n'a
    donc besoin que de la clé de texte, sans ligne de base (`injecter_textes.TEXTES_PROPRES`).
108. **Les zones d'éclairage que CA livre** ne sont pas celles du projet du kit : la collection compilée des Empires
    (`terrain/campaigns/wh3_main_combi_map_1/environment_collection.xml` des packs) a ses zones régionales en
    cylindres infinis (Bretonnie × 4, rayons 30 à 60, fondu de 10 à 15 unités ; Badlands, Cathay...), là où le projet
    du kit n'a qu'une sphère. Les `.environment` du kit, eux, sont identiques à ceux du jeu. Un cylindre ne dépend que
    de la position de la caméra au sol : pas de saut au zoom (`eclairage_wh1.ZONES_CYLINDRES`).
    **[Un cylindre joue à toute hauteur de caméra (erreur 109) ; une zone se fait à la manière de CA : n° 144.]** [25.09.2026, ménage]
109. **Shaders de WH1 disparus de WH3** : `lava_flowing_01` (lave de campagne) et `wh_waterfall_01` (cascade). CA a
    refait la lave (mêmes noms de modèles, shader `rigid_lava`) et converti le matériau de cascade (shader
    `rigid_waterfall_simple`, emplacements `s_X` -> `t_xml_X` version 2, masque `_diffuse` -> `_base_colour`).
    `fichiers_wh1.Relocateur` prend la version de CA d'un objet dont le shader manque, ou convertit le matériau.
    Six effets de campagne de WH1 (herbe, ombres, nuages, rais de lumière, particules, tempête de neige) : leurs
    ÉMETTEURS sont toujours dans les bibliothèques de WH3 (même `id`, même bibliothèque, retouchés par CA : émissif et
    mélange additif très baissés) ; seuls manquent les six fichiers de haut niveau `vfx/<effet>.xml` (correction du
    23.09.2026, erreur 111). Ces fichiers sont en UTF-16 : chercher `id="grass"` encodé en UTF-16 LE.
110. **Les voix de l'histoire de WH1 sont dans WH3, en anglais et en français** (session « IA et modding 3D »,
    23.09.2026) : les 43 répliques `dlc05.mini.story` (Orion et Durthu 001 à 021, `all.001`) ont un évènement
    `Play_dlc05_mini_story_<qui>_<nnn>_1` dans `campaign_advice__core.bnk` (`audio_en_bnk.pack`, `audio_fr_bnk.pack`),
    chacun un son en flux dont le `.wem` est dans `audio_en.pack` et `audio_fr.pack` (43 sur 43 dans chaque langue).
    Preuve : chaîne Wwise évènement -> action -> son -> média (FNV-1 du nom en minuscules, sections HIRC des banques).
111. **Scènes Cindy** (même session) : WH3 livre ses scènes et caméras en v22 (20 fichiers, une bataille de quête de
    WH2), v23, v26 et v27 ; celles de WH1 sont en v20 (fin) et v21 (intros). Scène : même structure de la v20 à la v22.
    Caméra v21 -> v22 : `NODE DOF_focus` devient `VARIANCE DOF_focus` (Variable + Variance) ; v20 -> v22 : yaw, pitch et
    roll sous `NODE rotation`, les trois vitesses sous `NODE time speed multipliers`. Outil :
    `02-scripts\cindy_wh1_vers_wh3.py <dossier> [--apply]` (relit et réécrit chaque fichier à l'identique avant de
    convertir). WH3 lit en campagne des `.CindyScene` nues, avec `ENVIRONMENT data=""` comme celles du prologue.
112. **Objets de WH1 à l'aspect du sol** : ses 82 collines modelées (`wef_climate_hill_01` à `_04`, `climate_hill`)
    sont au matériau 86 avec des textures factices (`test_gray`, `flatnormal`, `test_black`, `test_gloss_map`) ; WH1 les
    dessinait avec la texture du sol. Le matériau 86 existe dans WH3 (262 modèles de campagne de CA), mais avec de vraies
    textures. Les fondre dans le relief : `props_wh1_vers_layers.collines_de_relief` (erreur 105).
113. **Rendu des modèles v7 de WH1 dans WH3** : sans `_base_colour` à côté du `_diffuse` cité, le moteur passe par un
    chemin de compatibilité ; il convient aux matériaux mats, pas aux très spéculaires (glace de WH1 : obsidienne). Recette
    de CA pour convertir un jeu de WH1 : `_base_colour` = couleur, `_material_map` R = spéculaire, G = 255 − brillance,
    B = 0, A = 255 (mesuré sur `wef_ice_shard` : 173 et 98,6 pour 165 et 156) (erreur 106).
114. **Les routes de WH1 ne sont pas dans son mélange global** : sous ses 2 023 tuiles de route, `global_blend.dds` porte
    surtout l'herbe (indice 2) ; chaque tuile (`terrain/tiles/campaign/roads/...`) a son `blend0.dds`, son `normal.dds`
    et un sol plat. Même chose pour ses plages (`sea_coast`) et embouchures. `blend0.dds` : DXT5 de (W + 2) × 32 par
    (H + 2) × 32 px (32 px par case, marge d'une case), ligne 0 au sud ; R, G, B, A = poids (somme 255) des
    emplacements 0 à 3 de la fiche `terrain/tiles/campaign/_tile_database/tiles/<famille>_<tuile>.bin` ; rotation :
    règle des rivières (routes 96,5 %, plages 100 %). Textures : routes `sand_a0` / `sand_a1` (bandes de 0,03 à 0,08
    unité, moins d'un pixel de notre mélange), plages `mud_a0` dans les deux emplacements, tuiles de mer `mud_a0`
    seul, lits de rivière `sand_a0` (1 362 poses sur 1 399). Fond de mer, plages et lits sont repris depuis le
    23.09.2026 (`textures_tuiles_wh1.corriger`, appelé par `textures_sol_wh1.appliquer` ; `--apply --refaire` refait le
    mélange depuis la sortie de BOB sauvegardée) ; les routes restent celles de WH3.
115. **Cartes de captage d'une campagne** (choix de la carte de bataille ou de siège selon le lieu) : trois calques
    RGB `blm_catchment_override.png`, `_settlement_standard.png`, `_settlement_unfortified.png` dans le dossier de
    bataille du projet (`raw_data\terrain\battles\<carte>\`), à la taille de sa carte de tuiles (2 × la grille des hex,
    + 1 ligne : 800 × 881 chez nous, 1600 × 1201 au prologue), couleurs = zones de `battle_catchment_override_areas`
    (noir = `Gatekeeper`). La compilation de bataille de BOB crée alors l'action « Battle Catchment AGF » et écrit
    `blm_catchment_override*.compressed_map` (FASTBIN0 v3, largeur et hauteur en u32 aux octets 10 et 14) ; motifs
    `blm_catchment_override%s%s.png` / `.compressed_map` de `empireutility.modder.x64.dll`, garde « Catchment
    override layer '%s' dimensions do not match layer '%s' » de `bob_terrain`. Les correspondances vont dans
    `battle_catchment_override_battle_mappings`.
116. **Une table de liens de CA garde ses lignes des Empires** : le moteur résout certaines clés de base en objets de
    campagne (indice 16 bits à +0xB8 de l'enregistrement) ; une clé qui renvoie à une région absente de la carte donne
    un objet nul et un plantage (infobulle des bosquets, erreur 110). Tables de liens des bosquets :
    `pooled_resource_to_region_junctions`, `rituals_to_regions` (10 lignes des Empires, un seul fichier `data__`).
117. **Une campagne scriptée a besoin d'un startpos généré APRÈS ses scripts** (session « IA et modding 3D »,
    23.09.2026) : `cm:is_new_game()` vaut « `__save_counter` == 1 » (`lib_campaign_manager.lua`) ; le compteur n'est
    écrit dans le startpos que si les scripts de la campagne tournent pendant sa génération (leur `SavingGame` le passe
    de 0 à 1). Startpos plus ancien que les scripts : compteur à 0, chaque nouvelle partie est prise pour une sauvegarde
    (ni intro, ni « Comment jouer », ni missions, ni rappels `add_first_tick_callback_new` ; `setup_wh_campaign` écrit
    « reconstructing markers and listeners from saved data »). Contrôle : `__save_counter` = 1 dans le startpos, et le
    script_log de la génération sans erreur de nos scripts (s'ils plantent pendant la génération, le compteur reste à 0).
118. **`height` et `sea_height` d'une campagne** (mesuré aux Empires, 23.09.2026) : sur la mer, `height` vaut 0,000 en
    médiane (p5 −0,06, p95 0,47) : c'est la surface de l'eau ; `sea_height` est le fond (−0,9 près des côtes, jusqu'à
    −109 au large) ; sous la terre, `sea_height` reste au moins 1,025 plus bas que `height`. Les mêmes valeurs dans les
    deux cartes font une eau de profondeur nulle, que le jeu ne dessine pas (mer, rivières et lacs), alors que Terry la
    montre (erreur 113).
    **[Corrigé par l'erreur 155 (23.09.2026) : voir n° 137 (le niveau de l'eau est 0 ; height n'est pas la surface sur la mer jouable).]** [25.09.2026, ménage]
119. **Textures du sol en jeu** : le jeu montre, pour chaque groupe de `texture_arrays.xml`, la texture de CA de ce
    groupe, quel que soit le chemin écrit dans la liste compilée de la carte (sable tropical et herbe fleurie de CA à la
    place des textures de WH1 écrites sur leurs groupes, 23.09.2026, erreur 114). Le mélange (`global_blend.dds`) choisit
    le groupe par pixel ; pour approcher un sol, prendre le groupe de CA le plus proche (`textures_sol_wh1.EQUIVALENTS_CA`).
120. **Masques de culture des décors** (`culture_mask` des entités, projet des Empires) : 496 705 masques, 179 valeurs ;
    vides 127 244 ; Nurgle 59 915, vampires 55 016, skavens 49 069, Tzeentch 45 478, Khorne 44 319, Slaanesh 37 785,
    Chaos et Hommes-bêtes 32 478 : les décors de corruption de CA sont masqués par culture. Jetons employés : 25 cultures,
    dont `wh2_main_rogue` ; aucun jeton « sans propriétaire ».
121. **Arbres de campagne** : le modèle suit la culture du propriétaire de la région (`campaign_tree_type_cultures` :
    `wh_dlc05_wef_wood_elves` -> WOODELVES...) ; sans variante pour cette culture, ou sans propriétaire, le jeu prend
    BASE (pour les arbres de WH1 : pins et feuillus de l'Empire ; constaté sur une capture de Charles autour de la ruine
    de Tal Eth Ayr, déduction à confirmer en jeu après `arbres_wh1.PREFIXE_AL`).
122. **Bascule des décors et arbres de corruption** (session « IA et modding 3D », 23.09.2026, données de CA, pas encore
    vu en jeu) : un masque de culture est satisfait par la culture du propriétaire OU par la corruption dominante
    (`corruption_types.prefab_type` : CHAOS, VAMPIRE, KHORNE...) au-delà du seuil `campaign_variables.
    min_visual_corruption_prop_value` = 50 (« intensité 0-255 présente dans la texture ») ; `max_visual_corruption_value`
    = 100. Les Hommes-bêtes répandent la corruption du Chaos (jeton `wh_main_chs_chaos` ; CA masque ses décors
    « bst, chs, dae, nor »). Le `corruption_mask.dds` des Empires est peint (moyenne 52, médiane 68 à 71 sous les décors
    de corruption) ; le nôtre est uniforme (21 à l'écriture de cette entrée, **128 au 23.09.2026 après-midi**, relevé de la
    session « IA et modding 3D » ; aux Empires il est peint de 0 à 204) : uniforme, le voile de corruption s'étendrait
    partout ou nulle part au lieu de suivre les provinces (non vérifié ; `saison_essai_corruption.lua` n'a jamais
    tourné). À établir en jeu (corruption du Chaos forcée à 100 dans une province,
    fin de tour), puis peindre le masque haut là où WH1 a ses décors de corruption et de dévastation.
123. **Matériaux XML de WH1 dans WH3** (23.09.2026, erreur 120) : WH3 a gardé les noms de shaders de WH1
    (`rigid_building_emissive`, `rigid_vertexpush`, `parallax_02`), mais ils ne lisent plus que les emplacements de
    version 2 : `<slot version="2">t_xml_base_colour</slot>`, `t_xml_material_map`, `t_xml_normal`, `t_xml_emissive`,
    `t_xml_emissive_texture`, `t_xml_diffuse_secondary`, `t_xml_parallax`, plus `t_xml_dither`
    (`commontextures/dither.dds`). Un matériau de WH1 (`<slot>s_diffuse</slot>`...) s'affiche sans aucune texture. CA a
    converti les siens : `s_specular` + `s_gloss` fondus en une `_material_map`, paramètres retouchés (pierre de lien
    120 -> 1,13 ; lanterne 2 500 -> 1,47 ; `emissive_scale` -> `emissive_tiling`, `emissive_direction` et
    `use_ws_position_as_uv` = 1 ajoutés) : la loi d'émission des matériaux du Chêne (`fichiers_wh1.emission_wh3`) ne vaut
    pas pour ce shader.
124. **Le matériau de la mer d'une campagne** (session « IA et modding 3D », 23.09.2026) : il vient de la base de
    variantes d'assets (`warscape_asset_variation_db/terrain_textures_campaign.assetdb`, clé `water_plane_material` par
    `campaign_texture_terrain/campaigns/<carte>`), pas des fichiers compilés par BOB : le `water_plane_material` du
    `.terry` ne va que dans le XML du kit. Empires et prologue y pointent un bouchon (`campaign_water_plane_default`,
    shader `debug_simple`, aussi le repli de l'exécutable) : leur mer se dessine par le relief, `lf_sea_colour` et les
    réglages `sea_*` des `.environment`. Le matériau d'eau cité par les objets (rivières, lacs de `global_props.bin`) est
    propre à chaque carte : celui des Empires lit `Sea/combi_A_mask.dds` (alpha = leur mer, bleu = leurs rivières, u =
    x / largeur du monde, v = z / profondeur, ligne 0 au nord) ; le nôtre (`eau_carte.materiau()`) lit nos masques
    (`masques_eau_carte.py`).
125. **Le réseau de rivières de WH1 dans ses tuiles** (23.09.2026, erreur 122) : le ruban des `blend0.dds` de chaque
    tuile s'estompe à son bord ; lu à 4 px par case, le réseau se coupe à presque chaque jonction (1 516 morceaux au
    seuil 0,5 ; écart médian 0,3 unité, 90 % sous 1 unité, mesure de la session « IA et modding 3D ») et les ruisseaux,
    plus fins qu'un pixel, n'y dépassent pas 0,2 à 0,4. Les rubans d'eau des tuiles (matériau 90) sont un pixel au nord
    de ce ruban (recouvrement meilleur de 0,26 à 0,33 une fois décalés d'une ligne vers le sud) et portent des « poils »
    perpendiculaires. Les deux ensemble, fermés par un disque de 0,6 unité, redonnent un réseau continu.
126. **Écran de sélection : seigneurs, pointeur de la carte** (23.09.2026, erreur 123). Le startpos porte
    `CAMPAIGN_PREOPEN_MAP_INFO` : `CAMPAIGN_PLAYERS_SETUP`, `FACTION_INFOS` (par faction : clé, nom du chef, **position en
    fraction de la carte, deux flottants** = (case x + 0,68) / largeur, (case y − 0,15) / hauteur ; puis
    `STARTING_GENERAL_OPTION_BLOCK`, une option par fiche de `start_pos_starting_general_options`),
    `REGION_OWNERSHIPS_BY_THEATRE`. Un chef en garnison (`start_pos_character_to_settlements`, startx / starty = 0) y est
    gravé en (0 ; 0). `frontend_faction_leaders.override_force_location_x/y` (fractions ; −1 = rien) n'est pas gravé par la
    génération : CA ne l'emploie que pour Eltharion (0,398 ; 0,420). Chez CA, un chef en garnison peut aussi avoir une
    position (Boris Todbringer à Middenheim, campagne du Chaos : (551, 581)).
127. **Le courant de l'eau de campagne** (23.09.2026, erreur 125 ; mesure de la session « IA et modding 3D » sur
    `Sea/combi_combined_flow_mask.dds` des Empires, 57 711 px de rivières au sens connu) : R − 128 = composante EST,
    G − 128 = composante NORD (ligne 0 au nord), vecteur vers l'AVAL, norme ~61 dans le lit (~73 dans les 4 dernières
    unités avant la mer), décroissant à zéro ~7 px hors du lit ; mer ~60, vers l'est ; B et A = deux bruits de phase
    lisses, sans lien avec l'eau. Masque neutre (128, 128) = eau immobile. Le sens ne se lit pas dans les tuiles de
    WH1 : la coordonnée « le long » de leurs rubans dépend de l'orientation de chaque tuile (52 % des pixels vers l'aval) ;
    il vient du réseau (distance le long de l'eau jusqu'à l'embouchure : `rivieres_wh1.flux_reseau`).
128. **Échap au menu principal** (session « IA et modding 3D », 23.09.2026) : c'est le raccourci `escape_menu`
    (`text/default_keys.xml`, seul fichier de touches du jeu) ; il arrive aux scripts par `ShortcutPressed` /
    `ShortcutTriggered` (`context.string`). `lib_movie_overlay` ne sait prendre Échap qu'en campagne et en bataille (au
    menu : avertissement « skippable frontend movie ... unsupported ») ; un calque peut le prendre par
    `uic:StealShortcutKey(true, "escape_menu")`. Espace n'est lié à aucun raccourci hors bataille, et il n'y a pas
    d'évènement de touche générique au menu.
129. **Convertir un jeu de textures de WH1 (spéculaire / brillance) au rendu de WH3** (relevé sur les conversions de CA
    des mêmes objets, 23.09.2026, erreur 126) : `_material_map` 512 × 512, BC3 chez CA, **point par point** : R = métal,
    G = 255 − brillance de WH1 (exact pour la tumeur, les toiles, la glace, l'arche), B 0, A 255. R = 0 pour la pierre,
    le bois, la toile (maison, pierre de lien, pierres dressées) ; R fort pour ce qui est spéculaire ET brillant (or
    147 / 178 -> 216, fer 125 / 107 -> 216, gemmes 117 / 230 -> 158, armes 100 / 99 -> 139, glace 165 / 156 -> 173).
    `_base_colour` : la diffuse de WH1 pour un non-métal, **le spéculaire de WH1 pour un métal** (or : 157 / 122 / 69 chez
    CA, spéculaire 147 / 115 / 65, diffuse 58 / 43 / 20). 899 modèles de campagne de CA sont en RMV2 v7, matériau 68,
    types 0 / 1 / 3 / 11 / 12, et n'ont que le `_base_colour` à côté du `_diffuse` cité (relevé de la session d'audit) ;
    `test_mask.dds` (type 3) manque aussi chez CA : sans effet.
130. **Pack des tables de départ (`zz_startpos_db.pack`) et textes** (erreur 127) : dans `start_pos_regions`,
    `rebel_faction_name` et `long_description` sont vides sur toutes les lignes ; un texte non vide (« PLACEHOLDER » du
    kit) fait planter la création du monde à la génération, sans vidage ni rapport (`logs\no_clean_exit`, arrêt après
    le chargement des scripts). La génération réussie enregistre le monde (`SavingGame`) 1,5 s après « Loading Mods » :
    un journal qui s'arrête à « Loading Mods » désigne les tables de départ.
131. **Parties automatiques (`02-scripts\essai_tours_auto.py`, 23.09.2026)** : pack d'essai séparé
    `zz_saison_essai_auto.pack` (recréé, retiré à la fin) ; lancement PAR L'INTERFACE (`frontend.start_campaign` referme
    notre campagne, erreur 128) : `main > button_campaign`, `main > button_start_campaign_new`, puis soit la liste des
    campagnes (`campaign_select_new > CcoCampaignMapPlayableAreaRecord1758400002 > button_campaign_entry`), soit
    directement la dernière choisie ; bouton du seigneur `lord_select_list > list_box > * > lord_button` (propriété
    `lord_key` = identifiant `start_pos_characters`, la liste se remplit en 20 à 45 s) ; `campaign_select_new >
    button_start_parent > button_start_campaign` (propriété `campaign_key`). En campagne : `custom_loading_screen >
    bottom_parent > button_continue`, fin de tour `hud_campaign > faction_buttons_docker > button_end_turn`, APRÈS avoir
    passé une à une les notifications `end_turn_docker > notification_frame > button_skip` (erreur 137 ; en mode
    `all_players_ai`, seul le tour 1 l'exige, les suivants se jouent seuls). Le
    `script_log` du menu est écrasé si la campagne démarre la même minute (même nom de fichier) : journal propre
    `saison_essai_menu.txt` dans le dossier du jeu. Les clics (même simulés) sont journalisés en campagne avec leur chemin
    (`path from root`). Mode joueur (`--sans-ia`) : la faction du joueur ne fait que finir ses tours ; `all_players_ai;`
    dans `user.script.txt` fait jouer l'IA pour elle.
    **[Le pilote clique jusqu'à 30 notifications par round dans les deux modes : à 3 sous l'IA, le clic de fin de tour n'était plus accepté (erreur 239).]** [25.09.2026, ménage]
132. **La carte de WH1 et la géographie du lore** (erreur 136, session « Extension carte Bretonnie est ») : Athel Loren
    agrandie, bloc nain et orque du nord-est à la place du Reikland ; à 48 villes communes avec l'Atlas of the Old World,
    écart médian 19 hex, 110 à 130 hex pour Karak Ziflin, Karak Tzor, le Poste de la Pierre Noire et le Défilé de la
    Hache. Pour étendre la carte à l'est : topologie du lore, pas de calage.
133. **Objets des tuiles de WH1** (erreur 141, session « Rendu de la carte ») : les tuiles `river_crossing` portent leurs
    ponts dans `bmd_data.bin` (FASTBIN0 v21, enregistrements v11 : chemin, matrice 12 f32, drapeaux, « BHM_TERRAIN ») :
    passerelle `rigidmodels/campaign/resources/jetty`, barrières, roseaux, rochers. Lecture : `ponts_wh1.py`.
    **Correction du n° 101** : la ligne `SST_RIVER` de `bmd_data.bin` se lit en points de 22 octets (x, y, z, largeur,
    puis une constante : 0,7 pour les croisements, 0,5 pour les rivières), pas 44 (vérifié sur 19 croisements et 47 des
    54 tuiles de rivière ; les 44 octets étaient deux points).
134. **Mode `all_players_ai` des essais automatiques** (erreur 143) : `FactionTurnStart` n'arrive aux scripts pour aucune
    faction ; `WorldStartRound`, `FactionBeginTurnPhaseNormal`, les évènements de bataille, de mission et d'interface,
    si. L'IA ne joue pas vraiment la faction locale (ni recrue ni bâtiment) ; aucune mission n'est émise pour une IA
    (`mission_manager:new`, `lib_campaign_mission_manager.lua` l. 135-138). Ce mode teste la stabilité des IA, les
    invasions et les dilemmes ; l'histoire et les mécaniques propres à un seigneur se testent en mode joueur.
    **[Corrigé par l'erreur 230 : `FactionTurnStart` manquait aussi en mode joueur ; cause et remède : n° 148.]** [25.09.2026, ménage]
135. **Plantage `Warhammer3.exe+0x1A3DCFA` = effets recréés de WH1** (erreur 146 ; l'herbe d'abord, puis au moins un
    autre des 6, sans doute le nuage : les 6 sont vides depuis le 23.09.2026, 17 h 40) : l'émetteur `grass` de la bibliothèque
    `wh_main_lib_campaign_enviro2` (référencé par `wh_main_campaign_enviro_grass`, effet de WH1 recréé) fait planter une
    tâche de rendu de WH3 dès qu'une pose est à l'écran. Méthode de diagnostic réutilisable : `essai_tours_auto.py
    --neutre-vfx [dossier]` remplace des fichiers du pack de jeu par ceux d'un dossier de `essai-auto\` dans le seul
    pack d'essai (chargé après) : A/B sans reconstruire le pack ni le terrain.
    **Nuance du 23.09.2026, 19 h 35 : les effets ne sont pas la seule cause.** Les 6 effets étant vides, le plantage revient
    quand plusieurs régions changent de maître au tour 1 : 2 plantages sur 5 essais (drapeau `saison_essai_transfert.txt`,
    `--ajout transfert`), l'un à +0x1A3DCFA, l'autre à une adresse neuve, +0x10CCEFC. Dans les deux cas, un champ attendu
    comme pointeur contient du texte (« wh_dlc05 », « i680 » en UTF-16) : cela évoque un objet libéré puis réutilisé.
    Piste en cours (session « Rendu de la carte ») : la base de tuiles n'a pas les familles `sea_coast`, `cliff_gen`,
    `cliff_gen_ends` ni `roads_light` de CA (voir n° 136).

136. **Diagnostic d'un plantage du jeu sous cdb** (erreur 153) : l'exécutable est protégé (sections `.sbss`, `.xcode`,
    `.shared` ; les RTTI ne se lisent pas sur disque, `lire_dll.py vtable` échoue) : pour nommer un objet, il faut un vidage
    complet (`--vidage-complet`, `/ma`). Dans une commande `sxd -c2`, une lecture mémoire ratée interrompt toute la suite :
    écrire pile et vidage d'abord, chaque lecture risquée sous `.catch { }` (codé dans `essai_tours_auto.commandes_cdb`).
    Un script d'essai qui doit se charger à coup sûr va dans `script\campaign\mod\` du pack d'essai, **sous un nom
    qu'aucun `required.lua` du pack ne charge** : `lib_core.load_mod_script` saute sans le dire un fichier déjà dans
    `package.loaded` (« Failed to load mod », sans « Loading mod file » ni erreur ; 23.09.2026, 21 h 15, essai perdu,
    relevé par la session « IA et modding 3D »). Un `required.lua` du pack d'essai ne remplace pas celui de notre pack
    (19 h 54, essai perdu).

137. **Ce que le moteur lit de la mer** (erreur 155, session « Rendu de la carte ») : le niveau de l'eau est 0
    (matériau d'eau : `sea_height_min` -2, `sea_height_max` 0, comme chez CA) ; l'eau ne se dessine que là où le fond
    (`sea_height`, canal G de `full_height_map.dds`) est sous 0 : il doit l'être partout, même sous la terre (Empires
    -0,91). `tile_mask.dds` : 16 terre, 32 mer (tuiles `sea_coast` et `cliff_gen` comprises), 0 routes, 64 cases noires
    hors carte. Le relief a une passe terre (R) et une passe fond marin (`ps_sea_geom`, G). `tile_list.bin` : noms, puis
    une pose par enregistrement de 21 octets, bornes de hauteur calculées par BOB sur le fond ; contrôle : aucune tuile de
    mer au maxi au-dessus de 0. `terrain_textures_campaign.assetdb` (FASTBIN0, `02-scripts\base_variantes_ca.py`) associe
    chaque groupe de sol à ses fichiers de CA pour toutes les campagnes (d'où l'erreur 114). Contrôle des textures des
    modèles après un pack : `02-scripts\controle_textures_objets.py`.

138. **La surface de la mer = des plans d'eau** (erreurs 163 et 164, session « Rendu de la carte ») : les Empires posent
    de grands `ECPolygonMesh` au matériau d'eau, à y = 0 ; sans eux, aucune eau sur la mer, même avec le fond sous 0.
    BOB écarte un plan dont le **pivot** est hors de la carte (« Failed to find valid quadtree node », entité absente de
    `global_props.bin`) : pivot à l'intérieur. Contrôle : nombre de plans d'eau de `global_props.bin` = nombre des
    calques ; lire `bob_warnings.log` après chaque BOB. Un objet ne doit jamais citer une texture sous `terrain/`
    (règle de `fichiers_wh1.Relocateur` et `montagnes_wh1.TEXTURES_OBJET`, contrôle `controle_textures_objets.py`) :
    piste du plantage de rendu (+0x1A3DCFA / +0x10CCEFC), à confirmer.

139. **Sol et éclairage lointain du terrain** (erreurs 179 et 181) : un groupe de sol n'existe pour le jeu que s'il est
    déclaré dans `warscape_asset_variation_db/terrain_textures_campaign.assetdb` (espaces `campaign_base_colour`,
    `campaign_material`, `campaign_normal`, dans l'ordre de la liste compilée de BOB) ; sinon il prend la dernière
    texture du tableau. Notre copie de la base (440 entrées de CA identiques à l'octet + nos clés `wh1_*` + la clé du plan
    d'eau) est embarquée par l'exception de `build_pack` ; **à refaire après toute mise à jour du jeu**. `lf_normal.dds`
    (éclairage du relief lointain) n'est pas faite par BOB pour une campagne : la recalculer depuis notre relief
    (`lf_normal_depuis_relief.py`) après chaque changement de relief.
140. **Le canal rouge du `_material_map` est du MÉTAL dans WH3** (erreur 202, agent de recherche de la session
    « Rendu de la carte », shader `rigid_default` désassemblé) : y recopier le spéculaire de WH1 transforme un objet
    brillant en métal (couleur propre écrasée, reflets gris-bleu). Glace de WH1 : métal 14, la valeur de la glace de CA
    (`gen_icicle`), et non 165 (`fichiers_wh1.METAL_GLACE`). La glace de WH1 n'est ni transparente ni émissive : c'est un
    fort reflet neutre. À vérifier sur toute autre recette de conversion qui remplit ce canal (gemmes : métal 175).
143. **Écouteurs de script non protégés en jeu publié** (erreur 213) : `core` appelle les écouteurs par
    `event_unprotected_callback` ; une erreur dans l'un annule l'évènement pour tous les autres (CA compris). Tout
    écouteur à nous passe par une fonction commune protégée et journalisée.
142. **Mise à jour du jeu : le kit suit, et efface nos lignes** (erreur 206). Steam met l'Assembly Kit à jour après le
    jeu et réécrit `raw_data\db`. Ordre de reprise : vérifier nos lignes (`grep wh_dlc05_wood_elves campaigns.xml`) ;
    `restaurer_lignes_kit.py` (à blanc puis `--apply`) ; repasser tous les lots dans l'ordre ; comparer les `start_pos_*`
    au `zz_startpos_db.pack` (`synchroniser_pack_startpos.py`) ; schémas de RPFM (`update_schemas`) et cache des
    dépendances (`generate_dependencies_cache`) ; `textures_sol_wh1.py --apply --refaire` ; pack d'essai hors de `data`
    comparé au précédent ; régénérer le startpos.
141. **L'outil d'édition et les séquences d'échappement d'un espace insécable** (erreur 205) : un texte à remplacer qui contient la séquence
    d'échappement écrite en toutes lettres n'est pas trouvé, et le remplacement y met un vrai caractère insécable.
    Viser un morceau voisin, ou retoucher par un script écrit dans un fichier ; relire la ligne après.

---

144. **Zones d'éclairage à la manière de CA** (erreur 251, 25.09.2026) : une teinte non nulle est interpolée à travers
    0/360 dans l'anneau de fondu (−3,5° écrit = 356,5 lu : toutes les teintes défilent) ; les 18 zones de CA aux Empires
    gardent teinte 0, luminosité, contraste, saturation et canaux du global, et se distinguent par la LUT, le brouillard,
    le soleil et l'ambiance. Le calage par canal de luminosité (Winterheart 0,62 / 0,65 / 0,78) faisait le bleu nuit sur
    tout l'écran : CA garde les canaux égaux. `eclairage_wh1.ZONES_FACON_CA`, zones remises une à une (`ZONES_REMISES`).
145. **Côte lisse en jeu** (erreurs 223 et 240) : la donnée de WH1 a le même escalier que la nôtre ; ce qui fait les crans
    de plusieurs cases, c'est une marche d'un pixel simplifiée de loin (LOD de BOB) et le sol des cases de mer pleines
    dessiné près des terres (découpe par `tile_mask` à `g_clip_threshold`, ≥ 0,5 u). Remède : berge en pente d'environ
    1 u, mer pleine au fond sous l'eau à moins de 2 u des terres (`PRES_DES_TERRES_PX = 24`, contrôle « 0 px au-dessus de
    0 »), pas de falaise sur le trait de côte. Distance en croix (`distance_a`) : 24 px en ligne droite, 17 px (1,4 u)
    en diagonale ; le contrôle se fait dans cette métrique (à vol d'oiseau, 8 037 px à 0,02 entre 1,4 et 2 u, déjà
    présents en 13 bis et 14).
146. **Neige en 9.0** (erreur 216) : le matériau de neige des Empires ne cite plus de masque ; le jeu lie lui-même le
    `snow_mask.dds` de la campagne. Ne pas copier un matériau de neige par carte.
147. **Mise à jour du kit et BOB** (erreur 220) : la 9.0 a remplacé `bob_terrain.modder.x64.dll` (code décalé d'environ
    +0xAF10) ; `compiler_terrain_bob.VERSIONS_DLL` est indexée par empreinte : après chaque mise à jour du kit, relever
    les décalages et ajouter l'empreinte avant la première chaîne.
148. **Évènements coupés par un écouteur de CA** (erreurs 213, 230, 231, 252) : `core:event_callback` évalue toutes les
    conditions sans protection en jeu publié ; une condition qui plante annule l'évènement pour tous, sans journal.
    `evt_callback` est une locale de lib_core : notre protection remplace la méthode `core.event_callback`
    (`required.lua`) et nomme le fautif une fois (« ecouteur [clé] en erreur sur <évènement> »). Sur notre carte : trois
    écouteurs de Mère Ostankya et Yuan Bo, retirés par `saison_start.lua`.
149. **Eau blanche des petites rivières** (enquête du rendu, 25.09.2026) : le matériau d'eau règle l'écume et la teinte
    d'après l'épaisseur d'eau vue rapportée à `river_depth_max_point` (0,8 aux Empires) ; nos rivières (1 à 5 cm, comme
    WH1) deviennent blanches de loin. Valeur des cartes du prologue et du Chaos de CA : 0,2
    (`masques_eau_carte.PROFONDEUR_RIVIERES`) ; `sea_depth_max_point` 0,6 et `foam_falloff` 20 pour une côte sombre
    comme WH1. Seconde cause, prouvée par la coque du sol désassemblée : les taches et festons viennent du sol tessellé
    grossièrement de loin (un sommet tous les 14 px au plus), qui comble un lit de 0,17 u (49 % de l'eau visible à 7 px) ;
    remède : berges basses (`rivieres_wh1.BERGES_BASSES`) et lit sombre (`terrain_wh1_vers_terry.COULEUR_SOUS_RIVIERES`).
    À juger en jeu (pack de 04 h 06, chaîne 15).
150. **Plantage de rendu `Warhammer3.exe+0x1AC7576` (9.0)** (erreur 265) : le jeu relit un objet `TerrainCustomTile`
    déjà libéré (`rax = 0x20`, lecture de 0x24), au premier tour ou pendant que la caméra bouge ; l'objet est une de nos
    falaises de WH1 (`montagnes/cliff_inland_custom_passable`). Apparu après la chaîne 14 (objets reposés sur les
    montagnes) ; cause en cours d'essai (chaîne 16 sans ces règles). La piste mémoire est RÉFUTÉE (plantage sur un PC
    redémarré). À part : `rpfm_server` garde la mémoire de chaque pack (69,7 Go après une nuit) :
    `build_pack.garde_memoire_rpfm` refuse au-delà de 8 Go.
    **Bandeaux des colonies** (même nuit) : leur hauteur est globale (`_kv_ui_tweakers.campaign_citybar_height`) ;
    `campaign_map_settlements.citybar_height_offset` vaut 0 chez CA partout ; un modèle haut se règle par
    `settlement_nameplate_offsets_per_primary_building_levels` (décalage par niveau du bâtiment principal ;
    `bandeaux_niveaux.py`).
151. **Zones de captage `*_chokepoint` = batailles de passage** (erreur 271 ; audit des cartes de bataille du 25.09.2026,
    `05-journal\2026-09-25-revue-beta\revue-cartes-de-bataille.md`) : les groupes de cartes `*_chokepoint`
    (`wh3_dlc20_macro_brt_hills_chokepoint`, `wh3_main_macro_old_world_mountains_dwf_chokepoint`) portent un
    `battle_type_override` qui change `land_normal` en `land_bridge` : toute bataille rangée dans la zone devient une
    bataille de passage, sur 2 cartes. Aux Empires, ces zones ne couvrent que des cols ; la montagne ordinaire est
    `wh3_main_macro_old_world_mountains` (17 variantes), les collines bretonnes `wh3_main_macro_brt_grasslands`.
    Autre relevé : WH3 n'a ni carte de bataille de neige ni de marais pour ces biomes ; une seule carte de siège par
    culture, comme chez CA.

## 16. Pour une IA qui reprend ce dossier

**L'état du projet, les sessions en cours et les recettes sont dans `CLAUDE.md`** (réécrit le 23.09.2026). Cette
section ne garde que la vérification de l'environnement. L'ancienne section 16 (état au 20.09.2026, blocage du
startpos, ordre des phases) est conservée dans `05-journal\historique-documents\GUIDE-2026-09-23-1500.md`.

```powershell
$exe = "C:\TotalWar-CampaignMap\01-outils\CampaignMapToolkit\CAIME\bin\Debug\CAIME.exe"
& $exe --help                     # 8 verbes attendus
& $exe config --show              # Warhammer3 doit pointer sur l'assembly_kit
powershell -ExecutionPolicy Bypass -File "C:\TotalWar-CampaignMap\02-scripts\lancer-outils.ps1" -Outil rpfm-server
# puis : claude mcp add --transport http rpfm http://127.0.0.1:45127/mcp   (ou l'équivalent du client)
```

Conventions : un projet = `04-projets\<nom>\` (`notes.md` = la fiche) ; références dans `03-references\<nom>\` ;
tout ce qui est daté dans `05-journal\<date>-<sujet>\` ; ce qui ne sert plus dans `99-archives\` (rangé, jamais
supprimé) ; fork : jamais `git add -A`, commits en anglais.

