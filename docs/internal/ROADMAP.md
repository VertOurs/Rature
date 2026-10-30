# Roadmap

Cette roadmap décrit la construction, à partir de la spécification. Le POC
est abandonné, voir `docs/adr/0004-abandon-the-prototype.md`.

Chaque chantier a un critère de fin. On ne passe pas au suivant tant qu'il
n'est pas atteint.

> **L'avancement réel vit dans `STATE.md`.** Les cases à cocher de ce
> document décrivent le périmètre de chaque chantier, pas son état.

---

## Vue d'ensemble

### Version 1

| Chantier | Objet | Visible pour l'utilisateur |
|---|---|---|
| 0 | Fondations : dépôt, Meson, CI, licence | Non |
| 1 | Logique métier et tests | Non |
| 2 | Réserve et récurrentes, côté logique | Non |
| 3 | Interface reconstruite | Oui, beaucoup |
| 4 | Confort et traductions | Oui |
| 5 | Publication : dépôt auto-hébergé | Oui |

### Version 2

| Chantier | Objet | Visible pour l'utilisateur |
|---|---|---|
| 6 | Observabilité, finition et paquetage natif | Peu |
| 7 | Capture et réserve | Oui, beaucoup |
| 8 | Confort et langues | Oui |

### Version 3

| Chantier | Objet | Visible pour l'utilisateur |
|---|---|---|
| 9 | Propreté et solidité | Peu |
| 10 | Synchronisation entre appareils | Oui |
| 11 | Compagnon Android : Jour et Réserve | Oui, beaucoup |

`0.9.x` correspond aux chantiers 0 à 4 terminés : fonctionnellement
complet, non publié. `1.0.0` correspond aux chantiers 0 à 5 tous
terminés : l'application est installable et se met à jour depuis le
dépôt auto-hébergé. C'est la clôture de la v1.

`2.0.0` correspond aux chantiers 6, 7 et 8 tous terminés, chacun avec
son critère de fin atteint. C'est la v2. Les versions `1.x`
intermédiaires suivent les règles d'incrément de `CONTRIBUTING.md`.

`3.0.0` correspond aux chantiers 9, 10 et 11 tous terminés, chacun avec
son critère de fin atteint. C'est la v3. Planifiée avec VertOurs le
30 octobre 2026. Les versions `2.x` intermédiaires suivent les mêmes
règles.

---

## Chantier 0 : fondations

Aucune fonctionnalité. On construit la chaîne de production.

- [ ] Créer le dépôt GitHub public
- [ ] Licence GPL-3.0, fichier LICENSE et en-têtes de fichiers
- [ ] Arborescence complète, vide mais en place
- [ ] Meson qui construit une fenêtre vide
- [ ] gettext branché, un `fr.po` même presque vide
- [ ] `pyproject.toml` avec ruff et pytest configurés
- [ ] Manifeste Flatpak qui appelle Meson
- [ ] CI GitHub Actions : ruff, pytest, construction du Flatpak
- [ ] Désactiver merge commit et rebase merge dans les réglages GitHub
- [ ] CHANGELOG.md initialisé

**Critère de fin** : une pull request de test passe au vert, et
`flatpak run io.github.vertours.Rature` ouvre une fenêtre vide.

Détail commande par commande dans `docs/internal/CHANTIER-0.md`.

---

## Chantier 1 : logique métier

Écrire la logique métier dans `core/`, en anglais, d'après la spécification
de `SPECIFICATION.md`.

- [ ] `models.py` : dataclasses Task, ReserveItem, RecurringItem
- [ ] `session.py` : ajout, rayure, renommage, suppression, verrouillage
- [ ] `storage.py` : chemins XDG, écriture atomique, archivage
- [ ] `migrations.py` : socle de migration, sans migration à écrire
      pour l'instant, le format naît en version 1
- [ ] Tests couvrant chaque règle. Le socle de migration est testé à vide,
      aucune migration à écrire tant que le format reste en version 1

**Critère de fin** : `pytest --cov=rature.core --cov-fail-under=90` passe en CI, et
aucun fichier de `core/` n'importe `gi`.

---

## Chantier 2 : réserve et récurrentes

La réserve et les récurrentes, côté logique uniquement.

