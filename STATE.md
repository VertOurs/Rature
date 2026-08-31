# État courant

STATE.md décrit l'état courant, pas l'historique. Un chantier terminé se
condense en trois lignes. Ce qui est durable part dans un ADR ou dans
`docs/internal/ARCHITECTURE.md` ; ce qui est historique est déjà dans git.

## Avancement

- **Chantier en cours** : 3, interface reconstruite en `.ui`
- **Étape suivante** : fenêtre principale avec navigation latérale, puis
  vue Jour (rayées en haut, en cours en dessous). Découpage complet dans
  `docs/internal/ROADMAP.md`.
- **Mode de travail** : agent dans l'IDE, PyCharm

## Dépôt

- `github.com/VertOurs/Rature`, public. `main` protégée : PR obligatoire,
  squash seul, historique linéaire.
- Signature GPG active : clé ed25519
  `25DA27801D5F4ECA1DAA2101E89227EAC418BC4A`, `commit.gpgsign` local.
- « Require status checks » actif dans le ruleset `main` : `lint`, `test`,
  `meson`, `flatpak`, mode strict, aucun contournement possible même par un
  admin. Vérifié le 31 août 2026 via `gh api repos/.../rulesets`.
- **Ouvert, côté VertOurs** :
  - ajouter la clé GPG publique à GitHub pour la mention « Verified »
  - supprimer le dossier local `review/` (dans `.gitignore`)

## Versions retenues

Revérifiées le 29 août 2026, à revérifier avant toute mise à jour du
manifeste (`CLAUDE.md` §4 règle 8).

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//50` | Stable courante. GNOME 51 sort le 16 septembre 2026, la 50 passe alors en fin de vie |
| Python cible | 3.13 | Celui du runtime 50, pas le 3.14 de la machine |
| Version du projet | `0.2.0` | Cœur métier et couche `App` complets, toujours sans interface |
| Meson minimal | 1.9 | Version de `org.gnome.Sdk//50`, pas celle de la machine (1.11) |

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

## Documents

Cadrage relu, contradictions résolues, six cas limites tranchés en
`SPECIFICATION.md` §2.7 le 25 août 2026.
