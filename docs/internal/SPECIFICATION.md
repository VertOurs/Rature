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
3. La liste peut être figée. Une liste figée bloque l'ajout d'une tâche,
   le tirage depuis la réserve et le retour d'une tâche de Demain
   (§2.5). Rayer, dérayer, renommer, marquer ou
   retirer la priorité, supprimer et réordonner restent possibles. Figer arrête la composition de la journée,
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
- Le numéro d'une tâche est une étiquette attribuée à son entrée dans la
  journée : à l'ajout, au tirage depuis la réserve, au retour depuis Demain
  ou au passage du jour pour une tâche préparée (§2.5). Une tâche de Demain
  n'a pas de numéro. Il ne change jamais, ni à la rature, ni à la suppression, ni au réordonnancement, ni au
  passage d'une tâche dans le bloc « Rayées »
- L'ordre d'affichage est indépendant du numéro. Une liste réordonnée peut
  très bien afficher 3, 1, 7. C'est voulu
- Un numéro libéré par une suppression n'est jamais réattribué dans la
  journée
- Rien n'est perdu au passage d'une journée à l'autre, liste préparée
  dans Demain comprise

### 2.5 Réserve et récurrentes

**Réserve** : liste mère sans date. Tout ce qui traîne. On y puise le matin,
elle n'est jamais affichée mélangée à la liste du jour.

**Ordre de la réserve** : celui de la liste, sans tri. Un ajout, un renvoi
manuel et un retour au passage du jour vont en fin de réserve. Au passage
du jour, les tâches non faites y arrivent en deux groupes : d'abord celles
issues de la réserve (point 2 ci-dessous), puis celles créées dans le jour
(point 3), chaque groupe dans l'ordre de la liste du jour, réordonnancement
compris. L'utilisateur peut réordonner les items à la main (§3.3) ; rien
d'autre ne déplace un item. Ajouté au chantier 7.2.

**Tirage depuis la réserve** : c'est un déplacement, jamais une copie.
L'item quitte la réserve au moment du tirage. La tâche créée conserve dans
`source_id` l'identifiant de l'item d'origine. Si elle n'est pas faite, elle
retourne en réserve au passage du jour, par son `source_id`.

**Renvoi manuel en réserve** : l'inverse du tirage, à la demande, sans
attendre le passage du jour. C'est aussi un déplacement : la tâche quitte la
journée et rejoint la fin de la réserve. Ajouté au chantier 7.2.

- une tâche issue de la réserve y retourne comme au passage du jour (point 2
  ci-dessous) : même `id` d'item, même `created`, texte renommé compris
  (§2.7.1)
- une tâche créée dans le jour devient un item neuf, daté du jour de
  référence. Aucun dédoublonnage : le geste est explicite, comme un ajout
  manuel (§2.7.4)
- une tâche issue d'une récurrente ne peut pas être renvoyée. Le passage du
  jour l'abandonne (point 4), elle reviendra d'elle-même ; la renvoyer en
  ferait un doublon de son propre modèle
- une tâche rayée ne peut pas être renvoyée : elle est faite
- autorisé sur une liste figée. Figer arrête la composition de la journée,
  pas son déroulement (§2.1 point 3), et retirer une tâche reste possible,
  comme la supprimer

Le numéro de la tâche n'est jamais réattribué, le compteur ne recule pas
(§2.4). La tâche ne laisse aucune trace dans la journée : elle n'est ni dans
l'archive, ni dans le journal de suppressions, donc absente des comptages de
§2.6, comme si elle n'avait jamais été tirée. Aucune annulation : le geste
inverse est le tirage.

**Priorité** : un seul niveau, une tâche du jour ou un item de réserve est
prioritaire ou ne l'est pas (`priority`, faux par défaut). C'est un
marqueur visuel, rien d'autre : il ne change **ni l'ordre d'affichage, ni
les numéros**, dans aucune vue. Ajouté au chantier 7.2.

La priorité suit la tâche partout, rien ne se perd :

- tirage depuis la réserve, renvoi manuel, retour au passage du jour
  (point 2 ci-dessous) : la priorité passe de l'item à la tâche et
  inversement, comme le texte renommé (§2.7.1)
- une tâche créée dans le jour qui part en réserve (renvoi manuel ou
  point 3) : l'item neuf garde sa priorité
- une tâche écartée comme doublon au passage du jour transmet sa priorité
  à l'item qui la remplace (§2.7.8)
- suppression puis annulation : la priorité est restaurée avec la tâche

Une tâche issue d'une récurrente peut être marquée, comme toute tâche du
jour ; elle est abandonnée au passage du jour avec sa priorité (point 4).
Les modèles récurrents n'ont pas de priorité. La priorité n'apparaît ni
dans les statistiques (§2.6), ni dans la copie texte (§3.12), ni dans la
fenêtre d'archives (§3.5) ; la donnée reste conservée dans les archives.

**Récurrentes** : modèles de tâches associés à des jours de la semaine,
injectés automatiquement au passage à une nouvelle journée.