- [ ] Réserve : ajouter, renommer, supprimer, envoyer au jour
- [ ] Retour automatique en réserve des tâches non faites
- [ ] Récurrentes : modèles avec jours de la semaine
- [ ] Injection des récurrentes au passage du jour
- [ ] Détection du changement de date à l'ouverture
- [ ] Réserve et récurrentes présentes dès la version 1 du format,
      aucune migration à écrire
- [ ] Une tâche tirée de la réserve puis renommée y retourne renommée (`SPECIFICATION.md` §2.7.1)
- [ ] Une récurrente à `weekdays` vide est refusée par core (`SPECIFICATION.md` §2.7.2)
- [ ] Supprimer une tâche issue de la réserve ne la fait pas revenir (`SPECIFICATION.md` §2.7.3)
- [ ] Le passage du jour dédoublonne, l'ajout manuel en réserve non (`SPECIFICATION.md` §2.7.4)
- [ ] Une journée remplie à 01:00 est archivée sous la date de la veille (`SPECIFICATION.md` §2.7.5)
- [ ] Les horodatages stockés portent leur décalage horaire (`SPECIFICATION.md` §2.7.6)

**Critère de fin** : tous les cas de passage du jour sont testés, y compris
le passage de plusieurs jours d'un coup et le passage à cheval sur minuit.

---

## Chantier 3 : interface

Reconstruction en `.ui`, branchée sur un coeur déjà testé.

- [ ] Lecture des archives dans `core` : liste des dates, chargement d'une journée
- [ ] Fenêtre principale : `App` détenue par l'application, erreurs de démarrage, taille de fenêtre, navigation latérale
- [ ] Vue Jour en lecture seule : rayées en haut, en cours en dessous, numéros
      stables, bannière de quarantaine (`StartupOutcome.RECOVERED_FROM_CORRUPTION`,
      reportée depuis la PR de la fenêtre principale)
- [ ] Vue Jour en édition : ajouter, rayer, dérayer, renommer, supprimer, figer
- [ ] Réordonnancement des tâches par glisser-déposer à l'intérieur d'un bloc
- [ ] Vue Réserve, avec bouton d'envoi vers le jour
- [ ] Glisser-déposer de la réserve vers l'entrée Jour du panneau
- [ ] Vue Récurrentes, avec choix des jours
- [ ] Fenêtre d'archives
- [ ] Adaptation aux fenêtres étroites

**Critère de fin** : l'application couvre toute la spécification de
`SPECIFICATION.md`, §2 et §3, réserve et récurrentes comprises.

---

## Chantier 4 : confort et traductions

- [ ] Raccourcis clavier et fenêtre d'aide
- [ ] Ajout direct d'une tâche déjà rayée
- [ ] Annulation de la dernière suppression : restauration depuis le journal
      `deletions`, puis retrait de l'entrée
- [ ] Recherche dans les archives
- [ ] Export d'une journée en texte
- [ ] Traduction française complète. Cohérence de langue de bout en bout :
      les chaînes de l'interface, la date de l'en-tête et les noms de
      jours (`SPECIFICATION.md` §3.4) sont dans la même langue, jamais une
      traduction partielle. Cas à traiter : une machine dont `LC_MESSAGES`
      et `LC_TIME` divergent, où la date pourrait rester dans une autre
      langue que l'interface
- [ ] Fenêtre Statistiques, périmètre défini en `SPECIFICATION.md` §2.6

**Critère de fin** : `msgfmt --statistics` ne signale aucune chaîne non
traduite pour `fr`, aucune action fréquente n'est sans raccourci, et la
fenêtre Statistiques n'affiche aucune appréciation, seulement des nombres.

---

## Chantier 5 : publication

Flathub est écarté, voir `docs/adr/0001-reject-flathub.md`. Les exigences
de qualité qu'il imposait sont conservées : elles servaient la
maintenabilité autant que la conformité.

### 5.1 Qualité, inchangé

- [ ] Runtime GNOME à jour, jamais en fin de vie
- [ ] Captures d'écran
- [ ] metainfo complet : liens, description, couleur de marque, releases
- [ ] `appstreamcli validate` sans erreur
- [ ] `desktop-file-validate` sans erreur
- [ ] `flatpak-builder-lint` sans erreur, utile même hors Flathub
- [ ] README en anglais avec captures et instructions d'installation
- [ ] Release taguée sur GitHub, CHANGELOG à jour

