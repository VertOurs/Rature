# Spécification du produit

Source unique du comportement produit de Rature. Rien de ce qu'il contient
n'est recopié ailleurs : les autres documents y renvoient. Toute
contradiction entre ce fichier et un autre document se tranche en faveur de
ce fichier.

La numérotation est stable. Les références de la forme `SPECIFICATION.md
§2.7.1` pointent ici et ne doivent pas changer de numéro.

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
  la journalisation rétroactive, pas une erreur à corriger. Maj+Entrée dans
  la zone de saisie du jour le fait en un geste (§3.2)
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
changé, et vérifié périodiquement tant que l'application reste ouverte :

1. La journée en cours est archivée telle quelle
2. Les tâches non faites issues de la réserve y retournent, identifiées par
   leur `source_id`
3. Les tâches non faites créées dans le jour partent en réserve, sans
   doublon de texte. La comparaison se fait après suppression des espaces de
   début et de fin, insensible à la casse, accents conservés
4. Les tâches non faites issues d'une récurrente sont abandonnées, elles
   reviendront d'elles-mêmes
5. Le compteur repart à 1, la liste est déverrouillée. Le journal de
   suppressions part avec l'archive, la nouvelle journée démarre avec un
   journal vide
6. Les récurrentes du jour sont injectées

Si plusieurs jours se sont écoulés depuis la dernière ouverture, le passage
du jour ne s'exécute qu'une fois. La journée enregistrée est archivée sous sa
propre date. Les jours intermédiaires n'existent pas, ils ne sont ni
archivés, ni peuplés. Seules les récurrentes du jour courant sont injectées.

Aucune donnée n'est perdue lors d'un passage de jour. C'est cette garantie
qui autorise à le déclencher sans demander confirmation. Une tâche supprimée
fait exception : la suppression est un abandon volontaire, elle ne revient
donc pas en réserve, y compris si la tâche en était issue.

Il n'existe aucun moyen de forcer un passage du jour dont la date de
référence n'a pas encore avancé. Une bascule anticipée archiverait la
journée en cours sous une date que la bascule suivante réécrirait, ce qui
contredirait la garantie ci-dessus.

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

## 3. Spécification d'interface

Cette section fixe ce que l'interface affiche et comment elle réagit. Elle a
le même statut que §2 : sa numérotation est stable, elle tranche toute
contradiction avec un autre document, et une proposition qui la contredit se
refuse en la citant.

§2 dit ce que l'application fait et ce qu'elle ne doit jamais faire. §3 dit à
quoi ça ressemble. Quand les deux se croisent, §2 gagne.

Les croquis sont schématiques. Ils fixent la disposition et la hiérarchie,
jamais les pixels. Le contrôle du rendu réel reste humain, voir `CLAUDE.md`
§6.

---

### 3.1 Fenêtre principale

Une seule fenêtre, `AdwApplicationWindow`, contenant un
`AdwNavigationSplitView`. Le panneau latéral porte trois entrées : Day,
Reserve, Recurring. Chaque entrée affiche sa vue dans le panneau de contenu.

Les archives ne sont pas une entrée du panneau. Elles s'ouvrent depuis le
menu principal, dans une fenêtre distincte, voir §3.5.

```
┌──────────────────────────────┬──────────────────────────────────────────┐
│ Rature                    ⋮  │  Monday 31 August                     🔒 │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Day                         │  ┌────────────────────────────────────┐  │
│  Reserve                     │  │  2   call the dentist       ↺   ⋮  │  │
│  Recurring                   │  │  5   take out the bin       ↺   ⋮  │  │
│                              │  └────────────────────────────────────┘  │
│                              │  ┌────────────────────────────────────┐  │
│                              │  │  1   finish the meson file  ✓   ⋮  │  │
│                              │  │  3   answer Marie           ✓   ⋮  │  │
│                              │  │  4   buy bread              ✓   ⋮  │  │
│                              │  └────────────────────────────────────┘  │
│                              │                                          │
│                              ├──────────────────────────────────────────┤
│                              │  [ Add a task…                        ]  │
└──────────────────────────────┴──────────────────────────────────────────┘
```

Le menu principal (`open-menu-symbolic`, en tête du panneau latéral) contient
au chantier 3 : Archives, puis About Rature. Au chantier 4, Keyboard
Shortcuts rejoint le menu, groupé avec About Rature (§3.11), et Statistics
rejoint Archives dans le premier groupe (§3.14).

