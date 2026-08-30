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