**Récurrente une semaine sur deux** : un modèle peut ne valoir qu'une
semaine sur deux. Il porte alors, en plus de ses jours, le lundi d'une
semaine active (`every_other_week_from`). Absent (`null`), le modèle vaut
chaque semaine, comme avant. Un modèle est dû à la date D si le jour de D
fait partie de ses jours et, s'il est une semaine sur deux, si le nombre de
semaines entre ce lundi et le lundi de D est pair (§2.7.7). L'utilisateur ne
saisit jamais de date : il choisit « cette semaine » ou « la semaine
prochaine » comme semaine active, `core` en déduit le lundi à partir de la
date de référence. Ajouté au chantier 7, hors des cases prévues, sur
décision de VertOurs.

**Demain** : la liste préparée pour la prochaine journée qui démarrera.
Demain n'est pas une date : après plusieurs jours sans ouverture, la liste
préparée devient quand même la liste du jour qui s'ouvre (point 7
ci-dessous). Décision et alternatives écartées :
`docs/adr/0008-prepare-tomorrow.md`. Ajouté au chantier 7.3.

- **Une tâche préparée** porte un identifiant, un texte, une origine, la
  trace de son item de réserve (`source_id`, `source_created`) et sa
  priorité. Pas de numéro, pas de rature : on ne raye pas dans Demain.
  L'origine est celle du jour (`day`) pour une tâche ajoutée dans Demain,
  celle de la réserve pour un item tiré, jamais celle d'une récurrente
- **On y ajoute, renomme, réordonne, supprime, marque ou retire la
  priorité.** Un ajout va en fin de liste. Aucun dédoublonnage, nulle
  part : chaque entrée dans Demain est un geste explicite (§2.7.4)
- **Demain n'a pas de verrou**, et figer la journée ne la concerne pas
  (§2.1 point 3)
- **Supprimer dans Demain est définitif** (§2.7.9)

Trois gestes y font entrer une tâche, chacun en fin de liste. Le même
libellé, `Move to tomorrow`, les désigne depuis le jour et depuis la
réserve (§3.8).

- **Depuis la réserve** : un déplacement, comme le tirage vers le jour.
  L'item quitte la réserve, la tâche préparée garde son `id` dans
  `source_id`, sa date dans `source_created`, son texte et sa priorité.
  Autorisé sur une journée figée, qui ne concerne pas Demain
- **Depuis le jour** : décaler une tâche en cours. La tâche garde son
  `id`, son origine, `source_id`, `source_created` et sa priorité, et perd
  son numéro. Mêmes restrictions que le renvoi manuel en réserve : ni une
  tâche rayée, ni une tâche issue d'une récurrente. Autorisé sur une liste
  figée. Comme le renvoi, aucune trace dans la journée : ni archive, ni
  journal, numéro jamais réattribué, absente des comptages de §2.6
- **Ajout direct** dans la vue Demain (§3.16)

Deux gestes l'en font sortir avant le passage du jour :

- **Retour vers le jour** (`Move to today`) : la tâche entre dans la
  journée en fin de liste et reçoit le numéro suivant, comme un tirage. Elle
  garde son `id`, son origine, sa trace de réserve et sa priorité. Refusé
  sur une liste figée, comme le tirage. C'est le geste qui défait un
  décalage par erreur, faute d'annulation
- **Renvoi en réserve** : mêmes règles que le renvoi depuis le jour. Une
  tâche issue de la réserve y retourne sous son `id` d'item et sa date
  d'origine ; une tâche créée dans le jour ou dans Demain devient un item
  neuf, daté du jour de référence, sans dédoublonnage

Une tâche tirée de la réserve vers Demain qui n'est pas faite le lendemain
retourne en réserve au passage du jour suivant, par son `source_id`, comme
toute tâche tirée (point 2).

**Récurrentes affichées dans Demain** : celles qui sont dues à la date de
référence plus un jour, parité comprise (§2.7.7), dans l'ordre où le passage
du jour les injecterait. En lecture seule : aucune action sur elles depuis
Demain. Limite acceptée : après plusieurs jours sans ouverture, le passage
du jour injecte les récurrentes de la date qui s'ouvre réellement, qui
peuvent différer de celles affichées la veille. L'affichage est une
indication, la règle reste le point 6.

**Ce que Demain ne touche pas** : ni les statistiques (§2.6), ni la copie
texte (§3.12), ni les archives. La liste vit dans le fichier principal
seulement. Une tâche préparée n'apparaît dans une archive qu'une fois entrée
dans une journée.

**Format** : version 4. Le fichier principal gagne une clé `tomorrow`, liste
ordonnée de tâches préparées (`PreparedTask` : `id`, `text`, `origin`,
`source_id`, `source_created`, `priority`). La migration 3 → 4 ajoute
`"tomorrow": []` au fichier principal ; un fichier d'archive ne change que
de numéro de version. Testée sur des fichiers v3 principal et archive
fabriqués, et sur la chaîne depuis la version 1 (`CLAUDE.md` §4 règle 7).

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
7. Les tâches préparées dans Demain entrent dans la journée, dans leur
   ordre, à la suite des récurrentes, comme si elles avaient été dictées en
   début de journée. Elles reçoivent leurs numéros à ce moment-là et
   gardent leur `id`, leur origine, leur trace de réserve et leur priorité.
   Demain se vide. Ajouté au chantier 7.3