### 5.2 Canal principal : dépôt Flatpak auto-hébergé

Un dépôt Flatpak statique publié sur GitHub Pages. C'est ce qui remplace
Flathub, et ça conserve les mises à jour automatiques.

- [ ] Générer une clé GPG de signature du dépôt, la sauvegarder hors
      machine, et stocker la partie privée en secret GitHub. Sans elle,
      plus aucune mise à jour publiable sur ce dépôt
- [ ] Construire et exporter le dépôt (`flatpak build-export`)
- [ ] Publier sur GitHub Pages via une action à chaque tag
- [ ] Fournir un fichier `.flatpakrepo` pour `flatpak remote-add`
- [ ] Documenter les deux commandes d'installation dans le README

L'utilisateur ajoute le dépôt une fois, puis reçoit les mises à jour comme
n'importe quelle application Flatpak.

### 5.3 Canal de secours : bundle en pièce jointe

- [ ] Générer un fichier `.flatpak` autonome (`flatpak build-bundle`)
- [ ] Le joindre à chaque release GitHub

Installation en une commande, sans mises à jour automatiques. Utile pour
essayer sans ajouter de dépôt.

AUR et COPR (paquets natifs, anciennement §5.4) ne conditionnent plus la
1.0 : décision du 8 septembre 2026, repoussés au chantier 6. Le `PKGBUILD`
écrit à ce stade vit dans `build-aux/aur/PKGBUILD`.

**Critère de fin** : l'application s'installe et se met à jour depuis le
dépôt auto-hébergé, et la publication d'une version reste automatisée.

---

## Chantier 6 : observabilité et finition

Rendre l'application diagnosticable avant d'y ajouter de la complexité.
Aucune fonctionnalité nouvelle pour l'utilisateur, en dehors d'une
correction.

- [ ] `logging` de la bibliothèque standard, un logger par module, aucune
      dépendance nouvelle
- [ ] Sortie vers stderr, donc lisible par `journalctl` sous Flatpak
- [ ] Niveau réglable par variable d'environnement, `INFO` par défaut
- [ ] Aucun texte de tâche ni de réserve dans les journaux au niveau par
      défaut. Ces textes sont des données personnelles. Les identifiants et
      les compteurs suffisent au diagnostic
- [ ] Points instrumentés au minimum : démarrage, chemin des données,
      passage du jour, archivage, échec d'écriture, migration appliquée
- [ ] Correction : le focus remonte et ne reste pas en place après un ajout
      en réserve
- [ ] README affiné, captures à jour, rendu plus attractif
- [ ] Logo revu
- [ ] Page statique de présentation du projet sur GitHub Pages, en plus du
      dépôt Flatpak déjà servi là
- [ ] Sponsoring : `FUNDING.yml` et mention dans le README

### Paquetage natif

Repoussé du chantier 5 (décision du 8 septembre 2026) : la 1.0 ne dépend
que du dépôt auto-hébergé et du bundle, pas des paquets natifs. Le
`PKGBUILD` écrit au chantier 5 vit déjà dans `build-aux/aur/PKGBUILD`.

Le chantier 6 prépare et vérifie les fichiers de paquetage ; la
soumission effective sur chaque plateforme est repoussée en v3/v4
(décision du 15 septembre 2026, voir « Repoussé volontairement ») : elle
demande un compte personnel de VertOurs par plateforme, que l'agent n'a
pas et ne doit pas créer à sa place.

- [ ] **AUR** (Arch) : `PKGBUILD` prêt dans `build-aux/aur/`, avec son
      `.SRCINFO`. Soumission repoussée en v3/v4
- [ ] **COPR** (Fedora) : `rature.spec` prêt dans `build-aux/copr/`,
      construction et `meson test` vérifiés en conteneur Fedora 44.
      Reconstruction automatique depuis le dépôt git à activer côté COPR
      au moment de la soumission. Soumission repoussée en v3/v4
- [ ] **Mageia** : `rature.spec` prêt dans `build-aux/mageia/`,
      construction et `meson test` vérifiés en conteneur Mageia 10.
      Soumission repoussée en v3/v4

