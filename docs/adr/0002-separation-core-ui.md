# ADR 0002 : séparation stricte entre core et ui

- **Date** : 2026-08-24
- **Statut** : acceptée

## Contexte

Le prototype mélangeait règles métier et code GTK dans un fichier unique.
Conséquence directe : rien n'était testable sans écran, et un bug se
reproduisait en cliquant plutôt qu'en lançant un test.

Cette limite est structurelle et non contournable pour un projet développé
avec l'assistance d'un agent : un agent peut exécuter `pytest`, il ne peut
pas juger d'un rendu visuel.

## Décision

Aucun fichier de `core/` n'importe `gi`, GTK, Adw ou Gdk. Si une fonction a
besoin de GTK, elle n'appartient pas à `core/`. Aucune exception.

`ui/` ne contient aucune règle métier. Il affiche l'état fourni par `core/`
et transmet les actions.

## Conséquences

- La logique est testée en intégration continue, sans serveur d'affichage
- L'interface peut être refaite sans toucher aux règles
- Le taux de couverture de `core/` devient un critère de fin mesurable,
  fixé à 90 %
- Contrainte permanente : toute tentation d'écrire une condition métier dans
  un gestionnaire d'événement doit être refusée
