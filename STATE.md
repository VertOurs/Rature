# État courant

STATE.md décrit l'état courant, pas l'historique. Un chantier terminé se
condense en trois lignes. Ce qui est durable part dans un ADR ou dans
`docs/ARCHITECTURE.md` ; ce qui est historique est déjà dans git.

## Avancement

- **Chantier en cours** : 5, publication. **`0.10.0` est publiée**
  (2026-09-03, sur `//50`) : quatre sources de version, `CHANGELOG` et
  metainfo `<release>` à jour, tag `v0.10.0` annoté et signé sur le
  commit de merge de la PR #93, release GitHub « nue » (tarball source).
  Le canal de distribution (§5.2 dépôt auto-hébergé + §5.3 bundle) est
  posé en CI, à valider par un `workflow_dispatch` sur `v0.10.0`.
- **Décisions du chantier 5** (`CLAUDE.md` §3) : mention de l'assistance IA
  = une ligne factuelle dans le README ; `ARCHITECTURE.md` traduit en
  anglais, publié dans `docs/`, version interne française retirée ; bump
  runtime vers GNOME 51.
- **`0.10.0` sort sur `//50`.** Décision du 3 septembre 2026 : ne pas
  bloquer la release sur GNOME 51. `//50` passe EOL vers le 16/09 ; le
  bump `//51` est fait ensuite, dès que l'image CI
  `ghcr.io/flathub-infra/flatpak-github-actions:gnome-51` existe (elle
  renvoie 404 au 3/09), et livré en `0.10.1`.
- **Fait au chantier 5** : décisions figées (`CLAUDE.md` §3),
  `ARCHITECTURE.md` traduit et publié dans `docs/ARCHITECTURE.md`
  (rafraîchi, version interne retirée), README réécrit avec la ligne IA,
  metainfo complété (`<branding>`, `<url type="contribute">`, description,
  `<screenshots>` + 4 captures dans `data/screenshots/`),
  `flatpak-builder-lint` manifeste **et** dépôt en CI (deux erreurs
  Flathub-only filtrées, `build-aux/flatpak/repo_lint.py`), `0.10.0`
  coupée, taguée et publiée.
- **§5.2 + §5.3, dépôt Flatpak auto-hébergé** : clé GPG dédiée à la
  signature du dépôt (FPR `C2CBB256D91B01B920B0BE3898280657575FC9DA`,
  ≠ clé de commit), publique dans `build-aux/flatpak/repo-signing-key.gpg`
  et dans le `.flatpakrepo`, privée dans le secret Actions
  `FLATPAK_GPG_PRIVATE_KEY`. GitHub Pages activé en mode `workflow`.
  `.github/workflows/release.yml` (sur tag `v*` ou `workflow_dispatch`) :
  build + bundle `.flatpak` signés, `build-update-repo` avec deltas
  statiques, publication de `repo/` + `.flatpakrepo` + clé + `index.html`
  sur Pages (`https://vertours.github.io/Rature/`), bundle joint à la
  release. À valider : un `workflow_dispatch` sur `v0.10.0`, puis un
  `flatpak remote-add` + `install` depuis une machine propre (hors agent,
  `CLAUDE.md` §6).
- **Étape suivante**, chantier 5 (`docs/internal/ROADMAP.md` §5), sur
  `//50` :
  1. Valider le pipeline `release.yml` (voir ci-dessus).
  2. §5.4 AUR (PKGBUILD) + COPR (.spec).
  3. Bump `//51` → `0.10.1` dès l'image CI `gnome-51` disponible.
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

Revérifiées le 29 août 2026, à revérifier avant toute mise à jour du
manifeste (`CLAUDE.md` §4 règle 8).

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//50` | Jusqu'à `0.10.0` incluse. GNOME 51 sort le 16 septembre 2026 ; bump `//51` en `0.10.1` dès l'image CI `gnome-51` disponible |
| Python cible | 3.13 | Celui du runtime 50, pas le 3.14 de la machine |
| Version du projet | `0.10.0` | Chantier 4 (confort + traduction FR) publié, sur `//50`. Coupée le 3 septembre 2026 |
| Meson minimal | 1.9 | Version de `org.gnome.Sdk//50`, pas celle de la machine (1.11) |

`0.10.0` (3 septembre 2026) publie les sept fonctionnalités du chantier 4
(annulation de la dernière suppression, ajout d'une tâche déjà rayée,
raccourcis clavier et fenêtre d'aide, export d'une journée en texte,
recherche dans les archives, fenêtre Statistiques, traduction française
complète) plus le correctif du fichier JSON non-objet. `[Unreleased]` est
vide ; l'incrément suivant sera `0.10.1`, le bump `//51`.

**Bump vers GNOME 51** : après la sortie stable (16 septembre 2026) et la
publication de l'image CI `gnome-51`. Touche le manifeste, la CI et la
table ci-dessus. Livré en `0.10.1`, `0.10.0` restant sur `//50`.

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
