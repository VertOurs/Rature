# CLAUDE.md

> **Note for contributors** : this is an internal working document, written in
> French, like everything under `docs/internal/`. The codebase, the user
> interface and all public documentation are in English.

Document de cadrage à l'usage de Claude. Lu automatiquement en mode agent.

À lire au début de chaque session, dans cet ordre :

1. ce fichier
2. `docs/internal/SPECIFICATION.md`, la spécification produit
3. `STATE.md`, l'état courant

---

## 1. Le projet

Application de bureau GNOME nommée **Rature**, qui reproduit une méthode de
liste quotidienne mise au point par son auteur. On dicte des tâches une par
une, on les raye au fil de la journée, sans planification ni catégories.

L'auteur s'appelle VertOurs. Il pratiquait cette méthode en conversation avec
Claude ; l'application la rend autonome.

Le projet est publié, même sans passer par Flathub. C'est délibéré : la
perspective d'être vu impose des captures, une documentation, des tests et
des versions. Un projet gardé pour soi s'arrête à « ça marche chez moi ».
Ne jamais proposer de relâcher les exigences de qualité au motif que
l'application est surtout pour son auteur.

**Second objectif, explicite : le dépôt doit pouvoir être montré à un
recruteur technique exigeant et lui plaire.** Cela vaut pour le code, mais
aussi pour l'historique git, les messages de commit, les tests, la CI, le
README et la lisibilité de l'ensemble. Un dépôt se juge autant sur sa forme
que sur ce qu'il fait.

**Le POC est abandonné.** Il n'est ni utilisé, ni migré, ni consulté, ni
recopié, même partiellement. La construction repart de la spécification
(`docs/internal/SPECIFICATION.md`). L'auteur continue d'utiliser ses
conversations Claude au quotidien en attendant que l'application soit prête,
il n'y a donc aucune urgence fonctionnelle et aucune donnée existante à
préserver.

---

## 2. Spécification du produit

La spécification produit vit dans `docs/internal/SPECIFICATION.md`. C'est le
document le plus important du dépôt : il décrit ce que fait l'application et
tranche toute contradiction en sa faveur. À lire au début de chaque session,
avant toute écriture de code métier. Ne rien en recopier ici.

---

## 3. Décisions figées

Discutées et tranchées. **Ne pas les rouvrir** sans demande explicite.

| Sujet | Choix |
|---|---|
| Nom | Rature |
| Identifiant | `io.github.vertours.Rature` |
| Compte GitHub | VertOurs |
| Périmètre | Application de bureau, PC uniquement |
| Distribution | Dépôt Flatpak auto-hébergé, bundle, AUR, COPR. Pas Flathub |
| Langue de l'interface | Anglais |
| Langue du code, des noms et des commentaires | Anglais |
| Langue des documents internes | Français, assumé |
| Traductions | gettext, dossier `po/`, français en priorité |
| Système de build | Meson |
| Licence | GPL-3.0-or-later |
| Runtime | GNOME courant, jamais une version en fin de vie |
| Architecture | `core/` sans aucun import GTK, séparé de `ui/` |
| Interface | Fichiers `.ui` + `Gtk.Template`, pas de widgets construits en Python |
| Données | JSON versionné, écriture atomique, migrations testées |
| Qualité | ruff, pytest, CI GitHub Actions |
| Sort du POC | Abandonné. Ni utilisé, ni migré, ni consulté, ni recopié |
| Version 0.9.x | Chantiers 0 à 4 terminés, fonctionnellement complet, non publié |
| Version 1.0.0 | Chantier 5 terminé, installable et mis à jour depuis le dépôt auto-hébergé |

Les décisions qui ont une histoire sont documentées dans `docs/adr/` :
rejet de Flathub (0001), séparation `core` et `ui` (0002), fichier JSON
unique (0003), abandon du prototype (0004), journal de suppressions (0005),
installation du paquet sous `datadir` (0006).

### Décisions encore ouvertes

- **Mention de l'assistance IA dans le README public.** À trancher avant le
  chantier 5, pas avant. Ne pas relancer le sujet d'ici là.
- **Traduction de `ARCHITECTURE.md` en anglais et publication dans `docs/`.**
  À trancher au chantier 5, pas avant.

---

## 4. Règles absolues

1. **`core/` n'importe jamais `gi`, GTK, Adw ou Gdk.** Si une fonction a
   besoin de GTK, elle n'appartient pas à `core/`. Aucune exception.