Si plusieurs jours se sont écoulés depuis la dernière ouverture, le passage
du jour ne s'exécute qu'une fois. La journée enregistrée est archivée sous sa
propre date. Les jours intermédiaires n'existent pas, ils ne sont ni
archivés, ni peuplés. Seules les récurrentes du jour courant sont injectées,
puis la liste préparée, une seule fois, dans la journée qui s'ouvre.

Aucune donnée n'est perdue lors d'un passage de jour, liste préparée
comprise. C'est cette garantie
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

Demain n'est jamais compté. Une tâche préparée n'est comptée qu'une fois
entrée dans une journée, comme ajoutée ce jour-là. Une tâche décalée du jour
vers Demain n'y laisse aucune trace, comme un renvoi en réserve. Ajouté au
chantier 7.3.

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

**2.7.7 Parité d'une récurrente une semaine sur deux**

Ajouté le 12 octobre 2026. La parité se compte en semaines écoulées depuis
le lundi stocké dans `every_other_week_from`, jamais par le numéro de
semaine ISO.

Une année ISO compte parfois 53 semaines : 2026 en compte 53. Les semaines
53 de 2026 et 1 de 2027 se suivent et sont toutes deux impaires. Une parité
ISO injecterait la même récurrente deux semaines de suite, puis l'oublierait
deux semaines de suite pour l'autre groupe. Le compte depuis un lundi fixe
ne connaît pas l'année et alterne sans exception.

Conséquences :

- `core` refuse un `every_other_week_from` qui n'est pas un lundi
- le lundi est calculé dans `core`, à partir de la date de référence
  (bascule 04:00, §2.5), jamais dans l'interface. Un dimanche à 02:00
  appartient encore à la semaine qui finit
- modifier le seul texte ou les seuls jours d'une récurrente ne décale pas
  ses semaines. Choisir de nouveau la semaine déjà active n'y change rien
  non plus : le lundi stocké est conservé
- une modification n'a jamais d'effet rétroactif sur la journée en cours :
  l'injection n'a lieu qu'au passage du jour, comme pour toute récurrente
- si plusieurs jours se sont écoulés, seules les récurrentes dues à la date
  de référence sont injectées (§2.5), la parité ne change rien à cette règle

Le choix transmis par l'interface a trois valeurs explicites, une par état
du formulaire : chaque semaine (case décochée), une semaine sur deux active
cette semaine, une semaine sur deux active la semaine prochaine. Repasser
une récurrente en hebdomadaire est donc possible : son
`every_other_week_from` redevient `null`.

**Limite acceptée** : un formulaire laissé ouvert pendant la bascule du
lundi 04:00 interprète le choix avec la nouvelle semaine. « This week »
désigne alors la semaine qui vient de commencer. Aucun code ne le corrige :
le cas demande de garder le formulaire ouvert pendant la nuit du dimanche
au lundi, et le sous-titre de la ligne montre le résultat dès
l'enregistrement.

**2.7.8 Priorité d'une tâche écartée comme doublon**

Ajouté le 12 octobre 2026, au chantier 7.2. Au passage du jour, une tâche
non faite créée dans le jour n'entre pas en réserve si son texte y figure
déjà (§2.5 point 3). Si cette tâche écartée était prioritaire, **l'item
existant devient prioritaire**. Un item déjà prioritaire le reste : le
doublon ne retire jamais une priorité.

L'item existant est celui que la comparaison de §2.5 point 3 a trouvé,
qu'il soit en réserve depuis longtemps, revenu au point 2 ou ajouté au même
passage du jour par une autre tâche du jour au texte identique.

Motif : la priorité est une information que l'utilisateur a posée. Écarter
le doublon sans la reporter la perdrait silencieusement, ce qui contredit la
garantie « aucune donnée n'est perdue » de §2.5.

**2.7.9 Suppression dans Demain**

Ajouté le 12 octobre 2026, au chantier 7.3. Supprimer une tâche de Demain
est **définitif** : aucune entrée de journal, aucune annulation.

Le journal de suppressions appartient à la journée (§2.2, ADR 0005) : il
part avec son archive et ne sert qu'au comptage de §2.6, qui ne voit pas
Demain. Y inscrire une tâche qui n'a jamais été dans une journée fausserait
ce comptage, et l'annulation de §3.2 restaure dans la journée, pas dans
Demain.

Comme en §2.7.3, supprimer une tâche préparée tirée de la réserve détruit
définitivement l'item d'origine. La protection reste celle de §3.2 : la
suppression est une entrée de menu, jamais un bouton de ligne, et §2.3
interdit la confirmation.

**2.7.10 Sauvegarde avant migration**

Ajouté le 30 octobre 2026, au chantier 9. Quand le chargement du fichier
principal applique au moins une migration, une copie du fichier d'origine
est faite avant toute écriture du fichier principal.

- **Nom** : `data.json.v<N>.bak`, dans le dossier de données, où `<N>` est
  la version **lue sur le disque**, avant migration. Un fichier en version 4
  migré vers 5 laisse `data.json.v4.bak`.
- **Contenu** : copie octet pour octet du fichier tel qu'il était sur le
  disque, jamais une réécriture du contenu chargé. Mêmes permissions que le
  fichier principal (`0o600`, ADR 0003, addendum).