**Taille et état.** La fenêtre lit `window-width`, `window-height` et
`window-maximized` à la construction, et les écrit à la fermeture. Pas de
liaison `Gio.Settings.bind` sur la largeur et la hauteur : elle enregistre
les dimensions transitoires de l'état maximisé.

**Propriété d'`App`.** `RatureApplication.do_activate` construit l'`App` une
fois, avant toute fenêtre, et la garde. Le traitement des échecs de démarrage
est en §3.6. Aucun autre objet n'appelle `App.open`.

**Passage du jour en cours d'exécution.** Une minuterie de soixante secondes
appelle `App.ensure_day`. Si elle rend une journée, les trois vues se
rafraîchissent et une bannière neutre l'annonce, voir §3.8. Un délai fixe et
court, plutôt qu'un réveil calculé jusqu'à 04:00, parce que le calcul se
trompe une nuit par an au changement d'heure.

---

### 3.2 Vue Jour

C'est la vue par défaut à l'ouverture.

**Structure.** `AdwToolbarView`. En tête, un `AdwHeaderBar` dont le titre est
la date de la journée en cours, en format long local. À droite, le bouton
Copy as text (§3.12), le bouton d'annulation de la dernière suppression, puis
le bouton bascule de verrouillage. En pied, la barre de saisie. Au centre, un
`GtkScrolledWindow`
contenant deux listes empilées.

**Les deux blocs.** Le bloc des rayées est toujours au-dessus, le bloc des
tâches en cours au-dessous, conformément à §2.1 point 5. Chacun est un
`GtkListBox` de style `boxed-list`. Un bloc vide n'est pas affiché : pas de
cadre vide, pas de titre de section, aucun libellé qui compte ce qu'il n'y a
pas.

L'ordre à l'intérieur d'un bloc est celui rendu par `Session.view()`. Il
n'est jamais recalculé dans l'interface.

**Une ligne.** Un seul modèle de ligne pour les deux blocs.

```
┌──────────────────────────────────────────────────────────────┐
│  12   text of the task                            ✓      ⋮   │
└──────────────────────────────────────────────────────────────┘
   │     │                                          │       │
   │     │                                          │       └ menu de ligne
   │     │                                          └ rayer ou dérayer
   │     └ texte, barré si la tâche est rayée
   └ numéro, chiffres tabulaires, atténué, jamais recalculé
```

Le numéro affiché est `task.num`. Il ne dépend ni de la position, ni du bloc,
conformément à §2.4.

Le barré est porté par une classe CSS appliquée à l'étiquette de texte, pas
par une construction de widget en Python.

**Rayer et supprimer.** Le bouton de la ligne raye, ou déraye si la tâche est
déjà rayée. Supprimer n'est jamais un bouton de ligne : c'est une entrée du
menu de ligne, marquée destructive. Les deux actions ne sont donc jamais
côte à côte et ne peuvent pas être confondues par un clic mal placé, ce
qu'exige §2.2.

Il n'y a aucune boîte de confirmation à la suppression, §2.3 l'interdit.
C'est le second geste nécessaire pour ouvrir le menu qui protège, pas une
question.

**Annuler la dernière suppression.** Un bouton dans l'en-tête, jamais un
contrôle de ligne : la ligne a disparu. Il restaure la dernière entrée du
journal `deletions` de la journée en cours, conformément à §2.2 et à
l'ADR 0005 :

- la tâche réapparaît à sa position d'origine (`index` du journal), avec son
  numéro d'origine, rayée si elle l'était, non rayée sinon
- l'entrée de journal est ensuite retirée. Le journal doit rester juste,
  sinon le comptage de §2.6 dérive
- une seule entrée à la fois, et seulement la journée en cours : le journal
  part avec l'archive au passage du jour, il n'y a plus rien à annuler après

Le bouton est insensible quand le journal de la journée est vide. Aucun
autre retour : la tâche réapparaît, sans bandeau ni message, §2.3. Le bouton
reste actif quand la liste est figée, comme la suppression elle-même.

Une tâche tirée de la réserve puis restaurée repart en réserve au passage du
jour suivant si elle n'a pas été rayée, par le mécanisme normal (§2.7.3).

**Menu de ligne.** Rename, puis Delete. Rien d'autre au chantier 3.

