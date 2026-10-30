# État courant

STATE.md décrit l'état courant, pas l'historique. Un chantier terminé se
condense en trois lignes. Ce qui est durable part dans un ADR ou dans
`docs/ARCHITECTURE.md` ; ce qui est historique est déjà dans git.

## Avancement

- **Chantier en cours** : 9, propreté et solidité, ouvert le
  30 octobre 2026 avec la planification de la v3 (chantiers 9, 10 et 11,
  `ROADMAP.md`). Fait : ADR traduites en anglais et renommées,
  renvois d'ADR et commentaires périmés corrigés, `window._perform` passé
  au logger, booléens de priorité et de date en paramètres nommés
  (règle ruff `FBT` activée), règles ruff `S` activées, `release.yml` refuse toute entrée qui n'est
  pas un tag `vX.Y.Z` existant, dépendances de développement en versions
  exactes suivies par Dependabot `pip`, `SECURITY.md` (signalement privé
  GitHub, accusé de réception sous sept jours, dernière version seule)
  (30 octobre 2026). Sauvegarde avant migration livrée
  (`SPECIFICATION.md` §2.7.10, `storage.load`). Spécification écrite pour
  l'`OSError` au démarrage (§3.6, situation 4), code à suivre.
  **Contrôle visuel en attente** (PR #187) : marquer puis démarquer une
  tâche prioritaire dans Jour, Demain et Réserve, avant la prochaine
  version. `mypy` et `gtk4-broadwayd` validés comme
  outils de CI (`CLAUDE.md` §4 règle 6). Chantier 8 terminé le
  29 octobre 2026, `2.0.0` publiée (ci-dessous).
- **Pour toute nouvelle langue** : l'ajouter à `po/LINGUAS`, créer le
  `.po` (`msginit`) avant `meson setup --reconfigure build`, Meson ne
  suivant pas ce fichier. Traduire les deux formats de date
  (`core/dates.py`) et le contexte `statistics column`. Le runtime
  Flatpak n'embarque que les locales du système : contrôle visuel sur une
  build hôte.
- **`2.0.0` est publiée** (29 octobre 2026, sur `//51`) : cinq langues en
  traduction machine (PR #174 à #178), correctifs de dates (PR #179),
  release PR #180 (squash `c3a04bc`). Tag `v2.0.0` annoté et signé,
  poussé, `release.yml` vert (run `40909905054`, build et deploy),
  `rature.flatpak` joint à la release (109 600 octets), metainfo du bundle
  en `2.0.0`, le dépôt sert un commit « Built from c3a04bc ». PKGBUILD et
  `.SRCINFO` recalés sur l'archive du tag (`sha256sum` identique sur deux
  téléchargements) dans un commit de suivi. Aucune migration. **Reste à
  la charge de VertOurs** : rien. Suivie de la PR `test/coverage-gate` :
  seuil de couverture CI étendu aux modules sans `gi` hors `core/` (liste
  dans `pyproject.toml`, commande devenue `pytest --cov`), test des formats
  `strftime` de chaque catalogue.
- **Mise à jour confirmée** : `flatpak update` de `0.10.1` vers `1.0.0`
  testé le 8 septembre 2026, sans souci, via le dépôt auto-hébergé.
  `1.0.0` → `1.1.0` : mise à jour lancée par l'agent le 15 septembre 2026
  (catalogue français vérifié au niveau fichier, 69 messages, valide),
  rendu de l'interface en français confirmé par VertOurs le même jour
  (`CLAUDE.md` §6). `1.2.0` → `1.3.0` : `flatpak update` par VertOurs le 28 septembre 2026, `flatpak info` affiche `1.3.0`. `1.3.0` → `1.4.0` : `flatpak update` par VertOurs le 5 octobre 2026, fonctionnalité confirmée sur la version installée. `1.5.0` → `1.6.0` : `flatpak update` lancé par l'agent le 12 octobre 2026, migration 1 → 2 confirmée par VertOurs sur ses vraies données le même jour. `1.6.0` → `1.7.0` : `flatpak update` lancé par l'agent le 12 octobre 2026, migration 2 → 3 confirmée par VertOurs sur ses vraies données le même jour. `1.7.0` → `1.7.1` : `flatpak update` lancé par l'agent le 12 octobre 2026, passage au runtime `//51`, sans migration, confirmé par VertOurs le même jour. `1.7.1` → `1.8.0` : `flatpak update` par VertOurs le 25 octobre 2026 après sauvegarde, migration 3 → 4 confirmée sur ses vraies données le même jour. `1.9.0` → `2.0.0` : `flatpak update` par VertOurs le 29 octobre 2026, `flatpak info` affiche `2.0.0`, commit `337b5907` identique au bundle publié, sans migration.
- **Bump runtime `//50` → `//51`** : PR #156 (squash `f9d8537`), livré dans `1.7.1`, avancé au
  12 octobre 2026 par décision de VertOurs (GNOME 51 sorti le
  16 septembre, image CI `gnome-51` publiée). Manifeste et image CI
  seuls ; les planchers Python et Meson ne bougent pas (voir « Versions
  retenues »). Flatpak construit et parcouru sous `//51` sur des données
  jetables (toutes les fenêtres et dialogues ouverts, `G_ENABLE_DIAGNOSTIC=1`) :
  aucun avertissement GTK ni libadwaita. Seuls signalements, forcés par
  `warnings.simplefilter("always")` : deux `DeprecationWarning` internes
  à PyGObject 3.58 (`gi/events.py`, API `asyncio` retirées en
  Python 3.16), hors de notre code. Contrôle visuel complet sous `//51`
  fait par VertOurs le 12 octobre 2026, avant fusion.
- **Image CI épinglée par digest, mise à jour manuelle** : `ci.yml` et
  `release.yml` référencent
  `ghcr.io/flathub-infra/flatpak-github-actions` par digest plutôt que
  par étiquette flottante (`:gnome-51` depuis le bump runtime), lot F de la revue de sécurité
  du 24 septembre 2026. Dependabot ne suit pas les images des blocs
  `container:` d'un fichier de workflow (`github-actions` ne couvre que
  les actions, `docker` que les `Dockerfile`/Kubernetes/Helm ; vérifié
  via `dependabot/dependabot-core#5819`, toujours ouverte). Bump manuel
  à chaque changement d'image voulu (fait pour `gnome-51` le 12 octobre 2026) :
  `skopeo inspect docker://ghcr.io/flathub-infra/flatpak-github-actions:<étiquette>`,
  copier le champ `Digest`, remplacer dans les deux fichiers, garder le
  commentaire `# <étiquette>` en clair à côté.
