# CLAUDE.md

> **Note for contributors** : this is an internal working document, written in
> French, like everything under `docs/internal/`. The codebase, the user
> interface and all public documentation are in English.

Document de cadrage à l'usage de Claude. Lu automatiquement en mode agent.
À relire au début de chaque session.

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
ci-dessous. L'auteur continue d'utiliser ses conversations Claude au
quotidien en attendant que l'application soit prête, il n'y a donc aucune
urgence fonctionnelle et aucune donnée existante à préserver.

---

## 2. Spécification du produit

**C'est la section la plus importante du document.** Tout le reste est de la
technique. Ceci est le produit.

### 2.1 Les règles de la méthode

1. Les tâches sont dictées une par une, en vrac, sans ordre imposé
2. Chaque tâche est ajoutée à une liste numérotée, sans commentaire
3. La liste peut être figée. Une liste figée bloque l'ajout d'une tâche et
   le tirage depuis la réserve. Rayer, dérayer, renommer, supprimer et
   réordonner restent possibles. Figer arrête la composition de la journée,
   pas son déroulement
4. Rayer une tâche la barre et la remonte dans un bloc « Rayées », en haut
5. La liste complète reste visible en permanence : rayées en haut, en cours
   en dessous
6. Renommer, déplacer, réordonner : exécuté sans discussion
7. Aucun commentaire, aucune motivation, aucune question

### 2.2 La distinction qui ne doit jamais être perdue

**Rayer** : la tâche est barrée mais reste visible. C'est une trace de ce qui
a été fait.

**Supprimer** : la tâche disparaît sans laisser de trace consultable. Elle ne
réapparaît dans aucune liste, aucune archive affichée, aucun export. Ce n'est
pas un accomplissement, c'est un abandon.

Ces deux actions sont distinctes dans l'interface, portent des icônes
différentes, et ne doivent jamais être fusionnées ni confondues. C'est le
point le plus critique de toute la spécification.

**Journal de suppressions.** Le comptage des suppressions demandé en §2.6
suppose de garder une trace de ce que §2.2 fait disparaître. Arbitrage
retenu : le fichier d'archive conserve une entrée par suppression, contenant
l'identifiant, le numéro, l'origine, l'horodatage **et le texte de la
tâche**.

Ce que « sans trace » signifie exactement, et il faut être précis :

- La tâche disparaît de toutes les vues : jour, réserve, archives affichées,
  export. Elle n'est jamais réaffichée par l'application, ni comptée comme
  un accomplissement
- Le journal n'est jamais présenté à l'utilisateur. La fenêtre Statistiques
  en tire un nombre, jamais un contenu
- Le texte reste toutefois lisible pour qui ouvre le fichier d'archive à la
  main. La disparition est fonctionnelle, elle n'est pas une garantie de
  confidentialité, et le document ne prétend pas le contraire

Une suppression annulée (chantier 4) restaure la tâche à l'identique depuis
son entrée de journal, puis retire cette entrée.

### 2.3 Ce que l'interface ne doit jamais faire

Contraintes de conception, à opposer à toute proposition contraire.

- Pas de félicitations, pas de messages d'encouragement, pas d'émoticônes
- Pas de séries, de scores, de badges, d'objectifs, de barres de
  progression, aucune forme de ludification
- Aucun chiffre affiché spontanément dans la vue Jour, ni compteur, ni
  comparaison avec les jours précédents
- Pas de boîte de confirmation à la suppression. Une annulation possible
  après coup, jamais une question avant
- Pas de suggestion, pas de tri automatique, pas de priorisation implicite
- Une entrée cryptique ou en abrégé est enregistrée telle quelle. Ce n'est
  jamais à l'application de demander des précisions

L'application est un support, pas un coach. Toute fonctionnalité qui commente
le comportement de l'utilisateur est hors sujet.

### 2.4 Comportements attendus

- Ajouter une tâche puis la rayer immédiatement est un usage normal, c'est de
  la journalisation rétroactive, pas une erreur à corriger
- Le numéro d'une tâche est une étiquette attribuée à l'ajout. Il ne change
  jamais, ni à la rature, ni à la suppression, ni au réordonnancement, ni au
  passage d'une tâche dans le bloc « Rayées »
- L'ordre d'affichage est indépendant du numéro. Une liste réordonnée peut
  très bien afficher 3, 1, 7. C'est voulu
- Un numéro libéré par une suppression n'est jamais réattribué dans la
  journée
- Rien n'est perdu au passage d'une journée à l'autre

### 2.5 Réserve et récurrentes

**Réserve** : liste mère sans date. Tout ce qui traîne. On y puise le matin,
elle n'est jamais affichée mélangée à la liste du jour.

**Tirage depuis la réserve** : c'est un déplacement, jamais une copie.
L'item quitte la réserve au moment du tirage. La tâche créée conserve dans
`source_id` l'identifiant de l'item d'origine. Si elle n'est pas faite, elle
retourne en réserve au passage du jour, par son `source_id`.

**Récurrentes** : modèles de tâches associés à des jours de la semaine,
injectés automatiquement au passage à une nouvelle journée.