**Renommer.** L'étiquette de texte est remplacée sur place par une zone de
saisie contenant le texte actuel, sélectionné. Entrée valide, Échap annule,
la perte du focus valide. Aucune fenêtre ne s'ouvre. Un texte vide après
suppression des espaces annule le renommage sans rien changer.

**Ajouter.** La barre de pied contient une `GtkEntry` seule, sans bouton :
l'ajout se fait à la touche Entrée. Après ajout, la zone se vide, **garde le
focus**, et la liste défile jusqu'à la nouvelle tâche. C'est la règle qui
rend la dictée en rafale possible, elle n'est pas négociable. Un texte vide
après suppression des espaces n'ajoute rien.

**Ajouter une tâche déjà rayée.** Maj+Entrée dans la même zone de saisie
ajoute la tâche directement dans le bloc des rayées, en un geste au lieu
d'ajouter puis rayer. C'est le raccourci de la journalisation rétroactive
de §2.4. Même attribution de numéro qu'un ajout normal ; la zone se vide et
garde le focus de la même façon ; la liste défile jusqu'à la nouvelle tâche,
en haut cette fois. Refusé sur une liste figée, comme tout ajout (§2.1
point 3). Aucun contrôle visible : le geste est répertorié dans la fenêtre
d'aide des raccourcis (autre point du chantier 4).

**Liste figée.** Le bouton de verrouillage bascule entre `App.lock` et
`App.unlock`, et change d'icône. Quand la liste est figée :

- la zone de saisie est insensible
- le dépôt d'un élément de réserve est refusé, voir §3.6
- rayer, dérayer, renommer, supprimer, annuler une suppression et
  réordonner restent actifs

Aucun autre changement d'apparence. Pas de bandeau, pas de message. L'état du
bouton suffit.

**Réordonner.** Les lignes sont déplaçables par glisser-déposer à
l'intérieur de leur propre bloc. Un dépôt d'un bloc vers l'autre est refusé
et ne produit aucun retour visuel de dépôt possible. Motif : `move_before`
ordonne `day.tasks`, mais `view()` remonte toujours les rayées, donc un
déplacement entre blocs n'aurait aucun effet visible et passerait pour un
bogue.

**Vue vide.** Un `AdwStatusPage` sans icône, texte en §3.8. Il remplace les
deux blocs, jamais la barre de saisie, qui reste utilisable.

---

### 3.3 Vue Réserve

```
┌────────────────────────────────────────────────────┐
│  Reserve                                           │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │  repair the bike light               →   ⋮   │  │
│  │  call the insurance                  →   ⋮   │  │
│  │  sort the photos                     →   ⋮   │  │
│  └──────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│  [ Add to the reserve…                          ]  │
└────────────────────────────────────────────────────┘
```

Même structure que la vue Jour : en-tête, liste unique, barre de saisie en
pied. L'ajout suit les mêmes règles, focus conservé compris. Aucun
dédoublonnage, §2.7.4.

**La date `created` n'est jamais affichée.** Elle existe dans les données et
sert au retour en réserve, elle n'a pas à être montrée. Une date d'entrée
affichée à côté d'une tâche vieille de trois mois est un commentaire sur le
comportement de l'utilisateur, ce que §2.3 interdit.

**Bouton d'envoi** (`→`) : appelle `draw_from_reserve`. La ligne disparaît de
la réserve, c'est un déplacement et non une copie, §2.5. Il est insensible
quand la liste du jour est figée.

**Menu de ligne** : Rename, puis Delete. Le renommage est en place, comme en
§3.2.

**Glisser-déposer.** Chaque ligne est une source de glissement portant
l'identifiant de l'item. La cible est l'entrée Day du panneau latéral. Le
dépôt et le bouton d'envoi appellent **la même méthode de la fenêtre**,
jamais deux chemins parallèles. Quand la liste du jour est figée, la cible
refuse le dépôt et ne s'illumine pas.

---

### 3.4 Vue Récurrentes