Écartés volontairement : PPA Ubuntu, OBS, et les dépôts officiels Fedora ou
Debian, qui demandent parrainage, revue et un engagement de maintenance hors
de proportion pour une personne seule.

**Critère de fin** : `journalctl` montre le démarrage, le passage du jour
et un échec d'écriture provoqué ; aucun texte de tâche n'apparaît dans les
journaux au niveau par défaut ; le focus reste en place après un ajout en
réserve ; les fichiers de paquetage natif sont prêts et vérifiés, la
soumission effective repoussée en v3/v4.

---

## Chantier 7 : capture et réserve

Travail sur la réserve et la priorité. La capture depuis le téléphone,
prévue en 7.1, a été livrée puis retirée (voir ci-dessous).

La vue Jour n'est pas concernée. Les numéros, les rayées, le passage à
04:00, l'annulation de suppression et les archives restent locaux et
inchangés.

### 7.1 Boîte de dépôt (retirée)

Livrée dans `1.2.0` le 24 septembre 2026, retirée le 28 septembre 2026 sur
décision de VertOurs : le dépôt d'un fichier texte ne convient pas à
l'usage réel. Motifs et périmètre du retrait :
`docs/adr/0007-text-inbox.md`, section « Withdrawal ». La
synchronisation avec le téléphone passe dans « Repoussé volontairement ».

### 7.2 Réserve et priorité

- [x] Renvoi manuel d'une tâche du jour vers la réserve : méthode dans
      `core` et bouton (`SPECIFICATION.md` §2.5 et §3.2), le
      5 octobre 2026
- [x] Renvoi par glisser-déposer d'une tâche du jour vers l'entrée
      Reserve du panneau latéral, même méthode que le bouton
      (`SPECIFICATION.md` §3.2), le 5 octobre 2026
- [x] Réordonnancement manuel des items de la réserve, par
      glisser-déposer comme la vue Jour (`SPECIFICATION.md` §2.5 et
      §3.3), le 5 octobre 2026
- [x] Priorité : marqueur visuel seul, aucun effet sur l'ordre d'affichage
      ni sur les numéros. S'applique aux tâches du jour et aux items de
      réserve (`SPECIFICATION.md` §2.5, §2.7.8, §3.2 et §3.3), le
      12 octobre 2026
- [x] Migration de format pour le champ de priorité, version 2 → 3. La
      première migration réelle (1 → 2) est celle de la récurrente une
      semaine sur deux, ci-dessous. Le 12 octobre 2026

**Critère de fin** : la priorité n'a aucun effet sur l'ordre ; la
migration s'applique sans perte sur un fichier de version antérieure.

### Hors cases prévues : récurrente une semaine sur deux

Ajoutée le 12 octobre 2026 sur décision de VertOurs, en dehors du cadrage
initial du chantier 7. Besoin réel : deux activités toujours en semaine A,
deux autres toujours en semaine B. Décisions et règle de parité :
`SPECIFICATION.md` §2.5, §2.7.7 et §3.4.

- [x] `RecurringItem.every_other_week_from` (lundi d'une semaine active,
      `null` pour chaque semaine) et règle de parité dans `recurrence.py`,
      lundi calculé dans `core` à partir de la date de référence, le
      12 octobre 2026
- [x] Format de données version 2, migration 1 → 2 testée sur un fichier
      principal et une archive de version 1, le 12 octobre 2026
- [x] Formulaire et sous-titre de la vue Récurrentes (`SPECIFICATION.md`
      §3.4), chaînes traduites, le 12 octobre 2026

**Critère de fin** : sur quatre semaines consécutives incluant le passage
de 2026 à 2027, chaque semaine n'injecte que la paire attendue, jamais les
deux, jamais aucune ; un fichier de version 1 migre sans perte et ses
récurrentes hebdomadaires s'injectent comme avant.

### 7.3 Préparer le lendemain

Besoin confirmé à l'usage (retour du 8 septembre 2026, après une semaine
sur `0.10.1`) : pouvoir préparer la liste du jour suivant avant le
passage de 04:00. Ce n'est pas un simple ajout : `SPECIFICATION.md` §2.5
ne connaît aujourd'hui qu'une seule journée active, et `CLAUDE.md` pose
« sans planification » comme principe fondateur du projet (§1).

