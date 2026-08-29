# État courant

Mis à jour en fin de chaque session. Le cadrage stable est dans `CLAUDE.md`.

## Avancement

- **Chantier en cours** : 0, fondations
- **Étape suivante** : session C, manifeste Flatpak, CI, README, CHANGELOG,
  CONTRIBUTING
- **Cible `0.9.x`** : chantiers 0 à 4 terminés, non publié
- **Cible `1.0.0`** : chantier 5 terminé, publié sur le dépôt auto-hébergé
- **Mode de travail** : agent dans l'IDE, PyCharm
- **POC** : abandonné, aucune donnée à reprendre

## Dépôt

- `github.com/VertOurs/Rature`, public
- Branche `main` protégée, pull request obligatoire, poussée directe interdite
- Fusion en squash uniquement, merge commit et rebase désactivés
- Un seul commit sur `main` : `docs: add project specification and decision
  records`. C'était l'exception fondatrice, la protection ne pouvant pas
  précéder l'existence du dépôt
- Branche en cours : `build/python-skeleton`, sessions A et B commitées,
  session C sur la même branche, une seule PR pour tout le chantier 0

## Versions retenues

Vérifiées le 26 août 2026, à revérifier avant toute mise à jour du manifeste,
conformément à `CLAUDE.md` §4 règle 8.

| Élément | Version | Motif |
|---|---|---|
| Runtime | `org.gnome.Platform//50` | Seule stable courante, la 49 arrive en fin de vie |
| Python cible | 3.13 | Celui du runtime 50, et non le 3.14 de la machine de développement |
| Version du projet | `0.1.0` | Premier jalon, rien de publiable |
| Meson minimal | 1.11 | Version présente sur la machine |

## Découpage restant du chantier 0

| Session | Contenu | État |
|---|---|---|
| A | Arborescence Python, `pyproject.toml`, deux tests | Terminée |
| B | Meson, gettext, fenêtre vide | Terminée |
| C | Manifeste Flatpak, CI, README, CHANGELOG, CONTRIBUTING | À faire |

La règle « Require status checks » sera ajoutée au ruleset GitHub à la fin de
la session C, une fois la CI existante.

Session B, notes :

- **Deux interpréteurs sur la machine.** Le venv du projet est en Python
  3.13 sans `gi` ; le `python3` système est en 3.14 avec `gi` (GTK 4.22,
  libadwaita 1.9.3). Le venv sert à `ruff` et `pytest`, le système à lancer
  l'application hors Flatpak.
- Option Meson `python` (défaut `python3`) : cible de l'interpréteur du
  lanceur installé. En local, `meson setup build -Dpython=/usr/bin/python3`.
  Sous Flatpak et en CI, laisser le défaut.
- Le paquet s'installe sous `<datadir>/rature/rature` et le lanceur ajoute
  ce dossier à `sys.path`. Indépendant du prefix, pas de dépendance au
  `site-packages` de l'interpréteur.
- `meson test` : trois tests, `desktop-file-validate`,
  `appstreamcli validate --no-net`, et `pytest` (résolu sur le `PATH`, donc
  le venv activé).
- Vérification locale de la fenêtre :
  `meson setup build --prefix="$PWD/build/local-install" -Dpython=/usr/bin/python3`
  puis `meson compile -C build && meson install -C build` puis
  `./build/local-install/bin/rature`. La fenêtre s'ouvre, sans erreur en
  sortie. Rendu visuel non vérifié, contrôle humain requis (`CLAUDE.md` §6).
- Chaîne de démonstration gettext : le label « Empty window » de
  `data/ui/window.ui`, traduit « Fenêtre vide ». Placeholder retiré au
  chantier 3.
- `appstreamcli validate` passe. Une seule remarque `--pedantic` :
  `cid-contains-uppercase-letter` sur le `R` de `Rature`, majuscule
  délibérée (`CLAUDE.md` §3), sans effet sur la validation.
- Métadonnées volontairement minimales : captures d'écran et couleur de
  marque du metainfo sont repoussées au chantier 5 (ROADMAP §5.1).

Session A, notes :

- En-tête court retenu, en tête de chaque fichier source :
  `# SPDX-License-Identifier: GPL-3.0-or-later`
  puis `# SPDX-FileCopyrightText: 2026 VertOurs`
- `data/`, `po/`, `build-aux/flatpak/` sont créés sur disque mais vides, donc
  absents de git. Ils entreront dans l'index en sessions B et C avec du
  contenu réel.
- `pyproject.toml` n'a pas de table `[build-system]` : le build passe par
  Meson, ce fichier ne sert qu'aux métadonnées et à `ruff` / `pytest`.

Signature des commits, à régler avant la PR du chantier 0 :

- Aucune config de signature sur la machine. Méthode non tranchée, SSH ou GPG.
- Rétro-signer uniquement les commits propres à la branche, `git rebase`
  limité à `main..HEAD`, tant que la branche n'est pas poussée.
- Ne jamais réécrire `1356198` : déjà sur `main`, protégée et poussée. Le
  commit fondateur reste non signé, c'est accepté.

## Documents

Cadrage relu, contradictions résolues, six cas limites tranchés en `CLAUDE.md`
§2.7 le 25 août 2026.