```
┌────────────────────────────────────────────────────┐
│  Recurring                                    +    │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │  water the plants                        ⋮   │  │
│  │  Mon Thu                                     │  │
│  ├──────────────────────────────────────────────┤  │
│  │  weekly backup                           ⋮   │  │
│  │  Sun                                         │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

Une `AdwActionRow` par modèle : le texte en titre, les jours en sous-titre,
abrégés et dans l'ordre de la semaine, lundi premier. Pas de barre de saisie
en pied : la création demande un texte et des jours, donc un formulaire.

Le bouton `+` de l'en-tête ouvre le formulaire de création. Le menu de ligne
contient Edit, qui ouvre le même formulaire prérempli, puis Delete.

**Formulaire**, une `AdwDialog` :

```
┌──────────────────────────────────────────┐
│  Cancel        Recurring task       Save │
├──────────────────────────────────────────┤
│  [ Task text                          ]  │
│                                          │
│  Days                                    │
│  (Mon)(Tue)(Wed)(Thu)(Fri)(Sat)(Sun)     │
└──────────────────────────────────────────┘
```

Sept boutons bascules, lundi à gauche. **Save est insensible tant que le
texte est vide ou qu'aucun jour n'est coché.** L'interdiction de §2.7.2 se
traduit par un bouton inactif, jamais par une erreur affichée après coup.
`core` refuse aussi la liste vide, cette double barrière est voulue.

Les libellés des bascules, comme les jours du sous-titre de la ligne, sont
les noms de jours abrégés de la locale, obtenus par `strftime` sur une
semaine de référence commençant un lundi, le même mécanisme que le titre de
date de la vue Jour. Pas de lettre seule : deux `T` ou deux `S` identiques à
l'écran ne se distinguent pas. Chaque bascule porte le nom complet du jour
en infobulle.

Rien n'affiche « tous les jours » : sept boutons cochés se lisent
directement.

---

### 3.5 Fenêtre d'archives

Fenêtre distincte, ouverte depuis le menu principal, en lecture seule.

```
┌──────────────────┬─────────────────────────────────────┐
│ Archives         │  Friday 28 August                   │
├──────────────────┼─────────────────────────────────────┤
│  30 August 2026  │  ┌───────────────────────────────┐  │
│  29 August 2026  │  │  1   answer Marie             │  │
│▶ 28 August 2026  │  │  4   buy bread                │  │
│  27 August 2026  │  └───────────────────────────────┘  │
│                  │  ┌───────────────────────────────┐  │
│                  │  │  2   call the dentist         │  │
│                  │  │  3   read the meson docs      │  │
│                  │  └───────────────────────────────┘  │
└──────────────────┴─────────────────────────────────────┘
```

- Liste des dates fournie par `App.archives()`, du plus récent au plus
  ancien. Aucun compte, aucun aperçu, aucun résumé à côté d'une date.
- Le contenu d'une journée suit la disposition de §3.2 : rayées en haut, en
  cours en dessous, mêmes numéros.
- Aucun bouton sur les lignes, aucun menu, aucun glisser-déposer. Seul
  l'en-tête porte un bouton Copy as text (§3.12), qui copie la date
  sélectionnée.
- Le journal de suppressions n'est jamais affiché, §2.2. Les tâches
  supprimées n'apparaissent pas non plus dans la journée archivée.
- Une archive illisible affiche un texte neutre à la place du contenu, sans
  empêcher de consulter les autres dates.
- Aucune archive : `AdwStatusPage`, texte en §3.8.

La recherche dans les archives est spécifiée en §3.13.

---

### 3.6 Démarrage, erreurs et refus

Trois situations, trois traitements distincts. Aucune n'est un plantage.

**1. Fichier écrit par une version future** (`FutureVersionError`, levée par
`App.open`). Il n'y a pas encore de fenêtre, donc une `Gtk.AlertDialog`
présentée sans parent, puis `quit`. L'application ne démarre pas. Écraser les
données d'une version plus récente est la seule faute irréparable.

**2. Fichier illisible mis en quarantaine**
(`StartupOutcome.RECOVERED_FROM_CORRUPTION`). L'application démarre sur une
journée vide. Une `AdwBanner` non modale en tête de la vue Jour indique que
le fichier a été mis de côté et donne son nouveau nom. Fermable, elle ne
revient pas. Sans elle, l'utilisateur croit avoir tout perdu.

**3. Échec d'écriture pendant une mutation** (`OSError`). `App` ne défait pas
la mutation en mémoire, c'est documenté sur la classe. L'interface attrape
l'`OSError` **en un seul endroit**, l'enrobage commun de toutes les actions,
et affiche une `AdwBanner`. L'application reste utilisable, aucune boîte
modale, aucune fermeture forcée. La bannière disparaît à la première
écriture réussie.

**Une seule bannière, trois messages possibles.** Les situations 2 et 3
partagent la même `AdwBanner`, avec le nouveau jour (§3.1) : jamais deux
bannières à la fois, jamais de file d'attente. À chaque rafraîchissement,
une fonction unique choisit le message le plus prioritaire parmi ceux
encore actifs et non fermés, et le pose sur cette bannière : échec
d'écriture d'abord, puis quarantaine, puis nouveau jour. Un échec
d'écriture masque ainsi temporairement une bannière de quarantaine
affichée, qui réapparaît dès que l'écriture suivante réussit. Fermer un
message ne ferme pas les autres, et un message fermé ne revient jamais,
y compris au rafraîchissement suivant.

**Refus métier.** `LockedError`, `KeyError` et `ValueError` remontent de
`core` mais ne doivent jamais atteindre l'utilisateur : l'interface rend
insensibles les commandes impossibles au lieu de les laisser échouer. Une
telle exception qui survient malgré tout est un bogue, elle se journalise sur
la sortie d'erreur et n'affiche rien.

---

### 3.7 Fenêtres étroites

Un `AdwBreakpoint` sur la fenêtre principale. Sous 500 unités de largeur,
`AdwNavigationSplitView` passe en mode replié : le panneau latéral devient
une page, avec un bouton de retour dans l'en-tête de la vue.

Contraintes qui restent vraies en étroit :

- la barre de saisie reste visible et accessible au clavier
- le texte d'une tâche s'enroule sur plusieurs lignes, il n'est jamais
  tronqué par des points de suspension
- le numéro et les boutons de ligne restent visibles

Le glisser-déposer de la réserve vers l'entrée Day n'est pas disponible en
mode replié, l'entrée n'étant pas à l'écran. Le bouton d'envoi couvre ce cas,
c'est la raison pour laquelle les deux existent.

---

### 3.8 Textes affichés

Liste fermée des chaînes de l'interface. Toutes traduisibles. Toute chaîne
visible absente de cette liste est une chaîne à ajouter ici d'abord.

| Emplacement | Texte |
|---|---|
| Entrée de navigation | `Day`, `Reserve`, `Recurring` |
| Menu principal | `Archives`, `Statistics`, `Keyboard Shortcuts`, `About Rature` |
| Saisie du jour | `Add a task…` |
| Saisie de la réserve | `Add to the reserve…` |
| Recherche dans les archives | `Search the archives…` |
| Menu de ligne | `Rename`, `Edit`, `Delete` |
| Infobulle de rature | `Strike through`, `Undo the strike` |
| Infobulle d'annulation de suppression | `Undo delete` |
| Infobulle de copie | `Copy as text` |
| Fenêtre des raccourcis, titres de groupe | `General`, `Navigation`, `Tasks` |
| Fenêtre des raccourcis, descriptions | `Quit`, `Keyboard Shortcuts`, `Show the Day view`, `Show the Reserve view`, `Show the Recurring view`, `Add a task`, `Add a task already struck`, `Undo the last deletion`, `Cancel an edit` |
| Infobulle d'envoi | `Send to the day` |
| Infobulle de verrou | `Freeze the list`, `Unfreeze the list` |
| Infobulle d'ajout de récurrente | `Add a recurring task` |
| Formulaire récurrent | `Recurring task`, `Task text`, `Days`, `Cancel`, `Save` |
| Vue Jour vide | `The list is empty.` |
| Réserve vide | `The reserve is empty.` |
| Récurrentes vides | `No recurring tasks.` |
| Archives vides | `No archived days.` |
| Archives sans correspondance | `No matching days.` |
| Archive illisible | `This archive cannot be read.` |
| Fenêtre Statistiques, en-têtes de colonne | `Day`, `Added`, `Struck`, `Deleted`, `To reserve` |
| Fenêtre Statistiques, ligne de total | `Total` |
| Bannière de quarantaine | `The data file could not be read. It was moved aside as %s.` |
| Bannière d'écriture | `Changes could not be saved to disk.` |
| Bannière de nouveau jour | `A new day has started. The previous one has been archived.` |
| Bouton de fermeture de bannière | `Dismiss` |
| Alerte version future | `This file was saved by a newer version of Rature.`, `Opening it could overwrite data. Update Rature to open this file: %s`, `Quit` |

Aucun de ces textes ne félicite, n'encourage, ne compte ni ne compare, §2.3.

Les noms de jours, dans le sous-titre des lignes récurrentes et sur les
bascules du formulaire, ne figurent pas dans cette liste : ils sont dérivés
de la locale par `strftime` (§3.4), n'entrent jamais au catalogue et sont
donc corrects dans toutes les langues sans traduction à écrire.

---

### 3.9 Icônes

Noms symboliques du thème Adwaita. **À vérifier un par un dans le thème du
runtime au moment de l'implémentation** : une icône absente s'affiche en
image cassée, et ça ne se voit qu'à l'exécution.

| Rôle | Nom |
|---|---|
| Rayer | `object-select-symbolic` |
| Dérayer | `edit-undo-symbolic` |
| Annuler la dernière suppression | `document-revert-symbolic` |
| Copier la journée en texte | `edit-copy-symbolic` |
| Menu de ligne | `view-more-symbolic` |
| Menu principal | `open-menu-symbolic` |
| Supprimer | `user-trash-symbolic` |
| Renommer | `document-edit-symbolic` |
| Envoyer au jour | `go-next-symbolic` |
| Figer | `changes-prevent-symbolic` |
| Déverrouiller | `changes-allow-symbolic` |
| Ajouter une récurrente | `list-add-symbolic` |

---

### 3.10 Ce que l'interface ne contient pas au chantier 3

Rappel de périmètre, `CLAUDE.md` §4 règle 4.

- Aucun raccourci clavier hors Entrée, Échap et `<primary>q` déjà en place
- Aucune annulation de suppression
- Aucune recherche, aucun export
- Aucune fenêtre de statistiques
- Aucune préférence, aucun écran de réglages
- Aucun ajout direct d'une tâche déjà rayée

---

### 3.11 Raccourcis clavier et fenêtre d'aide

Ajouté au chantier 4. Le jeu se limite à des raccourcis à convention forte ;
rien de propre à l'application au-delà de ce qui existait déjà.

**Accélérateurs.**

| Raccourci | Action | État |
|---|---|---|
| `Entrée` | Ajouter une tâche | déjà en place, §3.2 |
| `Maj+Entrée` | Ajouter une tâche déjà rayée | déjà en place, §3.2 |
| `Échap` | Annuler un renommage en cours | déjà en place, §3.2 |
| `Ctrl+Q` | Quitter | déjà en place |
| `Ctrl+Z` | Annuler la dernière suppression | nouveau, déclenche l'action de §3.2 |
| `Ctrl+1`, `Ctrl+2`, `Ctrl+3` | Aller à Day, Reserve, Recurring | nouveau |
| `Ctrl+?`, `F1` | Ouvrir la fenêtre d'aide | nouveau |

Rien pour figer la liste ni pour rayer une tâche : aucune touche standard, et
§2.3 veut que la suppression comme la rature restent des gestes explicites, à
la souris ou au menu. `Ctrl+1/2/3` changent seulement la vue affichée, sans
rien sélectionner dans les listes.

**Fenêtre d'aide.** Un `AdwShortcutsDialog` chargé depuis un `.ui`, ouvert
par `present`. `GtkShortcutsWindow` est écarté : déprécié depuis GTK 4.18,
et `CLAUDE.md` §9 impose les API stables. `set_help_overlay` n'acceptant
qu'un `GtkShortcutsWindow`, l'action `win.show-help-overlay` et ses
accélérateurs `Ctrl+?` et `F1` sont posés à la main. Trois sections :

- **General** : Quitter, Keyboard Shortcuts
- **Navigation** : les trois vues
- **Tasks** : Ajouter une tâche, Ajouter une tâche déjà rayée, Annuler la
  dernière suppression, Annuler un renommage

Le contenu est entièrement déclaratif, sans logique. L'entrée Keyboard
Shortcuts du menu principal déclenche la même action `win.show-help-overlay`.
Tous les libellés affichés sont en §3.8.

---

### 3.12 Export d'une journée en texte

Ajouté au chantier 4. Un bouton Copy as text (`edit-copy-symbolic`, §3.9)
dans l'en-tête de la vue Jour et dans l'en-tête de la fenêtre d'archives
copie la journée affichée dans le presse-papier, en texte brut. Aucun
fichier, aucun dialogue, aucun retour visible : le style du reste de
l'interface, où l'annulation comme l'ajout ne confirment rien.

- Vue Jour : la journée en cours. Le bouton reste actif même sur une journée
  vide.
- Fenêtre d'archives : la date sélectionnée. Inactif tant qu'aucune date
  lisible n'est affichée.

**Format.**

```
Monday 31 August

