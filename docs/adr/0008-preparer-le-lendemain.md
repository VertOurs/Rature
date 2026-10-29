# ADR 0008 : préparer le lendemain

- **Date** : 2026-10-12
- **Statut** : acceptée

## Contexte

Besoin confirmé à l'usage dès le 8 septembre 2026, après une semaine sur
`0.10.1` : pouvoir préparer la liste du jour suivant avant le passage de
04:00. La veille au soir, on sait déjà ce qui ouvrira la journée ; il faut
aujourd'hui le garder en tête ou le dicter dans la réserve, où il se mélange
à tout le reste.

Le besoin heurte deux choses posées très tôt :

- `CLAUDE.md` §1 décrit une méthode « sans planification ni catégories »
- `docs/internal/SPECIFICATION.md` §2.5 ne connaît qu'une seule journée
  active, et le passage du jour la remplace par une journée vide, peuplée
  des seules récurrentes

`docs/internal/ROADMAP.md` avait donc gelé 7.3 jusqu'à un cadrage dédié,
tenu avec VertOurs le 12 octobre 2026.

## Décision

Une vue **Demain** rejoint le panneau latéral. Elle contient la liste
préparée pour la prochaine journée et montre, en lecture seule, les
récurrentes qui seront dues ce jour-là.

**Demain n'est pas une date.** C'est la prochaine journée qui démarrera.
Après plusieurs jours sans ouverture, la liste préparée devient quand même
la liste du jour : elle n'est ni perdue, ni reportée à une date passée, ni
archivée seule. C'est la conséquence directe de §2.5, où les jours
intermédiaires n'existent pas : il n'y a qu'une journée suivante, celle qui
s'ouvre.

**Au passage du jour**, l'étape 6 de §2.5 injecte toujours les récurrentes
du nouveau jour en premier. Une étape 7 s'y ajoute : les tâches préparées
entrent ensuite dans la journée, dans leur ordre, comme si elles avaient été
dictées en début de journée. Elles reçoivent leurs numéros à ce moment-là, à
la suite des récurrentes, et la liste Demain se vide.

**Dans Demain**, on peut ajouter, renommer, réordonner, supprimer, marquer
prioritaire et tirer depuis la réserve. Le tirage reste un déplacement,
`source_id` conservé (§2.5) : une tâche tirée de la réserve vers Demain
retournera en réserve au passage du jour suivant si elle n'est pas faite,
par le mécanisme habituel. On ne raye pas dans Demain, et aucune tâche n'y
porte de numéro : les numéros n'existent que dans une journée (§2.4).

**Décaler une tâche du jour vers Demain** : entrée du menu de ligne et
glisser-déposer sur l'entrée Demain du panneau, comme le renvoi en réserve
(§2.5). Mêmes restrictions : ni une tâche rayée, ni une tâche issue d'une
récurrente. Autorisé sur une liste figée, et sans trace dans la journée : la
tâche n'est ni archivée ni journalisée, son numéro n'est jamais réattribué.

**Le geste inverse existe** : ramener une tâche de Demain dans la journée,
par le menu de ligne ou en la glissant sur l'entrée du jour. Refusé sur une
liste figée, comme le tirage depuis la réserve. Le report vers Demain n'a
pas d'annulation ; sans ce geste, un report par erreur coûterait deux gestes
en passant par la réserve. Ajouté à la validation des points de détail, le
12 octobre 2026.

**Aucun report automatique.** Une tâche non rayée en fin de journée suit
toujours §2.5 : retour en réserve ou abandon pour une récurrente. Le report
vers Demain reste un geste explicite.

## Pourquoi ce n'est pas de la planification

Ce qui est écarté par §1, c'est l'agenda : des tâches attachées à des dates,
un calendrier à tenir, une liste qui juge. Demain ne porte aucune date et ne
regarde qu'une journée devant : c'est la dictée du début de journée, faite la
veille. Elle ne crée ni catégorie, ni échéance, ni retard possible, puisque
ce qui n'a pas été fait ne reste pas dans Demain : la liste se vide à chaque
passage du jour.

## Alternatives écartées

- **Un agenda, à la semaine ou au mois.** Écarté : c'est exactement la
  planification que §1 exclut, et il imposerait des tâches datées, donc des
  retards, que §2.3 interdit de commenter mais qu'un agenda montre par
  construction. Noté comme candidate v3 dans « Repoussé volontairement »,
  le temps de voir si Demain suffit.
- **Un paramètre de report automatique** des tâches non rayées vers le
  lendemain, au lieu du retour en réserve. Écarté pour l'instant : le report
  serait silencieux, et une tâche qu'on repousse chaque soir sans le décider
  finit en liste perpétuelle, ce que la réserve évite en sortant les tâches
  de la journée. Le report reste un geste explicite. À réévaluer après deux
  semaines d'usage de Demain.
- **Des tâches datées dans la réserve**, qui basculeraient au passage du
  jour. Écarté : la réserve est la liste mère sans date (§2.5), et une date
  par item y ferait entrer l'agenda par la petite porte.

## Conséquences

- §2.5 gagne une étape 7 au passage du jour, après l'injection des
  récurrentes, et la garantie « aucune donnée n'est perdue » couvre aussi la
  liste préparée
- Le format de données doit porter la liste Demain : une migration 3 → 4,
  testée comme les précédentes
- Une seconde liste sans numéros existe à côté de la journée : la règle
  « numéro attribué à l'ajout » (§2.4) devient « numéro attribué à l'entrée
  dans la journée », sans changement pour les tâches dictées dans le jour
- Les comptages de §2.6 ne voient pas Demain : une tâche préparée n'est
  comptée qu'une fois entrée dans une journée, une tâche décalée du jour
  n'y laisse aucune trace, comme un renvoi en réserve
- Les points de détail (raccourcis, place dans le panneau, suppression et
  annulation dans Demain, récurrentes affichées, format) sont tranchés dans
  `docs/internal/SPECIFICATION.md` avant tout code, conformément à
  `docs/internal/ROADMAP.md`

## Addendum (2026-10-29)

Le paramètre de report automatique, écarté « pour l'instant » ci-dessus,
est abandonné : décision de VertOurs le 29 octobre 2026, sans attendre les
deux semaines d'usage prévues. Le report vers Demain reste un geste
explicite, et une tâche non rayée suit toujours §2.5.
