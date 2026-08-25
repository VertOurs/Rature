# ADR 0004 : abandon du prototype

- **Date** : 2026-08-24
- **Statut** : acceptée

## Contexte

Un prototype fonctionnel existait : fichier unique, français dans le code et
l'interface, aucun test, aucune séparation des responsabilités, packagé en
Flatpak sur un runtime déjà en fin de vie. Il répondait à la question « est-ce
que la méthode se transpose en application », et la réponse était oui.

Le reprendre comme base imposait de traîner ses choix : langue, structure,
absence de tests, format de données sans identifiants.

## Décision

Le prototype est abandonné. Il n'est ni utilisé, ni migré, ni consulté, ni
recopié, même partiellement. La construction repart de la spécification
écrite dans `CLAUDE.md` §2.

L'auteur continue d'utiliser ses conversations quotidiennes en attendant que
l'application soit prête.

## Conséquences

- Aucune donnée réelle à préserver, donc aucune migration à écrire
- Le format de données naît en version 1, complet, avec réserve et
  récurrentes
- La spécification devient l'unique source de vérité, ce qui a imposé de
  l'écrire réellement plutôt que de la déduire du code existant
- Coût assumé : plusieurs chantiers sans rien d'utilisable, période où un
  projet personnel s'abandonne facilement