- [x] Session de cadrage dédiée avant tout code, tenue avec VertOurs le
      12 octobre 2026 : une vue Demain, liste séparée de la journée et de
      la réserve, qui devient la liste du prochain jour qui démarre.
      Décaler une tâche du jour vers Demain : oui, geste explicite.
      Paramètre de report automatique : non, voir « Repoussé
      volontairement »
- [x] ADR documentant la décision et son articulation avec §2.5 :
      `docs/adr/0008-prepare-tomorrow.md`, le 12 octobre 2026
- [x] `SPECIFICATION.md` mis à jour avant l'implémentation, pas après :
      seize points de détail validés le 12 octobre 2026, reportés le
      25 octobre 2026 (§2.5 bloc Demain et étape 7, §2.7.9, §3.16)
- [x] `core` : liste Demain (ajout, renommage, réordonnancement,
      suppression, priorité, tirage depuis la réserve), décalage d'une
      tâche du jour vers Demain et retour de Demain vers le jour, étape 7
      du passage du jour, récurrentes dues affichées. PR #162 et #163, le
      25 octobre 2026
- [x] Format de données version 4, migration 3 → 4 testée sur des
      fichiers v3 principal et archive, et chaîne depuis v1. PR #161, le
      25 octobre 2026
- [x] Vue Demain dans le panneau latéral, entrées de menu et
      glisser-déposer « Move to tomorrow » (jour et réserve) et « Move to
      today », raccourcis `Ctrl+1` à `Ctrl+4` dans l'ordre du panneau,
      chaînes traduites. PR #164 et #165, contrôlées visuellement par
      VertOurs le 25 octobre 2026

**Critère de fin** : une liste préparée devient la liste du jour au
passage suivant, après les récurrentes et dans son ordre, même après
plusieurs jours sans ouverture ; rien n'est perdu ; aucune tâche de Demain
ne porte de numéro avant d'entrer dans une journée.

**Ne commence pas avant que la spec ci-dessus soit validée.** L'abandon du
POC (ADR 0004) vient exactement du scénario inverse : une fonctionnalité
codée avant que la spec ne la décrive.

---

## Chantier 8 : confort et langues

- [x] Fenêtre Statistiques rafraîchie pendant qu'elle est ouverte, sans
      avoir à la refermer. PR #171, le 25 octobre 2026
- Fenêtre Archives rafraîchie de la même façon : relevée au cadrage de
  8.3 le 25 octobre 2026, hors critère de fin. Passe au chantier 9 le
  30 octobre 2026
- [x] Catalogues `es`, `de`, `pt_BR`, `ru`, `eo`. PR #174 à #178, le
      29 octobre 2026
- [x] Date de la barre latérale des Archives traduisible comme la date
      longue : `%d %B %Y` donne « 05 octubre 2026 » en espagnol, au
      lieu de « 5 de octubre de 2026 ». Relevé au contrôle visuel de
      `es` le 29 octobre 2026, hors critère de fin. Fait avant `2.0.0`,
      à la revue de code du 29 octobre 2026
- [x] Job CI de traduction :
      `msgfmt --check --check-format --check-header`. Déjà couvert par
      `tests/test_translations.py`, lancé en CI dans le job `test` sur
      chaque catalogue de `po/LINGUAS` : `--check` inclut les deux autres
      options. Constaté le 25 octobre 2026, aucun job séparé
- [x] Les traductions produites par machine sont signalées comme telles dans
      l'en-tête du `.po` concerné. Transparence sur l'origine, pas de
      traducteur humain attribué à tort. Le 29 octobre 2026
- [x] Nom accessible (`accessibility` / `label`) sur chaque bouton à icône
      seule des lignes et des en-têtes : aujourd'hui seule l'infobulle les
      décrit. Relevé à la revue de code du 5 octobre 2026. PR #170, le
      25 octobre 2026

**Critère de fin** : `msgfmt --statistics` ne signale aucune chaîne non
traduite pour chaque catalogue livré, le job CI de traduction est vert, et
la fenêtre Statistiques se met à jour sans être refermée.

---

## Chantier 9 : propreté et solidité

