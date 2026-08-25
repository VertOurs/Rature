# ADR 0003 : un fichier JSON plutôt qu'une base de données

- **Date** : 2026-08-24
- **Statut** : acceptée

## Contexte

L'application manipule quelques dizaines d'entrées par jour, sur un poste
unique, sans accès concurrent ni synchronisation. SQLite était l'alternative
naturelle.

## Décision

Un fichier JSON versionné dans `$XDG_DATA_HOME/rature/`, plus un fichier par
journée archivée dans `archive/`.

Écriture atomique obligatoire : fichier temporaire dans le même répertoire,
`flush`, `os.fsync` sur le fichier, fermeture, `os.replace`, puis `os.fsync`
sur le descripteur du répertoire.

## Conséquences

- Données lisibles et réparables à la main, ce qui compte pour une
  application qui contient les listes de son auteur
- Aucune dépendance supplémentaire
- Le fsync du répertoire n'est pas optionnel : sans lui, le renommage peut
  être perdu lors d'une coupure et la garantie d'atomicité serait fausse
- Un champ `version` et des identifiants uuid sont présents dès la version 1,
  pour éviter d'imposer une migration sur données réelles plus tard
- Ce choix serait à rouvrir si une synchronisation multi-postes devenait
  nécessaire, ce qui est explicitement hors périmètre