- **GitHub Sponsors actif** : compte de VertOurs en place et public,
  vérifié le 15 septembre 2026 (`sponsorsListing.isPublic: true` côté
  API, `github.com/sponsors/VertOurs` répond 200). Le lien du README et
  le bouton « Sponsor » du dépôt sont désormais fonctionnels.
- **Reste à la charge de VertOurs, non bloquant** (chantier 6) :
  soumission AUR (compte + clé SSH sur `aur.archlinux.org`), soumission
  COPR (compte Fedora sur `copr.fedorainfracloud.org`), soumission
  Mageia (dépôt communautaire). Repoussées en v3/v4 par décision du
  15 septembre 2026, aucun des trois ne demande de compte créé par
  l'agent. Détail dans « Chantiers terminés ».
- **Mode de travail** : agent dans l'IDE, PyCharm

## Dépôt

- `github.com/VertOurs/Rature`, public. `main` protégée : PR obligatoire,
  squash seul, historique linéaire.
- Signature GPG active : clé ed25519
  `25DA27801D5F4ECA1DAA2101E89227EAC418BC4A`, `commit.gpgsign` local, clé
  publique déjà sur GitHub (le tag `v0.2.0` remonte `verified: true` côté
  API, vérifié le 31 août 2026).
- « Require status checks » actif dans le ruleset `main` : `lint`, `test`,
  `meson`, `flatpak`, mode strict, aucun contournement possible même par un
  admin. Vérifié le 31 août 2026 via `gh api repos/.../rulesets`.
