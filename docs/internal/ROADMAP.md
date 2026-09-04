# Roadmap

Cette roadmap décrit la construction, à partir de la spécification. Le POC
est abandonné, voir `docs/adr/0004-abandon-du-poc.md`.

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
| 5 | Publication : dépôt auto-hébergé, AUR, COPR | Oui |

### Version 2

| Chantier | Objet | Visible pour l'utilisateur |
|---|---|---|
| 6 | Observabilité et finition | Peu |
| 7 | Capture et réserve | Oui, beaucoup |
| 8 | Confort et langues | Oui |

`0.9.x` correspond aux chantiers 0 à 4 terminés : fonctionnellement
complet, non publié. `1.0.0` correspond aux chantiers 0 à 5 tous
terminés : l'application est installable et se met à jour depuis le
dépôt auto-hébergé. C'est la clôture de la v1.

`2.0.0` correspond aux chantiers 6, 7 et 8 tous terminés, chacun avec
son critère de fin atteint. C'est la v2. Les versions `1.x`
intermédiaires suivent les règles d'incrément de `CONTRIBUTING.md`.

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

Flathub est écarté, voir `docs/adr/0001-rejet-de-flathub.md`. Les exigences
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

### 5.4 Paquets natifs

- [ ] **AUR** (Arch) : un PKGBUILD, publication immédiate, sans revue
- [ ] **COPR** (Fedora) : un fichier .spec, reconstruction automatique depuis
      le dépôt git

Écartés volontairement : PPA Ubuntu, OBS, et les dépôts officiels Fedora ou
Debian, qui demandent parrainage, revue et un engagement de maintenance hors
de proportion pour une personne seule.

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
- [ ] README affiné, captures à jour

**Critère de fin** : `journalctl` montre le démarrage, le passage du jour
et un échec d'écriture provoqué ; aucun texte de tâche n'apparaît dans les
journaux au niveau par défaut ; le focus reste en place après un ajout en
réserve.

---

## Chantier 7 : capture et réserve

La capture depuis le téléphone revient, sans application dédiée, sans
réseau et sans compte tiers : un fichier texte déposé dans un dossier
synchronisé.

La vue Jour n'est pas concernée. Les numéros, les rayées, le passage à
04:00, l'annulation de suppression et les archives restent locaux et
inchangés.

### 7.1 Boîte de dépôt

- [ ] ADR 0007 : boîte de dépôt texte, écrite avant le code
- [ ] Dossier surveillé choisi par l'utilisateur via le portail de fichiers,
      mémorisé dans GSettings. Aucune permission large ajoutée au manifeste
- [ ] Lecture au démarrage, puis à chaque retour de focus de la fenêtre.
      Pas de surveillance continue
- [ ] Format : une tâche par ligne, lignes vides ignorées, aucune syntaxe
- [ ] Un fichier importé est déplacé dans un sous-dossier `traité/`, jamais
      supprimé
- [ ] Aucun dédoublonnage à l'import, conformément à `SPECIFICATION.md`
      §2.7.4 qui ne dédoublonne qu'au passage du jour
- [ ] Fichier illisible ou mal encodé : rien n'est importé, le fichier reste
      en place, une bannière prévient. Réutilise le motif de quarantaine déjà
      en place pour `data.json`
- [ ] Chaque source de capture écrit son propre fichier
      (`inbox-<machine>-<horodatage>.txt`), donc jamais deux écrivains sur un
      même fichier

### 7.2 Réserve et priorité

- [ ] Renvoi manuel d'une tâche du jour vers la réserve : méthode dans
      `core`, bouton, glisser-déposer
- [ ] Priorité : marqueur visuel seul, aucun effet sur l'ordre d'affichage
      ni sur les numéros. S'applique aux tâches du jour et aux items de
      réserve
- [ ] Migration de format pour le champ de priorité. Première utilisation
      réelle du socle `migrations.py` posé au chantier 1

**Critère de fin** : un fichier texte déposé depuis un téléphone via un
dossier synchronisé apparaît en réserve au retour de focus, et se retrouve
dans `traité/` ; un fichier illisible ne fait perdre aucune tâche et
déclenche la bannière ; la priorité n'a aucun effet sur l'ordre ; la
migration s'applique sans perte sur un fichier de version antérieure.

---

## Chantier 8 : confort et langues

- [ ] Fenêtre Statistiques rafraîchie pendant qu'elle est ouverte, sans
      avoir à la refermer
- [ ] Catalogues `es`, `de`, `pt_BR`, `ru`, `eo`
- [ ] Job CI de traduction :
      `msgfmt --check --check-format --check-header`
- [ ] Les traductions produites par machine sont signalées comme telles dans
      l'en-tête du `.po` concerné. Transparence sur l'origine, pas de
      traducteur humain attribué à tort

**Critère de fin** : `msgfmt --statistics` ne signale aucune chaîne non
traduite pour chaque catalogue livré, le job CI de traduction est vert, et
la fenêtre Statistiques se met à jour sans être refermée.

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
- **Synchronisation de la journée en cours entre machines.** Écartée. Elle
  imposerait un moteur de fusion dans `core/`, avec des conflits sur le
  compteur de numéros, le verrouillage et le passage du jour. La réserve,
  qui est la partie durable des données, est traitée au chantier 7.
- **Synchronisation avec Todoist ou un autre service tiers.** Écartée au
  profit de la boîte de dépôt texte du chantier 7, qui couvre le même besoin
  sans réseau, sans jeton et sans compte. À réévaluer seulement si la boîte
  de dépôt se révèle insuffisante à l'usage.
- **Application Android dédiée.** Écartée. Le coût n'est pas dans le code
  mais dans la maintenance de deux bases à vie, pour une personne seule.
  La capture depuis le téléphone est traitée au chantier 7 par n'importe
  quelle application de notes capable d'écrire dans un dossier synchronisé.
- **Version mobile de l'application.** Écartée le 24 août 2026. Le projet
  reste une application de bureau.

Note : l'entrée « Traduction espéranto », auparavant repoussée, entre au
chantier 8 et sort donc de cette section. L'entrée « capture depuis le
téléphone », auparavant regroupée avec « version mobile » et repoussée le
24 août 2026, entre au chantier 7 sous la forme d'une boîte de dépôt texte
et sort donc, elle aussi, de cette section.