Issu de la revue du 30 octobre 2026. Peu visible pour l'utilisateur :
protéger ses données, durcir la chaîne de publication, préparer le code
aux chantiers 10 et 11. Deux nouveaux outils de CI validés par VertOurs
le 30 octobre 2026 (`CLAUDE.md` §4 règle 6) : `mypy` et `gtk4-broadwayd`.

### Données

- [x] Sauvegarde avant migration : quand le chargement applique au moins
      une migration, copier `data.json` en `data.json.v<N>.bak` avant la
      première écriture, une seule fois. `SPECIFICATION.md` mis à jour
      avant le code
- [x] `OSError` au démarrage (permission, disque plein, quarantaine
      impossible) : `Gtk.AlertDialog` puis fermeture, sur le modèle de
      `FutureVersionError`. Quatrième cas ajouté à `SPECIFICATION.md` §3.6
- [x] Fenêtre Archives rafraîchie au passage du jour : ouverte pendant le
      passage, elle ne montre pas la journée qui vient d'être archivée.
      Reste du chantier 8. `SPECIFICATION.md` §3.5 mis à jour, le
      30 octobre 2026

### Sécurité

- [x] `release.yml` : refuser, avant le build, toute entrée qui n'est pas
      un tag existant au format `vX.Y.Z`
- [x] `SECURITY.md` : contact, délai de réponse, versions supportées
- [x] Dépendances de développement en versions exactes, écosystème `pip`
      dans `dependabot.yml`
- [x] Règles ruff `S` (bandit) activées ; l'`assert` de
      `recurring_form.py` devient un `if`/`raise`

### Propreté

- [x] Provenance réserve regroupée en un seul champ optionnel dans `Task`
      et `PreparedTask`. Sérialisation inchangée, donc aucune migration.
      `ReserveSource`, étendu à `Deletion` ; l'invariant « source si et
      seulement si `origin` vaut `reserve` », déjà écrit dans
      `ARCHITECTURE.md`, est désormais vérifié dans les deux sens. Le
      30 octobre 2026
- [x] `mypy --strict` sur `rature.core` en CI, vert. mypy `2.4.1` épinglé,
      lancé dans le job `lint`, configuration dans `pyproject.toml`. Le
      30 octobre 2026
- [x] Renvois « ADR 0007 addendum » corrigés en ADR 0003 (`storage.py`
      trois fois, `app.py` une fois)
