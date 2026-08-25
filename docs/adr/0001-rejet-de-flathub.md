# ADR 0001 : rejet de Flathub, dépôt Flatpak auto-hébergé

- **Date** : 2026-08-24
- **Statut** : acceptée

## Contexte

Flathub était le canal de distribution visé, pour sa visibilité et ses mises
à jour automatiques. La politique de Flathub, durcie le 29 mai 2026, interdit
tout contenu généré ou assisté par IA, dans l'application comme dans la
soumission : manifeste, métadonnées, correctifs, scripts de build, texte de
la pull request. Elle n'est pas rétroactive et prévoit des exceptions pour
les projets matures et bien maintenus, ce qui ne correspond pas à un projet
qui démarre. GNOME Circle a suspendu ses nouvelles soumissions le 30 mai 2026.

Le projet est développé avec l'assistance d'un agent. Trois voies étaient
ouvertes : écrire l'intégralité du code sans assistance, renoncer à ces deux
canaux, ou renoncer à publier.

## Décision

Ni Flathub, ni GNOME Circle. La distribution passe par :

1. Un dépôt Flatpak statique auto-hébergé sur GitHub Pages, canal principal
2. Un bundle `.flatpak` joint à chaque release, pour essayer sans s'engager
3. AUR et COPR, paquets natifs à faible coût de maintenance

## Conséquences

- Les mises à jour automatiques sont conservées, via l'ajout du dépôt
- La visibilité dans la logithèque GNOME est perdue
- Une clé GPG de signature devient critique : sans elle, plus aucune mise à
  jour publiable sur le dépôt
- Les exigences de qualité de Flathub sont conservées volontairement, elles
  servaient la maintenabilité autant que la conformité
