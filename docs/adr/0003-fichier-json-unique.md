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

## Addendum (2026-09-24)

Revue de bugs et de sécurité, lot E : `data.json` et les archives
s'écrivaient en `0o644` (masqué par l'umask du système à partir d'un
`open()` sans mode explicite), et leur répertoire en `0o755`, lisibles
par tout le système alors qu'ils contiennent le texte des tâches de
l'utilisateur. `_atomic_write_json` force désormais `0o600` sur le
fichier temporaire via un `opener` dédié, et `save()`/`archive()`
créent leur répertoire en `0o700` ; les deux valeurs n'ont aucun bit
que l'umask pourrait retirer, donc fiables quel que soit l'umask du
système. `App.open` restreint en plus le répertoire de données existant
à `0o700` à chaque lancement (`storage.restrict_data_dir_permissions`),
pas à chaque écriture : un répertoire à `0o700` bloque déjà l'accès à
tout son contenu, anciennes archives en `0o644` comprises, donc ce seul
appel couvre aussi une installation antérieure à ce correctif sans
retoucher chaque fichier existant un par un. Un échec de ce chmod est
journalisé mais jamais bloquant : la restriction est une amélioration
de confidentialité, pas une condition de démarrage.