- **Une seule fois** : tant que le fichier principal n'a pas été réécrit, il
  reste dans son ancienne version et chaque lancement le migre de nouveau en
  mémoire. Si `data.json.v<N>.bak` existe déjà, il n'est ni écrasé ni
  doublé : la sauvegarde la plus ancienne est la vraie copie d'origine.
- **Jamais supprimée** par l'application. Elle reste à la charge de
  l'utilisateur, comme les fichiers mis en quarantaine.
- **Échec de la copie** : aucune donnée migrée n'est écrite sans
  sauvegarde. L'échec remonte de `App.open` comme une `OSError` au
  démarrage et suit le traitement de §3.6.
- **Rien dans l'interface** : ni bannière ni message. La sauvegarde est
  journalisée au niveau `INFO`, avec son chemin et jamais son contenu.
- **Archives non concernées** : un fichier d'archive est migré en mémoire à
  la lecture et n'est jamais réécrit ensuite. Il reste sur le disque dans
  sa version d'origine.

Motif : une migration ratée détruit des données (`CLAUDE.md` §4 règle 7).
Jusqu'ici, la sauvegarde avant une mise à jour dépendait de l'utilisateur ;
elle devient automatique.

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
`AdwNavigationSplitView`. Le panneau latéral porte quatre entrées, dans cet
ordre : Day, Tomorrow, Reserve, Recurring. Chaque entrée affiche sa vue dans
le panneau de contenu. Tomorrow rejoint le panneau au chantier 7.3, juste
après Day (§3.16).

Les archives ne sont pas une entrée du panneau. Elles s'ouvrent depuis le
menu principal, dans une fenêtre distincte, voir §3.5.

```
┌──────────────────────────────┬──────────────────────────────────────────┐
│ Rature                    ⋮  │  Monday 31 August                     🔒 │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Day                         │  ┌────────────────────────────────────┐  │
│  Tomorrow                    │  │  2   call the dentist       ↺   ⋮  │  │
│  Reserve                     │  │  5   take out the bin       ↺   ⋮  │  │
│  Recurring                   │  └────────────────────────────────────┘  │
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
appelle `App.ensure_day`. Si elle rend une journée, toutes les vues se
rafraîchissent et une bannière neutre l'annonce, voir §3.8. La bannière ne
change pas avec Demain : elle ne dit rien de la liste préparée entrée dans
la journée. Un délai fixe et
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
│  ←   12   text of the task                     ✓    ★    ⋮   │
└──────────────────────────────────────────────────────────────┘
   │    │     │                                  │    │    │
   │    │     │                                  │    │    └ menu de ligne
   │    │     │                                  │    └ priorité, §2.5
   │    │     │                                  └ rayer ou dérayer
   │    │     └ texte, barré si la tâche est rayée
   │    └ numéro, chiffres tabulaires, atténué, jamais recalculé
   └ renvoyer en réserve, absent sur une rayée ou une récurrente
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

**Renvoyer en réserve.** Ajouté au chantier 7.2. Un bouton plat (`←`), tout
à gauche de la ligne, avant le numéro, appelle `send_to_reserve`. La ligne
disparaît de la journée et réapparaît en fin de réserve, règles en §2.5. Le
bouton n'existe que sur une tâche en cours qui n'est pas issue d'une
récurrente : il est masqué, pas insensible, sur les autres, puisqu'aucun
état ne le rendra jamais utilisable. Il reste actif sur une liste figée.
Aucun retour visuel au-delà du déplacement, §2.3.

**Renvoyer par glisser-déposer.** Ajouté au chantier 7.2. Une ligne de la
vue Jour, déjà source de glissement pour le réordonnancement, peut aussi
être déposée sur l'entrée Reserve du panneau latéral. Le dépôt et le bouton
`←` appellent **la même méthode de la fenêtre**, jamais deux chemins
parallèles, comme en §3.3. La cible refuse le dépôt et ne s'illumine pas
quand le bouton serait absent : tâche rayée ou issue d'une récurrente. Elle
l'accepte sur une liste figée, comme le bouton. Indisponible en mode
replié, l'entrée n'étant pas à l'écran ; le bouton couvre ce cas (§3.7).

**Menu de ligne.** Rename, puis Delete au chantier 3. Depuis le
chantier 7.2 : Rename, `Mark as priority` ou `Remove priority` selon l'état
de la tâche, puis Delete. Depuis le chantier 7.3, `Move to tomorrow` s'insère
avant Delete, qui reste la dernière entrée.

**Décaler vers Demain.** Ajouté au chantier 7.3, règles en §2.5. L'entrée
`Move to tomorrow` du menu, ou le dépôt de la ligne sur l'entrée Tomorrow du
panneau latéral, appellent **la même méthode de la fenêtre**. La ligne
disparaît de la journée et réapparaît en fin de Demain. L'entrée de menu
n'existe que là où le bouton `←` existe : tâche en cours, non issue d'une
récurrente. Elle est absente, pas insensible, sur les autres. La cible
refuse le dépôt et ne s'illumine pas dans les mêmes cas. Les deux restent
actifs sur une liste figée. Aucun retour visuel au-delà du déplacement,
§2.3.

**Priorité.** Ajouté au chantier 7.2, règles en §2.5. L'entrée du menu
marque ou retire la priorité, mêmes autorisations que le renommage : liste
figée et tâche rayée comprises (§2.1 point 3). Une tâche prioritaire porte
une icône symbolique discrète (§3.9), à droite, juste avant le bouton de
menu, dans la couleur d'accent du système, jamais en rouge. Nom accessible
et infobulle : `Priority`. Sur une tâche non prioritaire, l'emplacement
reste réservé mais vide : l'icône forme une colonne stable et ne décale ni
le texte ni les boutons. Ni l'ordre, ni le numéro, ni le bloc ne changent.
Aucun autre retour visuel, §2.3.

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
- le retour d'une tâche de Demain est refusé, menu et dépôt (§3.16)
- rayer, dérayer, renommer, marquer ou retirer la priorité, supprimer,
  annuler une suppression, réordonner, renvoyer en réserve et décaler vers
  Demain restent actifs

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
│  │  repair the bike light          →    ★   ⋮   │  │
│  │  call the insurance             →        ⋮   │  │
│  │  sort the photos                →        ⋮   │  │
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

**Menu de ligne** : Rename, `Mark as priority` ou `Remove priority` selon
l'état de l'item, `Move to tomorrow` depuis le chantier 7.3, puis Delete. Le
renommage est en place, comme en §3.2. La
priorité s'affiche comme en §3.2 : même icône, même colonne, juste avant le
bouton de menu. Marquer est autorisé sur une liste du jour figée, qui ne
concerne pas la réserve.

**Glisser-déposer.** Chaque ligne est une source de glissement portant
l'identifiant de l'item. La cible est l'entrée Day du panneau latéral. Le
dépôt et le bouton d'envoi appellent **la même méthode de la fenêtre**,
jamais deux chemins parallèles. Quand la liste du jour est figée, la cible
refuse le dépôt et ne s'illumine pas.

**Réordonner.** Ajouté au chantier 7.2. Le même glissement, déposé sur une
autre ligne de la réserve, déplace l'item, avec les règles de la vue Jour
(§3.2) : moitié haute de la ligne visée, l'item passe devant elle ; moitié
basse, devant la suivante, ou en fin de liste sur la dernière. Un dépôt sur
la ligne elle-même ne change rien. Une seule source de glissement par ligne,
plusieurs cibles : l'entrée Day tire l'item, une autre ligne le déplace,
l'entrée Tomorrow le prépare (ci-dessous). Autorisé sur une liste du jour figée, qui ne concerne pas la
réserve (§2.1 point 3).

**Préparer pour demain.** Ajouté au chantier 7.3, règles en §2.5. L'entrée
`Move to tomorrow` du menu, ou le dépôt de la ligne sur l'entrée Tomorrow du
panneau latéral, appellent **la même méthode de la fenêtre**. L'item quitte
la réserve et réapparaît en fin de Demain. Toujours disponible, y compris
sur une liste du jour figée : Demain n'a pas de verrou.

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
│  ├──────────────────────────────────────────────┤  │
│  │  swimming                                ⋮   │  │
│  │  Tue Thu · every two weeks · this week       │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

Une `AdwActionRow` par modèle : le texte en titre, les jours en sous-titre,
abrégés et dans l'ordre de la semaine, lundi premier. Pour une récurrente
une semaine sur deux (§2.5), le sous-titre ajoute `· every two weeks`
puis `· this week` si la semaine de la date de référence est active, sinon
`· next week`. Cette information vient de `core`, l'interface ne calcule
aucune parité. Pas de barre de saisie
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
│                                          │
│  [x] Every two weeks                     │
│  (This week)(Next week)                  │
└──────────────────────────────────────────┘
```