**Date de référence** : la date locale, jamais UTC. La bascule d'un jour à
l'autre a lieu à 04:00 heure locale. Une liste remplie à 01:00 appartient à
la journée de la veille. Au changement d'heure, la bascule suit l'heure
locale, sans compensation.

**Passage du jour**, déclenché à l'ouverture si la date de référence a
changé, ou manuellement :

1. La journée en cours est archivée telle quelle
2. Les tâches non faites issues de la réserve y retournent, identifiées par
   leur `source_id`
3. Les tâches non faites créées dans le jour partent en réserve, sans
   doublon de texte. La comparaison se fait après suppression des espaces de
   début et de fin, insensible à la casse, accents conservés
4. Les tâches non faites issues d'une récurrente sont abandonnées, elles
   reviendront d'elles-mêmes
5. Le compteur repart à 1, la liste est déverrouillée
6. Les récurrentes du jour sont injectées

Si plusieurs jours se sont écoulés depuis la dernière ouverture, le passage
du jour ne s'exécute qu'une fois. La journée enregistrée est archivée sous sa
propre date. Les jours intermédiaires n'existent pas, ils ne sont ni
archivés, ni peuplés. Seules les récurrentes du jour courant sont injectées.

Aucune donnée n'est perdue lors d'un passage de jour. C'est cette garantie
qui autorise à le déclencher sans demander confirmation. Une tâche supprimée
fait exception : la suppression est un abandon volontaire, elle ne revient
donc pas en réserve, y compris si la tâche en était issue.

### 2.6 Statistiques

Une fenêtre Statistiques existe, ouverte volontairement par l'utilisateur
depuis le menu. Elle est en lecture seule et porte sur les archives.

**Autorisé** : nombres bruts par jour et par période. Tâches ajoutées,
rayées, supprimées, renvoyées en réserve. Une répartition dans le temps.

Les trois premiers comptages se déduisent des tâches archivées. Les
suppressions se comptent à partir du journal décrit en §2.2. Ce journal
contient le texte des tâches supprimées, mais la fenêtre Statistiques
n'affiche qu'un nombre. Ne jamais y exposer le contenu, sous aucune forme,
y compris un aperçu ou une recherche.

**Interdit** : toute appréciation de ces nombres. Pas de moyenne présentée
comme un objectif, pas de tendance commentée, pas de série de jours
consécutifs, pas de couleur qui distingue un bon jour d'un mauvais, pas de
notification.

La différence n'est pas la donnée, c'est qui déclenche l'affichage. Un
chiffre que l'utilisateur va chercher est une consultation. Le même chiffre
poussé vers lui devient un commentaire sur son comportement, ce que §2.3
interdit.

### 2.7 Cas tranchés

Cas limites soulevés à la relecture du cadrage et tranchés le 25 août 2026.
Ils ne sont pas des détails d'implémentation : chacun décide d'un
comportement observable. Ne pas les rouvrir sans demande explicite.

**2.7.1 Renommage d'une tâche tirée de la réserve**

Une tâche tirée de la réserve puis renommée dans la journée retourne en
réserve avec son **texte renommé**, pas son texte d'origine.

Le renommage est une correction assumée par l'utilisateur, pas un accident.
Il n'y a aucune raison de lui réimposer une formulation qu'il vient de
rejeter. L'item de réserve est retrouvé par son `source_id`, puis son texte
est écrasé par celui de la tâche.

Conséquence : le texte d'un item de réserve n'est pas immuable. Seul son `id`
l'est.

**2.7.2 Récurrente sans jour sélectionné**

`weekdays` ne peut jamais être vide. Une récurrente porte toujours la liste
explicite de ses jours. « Tous les jours » s'écrit `[0, 1, 2, 3, 4, 5, 6]`.

L'interface interdit de valider une récurrente sans aucun jour coché. La
couche `core/` refuse une liste vide et lève une erreur.

Motif : une liste vide interprétée comme « tous les jours » produit exactement
l'inverse de ce que l'utilisateur croit faire en décochant tout. Le cas le
plus probable est une désactivation qui déclenche la récurrente sept jours
sur sept.

**2.7.3 Suppression d'une tâche issue de la réserve**

Le tirage depuis la réserve est un déplacement. Supprimer la tâche du jour
qui en résulte détruit donc définitivement l'item de réserve d'origine. Il ne
revient pas, ni au passage du jour, ni autrement.

C'est cohérent avec §2.2 : supprimer est un abandon volontaire. Le
comportement est conservé tel quel, sans confirmation, conformément à §2.3.

La récupération passe par l'annulation de la dernière suppression
(chantier 4), qui restaure la tâche dans la journée. L'item repart alors en
réserve au passage du jour suivant s'il n'a pas été rayé, par le mécanisme
normal.

**2.7.4 Doublons dans la réserve**

Le passage du jour n'envoie pas en réserve une tâche dont le texte y figure
déjà (§2.5 point 3). Cette contrainte ne s'applique **qu'au passage du jour**.