2. **Toute chaîne affichée passe par `_()`.** Jamais de texte en dur dans le
   code ou dans un `.ui` non marqué comme traduisible.
3. **Anglais partout dans le dépôt** : variables, fonctions, noms de
   fichiers, commentaires, messages de commit, issues. Les documents de
   `docs/internal/` sont en français, assumé.
4. **Un chantier à la fois.** Ne pas proposer de fonctionnalité appartenant à
   un chantier ultérieur, même si elle est facile. La noter dans la roadmap
   et passer à autre chose.
5. **Flathub est écarté définitivement.** La politique de Flathub, durcie le
   29 mai 2026, interdit tout contenu généré ou assisté par IA, dans
   l'application comme dans la soumission (manifeste, métadonnées,
   correctifs, scripts de build, pull request). Elle n'est pas rétroactive
   et prévoit des exceptions pour les projets matures et bien maintenus, ce
   qui ne correspond pas à un projet qui démarre. GNOME Circle a par
   ailleurs suspendu ses nouvelles soumissions le 30 mai 2026. Décision du
   24 août 2026 : ni Flathub, ni GNOME Circle. Ne pas la reproposer, ne pas
   la contourner, ne pas la commenter à chaque session.
6. **Pas de nouvelle dépendance sans validation explicite.** Trois
   catégories, à ne pas confondre :
   - Exécution : runtime GNOME (PyGObject, GTK, libadwaita) et bibliothèque
     standard Python. Rien d'autre
   - Construction : Meson, gettext
   - Développement : ruff, pytest, pytest-cov

   Toute addition, dans n'importe laquelle des trois, demande une
   validation.
7. **Les migrations de données sont testées avant d'être livrées.**
   Aujourd'hui il n'existe aucune donnée réelle. Dès que l'auteur utilisera
   l'application au quotidien, sauvegarder son fichier de données avant tout
   test de migration. Une migration ratée détruit des données.
8. **Dépendances toujours à jour.** Runtime GNOME, version de Python,
   bibliothèques, actions de CI : toujours une version courante et
   supportée, jamais une version obsolète ni proche de sa fin de vie.
   Vérifier sur `https://docs.flathub.org/docs/for-app-authors/runtimes`
   avant d'écrire ou de mettre à jour un manifeste. Ne jamais se fier à sa
   mémoire : les dates de fin de support ne sont pas dans les connaissances
   de Claude.
9. **Les idées qui surgissent en cours de route vont dans la roadmap ou
   dans une issue.** Jamais dans la session en cours. C'est la règle qui
   protège le projet de la dérive de périmètre.
10. **Rappeler le versionnage.** À chaque fusion susceptible de donner lieu
   à une version, signaler quel incrément s'applique et pourquoi.
   L'auteur a demandé explicitement ce rappel.
11. **Aucun renvoi vers un fichier qui n'existe pas.** Un lien mort dans un
   document de cadrage envoie l'agent chercher un contenu inventé.
12. **Contredire quand c'est nécessaire.** L'auteur pratique par ailleurs une
   méthode où Claude exécute sans discuter. Cela vaut pour ses listes de
   tâches, jamais pour le développement. Ici, une mauvaise idée doit être
   signalée, argumentée, et la décision lui revient ensuite.

---

## 5. Travail en mode agent

L'agent a accès au dépôt et peut exécuter des commandes. Garde-fous non
négociables.

1. **Jamais de travail sur `main`.** Une branche par tâche, toujours.
2. **Jamais de `git commit` ni de `git push` sans validation explicite.**
   Présenter le plan complet des commits, un message par commit, avant d'en
   écrire un seul. Un accord unique sur ce plan vaut pour tous les commits
   qu'il liste. Toute intention absente du plan demande une nouvelle
   validation. Le `git push` reste soumis à un accord distinct.
3. **Une modification à la fois.** Pas de refactoring massif non demandé,
   même s'il paraît évident. Le proposer, ne pas le faire.
4. **Lire avant d'écrire.** Consulter l'état réel des fichiers plutôt que de
   supposer. Ne jamais recréer un fichier qui existe.
5. **Ne jamais toucher aux données de l'utilisateur** dans
   `~/.var/app/` ou `~/.local/share/` sans demande explicite.
6. **Tenir `STATE.md` à jour** en fin de session.

---

## 6. Ce que Claude peut vérifier, et ce qu'il ne peut pas

À dire honnêtement plutôt qu'à laisser croire.

**Vérifiable en mode agent** : syntaxe, `ruff`, `pytest`, `meson compile`,
`meson test`, construction du Flatpak, lancement de l'application et lecture
des erreurs en sortie, validation du metainfo et du `.desktop`.

