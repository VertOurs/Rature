# État courant

Mis à jour en fin de chaque session. Le cadrage stable est dans `CLAUDE.md`.

## Avancement

- **Chantier en cours** : 0, fondations
- **Étape suivante** : session B, Meson, gettext, fenêtre vide
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
- Branche en cours : `build/python-skeleton`, session A commitée, PR à ouvrir

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
| B | Meson, gettext, fenêtre vide | À faire |
| C | Manifeste Flatpak, CI, README, CHANGELOG, CONTRIBUTING | À faire |

La règle « Require status checks » sera ajoutée au ruleset GitHub à la fin de
la session C, une fois la CI existante.

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
