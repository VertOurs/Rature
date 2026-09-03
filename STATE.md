# État courant

STATE.md décrit l'état courant, pas l'historique. Un chantier terminé se
condense en trois lignes. Ce qui est durable part dans un ADR ou dans
`docs/internal/ARCHITECTURE.md` ; ce qui est historique est déjà dans git.

## Avancement

- **Chantier en cours** : 5, publication. Le chantier 4 est terminé (voir
  « Chantiers terminés ») ; `[Unreleased]` dans `CHANGELOG.md` est prêt
  pour une release `0.10.0`, à couper par l'auteur.
- **Décisions du chantier 5** (`CLAUDE.md` §3) : mention de l'assistance IA
  = une ligne factuelle dans le README ; `ARCHITECTURE.md` traduit en
  anglais, publié dans `docs/`, version interne française retirée ; bump
  runtime vers GNOME 51.
- **Bump `//51` bloqué par l'amont** jusqu'au ~16 septembre 2026 : l'image
  CI `ghcr.io/flathub-infra/flatpak-github-actions:gnome-51` renvoie 404
  et le runtime `//51` stable n'est pas encore sur `flathub` (51 est en
  RC, stable le 16/09). `//50` reste la stable courante, non EOL, d'ici
  là. Vérifié le 3 septembre 2026.
- **Étape suivante**, chantier 5 (`docs/internal/ROADMAP.md` §5), sur
  `//50` :
  1. Traduire `ARCHITECTURE.md` en anglais → `docs/ARCHITECTURE.md`,
     retirer `docs/internal/ARCHITECTURE.md`, corriger tous les renvois.
  2. Qualité §5.1 : README anglais (ligne IA, install), metainfo complet
     (`<url>`, `<branding>`, `<releases>`, `<screenshots>`), captures,
     `flatpak-builder-lint` en CI.
  3. Dès que l'image `gnome-51` existe : bump `//50` → `//51` (manifeste,
     CI, table « Versions retenues »).
  4. Couper `0.10.0` (version Meson, CHANGELOG, tag signé) — après le
     bump —, puis §5.2 dépôt Flatpak auto-hébergé.
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

## Versions retenues

Revérifiées le 29 août 2026, à revérifier avant toute mise à jour du
manifeste (`CLAUDE.md` §4 règle 8).

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//50` | Stable courante. GNOME 51 sort le 16 septembre 2026, la 50 passe alors en fin de vie |
| Python cible | 3.13 | Celui du runtime 50, pas le 3.14 de la machine |
| Version du projet | `0.9.0` | Adaptation aux fenêtres étroites ; complète le chantier 3 |
| Meson minimal | 1.9 | Version de `org.gnome.Sdk//50`, pas celle de la machine (1.11) |

`[Unreleased]` dans `CHANGELOG.md` accumule sept fonctionnalités
(annulation de la dernière suppression, ajout d'une tâche déjà rayée,
raccourcis clavier et fenêtre d'aide, export d'une journée en texte,
recherche dans les archives, fenêtre Statistiques, traduction française
complète) et deux correctifs (PR #44, plantage au démarrage ; PR #46,
titre d'en-tête). Le chantier 4 est complet ; une fonctionnalité impose
un incrément **mineur** : la prochaine release sera `0.10.0`.

**Bump vers GNOME 51 à partir du 16 septembre 2026** : manifeste, CI,
`STATE.md`. Rien de publié d'ici là, donc pas d'urgence.

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
