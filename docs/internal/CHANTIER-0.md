# Chantier 0 : fondations

Objectif : une chaîne de production complète et verte, sur une application
qui ne fait rien. Aucune fonctionnalité ici, c'est volontaire.

Durée réaliste : deux à trois sessions courtes.

> **L'avancement réel vit dans `STATE.md`.** Les cases de ce document
> décrivent le périmètre, pas l'état.

---

## Étape 0.1 : figer le nom

Fait. Nom retenu : **Rature**. Identifiant : `io.github.vertours.Rature`.

« Rature » désigne le trait qui barre une entrée, c'est le geste central de
l'application.

- [x] Nom choisi
- [x] Aucune application Flathub ne porte ce nom
- [x] Un dépôt GitHub `rature` existe ailleurs, outil d'anonymisation de
      documents, autre compte et autre usage. Aucun conflit d'identifiant.
- [ ] Vérifier que le dépôt `Rature` est disponible sur le compte VertOurs

Note : la partie domaine doit être en minuscules, d'où `io.github.vertours`
et non `io.github.VertOurs`. La partie finale garde sa majuscule.

Le nom est français, l'interface est en anglais. C'est le résumé affiché
sous le nom qui porte le sens pour un anglophone. À rédiger au chantier 5,
piste de départ : « Your day, one line at a time ».

---

## Étape 0.2 : dépôt local

```bash
mkdir -p ~/Documents/DEV/rature
cd ~/Documents/DEV/rature
git init -b main
```

Créer `.gitignore`. Version en vigueur, à recopier depuis le vrai fichier
à la racine si elle diverge :

```
build/
build-flatpak/
.flatpak-builder/
__pycache__/
*.pyc
*.mo
/po/rature.pot
*.pot~
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# Local environment
.venv/

# Session reviews, not versioned
review/

# Editors
.idea/
.vscode/

# Local agent settings
.claude/settings.local.json
.claude/*.tmp.*
```

---

## Étape 0.3 : licence

- [ ] Récupérer le texte GPL-3.0 dans `LICENSE`
- [ ] Prévoir l'en-tête court à mettre en tête de chaque fichier source

Le texte officiel se récupère sur `https://www.gnu.org/licenses/gpl-3.0.txt`.

---

## Étape 0.4 : arborescence

```bash
mkdir -p src/rature/core src/rature/ui
mkdir -p data/ui data/icons/hicolor/scalable/apps
mkdir -p po tests build-aux/flatpak docs
```

Créer les `__init__.py` nécessaires.

---

## Étape 0.5 : outils Python

`pyproject.toml`, configuration de ruff et pytest.

Points à régler :
- ruff : longueur de ligne, règles activées, format
- pytest : chemin des tests, ajout de `src` au chemin d'import

```bash
pip install --user ruff pytest
```

- [ ] `ruff check .` passe sur un dépôt vide
- [ ] `pytest` s'exécute même sans test

---

## Étape 0.6 : Meson

Trois fichiers : `meson.build` à la racine, un dans `data/`, un dans `po/`.

Ce que le build doit faire dès maintenant :
- installer le paquet Python dans le bon préfixe
- générer le lanceur exécutable
- traduire et installer le `.desktop` et le `.metainfo.xml`
- compiler les `.po` en `.mo`
- installer l'icône
- déclarer `meson test` qui appelle pytest

```bash
meson setup build
meson compile -C build
meson test -C build
```

- [ ] Les trois commandes passent
- [ ] `./build/rature` ouvre une fenêtre vide

---

## Étape 0.7 : gettext

- [ ] `po/LINGUAS` contenant `fr`
- [ ] `po/POTFILES.in` listant les fichiers contenant des chaînes
- [ ] Générer le `.pot`, puis `fr.po`

```bash
meson compile -C build rature-pot
meson compile -C build rature-update-po
```

- [ ] Une chaîne de test s'affiche en français quand la locale est française

---

## Étape 0.8 : Flatpak par Meson

Le manifeste change de nature : il ne fait plus des `install` à la main, il
appelle Meson.

```yaml
modules:
  - name: rature
    buildsystem: meson
    sources:
      - type: dir
        path: ../..
```

```bash
flatpak-builder --user --install --force-clean build-flatpak \
  build-aux/flatpak/io.github.vertours.Rature.yml
flatpak run io.github.vertours.Rature
```

- [ ] La fenêtre vide s'ouvre depuis le Flatpak

---

## Étape 0.9 : intégration continue

`.github/workflows/ci.yml`, déclenché sur chaque pull request.

Trois travaux :
1. `ruff check` et `ruff format --check`
2. `pytest`
3. Construction du Flatpak dans le conteneur `bilelmoussaoui/flatpak-github-actions`

- [ ] Une pull request de test passe au vert

---

## Étape 0.10 : documentation et discipline

- [ ] `README.md` en anglais, court
- [ ] `CHANGELOG.md`, format Keep a Changelog
- [ ] `CONTRIBUTING.md`, même si personne d'autre ne contribue, il fixe les
      règles pour soi-même
- [ ] `docs/internal/ARCHITECTURE.md` copié dans le dépôt
- [ ] `docs/internal/ROADMAP.md` copié dans le dépôt
- [ ] `docs/internal/CHANTIER-0.md` copié dans le dépôt
- [ ] `CLAUDE.md` et `STATE.md` copiés à la racine
- [ ] `docs/adr/` copié dans le dépôt
- [ ] Protéger la branche `main` : pas de commit direct, CI verte obligatoire
- [ ] Désactiver merge commit et rebase merge dans les réglages GitHub

---

## Critère de fin du chantier 0

Tout doit être vrai :

- [ ] `meson setup build && meson compile -C build && meson test -C build` passe
- [ ] Le Flatpak se construit et s'ouvre
- [ ] Une pull request de test est verte
- [ ] `main` est protégée
- [ ] Le dépôt contient licence, README, CHANGELOG, architecture, roadmap

Alors seulement, chantier 1.