Sous les jours, une case à cocher `Every two weeks`, **décochée par
défaut** : pour une récurrente hebdomadaire, le formulaire se remplit
exactement comme avant. Cochée, elle révèle deux bascules exclusives,
`This week` et `Next week`, groupées et du même style que les jours,
`This week` active par défaut. Elles désignent la semaine active à partir de
la date de référence ; l'interface ne transmet que ce choix, `core` en
déduit le lundi (§2.7.7). Décochée, les deux bascules sont masquées et la
récurrente redevient hebdomadaire à l'enregistrement.

En édition d'une récurrente une semaine sur deux, la case est cochée et la
bascule présélectionnée est celle que `core` indique pour la date de
référence : `This week` si la semaine courante est active, sinon
`Next week`. Enregistrer sans y toucher ne décale donc pas les semaines.

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

Quatre situations, quatre traitements distincts. Aucune n'est un plantage.

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

**4. Dossier de données inutilisable au démarrage** (`OSError` levée par
`App.open`). Ajouté le 30 octobre 2026, au chantier 9. Couvre toute
`OSError` qui sort de `App.open` : fichier principal illisible faute de
permission, dossier impossible à créer, disque plein ou en lecture seule
au premier lancement, quarantaine impossible, sauvegarde avant migration
impossible (§2.7.10). Même traitement que la situation 1 : pas encore de
fenêtre, donc une `Gtk.AlertDialog` présentée sans parent, qui donne le
chemin du dossier de données, puis `quit`. Rien n'est écrit, rien n'est
réparé automatiquement : la cause est hors de l'application (droits,
place, support), seul l'utilisateur peut la corriger. L'exception
complète est journalisée au niveau `ERROR`.

