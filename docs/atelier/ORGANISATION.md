# Atelier de modding Total War — organisation et règles de travail

Ce fichier dit **où vont les choses, comment on nomme, ce qu'on fait au début et à la fin d'une séance, et comment on
consigne les erreurs**. **Le point d'entrée est `CLAUDE.md`** (état du projet, sessions et domaines, recettes, règles) ;
le fond du métier est d'abord dans les guides de l'Atlas (`05-journal\2026-09-23-extension-carte\travail\site\atelier\`,
règle du 04.10.2026, `CLAUDE.md` § 6), puis dans `GUIDE.md` (nos découvertes, § 15) ; le journal des erreurs dans
`ERREURS-ET-LECONS.md`. `AGENTS.md` renvoie à
`CLAUDE.md` pour les agents qui lisent ce nom.

## 1. Ordre de lecture pour qui reprend le dossier

L'ordre de lecture est dans `CLAUDE.md` § 1 (le fichier d'entrée) ; il n'est pas répété ici pour ne pas diverger.

## 2. L'arborescence et ce qui va où

```
TotalWar-CampaignMap\
├── CLAUDE.md, README.md, GUIDE.md, ERREURS-ET-LECONS.md, AGENTS.md   ← les seuls fichiers à la racine
├── 01-outils\      outils installés ou compilés. On n'y écrit qu'en compilant le fork ou en
│                   déposant une version d'outil (dossier versionné : rpfm-v5.0.6-..., jamais écrasé).
├── 02-scripts\     un script = un travail, avec son mode d'emploi en tête de fichier.
│                   .py en UTF-8 ; .ps1 en ASCII pur (PowerShell 5.1 lit sans BOM en ANSI).
├── 03-references\  un sous-dossier par projet : croquis, cartes, images, textes qui inspirent.
├── 04-projets\     un sous-dossier par projet (voir § 3). Le map.hex d'une vraie carte vit dans
│                   l'Assembly Kit (raw_data\EmpireDesignData\campaign_maps\<carte>\) ; ici on
│                   garde tout ce qui le fabrique et le contrôle.
├── 05-journal\     tout ce qui est daté : preuves, captures, journaux, sauvegardes des tables,
│                   inventaires. Nom : AAAA-MM-JJ-sujet ou sujet-JJ-MM-AAAA. On n'y supprime rien sans
│                   l'accord de Charles (liste montrée d'abord, corbeille, jamais d'effacement définitif).
├── 99-archives\   ce qui ne sert plus (scripts remplacés, essais, anciens projets), RANGÉ et non supprimé,
│                   sous le chemin d'origine (99-archives\02-scripts\..., 99-archives\04-projets\...), avec
│                   `INDEX.md` qui dit quoi, pourquoi et quand. Charles seul décide de supprimer.
├── 99-a-supprimer-AAAAMMJJ\   (pratique du 23.09, remplacée depuis le ménage du 03.10 : la corbeille de Windows,
│                   après accord de Charles sur la liste)
└── .claude\        réglages de Claude Code pour ce projet : `settings.json`, `hooks\garde_commandes.py` (le garde
                    des commandes, `CLAUDE.md` § 6).
```

`05-journal\INDEX.md` dit, dossier par dossier, ce qui est vivant, ce qui est une archive et ce qui est remplacé ; les
journaux de commandes (`pack-*.log`, `startpos-*.log`, `essai-*.log`) sont à la racine de `05-journal\`.

Ce qui ne va nulle part ici : les autosaves et `backups\` de CAIME (ils naissent à côté du
`map.hex`, on les laisse là et on ne les copie pas), les paquets du Store (non relocalisables),
l'installation officielle de CAIME (`%LOCALAPPDATA%`).

## 3. Les projets de carte

Deux projets vivants (le modèle « une fiche, un dessin, une légende » de l'île d'essai du 20.09 ne sert plus) :
- `04-projets\saison-des-revelations\` : la Saison (carte `wh_dlc05_wood_elves_map_1`) ; fiche `notes.md` ;
- `04-projets\saison-expanded\` : Saison Expanded (carte `saison_expanded_map`) ; `README.md`, `PLAN.md`, `JOURNAL.md`,
  `outils\`.
Le nom de carte (dossier de l'Assembly Kit) : minuscules, chiffres et soulignés, sensible à la casse. Clés de base :
`saison_` pour tout ce que nous créons, `wh_dlc05_` seulement pour ce qui vient de WH1 (décision du 25.09, `CLAUDE.md`
§ 2) ; l'ancienne convention « clés préfixées par le nom de carte » (`ile_claude_…`) est abandonnée.

## 4. Rituel de séance

**Avant** : lire (§ 1) ; relire la section du guide de l'Atlas de l'étape du jour (`CLAUDE.md` § 6) ; vérifier
l'environnement (`GUIDE.md` § 16, trente secondes) ; si la séance touche CAIME, `git status` et `git log -3` dans le
fork, et que rien n'est en cours de fusion.

**Pendant** : consigner chaque erreur dans `ERREURS-ET-LECONS.md` **au moment où on la comprend**,
pas en fin de séance ; ne jamais jeter la sortie d'un validateur, la regrouper ; comparer chaque
import au dessin par un PNG de contrôle.

**Après** : envoyer son état à la Construction, seule à écrire `CLAUDE.md` § 4 (`CLAUDE.md` § 3) et, en fin de
chantier, un point de reprise daté dans `05-journal\`
(et son entrée dans `05-journal\INDEX.md`) ; `notes.md` si une demande de Charles change ; `GUIDE.md` § 15 pour chaque
découverte ; commettre le fork avec des fichiers nommés (jamais `git add -A`). Rien n'est envoyé en amont ni
redistribué sans l'accord de Charles.

## 5. Comment consigner une erreur

Le test : **« quelqu'un l'avait-il déjà écrit quelque part ? »**

- Si oui (guide, journal, doc officielle, message d'un outil, donnée sur disque) : c'était
  **évitable**. Entrée dans `ERREURS-ET-LECONS.md` avec l'étiquette `[évitable]`, la règle qui
  l'évite, et si possible la règle **codée** (garde dans un script, verbe, vérification
  automatique). Une règle seulement écrite se ré-oublie.
- Si non : c'était une **découverte** (un comportement de l'outil que personne ne connaissait).
  Entrée avec l'étiquette `[découverte]`, le fait établi et la preuve, puis report dans
  `GUIDE.md` § 15 (pièges) ou dans la section concernée. La prochaine fois, elle serait évitable.

Une entrée = quoi → symptôme → cause → règle. Pas de récit, pas de justification.

## 6. Les interdits propres à l'organisation du dossier

Les règles non négociables (git, BOB / Terry / Tweak, shell, sauvegarde du kit, publication) sont dans `CLAUDE.md` § 6.
En plus :
- Écrire dans `01-outils\` autrement qu'en compilant le fork ou en déposant une version datée.
- Supprimer quoi que ce soit dans `05-journal\` sans l'accord de Charles (corbeille seulement).
- Usage commercial, service pour des tiers, redistribution des fichiers générés : interdits par les licences.