**Non vérifiable, jamais** : le rendu visuel. Alignements, lisibilité,
comportement au redimensionnement, cohérence avec les recommandations
d'interface GNOME. Ces points relèvent d'un contrôle humain, à demander
explicitement après toute modification d'interface.

**En conversation simple, hors agent** : seule la syntaxe est vérifiable, et
uniquement pour du code sans GTK. Le dire à chaque livraison plutôt que de
sous-entendre une validation qui n'a pas eu lieu.

C'est cette limite qui justifie l'architecture : ce qui est dans `core/` est
testable, ce qui est dans `ui/` ne l'est pas. Plus la logique remonte dans
`ui/`, moins le projet est vérifiable.

---

## 7. Manière de travailler attendue

**Format des réponses**
- Étapes courtes, numérotées, concrètes
- Checklists plutôt que paragraphes
- Un résumé court avant ou après les explications longues
- Peu de théorie, beaucoup de commandes exécutables
- Pas de tirets cadratins, jamais

**Rythme**
- L'auteur a une énergie fluctuante. Découper en blocs qui tiennent en une
  session courte.
- Toujours terminer par une action unique et immédiatement faisable.
- Ne pas empiler les options non hiérarchisées. Recommander, expliquer
  brièvement pourquoi, laisser le choix.

**Livraisons**
- Modifier les fichiers existants plutôt que tout réécrire, sauf si la
  réécriture est explicitement justifiée et annoncée.
- Une modification, une explication de ce qui change et pourquoi.
- Toujours donner la commande de vérification à lancer après.

---

## 8. Conventions du dépôt

Les conventions du dépôt (style de code, messages de commit, branches,
fusion, versionnage, releases, interface, traductions) vivent dans
`CONTRIBUTING.md`. Elles s'appliquent aussi à l'agent.

---

## 9. Ce qui a déjà posé problème

- **Runtime en fin de vie.** Le POC visait GNOME 47, déjà obsolète. Vérifier
  la version courante avant d'écrire un manifeste, ne jamais se fier à sa
  mémoire.
- **API dépréciées.** `Adw.MessageDialog` et `Gtk.UriLauncher` ont causé des
  avertissements et un plantage. Préférer les API stables.
- **Identifiant mal choisi.** `org.vertours.*` était invalide faute de
  domaine possédé. Vérifier les règles avant de nommer.
- **Fichiers perdus.** Le POC a dû être régénéré entièrement, faute de dépôt
  git.
- **Dérive de périmètre.** Une demande de fonctionnalité a immédiatement
  déclenché une réécriture complète. Cadrer d'abord, coder ensuite.
- **Décisions prises trop vite.** Un nom a été figé alors que la question
  restait ouverte. Reformuler la décision et attendre confirmation.

---

## 10. Définition de « terminé »

**À la charge de Claude**
- [ ] Code en anglais, séparation `core/` et `ui/` respectée
- [ ] Chaînes visibles marquées traduisibles
- [ ] Tests couvrant le comportement ajouté, et qui passent
- [ ] `ruff check` et `ruff format --check` passent
- [ ] Le Flatpak se construit encore
- [ ] CHANGELOG mis à jour
- [ ] Section « État courant » mise à jour

**À la charge de VertOurs**
- [ ] Contrôle visuel de toute modification d'interface
- [ ] Validation du message de commit
- [ ] Fusion de la pull request, CI verte

---

## 11. Commandes de référence

```bash
# Développement
meson setup build
meson compile -C build
meson test -C build

# Qualité
ruff check .
ruff format --check .
pytest
pytest --cov=rature.core --cov-fail-under=90

# Traductions
msgfmt --statistics po/fr.po -o /dev/null

# Flatpak local
flatpak-builder --user --install --force-clean build-flatpak \
  build-aux/flatpak/io.github.vertours.Rature.yml
flatpak run io.github.vertours.Rature

# Validation des métadonnées
# appstreamcli accepte la source ; desktop-file-validate exige un .desktop,
# donc le fichier fusionné, présent après `meson compile`.
appstreamcli validate data/io.github.vertours.Rature.metainfo.xml.in
desktop-file-validate build/data/io.github.vertours.Rature.desktop
flatpak run --command=flatpak-builder-lint org.flatpak.Builder \
  manifest build-aux/flatpak/io.github.vertours.Rature.yml
```

---

## 12. État courant

Voir `STATE.md`, mis à jour en fin de chaque session.
