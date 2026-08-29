# État courant

Mis à jour en fin de chaque session. Le cadrage stable est dans `CLAUDE.md`.

## Avancement

- **Chantier en cours** : 1, logique métier
- **Étape suivante** : `core/models.py`, dataclasses Task, ReserveItem,
  RecurringItem
- **Cible `0.9.x`** : chantiers 0 à 4 terminés, non publié
- **Cible `1.0.0`** : chantier 5 terminé, publié sur le dépôt auto-hébergé
- **Mode de travail** : agent dans l'IDE, PyCharm
- **POC** : abandonné, aucune donnée à reprendre

## Dépôt

- `github.com/VertOurs/Rature`, public
- Branche `main` protégée, pull request obligatoire, poussée directe interdite
- Fusion en squash uniquement, merge commit et rebase désactivés
- `main` : deux commits, `1356198` (exception fondatrice) puis `6408dcd`
  (chantier 0, squash de la PR #1)
- Signature GPG active : clé ed25519
  `25DA27801D5F4ECA1DAA2101E89227EAC418BC4A`,
  `git config --local commit.gpgsign true`. Clé publique à ajouter à GitHub
  pour la mention « Verified » sur les futurs commits
- **Ouvert, côté VertOurs** : activer « Require status checks » dans le
  ruleset `main`, jobs `lint`, `test`, `meson`, `flatpak`, maintenant que la
  CI existe

## Versions retenues

Revérifiées le 29 août 2026, à revérifier avant toute mise à jour du
manifeste, conformément à `CLAUDE.md` §4 règle 8.

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//50` | Stable courante. GNOME 51 sort le 16 septembre 2026, la 50 passe alors en fin de vie |
| Python cible | 3.13 | Celui du runtime 50, et non le 3.14 de la machine de développement |
| Version du projet | `0.1.0` | Premier jalon, rien de publiable |
| Meson minimal | 1.9 | Version fournie par `org.gnome.Sdk//50`, pas celle de la machine (1.11) |

**Bump vers GNOME 51 à faire à partir du 16 septembre 2026** : manifeste,
CI, `STATE.md`. Le chantier 0 ne publie rien, donc pas d'urgence, mais ne
rien publier sur une 50 en fin de vie.

## Chantier 0, terminé

Fusionné le 29 août 2026, PR #1, squash. CI verte sur `lint`, `test`,
`flatpak`. `meson test` 3/3, `flatpak run io.github.vertours.Rature` ouvre la
fenêtre. Rendu visuel non vérifié, contrôle humain (`CLAUDE.md` §6).

Faits durables à garder pour la suite :

- **Deux interpréteurs sur la machine.** Le venv du projet est en Python 3.13
  sans `gi`, il sert à `ruff` et `pytest`. `/usr/bin/python3` est en 3.14
  avec `gi` (GTK 4.22, libadwaita 1.9.3), il sert à lancer l'application hors
  Flatpak. Option Meson `python` : en local
  `meson setup build -Dpython=/usr/bin/python3`, défaut sous Flatpak et en CI.
- Le paquet s'installe sous `<datadir>/rature/rature`, le lanceur ajoute ce
  dossier à `sys.path`. Indépendant du prefix.
- Plancher Meson `1.9` : version de `org.gnome.Sdk//50`.
- `meson test` en local enchaîne `desktop-file-validate`,
  `appstreamcli-validate` et `pytest` (résolu sur le `PATH`, donc le venv
  activé). En CI, le job `meson` ne lance que les deux tests de métadonnées
  par leur nom, `pytest` a son propre job. La séquence CI est
  `meson setup` puis `meson compile` puis `meson test`, le compile est
  nécessaire, les fichiers fusionnés ne sont pas dans le rebuild implicite
  de `meson test`.
- Dépendances de dev déclarées dans `pyproject.toml`,
  `[dependency-groups] dev` (PEP 735) : `ruff`, `pytest`, `pytest-cov`.
  Installation `pip install --group dev`, pip 25.1 ou plus.
- Démonstration gettext : le label « Empty window » de `data/ui/window.ui`,
  traduit « Fenêtre vide ». Placeholder retiré au chantier 3.
- `appstreamcli validate` passe. Seule remarque `--pedantic` :
  `cid-contains-uppercase-letter` sur le `R` de `Rature`, délibéré
  (`CLAUDE.md` §3).
- Métadonnées volontairement minimales : captures d'écran et couleur de
  marque repoussées au chantier 5 (ROADMAP §5.1).
- `flatpak-builder-lint` tourne dans le conteneur `gnome-50` en CI. Il
  redeviendra un point de contrôle explicite au chantier 5.
  `org.flatpak.Builder` n'est pas installé en local.
- `pyproject.toml` n'a pas de table `[build-system]` : le build passe par
  Meson.

## Revue externe du 29 août 2026

Revue externe reçue le 29 août 2026, non versionnée, visait le commit
`a8f98ea`. Partie 3 déjà couverte par la session C. Partie 2, les neuf
correctifs, appliquée sur la branche `chore/post-review-cleanup` :

- `.venv/` ignoré explicitement, bloc d'exemple de `CHANTIER-0.md` rafraîchi
- chemins réels dans `CLAUDE.md` §11
- `test_version_sources_agree` : accord entre `__init__.py`, `pyproject.toml`,
  `meson.build` et la dernière `<release>` du metainfo. Un bump laisse la
  suite rouge tant que l'entrée metainfo n'est pas écrite, c'est voulu
- job CI `meson`, suppression des deux tests pytest de validation redondants
- `POTFILES.in` réduit aux fichiers portant des chaînes marquées
- `[dependency-groups] dev` ajouté
- `STATE.md` désigné source unique de l'avancement, en-tête ajouté sur
  `ROADMAP.md` et `CHANTIER-0.md`, listes de préfixes de branche unifiées
- ADR 0006 sur l'installation sous `datadir`

Les fichiers de revue ne sont pas versionnés (`review/` est dans
`.gitignore`) : une revue datée devient fausse au fil des correctifs.

## Chantier 1, à venir

Logique métier dans `core/`, d'après `CLAUDE.md` §2. Découpage dans
`docs/internal/ROADMAP.md`. Premier pas : `core/models.py`, des `dataclass`
pures avec sérialisation vers dictionnaire et retour.

Rappel : aucun fichier de `core/` n'importe `gi`, le test
`tests/test_core_has_no_gtk.py` le vérifie déjà.

## Documents

Cadrage relu, contradictions résolues, six cas limites tranchés en `CLAUDE.md`
§2.7 le 25 août 2026.
