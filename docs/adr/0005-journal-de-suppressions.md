# ADR 0005 : journal de suppressions

- **Date** : 2026-08-24
- **Statut** : acceptée

## Contexte

Deux règles de la spécification s'opposaient directement.

`docs/internal/SPECIFICATION.md` §2.2 pose que supprimer une tâche la fait
disparaître sans laisser de trace. C'est le point le plus critique du produit : la distinction
entre rayer, qui garde une trace de ce qui a été fait, et supprimer, qui
efface un abandon.

`docs/internal/SPECIFICATION.md` §2.6 autorise la fenêtre Statistiques à
compter les tâches supprimées. Or on ne compte pas ce qui n'a laissé aucune trace.

Trois issues étaient possibles : retirer les suppressions du périmètre
statistique, journaliser sans le texte, ou journaliser l'entrée complète.

## Décision

Le fichier d'archive conserve un journal `deletions`. Chaque entrée contient
l'identifiant, le numéro, le texte, l'origine, le `source_id` éventuel et
l'horodatage local.

Le journal n'est jamais affiché. La fenêtre Statistiques n'en tire qu'un
nombre.

La variante sans texte avait été proposée pour préserver littéralement la
formule « sans laisser de trace ». Elle a été écartée : elle privait
l'annulation de suppression d'une restauration fidèle, pour un gain qui
n'était pas recherché. Le besoin exprimé n'était pas la confidentialité,
c'était l'absence de trace dans l'interface.

## Conséquences

- Le comptage des suppressions devient possible, par jour et par origine
- L'annulation de suppression restaure la tâche à l'identique, sans
  reconstruction approximative
- La formule de `docs/internal/SPECIFICATION.md` §2.2 a dû être reformulée.
  La disparition est fonctionnelle : la tâche quitte toutes les vues et
  n'est jamais réaffichée. Elle n'est pas une garantie de confidentialité,
  le texte restant lisible pour qui ouvre le fichier d'archive à la main. Le
  document le dit explicitement plutôt que de laisser croire l'inverse
- Interdiction permanente : la fenêtre Statistiques ne doit exposer le
  contenu du journal sous aucune forme, ni aperçu, ni recherche, ni export.
  Toute demande future en ce sens se heurte à ce choix, et c'est voulu
- L'annulation de suppression doit maintenir le journal, sans quoi le
  comptage dérive. À couvrir par un test au chantier 4
- Le modèle `Deletion` porte aujourd'hui `id`, `num`, `text`, `origin`,
  `source_id` et `deleted_at`. Il lui manque `done`, `done_at`,
  `source_created` et `template_id` pour restaurer « à l'identique » une
  tâche rayée ou tirée de la réserve. Le chantier 4 devra étendre `Deletion`
  (changement de format, donc migration testée) ou revoir la promesse
- Le champ existe dès la version 1 du format, pour ne pas imposer une
  migration sur données réelles
- Le journal est porté par la journée, pas global : il part avec l'archive
  au passage du jour, la nouvelle journée en ouvre un vide. Chaque entrée
  garde le texte complet et l'origine (`day`, `reserve` ou `recurring`),
  jamais affichée