[x] 1  finish the meson file
[x] 3  answer Marie
[ ] 2  call the dentist
[ ] 5  take out the bin
```

- Première ligne : la date, format long local, comme le titre de l'en-tête
  du Jour.
- Une ligne vide, puis une ligne par tâche dans l'ordre de `Session.view()`
  (les rayées d'abord, comme à l'écran).
- `[x]` si la tâche est rayée, `[ ]` sinon ; puis le numéro ; puis le texte.
  Deux espaces entre le numéro et le texte. Le numéro n'est ni aligné ni
  recalculé (§2.4).
- Une tâche supprimée n'apparaît jamais, §2.2. Le journal `deletions` non
  plus.
- Journée vide : la date seule, sans ligne vide ni corps.
- Pas de saut de ligne final.

Côté `core`, une fonction pure `day_text(session)` produit ce texte.
`App.day_text` et `App.archived_day_text(date)` l'exposent à l'interface, qui
ne fait que l'écrire dans le presse-papier.

---

### 3.13 Recherche dans les archives

Ajoutée au chantier 4. Un `GtkSearchEntry` en tête de la barre latérale de la
fenêtre d'archives (§3.5), texte d'invite en §3.8. Il **filtre la liste des
dates** : ne restent affichées que les journées contenant au moins une tâche,
rayée ou en cours, dont le texte correspond à la requête. L'ordre est celui
d'`App.archives()`, du plus récent au plus ancien, jamais retrié. Rien
d'autre ne change dans la barre latérale : pas de compteur, pas d'aperçu,
pas de résumé à côté d'une date, §3.5 reste vrai.

**Correspondance.** Sous-chaîne, insensible à la casse **et aux accents**.
Les deux côtés sont normalisés de la même façon : décomposition Unicode NFKD,
retrait des marques diacritiques, puis `casefold`. Taper `reparer` trouve
donc `réparer`. La requête est débarrassée de ses espaces de début et de fin
avant comparaison. C'est un écart assumé avec le dédoublonnage du passage du
jour (§2.5 point 3, « accents conservés ») : une recherche tolère l'à-peu-près,
un dédoublonnage non.

**Périmètre.** Seul le texte des tâches est recherché. Jamais la date, jamais
le journal `deletions` : §2.2 et §2.6 interdisent d'exposer son contenu sous
quelque forme que ce soit, recherche comprise. Une tâche supprimée n'est donc
jamais trouvée.

**Requête vide.** Toutes les dates, exactement le comportement d'avant la
fonctionnalité, journaux illisibles compris.

**Zéro résultat.** La barre latérale affiche un `AdwStatusPage`, texte
`No matching days.` en §3.8. Le panneau de contenu est vidé, aucune journée
n'est montrée, et le bouton Copy as text redevient inactif (§3.12).

**Sélection.** Après application du filtre, si la date affichée figure encore
dans la liste réduite elle reste sélectionnée ; sinon la première date
restante est sélectionnée et affichée. Quand la requête est effacée, la liste
complète revient et la date affichée, s'il y en a une, reste sélectionnée.

**Au fil de la frappe.** Le filtre s'applique à chaque modification de la
zone de saisie, après un court délai anti-rebond. La fenêtre garde en mémoire
les archives déjà analysées pour toute sa durée de vie, afin de ne pas
relire chaque fichier à chaque caractère. La fenêtre étant reconstruite à
chaque ouverture (§3.5), ce cache ne survit jamais à une modification du
dossier d'archives.

**Archive illisible.** Une archive qui ne se lit pas ne peut pas être
comparée : elle est absente des résultats dès qu'une requête est saisie. Elle
n'apparaît que dans la liste non filtrée, où la sélectionner affiche le texte
neutre prévu en §3.5. Une archive illisible ne fait jamais échouer la
recherche entière.

**Pas de mise en évidence.** Le panneau de contenu rend la journée comme en
§3.5, sans marquer les tâches qui correspondent. La date filtrée suffit à
indiquer où regarder.

**Lecture seule.** Comme le reste de la fenêtre, la recherche ne modifie rien
sur le disque.

Côté `core`, une fonction pure travaille sur le contenu des archives.
`App.search_archives(query)` rend les dates correspondantes, du plus récent
au plus ancien, dans le même ordre qu'`App.archives()`. Une requête vide ou
uniquement composée d'espaces rend la même liste qu'`App.archives()`.

---

### 3.14 Fenêtre Statistiques

Ajoutée au chantier 4. Périmètre produit en §2.6 : lecture seule, sur les
archives, **rien que des nombres, aucune appréciation**. Cette section fixe
la forme.

Fenêtre distincte, un `AdwWindow` comme la fenêtre d'archives, ouverte depuis
l'entrée Statistics du menu principal (§3.1). Rien n'y est modifiable, aucun
bouton d'action, aucun contrôle : pas de sélecteur de période, pas de
graphique, pas de couleur qui distingue une valeur d'une autre. Un tableau,
et c'est tout. La période, c'est l'ensemble des archives ; la répartition
dans le temps, ce sont les lignes ; le « par période » de §2.6, c'est la
ligne de total.

**Le tableau.** Une ligne par journée archivée, du plus récent au plus
ancien, exactement l'ordre d'`App.archives()`. Cinq colonnes, en-têtes en
§3.8 :

```
┌────────────────┬───────┬────────┬─────────┬────────────┐
│ Day            │ Added │ Struck │ Deleted │ To reserve │
├────────────────┼───────┼────────┼─────────┼────────────┤
│ 30 August 2026 │   7   │   5    │    1    │     2      │
│ 29 August 2026 │   4   │   4    │    0    │     0      │
│ 28 August 2026 │   9   │   6    │    2    │     1      │
├────────────────┼───────┼────────┼─────────┼────────────┤
│ Total          │  20   │   15   │    3    │     3      │
└────────────────┴───────┴────────┴─────────┴────────────┘
```

- **Day** : la date de la journée, format long local, comme le titre de la
  vue Jour et de la fenêtre d'archives.
- **Added** : `len(day.tasks) + len(day.deletions)`, c'est à dire toute
  tâche ayant reçu un numéro ce jour-là, égal à `day.counter - 1`. Le
  journal `deletions` n'est utilisé que pour son **nombre d'entrées**,
  jamais pour leur texte (§2.2, §2.6).
- **Struck** : les tâches `done` de la journée archivée. Une tâche rayée
  puis supprimée ne compte pas ici : elle a disparu de la journée
  archivée (§3.5) et n'est comptée que dans Deleted.
- **Deleted** : `len(day.deletions)`.
- **To reserve** : les tâches de la journée archivée qui ne sont ni faites
  ni issues d'une récurrente. C'est ce que le passage du jour renvoie en
  réserve (§2.5 points 2 et 3), **avant** son dédoublonnage. Le nombre
  exact déplacé n'est pas dans l'archive : elle est écrite avant le
  déplacement, et le dédoublonnage n'y laisse pas de trace. Ce comptage
  peut donc dépasser d'une unité ou deux le nombre réellement ajouté à la
  réserve, uniquement quand deux textes identiques y coexistaient. Écart
  assumé : §2.6 demande des nombres, pas une comptabilité au corps près.

Les cinq colonnes sont des comptages **indépendants**. Elles ne se
partitionnent pas : `Added` n'est pas la somme des autres, et `To reserve`
recoupe les tâches non rayées.

**Ligne de total.** Une dernière ligne `Total` (§3.8) somme chaque colonne
sur toutes les journées listées. Aucune moyenne, aucun ratio, aucune
projection : §2.6 interdit toute valeur présentée comme un objectif.

**Archive illisible.** Ignorée, silencieusement, comme pour la recherche
(§3.13) : elle n'a pas de ligne et n'entre dans aucun total. Une archive
qui ne se lit pas ne fait jamais échouer la fenêtre entière.

**Aucune archive.** Un `AdwStatusPage`, texte `No archived days.` (§3.8),
à la place du tableau.

**Rien n'est poussé.** La fenêtre ne s'ouvre que sur action de
l'utilisateur, ne notifie jamais, ne se rouvre pas seule, et n'apparaît
dans aucune autre vue. §2.6 : un chiffre qu'on va chercher est une
consultation ; poussé, il devient un commentaire.

Côté `core`, une fonction pure `day_counts(day)` rend les quatre nombres
d'une journée (un petit dataclass de compteurs). `App.statistics()` les
expose à l'interface sous la forme d'une liste `(date, compteurs)` du plus
récent au plus ancien, dans le même ordre qu'`App.archives()`, les archives
illisibles omises. Les totaux se somment dans l'interface, ils n'ont pas
besoin de `core`.