- Deuxième clé GPG, dédiée à la **signature du dépôt Flatpak** (jamais aux
  commits) : ed25519 `C2CBB256D91B01B920B0BE3898280657575FC9DA`, uid
  « Rature Flatpak repo signing », sans passphrase. Publique versionnée,
  privée dans le secret Actions `FLATPAK_GPG_PRIVATE_KEY`. GitHub Pages
  activé (`build_type=workflow`), sert `https://vertours.github.io/Rature/`.

## Versions retenues

Revérifiées le 12 octobre 2026, à revérifier avant toute mise à jour du
manifeste (`CLAUDE.md` §4 règle 8). Sur Flathub, `//51` est la branche la
plus récente (publiée le 9 octobre 2026), `//52` n'existe pas, aucune
branche n'est marquée en fin de vie. La documentation Flathub des runtimes
ne liste pas les versions, seulement la règle : une branche est supportée
environ un an, jusqu'à la sortie de la stable suivante.

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//51` | Stable courante. SDK 51 : Python 3.14.7, Meson 1.12.0, GTK 4.24.0, libadwaita 1.10.0, PyGObject 3.58.0. Image CI `gnome-51` épinglée par digest |
| Python cible | 3.13 | Besoin du projet, jamais au-dessus de la plus ancienne distribution visée : Mageia 10 est en 3.13.15 (Fedora 44 et Arch en 3.14). `requires-python` et ruff `py313`. Le job `test` de la CI tourne en matrice sur 3.13 (plancher) et 3.14 (runtime) : ruff `py313` bloque la syntaxe 3.14, pas une API de la bibliothèque standard apparue en 3.14. Le check exigé par le ruleset reste `test`, un job de synthèse qui ne passe que si les deux versions passent ; lint et meson restent en 3.14. Une cible `py314` ferait réécrire à `ruff format` des `except (A, B):` en syntaxe 3.14 seule (PEP 758) |
| Version du projet | `2.0.0` | Clôture de la v2 (chantiers 6 à 8) : cinq catalogues en traduction machine et correctifs de dates, sans changement de format. Coupée le 29 octobre 2026 |
| Meson minimal | 1.9 | Besoin du projet, jamais au-dessus de la plus ancienne distribution visée : Mageia 10 en 1.10.1, Fedora 44 (et la machine) en 1.11.2, Arch en 1.12.1, SDK 51 en 1.12.0. Aucune fonction postérieure à 1.9 utilisée |

`0.10.0` (3 septembre 2026) publie les sept fonctionnalités du chantier 4
(annulation de la dernière suppression, ajout d'une tâche déjà rayée,
raccourcis clavier et fenêtre d'aide, export d'une journée en texte,
recherche dans les archives, fenêtre Statistiques, traduction française
complète) plus le correctif du fichier JSON non-objet.

`0.10.1` (3 septembre 2026) publie le dépôt Flatpak auto-hébergé et le
bundle autonome (§5.2, §5.3) et corrige l'interface restée en anglais sous
Flatpak.

`1.0.0` (8 septembre 2026) ferme la v1 : chantiers 0 à 5 tous terminés, le
critère de fin du chantier 5 est atteint (installation et mise à jour
automatique confirmées sur une machine propre). Aucun changement
fonctionnel depuis `0.10.1`. AUR et COPR repoussés au chantier 6.

`1.1.0` (15 septembre 2026) ferme le chantier 6 : logging structuré
confirmé par `journalctl` en usage réel, paquetage natif (AUR, COPR,
Mageia) préparé et vérifié en conteneur mais pas encore soumis (repoussé
en v3/v4), README et page de présentation refaits, `FUNDING.yml`. Aucune
migration de format (`migrations.py` toujours à vide, rien à couvrir).

`1.3.0` (28 septembre 2026) retire la boîte de dépôt et corrige le menu
« ⋯ » des tâches. Mineure : un retrait serait majeur en SemVer strict,
mais `ROADMAP.md` réserve `2.0.0` à la fin du chantier 8 et prévaut
(`CONTRIBUTING.md`, « Versioning »). Indépendante du bump `//51`.