Au passage du jour fait à l'ouverture, les deux écritures se distinguent.
L'archive de la journée écoulée qui ne peut pas s'écrire entre dans ce
cas : rien n'a encore été écrit, le passage sera rejoué au lancement
suivant. Le fichier principal qui ne peut pas s'écrire n'y entre pas :
`ensure_day` le rend comme `SAVE_FAILED`, l'archive est déjà sur le
disque, l'application démarre et la situation 3 s'applique.

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
c'est la raison pour laquelle les deux existent. Il en va de même, dans
l'autre sens, du dépôt d'une tâche du jour sur l'entrée Reserve et du
bouton de renvoi (§3.2).

Depuis le chantier 7.3, le panneau compte une entrée de plus, Tomorrow,
sans autre traitement particulier. Les dépôts sur l'entrée Tomorrow, depuis
le jour ou la réserve, et sur les entrées Day et Reserve depuis Demain, sont
indisponibles en mode replié pour la même raison ; les entrées
`Move to tomorrow` et `Move to today` des menus de ligne et le bouton `←`
couvrent ces cas.

---

### 3.8 Textes affichés

Liste fermée des chaînes de l'interface. Toutes traduisibles. Toute chaîne
visible absente de cette liste est une chaîne à ajouter ici d'abord.

| Emplacement | Texte |
|---|---|
| Entrée de navigation | `Day`, `Tomorrow`, `Reserve`, `Recurring` |
| Titre de la vue Demain | `Tomorrow` |
| Menu principal | `Archives`, `Statistics`, `Keyboard Shortcuts`, `About Rature` |
| Saisie du jour | `Add a task…` |
| Saisie de Demain | `Add a task for tomorrow…` |
| Saisie de la réserve | `Add to the reserve…` |
| Recherche dans les archives | `Search the archives…` |
| Menu de ligne | `Rename`, `Edit`, `Mark as priority`, `Remove priority`, `Move to tomorrow`, `Move to today`, `Delete` |
| Icône de priorité, nom accessible et infobulle | `Priority` |
| Infobulle de rature | `Strike through`, `Undo the strike` |
| Infobulle d'annulation de suppression | `Undo delete` |
| Infobulle de copie | `Copy as text` |
| Fenêtre des raccourcis, titres de groupe | `General`, `Navigation`, `Tasks` |
| Fenêtre des raccourcis, descriptions | `Quit`, `Keyboard Shortcuts`, `Show the Day view`, `Show the Tomorrow view`, `Show the Reserve view`, `Show the Recurring view`, `Add a task`, `Add a task already struck`, `Undo the last deletion`, `Cancel an edit` |
| Infobulle d'envoi | `Send to the day` |
| Infobulle de renvoi | `Send back to the reserve` |
| Infobulle de verrou | `Freeze the list`, `Unfreeze the list` |
| Infobulle d'ajout de récurrente | `Add a recurring task` |
| Menu principal, nom accessible et infobulle | `Main menu` |
| Menu de ligne, nom accessible et infobulle | `More options` |
| Formulaire récurrent | `Recurring task`, `Task text`, `Days`, `Every two weeks`, `This week`, `Next week`, `Cancel`, `Save` |
| Sous-titre de récurrente une semaine sur deux | `every two weeks`, `this week`, `next week` |
| Vue Jour vide | `The list is empty.` |
| Demain vide | `Nothing is prepared.` |
| Réserve vide | `The reserve is empty.` |
| Récurrentes vides | `No recurring tasks.` |
| Archives vides | `No archived days.` |
| Archives sans correspondance | `No matching days.` |
| Archive illisible | `This archive cannot be read.` |
| Fenêtre Statistiques, en-têtes de colonne | `Day` (contexte `statistics column`, distinct du `Day` de la navigation), `Added`, `Struck`, `Deleted`, `To reserve` |
| Fenêtre Statistiques, ligne de total | `Total` |
| Bannière de quarantaine | `The data file could not be read. It was moved aside as %s.` |
| Bannière d'écriture | `Changes could not be saved to disk.` |
| Bannière de nouveau jour | `A new day has started. The previous one has been archived.` |
| Bouton de fermeture de bannière | `Dismiss` |
| Alerte version future | `This file was saved by a newer version of Rature.`, `Opening it could overwrite data. Update Rature to open this file: %s`, `Quit` |
| Alerte dossier de données inutilisable | `Rature could not use its data folder.`, `Check that this folder can be read and written, and that the disk is not full: %s`, `Quit` |
| Format de la date longue (titres de la vue Jour et de la fenêtre d'archives, colonne Day des Statistiques, copie texte) | `%A %-d %B` |
| Format de la date avec année (barre latérale de la fenêtre d'archives) | `%-d %B %Y` |

Aucun de ces textes ne félicite, n'encourage, ne compte ni ne compare, §2.3.

**Noms accessibles.** Ajouté au chantier 8. Chaque bouton à icône seule
porte un nom accessible, lu par un lecteur d'écran : le texte de son
infobulle, ci-dessus. GTK expose l'infobulle comme description, pas comme
nom ; sans nom, le bouton n'est annoncé que par son rôle. Quand l'infobulle
change avec l'état du bouton (rature, verrou), le nom change avec elle. Le
bouton de menu de chaque ligne et celui du menu principal, qui n'avaient
aucun texte, reçoivent la même chaîne en infobulle et en nom. Aucune autre
chaîne n'est créée pour l'accessibilité.

Les noms de jours, dans le sous-titre des lignes récurrentes et sur les
bascules du formulaire, ne figurent pas dans cette liste : ils sont dérivés
de la locale par `strftime` (§3.4), n'entrent jamais au catalogue et sont
donc corrects dans toutes les langues sans traduction à écrire.

**Date longue.** Son format `strftime` passe en revanche par le catalogue,
avec un commentaire pour les traducteurs : `strftime` fournit les noms de
jour et de mois, mais l'ordre et les mots de liaison varient d'une langue à
l'autre (« jueves, 29 de octubre » en espagnol, `%A, %-d de %B`) ; le
français utilise `%A %-d %B`, sans zéro initial (« jeudi 5 novembre »). Ajouté au
chantier 8.4. Un seul format, partagé par toutes les dates longues ; la
barre latérale des archives a le sien, avec l'année et sans le jour de la
semaine (« 5 de octubre de 2026 »). Si la
locale de la langue de l'interface n'est pas installée, le format du
catalogue n'est pas appliqué : les noms resteraient dans une autre langue
(« Thursday, 29 de October »). La date garde alors le format source, sans
mots de liaison, dans une seule langue.

**Cohérence de langue.** Les noms de jours et les dates longues (titre de la
vue Jour, de la fenêtre d'archives, colonne Day des Statistiques) suivent la
même langue que l'interface, y compris sur une machine où `LANGUAGE` et
`LC_TIME` divergent : le lanceur réaligne `LC_TIME` sur la langue des
messages au démarrage. Si la locale correspondante n'est pas installée sur
la machine, la date peut rester dans une autre langue ; c'est une limite du
système, pas un choix de l'application.

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
| Renvoyer en réserve | `go-previous-symbolic` |
| Figer | `changes-prevent-symbolic` |
| Déverrouiller | `changes-allow-symbolic` |
| Ajouter une récurrente | `list-add-symbolic` |
| Priorité | `starred-symbolic` |

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
| `Ctrl+1`, `Ctrl+2`, `Ctrl+3`, `Ctrl+4` | Aller à Day, Tomorrow, Reserve, Recurring | `Ctrl+4` et décalage au chantier 7.3 |
| `Ctrl+?`, `F1` | Ouvrir la fenêtre d'aide | nouveau |

Rien pour figer la liste ni pour rayer une tâche : aucune touche standard, et
§2.3 veut que la suppression comme la rature restent des gestes explicites, à
la souris ou au menu. `Ctrl+1` à `Ctrl+4` changent seulement la vue
affichée, sans rien sélectionner dans les listes.

**Ordre du panneau.** Les chiffres suivent l'ordre des entrées du panneau
latéral (§3.1). Depuis le chantier 7.3, Tomorrow prend `Ctrl+2`, Reserve
passe de `Ctrl+2` à `Ctrl+3` et Recurring de `Ctrl+3` à `Ctrl+4`. C'est un
changement visible pour qui avait pris l'habitude des anciens chiffres : il
figure dans la rubrique « Changed » du `CHANGELOG.md` de la version qui le
livre.

**Fenêtre d'aide.** Un `AdwShortcutsDialog` chargé depuis un `.ui`, ouvert
par `present`. `GtkShortcutsWindow` est écarté : déprécié depuis GTK 4.18,
et `CLAUDE.md` §9 impose les API stables. `set_help_overlay` n'acceptant
qu'un `GtkShortcutsWindow`, l'action `win.show-help-overlay` et ses
accélérateurs `Ctrl+?` et `F1` sont posés à la main. Trois sections :

- **General** : Quitter, Keyboard Shortcuts
- **Navigation** : les quatre vues, dans l'ordre du panneau
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
┌────────────────────┬───────┬────────┬─────────┬────────────┐
│ Day                │ Added │ Struck │ Deleted │ To reserve │
├────────────────────┼───────┼────────┼─────────┼────────────┤
│ Sunday 30 August   │   7   │   5    │    1    │     2      │
│ Saturday 29 August │   4   │   4    │    0    │     0      │
│ Friday 28 August   │   9   │   6    │    2    │     1      │
├────────────────────┼───────┼────────┼─────────┼────────────┤
│ Total              │  20   │   15   │    3    │     3      │
└────────────────────┴───────┴────────┴─────────┴────────────┘
```

- **Day** : la date de la journée en format long local avec le jour de la
  semaine (format traduisible, §3.8), comme les titres d'en-tête de la vue Jour et de la
  fenêtre d'archives.
- **Added** : `len(day.tasks) + len(day.deletions)`, c'est à dire toute
  tâche ayant reçu un numéro ce jour-là et restée dans la journée,
  rayée, en cours ou supprimée. Ce n'est pas `day.counter - 1` : une tâche
  renvoyée en réserve (§2.5, chantier 7.2) ou décalée vers Demain
  (chantier 7.3) a consommé un numéro sans laisser de trace. Le
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

**Rafraîchissement.** Ajouté au chantier 8. Une fenêtre Statistiques
ouverte se reconstruit quand le passage du jour archive une journée,
détecté par la minuterie de §3.1 : la nouvelle ligne apparaît en tête et
la ligne de total suit. Une fenêtre qui affichait `No archived days.`
passe au tableau. C'est le seul événement qui change les archives pendant
que l'application tourne : rayer, dérayer, ajouter ou supprimer une tâche
ne touche que la journée en cours, que la fenêtre ne montre pas (§2.6).
Rien n'attire l'attention sur le changement : ni mise en évidence de la
nouvelle ligne, ni animation, ni retour en haut du défilement, ni
fenêtre ramenée au premier plan. La fenêtre reste exacte, elle ne
signale rien, conformément au paragraphe ci-dessus.

Côté `core`, une fonction pure `day_counts(day)` rend les quatre nombres
d'une journée (un petit dataclass de compteurs). `App.statistics()` les
expose à l'interface sous la forme d'une liste `(date, compteurs)` du plus
récent au plus ancien, dans le même ordre qu'`App.archives()`, les archives
illisibles omises. Les totaux se somment dans l'interface, ils n'ont pas
besoin de `core`.

---

### 3.16 Vue Demain

Ajoutée au chantier 7.3, règles produit en §2.5 et §2.7.9. Le numéro §3.15
n'est pas réutilisé : il désignait la boîte de dépôt, retirée, et
l'ADR 0007 le cite encore.

```
┌────────────────────────────────────────────────────┐
│  Tomorrow                                          │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │  water the plants                            │  │
│  │  weekly backup                               │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  ←   call the insurance              ★   ⋮   │  │
│  │  ←   book the train                      ⋮   │  │
│  └──────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│  [ Add a task for tomorrow…                     ]  │
└────────────────────────────────────────────────────┘
```

**Structure.** Même squelette que la vue Jour : `AdwToolbarView`, en-tête,
deux listes empilées dans un `GtkScrolledWindow`, barre de saisie en pied.
Le titre est `Tomorrow`, **sans date** : Demain n'est pas une date (§2.5).
L'en-tête ne porte aucun bouton : ni copie texte (§3.12), ni annulation de
suppression (§2.7.9), ni verrou, Demain n'en a pas.

**Récurrentes dues.** Le bloc du haut liste les récurrentes dues à la date
de référence plus un jour, dans l'ordre d'injection (§2.5). Lecture seule :
texte seul, sans numéro, sans bouton, sans menu, sans glissement. Ni cible
de dépôt, ni réordonnables. La liste vient de `core`, l'interface ne calcule
ni jour ni parité. Un bloc vide n'est pas affiché, comme en §3.2.

**Tâches préparées.** Le bloc du bas, dans l'ordre de la liste `tomorrow`.
Une ligne :

- `←` à gauche, renvoyer en réserve (§2.5), même bouton et même infobulle
  qu'en §3.2. Présent sur toutes les lignes : une tâche préparée n'est
  jamais rayée ni issue d'une récurrente. Le dépôt de la ligne sur l'entrée
  Reserve du panneau latéral appelle **la même méthode de la fenêtre** que
  le bouton, comme en §3.2. La cible l'accepte toujours
- **aucun numéro** et **aucun bouton de rature** (§2.4, §2.5)
- l'icône de priorité dans sa colonne, puis le menu de ligne, comme en §3.2

**Menu de ligne** : Rename, `Mark as priority` ou `Remove priority`,
`Move to today`, puis Delete. Le renommage est en place, comme en §3.2.
Delete est **définitif**, sans journal ni annulation (§2.7.9).

**Ramener dans la journée.** L'entrée `Move to today`, ou le dépôt de la
ligne sur l'entrée Day du panneau latéral, appellent **la même méthode de la
fenêtre**. La tâche entre en fin de journée avec le numéro suivant (§2.5).
Quand la liste du jour est figée, l'entrée de menu est insensible, et la
cible refuse le dépôt et ne s'illumine pas, comme pour un élément de réserve
(§3.3).

**Réordonner.** Glisser-déposer à l'intérieur du bloc des tâches préparées,
mêmes règles qu'en §3.2 et §3.3 : moitié haute, devant la ligne visée ;
moitié basse, devant la suivante ou en fin de liste. Toujours disponible.

**Ajouter.** `Add a task for tomorrow…` (§3.8). Mêmes règles que la vue
Jour : Entrée ajoute en fin de liste, la zone se vide, **garde le focus**,
et la liste défile jusqu'à la nouvelle tâche. Maj+Entrée ajoute
normalement : on ne raye pas dans Demain. Un texte vide après suppression
des espaces n'ajoute rien. Jamais insensible, figer la journée ne concerne
pas Demain.

**Annulation.** `Ctrl+Z` garde son effet de §3.11 depuis cette vue : il
restaure la dernière suppression de la journée, dans la journée. Il ne
restaure jamais une tâche supprimée dans Demain, qui n'a pas de journal.

**Vue vide.** Un `AdwStatusPage` sans icône, texte `Nothing is prepared.`
(§3.8), quand il n'y a ni tâche préparée ni récurrente due. Il remplace les
deux blocs, jamais la barre de saisie.

**Ce que la vue ne montre pas.** Aucune date, aucun compteur, aucune
indication sur ce que deviendra la liste. Rien n'annonce son entrée dans la
journée au passage du jour : la bannière de §3.1 reste inchangée.