Un ajout manuel en réserve n'est jamais dédoublonné. L'utilisateur peut y
inscrire deux fois le même texte s'il le souhaite. C'est volontaire : deux
entrées identiques peuvent désigner deux choses différentes, et §2.3 interdit
à l'application de demander des précisions.

**2.7.5 Nom du fichier d'archive**

Le fichier d'archive porte la date du jour archivé, c'est à dire la valeur du
champ `date` de la journée, au format `AAAA-MM-JJ`.

Ce n'est **jamais** la date système au moment de l'archivage. Le passage du
jour a lieu après la bascule, donc au moment où il s'exécute la date système
désigne déjà le jour suivant.

Conséquence directe de la bascule de 04:00 décrite en §2.5 : une liste
remplie à 01:00 appartient à la journée de la veille et son archive porte la
date de la veille.

**2.7.6 Horodatages**

Tout horodatage stocké porte son décalage horaire :
`2026-08-24T14:32:07+02:00`. Cela concerne `done_at` sur les tâches et
`deleted_at` dans le journal `deletions`.

Sans décalage, deux horodatages identiques désignent deux instants différents
lors du passage à l'heure d'hiver, et la fenêtre Statistiques compte faux une
nuit par an.

Le champ `created` des items de réserve reste une date simple, sans heure. Il
n'est pas concerné.

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
   Proposer le message de commit, attendre l'accord.
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

Le dépôt doit tenir devant un lecteur exigeant. L'historique git est la
première chose qu'un recruteur technique regarde.

### Style de code

Pas de commentaires explicatifs inline (#) dans le code. Une fonction bien
écrite se documente elle-même par son nom et sa structure. Si un commentaire
semble nécessaire, c'est le signe que la fonction doit être refactorisée ou
renommée, pas commentée.

Docstrings courtes autorisées (une ligne, but de la fonction/classe/module).
Pas de docstrings longues ou explicatives.

### Messages de commit : Conventional Commits 1.0.0

Standard le plus répandu dans l'industrie, lisible par un humain et
exploitable par un outil pour générer un CHANGELOG.

```
<type>(<portée facultative>): <description à l'impératif>

<corps facultatif, le pourquoi plutôt que le quoi>

<pied facultatif : BREAKING CHANGE, Closes #12>
```

**Types autorisés**

| Type | Usage |
|---|---|
| `feat` | Nouvelle fonctionnalité visible par l'utilisateur |
| `fix` | Correction de bogue |
| `refactor` | Réécriture sans changement de comportement |
| `test` | Ajout ou correction de tests |
| `docs` | Documentation seule |
| `build` | Meson, Flatpak, empaquetage, dépendances |
| `ci` | Intégration continue |
| `i18n` | Chaînes traduisibles et fichiers de traduction |
| `chore` | Tâches diverses sans effet sur le code livré |

**Règles**

- Description à l'impératif présent, en anglais, sans majuscule initiale,
  sans point final, 72 caractères au maximum
- Une intention par commit. Si le message contient « et », il y a
  probablement deux commits
- Le corps explique le pourquoi, jamais le quoi, que le diff montre déjà
- `BREAKING CHANGE:` en pied pour toute rupture de format de données ou de
  comportement
- Portées cohérentes avec l'arborescence : `core`, `ui`, `storage`, `i18n`,
  `flatpak`, `meson`

**Exemples**

```
feat(core): add reserve list with day promotion

fix(ui): keep task numbering stable after deletion

refactor(core): extract day rollover from session

Rollover logic was tangled with persistence, which made it impossible
to test without touching the filesystem.

feat(storage): switch to atomic writes

BREAKING CHANGE: data file layout changed, see migrations.py
```

### Historique

- Une branche par tâche, préfixée par le type de commit : `feat/`, `fix/`,
  `refactor/`, `build/`, `ci/`, `docs/`, `test/`, `chore/`
- Fusion par pull request, jamais de commit direct sur `main`
- Fusion en squash uniquement, un commit par pull request. Les options
  « merge commit » et « rebase and merge » sont désactivées dans les
  réglages du dépôt, pour que la règle soit tenue par l'outil et non par la
  mémoire
- Historique linéaire, pas de commit de fusion
- Commits signés avec GPG, pour la mention « Verified » sur GitHub

### Versions

Versionnage sémantique. Claude signale l'incrément applicable à chaque
fusion susceptible de donner lieu à une version.

- `fix` seul : incrément de correctif, `0.1.0` vers `0.1.1`
- `feat` : incrément mineur, `0.1.1` vers `0.2.0`
- `BREAKING CHANGE` : incrément majeur
- Avant la version 1.0, les ruptures se contentent d'un incrément mineur

`0.9.x` correspond aux chantiers 0 à 4 terminés : fonctionnellement
complet, non publié. `1.0.0` correspond au chantier 5 terminé :
l'application est installable et se met à jour depuis le dépôt
auto-hébergé.

### Releases

Un tag par version, une entrée de CHANGELOG au format Keep a Changelog,
jamais de release sans CI verte.

### Interface

Suivre les recommandations d'interface GNOME et l'accessibilité au clavier.
Toute action fréquente a un raccourci.

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