`1.4.0` (5 octobre 2026) publie le renvoi manuel d'une tâche du jour
vers la réserve (première case de 7.2, PR #139) et la conservation du
focus et du défilement à la reconstruction des listes (PR #138).
Mineure : nouvelle fonctionnalité, aucune migration de format.

`1.4.1` (5 octobre 2026) corrige le décalage de 46 px des numéros et
textes sur les lignes sans flèche (rayées, récurrentes), relevé à la
revue de code (PR #142). Corrective.

`1.5.0` (5 octobre 2026) publie le renvoi d'une tâche du jour par
glisser-déposer sur l'entrée Reserve (PR #144) et le réordonnancement
de la réserve par glisser-déposer (PR #145). Mineure : deux
fonctionnalités, aucune migration de format.

`1.6.0` (12 octobre 2026) publie la récurrente une semaine sur deux
(PR #148) et le format de données version 2, première migration réelle.
Mineure : le changement de format serait majeur en SemVer strict, mais
`ROADMAP.md` réserve `2.0.0` à la fin du chantier 8 et prévaut
(`CONTRIBUTING.md`, « Versioning »). Un fichier écrit en version 2 n'est
plus lisible par `1.5.0` et antérieures.

`1.7.0` (12 octobre 2026) publie la priorité, dernière case de 7.2
(PR #152), et le format de données version 3. Mineure pour la même
raison que `1.6.0`. Un fichier écrit en version 3 n'est plus lisible par
`1.6.0` et antérieures.

`1.7.1` (12 octobre 2026) passe le runtime à GNOME 51 (PR #156).
Corrective : aucune fonctionnalité, aucun changement de format.

`1.8.0` (25 octobre 2026) publie la vue Demain, chantier 7.3 (PR #160 à
#165), et le format de données version 4. Mineure pour la même raison
que `1.6.0`. Un fichier écrit en version 4 n'est plus lisible par
`1.7.1` et antérieures. Clôt le chantier 7.

`1.9.0` (25 octobre 2026) publie les noms accessibles (PR #170) et la
fenêtre Statistiques rafraîchie au passage du jour (PR #171). Mineure,
aucun changement de format.

**Bump vers GNOME 51** : avancé au 12 octobre 2026 par décision de
VertOurs, initialement prévu pas avant le 16 octobre. Touche le
manifeste et l'image CI. Livré dans `1.7.1` (corrective), première
version taguée après le bump.

## Environnement de la machine

- **Deux interpréteurs.** Le venv du projet est en Python 3.13 sans `gi`, il
  sert à `ruff` et `pytest`. `/usr/bin/python3` est en 3.14 avec `gi`
  (GTK 4.22, libadwaita 1.9.3), il sert à lancer l'application hors Flatpak.
- Option Meson `python` : en local
  `meson setup build -Dpython=/usr/bin/python3`. Défaut sous Flatpak et en
  CI.

## Chantiers terminés

- **Chantier 0**, PR #1, 29 août 2026 : dépôt, Meson, gettext, fenêtre vide,
  manifeste Flatpak, CI quatre jobs. Pas à pas dans
  `docs/internal/CHANTIER-0.md`.
- **Deux passes de correctifs**, PR #3 et #4 : revue externe et audit
  interne, règle de style reformulée, CI durcie, manifeste nettoyé. `CLAUDE.md`
  §5.2 tranchée, option (a).
- **Déduplication documentaire**, deux sessions, PR #5 et #6 : spécification
  extraite dans `docs/internal/SPECIFICATION.md`, conventions dans
  `CONTRIBUTING.md`, `CLAUDE.md` réduit de ~27 ko à ~11 ko, renvois
  normalisés sur `SPECIFICATION.md §X`.
- **Chantier 1**, PR #7 à #11 : logique métier de `core/` —
  `models` (Task, ReserveItem, RecurringItem, Deletion), `session` (liste du
  jour et ses opérations), `storage` (JSON atomique, archivage), `migrations`
  (socle). Couverture `rature.core` gatée à 90 % en CI, aucun import `gi`.
- **Chantier 2**, PR #13 à #15 : réserve (CRUD + tirage), récurrentes
  (CRUD + `recurrence.due_on`), passage du jour (`reference_date` bascule
  04:00, `roll_over` en avant seulement, six étapes, multi-jours). `Task`
  gagne `source_created` ; l'archivage écrase (idempotent, ADR 0003 +
  ARCHITECTURE). Couverture `rature.core` 100 %.
- **Durcissement avant chantier 3**, PR #18 à #20 : `Task`/`Deletion`
  validés à la construction, horloges obligatoires partout dans `core/`,
  `Session.move_before` ; couche de coordination `App` (`core/app.py`,
  ouverture/premier lancement/quarantaine, passage du jour automatique,
  enrobage des mutations) ; `config.py` adopté, traductions par
  `gettext.bindtextdomain`/`textdomain`, schéma GSettings de fenêtre posé
  sans être lu, porte de couverture CI à 100 % avec `--cov-branch`,
  dependabot, version 0.2.0. Le chantier 3 peut commencer sans toucher au
  build.
- **Chantier 3**, versions `0.3.0` à `0.9.0` (détail dans `CHANGELOG.md`) :
  interface reconstruite en `.ui` — fenêtre principale (navigation
  latérale, taille et état persistés par GSettings, À propos), vue Jour
  (lecture, édition, réordonnancement par glisser-déposer), vue Réserve
  (+ glisser-déposer d'un élément vers l'entrée Day), vue Récurrentes,
  fenêtre d'archives en lecture seule (`App.archived_session`), et
  l'adaptation aux fenêtres étroites (`AdwBreakpoint` sous 500 unités,
  panneau latéral replié avec bouton retour). Couvre `SPECIFICATION.md`
  §2 et §3 en entier.
- **Purge de dette avant chantier 4**, PR #38 à #46 : revue externe puis
  autocritique du chantier 3. Couplage à l'ordre et à la structure des
  `.ui` supprimé, titres d'en-tête en `AdwWindowTitle`, logique des vues
  factorisée (`inline_rename`, `list_helpers`, `reorder` testé), plantage
  au démarrage sur un JSON non-objet corrigé. Deux points fragiles mais
  corrects laissés commentés. Correctifs #44 et #46 en attente de release.
- **Chantier 4**, PR #49 à #76 : confort et traductions. Annulation de la
  dernière suppression, ajout d'une tâche déjà rayée (Maj+Entrée),
  raccourcis clavier + fenêtre d'aide, export d'une journée en texte,
  recherche dans les archives, fenêtre Statistiques (`core.search`,
  `core.stats`, `App.search_archives` / `archive_matches` / `statistics`).
  Traduction française : `fr.po` à 100 %, tout `_()` extrait
  (`POTFILES.in`), `LC_TIME` réaligné sur la langue des messages au
  démarrage (`rature.i18n`). Couvre `SPECIFICATION.md` §3.11 à §3.14 et le
  critère de langue du `ROADMAP`.
- **Chantier 5**, versions `0.10.0`, `0.10.1` et `1.0.0` (détail dans
  `CHANGELOG.md`) : publication. Qualité façon Flathub sans Flathub
  (`flatpak-builder-lint` manifeste et dépôt en CI, metainfo et README
  complétés, `ARCHITECTURE.md` publié en anglais). Dépôt Flatpak
  auto-hébergé signé sur GitHub Pages (clé et workflow détaillés dans
  « Dépôt » ci-dessous) et bundle `.flatpak` joint à chaque release ;
  installation et mise à jour automatique confirmées sur une machine
  propre. AUR et COPR repoussés au chantier 6, `PKGBUILD` déjà écrit dans
  `build-aux/aur/PKGBUILD`. Clôturé par `1.0.0`, qui ferme la v1.
- **Chantier 6**, PR #107 à #117, 15 septembre 2026 : observabilité et
  finition, aucun changement fonctionnel visible pour l'utilisateur en
  dehors du correctif de focus (non reproduit, voir plus bas). Issue #85
  (trou de couverture `storage`) close en ouverture de chantier.
  Logging stdlib (`rature.logging_setup`, un handler stderr, niveau
  `RATURE_LOG_LEVEL`) branché dans `src/rature.in` ; six points visés,
  cinq instrumentés (démarrage, chemin des données, quarantaine, passage
  du jour, archivage, échec d'écriture ; migration appliquée en attente,
  aucune migration n'existe encore) et confirmés par un lancement réel
  avec `journalctl` le 15 septembre 2026, sur le binaire installé hors
  Flatpak et un dossier de données jetable ; aucun texte de tâche dans
  les quatre captures. Focus après ajout en réserve : bug non
  reproductible par VertOurs ni par l'agent, garde-fou de non-régression
  ajouté (`tests/test_focus_kept_on_add.py`) plutôt qu'un correctif à
  l'aveugle. Paquetage natif préparé et vérifié par une construction
  réelle en conteneur (Arch, Fedora 44, Mageia 10) pour AUR, COPR et
  Mageia, `tests/test_versions.py` étendu pour garder les trois `.spec`/
  `PKGBUILD` synchronisés avec la version du projet ; soumission
  effective repoussée en v3/v4 (comptes personnels requis). README
  refait (statut à jour, trois badges, en-tête recentré sur l'icône
  existante, section « Why another todo app » en première personne),
  page de présentation GitHub Pages étoffée
  (`build-aux/flatpak/index.html`, prend effet au prochain tag `v*`),
  logo abandonné, `FUNDING.yml` ajouté. Alertes de sécurité Dependabot
  activées. Critère de fin atteint le 15 septembre 2026. Clôturé par
  `1.1.0`, coupée le même jour.

- **Chantier 7**, 22 septembre au 25 octobre 2026, versions `1.2.0` à
  `1.8.0` : 7.1 boîte de dépôt livrée puis retirée (ADR 0007, PR #135) ;
  7.2 renvoi en réserve, réordonnancement de la réserve, priorité ; hors
  cases, récurrente une semaine sur deux ; 7.3 vue Demain (ADR 0008,
  PR #160 à #165). Trois migrations réelles (1 → 2, 2 → 3, 3 → 4), chacune
  testée sur des fichiers fabriqués puis confirmée sur les vraies données
  de VertOurs après sauvegarde.
- **Chantier 8**, 25 au 29 octobre 2026, versions `1.9.0` et `2.0.0` :
  noms accessibles (PR #170), Statistiques rafraîchies au passage du jour
  (PR #171), catalogues `es`, `de`, `pt_BR`, `ru`, `eo` en traduction
  machine signalée (PR #174 à #178), formats de date pris au catalogue
  avec repli sans locale, correctifs de la revue de code (PR #179).

## Documents

Cadrage relu, contradictions résolues, six cas limites tranchés en
`SPECIFICATION.md` §2.7 le 25 août 2026.

`SPECIFICATION.md` §3, spécification d'interface, ajoutée le 31 août 2026 :
fenêtre principale, les trois vues, fenêtre d'archives, démarrage et refus,
fenêtres étroites, textes et icônes. Entièrement couverte par le
chantier 3, terminé.

`SPECIFICATION.md` §3.11 à §3.14 (raccourcis et fenêtre d'aide, export
texte, recherche dans les archives, fenêtre Statistiques) et la note de
cohérence de langue en §3.8 ajoutées au chantier 4, terminé.

`ROADMAP.md` étendue à la v2 le 4 septembre 2026 (PR #102) : chantiers 6
(observabilité et finition), 7 (capture et réserve) et 8 (confort et
langues), qui closent sur `2.0.0`. `CONTRIBUTING.md` mis à jour en
conséquence : les versions majeures sont désormais pilotées par les
jalons de `ROADMAP.md`, qui prévaut sur les règles d'incrément générales.

`ROADMAP.md` étendue à la v3 le 30 octobre 2026 : chantiers 9 (propreté
et solidité), 10 (synchronisation entre appareils) et 11 (compagnon
Android, Jour et Réserve), qui closent sur `3.0.0`. Todoist abandonné ;
version mobile complète toujours écartée.
