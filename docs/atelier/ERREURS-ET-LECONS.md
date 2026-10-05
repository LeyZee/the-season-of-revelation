# Erreurs commises et leçons — journal de l'atelier

Ce fichier existe parce que Charles l'a demandé le 20.09.2026 : **chaque erreur faite pendant le
travail est consignée ici avec la règle qui l'évite**. Une IA qui reprend l'atelier lit le sommaire « Règles vivantes » ci-dessous, puis
les entrées des deux derniers jours, et y ajoute ses propres erreurs le jour même. Le GUIDE.md § 15 résume les
pièges de l'outillage ; ici, c'est le journal complet, daté, avec le symptôme, la cause et la règle.

Format d'une entrée : **quoi** (ce que j'ai fait) → **symptôme** → **cause** → **règle**.

Deux étiquettes (règle fixée le 20.09.2026 avec Charles, détail dans `README.md` § 5) :
- `[évitable]` : quelqu'un l'avait déjà écrit quelque part. L'entrée donne la règle, et dit si
  elle est codée (script, verbe, garde).
- `[découverte]` : personne ne pouvait le savoir. L'entrée donne le fait et la preuve, et le fait
  est reporté dans `GUIDE.md` (§ 15 ou la section concernée) pour devenir évitable.

Dans la session ci-dessous, les sections A, B et C sont des `[évitable]` ; la section D regroupe
les `[découverte]`.

---
## Règles vivantes (sommaire au 04.10.2026, grand nettoyage ; le détail est dans l'entrée citée)

À lire en premier, puis les entrées des deux derniers jours ; le reste à la demande (recherche par numéro ou par mot ;
les étiquettes s'écrivent aussi sans accent : chercher `\[(é|e)vitable\]`). Les numéros 6 et 29 sont en double (citer
A6 / B6 et 29-undo / 29-attribution). Une règle remplacée porte « [Remplacée le … par n° …] » dans son entrée. L'ancien
sommaire (25.09.2026) est rangé en bas du fichier. Source : `05-journal\2026-10-04-grand-nettoyage\audit-erreurs.md` § 6.
Les règles sont numérotées R1 à R40 (pour ne pas les confondre avec les entrées) ; les nombres entre parenthèses sont
des numéros d'entrées.

**Déclarer (base, clés)**
R1. Avant toute déclaration : relire les décisions de Charles (`CLAUDE.md` § 2) ; `saison_` pour ce que nous créons,
   `wh_dlc05_` pour ce qui vient de WH1 ; retirer des lignes par un outil ciblé, jamais `declare_map --undo` (29, 272).
R2. Une ligne de base part d'un gabarit qui marche : la ligne de WH1 pour le contenu ; la ligne de la Saison, champ par
   champ, pour une campagne ou une zone jouable neuve (`campaigns.mask` vide, aperçu au rapport du monde, hauteur 600) ;
   tout écart se justifie (48, 53, 331, 332).
R3. Jamais une de nos régions dans un groupe, une liste ou une table de liens de CA ; jamais remplacer une table de CA ;
   un pack d'une autre carte ne garde que les lignes dont les régions sont sur sa carte (110, 154, 156, 330 ;
   `verifier_groupes.py`).
R4. Aucune `*_ownership_content_pack_junctions` pour une clé à nous : le jeu se ferme sans rien dire (107, 268, 329).
R5. Un nom propre ou de mécanique se vérifie dans le `.loc` français du jeu, et de nouveau après une mise à jour (139,
   191, 207, 256).
R6. Sauvegarde dans `db-backups\` avant d'écrire dans `raw_data\db` ; préavis : l'heure de `preavis.py heure` telle
   quelle, `attendre` en arrière-plan, relire les messages, puis écrire (145, 215, 221).

**CAIME**
R7. Avant chaque étape, relire la section du guide de l'Atlas et la doc officielle, et la suivre à la lettre ;
   `validate --all` avant tout export, Error ET Warning des villes corrigés (seule exception : l'étendue d'une ville en
   col) (335 ; remplace 38).
R8. Ville = disque de 19 hex ; port = 16 hex principaux de terre + 3 hex de Port consécutifs de l'anneau 2 (chez CA :
   deux en mer, un sur la plage) ; un port de WH1 garde 16 + 3 ; ses cases de port restent dans leur région de mer
   (313, 334, 337). La Saison garde ses ports [mer, mer, mer], validés en jeu (décision de Charles, 04.10.2026).
R9. Le trio (modèle primary, `primary_building`, `port_building`) existe tel quel chez CA pour la sous-culture du
   maître ; une région qui change de maître prend modèles ET bâtiments ; une faction en horde chez CA n'a pas de
   colonie (333, 334, 335).
R10. Régions posées par script : `generate-region-borders` avant validate et process (336).
R11. Routes en fils, peu de carrefours : contrôler les degrés du graphe, borner `process` dans le temps ; un miroir de
    carte se fait dans le repère des hex (338).
R12. Toute retouche : nombre de cases franchissables comparé avant / après ; en agrandissant, mer seule contrôlée port
    par port ; rivières et côtes avant les villes (314, 316, 328).
R13. Couches : `Impassable` 1 = franchissable ; ne réimporter que les couches changées (Roads, Rivers, Region Borders
    perdent leurs directions) ; après un import, recopier les `.hex_layer` du projet et tout réexporter (40, 46, 174 ;
    découverte du 20.09).

**Terry et BOB**
R14. `tile_map.png` vient de l'export CAIME (Baseline Tilemap), jamais peinte ni retouchée ; 0 « Failed to find tile »
    (63 et § C annotés le 27.09). Exception décidée par Charles le 04.10.2026 : la Saison garde sa `tile_map.png` peinte
    par script (côtes validées en jeu) ; export CAIME pour toute carte neuve (85, 86, 87).
R15. Positions des entités en espace des hex ; un raster se lit à z × √3/2 ; le sens de rangement de chaque fichier
    compilé se prouve un par un (89, 253 ; découverte du 21.09).
R16. Eau : plans d'eau `ECPolygonMesh` (pivot dans la carte) ; `sea_height` sous 0 là où il y a de la mer, sans effet
    sous la terre ; côte en pente douce, ni marche ni falaise sur le trait ; mer pleine sous l'eau à moins de 2 u des
    terres (155, 163, 164, 223, 240).
R17. Après toute mise à jour du kit : empreinte de `bob_terrain` relevée et `compiler_terrain_bob.py --carte` à blanc ;
    liste d'arbres de BOB jamais prise telle quelle sur une carte plus haute que large (220, 311, 325). BOB sous `cdb`
    est la méthode assumée de l'atelier (décision de Charles, 04.10.2026).
R18. Modèles de WH1 : convertir selon le shader de WH3 qui les lit, puis contrôler sur les conversions de CA des MÊMES
    objets ; corriger tous les fichiers que la règle touche ; jamais un fichier à nous à un chemin que CA cite (un ajout
    à une base de CA passe par un catalogue à nous, 341) ; montagnes en objets au matériau 68 (117, 126, 202, 254, 327 ;
    pas de pack de la Saison avant la décision de Charles sur ces montagnes).
R19. Un effet ou un fichier de rendu converti de WH1 ne s'embarque qu'après un essai en jeu, caméra dessus ; un réglage
    qui porte un contrôle validé ne change qu'en annonçant le contrôle qui tombe (146, 240).
R20. Éclairage : zones à la manière de CA (LUT, brouillard, soleil, ambiance), une à la fois, montrées en image puis
    essayées en jeu ; captures faites par Charles (109, 251).

**Tables et scripts**
R21. Une table neuve a son entrée dans `TABLES_LOT*` et figure au journal du pack avec son nombre de lignes ; les lots
    restent rejouables (idempotents) (131, 145, 206).
R22. Débuts de tour sur `FactionBeginTurnPhaseNormal` ; protection centrale de `core.event_callback` ; à chaque montée de
    version, lire les écouteurs nommés en erreur et retirer par leur nom ceux sans objet (230, 231, 252).
R23. Lua : jamais `find`/`match` avec le 4e argument `true` (codé) ; une erreur de script de CA vue en essai est imputée
    au mod tant que l'appel fautif n'est pas trouvé dans nos scripts (287, 291, 292).

**Startpos**
R24. Tables `start_pos_*` dans le pack de génération seulement ; `startpos_manuel.py … --sans-working-dir --ai-map-data`,
    `data\campaign_maps\<carte>\` présent ; `__save_counter` = 1 ; copie dans le projet, puis pack reconstruit ;
    `user.script.txt` remis (39, 58, 59, 112, 331).
R25. Après une restauration du kit : chaque lot compté contre sa source ; chaque table `start_pos` comparée au pack de
    départ (0 ligne du pack absente du kit) ; retouches hors lots repassées (302, 305, 326).

**Pack et mises à jour**
R26. Avant le pack : `verifier_textes`, `verifier_groupes`, `rpfm_server` sous 8 Go de mémoire PRIVÉE ; après : essai de
    démarrage avant d'annoncer ou de dire « construit » (107, 265, 275, 330).
R27. Mise à jour du jeu ou du kit : photo avant ; après, compter nos lignes de `raw_data\db` avant toute construction,
    schémas RPFM et cache des dépendances ; toute adresse mémoire porte sa version (8.1, 9.0, 9.0.2) (206, 290).
R28. On corrige la source, jamais le produit ; jamais un fichier final dans un dossier de sortie ; chaque module écrit
    dans le dossier de SA carte ; un nom de fichier neuf se vérifie libre (44, 121, 229, 312).

**Essais en jeu**
R29. Prévenir Charles avant TOUT lancement du jeu ; aucun pilotage d'écran sans son accord du moment, jamais pendant un
    essai ; pas de capture du bureau ; `etat_clavier.py` après tout pilotage (108, 124, 277, 279, 286).
R30. À chaque reprise : `crash_report\`, `save_games\`, `user.script.txt` ; `essai_tours_auto.py --nettoyer` après tout
    arrêt forcé ; le jeu d'essai n'est à personne d'autre (69, 144, 178).
R31. Un seul changement de fond par essai ; le témoin se rejoue avec la commande exacte ; un changement du pilote se
    valide seul par 2 tours sur un pack éprouvé ; le pilote ne touche jamais en masse aux objets de CA (35, 39, 239,
    270).
R32. Un correctif de script se prouve chargé par sa propre ligne de journal ; avant de conclure à un gel : `ui_locked`,
    panneaux ouverts, `script_log` (231, 285, 288).
R33. Sous `all_players_ai`, la faction du joueur ne joue pas : les mécaniques du seigneur se testent en mode joueur ou à
    la main (210).
R34. Plantage aléatoire : 10 essais par variante au moins (une trentaine pour un taux faible), « piste » avant « cause »,
    sur des parties jouées comme le joueur (caméra, intro) (186, 188, 265, 327).
R35. Ce qui se voit en jeu se juge en jeu, face à la référence WH1 de Charles : ni Terry, ni un fichier compilé, ni les
    tables (67, 113, 114, 282).

**Workshop et site**
R36. Un pack = un objet Workshop ; UNE modification par objet (pack et textes ensemble), puis attendre la levée ; un envoi
    par le lanceur à la fois, `launcher.log` relu, erreur 25 : ne rien renvoyer ; ce qui est en ligne se vérifie
    (tailles) (278, 306, 310, 339 ; remplace 276).
R37. Site : un dossier d'envoi part de la liste complète du déploiement précédent et se compare dans les deux sens ;
    zéro `msedge --headless` avant de rendre la main ; toute phrase de lore publiée passe par un audit (172, 307, 340).

**Méthode**
R38. Shell : ni heredoc, ni `python -c` composé (même d'une ligne), ni `sed` pour retoucher, ni script écrit par
    PowerShell ; pas de tube qui tronque un script qui écrit ; le jeu par `Start-Process` ; chemins absolus ; à
    transmettre à chaque agent (129, 193, 212, 267, 289, 303).
R39. Annoncer la mesure du produit écrit, jamais le bilan de l'algorithme ni l'intention du code ; toute heure vient de
    `date` ; une affirmation sur CA ou dans un guide se vérifie sur les fichiers de CA (81, 211, 248, 337).
R40. Contenu et aspect : WH1 tel quel d'abord (48, 65, 222) ; convention d'un moteur ou d'un outil de CA : un exemple de
    CA qui marche d'abord, et « comme dans X » se mesure sur X (45, 93, 313).

Règles périmées (ne plus appliquer telles quelles) : celles de l'ancien sommaire (25, 63, 73, 74, 97, 102, 109, 113,
143, 155, 208, 230, 232, § C) et celles annotées le 04.10.2026 dans leurs entrées : découvertes du 20.09 (`campaigns.mask`,
script de RPFM, `start_pos_*` hors pack de mod, export BOB avant `build_starpos`, `town-sprawl` non bloquant), 29-undo,
38, découverte de la session 45 (ports), 45 / 174 / 335 (ports), 85, 86, 87, 102 (falaises), 106 / 117 (recette),
110 (remplacer la table de CA), 114, 154 / 156 (préfixe), 179 (copie de la base), 185, B6, 213 (moyen), 265 (piste
des objets reposés), 276.

---

## Session du 20.09.2026 — mise en place de l'atelier et première carte inventée

### A. Erreurs de méthode (coûtent des tours, cachent des faits)

1. **Filtrer trop fort la sortie des validateurs.** J'ai masqué toutes les lignes « validation: Hex »
   pour raccourcir le rapport ; du coup j'ai vu « rivers: FAILED » et « climates: FAILED » sans
   savoir pourquoi, et j'ai dû relancer. → **Règle : ne jamais jeter les messages, les regrouper**
   (remplacer les coordonnées par `Hex(x, y)` et compter les occurrences par type). Le script
   `run_wh3_proof.ps1` et la commande de relance de l'île le font désormais.

2. **Conclure « bug » sans lire la table.** L'export lookup refusait « no campaign uses the map » ;
   j'ai écrit « à établir » alors que `campaigns.xml` répondait en dix secondes : aucune campagne
   n'utilise `wh3_main_combi_map_1`, les vanilla actuelles sont `_map_5` et `_map_4`. → **Règle :
   un message d'outil qui cite une donnée se vérifie dans la donnée avant d'être classé.**

3. **Écrire le guide avant d'avoir lu toute la documentation.** La version 1 contenait neuf erreurs
   (Resize pris pour une mise à l'échelle, « une Error bloque », ponts sur rivières, règles du
   sprawl absentes, deux tables oubliées). L'audit par un agent les a trouvées. → **Règle : pour
   un document de référence, faire relire par un agent contre les sources, avant de livrer.**

4. **Explorer une interface à l'écran sans en avoir besoin.** J'ai passé plusieurs tours à vouloir
   cliquer dans BOB pour voir son arbre, qui n'est que l'arborescence de `raw_data` déjà lisible
   sur disque. → **Règle : avant de piloter une fenêtre, demander ce que l'écran apprendrait que
   le disque, le code ou la ligne de commande ne donnent pas.**
    **[Complétée par les erreurs 108 (jamais piloter l'écran sans l'accord de Charles au moment même ; `etat_clavier.py` après) et 124 (prévenir Charles avant tout lancement du jeu).]** [25.09.2026, ménage]

5. **Lancer un outil inconnu avec des options d'aide.** `bob.modder.x64.exe -h` ouvre une boîte
   modale « Illegal option format » qui bloque le processus ; trois processus BOB sont restés
   suspendus jusqu'à ce que Charles clique. → **Règle : un exécutable à fenêtre ne se lance
   jamais avec des arguments devinés depuis un script ; on lit d'abord sa doc ou on regarde ce que
   son lanceur officiel lui passe (`-no_console`).**

6. `[évitable]` **PR ouverte sans demander de relecteur, alors que le README l'exige.** Le README
   du dépôt décrit un workflow en cinq points dont le 3 : « Create a pull request and assign either
   @victimized0, @robert-d-schultz or @MrJox as a reviewer ». Je l'avais lu et même cité dans la
   séance, puis je ne l'ai pas appliqué en ouvrant la PR #10. Sans conséquence ici, victimized
   suivait le fil Discord et deux relecteurs ont approuvé en onze minutes. → **Règle : avant
   d'ouvrir une PR, relire le workflow du dépôt (README, CONTRIBUTING, gabarit de PR) et cocher
   chaque point.** Un contributeur externe ne peut pas demander de relecteur, l'API l'exige avec
   les droits `push` ou `triage` ; dans ce cas, **citer les pseudos dans le corps de la PR**.
   À savoir aussi : le point 2 du même workflow dit « push to this repo », ce qui suppose un
   accès en écriture ; `LeyZee` a `push: false`, donc le passage par un fork était la seule voie,
   et c'est une adaptation légitime, pas un écart.

### B. Erreurs d'outillage Windows / shell

6. **`sed` sous Git Bash avec des antislashs dans le motif.** MSYS convertit ce qui ressemble à
   un chemin ; le remplacement échoue en silence. Deux fois. → **Règle : remplacer du texte avec
   l'outil Edit ou un script Python ; jamais `sed` quand le motif contient `\`.**
   [Remplacée le 04.10.2026 par n° 189 et n° 269 : toute retouche de fichier passe par l'outil d'édition, jamais
   `sed`, antislash ou non ; `grep` et `sed` jamais dans le même segment.]

7. **`Get-Content -Raw` en PowerShell 5.1 sur un UTF-8 sans BOM.** Lu en ANSI, réécrit en UTF-8 :
   accents détruits dans la note de mémoire et dans un script. → **Règle : PowerShell 5.1 ne
   touche pas aux fichiers texte accentués ; Python ou l'outil Edit.**

8. **Accents dans un `.ps1` sans BOM.** PowerShell 5.1 lit le script en ANSI. → **Règle : scripts
   PowerShell en ASCII pur, et le dire en tête du fichier.**

9. **Une fonction PowerShell qui affiche ET retourne.** Tout ce qui va dans le pipeline devient la
   valeur de retour ; `(Step ...) -ne 0` comparait un tableau et coupait le script après la
   première étape. → **Règle : `Write-Host` pour afficher, `return` d'une seule valeur.**

10. **Heredoc bash trop long** (`ENAMETOOLONG` au-delà de quelques dizaines de Ko). → **Règle :
    un fichier long s'écrit avec l'outil Write.**

11. **Éditer un fichier après l'avoir déplacé.** L'outil Edit refuse un chemin non relu. →
    **Règle : après un `mv`, relire le fichier à son nouveau chemin avant de l'éditer ; et faire
    les déplacements de dossiers en début de session, pas au milieu d'une série d'éditions.**

12. **`vs_installer.exe modify` avec `--wait`, non élevé.** Option inconnue (exit 87), puis refus
    d'élévation silencieux (exit 143) : rien d'installé, exit code trompeur. → **Règle : lire le
    journal `%TEMP%\dd_installer_*.log` après tout appel à l'installeur VS ; lancer `setup.exe
    modify` via `Start-Process -Verb RunAs`.**

13. **Coordonnées d'écran.** J'ai divisé par l'échelle de la capture alors que le repère annoncé
    (« coordinate frame ») est déjà celui à utiliser, puis j'ai cliqué sur une fenêtre que
    l'outil ne rattache pas à l'application autorisée. → **Règle : avec l'outil d'écran, utiliser
    tel quel le repère annoncé ; si un clic est refusé « desktop shell » deux fois, arrêter
    l'exploration à l'écran.**

### C. Erreurs de données (la carte sortait fausse ou incomplète)

14. **Image importée à l'envers.** La ligne 0 du damier est en bas de la carte ; l'export PNG de
    CAIME retourne l'image. → **Règle : toute image se retourne avant encodage** (fait dans
    `write_layer`). Contrôle obligatoire : `export-layer --format png` et comparer au dessin.

15. **Tous les climats vides.** Mon lecteur de `info --names` remettait la liste « Climates » à zéro
    parce que le tableau des tailles de couches, plus bas, répète les mots « Climates » et
    « Attritions ». → **Règle : un analyseur de sortie s'arrête à la fin de sa section ; et on
    vérifie les octets d'un fichier de couche (`Counter` des valeurs) avant d'importer.**

16. **Rivière qui entre dans la mer.** Le générateur marquait le dernier hex de mer. → **Règle :
    une rivière s'arrête sur le dernier hex de terre** (validateur : « river edge pointing into a
    sea hex », « both a river and sea »).

17. **Régions morcelées.** Un découpage de Voronoï coupe les régions à travers les baies ; le
    validateur signale « split into N disconnected areas », et le startpos casse. → **Règle : les
    régions se font pousser par inondation sur la terre seulement, depuis des graines.**

18. **Carte vierge sans noms.** Un `map.hex` neuf ne connaît aucun nom de région ni de sol ; les
    couches importées pointaient dans le vide. → **Règle : `sync-names` juste après `create`,
    puis `info --names`, puis générer.**

19. **Gabarits WH3 pris pour complets.** `wh3_main_combi_map_1` n'a que `map.hex`, et c'est une
    version périmée de la carte. → **Règle : partir de `wh3_main_prologue_map` (complet) ou d'un
    dossier vanilla de l'AKit, et vérifier les cinq fichiers avant tout export Map Data.**

20. **Fichiers d'appui absents du projet neuf.** Map Data et Dynamic Resources les exigent. →
    **Règle : `trees.png`, `tree_database.xml`, `dynamic_resources.png`,
    `dynamic_resources_database.xml` se créent avec le projet** (images vides aux proportions du
    prologue : 7,04 × 7,37 px par hex pour les arbres, 2,54 × 2,40 pour les ressources).

### D. Ce qui n'était pas une erreur mais un piège de l'outil, à connaître

- Windows en français : la base ne charge pas sans le correctif de culture (fork).
- `--borders` plantait sans fenêtre : options statiques non initialisées (corrigé dans le fork).
- `--dynamic-resources` plante MapDataBuilder sur WH3 (code −1073741819, symbole absent ou
  changé dans `tooldatabuilderdll.modder.x64.dll`) : non résolu, à creuser dans `main.cpp`.
- RPFM 5 n'a plus de `rpfm_cli.exe` ; CAIME l'exige pour sa source « RPFM » : garder la 4.2.7.
- Terry est un mode de Tweak ; le paquet Store est le même kit dans un conteneur.

---

### E. Résultat après correction des erreurs C14 à C20 (20.09.2026, 15 h 40)

Carte inventée `ile_claude_map` : onze validateurs sur onze au vert, il ne reste que des remarques
d'information (côtes fines, plages isolées, frontières non générées, une mer qui touche six
régions). Les cinq fichiers de jeu de CAIME sont produits. Chaque règle de la section C est
codée dans `02-scripts\caime_layers.py` ou dans le verbe `sync-names`.

## Session du 20.09.2026 (16 h 30 – 17 h 15) — inventaire du kit Warhammer 1

### A. Erreurs de méthode

21. `[évitable]` **Deviner le nom d'un fichier produit par un outil.** Pour l'aller-retour du
    `map.hex`, j'ai passé `Attritions.hex_layer` à `import-layer` alors que `export-layer` avait
    écrit `layer_attritions.hex_layer` et l'avait affiché ; l'import a échoué (« Layer file not
    found ») et la comparaison d'octets a conclu « identique » sur un fichier jamais réécrit. →
    **Règle : réutiliser le chemin imprimé par l'outil ; un test qui compare deux fichiers
    vérifie d'abord que l'écriture a eu lieu (horodatage ou message « Saved »).** Codée dans le
    script d'aller-retour (contrôle des octets d'horodatage).

22. `[évitable]` **Compter des lignes XML avec des expressions régulières devinées.** Deux essais
    faux (« 0 table », puis le mauvais nom d'élément) avant d'utiliser `ElementTree` ; les lignes
    de la base WH1 sont des éléments `<regions record_key=...>` avec attributs, ce que mon motif
    `<regions>` ne voyait pas. → **Règle : un XML se lit avec un analyseur XML ; l'expression
    régulière sert à chercher, pas à compter.**

23. `[évitable]` **Écrire un script d'inventaire avant d'avoir lu le schéma d'entrée de l'outil.**
    Trois scripts RPFM successifs pour apprendre la forme des réponses (`StringContainerInfo`,
    `VecStringContainerInfo`, `HashMapDataSourceHashSetContainerPath`) et le nom des arguments.
    → **Règle : d'abord `tools/list` et une réponse brute, puis le script.** (`schema.py` fait
    la première partie.)

24. `[évitable]` **Une commande `git rebase --onto` notée sans vérifier ce qu'elle rejoue.** La
    fiche du projet proposait `git rebase --onto origin/main d426716 cli-create-import` pour
    retirer le commit de culture devenu doublon ; elle aurait aussi **perdu** `9a64b7b` (les
    verbes CLI), antérieur à `d426716`, car `--onto` ne rejoue que `<réf>..<branche>`. Vue avant
    exécution (17 h 50). → **Règle : avant un rebasage, lister `git log --oneline <réf>..<branche>`
    et vérifier que c'est exactement ce qu'on veut rejouer ; pour retirer un commit du milieu,
    partir de la base amont complète avec `--empty=drop`.**

25. `[évitable]` **Deux séances d'atelier en parallèle sur les mêmes fichiers** (16 h 30 – 17 h 30) :
    trois sections pour la même relecture du Discord, une fiche projet réécrite pendant qu'on la
    modifiait, une commande erronée héritée. Rien de perdu, mais une demi-heure de réconciliation.
    → **Règle : une seule séance à la fois sur l'atelier ; si deux sont nécessaires, des dossiers
    disjoints et aucun fichier commun.**
    **[Règle périmée : remplacée par le partage des domaines (`CLAUDE.md` § 3) et le préavis (erreurs 145, 215, 221).]** [25.09.2026, ménage]

26. `[évitable]` **Créer un projet de carte sans ses quatre fichiers d'appui.** C'est la règle C20,
    écrite dans ce fichier le matin même, et je l'ai quand même oubliée en créant
    `wh_dlc05_wood_elves_map_1` : dossier avec le seul `map.hex`. → **Règle : `make_support_files.py`
    juste après `create`** (`trees.png` 7,04 × 7,375 px/hex, `dynamic_resources.png` 2,5417 × 2,40,
    les deux XML copiés du prologue). Désormais codée dans un script, plus seulement écrite.
    (Ce n'était pas la cause du plantage de MapDataBuilder, mais c'était un manque réel.)

27. `[évitable]` **Nommer un script d'essai comme un module standard.** `bisect.py` dans le dossier
    courant masque le `bisect` de la bibliothèque standard ; l'import de Pillow a échoué avec une
    erreur d'import circulaire incompréhensible. → **Règle : préfixer les scripts jetables
    (`mdb_bisect.py`) et les garder dans le dossier de travail, jamais dans le dossier du projet.**

28. `[évitable]` **Chercher la cause dans les données avant d'avoir comparé avec un témoin.**
    Douze essais pour isoler le plantage de MapDataBuilder (couches, régions, routes, provinces,
    noms, taille, accents) alors que l'essai qui tranche — **déclarer une carte neuve et minimale**
    — dit en une minute que le problème n'est pas dans nos données. → **Règle : devant un plantage
    d'outil, fabriquer d'abord le plus petit cas neuf possible et le comparer à un cas qui marche ;
    la bissection sur les vraies données vient après.**

29. `[évitable]` **`declare_map.py --undo` lancé avec une fiche modifiée.** Pour bissecter le
    plantage de MapDataBuilder, j'ai enchaîné des `--undo` avec des fiches réduites. L'undo retire
    ce que la fiche **courante** déclare : avec une fiche modifiée, il a supprimé des lignes
    `regions` et `provinces` **partagées avec une autre carte** (ces tables sont globales, pas
    propres à une carte). La carte témoin s'est retrouvée sans aucune région, `sync-names` a
    produit des cartes vides, et MapDataBuilder tombait sur un pointeur nul : **deux heures à
    chercher une cause que je fabriquais à chaque essai.** → **Règle : `--undo` uniquement avec la
    fiche exacte qui a servi à `--apply` ; pour une variante, travailler sur une copie du kit ou
    vérifier après chaque cycle que `sync-names` annonce le bon nombre de régions.** Et pour
    bissecter : **un seul changement à la fois, avec un témoin relancé à chaque tour.**
    [Remplacée le 04.10.2026 par n° 272 : pour retirer des lignes, un outil ciblé, jamais `declare_map --undo`, même
    avec la fiche exacte. La partie « un seul changement à la fois, témoin relancé » reste valable.]

30. `[évitable]` **Bissecter sans revérifier le témoin.** Le témoin (`ile_claude_map`) est passé de
    « marche » à « plante » au milieu de la série sans que je m'en aperçoive, ce qui a invalidé une
    dizaine d'essais et m'a fait conclure « toute carte neuve plante ». → **Règle : relancer le
    témoin à chaque tour de bissection, pas seulement au début.**

### D. Découvertes (reportées dans `GUIDE.md` § 15)

- **Un plantage de la DLL de CA ne dit rien par défaut ; un filtre d'exception le fait parler.**
  `SetUnhandledExceptionFilter` ajouté dans `MapDataBuilder\main.cpp` (fork) affiche le code,
  l'adresse, le sens de l'accès et le module : `0xC0000005 (reading 0x8) in
  empireutility.modder.x64.dll+0x318ead`. « Lecture de l'adresse 8 » = pointeur nul déréférencé,
  donc une donnée attendue et absente — ce qui a orienté la recherche vers la base, pas vers le
  format des fichiers. Sans cet outil, le même plantage se présente comme un simple code de sortie
  −1073741819 indiscernable d'une DLL introuvable.
- **Une carte dont le `map.hex` ne déclare aucune région fait planter MapDataBuilder.** Preuve : le
  même fichier, avant et après, comparé champ par champ (8 + 1 régions contre 0 + 0). Retirer une
  seule région d'une carte saine ne suffit pas à reproduire : la condition exacte reste à cerner.
  **Contrôle à faire avant tout `process` : `sync-names` doit annoncer le bon nombre de régions.**
- **MapDataBuilder plante si la zone jouable de la carte traitée est la dernière ligne de
  `campaign_map_playable_areas`** (20.09.2026, 19 h 40). Vérifié quatre fois dans les deux sens,
  à contenu de lignes identique : seul l'ordre change. C'est la cause réelle de toute la série de
  plantages de la soirée, y compris ceux que j'avais attribués à la base « à moitié déclarée ».
  Trouvée en comparant nos lignes avec la sauvegarde horodatée du dernier état qui marchait, puis
  en restaurant les fichiers, puis en isolant table par table. → **Règle codée :
  `02-scripts\fix_playable_area_order.py`, appelé par `build_saison_map.py`.** Reportée dans
  `GUIDE.md` § 15 n° 25.
- **Leçon de méthode qui vaut pour la suite** : la sauvegarde horodatée prise *avant* chaque
  écriture est ce qui a permis de retrouver l'état qui marchait et de le comparer. Sans
  `db-backups\`, cette panne restait insoluble.
- **Les tailles des colonies changent entre WH1 et WH3** : 7 hex (4 en port) contre 19 hex de
  terre (16 en port), comptés par région et sur la terre seulement. Codé dans `grow_town_slots.py`.
- **Le validateur d'étalement est plus strict que les données de CA** : `wh3_main_combi_map_1`
  échoue sur 5 colonies (terrain difficile en deux zones autour d'une colonie), notre carte sur 2.
  Un échec `town-sprawl` de ce type n'est donc pas bloquant.
  [Remplacée le 04.10.2026 par n° 335 (preuves 333, 334 : plantages au chargement que le validateur annonçait) :
  `validate --all` avant tout export, Error ET Warning des villes corrigés ; seule exception : l'étendue d'une ville en
  col, comme chez CA.]
- **Le bloc « trois entiers inconnus » du `map.hex` (formats 0x12 et 0x14) est une liste.**
  Preuve : octets suivant les listes de noms — vanilla `01 00 00 00 | 00 00 00 00 | 00 00 00 00 |
  22 01 00 00 (290 couleurs)` ; `wh_dlc05_wood_elves_map_1` : `02 00 00 00 | 00 00 00 00 |
  00 00 00 00 | 02 00 00 00 "32" | 00 00 00 00 | 22 01 00 00` ; `wh_dlc03_beastmen_map_1` :
  idem avec `01 00 00 00 "8"`. Disposition : `int32 N`, puis N × (chaîne ASCII, uint32). Le bloc
  de fin est symétrique : `int32 N`, puis N × (`int32 taille`, octets), un bit par hex avec les
  lignes complétées à l'octet (414 × 250 → 52 × 250 = 13 000 octets, là où `Capacity / 8`
  donnerait 12 937). Symptômes avant correctif : exception « dimensions du tableau » (Elfes
  sylvains) ou « 20 × 0 hex » (Hommes-bêtes). Corrigé dans le fork (`MapHexFile.cs`) ;
  aller-retour identique à l'octet près hors horodatage et CRC.
- **`rpfm_server` : l'état (jeu sélectionné, packs ouverts) est propre à chaque session MCP.**
  Preuve : `open_packfiles` dans une session, `list_open_packs` vide dans la suivante. Un
  script = une session, toutes les étapes dedans.
- **`open_packfiles` avec plusieurs chemins ne rend qu'une seule clé** (`file_name` =
  `new_file.pack`) : les packs semblent fusionnés ; ouvrir un pack à la fois quand on veut les
  distinguer. À confirmer.
- **Les packs d'un DLC WH1 (`data_we.pack`) ne portent pas le contenu du DLC** (35 fichiers :
  audio et missions) ; carte, terrain, scripts et startpos de la mini-campagne sont dans
  `data.pack` et `terrain*.pack`. Chercher par les dépendances (`GameFiles`), jamais dans le pack
  du DLC.
- **Le terrain visuel de campagne WH3 se rétro-conçoit en projet Terry** (ChaosRobie, Discord) :
  tif à 8 px par hex, un `.layer` par région, BOB régénère la maille globale.

## Session du 20.09.2026 (18 h 30 – 19 h 15) — revue de la PR #11

### A. Erreurs de méthode

29. `[évitable]` **Attribuer un fichier à son éditeur parce qu'il est dans le dossier de
    l'éditeur.** Dans la réponse publique à la revue, j'allais écrire que « CA a réexporté
    `wh_dlc05_wood_elves_map_1` pour Warhammer 3 et l'entrée supplémentaire a disparu », comme
    preuve que WH3 n'a pas besoin de cette entrée. Le fichier est dans
    `assembly_kit\raw_data\EmpireDesignData\campaign_maps` du kit WH3, mais il date de **18 h 35
    aujourd'hui** : c'est notre propre conversion, produite par l'autre séance. Les vraies cartes
    de CA du même dossier sont toutes à 14 h 40 (heure d'installation du kit). Vu avant envoi.
    → **Règle : avant d'attribuer publiquement une donnée à un éditeur, vérifier l'horodatage et
    le recouper avec les autres fichiers du même dossier ; un dossier d'installation où l'on
    écrit soi-même n'est plus une source.** Corollaire : écrire nos cartes d'essai ailleurs que
    dans le kit, ou les préfixer.

### D. Découvertes

- **Le nombre de blocs de fin est toujours égal au nombre d'entrées** du `map.hex` : 2 et 2 sur
  les deux mini-campagnes WH1, 1 et 1 sur les 14 autres cartes 0x12/0x14. Chaque nom va donc avec
  un bloc. Tous les blocs sont entièrement à zéro, second compris.
- **`« 8 »` et `« 32 »` ne correspondent à aucun compte du fichier** : régions (53 + 3 et 58 + 4),
  types de sol (13 + 3 pour les deux), climats (19 et 24), attritions (7 et 8), tables de couleurs
  (290 et 289 pour les deux), dimensions. Relevé sur 22 fichiers de référence par
  `02-scripts\dump_map_hex_entries.py`.
- **Les 4 octets non lus en fin de `map.hex`** sont la somme de contrôle écrite par
  `AppendChecksum` ; `Load` ne les consomme pas. Tout le reste du fichier est couvert.

## Session du 20.09.2026 (20 h 15 – ) — déblocage du startpos

### A. Erreurs de méthode

31. `[évitable]` **Écrire « listés et extraits » pour des fichiers seulement listés.** Le journal
    d'inventaire annonce « terrain compilé (172 fichiers) listés et extraits » ; sur disque,
    `05-journal\2026-09-20-inventaire-wh1\extrait-packs-wh1\terrain\` ne contient que les deux
    XML (`environment_collection.xml`, `texture_arrays.xml`). Le terrain binaire est resté dans
    les packs WH1. Une séance qui reprend croit disposer de la matière de la phase 3. → **Règle :
    une phrase de journal qui annonce une extraction cite le compte de fichiers *sur disque*
    (`find | wc -l`), pas le compte listé par l'outil.**

32. `[évitable]` **Ajouter à un pack les fichiers d'un dossier sans descendre dans ses
    sous-dossiers.** `build_pack.py` liste `working_data\campaign_maps\<carte>\` avec
    `os.listdir` : `display\borders\borders.pbd` (39 991 octets, produit par CAIME) n'est jamais
    entré dans le pack, alors que le jeu le lit sous ce chemin exact (vérifié sur le prologue
    vanilla : `campaign_maps\wh3_main_prologue_map\display\borders\borders.pbd`). → **Règle : un
    ajout au pack parcourt l'arborescence (`os.walk`) et conserve les chemins relatifs.**

33. `[évitable]` **Déclarer dans une table des noms de fichiers sans vérifier qu'ils existent.**
    Les sept colonnes de fichiers de notre `campaign_map_playable_areas`
    (`map_file`, `overlay_file`, `radar_file`, `minimap_lookup_file`, `campaign_overlay_lookup`,
    `campaign_overlay_map`, `campaign_overlay_map_text`) ont été générées en `<mapname>_*` par
    `declare_map.py`, alors que les fichiers réels portent les noms de WH1
    (`wh_dlc05_wood_elves_lookup.tga`, `..._minimap.png`, …). **Aucun des sept n'existe dans le
    pack.** La ligne de CA, dans le kit WH1, donnait les bons noms. → **Règle : toute colonne qui
    nomme un fichier se vérifie contre le contenu réel du pack avant la construction ; quand on
    porte une carte, on reprend les noms de la ligne d'origine.**

34. `[évitable]` **Appeler `build_starpos_post` et `build_starpos_cleanup` sans attendre que le
    jeu ait tourné.** `build_starpos` répond `"Success"` en **zéro seconde** : cela veut dire
    « le jeu est lancé », pas « le startpos est construit ». Mon script du témoin a enchaîné
    `post` puis `cleanup` aussitôt, donc il a supprimé le `user.script.txt` et restauré les
    fichiers **pendant que le jeu démarrait** : l'essai ne voulait plus rien dire. La séance
    d'hier l'avait déjà écrit (essai 3 : « attente de la fin du jeu avant `post` »), je ne l'ai
    pas appliqué. → **Règle codée** dans `02-scripts\startpos_essai.py` : attendre l'apparition
    du processus `Warhammer3.exe` (180 s), puis sa disparition (900 s), et seulement ensuite
    `post` puis `cleanup`.

35. `[évitable]` **Conclure « le plantage s'est déplacé » en comparant deux campagnes
    différentes.** Après l'export BOB, notre campagne plantait à `Warhammer3.exe+0x234ACF8` ;
    j'ai comparé à `+0x27A9A9C` relevé avant l'export — mais ce chiffre-là venait des essais sur
    le **prologue vanilla**, pas sur la nôtre. Les vidages d'hier soir, relus, donnent déjà
    `+0x234ACF8` sur notre campagne **avant** l'export, et le témoin prologue refait **après**
    l'export donne toujours `+0x27A9A9C` : **l'export n'a rien déplacé du tout**, l'adresse dépend
    de la campagne. Annoncé à Charles comme un progrès pendant vingt minutes. C'est la règle A30
    (« relancer le témoin à chaque tour ») appliquée à l'envers : j'avais un témoin, je ne l'ai
    pas rejoué avant de conclure. → **Règle : une mesure d'avant et une mesure d'après ne se
    comparent que si tout le reste est identique — même campagne, même script, même pack ; sinon
    on rejoue le témoin d'abord.** Et pour un plantage, ranger les vidages par (cas testé,
    adresse) avant d'interpréter, pas par ordre chronologique.

36. `[évitable]` **Prendre « plus de plantage » pour « ça avance ».** Mettre
    `add_working_directory assembly_kit\working_data;` **avant** `process_campaign_startpos` fait
    disparaître le plantage : le jeu sort proprement en neuf secondes. Mais il sort **avant l'init
    réseau**, c'est-à-dire plus tôt qu'avant, et sans rien produire. → **Règle : un échec plus
    précoce n'est pas un progrès. Le signe d'avancement, c'est d'aller plus loin (durée, journaux
    écrits, fichiers produits), pas de planter moins fort.**

37. `[évitable]` **Corriger une valeur sans regarder ce que l'outil en fait.** Huit personnages
    portaient le sous-type `default`, valide dans Warhammer 1 et absent des 613 `agent_subtypes`
    de Warhammer 3 ; le site du plantage cite `faction_leader` et lit un enregistrement nul. La
    piste semblait parfaite, et `declare_campaign.py` avait bien un défaut réel (`return
    sub_map[value] or value` réinstalle la clé quand la traduction vaut `None`). Mais **BOB
    normalise le sous-type à l'export** : il réécrit `wh_main_brt_lord` en `default` de lui-même.
    Le fichier exporté est identique avant et après, et le plantage aussi (mesuré). J'ai dépensé
    un cycle `--undo --apply` sur le kit pour rien. → **Règle : avant de corriger une valeur qui
    traverse un outil, comparer l'entrée et la sortie de cet outil sur la valeur en question.**
    Une ligne de Python (diff colonne par colonne entre `raw_data\db\<table>.xml` et
    `raw_data\EmpireDesignData\campaigns\<campagne>\<table>.xml`) l'aurait dit tout de suite.

### D. Découvertes

- **La chaîne du bloc d'entrées du `map.hex` est la valeur `campaigns.mask`.** Preuve :
  `raw_data\db\campaigns.xml` du kit Warhammer 1 donne `wh_dlc05_wood_elves` → `mask = 32` et
  `wh_dlc03_beastmen` → `mask = 8`, exactement les deux chaînes relevées le matin dans les
  `map.hex` des deux mini-campagnes ; `main_warhammer` n'a pas de masque, et les cartes vanilla
  n'ont que l'entrée vide. Le bloc de fin apparié est alors le masque hex par hex de cette
  campagne (tous les octets à zéro dans les 22 fichiers de référence : lecture plausible, non
  vérifiée sur des données non nulles). Ferme la question ouverte le matin (« « 8 » et « 32 » ne
  correspondent à aucun compte du fichier »). Reporté dans `GUIDE.md` § 15 n° 15 ; à citer dans
  la PR `fix/map-hex-entry-list`, qui pourra nommer le champ au lieu de le dire inconnu.
  [Précisée le 04.10.2026 par n° 331 : vrai pour le `map.hex` de WH1, mais dans WH3 `campaigns.mask = 32` fait planter
  la génération ; toutes les campagnes du kit l'ont vide : une ligne `campaigns` à nous garde `mask` vide.]
- **Le script que RPFM fait exécuter au jeu pour construire un startpos** (extrait des chaînes de
  `rpfm_server.exe`, car RPFM efface le fichier ensuite) — il l'écrit dans
  `%APPDATA%\The Creative Assembly\Warhammer3\scripts\user.script.txt` :

  ```
  add_working_directory assembly_kit\working_data;
  mod <pack>;
  process_campaign_startpos <campagne> <hlp_spd>;
  quit_after_campaign_processing;
  ```

  Deux conséquences : le jeu **crée réellement le monde de campagne** (d'où l'hypothèse du
  terrain), et il lit aussi les fichiers **en vrac dans `assembly_kit\working_data`**, donc ce qui
  manque au pack peut être servi de là.
  [Remplacée le 04.10.2026 par n° 190 (code de RPFM 5.0.6 : pas d'`add_working_directory` pour WH3) et n° 39 :
  le script du startpos s'écrit à la main (`startpos_manuel.py --sans-working-dir`) ; avec `add_working_directory`, le
  jeu sort en 9 s sans rien produire.]
- **Un cinquième outil de startpos existe dans RPFM** : `build_starpos_check_victory_conditions`,
  qui vérifie la présence de `db/victory_objectives.txt` dans le pack (message :
  « Processing the startpos without this file will result in issues in campaign »). Appelé sur
  notre pack le 20.09.2026 au soir : répond `"Success"`. Ce n'est donc pas la cause du plantage.
- **Le journal du jeu situe le plantage après le chargement complet de la base.**
  `%APPDATA%\The Creative Assembly\Warhammer3\logs\mp_log.txt` s'arrête sur
  `calculating data checksum... done` puis l'initialisation réseau, quatorze secondes après le
  démarrage. Nos 267 lignes de base ne cassent donc pas le chargement ; le plantage est plus tard.
  `crash_report\*.stack.txt` ne donne que `Warhammer3` et `ntdll` : inutilisable.
- **`build_starpos` plante le jeu même sur une campagne vanilla, depuis un pack vide.** Preuve :
  `wh3_main_prologue` construit depuis `temoin_startpos.pack` (vide), notre pack retiré de
  `<jeu>\data\` : le jeu démarre, tourne 25 à 34 s, écrit un rapport de plantage, et
  `build_starpos_post` rend « Startpos file failed to generate ». Deux fois, plus une troisième
  fois avec un `user.script.txt` écrit à la main. **La cause n'est donc jamais dans les données
  d'une carte.** (Journal : `05-journal\2026-09-20-inventaire-wh1\phase-2-startpos-temoin.md`.)
- **Le vidage mémoire du jeu se lit sans débogueur.** Le `.mdmp` est un MINIDUMP standard : flux
  n° 6 (`Exception`) → code, adresse, sens de l'accès ; flux n° 4 (`ModuleList`) → le module qui
  contient l'adresse. Ici : `0xC0000005`, **lecture de l'adresse 0x0**, dans
  `Warhammer3.exe+0x27A9A9C` — pointeur nul, donc une donnée attendue et absente. Le
  `crash_report\*.stack.txt` fourni par le jeu (« Warhammer3, ntdll ») n'apprend rien ; le `.mdmp`
  à côté, si. Script de lecture : voir le journal ci-dessus.
- **Les tables `start_pos_*` n'entrent jamais dans un pack de mod.** `start_pos_factions` et
  `start_pos_regions` sont dans les packs du jeu, mais **`start_pos_characters` n'y est pas** ; et
  « The Old World Campaign » (campagne neuve qui marche, 606 tables) n'en embarque **aucune**, il
  ne livre que le `startpos.esf` fini. Elles doivent donc arriver par
  `assembly_kit\working_data\db\`, que RPFM fait lire au jeu avec
  `add_working_directory assembly_kit\working_data;`. **Ce dossier n'existe pas** : aucun des deux
  kits ne le livre (il se fabrique depuis `raw_data\db` par le nœud `database` de BOB) et
  `binaries\bob_db.log` fait 0 octet. C'est la cause du pointeur nul, et c'est la « brique 2 » du
  `GUIDE.md` § 16, jamais faite.
  [Remplacée le 04.10.2026 par n° 39, n° 190 et la recette de `CLAUDE.md` § 5 (et par la découverte du même soir, plus
  bas : dans un pack de mod, le jeu nomme la ligne fautive) : les tables `start_pos_*` passent par un pack de génération
  (`zz_startpos_db.pack`, `--sans-working-dir`), jamais par `working_data`, et jamais dans le pack joué.]
- **La chaîne officielle du startpos est dans `bob_campaign.modder.x64.dll`, et RPFM n'en fait que
  la seconde moitié.** Actions lues dans la DLL : `Build Queried Campaign Tables` (lit
  `<raw>/database/campaigns`, `start_pos_factions`, `start_pos_regions`, `start_pos_settlements`,
  `campaign_map_playable_areas` → écrit `<working>/start_pos_db/` et les `startpos_*.xml` sous
  `raw_data/EmpireDesignData/campaigns/`), `Export XML` (une par campagne),
  `Export start pos localisation`, puis `CampaignStartPos` qui lance le jeu avec
  **`set_campaign_startpos_working_directory`** — commande que RPFM n'écrit jamais — et récupère
  `data/campaigns/<campagne>/startpos.esf`. **Règle : avant tout `build_starpos` de RPFM, faire
  l'export BOB.** Fait le 20.09.2026 à 21 h 00 : 3 788 actions en 109 s, zéro erreur, zéro
  avertissement ; 1 694 fichiers dans `working_data\db\`, 54 fichiers plus un `.pack` par campagne
  dans `raw_data\EmpireDesignData\campaigns\`. **L'export était une brique manquante réelle, mais
  il ne débloque pas le startpos** : le plantage est identique avant et après (vérifié en rejouant
  le témoin prologue à 21 h 20). Et l'action `Campaign / Process start pos` de BOB lui-même rend
  « Startpos file not found after running the game! » : **la génération de startpos ne marche pas
  sur cette installation, même pour une campagne vanilla sans aucun mod chargé.**
  [Remplacée le 04.10.2026 par la recette du startpos de `CLAUDE.md` § 5 (`startpos_manuel.py`, n° 39, 190) : ni
  `build_starpos` de RPFM ni export BOB à chaque génération ; l'export BOB n'a servi qu'à amorcer le pack de génération.]
- **Le jeu a une commande faite pour ça** : `wait_for_debugger`, que son binaire décrit comme
  « Waits for debugger when the command is read, **useful for debugging startpos generation** ».
  Inutilisable ici : Visual Studio n'est installé qu'en **Build Tools** (pas d'IDE, pas de
  `cdb.exe`, pas de `vsjitdebugger`).
- **`read_layer` puis `encode_flat` n'est PAS un aller-retour fidèle pour les couches d'arêtes.**
  Mesuré le 20.09.2026 sur les treize couches de notre carte : identique à l'octet près pour dix
  d'entre elles, **différent pour `Rivers`, `Roads` et `RegionBorders`**. Ces trois-là stockent un
  **masque des six arêtes** par hex ; `read_layer` le réduit à un booléen et `encode_flat` réécrit
  `1`. Le nombre d'hex non nuls est conservé — donc le défaut est **invisible à un contrôle
  naïf** — mais la direction des rivières, des routes et des frontières est aplatie (1 803, 3 132
  et 11 728 octets changés ; premier écart : une valeur 9 devient 1). → **Règle : ne jamais
  réécrire ces trois couches par ce chemin ; n'importer que les couches qu'on a réellement
  modifiées.** Attention : `grow_town_slots.py` écrit **toutes** les couches dans son dossier de
  sortie ; n'en importer que `TownSlots` et `TownSprawl`, comme son mode d'emploi le fait.

38. `[évitable]` **Reverter un essai avant d'avoir posé la seule question qui comptait.** Pour
    donner un emplacement de colonie aux deux régions sauvages (contournement du plantage du
    startpos), j'ai posé 19 hex de terre et 4 hex de mer, puis trois validateurs ont échoué
    (`town-slots`, `impassable`, `town-sprawl` : les régions sauvages sont entièrement
    infranchissables). J'ai restauré la carte — **sans avoir lancé `process` ni le jeu**. Or le
    journal dit déjà qu'un échec de `town-sprawl` n'est **pas bloquant** (§ D, carte de CA qui
    échoue sur 5 colonies), et rien ne prouvait que ceux-là l'étaient : `map_data.esf` se serait
    peut-être produit quand même, et c'est le jeu qui tranche, pas le validateur. → **Règle :
    quand un essai vise une question précise, aller jusqu'à cette question ; un validateur rouge
    n'est pas une réponse, c'est un avis.**
    [Remplacée le 04.10.2026 par n° 335 (preuves 333, 334) : `validate --all` avant tout export, Error ET Warning des
    villes corrigés (seule exception : l'étendue d'une ville en col, comme chez CA). La première moitié (« aller jusqu'à
    la question posée ») reste valable.]

- **Le vidage garde les arguments de l'appel qui a échoué.** Au plantage, `rdx` pointait encore sur
  la clé passée à la fonction qui a rendu nul : `0xFFFF0000`. → **Règle : désassembler la fonction
  appelée avant de lire ses arguments ; le vidage contient les deux.**
- ~~**Le chemin de génération du startpos ne teste pas son propre sentinelle.** … une région sans
  emplacement de colonie produit exactement ce `0xFFFF` … **Contournement : donner un emplacement
  de colonie à toutes les régions.**~~
  **Corrigé le 21.09.2026 — les deux lectures ci-dessus étaient fausses**, faute d'avoir
  désassemblé les fonctions jusqu'au bout (voir l'entrée 39).
  - La clé `0xFFFF0000` n'est **pas** une coordonnée : c'est une paire `(A = 0, B = 0xFFFF)`
    servant à un accès `conteneur[A].sous_tableau[B]`. Le résolveur `Warhammer3+0x272F13C` rend
    **NULL** (pas `-1`) dès que l'un des deux mots vaut `0xFFFF`, et l'appelant déréférence.
  - La coordonnée réelle est ailleurs, dans `[rbp+0x40]` chez l'appelant, et vaut `0x0058010E`
    = **(270, 88)**, la position de départ d'Orion.
  - Le contournement « donner un emplacement de colonie aux régions sauvages » a été appliqué
    entièrement et **n'a rien changé** : mesuré, la clé vaut `0xFFFF0000` y compris sur un hex
    qui porte une colonie. Le tableau par hex du jeu est vide partout. Ne pas rouvrir cette piste.
- **Mettre les tables `start_pos_*` dans un pack fait parler le jeu.** Tant qu'elles sont dans le
  kit, le jeu se tait et plante ; dans un **pack de mod**, son validateur s'active et écrit
  `crash_report\bad_mods_report.txt` avec `first_invalid_database_record`,
  `first_invalid_database_table` et `first_invalid_packfile`. Il ne nomme qu'un enregistrement à la
  fois, mais il le nomme. **C'est le meilleur outil de diagnostic trouvé de la soirée.**
- **Les groupes de personnalité de l'IA ont tous été renommés entre WH1 et WH3.** Warhammer 3 les
  préfixe `wh3_combi_personality_group_`. Une seule valeur WH1 dans `cai_personality_group` fait
  **refuser le pack entier**. Nous en avions 8, sur 17 de nos 39 factions. Correspondances codées
  dans `declare_campaign.py`.
- **La sortie de BOB n'est pas valide telle quelle dans un pack de mod.** BOB normalise le
  `subtype` des personnages en `default` à l'export ; `default` est une clé de Warhammer 1, absente
  des 613 `agent_subtypes` de Warhammer 3, et le validateur de mods la refuse. Il faut **défaire
  cette normalisation** après l'export, en reprenant la valeur du kit. (Corollaire : ma conclusion
  de 22 h 20 « BOB normalise, donc ce n'est pas un défaut » était à moitié fausse — elle valait
  pour `working_data`, pas pour un pack.)
- **Les références d'une table se lisent dans son propre schéma.** `decode_packed_file` rend la
  `definition`, dont chaque champ porte `is_reference = [table, colonne]` ; il suffit de lire les
  valeurs valides dans `raw_data\db\<table>.xml`. `02-scripts\valider_start_pos.py` vérifie ainsi
  522 lignes sans lancer le jeu. **L'outil `get_reference_data_from_definition` de RPFM, lui, rend
  une réponse vide** : ne pas compter dessus.
- **Une structure du jeu se retrouve en mémoire par sa table virtuelle.** Toutes les instances
  d'une même classe la partagent : chercher ses huit octets dans le vidage les donne toutes, ce qui
  permet de **comparer notre campagne à celles de CA champ par champ**
  (`02-scripts\structures_campagnes.py`). C'est ce qui a prouvé que le champ `+0x48` n'était nul
  que chez nous.
- **`cdb.exe` s'obtient sans élévation** : `winget install Microsoft.WinDbg --scope user` installe
  un paquet qui contient `amd64\cdb.exe` sous `C:\Program Files\WindowsApps\Microsoft.WinDbg_…`.
  Inutile d'ajouter les *Debugging Tools* au SDK. La commande utile est
  `cdb -z <vidage> -c ".ecxr; k 40; u @rip L6; q"` : **sans `.ecxr`, on regarde le fil du
  rapporteur de plantage, pas le fil fautif**, et la pile ne veut rien dire. Les symboles publics
  de Microsoft ne nomment pas le code de CA (`Warhammer3!luaopen_debug+0x…` est l'export le plus
  proche, le nombre n'a aucun sens) : on travaille en RVA et on nomme les cadres par les chaînes
  qu'ils référencent.
- **Une pile reconstituée par balayage de la pile est à moitié du bruit.** La mienne donnait cinq
  cadres de machinerie d'exception avant les vrais ; le déroulement de `cdb` n'en garde aucun.
  → `cdb` fait autorité ; le balayage ne sert que s'il n'y a pas de débogueur.
- **Un vidage mémoire se lit entièrement par script, sans débogueur** :
  `02-scripts\lire_vidage.py`. Registres, octets de l'instruction fautive relus dans le PE,
  pile reconstituée en balayant la pile du fil fautif, et **chaînes référencées autour du site**
  (les `lea r64, [rip+disp32]` résolus) — c'est ce dernier point qui dit de quoi parle une
  fonction quand on n'a pas les symboles. Résultat pour nos deux plantages :
  notre campagne `mov r8d,[rax+0x24]` avec `rax = 0`, à 878 octets de la chaîne `faction_leader`
  et juste après `ANCILLARIES` / `PAYLOADS_BLOCK` ; prologue `mov rax,[rcx]` puis
  `call [rax+0x28]` avec `rcx = 0`, un appel virtuel sur un objet nul.
- **`Pack / Create pack file` n'est pas un préalable au startpos** : c'est un *consommateur* de
  `Process start pos` dans BOB, il rend `DependencyFailed` quand celui-ci échoue. La recette
  communautaire qui dit de cocher les deux ne corrige donc rien.
- **BOB normalise le sous-type des personnages à l'export** : `wh_main_brt_lord` et
  `wh_main_dwf_lord` deviennent `default`, mais `wh_main_grn_orc_warboss` et
  `wh_dlc05_wef_glade_lord` sont gardés — et les quatre ont pourtant `auto_generate = 1`. La règle
  exacte reste à trouver (sans doute le seigneur par défaut de la faction). Conséquence pratique :
  **`default` dans un `start_pos_characters.xml` de campagne est une valeur normale de BOB**, pas
  un reste de Warhammer 1.
- **Dans BOB, cocher un nœud ouvre un sélecteur d'actions, et le nœud n'est coché que si une
  action l'est.** Cliquer ailleurs sans avoir coché d'action annule la sélection — silencieusement.
  Et `Campaign / Build Queried Campaign Tables` **seule** ne produit rien (4 s, deux actions au
  vert, zéro fichier) : elle ne bâtit que les campagnes « interrogées » par les actions
  `Export XML`. C'est `<All>` qui fait le travail, et BOB ajoute alors de lui-même le nœud
  `Database Export`.
- **Une fenêtre se déplace et se redimensionne par l'API Windows, pas à la souris.**
  `MoveWindow` + `SetForegroundWindow` via `Add-Type` : un glisser de barre de titre près du bas
  de l'écran se fait refuser (« desktop shell », erreur A13) et la fenêtre de BOB s'ouvre à
  158 × 26 pixels en bas de l'écran. Trois lignes de PowerShell remplacent une série de clics
  incertains.
- **Les commandes de console du jeu se lisent dans `Warhammer3.exe`**, avec leur description :
  `process_campaign_startpos name` (« Adds name to list of campaigns to preprocess », **un seul
  argument** — RPFM en passe un second, vide), `process_campaign_ai_map_data`,
  `set_campaign_startpos_working_directory path`, `unset_campaign_startpos_working_directory`,
  `quit_after_campaign_processing`, `add_working_directory <directory name>`, et le chemin de
  sortie `campaigns/%S/startpos.esf`. Plus fiable que de deviner la syntaxe.
- **`build_starpos` de RPFM répond `"Success"` en zéro seconde** : cela veut dire « le jeu est
  lancé », pas « le startpos est construit ». Le réglage `warhammer_3_assembly_kit` était **vide**
  dans `HKCU\Software\FrodoWazEre\rpfm` ; le renseigner fait bien voir le kit au serveur
  (`assembly_kit_path` répond le bon chemin) mais **ne change pas** le script écrit.
- **Ce qu'un dossier `campaign_maps\<carte>\` contient chez CA** (prologue WH3, 33 fichiers) :
  `map_data.esf`, `pathfinding.ppd`, `trade_routes.ptd`, `dynamic_resources.esf`, `hlp_data.esf`,
  `spd_data.esf`, `camera_heightmap.png`, `prebattle_map.png`, les lookups `.tga` et `.dds`, et
  sous `display\` : `borders\borders.pbd`, `trees\trees.campaign_tree_list`, flèches, rivières,
  skybox, frontières. Le `_text.dds` que la table déclare **n'existe pas** chez CA : une image de
  la table absente du pack n'est donc pas forcément fatale.

## Session du 21.09.2026 (00 h 00 – 00 h 45) — le plantage du startpos nommé

### A. Erreurs de méthode

39. `[évitable]` **Rejouer un « témoin » avec une autre variante de commande que celle qui avait
    produit la mesure d'origine.** Les essais qui plantaient étaient lancés
    `startpos_manuel.py … --sans-working-dir` — c'est écrit noir sur blanc dans le journal, à la
    ligne « Ce qu'il faut refaire pour rejouer cet état ». J'ai relancé **sans** ce drapeau, donc
    avec `add_working_directory assembly_kit\working_data;` en plus : le jeu sort alors en neuf
    secondes sans rien faire, code 0. J'en ai conclu une régression, puis j'ai soupçonné tour à
    tour le pack, `rpfm_server`, Steam, l'espace disque et `no_clean_exit` — six essais perdus.
    C'est la règle A35 une seconde fois. → **Règle : avant de rejouer un témoin, relire dans le
    journal la commande exacte qui a produit la mesure, drapeaux compris, et la recopier. Le
    journal a une section « pour rejouer cet état » : elle est là pour ça, la lire d'abord.**

40. `[évitable]` **Noter l'inverse de ce que la source dit.** J'avais consigné que le hex fautif
    était « infranchissable » parce que sa couche `Impassable` vaut 1. Or l'en-tête de
    `02-scripts\caime_layers.py` le dit en toutes lettres : « `Impassable` : 1 = passable,
    0 = impassable (careful: it is a passability flag) ». Le hex était donc **franchissable**, ce
    qui change entièrement sa lecture. → **Règle : pour toute couche dont le nom est un adjectif,
    relire l'encodage dans `caime_layers.py` avant d'interpréter une valeur ; ne jamais déduire le
    sens d'un drapeau de son nom.**

### B. Découvertes

- **La coordonnée qui fait planter le startpos est une position de personnage**, et on peut le
  prouver : elle est identique sur les six vidages, elle se trouve telle quelle dans
  `start_pos_characters`, et **elle suit le personnage quand on le déplace** (Orion mis en
  (283, 87) → le plantage passe en (283, 87) ; les trois seigneurs mis en (0, 0) → le plantage
  passe en (1, 1)). → **Méthode : quand un vidage livre une coordonnée, la chercher dans les
  tables de départ avant toute autre hypothèse ; puis la déplacer pour confirmer.**
- **Le tableau « une entrée de 10 octets par hex » du jeu est décodé depuis un flux RLE** de
  `{dword valeur ; word répétitions}` (`Warhammer3+0x270FA76`). C'est pour cela qu'un
  `map_data.esf` de 1,2 Mo suffit à 176 000 hex, et pour cela qu'une comparaison octet à octet des
  fichiers ne montre pas les enregistrements : ils sont construits au chargement.
- **On trouve l'écrivain d'un tableau en balayant l'exécutable, pas en cherchant au hasard.**
  L'idiome `mov rax,[base+0A0h]` / `lea rdx,[r+r*4]` / `[rax+rdx*2]` ne désigne que les accès à ce
  tableau : 25 sites dans `Warhammer3.exe`, dont le site du plantage et le décodeur RLE.
  Codé dans `02-scripts\chercher_motif_exe.py --pas-de-10`.
- **L'orientation des couches est tranchée** : l'axe y du jeu est celui de CAIME en espace hex
  (ligne 0 en bas). Preuve : `debug\debug_edge_costs.raw` de MapDataBuilder donne `[5,5,5,5,5,5]`
  au hex (270, 88) lu en espace hex, et `[0,0,0,0,0,0]` lu en espace image.
- **MapDataBuilder écrit un dossier `debug\` de rasters, un octet ou deux par hex** :
  `debug_tile_groups.raw` (la région-zone de chaque hex), `debug_hlci_areas_map.raw`,
  `debug_land_region_passable_edges.raw`, `debug_edge_costs.raw` (6 arêtes), `debug_is_navigable.raw`.
  C'est la vue qu'a l'outil de notre carte, gratuite et lisible sans le jeu.
- **Chaque région est scindée en deux « tile groups »** par MapDataBuilder : celui qui porte
  l'emplacement de colonie et celui qui ne le porte pas (56 régions sur 61 chez nous). Un tile
  group n'appartient jamais à deux régions.
- **En-tête d'un `map_data.esf` (ESF `0xABCB`)** : `[magic u32][0 u32][horodatage u32][offset de la
  table des noms u32]`, racine à l'offset 16 ; table des noms = `u16 nombre` puis `u16 longueur +
  ASCII`. Un nœud-enregistrement s'écrit `type(1) nom(1) CAULEB128(offset de fin)`, le type valant
  `0x80 | version<<1`, et `0xC0` pour un bloc d'enregistrements.
- **Dans `start_pos_characters`, (0, 0) veut dire « dans ma capitale »**, pas « position nulle » :
  23 de nos 26 personnages sont dans ce cas, et les trois autres sont les seigneurs légendaires qui
  démarrent en armée. `start_pos_character_to_settlements` vide est donc **normal**. **[Démenti le 22.09 par
  l'erreur 95 et `GUIDE.md` § 15 n° 100 : sans ce lien, WH3 pose le personnage en (1, 1). C'est la règle en vigueur.]**

## Session du 21.09.2026 (00 h 45 - 01 h 35) - le verrou du startpos saute

### A. Erreurs de methode

41. `[evitable]` **Changer l'octet qui etiquette un format sans convertir le format.** Voyant que
    CA livre ses `map_data.esf` en ESF `0xABCA` et que le kit ecrit `0xABCB`, j'ai retourne la
    magie seule. Le jeu a bien change de comportement, mais il a lu les tables de chaines avec la
    mauvaise largeur de champ et a indexe hors du tableau (plantage a `Warhammer3+0x4946BB`).
    Le pas etait bon, le raccourci non. -> **Regle : une magie de fichier designe une grammaire.
    Avant de la changer, lire le fichier des deux cotes et convertir ce qui differe ; puis relire
    le resultat pour le verifier.** Code dans `lire_esf.convertir_vers_abca`, qui relit ce qu'il
    ecrit avant de le rendre.

42. `[evitable]` **Ecrire dans un commentaire de code une cause qu'on n'a pas verifiee.** J'ai
    porte `TARGET_PORT` de `grow_town_slots.py` a 19 en annoncant « MapDataBuilder exige les 19 »,
    avant d'avoir mesure l'effet. Les 57 colonies sont bien passees a 19 hex et les trois fautives
    n'ont **toujours** pas de position. Le commentaire, lui, serait reste comme un fait acquis.
    -> **Regle : un commentaire affirme ce qui a ete mesure, et dit ce qui a ete essaye sans
    succes. Corriger le commentaire fait partie de la mesure qui l'infirme.**

43. `[evitable]` **Decoder un entier sans verifier l'ordre des octets.** Le champ « nombre d'hex »
    d'une region m'a donne 3 420 161 la ou la couche en comptait 77 876, et j'ai failli y voir un
    defaut de MapDataBuilder. Les octets `01 30 34` lus en **gros-boutien** valent exactement
    77 876 : dans l'ESF, les entiers sur **trois** octets (types `0x18`, `0x1C`) sont ranges poids
    fort en premier, ceux sur deux octets poids faible en premier. -> **Regle : valider un
    decodage sur une valeur dont on connait deja la reponse par ailleurs — ici les 61 comptes
    d'hex de la couche Regions — avant d'en tirer une conclusion.**

### B. Decouvertes

- **MapDataBuilder du kit ecrit `map_data.esf` au format ESF `0xABCB` ; Warhammer 3 ne consomme
  que `0xABCA`.** En `0xABCB` le jeu laisse son tableau « une entree de 10 octets par hex » a la
  valeur de remplissage `0xFFFF0000` et la generation du startpos meurt dans l'IA de campagne a
  `Warhammer3+0x2A4401A`. **La seule difference entre les deux formats est la largeur du champ de
  longueur des deux tables de chaines en fin de fichier : `u16` pour `0xABCA`, `u32` pour
  `0xABCB`.** En-tete, arbre de noeuds et table des noms sont identiques. Demontre par
  aller-retour : converti -> le plantage disparait et se deplace ; remis en `0xABCB` -> il revient
  a l'identique. **Codé dans `build_pack.py` (`corrige_esf`).** C'est le verrou qui tenait le
  projet depuis le 20.09.2026 au soir.
- **Grammaire de l'ESF de Total War, etablie sur les octets et verifiee** (le parcours de l'arbre
  tombe exactement sur la table des noms, sur trois cartes) :
  en-tete `u32 magie | u32 0 | u32 horodatage | u32 offset de la table des noms`, racine a
  l'offset 16 ; table des noms `u16 nombre` puis `u16 longueur + ASCII` ;
  noeud-enregistrement `type(1) nom(1) CAULEB128(taille du contenu)`, le type valant
  `0x80 | version<<1` et `0xC0` pour un bloc (`CAULEB(taille) CAULEB(nombre)` puis chaque groupe
  precede de sa taille) ; noeud-valeur de taille fixe par type, tableau = `type|0x40` puis
  `CAULEB(taille en octets)`. CAULEB128 : 7 bits par octet, **poids fort en premier**, `0x80` =
  « un autre suit ». Lecteur complet dans `02-scripts\lire_esf.py`.
- **Le tableau par hex du jeu fait 10 octets** : 4 octets de paire `(region, zone)` decompresses
  depuis `REGION_AREA_INDEX_OVERRIDE`, plus 6 octets venant de `HEX_MAP_DATA`.
- **`SETTLEMENT_INFO` porte la position logique de la colonie**, et cette position vaut **le
  centre du disque hexagonal de rayon 2** de son emplacement (verifie au hex pres). Sans disque
  parfait, MapDataBuilder ecrit `0xFFFF, 0xFFFF` — mais le disque parfait **ne suffit pas** :
  trois de nos colonies gardent `0xFFFF` avec un disque parfait, dans une seule zone, sans port.
- **Modele d'une colonie portuaire chez CA** (`wh3_main_chaos_map_4`, 26 ports, aucune sans
  position) : bloc de port = le disque entier de 19 hex et il porte la position, bloc principal =
  son sous-ensemble terrestre de 16 hex.
  [Note du 04.10.2026 : ceci décrit le bloc de port de `map_data.esf` (compilé) ; la règle des couches de CAIME
  (16 + 3 hex de Port, n° 45, 337) parle de la carte source : deux choses différentes.]
- **Une region de CA n'a qu'une seule « zone » (`REGION_AREAS`)** ; les notres en ont jusqu'a
  seize, parce que nos regions sont coupees par l'infranchissable. Le jeu sait faire, mais c'est
  une difference structurelle a garder en tete.
- **`extract_packed_files` de rpfm_server exige `export_as_tsv`** bien que le schema le dise
  optionnel : sans lui, l'appel rend une reponse vide et n'ecrit rien.

## Session du 21.09.2026 (11 h 30 - 12 h 15) - le startpos est genere

### A. Erreurs de methode

44. `[evitable]` **Corriger dans un produit de construction au lieu de corriger la source.**
    Le 20.09.2026, `ajouter_images_campagne.py` a reecrit les sept colonnes de fichiers de
    `campaign_map_playable_areas` **dans le pack**, et `retirer_colonies_sauvages.py` a retire deux
    colonies **du pack**. Or `build_pack.py` recopie a chaque construction les tables **du kit** :
    les deux corrections etaient effacees a chaque reconstruction, sans un message. Consequence
    directe : la minicarte declaree (`radar_file`) pointait vers un fichier absent, et la
    generation du startpos mourait en la lisant (`Warhammer3+0x3211033`) — une fois les autres
    verrous leves. La regle A33 (« toute colonne qui nomme un fichier se verifie contre le pack »)
    etait ecrite, mais pas codee. -> **Regle : on corrige la source, jamais le produit ; et toute
    regle qui peut etre verifiee par la chaine de construction y est codee.** Codé : `build_pack.py`
    verifie maintenant chaque fichier declare et sort en erreur s'il manque ;
    `corriger_zone_jouable.py` et `retirer_colonies_sauvages.py --kit` corrigent le kit.

45. `[evitable]` **Chercher la cause en decortiquant au lieu de regarder comment l'auteur fait.**
    Pour les trois ports sans position, j'ai essaye quatre hypotheses successives (19 hex, disque
    parfait, zone unique, retrait des ports), chacune mesuree mais aucune tiree de la reference.
    Il suffisait d'exporter les couches de la carte **de CA** et de regarder une de ses colonies
    portuaires : le modele (disque de 19 hex = 16 principal + 3 port, cote mer) s'y lit en une
    commande. -> **Regle : devant un format ou une convention d'un outil de CA, exporter d'abord un
    exemple de CA qui fonctionne, et verifier son propre outil sur cet exemple avant de l'appliquer
    a nos donnees** (fait ici : 242 colonies de CA jugees conformes, zero a repeindre).
    [Ports : remplacée le 04.10.2026 par n° 337 (mesure sur 290 ports de CA) : 16 hex principaux de terre + 3 hex de
    Port consécutifs de l'anneau 2, deux en mer et un sur la plage ; la Saison garde ses ports [mer, mer, mer], validés
    en jeu (décision de Charles, 04.10). La règle de méthode (exemple de CA d'abord) reste valable.]

46. `[evitable]` **Oublier de relancer tous les exports apres un changement de carte.** J'ai
    enchaine des `process --map-data` seuls, alors que notre `GUIDE.md` § 10 dit : « tout
    changement impose de tout retraiter ». `pathfinding.ppd` et `trade_routes.ptd` dataient de la
    veille. -> **Regle : apres toute modification de couche, `process --all`.**

### B. Decouvertes

- **Modele d'un emplacement de colonie dans Warhammer 3**, lu dans la carte source de CA : disque
  hexagonal parfait de rayon 2 (19 hex), dont le centre est la position logique de la colonie
  (`SETTLEMENT_INFO` de `map_data.esf`). Colonie interieure : 19 hex en emplacement principal.
  **Colonie portuaire : 16 hex en principal, tous sur terre, et 3 hex consecutifs du second anneau,
  cote mer, en emplacement de port** (chez CA deux sur terre, un en mer dans la region de mer).
  [Corrigée le 04.10.2026 par n° 337 : chez CA, deux hex de port en mer et un sur la plage ; la Saison garde ses
  ports [mer, mer, mer], validés en jeu (décision de Charles, 04.10).]
  L'etalement couvre exactement les 19 hex. Sans ce disque, MapDataBuilder ecrit la position
  `0xFFFF` et l'IA de campagne du jeu meurt a `Warhammer3+0x2A4401A` sur la coordonnee
  `0xFFFFFFFF`. Code : `recentrer_emplacements.py`.
- **La generation du startpos lit la minicarte** declaree dans `campaign_map_playable_areas.radar_file`
  (sous `campaign_maps\<carte>\`), apres avoir construit tout le monde de campagne. Fichier
  absent -> objet image nul -> plantage `Warhammer3+0x3211033`.
- **Le jeu ecrit le startpos en ESF `0xABCB`**, enveloppe et contenu compresse (LZMA1 brut,
  proprietes `5d 00 00 04 00`), alors que CA livre les siens en `0xABCA`.
- **Tous les entiers sur trois octets de l'ESF sont en gros-boutien**, chez CA comme chez nous
  (verifie sur la taille decompressee des deux startpos et sur les comptes d'hex).
- **Commandes de script du jeu utiles au test** (relevees dans `Warhammer3.exe`, table des
  commandes de `CliCommands.cpp`) : `take_custom_screenshot <fichier> <largeur> <hauteur>`,
  `game_startup_mode <battle|campaign|campaign_edit|frontend|naval>`, `all_players_ai`, et les
  reglages `x_res`, `y_res`, `x_pos`, `y_pos` applicables pour une seule session.

## Session du 21.09.2026 (12 h 15 - 13 h 15) - l'ecran de selection

### A. Erreurs de methode

47. `[evitable]` **Injecter les textes d'un autre jeu sans les filtrer contre ceux du jeu cible.**
    `injecter_textes.py` a pose 3 590 textes de Warhammer 1 dans notre pack ; 2 772 de ces cles
    existent dans Warhammer 3 (unites, competences, batiments, effets des Elfes sylvains). Comme le
    jeu charge les `.loc` d'un mod quelle que soit la langue, notre pack remplacait les textes a
    jour de Warhammer 3 par ceux de Warhammer 1, **en francais pour tout le monde**, et jusque dans
    les Empires Immortels si le mod etait active. -> **Regle : un mod ne pose que les cles que le
    jeu ne connait pas ; toute cle du jeu est laissee au jeu, qui la fournit dans chaque langue.**
    Code : `injecter_textes.py` retire les 243 424 cles relevees dans `local_en.pack` et
    `local_fr.pack` (`cles-vanilla-wh3.txt.gz`, `--vanilla` pour la refaire).

48. `[evitable]` **Recopier une valeur d'une autre campagne au lieu de celle de la carte d'origine.**
    `preview_width` x `preview_height` valaient 256 x 256, recopies du prologue, alors que
    Warhammer 1 donnait 472 x 600 pour cette carte (les proportions du parchemin) ; les fiches de
    seigneur etaient celles des Empires Immortels alors que Warhammer 1 avait des fiches propres a
    la mini-campagne. Meme famille que la regle 45. -> **Regle : pour chaque ligne de la base,
    partir de la ligne de Warhammer 1 de cette campagne quand elle existe ; ne prendre chez CA
    (Warhammer 3) que ce que Warhammer 1 n'avait pas (colonnes nouvelles, assets presents).**
    [Codée le 04.10.2026 par n° 332 (rechute : 256 × 256 en dur dans `declare_map.py`) : aperçu au rapport du monde,
    hauteur 600. Hiérarchie des gabarits fixée le 04.10.2026 (avec n° 53 et 331) : contenu = ligne de WH1 ; ligne
    `campaigns` ou zone jouable d'une carte neuve = ligne de la Saison, champ par champ ; convention de moteur absente
    des deux = CA.]

49. `[evitable]` **Deviner ce que l'interface lit au lieu de lire sa mise en page.** Les images de
    la vignette (`_button`, `_vertical`), la cle du titre (numero de la zone jouable) et la source
    de l'onglet Carte (`RadarImagePath`) sont ecrits en toutes lettres dans
    `ui/frontend ui/campaign_select_new.twui.xml`, extrait en une commande. -> **Regle : pour un
    ecran du jeu, extraire son `.twui.xml` et y chercher les `context_function_id` avant de
    toucher aux donnees.**

### B. Decouvertes

- **L'ecran Nouvelle campagne** (mise en page `campaign_select_new.twui.xml`) : image
  `frontend_image` en fond plein ecran, plus `<nom>_button.png` (278 x 128) et
  `<nom>_vertical.png` (380 x 735) par suffixe ; titre et description sous
  `campaign_map_playable_areas_onscreen_name_<index>` et `..._onscreen_description_<index>` ;
  onglet Carte = `radar_file` ; liste triee par `sort_order`.
- **Le jeu charge les `.loc` d'un mod quelle que soit la langue du joueur** (confirme par les outils
  de traduction de la communaute). Deux langues = deux packs ; le second, qui ne contient que son
  `.loc` **sous le meme chemin** que le premier, le masque quand il passe devant dans l'ordre de
  chargement (`!` en tete du nom).
- **`start_pos_starting_general_options`** relie un personnage du startpos a une fiche de
  `frontend_faction_leaders` ; sans elle, aucun seigneur n'est choisissable. La cle d'une fiche est
  libre : une campagne peut avoir ses propres fiches (Warhammer 1 le faisait pour ses
  mini-campagnes).
- **La generation du startpos grave un apercu de la minicarte** (`SAVE_GAME_HEADER` > `MAPS`, RGBA)
  a la taille `preview_width` x `preview_height` : regenerer le startpos apres tout changement de
  minicarte ou de ces deux colonnes.
- **Format des images de correspondance de Warhammer 3** : TGA a palette, 16 bits par pixel,
  palette BGRA 32 bits, origine en bas ; minicarte parchemin RGBA a la moitie de la resolution,
  correspondance de la minicarte au quart.
- **`start_pos_factions_description_<ID>`** porte la description de chaque faction de depart.

## Session du 21.09.2026 (13 h 15 - 13 h 50) - phase 3, le terrain

### B. Decouvertes (detail : `05-journal\2026-09-21-phase-3-terrain\terrain.md`)

- **Le terrain de campagne compile n'a pas le meme format dans WH1 et WH3** (maillages et carte
  R16 contre carte pleine BC6H et plan logique) : on ne recopie pas, on refait un projet Terry.
- **Hauteurs de WH1** : `lf_height_map.dds` en R16, ligne 0 au nord, hauteur =
  0,0002185272 x v - 0,753375 (etalonne sur les 614 484 sommets des maillages, ecart moyen 0,38).
  `global_blend.dds` de WH1 est, lui, range du sud vers le nord : **chaque image a son
  orientation, a prouver une par une** (hauteurs : la mer au minimum ; melange : les marais).
- **Dans un projet Terry de campagne, la mer est declaree par `tile_map.png`** (type de tuile
  `sea`, couleur (83, 141, 213)), pas par la hauteur ; plan d'eau a 0 ; `sea_height` = fond sous
  l'eau. La legende des couleurs est dans `_tile_database\_settings.bin`, et elle contient des
  tuiles de riviere en maillage (`river_mesh`...) : BOB fabrique les rivieres 3D.
- **`blend.tif` = numero de texture de WH3** (identique a 99,66 % au melange compile).
- Tous les rasters suivent 8 px par hex **plus 4 lignes** (3200 x 3524 pour 400 x 440).

## Session du 21.09.2026 (14 h 40 - 16 h 40) - phase 3, BOB ne compilait pas le relief

### A. Evitables

50. `[evitable]` **Essayer des fichiers au hasard quand un outil de CA « ne fait rien » sans
    erreur.** Pendant une heure : `lf_heights.tif`, `climate_map.png`, reimport des hauteurs par
    Terry, cases de reglage... Aucun ne pouvait marcher : BOB ne cree pas les actions lourdes d'une
    campagne absente de SA base. Le temoin (le projet de ChaosRobie sous un autre nom) et la lecture
    de la DLL l'ont montre en vingt minutes. -> **Regle : 1) temoin avec un projet connu pour bon ;
    2) capturer la commande exacte ; 3) lire la condition dans la DLL (chaine -> code -> fonction ->
    appelant) et la verifier sous `cdb` ; seulement ensuite toucher aux fichiers.** Code :
    `02-scripts\lire_dll.py` (refs, fonction, vtable, annoter).

51. `[evitable]` **Laisser Terry ouvert pendant qu'on ecrit dans `working_data`.** Terry surveille
    ce dossier et verrouille les packs qu'on y pose : RPFM n'a pas pu y enregistrer, et un essai de
    pack a ete fausse (le pack ne se deplacait plus). -> **Regle : fermer Terry avant d'ecrire dans
    `working_data` ou d'y lancer BOB.** Code : `compiler_terrain_bob.py` refuse de tourner si
    Terry est ouvert.

### B. Decouvertes (detail : `05-journal\2026-09-21-phase-3-terrain\terrain.md` § 7)

- **BOB ne compile le terrain d'une campagne que si le nom du dossier de terrain est dans la table
  `campaign_map_playable_areas` de SA base**, qui est celle du jeu (`db.pack`, 10 zones, 3
  campagnes) : ni les XML du kit, ni `working_data\db`, ni un pack (mod, Release ou Patch, dans
  `working_data` ou `data`) n'y ajoutent de ligne. Sinon : action d'erreur muette, et seulement
  Terry file + 5 masques. Preuve : bob_terrain+0x29189 (`record_from_name`) renvoie 0 sous `cdb` ;
  le projet des Empires copie sous un autre nom echoue pareil. **Contournement : `compiler_terrain_
  bob.py`** fournit l'enregistrement (minx, maxx du kit) au retour de la recherche.
  [Décision de Charles, 04.10.2026 : BOB sous `cdb` (`compiler_terrain_bob.py`) est gardé et assumé comme méthode de
  l'atelier (seule voie connue pour une carte neuve), malgré les guides de l'Atlas (« on ne contourne pas les outils de
  CA ») ; à écrire franchement dans les guides. Voir aussi n° 220 et 311.]
- **Commande de Terry pour BOB** : `BOB.modder.x64.exe /dont_stop_on_error /nosplashscreen
  /get_latest_rules -no_console /offline /configuration:_terry_auto /workspace:
  "/changelist:Terry (<.terry>)"`, configuration dans `binaries\BOB\_terry_auto_configuration.xml`.
- **Terry n'ouvre un projet en vue 3D que si un terrain compile existe** dans le dossier cible
  (sinon plantage) ; ouvrir avec « 3D View » decoche, ou amorcer avec un terrain compile.
- BOB lit `binaries\bob_project.script.txt` et `project.script.txt` s'ils existent ; une ligne
  `mod <pack>;` y fait planter BOB au demarrage.

## Session du 21.09.2026 (16 h 30 - 17 h 55) - phase 3, terrain compile complet

### A. Evitables

53. `[evitable]` **Recopier la cle neuve dans un champ qui designe une chose existante
    (`startpos_map`), et empiler les changements du startpos sans essai en jeu entre eux.** Le
    jeu plantait au tout debut du chargement (`+0x27A7DFF`, recherche qui rend nul). Les fiches
    neuves d'Old World valent toutes `default` : il suffisait de regarder un mod qui marche. Et
    trois startpos (12 h 32, 12 h 38, 13 h 07) ont ete produits sans qu'aucun soit charge en jeu,
    si bien que le plantage est arrive en meme temps que le terrain et l'a d'abord fait
    soupconner. -> **Regles : 1) pour toute colonne qui nomme une autre chose (variante, carte,
    fichier), prendre la convention d'une campagne neuve qui fonctionne (Old World), jamais notre
    propre cle par symetrie ; 2) un seul changement de fond entre deux essais en jeu.** Code :
    `ajouter_seigneurs_jouables.py` (`STARTPOS_MAP = "default"`, corrige aussi les fiches deja
    creees). **Ce n'etait pas la cause du plantage : voir 55.**
    [Règle 1 précisée le 04.10.2026 (avec n° 48 et 331) : contenu = ligne de WH1 ; ligne `campaigns` ou zone jouable
    d'une carte neuve = ligne de la Saison, champ par champ ; convention de moteur absente des deux = CA (une campagne
    neuve qui marche).]

52. `[evitable]` **Conclure « pas de plantage » sur un essai interrompu trop tot.** Un essai
    ralenti par mes points d'arret n'avait pas plante au bout de 4 min ; je l'ai arrete et j'ai
    cru a un probleme de concurrence. Relance jusqu'au bout : meme plantage. -> **Regle : un essai
    ne conclut que s'il va a son terme (code de sortie, fichier ecrit ou plantage) ; sinon il ne
    prouve rien.**

### B. Decouvertes (detail : `05-journal\2026-09-21-phase-3-terrain\terrain.md` § 7.6 a 8)

- **« Generate Camera Height Map » fait planter BOB** : DirectX refuse la surface d'affichage en
  mode flip (`0x80070005`), repli en mode classique, puis appel d'un pointeur nul. Le fichier est
  indispensable (toutes les cartes de CA et Old World le livrent) : `camera_heightmap.py` le
  fabrique (PNG 16 bits, texte `height_scale`, `tile_map` / 4, maximum des hauteurs par bloc de
  16 px, 1,03 en mer ; recette relevee sur les Empires).
- **Pour une campagne, BOB ne produit pas `lf_normal.dds`** ; celui de WH1 se reprend tel quel
  (conseil de ChaosRobie) **en inversant le vert** : X (alpha) de meme signe, Y (vert) de signe
  oppose entre WH1 et WH3 (correlation avec les pentes : +0,70 contre -0,74). Inversion exacte
  dans les blocs DXT5 (g -> 63 - g). Script : `lf_normal_wh1_vers_wh3.py`.
- **Sens de rangement par fichier compile** : `full_height_map.dds` du sud au nord (correlation
  0,91 retourne) ; `lf_normal.dds` et `camera_heightmap.png` du nord au sud, comme les rasters de
  Terry. Chaque fichier a son sens : le verifier par correlation, un par un.
- **ChaosRobie** : campagnes de DLC de WH1 = question de droits (DLC requis et verification a
  l'ecran de selection si publication) ; rivieres par les tuiles de WH1 (pas les splines) ;
  relief et normal map de WH1 repris tels quels.

## Session du 21.09.2026 (18 h 15 - 19 h 30) - le plantage au chargement de la campagne

### A. Evitables (detail : `05-journal\2026-09-21-phase-3-terrain\plantage-chargement.md`)

54. `[evitable]` **Ecarter des lignes sur une verification fausse : « WH3 ne declare aucun gabarit
    d'emplacement pour ses regions elfes ».** Phase 2 : les 36 lignes des 18 regions d'Athel Loren
    ont ete ecartees (« 0 ligne pour les 15 regions wef de WH3 »). Faux : l'Empire Immortel en
    declare pour chacune de ses regions de foret (`wh_main_special_waterfall_palace_primary` pour
    huit d'entre elles, gabarits propres pour le Chene des Ages, la Cascade, Crag Halls, l'Enclume
    de Vaul, Yn Edryl Korian). Resultat : 18 colonies **sans aucun emplacement** ; le startpos se
    generait sans erreur et le jeu plantait des le debut du chargement (`Warhammer3.exe+0x27A7DFF`,
    lecture de 0x30 : il cherche l'emplacement `primary` d'une colonie et n'en trouve pas).
    -> **Regles : 1) « CA n'en a aucun » s'ecrit avec la requete qui le prouve et un contre-essai
    par une autre entree (ici chercher par le lieu, `oak_of_ages`, et pas par la faction) ;
    2) ne jamais ecarter une ligne sans la remplacer : une ligne absente est un manque, pas une
    simplification.** Code : `build_correspondances.py` (`SLOT_ELFES`, `SLOT_PAR_REGION`, plus
    aucun « a ignorer ») ; controle generique `comparer_structure_esf.py`, qui retrouve seul ce
    defaut dans l'ancien startpos (4 anomalies, toutes des emplacements, rien d'autre).

55. `[evitable]` **Corriger un plantage sur une conjecture (entree 53).** J'ai attribue le
    plantage a `startpos_map` parce que c'etait la difference entre le seul startpos charge et les
    suivants ; apres correctif, meme plantage a la meme adresse (essai de Charles, 18 h 11). La
    convention `default` reste juste, mais le diagnostic ne l'etait pas. -> **Regle : avant de
    corriger un plantage, lire dans le vidage ce que le code cherchait (chaine ou cle comparee par
    la fonction qui rend nul) ; une difference entre deux fichiers n'est qu'une piste.** Methode :
    `cdb -z <vidage>` puis `u` sur la fonction de recherche et son predicat ; chaines lues dans
    l'exe sur disque (`lire_dll.py refs`, `chaines_de_fonctions.py`).

56. `[evitable]` **Conclure « Warhammer3.exe est protege, aucune reference aux chaines » a partir de
    mon propre outil.** `lire_dll.py` ne balayait que la section nommee `.text` ; dans
    Warhammer3.exe elle fait 512 octets, le code est dans `.sbss` (50 Mo) et `.shared` (160 Mo),
    noms brouilles. -> **Regle : un outil qui ne trouve rien prouve d'abord qu'il regarde au bon
    endroit (taille de ce qu'il a lu).** Code : `lire_dll.py` balaie toutes les sections
    executables (`codes`, `code_de`) ; `chaines_de_fonctions.py` suit.

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 42 a 45)

- **Le jeu exige un emplacement `primary` par colonie au chargement**, et la generation du
  startpos ne le verifie pas. Signature : `+0x27A7DFF`, apres la recherche `+0x2726890` dont le
  predicat `+0x272943C` compare le type d'emplacement a « primary » (`+0x328DAB0`).
- **Le startpos est compresse** : bloc `COMPRESSED_DATA` = LZMA « alone » (proprietes et taille dans
  `COMPRESSED_DATA_INFO`). Une fois decompresse, sa structure se compare a celle d'un startpos qui
  charge (Old World) : `comparer_structure_esf.py`.
- **Le Chene des Ages n'a aucun emplacement secondaire, par construction** : chaine
  `wh_dlc05_wef_oak_of_ages`, `active_slot_count` 0 a tous les niveaux
  (`campaign_building_chain_slot_unlocks`). Colonie elfe majeure : 3, 5, 6, 8, 9 selon le niveau.
- **Gabarits des regions de foret de WH3** : principal = jeu de chaines
  `wh3_main_primary_core_special_major_forest` (colonie elfe seulement), porte par cinq gabarits
  identiques. ~~les batiments elfes de base sont permis partout ; le secondaire n'ajoute que
  garnison, monument et ressource.~~ **Faux, corrige a 21 h (erreur 60)** : les batiments elfes
  viennent du secondaire, jeu `wh3_main_secondary_core_generic_major_variant_wef_forest`.

## Session du 21.09.2026 (19 h 15 - 20 h 35) - la campagne se charge en jeu

### A. Evitables (detail : `05-journal\2026-09-21-phase-3-terrain\plantage-chargement.md` § 6 a 8)

57. `[evitable]` **Traduire les groupes d'IA de Warhammer 1 par une table, sans verifier qu'ils
    contiennent une personnalite.** `wh_dlc03_group_beastmen_waaagh` -> 
    `wh3_combi_personality_group_beastmen_brayherd`, groupe qui existe mais **vide** (0 ligne dans
    `cai_personality_group_junctions`) : plantage au chargement (`+0x27A863F`, lecture de
    `[0+0x200]`, la personnalite de la faction). La meme table laissait `default` a 20 factions (la
    personnalite la plus pauvre). -> **Regle : le groupe d'une faction est celui que CA lui donne
    dans l'Empire Immortel, sinon le groupe mineur de sa culture ; un groupe sans personnalite est
    une erreur.** Code : `groupes_ia.py` (regle), `corriger_groupes_ia.py` (24 factions corrigees),
    `declare_campaign.py` l'emploie.

58. `[evitable]` **Essayer en jeu un startpos regenere sans reconstruire le pack.** Le startpos du
    pack passe **devant** la copie en vrac de `<jeu>\data\campaigns\...` : deux essais sous
    debogueur ont tourne sur l'ancien startpos (celui de 18 h 45), et j'ai cru que la correction des
    groupes ne marchait pas. -> **Regle : startpos regenere -> copie dans le projet -> `build_pack.py`
    -> seulement ensuite l'essai ; les copies en vrac se retirent de `data\` pour un essai propre.**
    Note dans `build_pack.py`.

59. `[evitable]` **Commande temoin du startpos sans `process_campaign_ai_map_data`.** Old World livre
    `hlp_data.esf` et `spd_data.esf` dans le dossier de sa carte ; nous non. Sans eux, le chargement
    de l'IA de campagne s'arrete **sans erreur** avant de relier ses factions, et le jeu plante des le
    reglage du joueur humain (`+0x255EF20`, `rcx = 2` : l'identifiant de la faction d'Orion au lieu
    de son adresse). -> **Regle : generer le startpos avec `--ai-map-data` et embarquer les deux
    fichiers.** Code : `build_pack.py` les embarque et previent s'ils manquent ; commande du temoin
    corrigee dans `CLAUDE.md`.
    [Complétée le 04.10.2026 par n° 331 : la génération n'écrit `hlp_data.esf` / `spd_data.esf` que si le dossier
    `data\campaign_maps\<carte>\` existe ; le créer avant de générer.]

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 46 a 49)

- **Donnees de carte de l'IA** : `campaign_maps\<carte>\hlp_data.esf` et `spd_data.esf`, ecrits par le
  jeu quand le script de generation contient `process_campaign_ai_map_data;` (16 s, 5 et 9 Mo ici).
  Le chargement de CAI_INTERFACE les ouvre (`+0x29A29F0`, `+0x29A272C`) et, s'ils manquent, sort sans
  lancer la resolution de CAI_WORLD.
- **Resolution de l'IA** : les CAI_FACTION lues du startpos gardent l'identifiant de leur faction
  jusqu'a `CAI_WORLD::resolve` (`+0x26EFE2C`, vtable +8), qui enchaine theatres, factions, regions...
  et abandonne au premier echec.
- **Debogueur sur le jeu** : `debug_chargement.py` lance Warhammer 3 sous `cdb` avec des points
  d'arret qui ecrivent et continuent ; dans un processus vivant le module s'appelle
  `warhammer3_retail_x64` (dans un vidage relu, `Warhammer3`). Charles fait le chemin dans le menu.
- **Le pack passe devant les fichiers en vrac** de `<jeu>\data\` pour un meme chemin (startpos).

## Session du 21.09.2026 (20 h 40 - ) - fidelite : diplomatie, batiments, carte

### A. Evitables

60. `[evitable]` **Remplacer un gabarit d'emplacement par un autre sans comparer ce qu'ils
    permettent.** Correctif de l'erreur 54 : les secondaires elfes de WH1 sont devenus
    `wh_main_human_major_secondary[_ressource]`, sur la foi d'une lecture non verifiee (« les
    batiments elfes de base sont permis partout, jeu de chaines sans nom »). Leur jeu
    `wh3_main_secondary_core_generic_major` ne donne aux elfes sylvains que les **avant-postes** :
    dans 14 regions d'Athel Loren sur 18, ni armurerie, ni archers, ni croissance. Le jeu chargeait,
    l'erreur ne se voyait qu'en jouant. -> **Regle : une correspondance de gabarit WH1 -> WH3 se
    valide en comparant, region par region, les chaines permises des deux cotes (superchaines de WH1,
    jeux de chaines de WH3) ; « le jeu charge » ne valide pas les regles de jeu.** Code :
    `comparer_batiments_wh1_wh3.py` (controle), `declarer_gabarits_elfes.py` (secondaires elfes
    majeurs de WH1 recrees sous leurs cles avec la recette de foret de WH3, plus deux gabarits propres
    pour l'Enclume de Vaul et Threllock).

61. `[evitable]` **Affirmer une infidelite a WH1 d'apres le nom d'une region.** J'ai ecrit a Charles
    « l'arbre de Threllock est rattache a l'Enclume de Vaul comme dans l'Empire Immortel, alors que
    notre carte a une region Threllock » ; Charles m'a demande de le corriger. Les tables de WH1 disent
    autre chose : ses dix batiments uniques (4 offices, 2 temples, 4 arbres) etaient permis dans
    **toute** colonie elfe majeure (superchaines des gabarits `wh_dlc05_elf_major_secondary*`), et la
    region Threllock, colonie mineure, ne pouvait pas porter l'arbre. (J'ai d'abord ajoute « un
    exemplaire chacun, `building_instances` » : faux aussi, c'est une limite **par colonie**, 1 426
    batiments ordinaires sur 1 431 y valent 1.) -> **Regle : un ecart de fidelite s'enonce avec les
    lignes de WH1 qui le prouvent (gabarit, superchaine, jonction), jamais d'apres un nom ; le sens
    d'une colonne se verifie sur ses autres lignes avant de l'invoquer.** Suite : Charles veut les
    regles de WH3 pour les batiments (21 h) ; l'arbre de Threllock devient le monument de notre region
    Threllock (`declarer_gabarits_elfes.PROPRES`).

62. `[evitable]` **Recidive : du Python passe par un heredoc Bash avec des `\n` dans ses chaines.**
    Le script qui reecrivait `comparer_batiments_wh1_wh3.py` a produit de vrais retours a la ligne
    dans deux f-strings (SyntaxError, vue a l'execution suivante, rien d'autre d'abime). La regle
    existait. -> **Regle, rappelee : tout Python qui contient un antislash s'ecrit dans un fichier
    (outil Write/Edit), jamais dans un heredoc.** Recidives le meme soir (22 h : un heredoc et un
    `python -c` avec `'\\'`) : sans degat, mais la regle vaut aussi pour `python -c`.

63. `[evitable]` **Peindre les routes dans `tile_map.png` sans avoir releve la grammaire de CA.** J'ai
    aminci les hex de route en lignes d'un pixel ; BOB a laisse **2 872 trous** (« area painted in tile
    map likely doesn't match the tile shape »). La grammaire des Empires, relevee ensuite en cinq
    minutes : chaque hex de route est un bloc 2 x 2 plein (30 283 sur 30 400). -> **Regle : avant de
    produire un format, en mesurer la grammaire sur l'exemple de CA (motifs par hex, longueurs de
    segments) ; les avertissements de BOB se comptent apres chaque compilation.** Code :
    `terrain_wh1_vers_terry.routes`.
    **[Corrigée le 27.09.2026 : ne jamais peindre ni retoucher `tile_map.png` à la main ; l'exporter
    depuis CAIME (Tools → Export → Baseline Tilemap). Pour WH3, l'export place un bloc 2 × 2 `roads`
    (93, 66, 24) par hex de route retenu après priorité de la mer et des falaises côtières
    (`BaselineTilemapExporter.cs`).]**
    [Décision de Charles, 04.10.2026 : la `tile_map.png` de la Saison, peinte par script
    (`terrain_wh1_vers_terry.py`), est laissée telle quelle (côtes C1 à C4 validées en jeu) ; l'export CAIME est la
    règle pour toute carte neuve (Expanded comprise).]

64. `[evitable]` **Un generateur qui supprime l'ancien projet avant d'avoir tout calcule.**
    `terrain_wh1_vers_terry.py` sauvegardait puis effacait le projet Terry, puis calculait les objets ;
    un controle qui echouait (calage des objets, 21 h 46) a laisse un projet a moitie ecrit (rasters
    sans `.terry` ni calques). Sauvegarde intacte, projet regenere a 21 h 53. -> **Regle : tout calcul
    et tout controle avant la premiere ecriture destructive.** Code : les objets sont calcules en tete
    de `ecrire_projet`.

65. `[evitable]` **Effacer un element visuel de WH1 en le prenant pour un defaut.** Les taches blanches
    de la capture de 20 h 38 etaient la **clairiere d'hiver** de la Saison des Revelations (textures de
    neige de WH1 + arbres d'hiver `wef_win_*` au meme endroit) ; je les ai converties en eboulis
    (21 h 05) et j'ai traduit les arbres d'hiver en arbres ordinaires. Charles (22 h 50) : « des
    endroits de la foret sont tout enneiges, la ils ne le sont pas ». -> **Regle : avant de
    « corriger » une bizarrerie, verifier ce que WH1 montre a cet endroit (textures, arbres, objets) ;
    un element de WH1 mal rendu se re-rend a la maniere de WH3 (masque de neige), il ne se supprime
    pas.**

66. `[evitable]` **Une regle de visibilite des objets deduite sans controle sur le contenu.** « Un objet
    present dans toutes les variantes de sa case est visible de tous » : dans les cases qui n'ont que
    des variantes sombres (devastation, Chaos, corruption), **5 277 decors du Chaos** (fissures, pics,
    cranes, tumeurs, lave) sont devenus permanents. Charles : « il n'y avait pas le Chaos a l'epoque ».
    -> **Regle : une regle de visibilite se valide par la part de decors sombres de ce qu'elle rend
    permanent (audit des calques ecrits) ; seul le decor naturel (bit 0) est permanent.**

67. `[evitable]` **Livrer un visuel sans l'avoir regarde.** Substituts WH3 a la place des modeles de
    WH1, visibilite, neige : tout etait controle par des chiffres (0 trou, ecarts de hauteur), rien par
    l'image. Charles : « je ne reconnais pas la map ». -> **Regle : aucun visuel ne part sans une
    verification a l'image (Terry de WH3, vue 3D, accord de Charles du 21.09.2026) face a une
    reference de WH1 (captures de Charles dans WH1).** Et : la fidelite passe par les modeles de WH1
    eux-memes quand le moteur les lit (WH3 lit RMV2 v7 : 41 % de ses propres modeles), les substituts
    n'en sont qu'un dernier recours annonce.

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 50 a 53)

- Recette des secondaires de foret de WH3 (garnison + foret + ressource + monument) ; un mauvais
  gabarit ecarte aussi, sans rien dire, les batiments de depart de la colonie.
- `building_instances` : limite par colonie.
- La diplomatie de depart se lit dans le startpos (`war`, `NON_AGGRESSION_PACT`, postures de l'IA).

### C. Decouvertes de la carte (reportees dans `GUIDE.md` § 15, n° 54 a 60)

- Arbres : la palette de `tree.tif` est la table `campaign_tree_ids` ; l'apparence suit la culture
  proprietaire (`campaign_tree_type_cultures`) ; `trees.png` de WH1 se traduit famille par famille.
- Routes : un bloc 2 x 2 plein par hex. Rivieres des Empires : chenaux « mer » bordes de cote ou de
  falaise, ou modeles poses comme objets ; une seule tuile de riviere classique dans WH3.
- Objets de WH1 : lots BMD v21 par region, case et variante ; z en espace des hex (× √3/2 pour le
  monde) ; convention d'angles de Terry Rx(-rx)·Ry(-ry)·Rz(-rz) ; 335 modeles de WH1 sur 519 absents
  de WH3 sous leur chemin ; modeles WH1 = RMV2 v7 (speculaire), WH3 = v8 (PBR).

## Session du 22.09.2026 (12 h 30 - ) - le plantage de fin de tour, le terrain de bataille

### A. Evitables (detail : `05-journal\2026-09-22-phase-4\plantage-fin-de-tour.md`)

68. `[evitable]` **Declarer une campagne sans livrer ce que designe chacune de ses colonnes :
    `terrain_folder`.** La comparaison des familles de fichiers avec CA (21.09.2026) couvrait
    `campaign_maps\<carte>\` et `terrain\campaigns\<carte>\`, pas `terrain\battles\<dossier>\`, que
    `campaign_map_playable_areas.terrain_folder` designe et que **toutes** les campagnes de CA livrent
    (12 fichiers, carte des lieux de bataille comprise). Le jeu y lit le masque des lieux de bataille a
    la premiere bataille terrestre : l'essai de Charles du 21.09.2026 a plante a la fin du tour 1
    (22 h 20, `Warhammer3.exe+0x1497949`). -> **Regle : chaque colonne de la zone jouable qui nomme un
    fichier ou un dossier a son pendant chez CA, et le notre doit contenir la meme famille de
    fichiers.** Code : `build_pack.verifie_fichiers_declares` controle les 9 fichiers de
    `terrain_folder` ; recette `dossier_bataille_campagne.py` + `compiler_terrain_bob.py --bataille`.

69. `[evitable]` **Ne pas relire `crash_report\` apres un essai de Charles.** Il n'a pas signale le
    plantage de 22 h 20 ; je ne l'ai trouve que le lendemain, par hasard, en cherchant autre chose
    (vidage `D2026-09-21_T22-20-07.mdmp`, sauvegarde automatique de 22 h 19). -> **Regle : a chaque
    reprise, lister ce que `crash_report\` et `save_games\` ont de plus recent que le dernier essai, et
    passer chaque vidage a `lire_vidage.py`, meme si Charles n'a rien dit.**

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 63 a 66)

- Le terrain de bataille d'une campagne : un terrain « porteur » a la taille de la carte de tuiles,
  couvert d'une seule tuile factice (`dummy_set_bca_gen\dummy_4_x_4`), un seul climat (`default` aux
  Empires), plat (`lf_normal` a un seul bloc distinct chez CA) ; BOB le compile par sa branche
  « bataille », et ecrit la carte des lieux de bataille si `save_meta_data_map` est vrai.
- Le choix des cartes de bataille (champ, siege) passe par les cartes de captage peintes et les tables
  `battle_catchment_override_*`, dont chaque ligne cite le dossier de bataille de sa campagne
  (`battle_path`) : sans elles, notre campagne n'a pas encore de cartes de bataille choisies par lieu.
- Le startpos de WH3 ne porte aucun etat d'exploration (`CAMPAIGN_SHROUD`) ; celui de WH1 en avait
  un pour les deux factions jouables. Ce qui etait explore au depart dans WH1 se refait par script.

## Session du 22.09.2026 (14 h 40 - ) - Terry : le sol qui ne se dessine pas

### A. Evitables (detail : `05-journal\2026-09-22-phase-4\terry-trous.md`)

70. `[evitable]` **Une regle de taille tiree d'une seule carte de CA.** Le 20.09.2026, j'ai ecrit au
    guide (§ 12.1) « `PatchVisibilityMask` : une case par 7,68 unites du monde », tire des seuls
    Empires (961,3 / 125), et le generateur a donne 34 x 38 a notre projet. La vraie regle est celle
    de la grille des parcelles que BOB compile (`patch_mask.dds`) : parcelle de
    plafond(plus grand cote de la carte de tuiles / 128) px, soit 114 x 125 chez nous. Terry ne
    dessinait le sol generique que sur les 34 x 38 premieres parcelles : ailleurs, seules les tuiles
    de route, et le ciel au travers (« boursoufle », Charles, 22.09.2026). Le prologue (123 x 92 pour
    1 600 x 1 201 px) contredisait la regle des 7,68 : il suffisait de la confronter a une deuxieme
    carte. -> **Regle : une regle de taille ou de proportion se verifie sur au moins deux cartes de CA
    (Empires et prologue) et contre ce que BOB compile pour la notre, avant d'etre codee.** Code :
    `terrain_wh1_vers_terry.grille_parcelles` et `controle_pvm` (refuse de generer si la grille
    differe du `patch_mask.dds` compile). J'ai aussi perdu une heure a corriger des fichiers compiles
    (hauteurs du brouillard, taille des normales, drapeaux des parcelles) pour un defaut d'affichage
    de Terry sans avoir d'abord etabli ce que Terry lit pour dessiner le sol : le projet (`.terry` et
    ses calques), pas seulement `working_data`.

71. `[evitable]` **Recidive de l'erreur 62** (22.09.2026, vers 14 h) : un script Python passe par un
    heredoc Bash, avec des antislashs dans un chemin. Sans degat (erreur de syntaxe), script ecrit
    dans un fichier. La regle tient ; c'est son application qui a manque.

72. `[evitable]` **Reprendre une famille de fichiers de WH1 sans relever comment le moteur trouve ses
    dependances.** `fichiers_wh1.Relocateur` suivait les chemins **cites** par chaque fichier. Un modele
    de decalque (576 octets, materiau 100) n'en cite aucun : il donne un chemin de base, auquel le
    moteur ajoute des suffixes, differents dans les deux jeux (`_diffuse` dans WH1, `_base_colour` dans
    WH3). Aucune texture de decalque n'avait ete reprise : les 430 decalques propres a WH1 s'affichaient
    en carres opaques (de la terre dans la neige), les 2 103 autres prenaient les textures de WH3.
    -> **Regle : avant de reprendre une famille de fichiers (modeles, decalques, arbres, tuiles), poser
    cote a cote la liste des fichiers d'un element chez CA et chez WH1, et verifier que la reprise livre
    l'equivalent de chacun.** Code : `decalques_wh1.py` (conversion aux noms de WH3), appele par
    `Relocateur` pour tout modele de materiau 100.

73. `[evitable]` **Mesurer les objets de WH1 avec leur z brut.** Pour comparer la hauteur des objets au
    sol, j'ai d'abord lu `lire_props_wh1.objets` directement : z y est dans l'espace des hex, il faut
    × √3/2 (GUIDE § 15, n° 60, et `props_wh1_vers_layers.Z_HEX_VERS_MONDE`). Résultat faux (un quart des
    objets « sous le sol » de plus d'une unité), vingt minutes perdues. -> **Regle : les positions des
    objets de WH1 se prennent toujours par `props_wh1_vers_layers.objets_uniques()`, jamais par le
    lecteur brut.**
    **[Remplacée par l'erreur 89 : les positions des entités ne se convertissent jamais ; seuls les rasters se lisent à z × √3/2 (`Z_VERS_RASTER`).]** [25.09.2026, ménage]

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 70 a 78)

- `PatchVisibilityMask` : une case par parcelle de terrain, 255 = parcelle dessinee (tout a 255
  aux Empires). Terry s'en sert pour dessiner le sol ; hors de la grille declaree, le sol manque.
- Le bit 0x40 de `patch_mask.dds` marque les parcelles qui contiennent des tuiles speciales (routes,
  cotes, falaises) : 70 % aux Empires, 15 % chez nous (le reseau des routes). 0x10 terre, 0x20 mer.
- `shroud_heights.dds` (R32F, moitie de la resolution du relief, rangee du sud vers le nord) =
  max 2 x 2 du relief + calque `HeightShroud` ; BOB l'ecrivait plat a 1,0 (`shroud_heights.py`).
- `lf_normal.dds` a la taille de `full_height_map.dds` (4 x la carte de tuiles), jamais le double
  (`lf_normal_a_la_taille_du_relief.py`).
- Textures d'un decalque de campagne : chemin de base cite par le modele + suffixe. WH3 :
  `_base_colour` (DX10 BC3 sRGB, forme dans l'alpha), `_material_map` (G = rugosite), `_parallax` ou
  `_normal` ; WH1 : `_diffuse`, `_specgloss` (brillance dans l'alpha), `_parallax` ou `_normal`.
- WH3 dessine encore les modeles v7 de WH1 (types de textures 0, 1, 3, 11, 12) : les Empires en posent
  plus de 200 000 (fissures, rochers). Les textures `test_*.dds` et `flatnormal.dds` citees par les
  modeles n'existent nulle part : le moteur met une texture par defaut, chez CA aussi.
- Le sol de WH1 = ses maillages de terrain (64 % de la carte, objets poses a 0,03 pres) + ses tuiles a
  maillage propre (montagnes, falaises, rivieres) ; `lf_height_map` n'est que le relief de base (0,26 plus
  bas en moyenne). Journal `2026-09-22-phase-4\relief-tuiles-wh1.md`.
- Format CHMF v5 dechiffre (`chmf.py`) ; `tile_list.bin` v1 et v2 : enregistrements de 21 octets, y compte
  depuis le sud, deux flottants = min/max du sol sur l'emprise elargie de 2 cases.
- Les « gros pics » vus dans Terry sont des eclats d'obsidienne du Chaos, masques en jeu hors des regions
  du Chaos : Terry montre toutes les variantes de culture a la fois.

## Session du 22.09.2026 (17 h 35 - ) - textures de sol et eclairage de WH1

### A. Evitables (detail : `05-journal\2026-09-22-phase-4\eclairage-textures-wh1.md`)

74. `[evitable]` **Dire qu'un outil ne touche pas un fichier sans relire la liste de ses sorties.** J'ai
    pose l'`environment_collection.xml` de WH1 (les 7 zones d'eclairage) dans `working_data` avant BOB, et
    ecrit au guide « BOB n'ecrit ni `lighting\` ni `environment_collection.xml` », d'apres ses seuls
    journaux (aucune action nommee). Or notre propre `compiler_terrain_bob.SORTIES` declare ce fichier parmi
    les sorties de BOB : BOB le refait d'apres le projet Terry, qui n'avait pas de zones, et efface le
    notre. Le pack de 17 h 59 est parti sans les zones de WH1 (vu a 18 h 00, avant tout essai). ->
    **Regle : avant d'ecrire dans `working_data` un fichier qui pourrait venir de BOB, chercher son nom dans
    `compiler_terrain_bob.SORTIES` ; s'il y est, le faire produire par le projet Terry (ou l'ecrire apres
    BOB), jamais avant.** Code : les zones sont des entites `ECEnvironmentVolume` du calque
    `eclairage_wh1` (`eclairage_wh1.entites_zones`) ; `build_pack.py` exige `environment_collection.xml`
    avec les 7 spheres, et refuse desormais d'enregistrer un pack dont le terrain manque ou est perime (il
    ne faisait qu'un avertissement).
    **[Code périmé : la collection est écrite par `build_pack.py` en cylindres ; état au 25.09 : `eclairage_wh1.ZONES_REMISES` (erreur 251).]** [25.09.2026, ménage]

75. `[evitable]` **Recidive : `cd` dans une commande Bash** (17 h 50) : le dossier de travail de la
    session a change (retabli aussitot, sans degat). La regle (memoire de reprise, piege 8) tient ; toujours
    des chemins absolus.

76. `[evitable]` **Deuxieme recidive de l'erreur 62** (18 h 45) : un `python - << 'EOF'` avec des chemins a
    antislashs pour corriger un script. Sans degat (heredoc entre apostrophes), mais la regle est nette :
    tout Python s'ecrit dans un fichier, puis s'execute. Aucune exception « petite correction ».

78. `[evitable]` **`sed` avec antislashs sous Git Bash** (19 h 20), en violation d'une regle non negociable de
    `CLAUDE.md`. Il a manque sa cible et altere une autre ligne (une classe de caracteres d'expression
    reguliere) d'un script du brouillon ; sans consequence hors du brouillon. -> **Regle (rappel) : toute
    modification de fichier passe par l'outil d'edition ; `sed` n'est jamais employe des qu'un antislash est
    en jeu.**

79. `[evitable]` **Troisieme recidive de l'erreur 62** (19 h 25) : `python - << 'EOF'` avec des expressions
    regulieres a antislashs. Meme regle que 62, 71, 76 ; je l'ecris ici pour que le compte soit juste.

77. `[evitable]` **Juger « objets volants » sur l'origine des objets.** Mes premiers comptes (11 % d'objets
    au-dessus du sol) prenaient la position d'origine des modeles ; une pierre levee a son origine en son
    milieu (boite de -0,63 a +0,63). Avec le bas reel de la boite : 6,5 % ; et 2 205 des 2 355 restants
    reposent sur un autre objet (collines modelees de WH1, tertres). Seuls 150 sont vraiment en l'air.
    -> **Regle : un ecart objet / sol se mesure avec le bas de la boite englobante tournee et mise a
    l'echelle, et en cherchant un support parmi les autres objets, jamais avec l'origine seule.** Code :
    `props_wh1_vers_layers.emprise` et `recaler_hors_sol_connu`.

80. `[evitable]` **Juger qu'un objet en porte un autre sur sa boite englobante.** La passe « au sommet pres »
    (chaine de 20 h 18) acceptait comme support tout objet dont la boite contenait le point le plus bas de
    l'objet et dont le haut etait a sa hauteur : une fissure, une colline modelee, une tour « portaient » ce qui
    passait a cote. Audit du projet ecrit (20 h 55) : 4 450 objets a plus de 0,05 au-dessus du sol, tous « portes » (3 345)
    ou « suspendus » (1 105 : murs et tours naines, or, cranes, ranges comme decor pendu). -> **Regle : un
    appui se juge sur la surface reelle du support (ses triangles) a la verticale du point le plus bas de
    l'objet, dans le repere de WH1 ; un objet porte suit exactement le deplacement de son appui, et seulement
    si la surface de l'appui sous lui reste au-dessus de notre sol.** Code : `sommets_rmv2.maillage`,
    `sommets_rmv2.surface_sous`, `props_wh1_vers_layers.poser_sur_le_sol`.

81. `[evitable]` **Annoncer un probleme regle d'apres le bilan de l'algorithme, sans mesurer le resultat
    ecrit.** Vers 20 h 20 j'ai presente la passe de pose comme la fin des objets volants d'apres ses propres
    comptes (« volaient, poses : 1 560 ») ; Charles en a vu « enormement » dans Terry a 20 h 50. Le bilan
    d'un algorithme ne mesure que ce qu'il croit faire. -> **Regle : apres toute passe de pose, mesurer les
    objets du projet ecrit (calques `.layer` et relief `.tif` relus sur disque), avec une mesure independante
    de l'algorithme (point le plus bas de chaque objet contre le sol), et donner ce chiffre, pas le bilan.**
    Script : `02-scripts\audit_objets.py` (relit les calques et le relief ecrits).

82. `[evitable]` **Remonter un objet enfoui sans regarder s'il l'etait deja dans WH1.** WH1 garde des objets
    entierement sous son sol (fissures a 4 unites sous terre au Massif d'Orcal, invisibles en jeu). La regle « objet
    enfoui -> remonte a l'enfoncement de son modele » les a sortis de 5 unites, et les fissures posees dessus ont
    suivi (+4,4 au-dessus du sol a l'audit de 21 h 50). -> **Regle : un objet n'est remonte que s'il etait visible
    dans WH1 (une partie au-dessus du sol de WH1) ; entierement sous le sol de WH1, il y reste.** Code :
    `props_wh1_vers_layers.poser_sur_le_sol` (`enfoui_wh1`).

83. `[evitable]` **Poser les objets de la mer sur le relief de terre, et inventer le fond.** En mer, le sol visible
    est `sea_height` (le fond), pas `height` ; notre fond etait un profil invente (-0,3 a -1,4) et la passe de pose
    mesurait les objets marins de WH1 contre le relief de terre : rochers et recifs « flottants » devant
    l'embouchure (Charles, 22 h). -> **Regle : en mer, le sol d'un objet est le fond ; le fond est celui de WH1
    (`lf_sea_height_map.dds`).** Code : `terrain_wh1_vers_terry.rasters` (`sol_objets`, `FOND_*`),
    `audit_objets.py` (fond en mer).

84. `[evitable]` **Recreer le dossier du projet Terry sans ses reglages d'apercu.** Le generateur efface le dossier du
    projet a chaque generation ; aucun `<carte>.terry.user` n'y etait jamais ecrit : Terry n'affichait ni le plan
    d'eau ni les arbres, et montrait les decors de toutes les cultures (« pourquoi l'eau et les arbres ne
    s'affichent pas ? », Charles). -> **Regle : le generateur ecrit le `.terry.user` (modele des Empires : plan
    d'eau, vegetation, culture de l'apercu).** Code : `terrain_wh1_vers_terry.ecrire_terry_user`.

85. `[evitable]` **Declarer les lacs en mer d'apres les hex logiques.** Les 85 hex `sea_lake` de la carte logique
    sont de la terre dans WH1 (92 % sous ses maillages de terrain) : WH1 y posait des plans d'eau en objets a
    l'altitude de chaque lac (26 `water_plane`, carres de test gris, materiau 83 inconnu de WH3). Declares en mer
    dans `tile_map.png`, ils devenaient des puits jusqu'au niveau de la mer ; la statue de la Dame du Lac et son
    cercle de pierres flottaient 4 unites au-dessus (golfe du Bidouze). -> **Regle : le visuel suit WH1, pas la
    logique : mer visuelle = `sea_coast` et `sea_ocean` ; les lacs sont de la terre et leurs plans d'eau deviennent des
    polygones d'eau de WH3 (`ECPolygonMesh`, comme les 361 des Empires), a leur hauteur de WH1.** Code :
    `terrain_wh1_vers_terry.SOLS_MER`, `props_wh1_vers_layers.entite_eau`.
    [Remplacée le 04.10.2026 (méthode du 27.09, annotation de n° 63 et § C) : `tile_map.png` vient de l'export CAIME,
    jamais peinte. Décision de Charles, 04.10 : la Saison garde sa `tile_map.png` peinte (validée en jeu) ; export
    CAIME pour toute carte neuve. La partie « lacs = polygones d'eau à leur hauteur de WH1 » reste valable.]

86. `[evitable]` **Tracer la mer du visuel d'apres la carte logique, puis relever la terre qui se noyait.** La mer
    logique (hex `sea_coast` / `sea_ocean`) s'arrete un hex trop tot tout le long de la cote : cette bande, de l'eau
    dans WH1 (ses maillages de mer), etait chez nous de la terre sous 0. La « terre basse relevee » de la phase 6
    remodelait alors toute la plaine cotiere sous 0,35 (228 000 px) en plateau de 0,08 a 0,35 : plaques de sol
    plates, bordees d'un a-pic, qui semblaient flotter au bord de l'eau (captures de Charles, 22 h 25). La terre de
    WH1 n'est sous 0 que sur 440 px. -> **Regle : la mer du visuel est celle de WH1 (hex a plus de moitie sous ses
    maillages de mer), sauf les emplacements principaux de ville ; la terre garde ses hauteurs de WH1 (les rares
    pixels sous 0 remontes a 3 cm).** Code : `terrain_wh1_vers_terry.mer_de_wh1`.
    [Remplacée le 04.10.2026 (méthode du 27.09) : `tile_map.png` exportée de CAIME, jamais peinte. Décision de
    Charles, 04.10 : la Saison garde sa `tile_map.png` peinte (côtes validées en jeu) ; export CAIME pour toute carte
    neuve.]

87. `[decouverte]` **Les tuiles de cote de WH3 ne couvrent qu'une bande reguliere.** Passer a la mer de WH1 (erreur
    86) a donne 28 « Failed to find tile » dans BOB (`TileSet_cliff_gen`, `TileSet_sea_coast`), donc des trous dans
    le rivage. Preuve : les 431 hex de bande de la mer logique de WH1 (0 echec) ont tous une seule serie de 1 a 3
    voisins de mer ; la mer de WH1 en ajoutait 27 a 4 ou 5 voisins de mer (pointes de terre d'un hex) ou a deux bras
    de mer, et chaque echec touchait l'un d'eux. Apres retouche au moindre ecart (20 hex noyes, 11 rendus a la
    terre, 26 hex d'ecart a la part d'eau de WH1) : 0 echec, `bob_warnings.log` vide (22 h 45). -> **Regle : la mer du
    visuel passe par `regulariser_cote` ; le generateur s'arrete s'il reste un hex de bande a plus de trois voisins
    de mer ou a deux bras de mer.** Code : `terrain_wh1_vers_terry.defaut_de_cote`, `regulariser_cote` ; GUIDE § 15,
    n° 97.
    [Remplacée le 04.10.2026 (méthode du 27.09) : pour une carte neuve, `tile_map.png` vient de l'export CAIME, jamais
    peinte ni régularisée. Décision de Charles, 04.10 : la chaîne de la Saison (`regulariser_cote`, `tile_map.png`
    écrite par `terrain_wh1_vers_terry.py`) est laissée telle quelle, ses côtes étant validées en jeu.]

88. `[evitable]` **Ramener Terry au premier plan avec `open_application`.** L'outil de controle de l'ecran ne
    retrouve pas la fenetre de Terry pendant qu'il charge un projet : il lance un **second** `tweak.modder.x64.exe`
    (vide), qui peut ensuite ecrire ses reglages ou tenir des fichiers. Deux fois le 22.09.2026 (21 h et 22 h 51).
    -> **Regle : pendant un chargement, suivre Terry par `Get-Process` (`Responding`, titre `TWeak - Terry - <carte>`)
    et par captures d'ecran seulement ; jamais `open_application` sur Terry. Si un second processus « TWeak » sans
    projet apparait, le fermer par `CloseMainWindow`.**

89. `[evitable]` **Ramener les objets de WH1 au repere des rasters.** Le 21.09.2026 (22 h 05), constat juste : les
    objets de WH1 sont en espace des hex (profondeur 338,9), le relief en pixels carres (293,5). Conclusion fausse :
    multiplier le z des objets par √3/2. Dans Terry, et donc dans le jeu, **le monde des entites est l'espace des
    hex** : Terry etire les rasters de 2/√3 en z. Tous nos objets etaient tasses de 13 % vers le sud par rapport a
    leur sol : pierres de lien flottant 1,6 au-dessus d'un sol pris 27 unites plus au sud, « des trucs qui volent
    partout » (Charles, 22 h 40), alors que nos audits, faits dans le meme repere faux, ne trouvaient que 45 objets en
    l'air. Preuves (22 h 55 - 23 h 10) : camera de Terry collee en (23,49 ; 162,75), en mer pour la lecture « pixels
    carres » : Terry montre la terre ; en (9,5 ; 237,38), en terre pour cette lecture : la mer ; aux Empires, 37 % des
    herbes et buissons de CA sont a 0,1 pres de leur sol si l'on lit le relief a z × √3/2, contre 3,5 % a z tel quel.
    -> **Regle : les positions des entites (objets, montagnes, eau, eclairage, camera) sont en espace des hex, jamais
    converties ; un raster (relief, fond, masques) se lit a la ligne de z × √3/2 ; un maillage pose d'apres les cases
    (montagnes de WH1) s'etire de 2/√3 en z. Un repere se verifie dans l'outil qui affiche (essai terre / mer a la
    camera de Terry) : un audit qui lit positions et rasters dans le meme repere faux ne voit rien.** Code :
    `props_wh1_vers_layers.Z_VERS_RASTER`, `montagnes_wh1.Z_VERS_MONDE`, `audit_objets.py`, `audit_vol.py` ; GUIDE
    § 15, n° 98.

90. `[evitable]` **Appliquer la regle « epouse le sol » a la vegetation et sur le sol connu de WH1.** La regle (99 %
    du dessous ramene au sol) visait fissures, mares, dalles et collines modelees ; une touffe d'herbe ou un buisson a
    un « dessous » fait de brins hauts : 3 050 plantes descendues de 0,41 en mediane (78 % a plus de 0,2 sous le sol),
    leur pivot de WH1 etant pourtant sur notre sol (audit de la session « IA et modding 3D », 23 h). -> **Regle : sur le
    sol connu de WH1 (ses maillages de terrain, notre sol a 0,005 pres), la hauteur de WH1 est gardee ; la regle ne
    s'applique qu'ailleurs, et jamais au materiau 97.** Code : `props_wh1_vers_layers.poser_sur_le_sol`.

91. `[evitable]` (session d'audit, 22.09.2026) **Comparer les positions de WH1 aux notres sans le repere documente.**
    45 534 objets « absents » faux. -> **Regle : avant toute comparaison WH1 / nous, appliquer le repere documente et
    le verifier sur un objet connu.** Code : `audit_fidelite.py` (`Z_WH1_VERS_NOUS`, 1 depuis l'erreur 89).

92. `[decouverte]` (session d'audit, 22.09.2026) **Les fichiers de WH1 n'ont pas tous le meme repere.** Maillages de
    sol (`global_meshes`) : x de 0 a 266,53, z de 0 a 293,52, la grille des rasters ; objets (`global_props`) et liste
    des arbres (bornes 266,53 × 339,77) : espace des hex, z × 2/√3 (le monde, erreur 89). -> **Regle : mesurer
    l'etendue de chaque fichier avant toute conclusion geometrique.**

93. `[evitable]` (session d'audit, 22.09.2026) **Conclure sur le repere des entites de WH3 d'apres les seuls fichiers
    de WH1.** L'etendue des maillages de sol de WH1 face a celle de ses objets a ete transmise comme une decouverte
    (« z × √3/2 juste »), sans verification sur une carte de CA de WH3 ; elle etait fausse (erreur 89). -> **Regle : une
    convention de repere de WH3 s'etablit sur les donnees de CA dans WH3 (etendue des entites face a celle des
    rasters, objets au sol), jamais par deduction depuis WH1.** Code : `audit_fidelite.objets` (essaie les deux
    reperes et dit lequel colle).

94. `[evitable]` **Tenir un objet par des boites qui se recoupent, et declarer inconnu le sol des routes de WH1.** (1) La
    regle « accroche » tenait un objet par tout voisin dont la boite recoupait la sienne : braseros (+0,24), tombes et
    tertres vampiriques (+0,1 a +0,2), qui flottaient deja dans WH1, restaient en l'air ; (2) les routes de WH1 (11 563
    cases) n'ont pas de maillage de terrain, mais leur sol est le relief de base + 0,2546, le notre (vegetation de WH1 a
    +0,005) : recales comme sur un sol inconnu, 323 pieux, fissures et tertres plantes par WH1 y etaient remontes, et
    284 autres sur le sol ordinaire. Mesure (audit du vrai vol, 23 h 15 -> 23 h 27) : 121 objets en l'air -> 26, tous
    pendus aux arbres de WH1. -> **Regle : tenir = contact reel des surfaces (`sommets_rmv2.se_touchent`) ; un arbre de
    WH1 tient ce qui pend a plus de 0,25 du sol ; routes de WH1 = sol connu ; sur le sol connu, un objet qui ne vole pas
    garde sa hauteur de WH1.** Code : `props_wh1_vers_layers.poser_sur_le_sol`, `terrain_wh1_vers_terry.rasters`,
    `02-scripts\audit_vol.py`.

95. `[decouverte]` (session d'audit, 22.09.2026, 23 h 40) **Un personnage en (0, 0) se place par
    `start_pos_character_to_settlements`.** Sans ce lien, WH3 le pose en case (1, 1) : les 23 chefs de faction
    (armees ennemies) etaient tous dans le coin de la carte (« les villes sont la, les armees non », Charles). WH1 et CA
    ont tous deux ce lien (198 des 202 personnages lies de CA sont en (0, 0)) ; `declare_campaign.py` ne portait pas la
    table. Avec les 23 liens de WH1, chaque chef est sur la case de sa capitale, en garnison, comme dans le startpos de
    WH1. -> **Regle : `declare_campaign` porte `start_pos_character_to_settlements` ; un personnage en (0, 0) sans lien
    est une erreur.** Garde : `02-scripts\garnisons_chefs.py` ; GUIDE § 15, n° 100.

96. `[evitable]` **Transposer l'eclairage de WH1 champ par champ dans celui de WH3.** Essai en jeu de Charles (23.09.2026,
    00 h) : voile cyan, couleurs lavees, « des qu'on zoome, ca change de luminosite ». Causes : brouillard de WH1 bleu vif
    (0,56 / 0,60 / 1,0 ; WH1 ne le prenait qu'a 15 %, `fog_colour_blend`, WH3 a 100 %) en couche de 3 unites collee au
    sol (la camera y entre en zoomant) ; gains de couleur de WH1 (vert x 1,10, bleu x 1,14) sans la LUT de CA ; cube
    ambiant bleute ; 7 zones en spheres, que WH3 evalue a la position de la camera, alors que CA fait ses zones en
    cylindres infinis (Realm of Chaos, prologue) ou presque rien (Empires : une petite sphere). -> **Regle : un reglage
    de rendu de WH1 ne se transpose pas en valeurs ; partir de l'eclairage de CA le plus proche (`woodelf`) et n'y
    reprendre de WH1 que ce qui a le meme sens dans les deux moteurs (direction et couleur du soleil). Zones : en
    cylindres, comme CA, ou pas du tout.** Code : `eclairage_wh1.convertir`, `ZONES_ACTIVES` ; build_pack ecrit la
    collection sans zone.
    **[Précisée le 25.09.2026 : une zone se fait « à la manière de CA » (LUT, brouillard, soleil, ambiance), jamais de teinte ni de calage par canal (erreur 251).]** [25.09.2026, ménage]

97. `[decouverte]` **La neige de campagne de WH3 lit le masque d'UNE carte.** C'est un post-traitement de
    l'environnement (`post_processes` du `.environment`) dont le materiau porte le chemin du masque :
    `combi_campaign_snow.xml.material` -> `terrain/campaigns/wh3_main_combi_map_1/snow_mask.dds`. Avec l'eclairage des
    Empires, notre masque (juste : 255 sous les 1 406 arbres d'hiver) n'etait jamais lu ; la clairiere d'hiver de WH1
    restait sans neige et ses lisieres, arbres et herbes givres faisaient des « trucs gris » sur un sol d'ete (capture de
    Charles). CA a un materiau par campagne (combi, chaos, prologue, vortex). -> **Regle : chaque carte a son materiau
    de neige, qui lit son masque.** Code : `eclairage_wh1.materiau_neige`, `NEIGE_NOUS` ; GUIDE § 15, n° 102.
    **[Vrai en 8.1 seulement. En 9.0, le matériau de neige de CA ne cite plus de masque : le jeu lie lui-même le `snow_mask.dds` de la campagne (erreur 216).]** [25.09.2026, ménage]

98. `[evitable]` **Ecrire un module neuf sans verifier que le nom est libre.** Le 23.09.2026 (00 h 50), `rivieres_wh1.py`
    (maillages d'eau drapes) a ecrase la premiere version du meme nom (22.09.2026, 20 h 19 : masque des rubans et regle
    de pose des tuiles de riviere validee sur 1 974 bords, dont le bit 0x04 = miroir local sur x) ; l'outil d'ecriture
    l'a signale (« updated » au lieu de « created »). Restauree depuis l'historique des fichiers de Claude Code
    (`~\.claude\file-history\<session>\`) sous `02-scripts\rivieres_wh1_masque.py`. -> **Regle : avant d'ecrire un
    fichier neuf, chercher son nom (Glob) ; un « updated » inattendu se traite tout de suite (historique des fichiers).**

99. `[evitable]` **Convertir un modele d'apres son seul premier morceau.** `fichiers_wh1.feuillage_wh3` (type 0 -> 27 pour
    le feuillage, materiau 97) ne lisait que le materiau du premier morceau du fichier : tronc (68) puis feuillage (97),
    le feuillage restait en type 0, sans couleur en jeu (« arbres gris » : `emp_medium_trees_02`, variante BASE, et une
    quinzaine d'arbustes, herbes, lisieres) ; feuillage puis tronc, le tronc etait converti a tort. -> **Regle : un RMV2
    se traite morceau par morceau, dans chaque LOD ; un controle liste chaque morceau (`variantes_lod` : « feuillage sans
    27 »).** Code : `fichiers_wh1.feuillage_wh3`.

100. `[decouverte]` **Pour un modele v7, le moteur de WH3 prefere les textures de CA de meme base.** A cote de la texture
    citee X_diffuse (X_specular, X_gloss_map...), il cherche X_base_colour et X_material_map ; quand CA a converti l'objet
    de WH1 pour WH3, ces fichiers existent au meme chemin de base et notre modele de WH1 les prend (la glace de CA est
    rose, 255/162/165, celle de WH1 bleu-gris, 125/145/158 : cristaux roses de la capture de Charles). 30 jeux touches,
    ~200 modeles (arbustes `emp_shrubs`, toiles, pierres, pierres de lien, decor vampire et peau-verte...). -> **Regle :
    tout jeu de textures de WH1 dont la base a un X_base_colour ou X_material_map dans WH3 va sous `_wh1/` (le modele
    reecrit).** Code : `fichiers_wh1.Relocateur._jeu_detourne` ; controle : le script de brouillon
    `textures_detournees.py` (a coder en garde) ; GUIDE § 15, n° 103.

### E. Decouvertes de 22 h (GUIDE § 15, n° 93 a 96)

- **Les arbres de la carte, dans Terry** : il les dessine d'apres `tree.tif` et la base du kit ; les familles
  « porteuses » (palmiers, jungle...) n'y ont aucune variante : aucun arbre. `tree.tif` est desormais peinte en
  familles de WH3 ressemblantes, pour BOB et l'apercu seulement.
- **La liste compilee des arbres de WH1** (`campaign_maps\<carte>\display\trees\trees.campaign_tree_list`) a le
  format de celle de WH3 (version 4, memes bornes, z en espace des hex) : 80 457 arbres, 45 essences ; elle est
  embarquee telle quelle (essences `wh1_*`, hauteurs recalees). Octet 13 : 0 a 5 (orientation ?).
- **Fond marin de WH1** : `lf_sea_height_map.dds` (u16, meme grille que le relief ; lf = 1,0058 x fond + 340 sur la
  terre ; en mer vers -0,68).
- **Montagnes de WH3** : les Empires en posent 3 044 en objets (`generic_props/mountains/<culture>/`), visibles
  sous le brouillard et en vue tactique, forme reportee dans le relief (`apply_height_patch`).

### B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 79 et 80)

- Le jeu lit les chemins de textures de la liste compilee de chaque carte (`global_map\texture_arrays.xml`,
  144 groupes) ; **Terry ne lit ni cette liste ni une texture posee en vrac dans `working_data` au chemin de
  CA** (deux essais, 17 h 40 et 17 h 55) : une texture de sol propre a la carte ne se juge qu'en jeu.
- Formats des textures de sol de CA et de WH1 (canaux mesures) : GUIDE § 15, n° 79 ; `bc7.py` encode le
  BC7 (mode 6) sans outil exterieur.
- `global_blend.dds` de WH1 : 5 835 px a 255 (sans texture) ; celui que BOB compile recopie exactement
  les numeros de `blend.tif`.
- BOB ecrit `environment_collection.xml` d'apres les entites `ECEnvironmentVolume` du projet (attribut
  `lighting_file`, forme `ECDoubleSphere` ou `ECInfiniteDoubleCylinder`) ; attribut XML d'une propriete
  Terry = son nom affiche en minuscules, espaces remplaces par `_`.

### C. Decouvertes du soir (19 h ; reportees dans `GUIDE.md` § 15, n° 81 a 84)

- **La cote de CA** : les Empires bordent toute leur mer d'une bande de 2 px de `tile_map.png` (un hex, cote
  terre) de types de cote : `cliff_gen` (253, 3, 1), `sea_coast` (255, 255, 0), et quelques blocs
  `cliff_gen_ends` (84, 230, 84). Notre carte n'en avait aucun : cote en escalier d'hex (« en pixels »,
  Charles). WH1 alternait falaises (`cliff_custom`) et rivages (`sea_coast`) le long de la meme cote.
  **[Corrigée le 27.09.2026 : ces couleurs décrivent l'ancien relevé ; exporter `tile_map.png`
  depuis CAIME, sans la peindre ni la retoucher. Pour WH3, CAIME place `cliff_gen` sur la terre
  côtière hors plage, `sea_coast` sur les plages, `cliff_gen_ends` aux transitions ; les rivières
  sont en `generic` et leurs embouchures en plage ; les routes priment sur les plages
  (`BaselineTilemapExporter.cs`).]**
- **La marche terre / fond marin est la norme** : aux Empires, terre au bord de la mer a 0,64 (mediane), fond a
  -0,39 ; WH1 aussi (terre 0,29, fond -0,46). C'est le trace de la cote qui fait la difference.
- **Terry copie et colle sa camera** : `camv3;oeil x;y;z;cible x;y;z` en coordonnees du monde (commandes
  `CopyCamera` / `PasteCamera`, sans raccourci par defaut ; F9 / F10 dans `working_data\Terry\local\
  keyboard.xml`, sauvegarde dans `terrain-backups`). Permet de viser un point precis de la carte.
- **WH1 faisait une partie de son relief avec des objets** : collines modelees `wef_climate_hill`, tertres,
  fissures (materiau 86, textures factices `test_*` : l'aspect du sol). Les cercles de pierres y reposent.
- `tile_list.bin` v1 : enregistrement [u16, u32 indice du nom, u8] puis [u16 x, u16 y, u8 code, u8 climats,
  f32, f32] ; `02-scripts\tuiles_wh1.py` (familles par case, 800 x 881, y depuis le sud).

### D. Decouvertes de 19 h 30 (essai de Charles en jeu : « les arbres n'ont aucune texture » ; `GUIDE.md` § 15,
n° 85 a 87)

- **Feuillage de WH1 (RMV2 v7, materiau 97 : arbres, herbes, roseaux)** : WH3 dessine la geometrie mais ne lie
  la couleur que sous le type de texture 27 (`base_colour`) ; WH1 la met sous le type 0 (`diffuse`). Resultat :
  grands triangles plats sans texture (et une bonne part des « pics » sombres vus dans Terry). Changer ce seul
  champ suffit (verifie dans Terry : feuillage, troncs, decoupe, couleurs). Code : `fichiers_wh1.feuillage_wh3`.
- **Emission** : CA a converti ses materiaux emissifs de WH1 vers WH3 selon I3 = 0,4631 x I1^(5/9) (trois
  materiaux du Chene des Ages presents dans les deux jeux, ajustement exact). La pierre de lien elfe (120) sortait
  en tache blanche. Code : `fichiers_wh1.emission_wh3`.
- **Variantes de decor de WH1** : les variantes de corruption (Chaos, vampires) existent dans presque toutes les
  regions ; WH1 les montrait selon la corruption en cours de partie. Au tour 1, seule Mousillon est vampirisee.
  WH1 avait aussi des « climats » de region (`wef`, `wef_ash`, `wef_win`, `brt_vmp`, `wef_chs`...), liste de 24.
- **La couche `climates` de la carte de WH1** ne porte que deux valeurs (`brt_chs`, `grn_chs`) : elle ne pilote pas
  les variantes. Le startpos de la mini-campagne n'est pas dans les packs de WH1 sous `campaigns\...\startpos.esf`.

## Session du 23.09.2026 (00 h 50 - ) - revue complete de la carte, cote de WH1

### A. Evitables

101. `[evitable]` **Poser un objet qui vole a l'enfoncement type de son modele, sur le sol de WH1.** Revue du 23.09.2026
    (audit de fidelite relance) : 961 objets descendus de 0,117 en mediane (jusqu'a 0,44), alors qu'ils ne flottaient que
    de 0,061 (0,063 au-dessus des maillages de WH1 eux-memes : assemblages de decor recopies par les artistes sur un sol
    inegal, qui flottaient deja dans WH1) ; tertres de cranes de 0,12 enterres en entier, rochers `grn_rock_of_tall_b`
    descendus de 0,39 pour 0,05 de vol. Aussi : les « prefab_as_mesh » de WH1 (idoles peaux-vertes, 8 et 9 morceaux)
    centrent chaque morceau sur sa propre boite ; `sommets_rmv2` ne centrait que sur la boite commune et les lisait jusqu'a
    3 unites trop bas. -> **Regle : sur le sol de WH1, un objet qui vole est descendu juste au contact (point bas 1 cm sous
    le sol) ; l'enfoncement type du modele ne sert que sur un sol inconnu. Un lecteur de sommets se verifie sur tous les
    modeles employes, contre les boites de l'en-tete.** Code : `props_wh1_vers_layers.CONTACT_SOL`,
    `sommets_rmv2.maillage` (centrage par morceau) ; controle : `verif_sommets.py` du brouillon (549 modeles sur 551
    d'accord avec leur boite ; les 2 autres sont des decalques, que la pose ne touche pas).

102. `[evitable]` **Faire la cote d'hex entiers et de tuiles de WH3 sans regarder comment WH1 fait la sienne.** Charles dans
    Terry (23.09.2026, 01 h) : « les bords autour de la mer... pixelises... ca fait des carres ». Notre mer etait faite
    d'hex entiers (0,67 unite), regularises pour les tuiles de cote de WH3 ; le relief sautait de 0,03 (terre) a -0,3 ou
    moins (fond) a chaque bord de case ; la bande de cote de WH3 posait dessus ses falaises et rivages carres ; sous l'eau,
    du sable tropical de WH3. WH1 : plages et tuiles de mer fondues dans ses maillages de terre et de mer (0 % de leur
    emprise hors de ces maillages), cote = frontiere des deux maillages au pixel (bords de case et diagonales des tuiles
    `*_tri`), 233 falaises sculptees `cliff_custom` par-dessus, texture sous l'eau = son `global_blend` (`grass_a2`).
    -> **Regle : un element de WH1 se reprend tel que WH1 le construit (ses maillages, ses tuiles), avant tout equivalent
    de WH3 ; mer visuelle = maillages de mer de WH1 au pixel ; une seule surface ecrite dans `height` et `sea_height`.**
    Code : `terrain_wh1_vers_terry.COTE_WH1`, `montagnes_wh1.FAMILLES` (+ `cliff_custom`) ; GUIDE § 15, n° 104.
    **[Remplacée par les erreurs 113 puis 155 : deux surfaces ; `sea_height` sous 0 partout.]** [25.09.2026, ménage]
    **[Corrigée le 27.09.2026 : `sea_height` doit rester sous 0 en mer pour ne pas masquer les
    maillages d'eau ; sous la terre, sa valeur ne change rien (ChaosRobie).]**
    [Partie « falaises » remplacée le 04.10.2026 par n° 223 : jamais de falaise sur le trait de côte
    (`FALAISES_DE_COTE = False`) ; les 233 `cliff_custom` de WH1 ne se reposent pas sur la côte. Mer visuelle : pour
    une carte neuve, `tile_map.png` exportée de CAIME (méthode du 27.09) ; la Saison garde la sienne (décision de
    Charles, 04.10).]

103. `[evitable]` (session « IA et modding 3D », 23.09.2026, 00 h 46) **Livrer dans `scripts-campagne` un `required.lua` qui
    chargeait des fichiers pas encore ecrits.** Remis aussitot ; le pack de 00 h 39 etait anterieur. -> **Regle :
    brouillons dans le scratchpad, livraison apres `verifier_lua.py` et comparaison du dossier.** Code : `build_pack.py`
    verifie la syntaxe de chaque script de `scripts-campagne` (Lua 5.1 du kit, `verifier_lua`) et refuse le pack a la
    premiere erreur.

104. `[evitable]` **Poser au sol une piece d'assemblage de WH1 dont le contact n'est pas prouve.** Revue du 23.09.2026 :
    65 objets que WH1 placait a plus de 0,25 au-dessus de son sol (cornes et cranes des totems du Chaos sur leur poteau,
    lanternes, attaches de cabanes, chaines, cheminees, pierres de dragon empilees) etaient descendus au sol, jusqu'a
    1 unite plus bas : `se_touchent` ne voit pas un contact aussi fin (corne sur une traverse). -> **Regle : sans appui
    trouve, un objet a plus de 0,25 au-dessus de son sol dans WH1 garde sa hauteur de WH1 (au decalage de notre sol
    pres) ; seuls les petits vols (artistes, 3 a 25 cm) sont ramenes au contact.** Code :
    `props_wh1_vers_layers.poser_sur_le_sol` (classe « assemblage »).

105. `[evitable]` **Laisser un objet de WH1 « a l'aspect du sol » s'afficher avec ses textures factices.** Les 82 collines
    modelees de WH1 (`wef_climate_hill_*`, `climate_hill` : materiau 86, `test_gray`, `flatnormal`), dont 25 dans la
    clairiere d'hiver, prenaient dans WH1 l'aspect du sol ; dans WH3, le materiau 86 affiche ses propres textures : bosses
    grises ou sombres (piste de la « tache sombre » vue par Charles). -> **Regle : un objet de WH1 dont tous les morceaux
    sont au materiau 86 avec la couleur `test_gray` est fondu dans le relief (dessus de son maillage, a z x √3/2) et n'est
    plus pose.** Code : `props_wh1_vers_layers.collines_de_relief`, `terrain_wh1_vers_terry.rasters` ; GUIDE n° 112.

106. `[decouverte]` **La glace de WH1 sort en obsidienne dans WH3.** Un modele v7 sans `_base_colour` passe par un chemin
    de compatibilite ou un speculaire fort (165 pour `wef_ice_shard`) assombrit tout : cristaux vert-noir dans Terry. CA
    a converti cette glace : `_material_map` R = speculaire de WH1 (173), G = 255 - brillance de WH1 (98,6 pour 156), mais
    en rose (255 / 162 / 165). -> **Regle : pour un materiau de WH1 tres speculaire, poser a cote de son `_diffuse` un
    `_base_colour` (le `_diffuse`, en-tete DX10 sRGB) et un `_material_map` a la recette de CA.** Code :
    `fichiers_wh1.Relocateur._pbr_glace` (3 jeux de glace), `decalques_wh1.en_dx10_couleur`, `carte_materiau_rg` ; GUIDE
    n° 113.
    [Recette remplacée le 04.10.2026 par n° 126 (métal = 1,5 × spéculaire si spéculaire et brillance ≥ 90, sinon 0)
    puis n° 202 (le canal R est lu comme du métal ; glace : `METAL_GLACE = 14`).]

107. `[evitable]` **Annoncer un pack a Charles sans l'avoir demarre.** Pack de 02 h 24 : le jeu se fermait tout seul
    8 s apres le lancement (« crash en lançant le jeu », Charles, 02 h 26), sans vidage, sans message, sans evenement
    Windows (`logs\no_clean_exit` seul). Sous cdb : `TerminateProcess(-1, 0)` appele par le jeu
    (`warhammer3_retail_x64+0x4970ed`) ; `dpa @rsp` sur la pile a ce moment nomme la table
    `campaign_map_playable_area_ownership_content_pack_junctions` (lot 2 de la session « IA et modding 3D » : verrou du
    DLC sur notre zone jouable). Aucun essai du jeu depuis 00 h 22 : quatre packs de donnees de gameplay sont partis sans
    demarrage. -> **Regle : tout pack qui ajoute ou change une table de base passe l'essai de demarrage avant d'etre
    annonce (`debug_chargement.py --arret-apres 45 --commandes <points d'arret sur TerminateProcess>` : le jeu doit
    tenir 45 s). Une fermeture sans vidage se diagnostique par un point d'arret sur `KERNELBASE!TerminateProcess` et
    `dpa` / `dpu` sur la pile. Une table de propriete de contenu (`*ownership*`) n'entre pas dans un pack de mod.** Code :
    `build_pack.TABLES_EXCLUES` (et retrait de la table si un pack precedent la porte).
    [Précisée le 04.10.2026 par n° 268 (rechute) et n° 329 : jamais une `*_ownership_content_pack_junctions` pour une
    clé à nous ; les verrous des seigneurs passent par les jonctions de faction de CA. La règle de l'essai de démarrage
    reste entière.]

108. `[evitable]` **Piloter l'ecran pendant que Charles se sert de l'ordinateur.** 23.09.2026, 02 h 45 : je placais la
    camera de Terry (clics sur le menu View, F10) pendant que Charles travaillait (Edge est passe devant au milieu d'une
    serie). Ensuite, Windows croyait AltGr enfonce (Ctrl gauche + Alt droit) : bouton du milieu sans effet dans Terry,
    double-clic sur le lanceur du jeu sans effet, Entree qui ouvrait la barre de saisie de Claude (« je n'arrive plus a
    ecrire », Charles). Origine probable, non prouvee : une frappe d'AltGr dont le relachement s'est perdu pendant que
    le pilotage bloquait ses entrees. Deux evenements « touche levee » ont tout remis. -> **Regle : ne pas piloter
    l'ecran sans le demander a Charles au moment meme ; apres toute seance de pilotage, `02-scripts\etat_clavier.py`
    (touches et boutons vus enfonces, voiles devant l'ecran ; `--relacher` les leve).** Manuellement : AltGr une fois,
    puis Ctrl gauche une fois.

109. `[evitable]` **Livrer des zones d'eclairage sans les avoir vues en jeu.** Revue de 01 h : les 7 spheres de WH1
    remises en cylindres (erreur 96 nuancee par la collection de CA). Essai de Charles, 02 h 53 : « de toutes les
    couleurs, ca fait tres mal aux yeux ». En cylindre, une zone joue a toute hauteur de camera (la sphere de WH1 ne
    jouait que de pres) ; nos trois zones de Bretonnie (rayons 90 a 110, un tiers de la carte) prenaient l'eclairage
    Bretonnie de CA (soleil 60 000 contre 30 000, filtre `campaign_chaos_ogre_kingdoms`) et les quatre clairieres leurs
    ecarts (orange, desature, pale, teinte froide) : lumiere et couleur changeaient a chaque mouvement. Aggravant :
    `build_pack` n'ecrivait la collection « eclairage global seul » que si elle manquait (une collection a zones restait).
    -> **Regle : un changement d'eclairage n'est livre qu'avec une capture en jeu (ou dans Terry) a trois hauteurs de
    camera et dans trois regions ; `eclairage_wh1.ZONES_CYLINDRES = False` ; `build_pack` reecrit la collection a chaque
    fois et refuse une zone quand elles sont retirees.**
    **[État des interrupteurs remplacé (clairières rallumées le 24.09, zones éteintes puis Winterheart seule à la manière de CA le 25.09 : erreur 251, `eclairage_wh1.ZONES_REMISES`). La règle de livraison (captures en jeu à trois hauteurs) tient.]** [25.09.2026, ménage]
    [Précisée le 04.10.2026 (conflit avec n° 277, 285, 286) : les captures en jeu sont faites par Charles, ou par une
    voie prouvée sans pilotage ; jamais de capture du bureau, et `take_screenshot` du mod MCP fige le jeu.]

110. `[evitable]` (session « IA et modding 3D », donnees ; analyse du vidage par la session de construction)
    **Ajouter nos lignes a une table de liens de CA qui garde celles des Empires.** Essai de Charles, 02 h 53 : plantage au
    tour 1 (`Warhammer3.exe+0x272AE00`, lecture de 0x128). Sous cdb : l'infobulle `ui/campaign ui/tooltip_wood_elf_glade`
    (en-tete `tooltip_worldroots_glade_forest_header`) cherche un enregistrement de base par sa cle, prend son indice de
    campagne (+0xB8), recoit un objet de campagne NUL et lit son nom. `pooled_resource_to_region_junctions` et
    `rituals_to_regions` donnaient deux bosquets a la foret d'Athel Loren : `wh3_main_combi_region_the_oak_of_ages` (CA,
    en premier, absent de notre carte) et notre Chene. -> **Regle : une cle de CA que le moteur resout en objet de
    campagne ne doit renvoyer qu'a des objets de NOTRE carte ; si la table de CA en garde d'autres, la remplacer (meme
    fichier `db/<table>/data__`, seul fichier de db.pack pour ces tables : `tables_gameplay.REMPLACE_CA`, branche dans
    `build_pack`) ou n'employer que des cles a nous. Effet de bord : pack actif dans les Empires, leurs bosquets perdent
    ces liens (desactiver le mod pour y jouer).** Lire un vidage : `lire_vidage.py`, puis `cdb -z` (`ub <appelant> L60`,
    `da` sur les chaines citees) pour nommer l'objet nul. Suite demandee par Charles (« il y a pas moyen de faire
    coexister toutes les campagnes ??? ») : cles a nous (ressource et rituel copies de ceux de CA), tables de CA
    intactes (en cours, session « IA et modding 3D »).
    [Moyen « remplacer la table de CA » remplacé le 04.10.2026 par n° 154 et n° 254 et la décision de Charles
    (`CLAUDE.md` § 2) : clés à nous, tables de CA intactes, jamais un fichier à nous à un chemin que CA cite.]

111. `[evitable]` **Declarer disparus de WH3 des emetteurs d'effets cherches en ASCII dans des fichiers UTF-16.** Revue
    de 01 h : « six emetteurs de campagne de WH1 retires des bibliotheques de WH3 » (GUIDE n° 109). L'agent de recherche
    les a retrouves sur les octets UTF-16 LE de `vfx_desc.pack` : meme `id`, meme bibliotheque ; seuls manquent les six
    fichiers de haut niveau `vfx/<effet>.xml`. -> **Regle : les XML de VFX de CA sont en UTF-16 ; chercher le motif
    encode en UTF-16 LE (et la syntaxe `id="..."` des bibliotheques, pas `name="..."` des references) avant de conclure
    a une absence.** Integration : variante « emetteurs de CA » dans `04-projets\...\effets-wh1\` (`build_pack`).

112. `[evitable]` **Livrer des scripts de campagne sans regenerer le startpos.** Essai de Charles de 03 h 19 : pas de
    cinematique, pas de « Comment jouer », pas de mission de victoire, camera « bizarre ». Script_log : « Loading value
    __save_counter [0] » : le startpos (22.09, 23 h 40) precedait nos scripts (23.09, 00 h 50), chaque nouvelle partie
    passait pour une sauvegarde (trouve par la session « IA et modding 3D », GUIDE n° 117). -> **Regle : tout
    changement des scripts de campagne ou des donnees qu'ils lisent au premier tour se termine par la regeneration du
    startpos avec le pack a jour (`startpos_manuel.py ... --ai-map-data`), le controle `__save_counter` = 1
    (`lire_esf.py --chaines`), la copie dans le projet (erreur 58) et un pack reconstruit.**

113. `[evitable]` **Ecrire la meme surface dans `height` et `sea_height`.** Revue de 01 h 30 (cote de WH1, erreur 102) :
    « une seule surface » pour supprimer les marches. Charles en jeu, 03 h 40 : « sur le cote de la mer il n'y a pas
    d'eau, que le fond de sable », « pourquoi il n'y a pas les rivieres, les lacs, la mer ». Chez CA (Empires),
    `height` vaut 0,000 en mediane sur la mer : c'est la SURFACE DE L'EAU ; `sea_height` est le fond (-0,9 pres des
    cotes, jusqu'a -109) et reste au moins 1,025 sous la terre. Meme surface = eau de profondeur nulle : ni mer, ni
    rivieres, ni lacs dessines. Terry, lui, montrait l'eau (autre rendu). -> **Regle : avant de changer la semantique
    d'une carte de BOB, mesurer celle de CA sur la meme couche (`height` / `sea_height` des Empires) ; verifier en JEU,
    pas dans Terry, tout ce qui touche a l'eau. Code : `terrain_wh1_vers_terry.NIVEAU_EAU`, `SOUS_TERRE_MER`.**
    **[Corrigée par l'erreur 155 : vrai seulement dans les marges hors jeu ; sur la mer jouable, `height` n'est pas la surface ; le niveau de l'eau est 0.]** [25.09.2026, ménage]
    **[Corrigée le 27.09.2026 : dans WH3, l'eau visible vient des maillages posés ; sous la terre,
    il n'y a pas de tuile de fond marin et la valeur de `sea_height` ne change rien (ChaosRobie).]**

114. `[evitable]` **Croire le jeu sur la foi du fichier compile.** 22.09.2026 : les chemins des textures de WH1 ecrits
    dans `global_map\texture_arrays.xml` (`textures_sol_wh1`) ; « Terry ne la lit pas, le jeu si », jamais verifie en
    jeu. Captures de Charles, 23.09.2026 : le sol de foret brun sombre de WH1 (`sand_b3`, 45 % de la carte) sort en sable
    tropical beige de CA, `grass_a2` en herbe fleurie de CA (fleurs roses et bleues), la neige en glace sombre : le jeu
    prend la texture de CA du groupe, quel que soit le chemin ecrit. D'ou l'aspect pastel, « plage », et la foret qui
    parait clairsemee. -> **Regle : un effet suppose d'un fichier compile se prouve sur une capture EN JEU (couleur
    mesuree) avant d'etre annonce. Code : `textures_sol_wh1.EQUIVALENTS_CA` (groupe de CA le plus proche en couleur et en
    nature ; `CHEMINS_WH1 = False`).**
    [Moyen remplacé le 04.10.2026 par n° 179 (groupes `wh1_*` déclarés) puis n° 341 (catalogue séparé des sols,
    `textures_sol_wh1.CATALOGUE_SEPARE`, validé en jeu par Charles le 25.09). La règle « prouver en jeu » reste.]

115. `[evitable]` **Laisser la variante BASE des arbres de WH1 dans Athel Loren.** Charles, captures cote a cote : « tu
    as ajoute beaucoup de pins ; dans WH1 il n'y a pas de pins ». Le modele d'un arbre suit la culture du proprietaire
    (`campaign_tree_type_cultures`) ; ruines, regions sans proprietaire ou tenues par des cultures sans variante de WH1
    prennent BASE = pins et feuillus de l'Empire (`gen_large_trees_01`, `emp_*`). -> **Regle : les arbres des provinces
    d'Athel Loren passent sous `wh1_al_*`, dont BASE est le modele des elfes sylvains (`arbres_wh1.PREFIXE_AL`,
    `masque_athel_loren`).**

116. `[evitable]` **Ecarter un decor de WH1 faute d'equivalent exact.** Les objets et effets de « devastation » de WH1
    (masque nul : pics, tumeurs, fissures ; 52 effets) etaient ecartes. Charles : « il manque des pics… il faut
    absolument les avoir ». -> **Regle : chercher l'approximation de CA avant d'ecarter : visibles de tous dans les
    cinq regions en ruine au tour 1 (`props_wh1_vers_layers.REGIONS_DEVASTEES_DEPART`), masques au Chaos et aux
    Hommes-betes ailleurs, comme les decors de corruption de CA aux Empires (culture_mask).**

117. `[evitable]` **Corriger un rendu pour un seul jeu de textures quand la cause touche tous les autres.** Erreur 106 :
    la glace de WH1 sortait en obsidienne (modele v7 sans `_base_colour` : chemin de compatibilite de WH3, tres
    speculaire) ; la recette de CA (`_base_colour` + `_material_map` R = speculaire, G = 255 - brillance) n'a ete
    appliquee qu'a la glace. Captures de Charles, 04 h 30 : epines, rochers et falaises « noirs veines de blanc ».
    -> **Regle : un defaut de rendu explique par une regle du moteur se corrige pour TOUS les fichiers que la regle
    touche, et le bilan le compte. Code : `fichiers_wh1.Relocateur.PBR_WH1` (tout `_diffuse` de WH1 qui a son
    `_specular` et son `_gloss_map`, sauf `_base_colour` deja fourni ou present chez CA).**
    [Recette (R = spéculaire) remplacée le 04.10.2026 par n° 126 puis n° 202 (R lu comme du métal). La règle « corriger
    tous les fichiers que la règle touche » reste.]
    Au passage (a verifier en jeu) : les rubans de riviere et les plans d'eau des lacs ont le meme materiau que chez CA,
    mais ne se voient pas en jeu (deja a 00 h 22, avant la cote de WH1) ; Terry les montrait : l'eau se verifie en jeu.

118. `[evitable]` **Lire des sommets de WH1 en flottants 32 bits sans verifier leur format.** Les 26 plans d'eau des lacs
    de WH1 (`generic_props/terrain/water_plane`, RMV2 v7, pas de 12 octets : x, y, z, w en DEMI-flottants puis uv)
    etaient lus en `<3f` : 0,008 au lieu de 1,711, des polygones d'eau de 0,00 x 0,01 unite. « Le lac n'est pas
    rempli » (Charles, 04 h 20). -> **Regle : un sommet de WH1 se decode selon son pas (8, 12 ou 16 octets : demi-
    flottants) ; toute taille derivee se controle (un plan d'eau de moins de 0,05 unite fait echouer la generation :
    `props_wh1_vers_layers.entite_eau`).**
    Rivieres (meme essai) : « plein de morceaux qui ne sont pas relies » : 1 399 rubans de tuile de WH1, poses tournees
    autrement (37) et rubans qui s'arretent avant le bord. Refaites en surface continue sur le reseau de WH1
    (`rivieres_wh1.eau_continue`, `construire_continu` : carreaux de 128 px, sommets partages a la meme hauteur).

119. `[evitable]` **Sauter sans bruit un jeu de textures que la recette ne sait pas lire.** `fichiers_wh1._pbr_glace`
    (erreur 117) ne convertissait que les jeux `_specular` + `_gloss_map` et rendait la main sans rien compter pour les
    autres : 9 jeux nommes `_spec` par WH1 (pierres de lien des elfes, arches de bois-de-reve, pierres dressees elfes,
    statue naine, pierres bretonnes, arbre de la sorciere, tertres de cranes, tumeurs du Chaos) et 6 dont le modele cite
    ses cartes sous une autre base (statue de la Dame du Lac) ou des factices absentes des deux jeux (`test_black`,
    `test_gloss_map` : 20 accessoires des hommes-betes) restaient au rendu de compatibilite. Charles, 05 h : « des statues
    des elfes, par-ci par-la dans Athel Loren, n'ont pas de texture ». -> **Regle : une recette qui ecarte un fichier le
    compte et l'affiche (`pbr_incomplets` dans le bilan de `modeles_wh1.py`) ; noms `_spec` / `_gloss` acceptes, cartes
    citees par le modele en repli (`Relocateur._noter_cartes`), factice `test_black` = R 0, `test_gloss*` = G 255.**
    65 jeux convertis au lieu de 50 ; restent 20, tous des feuillages (couleur en type 27) ou des textures sans modele.

120. `[decouverte]` **Les materiaux XML de WH1 ne branchent aucune texture dans WH3** (GUIDE § 15, n° 123). Meme essai :
    les pierres de lien (`wef_waystone_01`), la lanterne, l'ambre, les champignons, tumeurs et toiles du Chaos gardaient
    les emplacements de WH1 (`s_diffuse`, `s_specular`, `s_gloss`, `s_normal`, `s_emissive`...) sur des shaders que WH3 a
    gardes sous le meme nom mais qui ne lisent plus que `t_xml_*` (version 2). Preuve : les versions de CA des memes
    materiaux (meme chemin, ou `_alpha_off` pour la pierre de lien). -> **Code : `fichiers_wh1.V1_V2` ; on part de la
    version de CA (shader, emplacements, parametres, textures communes) et on y met nos textures de WH1 ; 6 materiaux.**

121. `[evitable]` (session « IA et modding 3D », incident signale par elle) **Creer un fichier dans `02-scripts` sans
    verifier qu'il n'existe pas.** 23.09.2026, 04 h 45 : son outil de masques d'eau a ete ecrit sous `eau_carte.py`, le
    nom de mon module de bascule cree quelques minutes plus tot ; l'outil d'ecriture l'a ecrase sans refus, 04 h 45 -
    04 h 46 min 49 s. Restaure a l'octet pres depuis la sauvegarde de Claude Code ; aucune execution de la chaine dans la
    fenetre. -> **Regle (les deux sessions) : avant de creer un fichier dans un dossier partage, verifier qu'il n'existe
    pas (`ls`) ; un outil d'une session porte un nom qui dit son role (`masques_eau_carte.py`).**

122. `[evitable]` **Livrer une eau de riviere sans mesurer sa continuite, son niveau face aux berges ni ses bords.**
    L'« eau continue » de 04 h 30 (erreur 118) remplissait le masque des `blend0` au seuil 0,5 avec la hauteur des rubans
    de WH1, en carres de pixels. Charles, pack de 04 h 37 : « les rivieres n'ont aucun sens, elles ne sont pas reliees,
    ca deborde » ; « il faut que ce ne soit plus pixelise ». Mesure (brouillon `rivieres\diag2.py`) : masque coupe en
    1 516 morceaux (le ruban s'estompe au bord de chaque tuile, GUIDE n° 125) ; eau au-dessus de la berge la plus basse
    a 13 px de 1,5 cm en mediane, de plus de 5 cm sur 16,7 % des pixels ; plus de la moitie des pixels d'eau des rubans
    hors du masque (decalage d'un pixel, « poils »). -> **Regle : avant de livrer une eau, compter les morceaux d'eau
    visible, comparer son niveau a la berge la plus basse, et ne jamais la mailler en carres de pixels. Code :
    `rivieres_wh1.champ_reseau` (blend0 + rubans recales, fermeture en disque de 7 px, maximum local), `niveau_eau`
    (plafond 1 cm sous la berge, enveloppe basse lissee), `creuser_doux` (rebord de 2 cm au bord du maillage, eau
    affleurante a 0,45, fond a 0,75), `construire_lisse` (marching squares). Resultat : 62 morceaux visibles, reseau
    principal d'un seul tenant (40 405 px).**

123. `[decouverte]` **Un chef en garnison n'a pas de pointeur sur la carte de l'ecran de selection** (GUIDE § 15,
    n° 126). Charles, 05 h 50 : « les pointeurs pour indiquer ou ils commencent, comme avec les elfes sylvains ». Le
    startpos grave pour chaque faction jouable la position de son seigneur en fraction de la carte (`FACTION_INFOS`,
    deux flottants) : Orion (0,677 ; 0,200), Durthu, Morghur justes ; Alberic, la Fee, le Duc rouge, en garnison
    (startx / starty = 0), en (0,002 ; 0,003), dans le coin. -> **Code : `ajouter_seigneurs_jouables.POINTEURS_GARNISON`
    pose la case de la capitale (lue dans le startpos) dans `override_force_location_x/y` de leur fiche, comme CA pour
    Eltharion ; la generation ne grave pas cette colonne (verifie) : lue par l'ecran, a confirmer par Charles.**

124. `[evitable]` **Lancer le jeu pour un essai pendant que Charles est devant l'ordinateur sans l'avoir prevenu.** Essais de
    demarrage de 05 h 35, 05 h 38 et 05 h 55 : le jeu ouvert par l'essai a recu des clics (video d'intro lancee, campagne
    demarree), puis l'essai l'a ferme a 45 s ; l'essai de 05 h 47, sans clic, est reste au menu. On a d'abord soupconne un
    script de la session d'audit. -> **Regle : prevenir Charles avant chaque lancement du jeu (essai, startpos) et lui dire
    de ne pas y toucher ; un journal de script qui montre une action d'interface pendant un essai se lit d'abord comme un
    clic de Charles.** (Confirme par Charles pour la fermeture de l'essai de 06 h 15.)

125. `[decouverte]` **L'eau des rivieres ne coule que si le masque de flux porte le sens du courant** (GUIDE § 15,
    n° 127). Charles, pack de 05 h 55 : « l'eau rend bien mieux mais elle n'a pas l'air de bouger » : notre masque de flux
    etait neutre (128, 128) sur les rivieres. La coordonnee « le long » des rubans de WH1 ne donne pas le sens (52 / 48 %,
    selon l'orientation des tuiles). -> **Code : `rivieres_wh1.flux_reseau` (distance le long de l'eau jusqu'a
    l'embouchure ; concorde avec la pente de notre eau sur 72 % des pixels lisibles, vers la mer a toutes les embouchures
    controlees), `relief-wh1\flux_rivieres.npy` ecrit par le generateur ; encodage de CA dans `masques_eau_carte.py`
    (session d'audit).** A voir en jeu.

## Session du 23.09.2026 (12 h 30 - ) - statues, neuf seigneurs, essais automatiques, menage

### A. Evitables et decouvertes (dans l'ordre ; les decouvertes sont reportees dans `GUIDE.md` § 15, n° 129 a 132)

126. `[evitable]` **Inventer une recette de conversion au lieu de la caler sur les conversions de CA des memes objets.**
    Charles, 06 h 05 puis 12 h 40 : « les statues n'ont toujours pas de texture ». `fichiers_wh1._pbr_glace` posait
    `_material_map` R (metal) = speculaire moyen de WH1, en aplat de 64 x 64 : la pierre de lune (speculaire 154,
    brillance 22) devenait un metal rugueux a 60 %, gris terne, sans le detail de WH1 porte par le speculaire et la
    brillance. Les conversions de CA des memes objets de WH1 (or, fer, gemmes, armes, glace, maison, pierre de lien,
    tumeur, toiles, arche) donnaient la regle (GUIDE n° 129). -> **Regle : une conversion de format se cale d'abord sur
    les objets que CA a convertis lui-meme. Code : `Relocateur._metal` (metal = 1,5 x speculaire si speculaire ET
    brillance >= 90, sinon 0 ; glace : speculaire), `_carte_pixels` (512 x 512 au plus, BC7, point par point),
    `_couleur_metal` (couleur de base d'un metal = son speculaire). L'or sort identique a celui de CA (R 216, G 77).**
    [Précisée le 04.10.2026 (conflit avec n° 202) : d'abord le shader de WH3 qui lit le fichier, puis contrôle sur les
    conversions de CA des MÊMES objets ; pour la glace, n° 202 l'emporte (`METAL_GLACE = 14`).]

127. `[evitable]` **Recopier dans le pack des tables de depart des colonnes que le pack laisse vides.** 23.09.2026,
    13 h 05 : la generation du startpos s'arretait apres le chargement des scripts, sans vidage (`no_clean_exit`, 75 a
    124 s), des que la ligne du Poste de la Pierre Noire etait reecrite depuis le kit : le kit porte « PLACEHOLDER » en
    `long_description` et « Dwarf Rebels » en `rebel_faction_name`, le pack les a vides sur toutes ses lignes.
    Dichotomie par les sauvegardes du pack prises avant chaque etape (`scratchpad\bissection_startpos.py`) : proprietaire
    seul, textes vides = generation en 15 s. -> **Regle : `synchroniser_pack_startpos.TEXTES_VIDES_PAR_TABLE` (regions)
    ecrit toujours ces textes vides et ne les compare pas ; un premier nettoyage etendu aux factions a vide 39
    descriptions qui marchaient, retabli par la sauvegarde : une regle se limite a la table ou elle est prouvee.**
    Aussi : `build_pack` retire du pack tout script qui n'est plus dans `scripts-campagne` (le pack est rouvert, jamais
    recree : un script retire serait reste actif).

128. `[decouverte]` **`frontend.start_campaign` ne lance pas notre campagne.** Essais automatiques du 23.09.2026, 13 h 38 a
    13 h 44 : appele au menu (chemin du prologue de CA, `frontend_start.lua`), il cree l'environnement de campagne et le
    detruit 2 a 3 s plus tard (`mp_log` : `notify_campaign_env_destroyed`), avec ou sans `all_players_ai` ; le menu
    revient et un script qui relance tourne en boucle. -> **Lancer par l'interface comme un joueur (GUIDE n° 131) ; un
    script de menu ne lance qu'une fois par session (`core:svr_save_bool`).** Code dans
    `04-projets\...\essai-auto\script\frontend\mod\saison_essai_auto.lua`.

129. `[evitable]` **Ecrire du Lua ou du Python par un heredoc de Git Bash avec des `\n` dans les chaines.** 13 h 53 : un
    `"\n"` du script de menu est devenu un vrai saut de ligne, chaine coupee, script non charge, jeu fige au menu 6 min ;
    deux remplacements Python par heredoc ont aussi echoue sur des lignes contenant `\n`. -> **Regle : modifier ces
    fichiers par l'outil d'edition, ou par un script Python ecrit dans un fichier ; `essai_tours_auto.py` verifie la
    syntaxe des scripts d'essai (`verifier_lua`) avant de construire le pack d'essai (code).**

130. `[evitable]` **Passer un chemin Windows dans une commande `cdb` entre guillemets.** 13 h 51 : `.dump /m C:\...` dans
    `sxd -c2 "..."` : les antislashs sont manges, vidage du plantage perdu. -> **Regle : barres obliques dans tout chemin
    donne a cdb (`essai_tours_auto.commandes_cdb`, code).**

131. `[evitable]` **Croire qu'une ligne du kit est dans le pack parce qu'un lot l'a ecrite.** 14 h 25 : la reserve de
    regiments de renom de Mousillon (`faction_to_mercenary_set_junctions`, lot 13) etait dans le kit mais aucune entree
    de `build_pack` ne lisait cette table : absente du pack et de la generation du startpos. Vue en relisant le journal
    de construction (tables et nombres de lignes). -> **Regle : apres un lot, verifier dans le journal de construction
    que chaque table du lot y figure avec son nombre de lignes ; toute table neuve a son entree dans
    `tables_gameplay.TABLES_LOT*` (ajoutee : `TABLES_LOT13`).**

132. `[evitable]` **Laisser Charles devant un jeu d'essai sans lui dire de ne rien toucher.** 13 h 46, 14 h 04 et 14 h 13 :
    trois essais fermes a la main (Echap, Quitter vers Windows) ou pilotes a la main (Drycha choisie), pris pour des
    sorties du jeu ; le journal le montre (`output_uicomponent_on_click` : `esc_menu > ... > button_windows`). -> **Regle :
    avant tout essai, dire a Charles de ne pas toucher la fenetre MEME si elle semble figee (fin de tour par le script
    apres 20 s), et lire les clics du journal avant de conclure a un plantage.**

133. `[evitable]` (session « Extension carte Bretonnie est », 23.09.2026 ; journal
    `05-journal\2026-09-23-extension-carte\carte-papier-v2.md` § 6) **Simplifier une boucle fermee par Douglas-Peucker
    sans la couper.** Premier point = dernier, segment de fermeture de longueur nulle : rien n'est garde, le SVG de la
    carte papier v1 n'avait aucun contour (seul l'apercu raster etait juste). -> **Regle, codee
    (`carte_papier_v2.dp_boucle`) : couper la boucle au point le plus eloigne du premier ; controle : longueur des `d=`
    par classe apres chaque rendu.**

134. `[evitable]` (meme session) **Reechantillonner plus grossierement des rivieres d'un pixel.** Fragmentees, presque
    toutes ecartees par le filtre de raccord (617 morceaux sur 27 181). -> **Regle, codee (`geo_extension.charger_atlas`) :
    elargir un trait avant de le reechantillonner.**

135. `[evitable]` (meme session) **Heredoc bash trop long** (regle B10 deja ecrite ; voir aussi l'erreur 129) : un
    fichier long s'ecrit avec l'outil d'ecriture.

136. `[decouverte]` (meme session) **La carte de la mini-campagne de WH1 n'est pas une reduction de la geographie du
    lore.** Athel Loren y est agrandie, et le bloc nain et orque du nord-est occupe la place que le lore donne au Reikland
    (Karak Ziflin, voisin de Montfort dans le lore, y est a 178 hex). Preuve : calage MLS sur 48 villes communes avec
    l'Atlas of the Old World, ecart median 19 hex ; Karak Ziflin, Karak Tzor, le Poste de la Pierre Noire et le Defile de
    la Hache decales de 110 a 130 hex. -> **A l'est, suivre la topologie du lore (qui touche quoi, par quel col), jamais
    un calage.** (GUIDE § 15 n° 132.)

137. `[decouverte]` **Au tour 1, le clic scripte sur la fin de tour ne termine pas le tour tant que les notifications
    d'actions en attente ne sont pas passees**, meme avec `all_players_ai` et meme apres
    `campaign_ui_manager:suppress_end_turn_warning` pour tous les avertissements. Essais du 23.09.2026, 14 h 36 a 14 h 48 :
    six clics sur `button_end_turn` sans effet en 6 min ; le journal montre ensuite quatre clics sur
    `hud_campaign > faction_buttons_docker > end_turn_docker > notification_frame > button_skip`, puis la fin de tour
    acceptee ; les tours 2 a 4 se jouent ensuite seuls en quelques secondes (mode IA). -> **Passer les notifications une
    par seconde avant de cliquer la fin de tour (`saison_essai_armer`, code).** (GUIDE § 15 n° 131.)

138. `[evitable]` (session « IA et modding 3D », 23.09.2026) **Un banc d'essai qui imite une bibliotheque de CA sans ses
    regles.** Le banc des chroniques imitait `mission_manager` sans la regle « une recompense par objectif »
    (`lib_campaign_mission_manager.lua` l. 1317 : sinon `trigger()` rend `false`, sans erreur Lua) ; il declarait justes
    des missions que le jeu refuse : les missions a plusieurs objectifs n'etaient jamais emises (Alberic, la Fee,
    Morghur, Drycha, Grom bloques a l'etape 1, le Duc Rouge a l'etape 2). Correctif : `mm:set_all_objectives_are_primary()`
    comme CA (`wh3_cp1_iron_favour.lua`), retour de `trigger()` verifie, ecouteur `MissionGenerationFailed`. -> **Regle :
    imiter une bibliotheque de CA au plus pres de son code ; le banc (`audit-ui\banc_chroniques.lua`) reproduit
    desormais la regle et verifie `set_all_objectives_are_primary`.**

139. `[evitable]` (meme session) **Imposer une forme de nom sans la verifier dans les textes du jeu.** Supposé : GW France
    dit Carcassonne, Aquitaine, Bastonne. Faux : GW France (Bibliotheque Imperiale) et CA en francais disent Gasconnie,
    Aquitanie, Bastogne, Massif d'Orquemont ; nos textes de WH1 (`textes_fr.tsv`) etaient justes (sauf « Duche
    d'Aquitaine ») et le JSON de la session les avait ecrases. -> **Regle : verifier une forme de nom dans le `.loc` du
    jeu (`local_fr.pack`) avant de l'imposer.** 36 textes francais corriges ; l'anglais reste Carcassonne / Aquitaine /
    Bastonne / Massif Orcal (formes anglaises de GW).

140. `[evitable]` (session « IA et modding 3D », 23.09.2026, 15 h 10 ; rechute de l'erreur 129) **Un Python contenant une
    barre oblique inverse lance par heredoc de Git Bash.** La passe des espaces insecables de `textes_gameplay.json` :
    la chaine `" \\1"` a perdu une barre oblique ; dans 102 textes francais, « espace + : ; ? ! » est devenu
    « U+00A0 + U+0001 » (ponctuation disparue). Repare d'apres les versions anterieures et le francais de CA. -> **Regle :
    tout script qui contient `\` s'ecrit avec l'outil d'ecriture ; apres toute passe automatique sur des textes,
    chercher les caracteres de controle. Garde codee dans `injecter_textes.py` : refus d'un texte contenant U+0000 a
    U+001F (hors saut de ligne et tabulation).**
    **Codee aussi (session « IA et modding 3D », 23.09.2026, 17 h 20) : `02-scripts\verifier_textes.py` controle
    `textes_gameplay.json` (caracteres de controle, `\n` litteraux, balises `[[ ]]`, typographie francaise,
    insecables en anglais), code de retour 1 en cas de defaut ; lance en tete de la recette du pack.**

141. `[decouverte]` (session « Rendu de la carte », 23.09.2026) **Les 20 ponts de WH1 etaient perdus : ils vivent dans le
    `bmd_data.bin` des tuiles `river_crossing`, pas dans le maillage ni dans `global_props.bin`.** Chaque tuile cite
    (FASTBIN0 v21, enregistrements version 11 : u16 11 | chemin | 12 f32 matrice + position | 30 octets de drapeaux |
    u16 n + « BHM_TERRAIN » | u32 0xFFFFFFFF, unites du ruban d'eau) un lot de 10 objets : passerelle
    `rigidmodels/campaign/resources/jetty` (0,69 × 0,33 u, tablier 0,056 au-dessus du sol de la tuile), `fence_1`,
    `fence_2`, 3 `marsh_reeds_01`, 4 `mtn_rocks_0N` ; le moteur de WH1 les posait depuis la tuile. -> **Reprendre une
    tuile de WH1, c'est aussi lire les objets de son `bmd_data.bin`** (`02-scripts\ponts_wh1.py`,
    `modeles_wh1.rassembler_tout` ; rapport `05-journal\2026-09-23-rendu-carte\ponts-wh1\`). (GUIDE § 15 n° 133.)

142. `[evitable]` (meme session) **Un essai a blanc qui ecrit ce que la chaine relit.** `terrain_wh1_vers_terry.py` sans
    `--apply` ecrivait quand meme `relief-wh1\mer_finale.npy`, `eau_rivieres.npy` et `flux_rivieres.npy` (entrees de
    `masques_eau_carte.py`) : un essai a blanc de code en chantier pouvait changer les masques d'eau du pack suivant.
    Corrige : ecrits seulement avec `--apply`. -> **Regle : un essai a blanc n'ecrit rien que la chaine relit.**

143. `[decouverte]` (sessions de construction et « IA et modding 3D », 23.09.2026) **Sous `all_players_ai`,
    `FactionTurnStart` n'arrive aux scripts pour AUCUNE faction.** Preuves (`script_log_230926_1538`) : l'ecouteur de la
    faction locale du script d'essai n'ecrit jamais ; la trace « ESSAI HARDE » (FactionTurnStart de la harde, IA) non
    plus, alors que les invasions de cette harde avancent a chaque tour (elles ecoutent `FactionBeginTurnPhaseNormal`,
    `lib_campaign_invasion_manager.lua` l. 632) et que `WorldStartRound` arrive. -> **En mode IA, tout ce qui ecoute
    `FactionTurnStart` est hors essai (histoire, chroniques, Echos, une bonne part des scripts de CA) : ce mode ne teste
    que la stabilite des IA, les invasions et les evenements de bataille ou de mission ; l'histoire et les mecaniques se
    testent en mode joueur (`--sans-ia`).** (GUIDE § 15 n° 134.)
    **[Élargie par l'erreur 230 (aussi en mode joueur) ; cause trouvée le 25.09.2026 : erreur 252.]** [25.09.2026, ménage]

144. `[evitable]` (session « Extension carte Bretonnie est », 23.09.2026, 15 h 59) **Toucher au jeu pendant les essais
    automatiques d'une autre session.** Avec l'accord de Charles, pour une capture : fenetre du jeu au premier plan, un
    coup de molette (5 crans) sur la carte strategique, pendant la serie d'essais de la session de construction (fin de
    la partie de Durthu, qui a plante vers 15 h 58 a `Warhammer3.exe+0x1A3DCFA` : le lien n'est pas etabli, mais
    l'essai est perturbe). -> **Regle : avant de piloter le jeu, meme avec l'accord de Charles, demander aux sessions
    d'essai s'il est libre ; le jeu d'essai n'est a personne d'autre.**

145. `[evitable]` (session « IA et modding 3D », 23.09.2026) **Ecrire dans le kit avant la fin du preavis annonce.** Trois
    fois dans la journee (15 h 24, 16 h 14, 16 h 21 : 43 s a 2 min d'avance), sur une lecture de l'heure. Sans consequence
    cette fois (la session de construction ne lisait pas le kit), mais le preavis sert a eviter qu'une construction lise
    une table a moitie ecrite. -> **Regle : n'ecrire qu'a la fin du minuteur du preavis, jamais sur une lecture de l'heure.**
    Rechute a 16 h 35 (lot 20) : heure annoncee 16 h 42, minuteur regle a 5 min 30 s apres l'envoi, ecriture 7 min avant
    l'heure annoncee. -> **L'heure annoncee et la fin du minuteur sont la meme valeur, calculee une seule fois, et le
    minuteur est regle sur cette heure.**
    **Codee (17 h 20) : `02-scripts\preavis.py heure` calcule une fois l'heure cible (au moins 5 min) qu'on annonce ;
    `preavis.py attendre`, en arriere-plan, dort jusqu'a elle. Et `donnees_campagne.py --apply` relit le lot ecrit et
    refait une passe : si elle n'est pas nulle, « LOT NON IDEMPOTENT », code 2 (seigneur de Mousillon recree a chaque
    passe du lot 17, vu a l'essai a blanc).**

146. `[evitable]` **Livrer un effet de WH1 recree sans l'avoir vu tourner en jeu.** Plantage `Warhammer3.exe+0x1A3DCFA`
    (tache de rendu, pointeur invalide ; pile : `ref_spawn_speed`, `TILE_DATABASE`) dans les essais automatiques :
    Durthu au tour 9 (camera deplacee par une notification), Alberic et la Fee au tour 1 (camera sur Bordeleaux et
    Carcassonne), jamais Orion. Diagnostic par le pack d'essai (`essai_tours_auto.py --neutre-vfx`) : les 6 effets de WH1
    vides -> plus de plantage ; l'herbe seule desactivee (`wh_main_campaign_enviro_grass`, emetteur `grass` de
    `wh_main_lib_campaign_enviro2`, qu'aucun effet de CA n'active dans WH3) -> plus de plantage. Effet converti le
    23.09 a 02 h 27, 33 poses, visible des Bretons et des elfes. -> **Regle : un effet (ou tout fichier de rendu)
    converti de WH1 ne s'embarque qu'apres un essai en jeu avec la camera sur une de ses poses ; un emetteur qu'aucun
    effet de CA n'emploie dans WH3 est suspect par defaut.** Corrige : emetteur `grass` desactive dans
    `effets-wh1\vfx\wh_main_campaign_enviro_grass.xml` (original range dans `99-archives\`) ; retrait des 33 poses par
    la session du rendu. (GUIDE § 15 n° 135.)
    **Complement (17 h 40) : l'herbe n'etait pas seule en cause.** Grom plantait encore au tour 1, meme adresse, avec
    l'herbe seule desactivee (camera a une cinquantaine d'unites du nuage `wh_main_campaign_enviro_cloud1`), et plus du
    tout avec les 6 effets de WH1 vides. -> **Regle : un diagnostic par elimination (A/B) se confirme sur plusieurs
    lieux de depart avant de designer un seul coupable ; ici, les 6 effets de WH1 sont remplaces par des effets vides
    (`effets-wh1\vfx`, originaux dans `99-archives\`) jusqu'a leur reconversion sur des effets de CA.**

147. `[evitable]` (session « Extension carte Bretonnie est », soiree du 23.09.2026 ; journal
    `05-journal\2026-09-23-extension-carte\carte-papier-v2.md` § 8) **Lisser (Chaikin) le contour d'un masque qui touche
    le bord de la feuille.** Les coins de la feuille s'arrondissent : 28 000 hex de brume perdus dans la vue « avant »
    (Artois et Lyonesse apparaissaient, absents du jeu). -> **Regle : une zone « feuille moins X » se trace comme
    rectangle + contour de X en regle evenodd, jamais en lissant son propre contour.**

148. `[evitable]` (meme session) **Retoucher `carte_papier_v2.css` sans regenerer le SVG.** Le style est colle dans le
    SVG par `carte_papier_v2.py` ; seul `page_v2.py` avait ete relance : carte noire. -> **Regle : toute retouche du CSS
    de la carte = relancer `carte_papier_v2.py` puis `page_v2.py`.**

149. `[decouverte]` (meme session) **Une page HTML servie sans charset (serveur Python local) est lue en Latin-1** : une
    plage de diacritiques combinants ecrite en clair dans une regex JavaScript devient « Range out of order » et arrete
    tout le script. -> **Dans le code des pages, des echappements ASCII (`\u0300-\u036f`).**

150. `[evitable]` (meme session) **Tracer les frontieres de provinces d'apres le masque de chaque province** : elles
    doublent la cote, en escalier. -> **Regle : les couper a l'interieur des terres (clipPath sur la terre rognee d'un
    hex) et les lisser.**

151. `[evitable]` (meme session) **Retouches de fichiers Python par heredoc, a plusieurs reprises** (rechute des erreurs
    129 et 135) : par l'outil d'edition ou un script ecrit dans un fichier.

152. `[evitable]` (construction, 23.09.2026, 19 h 06) **Captures en jeu : `open_application` sur le jeu deja lance en
    lance un second exemplaire** (« Mutex error : another instance is running »). Tant que ce second processus vivait,
    le jeu sous cdb ne traitait plus les clics ; ils sont arrives en rafale apres `taskkill` de l'intrus. Ensuite, la
    souris laissee au bord de l'ecran (bouton du bas a droite) a fait **defiler la carte toute seule** (defilement par
    les bords). -> **Regles : pour ramener le jeu devant, cliquer dans sa fenetre visible, jamais `open_application` ;
    apres chaque clic pres d'un bord, remettre la souris au centre (`mouse_move`) ; la premiere capture, prise avant
    tout geste, est la bonne (camera posee par `--pause-tour`).**

153. `[decouverte]` (construction, 23.09.2026, 19 h 20 - 19 h 35) **Plantage de rendu sans les effets de WH1, et vidage
    perdu.** Preuves : 5 essais a 5 transferts, 2 plantages (+0x1A3DCFA et +0x10CCEFC, texte a la place d'un pointeur) ;
    le premier vidage n'a pas ete ecrit parce que `dps @rdx` (rdx = texte) a interrompu la commande cdb, et le lanceur a
    classe l'essai « sortie ». `lire_dll.py vtable` echoue : exe protege, pas de RTTI sur disque. -> **Regles codees :
    pile et vidage d'abord, lectures sous `.catch`, et « plantage » des qu'une exception de seconde chance est dans
    `cdb.log` (`essai_tours_auto.py`).** Reporte dans `GUIDE.md` § 15, n° 135 (nuance) et 136.

154. `[evitable]` (session « IA et modding 3D », lot 1 du 21.09 ; trouve le 23.09.2026 a 20 h dans le vidage complet
    de Durthu, tour 6, +0x272AE00) **Rechute de l'erreur 110 par une autre table** : nos regions (le Chene, Fort
    Solstice, Grunere, Montlac, Quenelles) avaient ete AJOUTEES au groupe de CA `wh2_dlc16_forest_region_group_main_1`,
    qui garde ses 8 regions des Empires. L'infobulle des clairieres parcourt le groupe et resout le Chene des Empires
    (`wh3_main_combi_region_the_oak_of_ages`) en objet nul -> plantage (objet `[rsi+0x68]` = cette cle, `[rsi+0x70]` =
    `wh_dlc05_parravon_montlac`). -> **Regle : jamais une de nos regions dans un groupe, une liste ou une ressource de
    CA qui garde des regions d'une autre carte ; un groupe a nous (`wh_dlc05_saison_...`).** Corrige par le lot 23
    (groupe `wh_dlc05_saison_forest_region_group_athel_loren`, `saison_foret.lua`). **Ne jamais rejouer le lot 1**
    (il remettrait des lignes retirees depuis). A surveiller, meme motif : `cai_region_hint_area_athel_loren`,
    `wh3_wood_elf_forests`, `cai_region_hint_area_bretonnia`, `cai_region_hint_area_dwarf_empire`,
    `cai_region_hint_sub_area_western_mountains`, `wh3_main_transfer_settlement_excluded_regions`.
    [Préfixe remplacé le 04.10.2026 par la décision de Charles du 25.09 (`CLAUDE.md` § 2) et n° 272 : `saison_` pour
    tout ce que nous créons, `wh_dlc05_` seulement pour ce qui vient de WH1. La règle « jamais une de nos régions dans
    un groupe de CA » reste.]

155. `[evitable]` (session « Rendu de la carte », chaines 2 et 3 du 23.09.2026, 16 h 43 et 18 h 41 ; cause PROBABLE,
    a confirmer en jeu avec le terrain de la chaine 4) **Fond marin (`sea_height`) mis a la hauteur de la terre pres des
    cotes** (`CASES_DE_MER`, puis `TERRE_PRES_DE_LA_MER` a moins de 8 px), pour effacer des bords sombres en escalier.
    Charles en jeu (packs de 17 h 42 et 19 h 02) : aucune eau, un sol de galets plat du rivage au large. Preuves :
    `full_height_map.dds` compile (BC6H signe) : R = height, G = sea_height ; `tile_list.bin` = noms, puis une pose par
    enregistrement de 21 octets (tuile u16 @2, case x u16 @7, z u16 @9, rotation @11, hauteur mini f32 @13, maxi f32
    @17), bornes calculees par BOB sur sea_height ; tuiles de mer au maxi au-dessus de 0 : Empires 0,3 %, The Old World
    0 %, nous 73,8 %. Sur les quatre cartes ou l'eau se dessine, sea_height reste sous 0 partout, meme sous la terre.
    -> **Regle : sea_height sous 0 partout (au plus -0,1) ; la terre d'une case de mer est un rivage noye a -0,1 ; jamais
    la hauteur de la terre dans sea_height. Controle : aucune pose de tuile de mer au maxi au-dessus de 0 dans
    `tile_list.bin`.** Code : `terrain_wh1_vers_terry.FOND_SOUS_ZERO`, `FOND_MAX`. Reporte dans `GUIDE.md` § 15, n° 137.
    Correction de l'erreur 113 : « height vaut 0 en mediane sur la mer » n'est vrai que dans les marges hors jeu ; sur
    la mer jouable des Empires, height vaut 0,9 en mediane et n'est pas la surface dessinee (le niveau de l'eau est 0).
    **[Corrigée le 27.09.2026 : `sea_height` doit rester sous 0 seulement là où il y a de la mer ;
    s'il dépasse les plans d'eau, il les masque. Sous la terre, il n'y a pas de tuile de fond marin
    et sa valeur ne change rien. Dans WH3, toute l'eau vient des maillages posés (ChaosRobie).
    `FOND_SOUS_ZERO` peut rester tel quel.]**

156. `[evitable]` (session « IA et modding 3D », lot 23 ; attrape par l'essai de demarrage du startpos, 23.09.2026,
    20 h 25) **Groupe de regions neuf absent du pack** : le lot 23 tenait l'entree `region_groups` du lot 1 pour un
    prefixe (`wh_dlc05_`), alors que c'est une LISTE EXPLICITE de cles (`cles_region_groups()`, `tables_gameplay`
    ligne 31). Les 5 jonctions sont entrees dans le pack, pas le groupe : le jeu refuse tout le pack
    (`bad_mods_report.txt` : `wh_dlc05_saison_forest_region_group_athel_lorenwh_dlc05_oak_of_ages`). -> **Regle : tout
    groupe neuf passe par `cles_region_groups()` ; chaque `region_group` cite par une jonction du pack existe dans le
    pack ou dans le jeu (controle a coder, propose par la session « IA et modding 3D »).** La regle de l'erreur 107
    (essai de demarrage avant toute annonce) a joue son role.
    **[Codé : `02-scripts\verifier_groupes.py`, à lancer avant le pack (`CLAUDE.md` § 5).]** [25.09.2026, ménage]
    [Préfixe `wh_dlc05_saison_` remplacé le 04.10.2026 par `saison_` (décision de Charles du 25.09, `CLAUDE.md` § 2 ;
    n° 272).]

Session « Extension carte Bretonnie est » (23.09.2026 ; detail : `05-journal\2026-09-23-extension-carte\carte-papier-v2.md`
§ 9 ; rien de cette session ne touche le pack, le startpos, le terrain ni le jeu) :

157. `[evitable]` **Heredoc encore utilise pour retoucher des fichiers Python** (`sceaux.py`, fichiers d'essai) : rechute
    des erreurs 129, 135 et 151. -> **Regle : l'outil d'edition, toujours ; jamais un heredoc pour modifier un fichier
    de code.**

158. `[evitable]` **Bande d'un cadre tracee en deux rectangles pleins emboites** : toute la carte recouverte de velin.
    -> **Regle : un anneau se trace en un seul chemin `evenodd` ; regarder le rendu apres tout ajout de forme pleine
    autour du contenu.**

159. `[evitable]` **Longs traces d'un SVG decoupes en morceaux, chacun sous masque** : cent fois plus d'elements a
    `clip-path` dans la vue « avant · apres », regression de lenteur dans cette vue seulement. -> **Regle : apres un
    changement de structure du SVG, mesurer chaque vue ; un masque se pose sur un groupe, pas sur chaque morceau.**

160. `[decouverte]` **Images collees dans la conversation** : ce ne sont pas des fichiers lisibles ; demander a Charles
    de les enregistrer (il les met dans `Downloads`).

161. `[decouverte]` **Essais de page web par Edge sans fenetre** : la fenetre ne descend pas sous ~500 px de large
    (emuler le telephone par `Emulation.setDeviceMetricsOverride`) ; en `file://`, `/favicon.ico` n'existe pas (faux
    positif) ; `Blob.text()` retire la marque d'ordre des octets (verifier les octets) ; `new Response('', {status:
    204})` leve une erreur (corps nul obligatoire pour un 204).

162. `[decouverte]` **Fluidite d'un SVG mesuree par trace du protocole de debogage** (fil `CrGpuMain`,
    « RasterDecoderImpl::DoRasterCHROMIUM::Deserializing ») : les traces geants a boite englobante pleine carte sont
    re-decodes pour chaque tuile ; decoupes en morceaux ranges par cases, sans `clip-path`, le travail des zooms passe de
    6,2 s a 2,6 s.

Session « Rendu de la carte » (23.09.2026, soir) :

163. `[decouverte]` (a confirmer en jeu) **La mer d'une carte faite avec Terry et BOB demande de grands plans d'eau**
    (`ECPolygonMesh` au materiau d'eau de la carte, a y = 0), comme les Empires (997 plans) ; le relief seul, meme avec
    le fond sous 0 (erreur 155), ne donne pas d'eau. Notre projet n'en avait que pour les 26 etangs. Code :
    `terrain_wh1_vers_terry.polygones_mer`, calque `mer_wh1`. Reporte dans `GUIDE.md` § 15, n° 138.
    [Confirmée le 27.09.2026 (ChaosRobie : dans WH3, toute l'eau vient des maillages posés) et par n° 318.]

164. `[decouverte]` **BOB ecarte un `ECPolygonMesh` dont le pivot est hors de la carte**, avec le seul avertissement
    « Failed to find valid quadtree node for Polygon Mesh entity » ; l'entite manque alors dans `global_props.bin`.
    Les plans des Empires ont tous leur pivot dans la carte, meme quand leurs points en sortent. Code : pivot interieur,
    a 0,5 u des bords (`MER_PLAN_BORD_PIVOT`). Controle : compter les plans d'eau de `global_props.bin`. Reporte au
    n° 138.

165. `[evitable]` **Deux generateurs ecrivaient le meme fichier du kit avec deux contenus differents** (montagnes et
    objets, `empire_mountain_small_01/*_material_map.dds`). -> **Regle : un dossier de sortie par generateur.**
    Controle propose pour `build_pack` : refuser un chemin present dans deux dossiers embarques avec des octets
    differents (a coder par la construction).

Session « Extension carte Bretonnie est » (23.09.2026, soiree ; rien ne touche le pack, le startpos ni le terrain) :

166. `[evitable]` **Scripts Python encore ecrits par heredoc** (outils de remplacement, retouche d'`images_recit.mjs`) :
    rechute des erreurs 129, 135, 151 et 157. -> **Regle : ecrire par l'outil d'ecriture, retoucher par l'outil
    d'edition.**

167. `[evitable]` **Outil de remplacement « ancien=nouveau » coupe au premier « = »** : deux fichiers d'essai abimes. ->
    **Regle : jamais un separateur qui peut figurer dans le motif ; pour du code, l'outil d'edition.**

168. `[decouverte]` **Git Bash (MSYS) convertit en chemin Windows tout argument contenant « / »** (par exemple
    « </main> ») : le motif arrive altere au script. -> **`MSYS_NO_PATHCONV=1` pour les arguments bruts.**

169. `[decouverte]` **Edge sans fenetre, emulation de telephone** : une sonde qui appelle `getComputedStyle` a chaque
    changement de classe (MutationObserver) fige la page (5 images en 25 s). -> **Mesurer le telephone sans sonde, ou
    avec une sonde legere.**

170. `[evitable]` **Captures d'une zone de carte peignant toute la page de 15 000 px** (plus de 25 min). -> **Pendant
    une capture, cacher le reste de la page (environ 10 s par image au lieu de 27).**

171. `[evitable]` **Trois faux echecs d'essais de page, machine chargee** (animations plus longues que les attentes). ->
    **Relancer l'essai seul avant de conclure a une regression.**

172. `[evitable]` **Phrases de lore fausses publiees sur le site** (objectif de la Fee, « Cor de la Chasse » au lieu de
    « Cor de la nature », source de Gotrek et Felix, raids et guerres de depart), corrigees apres audit. -> **Toute
    phrase de lore publiee repasse par les dossiers sources du projet, par un audit, avant la mise en ligne.**

173. `[evitable]` (construction et session de l'extension, 23.09.2026, 22 h 50) **`positions_colonies.json` lu comme les
    positions des villes en jeu** : pour les ports il donne un hex de PORT cote mer, pour l'interieur le centre de la
    REGION, et son « affichage » oublie le decalage des colonnes impaires. On a cru Bordeleaux et Brionne 1 u au large ;
    les vraies positions (map_data.esf, REGION_KEYS : x = 0,667995 q ; z = 0,771334 r + 0,3857 si q impair) sont
    justes et identiques a WH1 pour les 54 colonies de l'interieur. -> **Regle : la position d'une colonie se lit dans
    map_data.esf ; note `positions_colonies.LISEZMOI.md` posee a cote du fichier.**

174. `[evitable]` (construction, 21.09 ; trouve le 23.09.2026 a 23 h 20) **Couches du projet pas mises a jour apres le
    recentrage des ports** : `04-projets\...\couches-slots\layer_town_slots.hex_layer` (20.09) differait de 46 hex de la
    couche du kit, tous sur les 3 ports ; `terrain_wh1_vers_terry` et `ajouts_carte_wh3` la lisent : le terrain et le
    jeu n'avaient pas les memes ports. -> **Regle : apres tout import de couche dans `map.hex`, copier les memes
    `.hex_layer` dans `couches-slots` (sauvegarde de l'ancienne) et relancer la chaine du terrain.** Fait le 23.09 a
    23 h 33 avec le retour des ports a leur hex de WH1 (`02-scripts\placer_ports_wh1.py`, demande de Charles :
    Bordeleaux (35,255), Brionne (23,183), Mousillon (53,302) ; map_data.esf les place bien, sans position 0xFFFF,
    malgre 3 hex de port tous en mer).
    [Ports : règle remplacée le 04.10.2026 par n° 337 (chez CA, deux hex de port en mer et un sur la plage ; règle
    pour Expanded et toute carte neuve). La Saison garde ses ports [mer, mer, mer], validés en jeu (décision de
    Charles, 04.10). La règle des couches (copier les `.hex_layer` dans `couches-slots`) reste.]

175. `[evitable]` (session « Rendu de la carte » et construction, 23.09.2026, 23 h 53) **Chaine du terrain tuee par
    manque de memoire** (`_ArrayMemoryError` dans `rivieres_wh1.composantes`) : deux diagnostics sur toute la carte
    tournaient pendant le generateur, en meme temps qu'un essai en jeu sous cdb qui ecrivait un vidage complet de 14 Go.
    -> **Regles : aucun calcul sur toute la carte pendant le generateur d'une chaine ; pas de partie en jeu pendant une
    chaine (la construction retient ses essais) ; memoire libre verifiee avant de lancer.** Les vidages complets
    (`--vidage-complet`, 13 a 15 Go chacun ; 144 Go dans `2026-09-23-essais-auto` le 23.09 a minuit) seulement quand un
    vidage doit etre analyse.

176. `[evitable]` (session « Extension carte Bretonnie est », 24.09.2026 vers 01 h) **Heredoc Python encore utilise**
    pour remplacer deux libelles dans `guide_caime.py` (rechute des erreurs 129, 135, 151, 157 et 166 ; pas de degat,
    sortie console mal encodee). -> **Regle : toute modification d'un fichier source par l'outil d'edition ; jamais un
    script Python ou Lua par heredoc, meme d'une ligne ; une retouche repetitive par un script ecrit comme fichier puis
    lance.** Sixieme rechute : la regle est a relire en tete de chaque seance (A1 a A5).

177. `[evitable]` (construction, 24.09.2026, 00 h 42) **Jeu lance directement pour un diagnostic, sans prevenir Charles**
    (rechute des erreurs 124 et 132) : la generation du startpos sortait en 3 a 6 s sans rien ecrire, juste apres le
    redemarrage des sessions ; le jeu, lance a la main, demarrait normalement ; la generation suivante a marche. ->
    **Regle : prevenir Charles avant TOUT lancement du jeu, meme de diagnostic ; une generation qui sort en quelques
    secondes sans rien ecrire se relance une fois (etat passager de Steam) avant d'enqueter.**
    [Précisée le 04.10.2026 par n° 329 et n° 331 : une fermeture silencieuse en 9 à 13 s vient aussi des données (une
    jonction `*_ownership_content_pack_junctions` sur une clé à nous, `campaigns.mask` non vide) ; après une relance
    sans effet, chercher d'abord ownership et `mask`.]

178. `[evitable]` (construction, 23-24.09.2026 ; releve par la session « IA et modding 3D » a 01 h) **Parties de Charles
    jouees avec le pack d'essai** : un essai arrete de force (TaskStop) ne fait pas son menage ; `user.script.txt`
    gardait « mod zz_saison_essai_auto.pack; », et l'essai suivant le « restaurait » tel quel en fin de partie. Le pack
    d'essai pose `_G.saison_essai_auto`, qui coupe intros, prologues, video et choix d'office : Charles ne voyait plus
    aucune cinematique. -> **Regles codees (`essai_tours_auto.py`) : `script_propre()` retire nos lignes d'essai avant de
    garder le fichier de Charles ; `--nettoyer` (user.script propre, packs d'essai retires, drapeaux ranges) a lancer
    apres TOUT arret force, avant de rendre la main a Charles ; prevenir Charles quand un essai tourne.**

Session « Rendu de la carte », nuit du 23 au 24.09.2026 (la panne de memoire de la chaine 8 est l'erreur 175) :

179. `[decouverte]` **Registre des textures de sol** : `warscape_asset_variation_db/terrain_textures_campaign.assetdb` a,
    dans ses espaces `campaign_base_colour`, `campaign_material` et `campaign_normal`, exactement les 144 cles de la liste
    compilee de BOB, dans le meme ordre. Un groupe non declare (nos `wh1_*`, index 144 a 160) prend la DERNIERE texture
    du tableau (`wasteland_chaos3`, cendre grise) : « les terres desolees du Chaos » (Charles, 23 h 35). -> **Regle :
    declarer tout groupe neuf dans une copie de la base, a la suite et dans l'ordre (`textures_sol_wh1.base_variantes`,
    gardes dans `remplacements_base_variantes`, exception de `build_pack`) ; la refaire a chaque mise a jour du jeu (la
    copie masque celle de CA tant que le mod est actif).** La base porte aussi, par carte,
    `campaign_texture_terrain/campaigns/<carte>` -> `water_plane_material`. Reporte au GUIDE § 15, n° 139.
    [Moyen remplacé le 04.10.2026 par n° 341 (catalogue séparé, mise à jour 1 du 25.09 ; `CATALOGUE_SEPARE = True`) et
    n° 254 : aucun fichier de CA remplacé, plus de copie de la base au chemin de CA. Le fait (groupe non déclaré = dernière
    texture du tableau) reste.]

180. `[evitable]` **Montagnes drapees sans leurs normales** (`montagnes_wh1.draper`, 22.09) : sommets deplaces sans
    transformer normales ni tangentes ; ecart median des normales a la surface 9,8° (WH1 : 2,9°), eclairage faux. ->
    **Regle : toute deformation d'un maillage transforme ses normales (inverse transposee) et ses tangentes
    (jacobienne).** Code : `montagnes_wh1.NORMALES_DRAPEES`, `PENTE_DRAPE_PX = 1,5` ; sommets : normale, tangente,
    bitangente en u8 z, y, x aux octets 16, 20, 24.

181. `[decouverte]` **`lf_normal.dds` : BOB n'en fait pas pour une campagne**, et le jeu eclaire le relief lointain avec
    elle. Chez CA elle suit le relief (correlation 0,89 / 0,91 aux Empires) ; la notre, celle de WH1, ne suivait plus
    notre relief (0,25) : deux eclairages, piste du « carre de luminosite » au dezoom (effet a confirmer). Codage : DXT5,
    R 255, B 0, A = nx, G = nz vers le sud, k = 2,35. `02-scripts\lf_normal_depuis_relief.py`, a relancer apres tout
    changement de relief (etape a reporter dans `chaine_terrain.ps1`). Reporte au n° 139.
    **[Au 25.09, `chaine_terrain.ps1` n'appelle toujours pas `lf_normal_depuis_relief.py` ; les chaînes 12 à 15 du rendu l'appellent (`chaine_sans_pack*.ps1`).]** [25.09.2026, ménage]

182. `[decouverte]` **Rivieres trop larges** : notre eau couvrait 3,8 fois les rubans d'eau de WH1 ; dans WH1, c'est un
    filet d'eau sur un lit de sable plus large. Retrecissement demande par Charles (chaine 9).

183. `[decouverte]` **Un redemarrage de session tue les chaines lancees en arriere-plan** : a 00 h 18, le projet de la
    chaine 8 etait reste avec la compilation de la chaine 7. -> **Regle : apres un redemarrage, relire la derniere etape
    du journal de chaine et les dates des fichiers compiles avant tout pack.**

184. `[evitable]` (session du rendu) **Deux scripts de brouillon ecrits par heredoc et un `python` par heredoc**
    (septieme rechute de l'erreur 129, sans degat). Meme regle.

185. `[evitable]` (session du rendu, 24.09.2026, 01 h 38 et 01 h 57 ; plus un `python -c` a chemins Windows qui a
    plante sur l'echappement a 02 h 00) **Python par heredoc et `python -c` a antislashs**, huitieme rechute, sans degat
    (brouillons seulement). -> **Regle durcie : tout code Python de plus d'une ligne, meme un controle, passe par un
    fichier ecrit avec l'outil d'ecriture ; jamais de heredoc, jamais de `python -c` contenant des antislashs ou des
    chemins Windows.**
    [Remplacée le 04.10.2026 par n° 267 (avec 176, 199) : tout code Python passe par un fichier, MÊME d'une ligne ;
    c'est ce qu'applique le garde `garde_commandes.py` (n° 212).]

186. `[evitable]` (construction, 24.09.2026, 01 h 42) **Conclusion tiree sur 5 essais** : « sans les montagnes de WH1,
    0 plantage sur 5 » annonce a Charles comme la cause trouvee ; les 4 parties suivantes ont plante 3 fois (3 sur 9 au
    total). Avec un plantage aleatoire d'environ 1 partie sur 2 a 1 sur 3, 0 sur 5 arrive par hasard 3 a 13 % du temps.
    -> **Regle : pour un plantage aleatoire, 10 essais au moins par variante avant toute conclusion, et annoncer « piste »
    et non « cause » tant que ce n'est pas le cas.**

187. `[evitable]` (arbres de WH1, 22.09 ; trouve par la session du rendu le 24.09.2026 a 02 h 30 ; PISTE du plantage de
    rendu +0x1A3DCFA / +0x10CCEFC, qui persistait sur un terrain sans aucune entite posee, la liste des arbres etant a
    part) **Liste des arbres de WH1 non conforme a CA** : (1) octet 12 de chaque enregistrement a 0 (recopie de WH1),
    alors que BOB et toutes les listes de CA ont 1 ; (2) 5 identifiants sans variante BASE (`wh1_tree_small_5`,
    `wh1_shrubs_grass_4/5`, `wh1_al_shrubs_grass_4/5`, environ 5 300 arbres) : pas de modele quand la culture du
    proprietaire n'a pas de variante (ruine, Hommes-betes, Peaux-vertes, Nains). Corrige le 24.09 a 02 h 36-02 h 42
    (liste embarquee, 5 lignes BASE ; `arbres_wh1.OCTET_12_COMME_BOB`, `BASE_DE_SECOURS`), pack de 02 h 43. -> **Regle :
    toute liste ou table d'arbres a nous est comparee champ par champ a celles de CA (octets, variante BASE pour chaque
    identifiant) avant d'entrer au pack.** A confirmer par les parties de Charles.

188. `[evitable]` (construction, lanceur d'essais, 23.09.2026 ; trouve par l'audit du 24.09 a 02 h 45) **Camera jamais
    posee dans les essais** : intros coupees, la camera restait a sa position de depart, hauteur 100 environ (4 a 38 en
    jeu normal) ; les 21 plantages de rendu +0x1A3DCFA / +0x10CCEFC dont la camera est journalisee sont TOUS a 100 ou plus
    (hasard : environ 0,2 %), et le risque est environ 50 fois plus fort au premier affichage de la carte qu'ensuite.
    Le plantage de rendu est donc au moins en partie un effet du lanceur (carte entiere dessinee de tres haut, arbres
    compris), jamais vu par Charles en jeu normal. Le lanceur cliquait aussi « Continuer » dans le tick meme du premier
    appel. -> **Regles codees (`essai-auto\...\saison_essai_auto.lua`) : camera posee sur le chef a hauteur de jeu au
    premier tick et a chaque round ; « Continuer » 5 s apres le premier tick. Un essai automatique doit reproduire ce que
    vit un joueur, sinon ses plantages ne prouvent rien sur le mod.**

Correction de fond signalee par la meme session : `lore-region-saison.md` § 7.1 dit qu'Aislinn n'a aucun lien de lore
avec la region ; c'est contredit par l'Arcane Journal « High Elf Realms » (The Old World), p. 7 : Tor Martel, « sur la
plus grande des iles Martel, visible des murs de Mousillon », est sa forteresse (a reporter par la session « IA et
modding 3D », redactrice de `lore-region-saison.md` ; la redactrice de CE fichier-ci est la session Construction,
voir `CLAUDE.md` § 3). **[Fait le 25.09.2026 vers 03 h 45 par la session « IA et modding 3D » (l. 44 et 761, source
marquée ‡, non relue par nous).]** [25.09.2026, ménage]

189. `[evitable]` (session de l'extension, 24.09.2026, 03 h 20 - 03 h 35 ; signale par elle) **Deux rechutes sans
    degat, verifiees par grep** : un `python - <<'EOF'` pour retoucher `atelier_v2.py` (rechute des erreurs 129 et
    185) et un `sed -i` a motifs `\/` sous Git Bash sur `schemas_suite.py` (regle de `CLAUDE.md` § 6). -> **Regle :
    toute retouche de fichier passe par l'outil d'edition, meme de trois remplacements ; jamais heredoc ni sed.**

190. `[decouverte]` (relecture du code de RPFM a l'etiquette v5.0.6 par la session de l'extension, 24.09.2026, 03 h 45)
    **RPFM n'ecrit pas `add_working_directory` pour Warhammer III.** Dans `build_starpos_pre`, cette ligne n'est
    ecrite que pour Attila et Thrones of Britannia ; pour WH3, `user.script.txt` recoit une seule ligne `mod` (le pack
    ouvert). Le script releve le 20.09 « extrait des chaines de `rpfm_server.exe` » (decouvertes du 20.09, plus haut)
    melangeait donc les chaines de plusieurs jeux ; la ligne `add_working_directory` des essais qui sortaient en 9 s
    venait de nos propres scripts (erreurs 36 et 39), ce que `startpos_manuel.py --sans-working-dir` corrige deja.
    -> **Regle : une commande « extraite des chaines » d'un binaire multi-jeux n'est qu'une piste ; la confirmer dans le
    code source a la bonne etiquette.** Reporte dans `GUIDE.md` § 4.2 (RPFM 5.0.6 : menus, clic droit sur la racine,
    `twad_key_deletes`, `build_starpos_post`).

191. `[evitable]` (textes, trouve par la session de l'extension, corrige par la session « IA et modding 3D » le
    24.09.2026 vers 03 h 50) **« Verene » au lieu de « Verena »** dans `textes_gameplay.json` (Turris Vigilans),
    `monuments-lore.json` et des commentaires de `saison_chroniques.lua` ; la forme officielle est dans `local_fr.pack`.
    Rechute de l'erreur 139. -> **Regle : un nom propre de Warhammer se verifie dans le `.loc` francais du jeu avant
    d'etre employe.**

192. `[evitable]` (session du rendu, `ajouts_carte_wh3.arbres` ; trouve par la construction le 24.09.2026 a 04 h 00 sur
    l'ecart entre le bilan de la chaine 9, 80 451 arbres, et le journal du pack, 80 997) **L'octet 12 remis a 0 pour
    546 touffes d'herbe de montagne de WH1** (code en dur « 0 si wh1_ »), alors que la regle de l'erreur 187 veut 1
    partout ; le pack de 03 h 52 en porte 551 a 0. Corrige a 04 h 02 (toujours 1). -> **Regle : un bilan de chaine et
    le journal du pack comptent la meme chose ; un ecart de compte se tire au clair avant d'annoncer le pack, et une
    regle d'octet se code a un seul endroit, sans exception par prefixe.**

193. `[evitable]` (session de l'extension, un agent dessinateur, 24.09.2026 vers 04 h 20) **Rechute de l'erreur 129** :
    petit script Python passe par heredoc sur l'entree standard pour verifier des imports ; rien d'ecrit, sans degat.
    -> Meme regle : pas de heredoc ni de `python -c` compose ; un script de verification s'ecrit dans le scratchpad avec
    l'outil d'edition. **A transmettre a chaque agent lance** (les sous-agents ne lisent pas ce fichier).

194. `[decouverte]` (relecture du code de RPFM 5.0.6 par la session de l'extension, 24.09.2026) **Trois pieges de RPFM
    et du kit** : *Install* refuse un pack ouvert depuis `data\`, alors que *Build Startpos* l'exige (ouvrir le pack
    ailleurs pour l'installer, depuis `data\` pour le startpos) ; *Load All CA Packs* est grise quand le cache des
    dependances est charge ; `raw_data\db` mele nos lignes a celles de CA (lots de `donnees_campagne.py`) : ne jamais
    s'en servir pour compter les lignes de CA, compter dans les packs du jeu.

195. `[evitable]` (session du rendu, 24.09.2026, 04 h 29 ; signale par elle) **`python - <<'EOF'` vide lance par
    megarde** : rien d'execute ni d'ecrit, mais c'est la forme interdite (erreurs 129, 185, 189, 193 : quatrieme rechute
    en une nuit, toutes sessions confondues). -> **Regle inchangee ; la frequence dit qu'il faudrait la coder** : un
    crochet qui refuse toute commande contenant `<<` suivi de `python` serait plus sur qu'un rappel (proposition a
    soumettre a Charles, car c'est un reglage de configuration).
    **[Fait le 24.09.2026, 19 h 55 : `garde_commandes.py` (erreur 212).]** [25.09.2026, ménage]

196. `[evitable]` (session de l'extension, agent des schemas du guide Terry, 24.09.2026 avant 04 h 31 ; signale par
    lui-meme) **Script Python de lecture par heredoc**, rien d'ecrit. Cinquieme rechute de l'erreur 129 cette nuit
    (189, 193, 195, 196 et la 185 de la veille), alors que la consigne est dans le brief de chaque agent. -> **Le
    rappel ne suffit plus : proposer a Charles le crochet de l'erreur 195** (refus de `python - <<`, `python3 - <<` et
    `python -c` avec antislashs), seule facon de rendre la regle automatique.
    **[Fait le 24.09.2026, 19 h 55 : `garde_commandes.py` (erreur 212).]** [25.09.2026, ménage]

197. `[evitable]` (session du rendu, 24.09.2026 vers 04 h 33 ; corrige par elle a 05 h 05) **Images « V1_*.jpg » lues
    comme WH1** alors que c'etait la premiere video de WH3 (interface de WH3 visible) : deux conclusions fausses
    transmises (« la cote de WH1 est en escalier », « WH1 a aussi le carre »), et la seconde relayee a Charles par la
    construction. La vraie image de WH1 a 82 s (`denses\WH1_0082s.jpg`, interface de WH1) montre bien une limite
    rectiligne du brouillard, mais en diagonale : indice, pas preuve. -> **Regle : identifier le jeu sur l'image elle-
    meme (interface, portrait, minicarte) avant de conclure ; nommer les images par jeu ET par video
    (`WH1_`, `WH3V1_`, `WH3V2_`), jamais `V1` seul.**

198. `[evitable]` (session de l'extension, agent d'audit des schemas du guide IA, 24.09.2026 avant 05 h 05 ; signale par
    lui-meme) **`python -c` a plusieurs instructions et deux `python - <<'EOF'`** pour lire une feuille de style et
    decouper des images ; lecture seule, rien d'ecrit. Rechute des erreurs 129, 185 et 193.

199. `[evitable]` (construction, 24.09.2026 entre 04 h 30 et 04 h 50 ; trouve en relisant ma propre nuit a l'occasion de
    la 198) **Moi aussi : trois `python -c` a plusieurs instructions avec des chemins Windows** (recadrages de la video
    V2, images de WH1 a 74/77/82 s, paire des embouchures), et un `python -c` plus tot pour lire la taille de la video.
    Lecture et images de travail seulement, rien dans le kit ni le pack. C'est exactement l'erreur 185, commise par la
    session qui tient ce fichier. -> **Meme regle, pour moi d'abord : tout script dans un fichier du scratchpad ecrit
    avec l'outil d'edition, meme de trois lignes. Six rechutes en une nuit (189, 193, 195, 196, 198, 199) : le crochet
    de l'erreur 195 est a proposer a Charles des son reveil.**
    **[Fait le 24.09.2026, 19 h 55 : `garde_commandes.py` (erreur 212).]** [25.09.2026, ménage]

200. `[evitable]` (session du rendu, `etangs_wh1`, regle « riviere » du 23.09 ; trouve le 24.09.2026 a 05 h 17 sur le
    retour de Charles) **Une mare de WH1 videe par une regle generale** : les elargissements de riviere de WH1 flottaient
    au-dessus de leur riviere, donc tout etang traverse par une riviere a ete abaisse au niveau de celle-ci. La mare sous
    la Clairiere Royale, une vraie cuvette qui tient son eau dans WH1, a perdu 32 a 42 cm : mare a moitie vide et creux
    sec derriere la cascade de la gorge. -> **Regle : une correction generale de niveau d'eau se verifie cas par cas
    sur les plans d'eau de WH1 qu'elle deplace de plus de 10 cm (liste imprimee par la chaine), et le niveau de WH1 est
    garde quand la cuvette de WH1 le tient** (`etangs_wh1.NIVEAU_WH1_SI_CUVETTE`, chaine 11).

201. `[evitable]` (session du rendu, 24.09.2026 vers 05 h 10) **Vue de controle trompeuse** : la premiere vue de dessus de
    Mousillon dessinait les trous des maillages de sol de WH1 (routes, rivieres, falaises) comme des tranchees sombres ;
    Charles y a lu « il manque des choses a terre ». -> **Regle : une vue de controle montree a Charles comble d'abord
    les trous des maillages de WH1 (relief de base), et sa legende dit ce qui est mesure et ce qui ne l'est pas.**

202. `[evitable]` puis `[decouverte]` (conversion des modeles de WH1, `fichiers_wh1.Relocateur`, recette « glace » ;
    trouve le 24.09.2026 a 05 h 26 par un agent de recherche de la session du rendu, sur la remarque de Charles « pics de
    glace tres moches ») **Cristaux de glace de Tal Amere rendus en metal** : la recette copiait le speculaire de WH1
    (165) dans le canal rouge du `_material_map`, que `rigid_default` de WH3 lit comme du metal ; 196 cristaux et 11
    statues de glace devenaient lavande terne. Corrige : `METAL_GLACE = 14` (glace de CA `gen_icicle`), application par
    `modeles_wh1.py --apply` apres la chaine 11. -> **Regle : une recette de conversion de materiau se verifie contre le
    shader de WH3 qui la lira (sens de chaque canal), pas contre la conversion d'un autre objet** ; reporte dans
    `GUIDE.md` § 15 n° 140. A controler : gemmes du Massif d'Orquemont (86 poses, metal 175).

203. `[evitable]` (construction, `build_pack.py` ; trouve le 24.09.2026 a 05 h 40 sur un signalement de la session du
    rendu, « 1 399 river_wh1_<n>.wsmodel orphelins ») **Le pack est rouvert, jamais recree : ses restes s'accumulent.**
    Releve (`scratchpad\restes_pack.py`) : 2 868 entrees sans source trouvee par mon script, dont 2 798 anciens maillages
    de riviere orphelins. -> **Regle codee : `build_pack` retire ces restes (motif `restes`) ; a faire : reconstruire le
    pack a neuf (ou retirer toute entree qu'aucune source ne fournit).**
    Seconde faute, dans la meme correction (05 h 45, corrigee par la session du rendu) : j'ai d'abord classe en « restes »
    six textures `ice0|ice2` aux chemins de CA, en ecrivant qu'elles remplacaient la glace de CA partout. Faux : c'est
    l'exception voulue `textures_sol_wh1.remplacements_glace` (neige de WH1, decision de Charles du 23.09), ajoutee par
    `build_pack` lui-meme, et CA ne peint ces groupes dans aucune campagne. Mon releve des sources ne connaissait pas les
    sources calculees (listes de remplacements). -> **Regle : avant de retirer un fichier « sans source », chercher son nom
    dans `build_pack.py` et les modules qu'il appelle ; un releve de sources par dossiers ne voit pas les sources
    calculees.**

204. `[evitable]` (session de l'extension, 24.09.2026 vers 05 h 25 ; signale par elle) **Six agents dans un meme fichier
    Python partage** (`schemas_atelier.py`), chacun sur sa fonction : un crochet perdu l'a rendu non compilable pendant
    moins d'une minute, et tout agent qui importait le module pouvait tomber dessus. -> **Regle : dans un fichier partage
    par plusieurs agents, une modification a la fois, compilee aussitot (`python -m py_compile <fichier>`) avant la
    suivante ; mieux, un fichier par agent.**

205. `[decouverte]` (session de l'extension, 24.09.2026 ; reporte dans `GUIDE.md` § 15 n° 141) **L'outil d'edition et
    les sequences d'echappement Unicode** : un texte qui contient la sequence d'echappement « barre oblique inverse, u, 00a0 » ecrite en toutes lettres dans le
    source n'est pas trouve, et dans le texte de remplacement l'outil ecrit un vrai caractere insecable a la place de la
    sequence (valable en Python, mais different du reste du fichier). Une ligne cassee en a resulte. -> Viser un morceau
    voisin sans la sequence, ou passer par un script ecrit avec l'outil d'ecriture ; relire la ligne apres.

206. `[decouverte]` (24.09.2026, 17 h 13 ; construction) **Steam met a jour l'Assembly Kit APRES le jeu (ici 1 h plus tard)
    et reecrit `raw_data\db` : toutes nos lignes du kit ont disparu** (1 322 XML ; le terrain, `working_data` et nos
    packs n'ont pas ete touches). Un `build_pack` lance a 17 h 13 a echoue (tables « absentes ») sans enregistrer. Remede
    : `02-scripts\restaurer_lignes_kit.py` (nos lignes reconnues a leur `record_timestamp` >= 20.09.2026 et a leur
    `record_uuid` absent du kit neuf ; source = la copie la plus recente entre la photo 8.1 et `db-backups`), puis
    repasse de tous les lots (IA : 2 a 30), des arbres, des Soeurs et des fiches, puis comparaison des tables de depart au
    `zz_startpos_db.pack` et d'un pack d'essai au pack precedent (10 ecarts expliques : deux quetes du lot 10 revenues
    sans toutes leurs jonctions, lot 22 jamais embarque, 3 lignes de CA). Il a fallu aussi : schemas de RPFM 9.0
    (`update_schemas`, publies le jour meme), cache des dependances regenere (`generate_dependencies_cache`), base de
    variantes du sol refaite (`textures_sol_wh1.py --apply --refaire`). -> **Regles : apres une mise a jour du jeu, NE
    RIEN construire avant d'avoir verifie `raw_data\db` (le kit arrive plus tard) ; photo du kit (`instantane_jeu.py`)
    a la fin de chaque session qui ecrit dans `raw_data\db` ; les sauvegardes « avant ecriture » ne suffisent pas a
    restaurer la derniere ecriture de chaque table, les lots doivent rester rejouables (idempotents).** Reporte dans
    `GUIDE.md` § 15 n° 142.

207. `[decouverte]` (session « IA et modding 3D », 24.09.2026 vers 18 h, `local_fr.pack` de la 9.0) **Le nom francais
    officiel du Duc Rouge est « Duc ecarlate »** (21 textes de CA, dont son nom propre, contre 3 « Duc Rouge ») : 22
    textes corriges. Meme regle que 139 et 191 : verifier chaque nom dans le `.loc` du jeu, et le reverifier apres une
    mise a jour du jeu.

208. `[decouverte]` (session du rendu, 24.09.2026 vers 18 h 20, brouillon `calage_hiver.py`) **Caler une zone d'eclairage
    sur des images : les facteurs de luminosite par canal corrigent deja la saturation et la teinte** (0,25 -> 0,33 ;
    166° -> 193°). Y ajouter la saturation mesuree compte l'ecart deux fois (x 1,40 donnait 0,43, criard ; x 1,10
    suffit). -> Regle : appliquer d'abord les facteurs par canal, remesurer, puis corriger le reste seulement.
    **[Méthode abandonnée pour les zones le 25.09.2026 (erreur 251) : ne plus caler une zone par canal.]** [25.09.2026, ménage]

209. `[decouverte]` (session de l'extension, site de l'Atlas, 24.09.2026 vers 19 h ; sonde temporaire creee puis
    supprimee) **Supabase derriere Cloudflare : la PREMIERE adresse de `x-forwarded-for` est choisie par le client**
    (un en-tete `X-Forwarded-For: 203.0.113.99` arrive en tete, suivi de la vraie adresse). Pour identifier une
    connexion : `cf-connecting-ip` (pose par Cloudflare, qui refuse qu'un client le fournisse : 403, erreur 1000), a
    defaut la DERNIERE adresse de `x-forwarded-for` ; `x-real-ip` n'arrive jamais a la base. Concerne le site, pas le
    jeu (pas de report dans `GUIDE.md`, qui traite du modding).

210. `[decouverte]` (session « IA et modding 3D », 24.09.2026 vers 19 h 10, sur les quatre essais 9.0) **Sous
    `all_players_ai`, la faction du joueur ne joue PAS** : 0 recrue, 0 batiment, tresor qui monte (Orion, Legion,
    Mousillon), alors que les memes factions tenues par l'IA ordinaire recrutent, construisent et se battent. Les essais
    automatiques ne prouvent donc rien sur les mecaniques propres au seigneur joue (traque de Richemont, tombeau de
    Galand, victoires reussies). -> **Regle : ce qui vise la faction jouee se verifie en partie a la main (Charles) ou
    par un drapeau d'essai qui force la situation ; a faire pour le banc : trouver comment rendre la faction du joueur a
    l'IA de campagne sous `all_players_ai`.** Essai du 24.09 a 19 h 13 (construction) : laisser 60 s au lieu de 5 avant
    la fin de tour (`--delai-fin 60`) ne change RIEN (Orion : 0 recrue, 0 batiment, tresor 6 000 -> 9 426) ; aucune
    fonction de script de CA ne confie une faction humaine a l'IA (releve des 901 scripts 9.0). Donc : pour
    l'equilibrage, prendre comme siege une faction peu influente (les Soeurs, Morghur, Drycha) et lire les autres ; pour
    les mecaniques du seigneur joue, partie a la main ou drapeau d'essai.
    **[Reporté au GUIDE § 15 n° 134.]** [25.09.2026, ménage]

211. `[evitable]` (toutes sessions, 24.09.2026 ; signale par la session du rendu a 19 h 25) **Heures ecrites sans les
    verifier** : des messages ont annonce 05 h 05 pour 04 h 59, 19 h 40 pour 19 h 23 ou 19 h 55 pour 19 h 20, ce qui
    brouille l'ordre des ecritures entre sessions (preavis, « ecrit a »). -> **Regle : toute heure citee dans un message
    ou un journal vient de `date` (ou de l'horodatage d'un fichier), jamais d'une estimation.**

212. `[evitable]` (session de l'extension, agents d'audit, 24.09.2026 entre 18 h et 20 h ; signale par elle) **Nouvelles
    rechutes des erreurs 129 et 185** : un script de brouillon cree avec `sed` et des antislashs sous Git Bash ; quatre
    `python -c` a plusieurs instructions pour « un coup d'oeil rapide » (lire des donnees, la taille d'images). Lecture
    seule, hors du projet, sans degat. Neuvieme rechute du jour, malgre la consigne ecrite dans chaque brief. ->
    **Le crochet de l'erreur 195 devient necessaire** : a soumettre a Charles en priorite. **REGLE CODEE (accord de
    Charles, 24.09.2026, 19 h 55)** : `.claude\settings.json` du projet declare un crochet PreToolUse (Bash et
    PowerShell), `.claude\hooks\garde_commandes.py`, qui REFUSE Python par heredoc ou here-string, `python -c` a
    plusieurs instructions ou a antislashs, et `sed` a antislashs sous Git Bash ; 15 cas d'essai (7 refus, 8 accords),
    verifie en direct. Une panne du garde laisse passer (jamais de blocage par erreur du crochet).

213. `[decouverte]` (session « IA et modding 3D », audit de fluidite, 24.09.2026 vers 19 h 55 ; `lib_core.lua` 9.0 ;
    reporte dans `GUIDE.md` § 15 n° 143) **En jeu publie, les ecouteurs de CA ne sont PAS proteges** : `core` passe par
    `event_unprotected_callback` ; une erreur dans UN ecouteur annule l'evenement pour TOUS les ecouteurs de ce tour,
    ceux de CA compris. `xpcall` n'agit qu'avec `FORCE_PROTECTED_EVENT_CALLBACKS`. L'hypothese « ecouteurs proteges »
    de l'audit des vampires etait fausse. -> **Regle : chacun de nos ecouteurs passe par une fonction commune qui
    protege et journalise (`pcall`), sans exception.** Mesure du meme audit : nos scripts coutent quelques
    millisecondes par round ; les tours de 30 a 40 s viennent du moteur (IA de campagne, chemins).
    [Moyen précisé le 04.10.2026 par n° 231 et n° 252 : la règle unique est la protection CENTRALE de
    `core.event_callback` dans `required.lua`, avec journal nommé (« ecouteur [clé] en erreur ») ; une protection par
    écouteur peut coexister, elle n'est plus exigée.]

214. `[evitable]` (session « Illustrations », 24.09.2026 vers 19 h 45, juste avant la pose du crochet ; signale par elle)
    **Deux rechutes, lecture seule** : un `sed` a antislash sous Git Bash (« unterminated s command », remplace par
    awk) et un `python -c` a plusieurs instructions (taille d'images). Couvert depuis 19 h 55 par le crochet
    `garde_commandes.py` (erreur 212). Nouveau script de cette session : `02-scripts\controle_illustration.py` (lecture
    seule sur le jeu, planches dans `04-projets\saison-des-revelations\illustrations\controle\`).

215. `[evitable]` (session « IA et modding 3D », 24.09.2026 vers 20 h 37 ; signale par elle) **Preavis mal annonce** :
    `preavis.py heure` affiche l'heure D'ECRITURE (maintenant + 5 a 6 min), pas l'heure ou le preavis est pris ; la
    session a annonce « pris a 20 h 42, j'ecris apres 20 h 47 » alors que le minuteur autorisait 20:42:48, soit environ
    4 min 30 apres le message. Sans degat (une ligne `ui_image`, lot idempotent). -> **Regle : annoncer telle quelle
    l'heure affichee par `preavis.py heure` (« j'ecris a HH:MM:SS »), sans rien y ajouter.**

216. `[evitable]` puis `[decouverte]` (session du rendu, chaine 12, 24.09.2026 vers 21 h 13) **Chaine en echec sur une
    etape que l'essai a blanc n'appelait pas** : `eclairage_wh1.installer()` cherchait dans le materiau de neige des
    Empires (`combi_campaign_snow.xml.material`) le masque `wh3_main_combi_map_1/snow_mask.dds` ; **en 9.0, ce materiau
    ne cite plus aucun masque, le jeu lie lui-meme le `snow_mask.dds` de la campagne**. Corrige : le materiau est garde
    tel quel, seules les textures de neige de WH1 sont echangees. Projet Terry ecrit en partie, chaine relancee a
    21 h 20. -> **Regle : l'essai a blanc d'une chaine appelle AUSSI tout ce que le generateur lit dans les packs du jeu
    (`produire()`, `materiau_neige()`, etc.), surtout apres une mise a jour du jeu.**

217. `[evitable]` (session de l'extension, agent de la carte du site, 24.09.2026 soir) **Fichier `.py` vide cree par
    heredoc** (`cat > zoom_png.py <<'EOF'`), puis rempli avec l'outil d'ecriture : le garde ne visait que Python PASSE
    par heredoc. -> **Regle codee (24.09.2026, 21 h 45)** : `garde_commandes.py` refuse aussi tout fichier `.py` ou
    `.lua` ecrit par heredoc ou here-string (`>`, `>>`, `Out-File`, `Set-Content`, `Add-Content`, `tee`) ; 20 cas d'essai.

218. `[evitable]` (meme agent) **Journal redirige vers un chemin relatif faux** : rien ne s'est lance, sans degat. ->
    **Regle : chemins absolus pour les journaux et les sorties.**

219. `[decouverte]` (meme agent, carte du site de l'Atlas ; preuve : noms visibles compares avant / apres avec
    `noms_visibles.mjs`) **Un symbole de lieu-dit a moins de 12 hex d'une ville peut cacher son nom a tous les zooms**
    (Brandywyne cachait Larret). -> Regle du site : un lieu-dit a 12 hex au moins de toute ville, sinon le deplacer.
    Et apres tout changement de calage de l'atlas, relire les lignes « NON RELIEE » de `routes_extension.py` et les
    gravures de la mer (le recalage du 24.09 avait ferme le couloir des Capuches-Tordues et pose deux gravures sur une
    liaison ou sur la cote). Concerne le site, pas le jeu.

220. `[decouverte]` (chaine 12, 24.09.2026, 21 h 44 ; construction et session du rendu) **Le kit 9.0 a remplace
    `bob_terrain.modder.x64.dll` : les points d'arret de `compiler_terrain_bob.py` ne valaient plus** (garde d'empreinte :
    arret net, rien de casse). Releves en lecture seule, concordants : le code a glisse d'environ +0xAF10 ; appel de
    `record_from_name` en 0x34099 (import IAT 0x174918), retour en 0x3409F, maxx lu en `[rbx+0F4h]` a 0x341F4, meme
    disposition. Constructeurs d'actions non reportes (sites ambigus). -> **Regle codee : table `VERSIONS_DLL` par
    empreinte ; apres chaque mise a jour du kit, relever et ajouter la nouvelle empreinte avant la premiere chaine**
    (liste de controle 9.0, passation § 3).

221. `[evitable]` (session « IA et modding 3D », 24.09.2026, 22:17:07 ; signale par elle) **Ecriture pendant le cycle du
    pack** : `preavis.py attendre` bloquait la session au premier plan, elle n'a donc pas lu le « rien entre 22 h 05 et
    22 h 30 » de la construction avant d'ecrire (1 ligne `ui_image`, idempotente ; sans degat, le pack final l'a
    relue). -> **Regle : lancer `preavis.py attendre` en arriere-plan, relire les messages a la fin du minuteur, puis
    ecrire.**

222. `[evitable]` (construction, 23.09.2026 00 h 50, compris le 24.09.2026 22 h 50 grace a la session du rendu)
    **Noms de villes caches derriere le modele 3D : un seul reglage, devine, au lieu des valeurs de WH1.**
    `etiquette_chene.py` avait mis `citybar_height_offset` = 3 au seul Chene, sans lire le kit de WH1 ni mesurer l'unite.
    Or WH1 relevait 13 des 57 colonies de la Saison (Chene, Mousillon, Gisoreux, palais d'Argwylon, cols et forts des
    Montagnes Grises...), et 3 laissait le bandeau du Chene dans sa couronne (modele jusqu'a ~6,7 u). Charles a vu le defaut
    en jeu le 24.09 (Chene, Mousillon). -> **Regle : un reglage d'affichage de colonie se reprend d'abord de la table de
    WH1 (colonie par colonie), puis se mesure en jeu ; jamais une valeur isolee.** Code : `etiquettes_colonies.py` (les 13
    valeurs de WH1, le Chene a 7, ecrites aussi dans `map_spec.json` pour que `declare_map.py` ne les remette pas a 0).
    Unite a confirmer en jeu au pack d'apres la chaine 13.

223. `[decouverte]` (session du rendu, 24.09.2026 22 h 45 ; golfe nord du Bidouze, mesures sur le cache de la chaine 12)
    **La cote de WH1 n'est pas plus fine que la notre dans les donnees : c'est le rendu qui differe.** Meme trace au pixel
    (mer 46 455 px contre 47 536 dans les maillages de WH1), meme escalier d'un tiers de case, meme marche de 44 cm (terre
    +0,14, fond -0,30) chez WH1 et chez nous. WH1 dessine ses tuiles de terre et de mer avec leurs aretes (diagonales des
    `*_tri`) ; WH3 simplifie la carte de hauteur de loin (LOD de BOB) : un mur d'un pixel retombe sur des mailles
    grossieres, d'ou des crans de plusieurs cases et une paroi sombre ; les falaises de cote remises en chaine 12
    (`FALAISES_DE_COTE = True`, 75 % du golfe a moins de 4 px d'une falaise) ajoutaient les murs verticaux. Ma lecture du
    GUIDE n° 104 (« WH1 lisse grace a ses maillages au pixel ») etait donc incomplete. -> **Regle : pour qu'une cote
    reste lisse dans WH3, la surface doit couper le niveau 0 en pente douce (berge d'environ 1 u) ; jamais de marche d'un
    pixel ni de falaise sur le trait de cote.** Code : chaine 13 (`cotes_wh1.LISSAGE = True`, berge en pente,
    `FALAISES_DE_COTE = False`, plan d'eau au contour du sol final). A reporter dans `GUIDE.md` § 15 apres controle en jeu.
    **Complement (25.09.2026, 00 h 05, controle dans Terry puis compile decode par le rendu)** : la chaine 13 n'avait pas
    tout regle. Le shader du sol (RigidTerrainTessellation) dessine aussi les cases de MER PLEINES voisines d'une case de
    terre (decoupe par `tile_mask` a `g_clip_threshold`, constante du moteur, au moins 0,5 u) ; or leur `height` valait
    +0,02 (`HAUTEUR_SUR_MER`, chaine 3), au-dessus du plan d'eau, avec un fosse au fond dans les cases mixtes : palier et
    fosse en crans de 0,33 u, l'escalier de la capture de Charles. -> **Regle : a moins de 2 u d'une case de terre, la
    mer pleine est au fond, sous l'eau (`PRES_DES_TERRES_PX = 24`, chaine 13 bis) ; controle : 0 px au-dessus de 0 dans
    ce rayon, sur toute la carte. Terry dessine `height` sans cette decoupe : il montre le palier en pleine mer (artefact),
    mais il a montre l'escalier du rivage avant le jeu.**

224. `[decouverte]` (session « Extension », site de l'atlas, nuit du 24 au 25.09.2026) **La page reserve plus de place
    autour d'une ville « capitale » que d'une petite ville** : le nom d'une ville posee comme petite ville ne trouvait
    plus de place (Fort Solstice dans la vue « La Saison », le Pre de Ceren a tous les zooms). Preuve : noms visibles
    compares avant / apres (`diag_nom2.mjs`). -> **Regle : le rang « capitale » des donnees suit la facon dont le nom
    est pose ; un rang propre a une vue va dans un champ a part (`capitale_extension`).** Concerne le site, pas le jeu.

225. `[decouverte]` (meme session, site) **Un drapeau ajoute est pose avant les noms des petites villes et peut cacher
    des noms voisins** (Lyonesse en vue entiere ; L'Humble Chapelle et Grunere au telephone). Preuve : sans la classe
    « majeure », le nom revient. -> **Regle : apres tout drapeau ajoute, comparer les noms visibles au bureau ET au
    telephone.**

226. `[decouverte]` (meme session, site) **Dans une province de montagne, l'ancre du nom de province tombe sur la
    forteresse** : au telephone, le nom cachait Karak Azgaraz, puis Tal Esth apres un premier decalage. -> **Regle :
    decaler le nom de province et verifier au telephone.**

227. `[evitable]` (meme session, site) **Un controle de connexite comptait la terre hors carte comme franchissable**
    (fausse fuite par les Terres Desolees). -> **Regle : un controle de connexite exclut la terre hors carte.**

228. `[evitable]` (meme session, et construction le 24.09 au soir) **Rechute de l'erreur 212** : un `python -c` a
    plusieurs instructions, refuse par le garde, rien d'execute. Le second refus signale (un `grep` a antislashs dans
    une commande qui contenait aussi `sed`) etait un **faux positif du garde** : il regardait toute la commande. Corrige
    le 24.09 vers 23 h : seul le segment qui contient `sed` compte (`garde_commandes.py`, 23 cas d'essai, 0 echec).

229. `[evitable]` (session « Extension », site de l'atlas, nuit du 24 au 25.09.2026) **Un fichier final ecrit dans le
    dossier de sortie, que la construction ecrase** : les nouvelles icones (favicon.svg, favicon.ico,
    apple-touch-icon.png) ecrites dans `travail\site\` ; `page_v2.py` recopie `travail\icones\` a chaque construction,
    et la suivante a remis les anciennes, sans bruit (vu aux tailles des fichiers). -> **Regle : jamais un fichier final
    dans un dossier de sortie ; chercher d'abord d'ou la construction le recopie, et ecrire la source** (comme
    `map_spec.json` pour `declare_map.py`, erreur 222). Code : `logo_site.py` ecrit dans `icones\` ; `icones.py` porte
    « ne plus lancer ».

230. `[decouverte]` (construction et session « IA et modding 3D », 24-25.09.2026) **`FactionTurnStart` n'atteint aucun
    ecouteur de mod sur notre carte, en mode joueur comme sous `all_players_ai`.** Preuve : sondes des essais du 24.09
    (22 h 20, 29 tours, 0 ligne) et du 25.09 (00 h 51, mode joueur, 3 tours) : `FactionBeginTurnPhaseNormal` recu a
    chaque tour, `FactionTurnStart` jamais. Mecanisme (lib_core 9.0, `core:event_callback`, l. 1967-2041) : les
    CONDITIONS de tous les ecouteurs sont evaluees dans une seule boucle, sans protection en jeu publie
    (`evt_callback = event_unprotected_callback`) ; une condition qui plante annule l'evenement pour tous, sans rien
    ecrire au journal (erreur 213 elargie). -> **Regles : nos ecouteurs de debut de tour passent sur
    `FactionBeginTurnPhaseNormal` ; un essai automatique ne prouve un ecouteur que par une ligne de journal de CET
    ecouteur ; l'IA remplace `evt_callback` par une version protegee a nous dans `required.lua` (erreurs nommees une
    fois par ecouteur), pour trouver et corriger l'ecouteur fautif.** A reporter dans `GUIDE.md` § 15 quand le fautif
    sera connu.
    **[Moyen remplacé par l'erreur 231 (`core.event_callback`) ; les fautifs sont trouvés : erreur 252.]** [25.09.2026, ménage]

231. `[evitable]` (session « IA et modding 3D », 25.09.2026 vers 01 h ; trouve par l'audit de fluidite, verifie par la
    construction) **Le remplacement d'`evt_callback` dans `required.lua` etait sans effet** : dans lib_core 9.0,
    `evt_callback` est une LOCALE du fichier (l. 19, `local evt_callback = nil`) ; l'affecter depuis notre script cree
    une globale homonyme que personne ne lit, et la ligne de journal « ecouteurs proteges » aurait affirme le contraire.
    La bonne prise : la methode `core:event_callback`, appelee par `self:event_callback` a chaque evenement (l. 2067).
    -> **Regle : avant de remplacer quoi que ce soit dans une bibliotheque de CA, verifier sa portee (`local` ?) dans le
    fichier extrait ; et prouver l'effet par le comportement (une erreur nommee, une sonde qui repond), jamais par une
    ligne ecrite par notre propre code.**

232. `[evitable]` (construction, 23-25.09.2026 ; trouve par l'audit de fluidite) **J'ai annonce « ~37 s par tour » comme
    la fluidite du jeu : c'etait le temps du pilote d'essai.** A chaque round, `saison_essai_auto.lua` attendait 5 s puis
    cliquait 30 fois une notification a une seconde d'intervalle (870 clics en 29 tours) ; la vraie fin de tour (clic →
    round suivant) : 2,25 s en moyenne, 5,8 s au plus, 1,65 s en mode joueur. `os.time()` du pilote n'avance que par pas
    de 128 s. -> **Regle : un temps de tour se mesure du clic de fin de tour au round suivant, par les horodatages du
    journal ; jamais le tour du pilote.** Code : `SAISON_ESSAI_MAX_NOTIFS` (3 sous l'IA, 30 en mode joueur,
    `essai_tours_auto.scripts_generes`).
    **[Revenu à 30 clics dans les deux modes le 25.09.2026 (erreur 239) ; la règle de mesure tient.]** [25.09.2026, ménage]

233. `[decouverte]` (session « Extension », site de l'atlas au telephone, 25.09.2026) **Lire `document.fonts.ready`
    force une mise en page complete** (trace de performance : mise en page forcee a cette ligne). Concerne le site.

234. `[decouverte]` (meme session, site) **Chaque police qui arrive apres une mise en page fait refaire toute la mise en
    page** (« Fonts changed » sur ~7 600 objets). -> **Regle : demander toutes les polices des la tete du document.**

235. `[decouverte]` (meme session) **Le processeur melange coeurs rapides et lents** : une mesure de performance n'est
    valable que navigateur attache aux coeurs rapides (logiques 0 a 11), en alternant avant / apres.

236. `[decouverte]` (meme session, site) **Le controle « fiche d'idee : details » de l'essai de participation au
    telephone est instable** (echoue une fois sur deux, meme sur la page d'avant : il lit `innerText` 700 ms apres
    l'ouverture). -> **Regle : ne pas conclure sur ce seul controle ; le relancer.**

237. `[evitable]` (meme session) **Un `.mjs` ecrit par l'API de PowerShell** (remplace depuis). -> **Regle : jamais de
    script ecrit par PowerShell ni par heredoc ; toujours l'outil d'ecriture** (famille de l'erreur 129).

238. `[evitable]` (meme session, `page_v2.ecrire_site`) **Une variable neuve portait le nom d'une variable existante de
    la meme fonction** (`empreintes`), attrapee dans la copie d'essai avant d'appliquer. -> **Regle : chercher le nom
    dans la fonction avant d'ajouter une variable.**

239. `[evitable]` (construction, 25.09.2026, 01 h 10 → 02 h 30) **J'ai reduit les clics de notification du pilote
    d'essai (30 → 3 sous l'IA) sur la foi d'un audit, sans essai court avant de m'en servir** : le clic de fin de tour
    n'etait plus accepte (BLOCAGE a chaque tour, essais de 02 h 15 et 02 h 24), ce qui a brouille le diagnostic du
    plantage de 02 h 20 (deux tours bloques mis sur le compte du pack) et coute un essai. -> **Regle : un changement du
    pilote d'essai se valide par un essai de 2 tours SEUL, sur un pack deja eprouve, avant tout essai qui juge le pack ;
    ne jamais changer le pilote et le pack dans le meme essai.** Retour aux 30 clics ; le vrai temps de tour se lit par
    les horodatages (erreur 232), pas par la duree de l'essai.

240. `[evitable]` (session du rendu, 25.09.2026, 02 h 30 ; vu par la construction avant la chaine 15) **Un reglage deja
    valide contre un defaut que Charles avait vu partir a ete baisse en silence** : `PRES_DES_TERRES_PX` ramene de 24 (2 u,
    controle « 0 px au-dessus de 0 a < 2 u » de la chaine 13 bis, qui a fait disparaitre l'escalier des cotes) a 12 par
    une seconde affectation (l. 313 ecrasant la l. 307), pour attenuer la nappe pale sous le brouillard de guerre, sans
    preuve que le moteur decoupe a moins d'1 u. Remis a 24 avant la chaine 15. -> **Regle : un parametre qui porte un
    controle valide (ici le rayon de la 13 bis) ne change qu'avec l'annonce du controle qui tombe, et le controle est
    refait sur la sortie ; jamais de seconde affectation qui ecrase la premiere dans un meme fichier.**

241 a 250 : session « Extension », site de l'atlas, nuit du 24 au 25.09.2026. **Concernent le site, pas le jeu.**

241. `[evitable]` **Capture CDP (`Page.captureScreenshot`, clip) visant la mauvaise zone** : le clip est en coordonnees de
    PAGE. -> **Regle : `clip.y = rect.top + scrollY`.**

242. `[evitable]` **Planche avant / apres faussee** : passes non alternees, l'une gardait l'etat de l'autre (cache, zoom).
    -> **Regle : une page neuve par passe.**

243. `[decouverte]` **Seuils d'apparition des drapeaux calcules sur `kFit()`** (le zoom « tout voir ») : ils changeaient avec
    la taille de l'ecran. -> **Regle : seuils relatifs au zoom de la carte.**

244. `[decouverte]` **`getBBox()` d'un `<use>` qui pointe un symbole d'une planche SVG rend la boite de toute la planche.**
    -> **Regle : mesurer le symbole lui-meme.**

245. `[decouverte]` **Le garde-fou de 4 minutes de `cdp_outils.mjs` tue Edge au milieu d'un essai long.** -> **Regle :
    decouper les essais longs.**

246. `[evitable]` **Galerie « La carte en jeu » empilee au telephone sans demander a Charles** (24.09 ; vue comme une
    regression le 25.09 a 3 h, retablie). -> **Regle : ne jamais retirer au telephone une animation ou un effet que Charles
    a valide sans son accord ; noter le choix dans le journal du chantier.**

247. `[evitable]` **Texte bilingue en `<span>` mis dans un attribut HTML (`aria-label`)** : balisage casse, « planche"> »
    affiche. Vu a la capture avant de montrer. -> **Regle : un attribut prend du texte simple ; bilingue par
    `data-aria-fr` / `data-aria-en`.**

248. `[evitable]` **Affirmation sur l'intention du code, pas sur sa sortie** : la relecture du 24.09 croyait que
    `typographie()` posait les espaces insecables ; 211 « : » sans insecable dans la page construite (corrige : 410
    posees). -> **Regle : verifier une affirmation sur la SORTIE construite** (meme famille que l'erreur 231 : prouver
    l'effet, pas l'intention).

249. `[evitable]` **Texte « Pourquoi » du decoupage du Pre de Ceren devenu faux apres un changement de geometrie.** ->
    **Regle : apres un changement de donnees ou de geometrie, chercher les textes qui le decrivent.**

250. `[evitable]` **Deux rechutes de l'erreur 212** (`python -c` compose, `sed` a antislash), refusees par le garde ; rien
    d'execute.

### Rappel de la session du 23.09.2026 (00 h 50 - ) : B. Decouvertes (reportees dans `GUIDE.md` § 15, n° 104 a 106)

- **La cote de WH1** (n° 104) : voir l'erreur 102.
- **Des objets de WH1 flottent** (n° 105) : 961 objets de 0,03 a 0,3 au-dessus de ses maillages de sol, tous en mode de
  hauteur `BHM_CLASSIC` (aucun ancrage au sol a l'execution).
- (session « IA et modding 3D ») **Le verrou de contenu payant de WH3** (n° 106) : `ownership_products` ->
  `ownership_content_pack_required_products` / `_requirements` -> `ownership_content_packs`, avec des jonctions par
  faction, sous-type, bataille, batiment et zone jouable ; en script, `cm:is_dlc_flag_enabled(produit, faction)`.
- (session « IA et modding 3D », releve des mecaniques, n° 106) : une erreur Lua dans un rappel du premier tick saute
  tous les suivants, mods et deblocage de l'interface compris ; l'ambre ne vient que des incidents des Chemins-racines ;
  `script/startpos.lua` existe dans `data_script.pack` ; `cm:get_campaign_name()` rend le nom du dossier,
  `campaign_name_key()` la cle de base ; les conseils de CA connaissent `wh_dlc05_wood_elves` et `wh_dlc05_oak_of_ages`.
  Correction de specification : les conseils du Chene cites en `scripts-mecaniques-wh3.md` § 0.8 sont dans un bloc
  commente de `wh_campaign_interventions.lua` (l. 6342-6663).
- (session « IA et modding 3D ») **`mission_text` n'existe que dans le kit** (n° 107) : un objectif scripte n'a besoin
  que de sa cle de texte.
- **Zones d'eclairage** (n° 108) : la collection que CA livre pour les Empires a ses zones en cylindres ; le projet du
  kit n'en montrait qu'une (conclusion de l'erreur 96 a nuancer : les zones ne sont pas a proscrire, les spheres oui).
- **Shaders de WH1 absents de WH3** (n° 109) : lave `lava_flowing_01` (2 686 objets, maillage a texture factice :
  lave grise), cascade `wh_waterfall_01` ; six emetteurs d'effets de campagne de WH1 retires des bibliotheques de WH3.
- (session « IA et modding 3D ») **Voix de l'histoire de WH1 presentes dans WH3** (n° 110) et **scenes Cindy v20 / v21
  -> v22** (n° 111, `cindy_wh1_vers_wh3.py`).

251. `[evitable]` puis `[decouverte]` (construction et session du rendu, 25.09.2026, 01 h - 02 h 50 ; vidéo de Charles
    de 02 h 19) **Zones d'éclairage « LSD »** : avec l'éclairage v3 (9 cylindres : 4 clairières, 3 Bretonnie, 2 zones
    vampires), l'image basculait dès qu'on entrait dans une zone (Winterheart bleu nuit, ciel et brume magenta et sol vert
    fluo, écran vert, forêt cyan, rouge-magenta), « comme une prise de LSD » (Charles). Causes : (1) la teinte de la
    Bretonnie était écrite −3,5°, lue 356,5° : dans l'anneau de fondu, le jeu interpole de 0 à 356,5 et parcourt toutes
    les teintes (shader final désassemblé) ; (2) le calage des clairières par canal (erreur 208) donnait le bleu nuit ;
    (3) une zone s'applique à tout l'écran selon le point regardé par la caméra. Découverte : les 18 zones de CA aux
    Empires ont une teinte à 0, la luminosité, le contraste et la saturation du global, des canaux égaux ; leur identité
    passe par la LUT, la couleur et la densité du brouillard, la force et la couleur du soleil. -> **Règle : une zone
    d'éclairage se fait « à la manière de CA » (notre global, plus LUT, brouillard, soleil et ambiance), jamais de teinte
    ni de calage par canal ; les zones reviennent une à une, montrées en image puis essayées en jeu (captures à trois
    hauteurs, erreur 109).** Code : `eclairage_wh1.ZONES_FACON_CA`, `ZONES_REMISES` (Winterheart seule, LUT
    `campaign_chaos_kislev`, choix de Charles sur conseil, 02 h 45). Rend caduque, pour les zones, la consigne « exactement
    comme dans WH1 » du 24.09 à 05 h 45. GUIDE § 15 n° 144.
    [Précisée le 04.10.2026 (conflit avec n° 277, 285, 286) : les captures en jeu sont faites par Charles, ou par une
    voie prouvée sans pilotage ; jamais de capture du bureau.]

252. `[decouverte]` (construction et session « IA et modding 3D », 25.09.2026, 02 h 15 - 02 h 42) **Les fautifs de
    `FactionTurnStart`** : une fois `core.event_callback` protégé (erreur 231), le journal a nommé trois écouteurs de CA
    de `wh3_campaign_bonus_values.lua` dont la CONDITION plantait à chaque début de tour sur notre carte :
    `region_gdp_leech_mother_ostankya` (l. 2690) et `create_disciple_army_mother_ostankya` (l. 2709), « attempt to index
    global 'mother_ostankya_features' » (nom relu dans le journal du jeu), et `faction_gdp_leech_yuan_bo` (l. 2765), global `matters_of_state` : des systèmes de
    Kislev et de Cathay que notre campagne ne charge pas. Leur erreur annulait l'évènement pour tous les écouteurs, de CA
    comme les nôtres, en mode joueur aussi. Preuve : sonde « [SONDE] FactionTurnStart recu » aux tours 1 à 3 après la
    protection (essai de 02 h 38). -> **Règle : un système de CA chargé sans ses dépendances casse un évènement entier ; à
    chaque montée de version, lire les erreurs nommées par la protection au premier essai et retirer les écouteurs sans
    objet (`saison_start.lua`, par leur nom), plutôt que de créer des globales factices.** GUIDE § 15 n° 148.

253. `[decouverte]` (session du rendu, audit des calques, 25.09.2026 vers 01 h) **Nos images de correspondance des
    régions étaient à l'envers (nord en bas)** : CA écrit ses lookups TGA ligne 0 au NORD, octet 17 = 0x10, et le jeu lit
    les lignes dans l'ordre du fichier sans tenir compte de l'origine TGA ; `preparer_minicarte.ecrit_tga_palette`
    écrivait du sud au nord (corrélation avec la carte peinte 0,05 contre 0,21 retournée ; chez CA 0,31 contre −0,02).
    Effet : territoires et frontières au dézoom, surbrillance de la minicarte. -> **Règle : les lookups s'écrivent comme
    ceux de CA (ligne 0 = nord, octet 17 = 0x10) ; contrôle par corrélation avec la carte peinte.** Corrigé :
    `preparer_minicarte.py`, fichiers retournés et `vue_de_loin.py --apply` (sauvegarde
    `db-backups\20260925-005632-lookups-avant-retournement`). GUIDE § 15 n° 35 annoté.

254. `[evitable]` (construction et session du rendu, depuis le 23.09.2026 ; trouvé le 25.09 vers 02 h 15) **Nos
    substituts posés à des chemins de CA étaient lus par CA dans toutes les campagnes** : `modeles_wh1.SUBSTITUTS_CA`
    remplissait des fichiers que CA cite sans les livrer (`vegetation/textures/flatnormal.dds`, `test_*`…) ; 283 arbres
    de CA lisaient notre `flatnormal.dds` mod actif, contre la règle « les campagnes coexistent ». -> **Règle : un
    fichier absent de WH3 ne se pose à son chemin que si aucun modèle de CA ne le cite ; sinon, une copie sous un chemin à
    nous.** Code : `fichiers_wh1.SUBSTITUTS_A_NOUS` ; `build_pack.SUBSTITUTS_CA_RETIRES` (15 chemins, non embarqués et
    retirés du pack rouvert) et `garde_substituts_ca()` (refuse le pack tant qu'un de nos modèles cite l'ancien chemin).
    GUIDE § 15 n° 67 annoté.

255. `[evitable]` (session « IA et modding 3D », nuit du 24 au 25.09.2026 ; signalé par elle) **Rechute de l'erreur 129** :
    un script par heredoc, refusé par le garde (`garde_commandes.py`, erreur 212) ; aucun dégât, refait par l'outil
    d'écriture. Le garde fait son travail.

256. `[evitable]` (session « IA et modding 3D », 25.09.2026 ; signalé par elle) **Noms de mécaniques de CA écrits sans
    vérifier le `.loc`** : « Guerre d'errance » et « Vœu de quête » dans les « Comment jouer » d'Albéric et de la Fée, au
    lieu de « Guerre Sainte » et « Serment de la Quête » (textes de CA). -> **Règle : tout nom de mécanique de CA se
    vérifie dans le `.loc` français avant d'écrire** (même famille que les erreurs 139, 191, 207).

257. `[decouverte]` (session du rendu, enquête des arbres jaunes, 25.09.2026 vers 04 h 30) **Le feuillage de WH1 passe
    par le shader hérité `fx_rigidcampaignvegetation`, qui ne lit AUCUNE normale** (désassemblé) : sa couleur vaut texture
    × `g_tint_colours` (teinte choisie par le moteur, par arbre), que le shader de WH1 n'avait pas. D'où l'effet nul du
    correctif flatnormal sur nos 303 maillages de feuillage, et des arbres bretons de WH1 (`brt_trees_diffuse`, 53°,
    saturation 0,59) rendus environ 2,1 fois leur texture, contre 1,1 à 1,35 pour la forêt elfe. Le commentaire de
    `fichiers_wh1.SUBSTITUTS_A_NOUS` qui prêtait à la normale bretonne un meilleur éclairage est RÉFUTÉ. -> **Règle : le
    ton d'un feuillage de WH1 se règle sur sa texture (gain par canal sur les texels opaques), pas par une normale.**
    Correctif proposé (C1a / C1b), à décider avec Charles, après un essai « feuillages gris ».

265. `[découverte]` puis `[évitable]` (construction, 25.09.2026, 02 h 20 - 04 h 45 ; piste mémoire : Charles) **Plantage de
    rendu intermittent `Warhammer3.exe+0x1AC7576` (9.0) = pression mémoire due à `rpfm_server`.** Deux plantages (essai
    Orion à 02 h 20, partie Mousillon de Charles à 04 h 18), même instruction, `rax = 0x20` les deux fois : le code teste un
    pointeur nul en `[r14+0x20]`, y lit 0x20, et `r14` pointe dans des en-têtes du tas. Un bloc déjà libéré est relu
    (restes de chaînes : une montagne de WH1 près de Brionne et ses textures) ; aucun fichier ne manque (tuiles, textures
    et maillages d'eau contrôlés par le rendu). `rpfm_server`, lancé le 24 à 17 h 42, tenait **69,7 Go** après une nuit de
    packs : 111 Go réservés sur 127,7, fichier d'échange agrandi par Windows à 96 Go. Fermé et relancé : 3 essais Duc de
    3 tours sur le même pack passés (04 h 35, 04 h 38, 04 h 41). D'où le faux indice « seulement depuis la chaîne 14 » :
    les plantages suivaient le nombre de packs construits depuis le lancement de `rpfm_server`, pas un changement du
    terrain. -> **Règle : avant un essai en jeu ou un pack, `rpfm_server` sous 8 Go (sinon, le relancer) ; un plantage
    intermittent se lit d'abord à la mémoire de la machine (mémoire réservée, pas seulement la RAM libre).** Code :
    `build_pack.garde_memoire_rpfm()` (refus au-delà de `SEUIL_RPFM_GO` = 8). GUIDE § 15 n° 150.
    **[25.09.2026, 13 h 55 : cause RÉFUTÉE.]** Même plantage chez Charles à 13 h 35 (Duc, écran noir à l'arrivée), PC
    redémarré à 12 h 34, `rpfm_server` éteint, 60 Go de mémoire réservée libre. La fuite de `rpfm_server` est réelle (garde
    gardé) mais n'est pas la cause. Le vidage de 13 h 35 montre l'objet dessiné : `TerrainCustomTile`, modèle
    `rigidmodels/_wh1/campaign/montagnes/cliff_inland_custom_passable/2x2_lt_tr_b_pose40128` (à 04 h 18 aussi une pièce de
    `cliff_inland_custom_passable`) ; `r14` pointe un objet déjà libéré. Seul changement des montagnes à la chaîne 14,
    juste avant le premier plantage : 3 814 objets reposés sur elles (`props_wh1_vers_layers.SOL_VISIBLE_DES_MONTAGNES`,
    `ASSEMBLAGES_HORS_MONTAGNES`, `RUINES_SUR_LEURS_DALLES`), coupés pour la chaîne 16 (accord de Charles). -> **Règle :
    trois essais automatiques réussis ne prouvent pas une correction quand l'essai ne joue pas comme le joueur (intro et
    caméra sautées) ; un plantage intermittent se juge sur des parties jouées comme Charles.**
    [Piste des 3 814 objets reposés remplacée le 04.10.2026 par n° 327 : cause désignée = montagnes et falaises de WH1
    posées au matériau 49 (correctif : matériau 68 ; 0 plantage sur 15 parties). La règle « parties jouées comme
    Charles » reste.]

268. `[découverte]` (construction, 25.09.2026, 17 h 55 ; demande de Charles : le verrou du DLC visible avant la partie)
    **Une zone jouable rattachée à un paquet de DLC est refusée par le jeu, même avec UNE seule ligne** :
    `campaign_map_playable_area_ownership_content_pack_junctions`, 1758400002 → `wh1_wood_elves` (pack de 17 h 54) : le jeu
    se ferme 20 s après le lancement, code 0, sans message (essais Duc et Kemmler, « sortie »), comme le 23.09 avec deux
    lignes (erreur 107). L'hypothèse des deux paquets est donc RÉFUTÉE. Relevé du kit par la session « IA et modding 3D » :
    aucune carte de CA n'est verrouillée par un paquet de DLC (`wh3_base_game` ou `wh3_roc_update` seulement) ; le cadenas
    de CA se fait PAR FACTION (`faction_ownership_content_pack_junctions`). -> **Règle : ne jamais rattacher notre zone
    jouable à un paquet de DLC. Le verrou du DLC de la campagne passe par script : au menu (bouton de lancement grisé,
    `saison_choix_par_defaut.VERROU_MENU`) et en campagne (`saison_verrou_dlc.lua`) ; celui des seigneurs par les
    jonctions de faction de CA.** Code : `build_pack.TABLES_EXCLUES` (table de nouveau exclue). GUIDE § 15 n° 106 annoté.

### Site de l'Atlas (session « Extension », nuit du 25.09.2026, 3 h 45 - 4 h 20 ; concerne le site, pas le mod)

258. `[évitable]` **Dévoilement de la carte lié au défilement, posé sur une visionneuse qui capte la molette** : après
    0,4 s de pause au-dessus de la carte, la molette zoomait la carte au lieu de faire défiler la page ; page bloquée, vélin
    à mi-chemin (« régression », Charles). -> **Règle : un effet lié au défilement au-dessus d'un élément qui capte molette
    ou toucher s'essaie avec des pauses, pointeur dessus ; tant que l'effet n'est pas fini, la page garde le défilement.**

259. `[évitable]` **Règles CSS d'état écrasées par une règle générale plus forte ou placée plus bas** (auréole de l'encre :
    `.devoilement > div` l'emportait sur `.dv-halo` ; aide « ? » de la carte sortie de l'écran au téléphone). -> **Règle :
    une règle d'état a au moins la force de la règle de base et vient après ; l'essai lit le style calculé, pas la source.**

260. `[découverte]` **WebKit (Safari, tout navigateur d'iPhone) : les animations liées au défilement (`view-timeline`) et
    une animation sans fin hors de l'écran font recalculer chaque image, page immobile** (12 images/s au lieu de 57 ;
    `document.getAnimations()` en montre la liste). -> Parade : classe `webkit` posée en tête, glissement des scènes par le
    script (qui ne travaille qu'au défilement), animations sans fin en pause hors de l'écran.

261. `[évitable]` **Lissage réglé par image (facteur fixe à chaque image)** : l'encre traînait selon la fréquence
    d'affichage. -> **Règle : lisser en temps réel, `1 - exp(-dt/τ)`.**

262. `[évitable]` **Attente fixe de 0,7 s dans l'essai de participation** alors que la page, plus longue, met 1,3 s à revenir
    à la carte ; échec pris deux fois pour un aléa. -> **Règle : attendre un état (carte à l'écran), jamais un délai fixe.**

263. `[évitable]` **Traversée au téléphone dessinée sur une émulation Chrome de 844 px de haut** ; un iPhone 13 sous Safari
    n'en donne que 664 (barres) : feuillet coupé. -> **Règle : essayer aux hauteurs réelles de Safari (descripteurs
    d'appareils WebKit de Playwright).**

264. `[découverte]` **Playwright WebKit sans fenêtre sous Windows : une capture d'écran fige le rendu et l'animation tourne
    au ralenti** ; mesures de fluidité non valables. -> **Règle : juger la fluidité iOS sur l'iPhone.**

266. `[découverte]` (session « Extension », vignette du lanceur, 25.09.2026 vers 5 h) **Un filet SVG purement horizontal
    peint avec un dégradé en `objectBoundingBox` ne s'affiche pas** (boîte de hauteur nulle) : le filet d'or sous la
    rubrique manquait depuis la v2. -> **Règle : un filet à dégradé est un rectangle (1,4 px de haut), pas une ligne.**

267. `[évitable]` (sessions « Extension » et construction, 25.09.2026) **Rechutes de l'erreur 212, arrêtées par le crochet
    `garde_commandes.py`, sans conséquence** : « Extension » : deux `python -c` à plusieurs instructions (lecture d'un JSON,
    d'une entrée de `factions_carte.json`) et un `sed` à antislashs (retouche d'un script d'essai `.mjs`) ; construction :
    un `sed` à antislashs (comparaison de journaux de pack), deux `python -c` composés (lecture d'un JSON et d'un bilan).
    Cause commune : l'envie d'aller vite sur une lecture « d'une ligne ». -> **Règle (déjà codée, le crochet fait son
    travail) : tout script, même d'une ligne, passe par un fichier écrit avec l'outil d'écriture ; pour lire un JSON,
    `grep` sur les clés ou un petit script du scratchpad.**

269. `[évitable]` (session « Extension », 25.09.2026, après-midi et soir ; troisième série du même jour que la 267)
    **Nouvelles rechutes de l'erreur 212, arrêtées par le crochet, sans conséquence** : un `python -c` à plusieurs
    instructions ; un heredoc Python vide tapé par réflexe ; trois `sed` à antislashs (deux `sed -i` sur des chaînes
    contenant `\&` ou `\"`, un `grep "a\|b"` dans le même segment qu'un `sed`). -> **Règle : tout remplacement de texte
    passe par l'outil d'édition ou par un script `.py` écrit avec l'outil d'écriture ; `grep` et `sed` jamais dans le
    même segment de commande** (le crochet juge le segment entier). Construction, même soir : un `python -c` composé
    (lecture de `map_spec.json`), refusé ; lu ensuite par un script du scratchpad. Même soir : un `python -c` composé de
    la construction (lecture d'un `bilan.json`, 18 h 15) et un de chacun des agents de revue de stabilité et du pack,
    tous refusés.

270. `[évitable]` (construction, 25.09.2026, 18 h 13 - 18 h 25) **Pilote d'essai : écarter « tous » les tutoriels de CA a
    cassé le jeu au chargement.** Pour que le tour 5 des vampires ne reste plus 6 min bloqué (flèche de la confédération,
    visite des provinces), le pilote ajoutait une précondition fausse à toute intervention de CA dont le nom contient
    `_tour` ou `text_pointer`, prise dans `cm:get_intervention_manager().persistent_intervention_list`. Résultat, deux fois
    de suite (essais 181340 puis 181903, le second avec ce seul changement) : au premier tick, `out()` de CA échoue
    (`lib_campaign_manager.lua:423`, « arithmetic on a string value »), les rappels du premier tick s'arrêtent, le jeu
    plante (vidage). Cause exacte non trouvée. La version précédente (recherche dans `_G`, qui ne trouvait rien) était
    inoffensive et a été remise ; la version fautive est rangée dans
    `05-journal\scripts-backups\saison_essai_auto-fautif-out-casse-20260925-1825.lua`. La règle 239 (un changement par
    essai) a permis de trouver le coupable en deux essais. -> **Règle : le pilote ne modifie jamais en masse les objets
    de CA (interventions, écouteurs) par un motif de nom ; s'il doit passer outre un écran de CA, il le ferme comme un
    joueur (clic sur la croix ou « terminer »), sur des noms de composants relevés dans le journal.**

271. `[évitable]` (audit des cartes de bataille, 25.09.2026, 19 h ; question de Charles : « les batailles tombent-elles
    sur les bons biomes ? ») **Zones de défilé peintes sur des provinces entières.** `captage_campagne.py` (l. 173-178)
    peint les collines de Bretonnie en `wh3_dlc20_macro_brt_hills_chokepoint` et toutes les Montagnes Grises et le Massif
    Orcal en `..._mountains_dwf_chokepoint` (36,7 % de la terre peinte) : toute bataille rangée y devient une bataille de
    passage, sur 2 cartes (découverte : GUIDE § 15 n° 151). Aucune bataille jouée ni aucun siège n'avaient été vus en 9.0
    (une seule bataille chargée, en 8.1, le 24.09 à 03 h 11). -> **Règle : une zone `*_chokepoint` seulement sur les cols ;
    contrôle = part de la terre franchissable en `_chokepoint` (quelques % au plus) ; toute nouvelle carte de captage se
    termine par une bataille rangée ET un siège chargés en jeu.**

272. `[évitable]` (sessions « Extension » et construction, 25.09.2026, 19 h 14 - 19 h 28) **Clés de jeu d'Expanded
    déclarées avant d'avoir appliqué la règle des noms abandonnés.** La table `expanded_declaration.json` affirmait « clés
    stables, jamais dérivées d'un nom » ; or `CLAUDE.md` § 2 (décision de Charles du 25.09) veut que les clés aux noms
    abandonnés soient renommées AVANT toute table. La construction a déclaré les 75 régions à 19 h 14 sans relire cette
    règle : 9 clés fausses (Thurin, Portsall, Saint-Lambert…) ont dû être retirées du kit (`retirer_cles_renommees.py`)
    et redéclarées. -> **Règle : avant toute déclaration de clés dans le kit, relire les décisions de Charles du § 2 ; la
    clé de jeu suit le nom retenu (l'identifiant interne du site peut rester) ; pour retirer des lignes, un outil ciblé,
    jamais `declare_map --undo`, qui retire aussi la carte et la campagne.**
273. `[évitable]` (session « Extension », 25.09.2026, soir ; concerne le site) **Fichiers de carte publiables remis sans
    leurs images** : 4 textures à empreinte citées avaient été remplacées par une construction d'aperçu ; la page
    publiée aurait eu des trous (vu avant la construction). -> **Règle : restaurer aussi les images citées ; contrôle
    `images_citees.py` (dossier de travail de la session).**
274. `[découverte]` (session « Extension », 25.09.2026 ; concerne le site) Les 64 images des récits (`images_recit.mjs`)
    peuvent dépasser 40 min sur une machine chargée : garde portée à 60 min ; ne relancer que les vues manquantes
    (`python images_recit.py "<filtre>"`). Même soir : deux `python -c` composés et un `sed` à antislashs refusés par le
    crochet (rechutes de 212 et 269, sans dégât) ; construction : un `sed` à antislashs refusé (19 h 25).
275. `[évitable]` (construction, 25.09.2026, 20 h 44) **Mémoire de rpfm_server mal lue** : avant le pack final, `tasklist`
    montrait 91 Mo pour rpfm_server (mémoire de TRAVAIL) ; `build_pack.garde_memoire_rpfm` mesure la mémoire PRIVÉE, qui
    était de 9,4 Go, et a refusé le pack (sans dégât : rien n'était écrit). -> **Règle : avant un pack, lire la mémoire
    privée (`Get-Process rpfm_server | PrivateMemorySize64`), ou relancer rpfm_server d'office avant la chaîne finale.**
    Cause trouvée le même soir : chaque script ouvre sa session MCP chez rpfm_server et ne la ferme jamais ; le serveur
    garde chaque session sans délai, avec la base du jeu et les packs OUVERTS (`/sessions`) ; un DELETE MCP est accepté
    mais ne libère rien (`rpfm_mcp.fermer`, essai de 20 h 50). À traiter après la bêta (une seule session partagée, ou
    relance du serveur par la chaîne).
    [Décision de Charles, 04.10.2026 : RPFM 5.1.1 (fuite de mémoire des sessions corrigée) à essayer sur une copie ; le
    pack de la Saison doit en sortir identique avant adoption.]
276. `[découverte]` (session « Extension », 25.09.2026, 21 h 15 ; concerne le Workshop) **Une « mise à jour » depuis le
    lanceur de WH3 remet le titre de la page Workshop au nom du .pack et VIDE sa description** ; la visibilité reste. Le
    lanceur n'offre le bouton d'envoi que pour un pack ACTIVÉ (penser à le désactiver ensuite). -> **Règle : après
    chaque mise à jour par le lanceur, remettre titre et description (textes : scratchpad de la session « Extension »,
    `est\workshop\description_*_en.txt`) ; la vignette d'Expanded vient de
    `05-journal\2026-09-23-extension-carte\vignette-lanceur\vignette_expanded_fr_512.png` (`pack_demo_expanded.py`).**
    [Remplacée le 04.10.2026 par n° 306, 310 et 339 : UNE modification par objet (pack et textes dans le même passage),
    puis attendre la levée ; un envoi par le lanceur à la fois, `launcher.log` relu ; erreur 25 : ne rien renvoyer.]
277. `[évitable]` (construction, 25.09.2026, 21 h 48) **Capture d'écran « témoin » qui ne montre pas le jeu** : pour
    comparer les sols avant et après le catalogue séparé, `ImageGrab` a capturé l'écran au tour 1 ; les deux images
    (`sol_avant.png`, `sol_apres.png`) montrent la fenêtre de Claude, le jeu étant derrière. Le témoin de 21 h 41 a été
    tenu pour bon sans être regardé. -> **Règle : ouvrir toute capture avant de s'en servir comme témoin ; une capture
    de l'écran ne prouve rien si le jeu n'est pas au premier plan, et le mettre devant, c'est piloter l'écran (accord de
    Charles, erreur 108). Sinon, faire juger en jeu par Charles.**
278. `[évitable]` (construction, 25.09.2026, 22 h 30) **Contenu d'un objet Workshop affirmé sans vérification** : j'ai écrit
    à la session « Extension » que la page de la Saison contenait « un seul objet qui contient les deux packs » ; le
    lanceur publie UN pack par objet, et la taille affichée (825,519 Mo = pack de 20 h 47 + miniature, à l'octet)
    prouvait que le pack anglais n'y était pas. Les joueurs non francophones n'avaient donc pas de textes anglais.
    -> **Règle : ce qui est en ligne se vérifie avant de l'écrire (taille affichée comparée aux packs locaux, liste des
    objets) ; un pack = un objet Workshop.** Suite : décision de Charles du 25.09, 23 h : pack principal en anglais,
    traduction française en objet à part (`build_pack.PACK_FR`, `injecter_textes.LANGUE_PRINCIPALE`).
279. `[évitable]` (construction, 25.09.2026, 22 h 47) **Pilotage d'écran accordé pendant un essai en jeu** : j'ai répondu
    « vas-y » à la session « Extension », qui voulait mettre Steam au premier plan, en raisonnant que le pilote clique par
    Lua et non à la souris. L'essai de la Fée a pris 116 erreurs des scripts d'interface de CA (« is not a ui
    component », `UIDestroyed`), puis le jeu s'est fermé ; elle avait passé 10 tours à 0 erreur sur le même pack.
    Probable perte de focus : le jeu en arrière-plan détruit ou recrée son interface. -> **Règle : aucun pilotage
    d'écran, aucune fenêtre mise au premier plan pendant un essai en jeu ; attendre « jeu fermé ».** (Non reproduit :
    essai arrêté sur décision de Charles.)
280. `[découverte]` (session « Extension », 25.09.2026, 01 h 20 à son heure) **Le lanceur ne liste un pack publié que si
    l'on est abonné à son objet** ; sinon il disparaît de « Vos mods ». Mise à jour : s'abonner, bouton dossier ->
    « MISE À JOUR », puis se désabonner (sinon la copie du Workshop double celle de `data\`). Un objet neuf abonne son
    auteur tout seul. Reporté au GUIDE § 15 n° 152.
281. `[évitable]` (essai WH3 MCP, 27.09.2026) **Première commande JSON écrite avec un BOM UTF-8.** Le
    `json.decode` du mod l'a refusée ; la même commande sans BOM a répondu `pong=true`. -> **Règle : écrire
    `wh3_mcp_command.json` en UTF-8 sans BOM et contrôler les premiers octets avant l'envoi ; déplacer le résultat
    précédent avant une nouvelle commande.**
282. `[évitable]` (diagnostic de Gisoreux, 27.09.2026) **Avoir conclu trop vite à l'absence de défaut visible.** Les
    tables et MCP montrent un bâtiment principal dans les trois régions, mais la capture du joueur et l'essai avec
    Mousillon montrent des cases vides dans le panneau. La cause de cet écart reste à établir. -> **Règle : pour un
    défaut d'interface, comparer le panneau et l'état du jeu dans la même partie ; ne pas déduire l'affichage des seules
    tables ou de `slot_list()`.**
    **[Corrigée le 27.09.2026 : l'essai a établi que la découverte et la propriété modifient l'affichage
    des cases, tandis que les trois bâtiments principaux sont présents dans la partie. Le gel reste
    à diagnostiquer avec la sauvegarde et le `script_log` du joueur.]**
283. `[évitable]` (essai WH3 MCP, 27.09.2026) **Avoir passé une durée nulle à
    `cm:scroll_camera_from_current`.** Le `script_log` a signalé deux erreurs, alors que le MCP répondait
    `ok` ; la caméra n'a pas bougé. -> **Règle : utiliser une durée positive et contrôler le `script_log`
    même si `eval` répond `ok`.**
284. `[évitable]` (diagnostic de Gisoreux, 27.09.2026) **Avoir relancé le jeu
    après que Charles a demandé de chercher dans le pack.** L'autorisation
    antérieure d'essayer le jeu ne remplaçait pas cette consigne plus récente.
    Le jeu a été arrêté et `user.script.txt` remis à l'identique. ->
    **Règle : suivre la consigne la plus récente ; pour un diagnostic demandé
    dans le pack, rester en lecture seule et demander un nouvel accord avant
    tout essai en jeu.**

285. `[découverte]` (diagnostic de Gisoreux, 02.10.2026, mod MCP) **Trois faux gels et un vrai piège du mod MCP.**
    (1) `take_screenshot` fige le jeu plus de 3 minutes (« ne répond pas », CPU arrêté) et laisse un TGA tronqué, noir :
    ne jamais l'envoyer ; arrêt forcé du jeu nécessaire. (2) Un `params` vide `{}` est lu comme un nombre par le mod
    (`attempt to index local 'params'`) : toujours passer au moins une clé. (3) `soak_turns` bloque au tour 5 : le tutoriel
    vampire de CA (`in_vmp_confederation_text_pointer`, puis `in_vmp_bloodlines_text_pointer`) verrouille l'interface
    (`ui_locked=true`) et seul son bouton `text_pointer_tp_vmp_confederation > button_parent > button_close` la libère
    (`SimulateLClick`) ; au tour 15, le pilote laisse le panneau `diplomacy_dropdown` ouvert pour le dilemme CA
    `wh_main_all_foolish_vainglory` : la fin de tour ne part pas tant qu'on ne l'a pas fermé (`close_panel
    {"panel":"diplomacy"}`). Ces blocages ne viennent pas de notre pack. -> **Règle : avant de conclure à un gel du jeu,
    lire `ui_locked`, les panneaux ouverts (`get_situation`) et le `script_log` ; piles de tous les fils par `cdb -pv`
    (fil principal en `PeekMessage` = le jeu tourne). Reporté au GUIDE § 15 n° 154.**
286. `[évitable]` (diagnostic de Gisoreux, 02.10.2026) **Capture du bureau par `ImageGrab` pour voir le jeu** : elle a montré
    la fenêtre de Claude et la barre latérale de Charles, pas le jeu (rechute de 277). -> **Règle : pas de capture du
    bureau ; pour voir un panneau, demander une capture à Charles ou lire l'état par script (`eval`, `list_ui`).**

287. `[découverte]` (passe de test des dix seigneurs, 03.10.2026) **`string.find(s, motif, 1, true)` (drapeau « texte brut »)
    rend nil à tort puis corrompt la bibliothèque de chaînes de TOUT le processus** sur le jeu 9.0.2 : ensuite
    `string.len('<706.8s>')` rend la chaîne elle-même et chaque `out()` de CA échoue (`lib_campaign_manager.lua:423 :
    attempt to perform arithmetic on a string value`), puis le moteur plante (déréférencement nul dans le Lua natif,
    `Warhammer3+0x244cfdf`, déterministe). Notre `saison_chroniques.lua:904` (`retirer_armee`, fin de chaque étape de
    chronique et des Échos) l'appelait : Albéric plante au tour 27, quand l'étape 1 expire. Preuve par expérience contrôlée
    sur un jeu neuf. Le manuel du mod MCP de WH3 le dit (§ 9). Même appel dans le script du pilote d'essai
    (`saison_essai_auto.lua:71`). -> **Règle : jamais `find`/`match` avec le 4e argument `true` dans un script du jeu ni
    dans un script d'essai ; comparer des éléments par `string.gmatch` ou `string.sub`. À coder : verifier_lua.py doit
    refuser ce motif (non fait au 03.10).** Corrections non appliquées (domaine de la session « IA et modding 3D »).
    [Codée : n° 292 (`verifier_lua.INTERDITS`). Annoté le 04.10.2026.]
288. `[découverte]` (passe de test, 03.10.2026) **Le pack d'essai prioritaire (`!!saison_essai_auto.pack`, `--prioritaire`) n'a
    pas remplacé `saison_chroniques.lua`** : la pile de l'erreur citait les mêmes lignes qu'avec la version d'origine.
    -> **Règle : pour tester un correctif de script, vérifier d'abord par une ligne `out(...)` posée dans le correctif
    qu'il est bien chargé ; sinon reconstruire le pack.**
289. `[évitable]` (passe de test, 03.10.2026) **Une commande lancée dans le même appel qu'un démarrage de jeu a bloqué
    l'outil 10 minutes** (le processus du pilote hérite de la sortie redirigée par `| Out-String`). -> **Règle : lancer
    le démarrage par `Start-Process` avec fichiers de sortie, puis relire le fichier.**
290. `[découverte]` (construction, 03.10.2026, constat de la session « Expanded map avec vaults ») **Le kit réécrit par
    une mise à jour le 27.09.2026 à 16 h 48** : `raw_data\db` ne contient plus aucune ligne de la Saison ni d'Expanded
    (0 ligne `wh_dlc05_` ou `saison_` dans `campaign_map_regions`, `regions`, `campaigns`), comme à la 9.0 (erreur 206,
    GUIDE § 15 n° 142). Le pack en ligne et ses copies (`05-journal\pack-backups\*maj1-20260925-2355*`) sont intacts.
    Restauration lancée le 03.10 à 01 h 36 par la session « Lakemen » (`restaurer_lignes_kit.py --apply`, 3 370 lignes,
    57 tables). -> **Règle (celle de l'erreur 206) : après toute mise à jour du jeu ou du kit, compter nos lignes dans
    `raw_data\db` AVANT toute construction ; restaurer par les lots idempotents et les sauvegardes de
    `05-journal\db-backups\`.**
291. `[évitable]` (construction, 25.09.2026, 23 h 45 ; trouvé le 03.10, voir n° 287) **Erreur du jeu attribuée au pilote
    d'essai sans preuve** : l'erreur `lib_campaign_manager.lua:423` des essais du Duc et de la Fée a été classée « pilote
    seulement, sans effet pour les joueurs », parce que seul le pilote avait des minuteurs en temps réel en campagne. La
    cause était notre `saison_chroniques.lua:904` (n° 287), qui plante la partie d'Albéric au tour 27. -> **Règle : une
    erreur de script de CA vue en essai est imputée au mod tant qu'on n'a pas trouvé l'appel fautif dans NOS scripts
    (pile, recherche du motif) ; on cherche avant de conclure.** (Mes n° 281 et 282 du 03.10 réutilisaient des numéros
    pris : renumérotés 290 et 291, règle « prochain numéro = le plus grand + 1, vérifié ».)
292. `[évitable]` (session « IA et modding 3D », 23.09.2026 ; trouvé le 03.10, voir n° 287) **Recherche « texte brut »
    (`find` avec 4e argument vrai) écrite dans `saison_chroniques.lua` (`retirer_armee`)** sans connaître son défaut en
    9.0.2 ; elle a fait planter Albéric au tour 27. Corrigée par une boucle `string.gmatch` (IA, 03.10) ; le marqueur de
    la rencontre « Nains » de `saison_foret.lua` passe en (272, 210), le point (272, 209) étant invalide pour le moteur.
    Le pilote d'essai (`saison_essai_auto.lua:71`) avait le même motif : remplacé par `string.sub(id, 1, 12)`
    (construction, 03.10 ; à valider par 2 tours sur un pack éprouvé, erreur 239). -> **Règle CODÉE :
    `verifier_lua.INTERDITS` refuse ce motif dans tout script du jeu et d'essai** (n° 287 : « à coder » fait).

Session « Expanded map avec vaults » (03.10.2026, passage de la grille d'Expanded à 560 × 905 pour les Voûtes ; détail :
`05-journal\2026-09-23-extension-carte\voutes-2026-10-03\pour-la-construction.md` § 5) :
293. `[évitable]` **Bruits qui dépendent de la forme de la grille** : 80 rangées ajoutées au sud ont changé tous les champs
    de bruit de la chaîne de l'Atlas, donc des bois, une île et un relief déjà validés. -> **Règle codée :
    `geo_extension.stable_au_sud` ; après tout changement de cadre, comparer les grilles à la sauvegarde.**
294. `[découverte]` **Une table du kit vidée ne lève aucune erreur** : `factions_carte.py` rendait « 0 région tenue »
    (kit réécrit, n° 290). -> **Règle codée : repli sur un instantané daté, avec un message ; lire le bilan chiffré de
    chaque étape.**
295. `[évitable]` **Le lissage des contours coupait les coins du cadre d'une corde** (côte en diagonale à travers le
    massif). -> **Règle codée : `carte_papier_v2.bords_denses`.**
296. `[évitable]` **Douze outils d'Expanded portaient le cadre en dur** (825, 250, 507, 1142, 575…), dont les miens
    (`projet_expanded`, `rivieres_atlas`, `retouches_expanded`). -> **Règle codée : `cadre_expanded.py`, seule source,
    contrôlée contre `carte_config`.**
297. `[évitable]` **`villes_expanded` ouvrait toute la terre d'une région neuve** : dans un massif, un passage partout.
    -> **Règle codée : la haute montagne des Voûtes reste fermée (même seuil que la carte de l'Atlas).**
298. `[évitable]` **Un fil de connexité tracé tout droit traverse tout ce qui est sur sa colonne** : avec les Voûtes, il
    perçait le massif. -> **Règle codée : le fil ne traverse que le voile, depuis une case déjà franchissable.**
299. `[évitable]` (concerne le site) **`images_recit.mjs` rendait toujours `travail\site\`**, même quand la carte d'essai
    était ailleurs : il aurait refait les images du récit sur l'ancienne carte. -> **Règle codée : il suit `ATLAS_SITE`,
    comme `page_v2.py`.**
300. `[évitable]` (même session, § 6 n° 8) **`spec_expanded.py` lancé sans `--lot2`** : `map_spec_expanded.json` est
    ressortie avec les seules régions de WH1 et a remplacé la bonne en silence ; rattrapé et contrôlé contre la copie du
    dépôt public. -> **Règle codée : l'Atlas est pris par défaut (`--sans-atlas` pour l'ancien comportement).**
301. `[évitable]` (même session, § 6 n° 9) **Minicarte d'Expanded : `cv2.remap` avec le bord constant par défaut**
    dessinait une frange d'encre au bord nord. -> **Règle codée : `BORDER_REPLICATE`.**
302. `[découverte]` (même session, § 6 n° 10) **La restauration du kit (n° 290) a ramené les onze mers `saison_sea_*` en
    noir** (0, 0, 0) : la recoloration du 25.09 à 20 h 10 (`maj_couleurs_mers.py`) n'est pas dans la copie restaurée. Sans
    effet sur la Saison. -> **Règle : après une restauration du kit, repasser aussi les retouches faites hors des lots
    (`maj_couleurs_mers.py --apply`, sous préavis) et compter ce qu'elles écrivent.** [Réglé le 03.10 à 03 h 19 : 11 mers
    recolorées avec la déclaration d'Expanded, sauvegarde `db-backups\20261003-031951`.]

Session « Lakemen » (passe de test et restauration du kit, 03.10.2026 ; `05-journal\2026-10-03-passe-test-dix-seigneurs\REPRISE.md`) :
303. `[évitable]` **Un tube `| Select-Object -First 1` a coupé un script en cours d'écriture** : PowerShell arrête la
    commande dès la première ligne reçue ; `restaurer_tables_photo.py` s'est interrompu après 10 tables sur 21. -> **Règle :
    jamais de tube qui tronque la sortie d'un script qui écrit ; sortie dans un fichier, puis lecture du fichier.**
304. `[évitable]` (construction, 25.09.2026) **`build_pack` écrivait toujours le pack français en place** (`PACK_FR` en
    dur), même pour un pack candidat construit sous un autre nom ; `injecter_textes` faisait de même par défaut. ->
    **Règle codée (03.10) : `build_pack.pack_traduction(pack)` et `injecter_textes` (sans `--pack-traduction`) prennent
    `!<nom>_fr.pack` à côté du pack construit ; seul le pack normal garde `!saison_des_revelations_fr.pack`.**
305. `[découverte]` **`restaurer_lignes_kit.py` ne prend que la copie la plus récente de chaque table** : les lignes du lot
    1 (21 tables) n'existaient que dans la photo 8.1 (`03-references\instantane-wh3-8.1\`), et non dans les sauvegardes
    récentes. -> **Règle : après une restauration, compter les lignes de chaque lot contre sa source ; outil
    `05-journal\2026-10-03-passe-test-dix-seigneurs\outils-passe\restaurer_tables_photo.py` pour les tables de la photo.**
    RPFM en 9.0.2 : `update_schemas` et `generate_dependencies_cache` avant tout pack (GUIDE § 15, déjà noté à la 9.0).

Session « Extension » (Workshop et site, 02.10.2026) :
306. `[découverte]` **Toute modification d'un objet Workshop le soumet à une « vérification automatique de contenus »**
    qui le masque (page illisible hors compte de l'auteur, liens externes remplacés par « {LIEN SUPPRIMÉ} ») et le
    VERROUILLE : « MISE À JOUR » du lanceur refusée (`launcher.log` : « error code #15 », le pack monte pourtant à
    100 %), seconde description refusée (« L'accès a été refusé »). Levée constatée après 1 h 40 (traduction), plus pour
    la Saison. -> **Règle : une seule modification par objet, puis attendre la levée ; pack et textes dans le même
    passage ; prévenir que le lien est indisponible pendant ce temps.** Rappel : la mise à jour 1 est en ligne depuis le
    26.09 (Saison 816,252 Mo = pack de 23 h 55 + vignette ; traduction 37,263 Mo) ; titres anglais remis le 02.10
    (rechute de l'erreur 276).
307. `[évitable]` **Edge sans fenêtre laissé en mémoire à chaque capture** : Edge se relance lui-même, `edge.kill()` ne
    tue que le lanceur ; 82 navigateurs, 1 100 processus, 23 Go, 239 profils temporaires (53 Go) ; Charles a vu son
    PC ramer. -> **Règle codée : `cdp_outils.mjs` ferme par `Browser.close` puis tue tout msedge de son profil
    (`travail\fermer_edge.mjs`) ; zéro msedge `--headless` avant de rendre la main ; filet
    `travail\nettoyer_navigateurs.ps1`. À vérifier : `rendre_png_v2.py` / `v3` (icônes de monuments, `--headless`).**

Session « Expanded map avec vaults » (03.10.2026, suite ; `voutes-2026-10-03\pour-la-construction.md` § 6) :
308. `[évitable]` (§ 6 n° 11) **Rivières de l'Atlas trouées** : `geo_extension.tracer` coupait le squelette à chaque nœud
    et écartait les morceaux de moins de 3 points ; au nord de la Bretonnie et au Reikland, rivières en pointillés et sans
    source. -> **Règle codée : `travail\rivieres_chainees.py` (appelé par `carte_papier_v2.py` : raccords, sources dans
    la montagne, anneaux et ramilles ôtés) ; 508 bouts deviennent 103 tronçons continus.** (Les lits creusés par
    `rivieres_atlas.py` dans le relief d'Expanded suivaient ces morceaux : à relancer sur les tronçons chaînés.)
309. `[évitable]` (§ 6 n° 12) **Bande de mer tirée à la règle au sud-ouest des grilles de l'Atlas** : la marge du bas du
    relevé est restée en mer quand la Tilée a été ajoutée dessous. -> **Règle codée : `geo_extension` la remet en terre ;
    contrôle : 479 cases changées, toutes dans la bande ; sauvegarde `travail\sauvegardes\20261003-avant-bande-mer-so\`.**
310. `[évitable]` (session « Lakemen », 03.10.2026, 15 h 01 ; rechute du n° 306) **Description anglaise de la page de la
    Saison modifiée sans relire le n° 306**, puis six essais de sauvegarde : page illisible hors compte de l'auteur, liens
    remplacés par « {LIEN SUPPRIMÉ} », toute nouvelle sauvegarde refusée (« L'accès a été refusé »), lanceur refusé aussi
    (« error #15 ») jusqu'à la levée (1 h 40 au moins). -> **Règle : relire le n° 306 avant toute modification d'un objet
    Workshop ; UNE modification par objet (pack et textes dans le même passage) ; jamais d'essais répétés ; pas d'envoi de
    pack prévu pendant la vérification de Steam.**
311. `[découverte]` (construction, 03.10.2026) **La 9.0.2 a changé l'empreinte de `bob_terrain.modder.x64.dll`** :
    `compiler_terrain_bob.py` refusait de tourner (« décalages à relever de nouveau »), bloquant toute compilation de
    terrain (Saison et Expanded). Relevé en lecture seule (`decalages_bob.py` du scratchpad : import de l'IAT, seul appel
    indirect, octets attendus) : décalages IDENTIQUES à la 9.0 (0x34099, 0x3409F, 0x341F4). -> **Règle : après toute mise à
    jour du kit, lancer `compiler_terrain_bob.py --carte <carte>` à blanc ; nouvelle empreinte ajoutée à `VERSIONS_DLL`
    seulement après relevé des octets.**
    [Décision de Charles, 04.10.2026 : BOB sous `cdb` (`compiler_terrain_bob.py`, `VERSIONS_DLL`) est gardé et assumé
    comme méthode de l'atelier, malgré les guides de l'Atlas ; voir la découverte du 21.09 (BOB et SA base).]
312. `[évitable]` (construction, 25.09.2026 ; trouvé le 03.10) **`textures_sol_wh1.SORTIE` et `SORTIE_BASE` écrits en dur
    vers le dossier de la Saison** : lancé pour Expanded (`SAISON_CARTE=expanded`), il aurait réécrit les textures de sol
    et la base de sols qu'embarque le pack de la bêta. -> **Règle codée : sorties par `carte_config.dans_projet(...)` ;
    contrôle : même chemin qu'avant pour la Saison, dossier d'Expanded pour Expanded. Tout module de la chaîne écrit
    dans le dossier de SA carte.** (`EMPRISE_MONTAGNES` reste une ENTRÉE de la Saison.)

Session « Expanded map integration et polish » (03.10.2026, 13 h - 16 h ; détail `04-projets\saison-expanded\JOURNAL.md`) :
313. `[évitable]` **Cases de port d'une ville neuve rattachées à la région de la ville « comme dans WH1 »** : faux, les 9
    cases de port de la Saison gardent leur région de MER (25 avertissements CAIME). -> **Règle codée : rattachées le
    temps de `grow_town_slots`, puis rendues à leur mer. Un « comme dans X » se vérifie sur le disque de X.**
314. `[évitable]` **Rivières du Bois Rêveur reflétées APRÈS la croissance des villes** : étalement en erreur. -> **Règle
    codée : rivières et côtes se posent avant les villes.**
315. `[évitable]` **Ouverture d'« infranchissables isolés » sans région** : 2 cases de terre sauvage franchissables. ->
    **Règle codée : une case ouverte prend la région voisine, sinon reste fermée.**
316. `[évitable]` **Règle des enclaves qui a ouvert le massif intérieur des Grises de l'est** (+4 800 cases franchissables,
    vues au compte de connexité 210 440 -> 215 272). -> **Règle codée : une réaffectation de région ne change jamais le
    passage ; la haute montagne reste fermée ; comparer le nombre de cases franchissables avant et après toute retouche.**
317. `[évitable]` **Montagnes faites au bruit seul** (« marbre fondu », trois essais avant l'érosion). -> **Règle codée :
    `relief_alpin` (érosion fluviale avec soulèvement, vallées de jeu en exutoires) ; mesurer un profil chiffré avant de
    juger à l'œil.**
318. `[évitable]` **Mers de l'extension sans plans d'eau** (le projet du 25.09 ne recopiait que ceux de WH1 ; le guide
    Terry : « sans eux, pas d'eau sur la mer »). -> **Règle codée : `eau_expanded` (toutes les mers depuis la grille).**
319. `[évitable]` **Éther à l'inverse de la convention** (fond +0,02, surface −1,2) : aurait masqué l'eau. Corrigé.
320. `[évitable]` **Polygones d'eau découpés en pavés tracés séparément** : fente sans eau d'un quart d'hex aux coupures.
    -> **Règle codée : tracé entier, puis intersection exacte (shapely).**
321. `[évitable]` **Identifiant de projet Terry recopié de la Saison** (deux projets du kit au même id). Corrigé.
322. `[évitable]` **Zone jouable d'Expanded restée celle de la Saison décalée** (caméra bornée au cadre de WH1). Corrigée
    sous préavis (`kit_expanded.py`) : x 0-373,14, z 0-697,06.
323. `[évitable]` **Rechutes du n° 212** : trois `python -c` composés ou heredocs arrêtés par le garde, un mauvais nom de
    couche (`layer_ground_types` / `groundtypes`). Le garde a fait son travail.
324. `[découverte]` **Notre CAIME (fork) exporte Borders en ligne de commande** (`process --borders`, code 0, `borders.pbd`
    écrit, carte de 560 × 905), alors que la v1.0.1 officielle exige la fenêtre. Reporté au GUIDE § 15 n° 156.
(N° 11 de la même liste, bande de mer du sud-ouest : voir n° 309 ; règle ajoutée : après un changement de cadre, relire
la rangée de l'ancien bord.)
325. `[découverte]` (session « Expanded map integration et polish », 03.10.2026, 16 h 50) **L'action « Campaign Trees »
    de BOB écrête la coordonnée z des arbres à `world_width` × 2/√3** : elle suppose une carte plus large que haute.
    Expanded (portrait, 373 × 698 u) : z max 431,45, 54 027 arbres empilés sur les rangées 550-574, aucun au nord ; la
    Saison aussi est écrêtée (z max 308,35 pour une profondeur de 338,9), sans effet car elle prend la liste de WH1
    (`liste_wh1`). Rasters et objets de `global_props.bin` sont à leur place. Preuve :
    `05-journal\2026-09-21-phase-3-terrain\compilations\saison_expanded_map-20261003-163550\`. -> **Règle : ne jamais
    prendre la liste d'arbres de BOB telle quelle sur une carte plus haute que large ; parade codée pour Expanded,
    `04-projets\saison-expanded\outils\arbres_expanded.py` (arbres du nord tirés du raster d'arbres, densité et mélange
    mesurés au sud).** Reporté au GUIDE § 15 n° 158.
326. `[évitable]` (restauration du kit du 03.10 ; trouvé par la construction à 18 h 45) **La restauration n'a ramené que les
    lots numérotés et les dernières copies des tables** : 19 lignes de départ de la Saison, écrites par des outils à part
    (`ajouter_seigneurs_jouables.py`, `seigneur_soeurs.py`, `seigneurs_drycha_kemmler_grom.py`, `declare_campaign.py`),
    manquaient au kit (7 relations diplomatiques, 10 options de départ des seigneurs, 1 trait, 1 calendrier) ; seul
    `zz_startpos_db.pack` les portait. Un `synchroniser_pack_startpos.py --supprimer` les aurait EFFACÉES du pack. Vu en
    préparant la recopie du départ d'Expanded. -> **Règle codée : après une restauration du kit, comparer CHAQUE table
    start_pos au pack des tables de départ (`synchroniser_pack_startpos.py --table <t>` à blanc : « lignes du pack absentes du
    kit » doit valoir 0) ; `restaurer_depuis_zz.py` remet les lignes manquantes du pack vers le kit (fait le 03.10, 19 lignes,
    sauvegarde `db-backups\20261003-185346-restaurer-depuis-zz`).**
327. `[découverte]` (construction, 03.10.2026) **Nos montagnes et falaises de WH1 posées en objets au matériau 49 des tuiles
    de terrain** sont la cause désignée du plantage de rendu `+0x1AC3FF2` (GUIDE § 15 n° 150, deux vidages complets).
    Corrigé : `montagnes_wh1.vers_materiau_68` (format relevé sur `lzd_mountain_03` de CA : en-tête de 2 248 octets, sommets
    de 32 octets, triangles retournés, masque à nous), `montagnes_materiau_68.py` pour les 2 531 modèles en place ; BOB des
    seuls `global_props` ; pack d'essai `saison_des_revelations_essai68.pack`, tables identiques au candidat. Série de
    20 lancements (session « Lakemen », 18 h 39 - 21 h 48) : 15 parties valides (≈ 177 min, 5 à 61 tours), **0 plantage
    de rendu**, 0 erreur de script, 0 vidage (sans correctif : 1 sur 11 le soir, 4 sur 8 le matin) ; 5 démarrages avortés
    = course du pilote (jeu relancé avant la fin du précédent ; filet ajouté à `serie.ps1`). Encourageant, pas une preuve
    (≈ 24 % de chances d'un zéro sur 15 au taux du soir) : ~30 parties pour trancher.
    [Décision de Charles, 04.10.2026 : les montagnes au matériau 68 sont déjà converties dans le KIT commun ; aucun pack
    de la Saison n'est reconstruit avant sa décision sur elles (après les avoir vues en jeu).]
328. `[découverte]` (Expanded, 03.10.2026 ; trouvé par la session « Recherche or et rivières navigables », consigné par la
    construction) **En agrandissant la carte, la lisière non jouable des mers de WH1 est restée infranchissable** : dans la
    Saison, l'ancien bord de carte est `Impassable = 0` ; dans Expanded, 434 cases (colonnes 123 à 127, rangées 503 à 645)
    fermaient le Golfe du Bidouze aux mers de l'Atlas : les ports de Bordeleaux, Brionne et Mousillon donnaient sur une mer
    close. CAIME n'a aucun contrôle de connexité de la mer, et notre contrôle mêlait terre et mer : rien ne l'a signalé.
    **Règle : en agrandissant une carte, ouvrir la lisière de mer de l'ancienne et contrôler la MER SEULE, port par port.**
    Codé : `villes_expanded` (étape 2) et `connexite_expanded` (« mer franchissable : … ports hors de la principale »).
    GUIDE § 15 n° 159.
329. `[découverte]` (construction, 04.10.2026, génération du startpos d'Expanded) **Une jonction de propriété de DLC
    recopiée d'une faction modèle de CA (`faction_ownership_content_pack_junctions`, 16 factions de l'Atlas) fait fermer le
    jeu sans rien dire en 9 à 13 s** : ni rapport, ni `mp_log`, ni startpos ; même famille que l'erreur 107 (jonction de
    propriété de la zone jouable). Trouvé par dichotomie sur une copie du pack (`essai_exp.pack`, une table retirée à la
    fois). **Règle : une table `*_ownership_content_pack_junctions` n'entre jamais dans un pack pour une clé à nous** ; codé :
    `build_pack.EXCLUES_EXPANDED`, et `factions_atlas.TABLES` ne la recopie plus. GUIDE § 15 n° 160.
330. `[évitable]` (construction, 04.10.2026) **Le pack d'Expanded embarquait des lignes de gameplay de la Saison qui citent
    une région absente d'Expanded** (Fort Solstice, repris sous `saison_glanborielle_fort_solstice` : 4 lignes dans
    `campaign_group_member_criteria_regions` et `regions_to_region_groups_junctions`) : `bad_mods_report.txt` à la
    génération. **Règle : un pack d'une autre carte ne garde que les lignes dont toutes les régions citées sont sur sa carte** ;
    codé : `build_pack.regions_absentes()` (lignes écartées et comptées au journal du pack). Et toujours un contrôle de
    démarrage avant de dire un pack « construit ».
331. `[découverte]` (construction, 04.10.2026) **`campaigns.mask = 32` sur la campagne d'Expanded fait planter la génération
    du startpos** (`Warhammer3.exe+0x2A588B2`, lecture de 0x14, 9.0.2) ; toutes les campagnes du kit, dont la Saison, ont un
    masque vide. Masque vidé dans le pack : startpos et données de l'IA écrits (22 s). Trouvé après avoir écarté par
    essais les lignes de départ de l'Atlas, les emplacements, les hordes et les personnages (le plantage changeait de place
    sans disparaître : signe que la cause était ailleurs). **Règle : une ligne `campaigns` neuve se fait sur le gabarit de
    celle de la Saison, champ par champ ; tout écart se justifie.** Aussi : la génération n'écrit les données de l'IA
    (`hlp_data.esf`, `spd_data.esf`) que si `data\campaign_maps\<carte>\` existe. GUIDE § 15 n° 161.
332. `[évitable]` (construction, 04.10.2026 ; vu par Charles en jeu) **Carte de l'écran de sélection d'Expanded déformée** :
    `campaign_map_playable_areas.preview_width / preview_height` à 256 × 256, valeur écrite EN DUR par `declare_map.py`,
    alors que le jeu affiche la carte dans ce format (CA : 750 × 600 au rapport de ses mondes ; Saison : 472 × 600 =
    266,5 / 338,9). **Règle : l'aperçu a le rapport du monde (hauteur 600).** Codé : `declare_map.py` le calcule (ou prend
    `preview_width` / `preview_height` de la fiche) ; Expanded : 321 × 600 (session Expanded, kit et fiche).
333. `[découverte]` (construction, 04.10.2026, chargement d'Expanded, 9.0.2) **Un modèle d'emplacement que CA n'emploie
    jamais pour la culture du maître fait planter le chargement de la partie** (`+0x2602213`, lecture de 0x30, « port,
    primary » dans la pile) : 18 régions du Bois Rêveur tenues par Slaanesh avec les primaires spéciaux des elfes sylvains
    (`wh_main_special_waterfall_palace_primary`…), plus des nains et Aislinn sur des modèles humains (49 emplacements).
    La génération du startpos, elle, passe. **Règle : un modèle d'emplacement se prend parmi ceux que CA emploie pour la
    sous-culture du maître ; jamais un `*_port` sur une région sans port.** Contrôle : `modeles_par_culture.py` (bloc-notes
    de la construction, à coder dans le kit d'Expanded). GUIDE § 15 n° 162.
334. `[découverte]` (construction et session Expanded, 04.10.2026) **Une colonie portuaire de WH1 grossie à 19 cases
    principales + 3 de port (au lieu de 16 + 3) fait planter le chargement** (`+0x2613117`, lecture de 0 : la fonction prend
    le premier élément d'une liste vide de la colonie). Bordeleaux, Brionne et Mousillon, grossies par `grow_town_slots`
    dans la grille d'Expanded ; trouvé par le pilote sous débogueur (point d'arrêt journalisant sur la fonction, il a
    nommé `wh_dlc05_bordeleaux_bordeleaux`) ; retirer le port du startpos ne suffit pas, la cause est dans la carte.
    **Règle : les colonies portuaires gardent 16 + 3 ; le grossissement des emplacements ne touche pas une colonie
    portuaire ; après toute croissance, les colonies de WH1 reviennent à l'identique de la Saison** (codé par la session
    Expanded : `villes_expanded.villes_wh1_a_l_identique`, appelée après `grow_town_slots`). Suite (même essai, même
    méthode) : `+0x2602213` nommé sur le Poste de la Pierre Noire, région de WH1 rendue à Karak Ziflin (nains) dont seul
    le bâtiment principal avait suivi (modèles et bâtiments de Drachenfels restés). **Règle : une région de WH1 qui change
    de maître prend modèles ET bâtiments dans la culture du nouveau maître** (codé : `depart_atlas.py` § 4, audit de toutes
    les colonies par la session Expanded). Encore ensuite : Tor Soleil (port neuf de l'Atlas, ports neufs en 16 + 1 /
    16 + 2). Méthode codée :
    `essai_tours_auto.py --cdb-avant <fichier>` (points d'arrêt à soi) et le profil
    `SAISON_CARTE=expanded` du pilote. GUIDE § 15 n° 163.
335. `[évitable]` (toutes sessions, 04.10.2026 ; relevé par Charles : « la plupart des erreurs qu'on fait, c'est par
    négligence, parce qu'on ne suit pas les guides ») **Les erreurs 333 et 334 étaient écrites dans notre propre guide
    CAIME** (`atelier\caime\index.md`, § Les villes : « port : 16 hex de terre + 3 hex consécutifs du bord, dont 1 en mer » ;
    le validateur avertit « emplacement principal ≠ 19 ou 16 ; port sans mer »). Des heures de débogueur pour retrouver
    une règle publiée. **Règle : avant chaque étape, relire la section du guide de l'Atlas et la doc officielle de l'outil,
    la suivre à la lettre ; `validate --all` de CAIME avant tout export, Warning des villes compris.** Inscrite dans
    `CLAUDE.md` § 6 et transmise à toutes les sessions. Suite (session Expanded) : `recentrer_emplacements` tolérait 2 ou 3
    hex de port en mer et ignorait le terrain à risque ; les 11 ports de l'Atlas refaits selon le guide (disque de 19,
    16 + 3 consécutifs, un seul en mer au milieu, en région de mer ; `outils\ports_expanded.py`) ; `validate --all` :
    3 Error d'étendue de villes de col (dont 2 identiques à la Saison, l'exception du guide) et 1 Warning (terre sauvage).
    Ports refaits : la liste vide disparaît ; plantage suivant `+0x2602213` sur `saison_tor_soleil:0` : modèle
    `wh3_dlc27_human_major_primary_port` pour un port haut-elfe, que CA n'emploie jamais (ports hef de CA : primaire
    mineur portuaire + `wh2_main_hef_settlement_minor_2`, ou modèles spéciaux de colonie). **Règle : le trio (modèle
    primary, primary_building, port_building) d'une colonie existe tel quel chez CA pour la même sous-culture.** Après
    correction (colonie elfe majeure de CA), même plantage sur Tor Soleil : sa maîtresse, Aislinn, est chez CA une HORDE
    sans aucune région (combi) ; Expanded lui en donnait trois. **Règle : une faction que CA fait partir en horde ne reçoit
    pas de colonie au départ.** Vérifié le 04.10 à 20 h 36 : les trois Tor données à une faction haut-elfe mineure à nous
    (`saison_hef_tor_soleil`, Aislinn horde sans région comme chez CA), la campagne d'Expanded CHARGE (premier tick,
    tour 1 d'Orion, aucun plantage) : démarrage de référence sans fleuves atteint. GUIDE § 15 n° 164.
    [Ports « un seul en mer au milieu » remplacés le 04.10.2026 par n° 337 (chez CA : deux hex de port en mer, un sur la
    plage), règle pour Expanded et toute carte neuve ; la Saison garde ses ports [mer, mer, mer], validés en jeu
    (décision de Charles, 04.10). Le reste de la règle (guide relu, `validate --all`) tient.]
336. `[découverte]` (session Expanded, consigné par la construction, 04.10.2026) **Notre guide CAIME se trompe sur la
    couche Region Borders** : il dit (§ Produire les couches par script) qu'elle se recalcule depuis Regions à
    l'enregistrement ; le code (`CalculateRegionEdgeMasks`) ne recalcule que parmi les hex déjà marqués `IsBorder`. La
    grille d'Expanded, régions importées par script, avait 0 hex de frontière (Saison : 12 301) ; validate : 129 Info
    « 0 passable region edge hexes ». **Règle : toute carte dont les régions sont posées par script passe
    `generate-region-borders` (verbe de notre fork, code « Auto-generate » de CAIME) avant validate et process.** À
    corriger dans le guide (session Extension, liste du grand nettoyage). Aussi : les 3 « Failed to find tile » du terrain
    de bataille d'Expanded sont les rangées hors de la grille des tuiles, comme la dernière rangée de la Saison.
    GUIDE § 15 n° 165.
337. `[découverte]` (session « Recherche or et rivières », consigné par la construction, 04.10.2026) **Notre guide CAIME
    décrit mal les ports de CA** (« 3 hex de Port, dont un en mer » ; « chez CA : deux sur la terre, un sur la mer »).
    Mesure sur les cartes de CA (Empires `_map_1` : 130 ports, `_map_7` : 134, `chaos_map_4` : 26) : motif [bout, milieu,
    bout] = [mer, mer, terre] pour 127 sur 130 et 131 sur 134, le hex de terre sur la plage (126 sur 127) ; [mer, mer, mer]
    pour 3 ; un seul port sur 290 n'a qu'un hex en mer. « Un en mer » n'est que le MINIMUM du validateur. **Règle : port =
    16 hex principaux de terre + 3 hex de Port consécutifs de l'anneau 2, deux en mer et un sur la plage.** À corriger
    dans le guide (session Extension). Leçon de méthode : un guide qui décrit « ce que fait CA » se vérifie par une mesure
    sur les fichiers de CA, pas seulement sur le code de l'outil. GUIDE § 15 n° 166.
    [Décision de Charles, 04.10.2026 : cette règle est LA règle des ports (Expanded et toute carte neuve) ; n° 45, 174
    et 335 annotés vers elle. La Saison garde ses ports [mer, mer, mer], validés en jeu.]
338. `[découverte]` (session Expanded, consigné par la construction, 04.10.2026) **Un réseau de routes trop maillé bloque
    l'export Pathfinding de CAIME** (22 min sans écrire, arrêté) alors que `validate --roads` le dit correct : routes du
    Bois Rêveur reflétées par symétrie d'image (331 carrefours à 3 branches, 55 à 4, 3 à 5 ; WH1 : des fils, 55
    carrefours). Refaites en miroir exact de la grille d'hex (colonne impaire décalée d'une rangée, nord et sud échangés) :
    20 carrefours, export en 4 s. **Règle : en plus de validate, contrôler les degrés du graphe des routes (des fils, peu
    de carrefours, comme CA et WH1) et borner `process` dans le temps ; un miroir de carte se fait dans le repère des hex,
    jamais de l'image.** GUIDE § 15 n° 167.
339. `[découverte]` (session « Mise à jour miniatures Steam », consigné par la construction, 04.10.2026) **Le lanceur de
    CA retente seul 4 fois chaque envoi Workshop** : la règle « une seule modification par objet » (erreurs 306, 310) ne se
    tient pas côté lanceur. Envoi de la miniature d'Expanded (mini-pack de démonstration + image, 436 844 octets) refusé
    par Steam, « error code #25 » (`k_EResultLimitExceeded`), 4 tentatives à 17 h 36-37 ; page inchangée. La page de la
    Saison (3807973986) restait « pas encore analysée… masquée temporairement » plus de 26 h après la modification du
    03.10. Journal du lanceur : `%APPDATA%\The Creative Assembly\Launcher\launcher.log` (heure UTC). **Règle : un envoi par
    le lanceur à la fois, puis lire `launcher.log` ; en cas d'erreur 25, ne rien renvoyer (limite atteinte) ; vérifier la
    page.** Aussi : le « téléchargement de 1,5 Go » de Steam à 17 h 16 était une mise à jour d'objets Workshop
    (`content_log.txt` : « Workshop update »), pas du jeu (Warhammer3.exe, db.pack et buildid inchangés, kit intact).
    Suite : la traduction française a pris la même erreur 25, refusée AVANT tout envoi (0 octet) : limite côté compte ou
    Steam, pas côté objet ni pack ; à retenter des heures plus tard, et le lanceur ne l'affiche pas. Autres faits : un BOB
    en cours tient les packs de `data\` ouverts (remplacement refusé, WinError 32 : attendre sa fin) ; un `launcher.exe`
    fantôme fait dire « le jeu est déjà en cours d'exécution ». Suite (22 h 50) : un NOUVEL objet pour Expanded a pris la
    même erreur 25, et le lanceur a créé un objet VIDE à chacune de ses 4 tentatives automatiques (3813668505, 3813668537,
    3813668607, 3813668715 : orphelins, invisibles dans la liste ; à supprimer par Charles) : la limite est côté compte
    ou Steam, pas côté objet. **Règle : après une erreur 25, ne plus rien envoyer ni créer par le lanceur ; essayer la
    page Steam ou attendre.** GUIDE § 15 n° 168.
340. `[évitable]` (session « Expanded map avec vaults », consigné par la construction, 04.10.2026 ; concerne le site)
    **L'envoi de l'Atlas de 17 h 54 a retiré de bretonia.dev le dossier `steam/` (90 images des trois pages Workshop) et
    2 images du Bois Rêveur** : 404 pendant environ 25 min, pages Workshop cassées pour tout le monde. Cause : le dossier
    d'envoi partait du build de la session (`page_v2.py`), qui ne produit pas `steam/` ; les contrôles comparaient le
    dossier à la production, jamais la production au dossier (`verifier_deploiement.py` ne regarde que les fichiers
    texte). Corrigé vers 18 h 20 (92 fichiers remis, 432 servis identiques à l'octet). **Règle : un dossier d'envoi part de
    la liste COMPLÈTE du déploiement précédent (tout fichier servi et absent du dossier est repris), puis on compare tous
    les fichiers, lourds compris, dans les deux sens, avant et après l'envoi.**
341. `[découverte]` (construction, consigné le 04.10.2026 au grand nettoyage ; décision du 25.09.2026) **Le catalogue
    séparé des sols remplace la copie de la base de variantes de CA** (entrée manquante : n° 114 et 179 décrivaient encore
    la copie). Audit de compatibilité du 25.09 vers 17 h 45 : remplacer `terrain_textures_campaign.assetdb` cassait tout
    autre mod de carte qui livre le sien (The Old World de ChaosRobie, 443 entrées : un seul des deux vaut) ; le jeu lit
    tous les `*.assetdb` du dossier. Correctif (accord de Charles) : un fichier À NOUS,
    `warscape_asset_variation_db/<pack>.assetdb` (`saison_des_revelations.assetdb` ; `saison_expanded.assetdb` depuis le
    03.10), qui ne porte que nos ajouts (clés `wh1_*` des trois espaces de texture et plan d'eau de notre carte), aucune
    entrée de CA. Code : `textures_sol_wh1.CATALOGUE_SEPARE = True`, `CATALOGUE_SEPARE_CHEMIN`, `build_pack.py`. **Validé
    en jeu par Charles le 25.09.2026 vers 23 h 35** (pack de 21 h 46, sols autour d'Orion : « rien d'anormal »). **Règle :
    un ajout à une base de CA passe par un fichier à nous, sous un nom à nous, qui ne porte que nos clés ; jamais une
    copie de la base de CA à son chemin (n° 254) ; un catalogue par mod.** GUIDE § 15 n° 169.
342. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 0 h) **Des nœuds de route que CA ne
    connaît pas laissent des trous de tuiles** : routes de l'Atlas avec 21 carrefours voisins, virages de 60°, formes à
    trois branches collées (formes canoniques 3, 7, 23) et routes côte à côte sans lien ; BOB : 107 « Failed to find
    tile » au lieu de 75, les 32 de plus en `TileSet_roads`, 25 trous sur 26 à 1 hex de ces nœuds. `validate --roads` ne
    les voit pas. **Règle : routes aux seules formes de CA (formes 1, 5, 9, 11, 13, 21), jamais deux carrefours voisins,
    ni virage de 60°, ni deux routes côte à côte hors des villes** (codé : `routes_expanded`) ; avec l'erreur 338, une
    route se trace comme chez CA et WH1 : des fils, peu de carrefours.
343. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 2 h 15 ; **écart au guide Terry accordé
    par Charles à 2 h 10**) **Les bouts de falaise que CAIME pose autour des plages font des trous de tuiles** : CAIME
    entoure chaque plage de deux `cliff_gen_ends` (84, 230, 84) ; toutes les plages d'Expanded sont un hex de plage entre
    deux bouts. Chez CA (`wh3_main_combi_map_1`, fichiers compilés) : 412 plages, 36 bouts sur toute la carte, la plupart
    des plages raccordées directement à la falaise. Un bout a deux poses possibles (liée à la falaise ou à la plage) ;
    chez CA 36/36 liées à la falaise, 0 trou ; dans Expanded, 9 bouts liés à la plage = 9 trous côté falaise ; les 10
    plages de la carte en ont. Preuve : `05-journal\2026-10-05-tuiles-cote\RAPPORT.md` (§ 3, `bouts_e.py`,
    `liens_bob.py`). **Écart : le guide Terry de l'Atlas dit « `tile_map.png` exportée de CAIME sans retouche » ; dans
    Expanded, les `cliff_gen_ends` sont repeints en `cliff_gen` (`tuiles_expanded.composer`, raccord plage-falaise de
    CA)**. Prédicteur sur la carte avec les fleuves : 102 → 43 boîtes sans pavage ; BOB seul confirmera. Les fleuves
    doublent presque la côte (14 540 px contre 10 658) : plus de trous attendus sans cette correction. Autres faits
    (GUIDE § 15 n° 170) : forme des tuiles de côte lue dans `_tile_database\tiles\*.bin` ; BOB chaîne ancre contre
    ancre ; ni la rangée 0 du bord ni un isthme d'un hex n'ont de tuile de côte. La Saison n'est pas touchée.
344. `[évitable]` (session Expanded, consigné par la construction, 05.10.2026, 2 h 55) **Fleuves d'Expanded : un chenal
    sans eau, l'ancienne rivière de WH1 flottant dessus** (vu en jeu par Charles après l'essai de 2 h 23, qui avait
    seulement prouvé le chargement). Deux causes. (1) La chaîne du terrain lisait des COPIES des couches de la grille
    (`couches-expanded`, `villes-sortie`) de 0 h 13, antérieures au lot des fleuves (2 h 05) : aucun plan d'eau sur les
    chenaux. (2) L'étape « terrain » de la méthode de CA pour un fleuve (fond à −0,35, berges basses, pas de ruban de
    rivière sur le chenal) n'avait été confiée à personne ; dans la zone de WH1, la terre était à 0,8 u et le fond à −2,1 u
    sous les tuiles de mer. **Règle : une chaîne qui lit des copies de couches les refait depuis la source (`map.hex`)
    avant de s'en servir** (codé : `outils\couches_a_jour.py`, appelé en tête de `projet_expanded.py` ;
    `outils\chenaux_fleuves.py` refuse de tourner sur des copies périmées) ; un lot qui change la grille nomme aussi
    l'étape du terrain qui va avec, et son responsable. Chenal : `chenaux_fleuves.py` (relief du chenal, berges, objets de
    WH1 retirés ou recalés, 36 rubans de WH1 rognés). Le pilote prouve un chargement, jamais un rendu : un lot visible se
    juge en jeu (déjà la règle des erreurs 223 et 251).
345. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 3 h 40) **« Escaliers » sur les berges
    des fleuves et les côtes d'Expanded** (vus en jeu par Charles) : sur le trait des tuiles de côte, notre terre était
    partout à 0,13 et le fond à −0,63. Chez CA (relief et fond des Empires Immortels, mesurés dans le kit), le profil dépend
    de la tuile : **sous une falaise (`cliff_gen`), un plateau de 0,74 u et le fond à −0,40 ; sous une plage
    (`sea_coast`), la terre passe sous l'eau (−0,16 au trait, +0,12 à 1 u) et le fond est à −0,19**. Le guide Terry de
    l'Atlas (« pour une côte lisse en jeu, berge en pente d'environ une unité, ni marche d'un pixel ni falaise sur le
    trait de côte ») ne vaut que pour une côte SANS tuile de côte, en `generic`, comme celle de la Saison ; il ne dit rien
    du relief sous une tuile de falaise. **Règle : avec l'export CAIME (`cliff_gen` / `sea_coast`), le relief du trait suit
    le profil de CA de sa tuile** (codé : `04-projets\saison-expanded\outils\cotes_relief.py`, appelé par
    `projet_expanded` avant l'écriture du relief ; objets de WH1 et rubans suivent la différence de relief). GUIDE § 15
    n° 171 ; correction du guide Terry transmise à la session Extension. **[Règle remplacée le 05.10.2026 à 11 h 45 par
    l'erreur 346 : un profil calculé au trait des tuiles laisse encore des hachures ; chez CA, le relief est continu sous
    la mer.]**
346. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 11 h 50) **Chez CA, le relief est continu
    et lisse sous les tuiles de mer ; le trait de côte n'existe que dans les tuiles et dans le fond** (relief des Empires
    Immortels ombré au pixel : la terre se prolonge sous la mer, aucun chenal creusé dans le relief). Charles voyait encore
    des hachures, des escaliers et des chenaux imparfaits dans Expanded, parce que notre relief suivait les hex des tuiles
    (profil des côtes calculé au trait des tuiles, relief remis à 0,02 sur chaque tuile de mer, erreur 345). **Règle : ne
    jamais sculpter le trait de côte ni un chenal dans le relief ; le lisser et le laisser continu sous la mer ; l'eau se
    lit sur les tuiles, le chenal se creuse dans le fond seulement** (codé : `outils\cotes_relief.py` v2,
    `outils\chenaux_fleuves.py` sans creusement du relief, `outils\mer_tuiles.py` pour `eau_materiau`,
    `rivieres_atlas_eau`, les arbres, les décors et les contrôles). GUIDE § 15 n° 171 (réécrit).
347. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 11 h 50 ; vérifié dans le code)
    **CAIME fait une falaise de toute terre côtière qui n'est pas une plage, rivière comprise** : dans
    `CAIME\Classes\Exporters\BaselineTilemapExporter.cs`, un hex de terre voisin de la mer devient `cliff_gen` sauf s'il
    est `IsBeach` ; seul un hex `IsRiver` ET `IsBeach` donne l'indice 8, « river ending at beach » (peint en plage pour
    WH3). Les 33 embouchures d'Expanded étaient des falaises, et les rivières n'arrivaient pas à la mer. **Règle : une
    embouchure se marque Beach ET River dans CAIME** (codé : `outils\plages_expanded.py`, +49 cases). GUIDE § 15 n° 172.
348. `[évitable]` (construction, 05.10.2026, 12 h 15) **Une étape en échec masquée par un tube : startpos généré sur des
    tables de départ périmées, plantage.** Après un redémarrage de Steam, `rpfm_server` ne tournait plus ;
    `startpos_db_expanded.py` a échoué (`URLError`, connexion refusée), mais `chaine_expanded.sh` le lisait par
    `| grep | cut` : sous `set -e` sans `pipefail`, le code d'erreur d'un tube est celui de la dernière commande, et la
    chaîne a continué. La génération du startpos sur la grille neuve (Beaches) avec les tables de 04 h 02 a planté
    (`Warhammer3.exe+0x24303E1`, lecture de 0x24, 9.0.2, pile dans le chargement de `startpos.esf`) ; avec les tables
    resynchronisées (12 h 00), même grille, même pack : génération en 82 s, chargement d'Orion au tour 1. **Règle : tout
    script de chaîne en `set -e` porte `set -o pipefail` ; `rpfm_server` est relancé AVANT la première étape qui le lit ;
    `user.script.txt` est remis par un `trap … EXIT`** (codé dans `chaine_expanded.sh`). Une grille changée exige des
    tables de départ resynchronisées : la recette du § 5 le disait.
349. `[découverte]` (session Expanded, consigné par la construction, 05.10.2026, 12 h 45) **Une plage ne va que sur une
    terre basse.** Coupe de la berge nord de la Brienne : une « plage » du lot des fleuves posée sur une terre à 1,25 u ;
    le profil de plage y faisait une pente raide, d'où une ombre sombre sur l'aperçu (et une digue). Chez CA, une plage
    est sur une terre basse. Le lot des fleuves posait des plages sur 25 à 55 % des berges : proportion mesurée sur les
    berges des fleuves de la carte de ChaosRobie (`04-projets\banc-fleuve\etude\SYNTHESE-fleuves-navigables.md` § 1.2 :
    plages 25-55 %, falaises 40-70 %, approches de pont 5-10 %), reprise sans tenir compte du relief. **Règle : une plage dont la terre monte au-delà de 0,8 u dans les 3 hex vers l'intérieur
    redevient falaise, sauf les plages de port et les embouchures (erreur 347), avec le filtre des suites de 3 cases**
    (appliqué par la session Expanded à toute la carte : 909 → 621 plages ; `validate` 0 Error / 1 Warning). Grille
    changée = tables de départ resynchronisées et startpos neuf (erreur 348). GUIDE § 15 n° 173.

## Comment tenir ce fichier

- Une entrée par erreur, le jour même, avec la règle. Pas de justification, pas de récit.
- Quand une règle est codée (script, verbe, garde), le dire dans l'entrée.
- Relire les règles A1 à A5 avant chaque séance : ce sont celles qui coûtent le plus.

Ajouts du 25.09.2026 (ménage) :
- **Prochain numéro** = le plus grand + 1, vérifié par une recherche avant d'écrire (les n° 6 et 29 sont en double).
- **Une règle remplacée** ne s'efface pas : on l'annote `[Remplacée le JJ.MM.AAAA par n° X : …]`, et l'on met à jour le
  sommaire « Règles vivantes » en tête.
- **Étiquettes** avec accents de préférence ; une entrée qui ne concerne pas le mod le dit (« Concerne le site »).
- **Une découverte du jeu** est reportée au GUIDE § 15 le jour même, avec le numéro de l'entrée.
- **Toute adresse mémoire** porte la version du jeu (8.1, 9.0).

Ajout du 04.10.2026 (grand nettoyage) : entrées hors ordre, laissées telles quelles (les numéros sont cités partout) :
52 après 53, 77 après 79, bloc 258 à 264, 266, 267 après 268 ; on ne renumérote pas.

---

## Ancien sommaire (25.09.2026, remplacé le 04.10.2026)

Gardé pour mémoire ; ne plus s'y fier (sommaire en vigueur : en tête du fichier).

À lire en premier, puis les entrées des deux derniers jours ; le reste à la demande (recherche par numéro ou par mot ;
les étiquettes s'écrivent aussi sans accent : chercher `\[(é|e)vitable\]`). Les numéros 6 et 29 sont en double (citer
A6 / B6 et 29-undo / 29-attribution).

Méthode
- Ne jamais jeter la sortie d'un outil, la regrouper (1). Un message qui cite une donnée se vérifie dans la donnée (2, 54, 61).
- Un témoin se rejoue avec la commande exacte, drapeaux compris, à chaque tour (30, 35, 39).
- Un seul changement de fond entre deux essais ; jamais le pilote d'essai et le pack dans le même essai (53, 239).
- Plantage aléatoire : 10 essais par variante, « piste » avant « cause » (186) ; un essai ne conclut qu'à son terme (52).
- Ce qui se voit en jeu se vérifie EN JEU, pas dans Terry ni dans un fichier compilé (67, 109, 113, 114, 146, 282).
- Annoncer la mesure du produit écrit, jamais le bilan de l'algorithme ni l'intention du code (81, 192, 231, 248) ;
  toute heure vient de `date` (211).
- Un réglage qui porte un contrôle validé ne change qu'en annonçant le contrôle qui tombe (240).
- Contenu et aspect : WH1 d'abord (45, 48, 102, 222) ; conventions du moteur de WH3 : CA d'abord (53, 93, 126, 202, 251).
Charles et le PC
- Prévenir Charles avant TOUT lancement du jeu et lui dire de ne rien toucher (124, 132, 177) ; ne pas piloter l'écran
  sans son accord du moment, `etat_clavier.py` après (4, 108) ; jamais `open_application` sur Terry ou le jeu (88, 152) ;
  `essai_tours_auto.py --nettoyer` après tout arrêt forcé (178).
Sessions en parallèle
- Préavis : annoncer l'heure affichée par `preavis.py heure`, `preavis.py attendre` en arrière-plan, relire les
  messages, puis écrire (145, 215, 221). Vérifier qu'un nom de fichier est libre (121). Le jeu d'essai n'est à personne
  d'autre (144).
Shell
- Ni heredoc, ni `python -c` composé, ni `sed` à antislashs, ni script écrit par PowerShell : un fichier écrit avec
  l'outil d'écriture (129 ; crochet `garde_commandes.py` : 212, 217, 228 ; 237). Chemins absolus (75, 218). À
  transmettre à chaque agent lancé (193).
- Fichier `wh3_mcp_command.json` : UTF-8 sans BOM ; vérifier l'encodage avant l'essai (281).
Pack, startpos, mise à jour
- Essai de démarrage avant d'annoncer un pack qui change une table (107) ; journal du pack : chaque table du lot avec
  son nombre de lignes (131) ; scripts changés → startpos régénéré, `__save_counter` = 1, pack reconstruit (58, 112).
- Jamais une de nos régions dans un groupe, une liste ou une table de liens de CA (110, 154, 156 ; `verifier_groupes.py`) ;
  jamais un fichier à nous à un chemin que CA cite (254).
- À chaque reprise : `crash_report\` et `save_games\` (69). Après une mise à jour du jeu : ne rien construire avant
  d'avoir vérifié `raw_data\db` ; empreintes des DLL ; les adresses d'avant sont celles de la 8.1 (206, 216, 220) ;
  lire les écouteurs nommés en erreur au premier essai (252).
Carte
- Positions des entités en espace des hex ; un raster se lit à z × √3/2 (89). `sea_height` sous 0 en mer pour ne pas
  masquer les maillages d'eau, sans effet sous la terre ; mer pleine sous l'eau à moins de 2 u des terres
  (155, 223, 240). Éclairage : zones à la manière de CA, une à la fois (251).
Règles périmées (ne plus appliquer telles quelles) : 25, 63 (peinture de `tile_map.png`), 73, 74 (code),
97 (en 9.0), 102 (une surface), 109 (état des zones), 113 (height = surface), 143 (limitée à l'IA),
155 (`sea_height` sous 0 partout), 208 (pour les zones), 230 (moyen), 232 (3 clics),
§ C « La cote de CA » (côte peinte) ; anciennes règles du GUIDE § 10-11 (anneaux interdits),
n° 55/81/84 (`tile_map.png` peinte), n° 137 (`sea_height` sous 0 partout).
Adresses mémoire : celles relevées avant le 24.09.2026, 16 h 07, sont celles du jeu 8.1 (signatures historiques).