- [x] Commentaires périmés : `models.py` (« milestone 4's undo »),
      manifeste Flatpak (« one translation »)
- [x] `window._perform` : `_logger.exception` au lieu de
      `traceback.print_exc`
- [x] Booléens positionnels passés en paramètres nommés (`set_priority`
      et voisins)

### Maintenabilité

- [x] Tests d'interface réels sous `gtk4-broadwayd` en CI, sortis de
      « Repoussé volontairement » : au moins ajouter, rayer, renommer, et
      le glisser-déposer dans le jour et la réserve. Infrastructure et
      premier test (ajouter) faits le 30 octobre 2026 : job CI `ui`,
      `build-aux/ui-tests.sh` dans le SDK GNOME 51, `tests/ui/`. Rayer,
      dérayer, renommer et le glisser-déposer (jour et réserve) le même
      jour : broadway ne synthétise pas de geste de pointeur, le test joue
      le `drag-begin` puis émet le vrai signal `drop` de la ligne cible
- [ ] Ensuite seulement : base commune aux lignes `task_row`,
      `reserve_row` et `prepared_row` (glisser-déposer, renommage,
      priorité, suppression). Les différences voulues (`COPY` pour la
      réserve) restent explicites
- [x] `sha256` du `PKGBUILD` et du `.SRCINFO` calculée dans `release.yml`
      après le tag : plus de commit de rattrapage. Les copies du dépôt
      gardent `SKIP` (l'archive d'un tag ne peut contenir sa propre
      somme), les copies remplies sont jointes à la release
      (`rature-aur.tar.gz`). Le 30 octobre 2026

### Vitrine

- [ ] README : « Status » en deux lignes ; nouvelle section
      « Engineering » (séparation `core`/`ui` testée, couverture 100 % sur
      `core`, écritures atomiques avec `fsync`, format versionné et
      migrations testées, dépôt Flatpak signé, CI épinglée, commits
      signés, lien vers les ADR) ; `pytest --cov` dans « Run the checks »
- [x] Langue des ADR : traduites en anglais, fichiers renommés, décision
      de VertOurs le 30 octobre 2026
- [ ] `STATE.md` déplacé dans `docs/internal/`, renvois mis à jour
      (`CLAUDE.md`, `CONTRIBUTING.md`, `ROADMAP.md`)
- [ ] En-tête du CHANGELOG aligné sur `CONTRIBUTING.md` (versions
      majeures pilotées par la roadmap)
- [ ] Captures d'écran Demain et Réserve (VertOurs)

Au fil de l'eau, hors critère : élaguer les docstrings longues quand on
touche un fichier ; découper `Session` si le chantier 10 la fait trop
grossir.

À la charge de VertOurs, hors dépôt : secret `FLATPAK_GPG_PRIVATE_KEY`
dans l'environnement `release`, limité aux tags `v*` ; CodeQL en
configuration par défaut.

**Critère de fin** : un fichier migré laisse sa sauvegarde ; un dossier de
données illisible au démarrage affiche une alerte au lieu de fermer
l'application ; `mypy --strict` et les tests `gtk4-broadwayd` sont verts
en CI ; la release suivante ne demande aucun commit de rattrapage.

---

## Chantier 10 : synchronisation entre appareils

Décisions déjà prises le 30 octobre 2026 :

- Pas de moteur de fusion, pas de verrou exclusif (un téléphone reste
  ouvert en permanence)
- Avant chaque écriture, relire le fichier ; s'il a changé, recharger puis
  rejouer le geste sur les données fraîches
- Le téléphone (chantier 11) est le cas de référence, pas un ajout tardif

- [ ] Session de cadrage avec VertOurs avant tout code, puis ADR 0009.
      Questions à trancher :
      - outil de synchronisation (Syncthing pressenti) ;
      - choix du dossier par le portail, sans nouvelle permission (retour
        d'expérience de l'ADR 0007) ;
      - fichiers de conflit de l'outil de synchronisation ;
      - passage du jour à 04:00 sur deux appareils ;
      - archives synchronisées ou non ;
      - quarantaine dans un dossier synchronisé (ne jamais écrire une
        journée vide par-dessus des données en cours de synchronisation) ;
      - validation des types au chargement
- [ ] `SPECIFICATION.md` mis à jour avant l'implémentation
- [ ] Implémentation, découpée au cadrage

**Critère de fin** : deux machines de bureau sur le même dossier, gestes
alternés et quasi simultanés pendant une semaine d'usage réel. Rien de
perdu, aucune écriture sans relecture préalable, chaque conflit signalé.

---

## Chantier 11 : compagnon Android, Jour et Réserve

- [ ] ADR 0010 : réouverture de « Application Android dédiée » et
      « Version mobile » sous une forme limitée. Argument : le même
      `rature.core` (Python pur, sans `gi`) plus une interface légère, pas
      une deuxième base
- [ ] Prototype jetable avant tout : un écran qui lit une copie de
      `data.json`, ajoute et raye, en APK installé sur le téléphone de
      VertOurs. Il valide `core` sur Android, les formats de date (`%-d`
      est une extension GNU), l'outil (Flet ou BeeWare) et la taille de
      l'APK
- [ ] Périmètre : vues Jour et Réserve. Hors périmètre : Demain, édition
      des récurrentes, archives, statistiques, glisser-déposer
- [ ] Même dépôt que le bureau, `core` partagé sans duplication
- [ ] APK joint aux releases

**Critère de fin** : une semaine d'usage réel, téléphone et bureau sur les
mêmes données, sans perte.

---

## Après publication

- Suivre les fins de vie de runtime, une migration par an environ
- Publier les correctifs avec un tag et une entrée de CHANGELOG
- Traiter les issues, ou les fermer honnêtement si hors périmètre

---

## Repoussé volontairement

Noté ici pour ne pas y penser pendant les chantiers.

- **Dictée vocale.** Écartée. Demanderait un moteur local, whisper.cpp ou
  vosk, et alourdirait fortement le paquet. Non utilisée en pratique par
  l'auteur. À réévaluer seulement si le manque se fait sentir à l'usage.
- **Synchronisation avec Todoist ou un autre service tiers.** Abandonnée
  le 30 octobre 2026 : dépendance externe, et le besoin est couvert par le
  compagnon Android du chantier 11.
- **Étiquettes temporelles ou catégories** (« cet après-midi », « à faire
  après »). Abandonnée le 8 septembre 2026 : ce sont des catégories, que
  la méthode exclut par construction (`CLAUDE.md` §1) et que
  `SPECIFICATION.md` §2.3 interdit (« pas de tri automatique, pas de
  priorisation implicite »). À revoir seulement si le besoin ressurgit.
- **Agenda à la semaine ou au mois.** Candidate, hors v3 (30 octobre
  2026). Écartée au cadrage de 7.3 le 12 octobre 2026
  (`docs/adr/0008-prepare-tomorrow.md`) : des tâches datées sont la planification que `CLAUDE.md` §1 exclut, et
  montrent des retards par construction. La vue Demain couvre le besoin
  exprimé ; à revoir seulement si elle ne suffit pas.
- **Paramètre de report automatique des tâches non rayées vers Demain.**
  Abandonné le 29 octobre 2026, par décision de VertOurs, sans attendre la
  réévaluation prévue le 12 octobre (`docs/adr/0008-prepare-tomorrow.md`,
  addendum). Le report reste un geste explicite ; une tâche non rayée suit
  toujours le passage du jour de `SPECIFICATION.md` §2.5.
- **Statistiques de suivi sur les récurrentes.** Abandonnée le
  8 septembre 2026, le temps de voir si le besoin persiste ; sinon
  candidate, hors v3 (30 octobre 2026). Si le besoin ressurgit,
  attention : un suivi de régularité frôle la série de jours consécutifs que `SPECIFICATION.md`
  §2.3 interdit explicitement.
- **Mettre une récurrente en pause sans la supprimer.** Candidate,
  relevée le 12 octobre 2026 : pendant les vacances scolaires, une
  activité s'arrête puis reprend. Aujourd'hui il faut la supprimer puis
  la recréer, ou décocher tous ses jours, ce que `SPECIFICATION.md`
  §2.7.2 interdit ; le besoin rejoint le motif de ce cas tranché (une
  désactivation ne doit jamais passer par une liste de jours vide). Non
  retenue au cadrage de la priorité (7.2), ni en v3 (30 octobre 2026) ;
  demanderait sa propre migration de format 4 → 5. Rien de codé.
- **Version mobile complète de l'application.** Écartée le 24 août 2026,
  confirmé le 30 octobre 2026 : le chantier 11 n'ouvre qu'un compagnon
  limité aux vues Jour et Réserve, sur le même `core`. Le coût d'une
  version complète est dans la maintenance de deux interfaces à vie, pour
  une personne seule.
- **Soumission effective des paquets AUR, COPR et Mageia.** Repoussée en
  v3/v4 le 15 septembre 2026 : chaque plateforme demande un compte
  personnel de VertOurs (AUR : compte et clé SSH ; COPR : compte Fedora ;
  Mageia : processus propre au dépôt communautaire), que l'agent n'a pas et
  ne doit pas créer à sa place. Le chantier 6 prépare et vérifie les
  fichiers : `PKGBUILD` et les `.spec` COPR/Mageia suivent la version du
  projet (`1.1.0` à la clôture du chantier), constructions validées en
  conteneur (Arch, Fedora, Mageia) le 15 septembre 2026
  (`build-aux/aur/PKGBUILD`, `.SRCINFO`, `build-aux/copr/rature.spec`,
  `build-aux/mageia/rature.spec`).

Note : l'entrée « Traduction espéranto », auparavant repoussée, entre au
chantier 8 et sort donc de cette section. L'entrée « capture depuis le
téléphone », entrée au chantier 7 le 24 août 2026 sous la forme d'une boîte
de dépôt texte, y revient le 28 septembre 2026 après le retrait de
celle-ci.

Sorties le 30 octobre 2026, à la planification de la v3 :
« Synchronisation de la journée en cours entre machines » entre au
chantier 10 ; « Application Android dédiée », « Version mobile » et
« Capture depuis le téléphone » entrent au chantier 11 sous la forme du
compagnon (une version mobile complète reste écartée, ci-dessus) ;
« Tests d'interface réels sous `gtk4-broadwayd` en CI » entrent au
chantier 9.
