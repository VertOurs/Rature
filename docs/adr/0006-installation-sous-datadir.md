# ADR 0006 : installation du paquet sous datadir

- **Date** : 2026-08-29
- **Statut** : acceptée

## Contexte

La session B devait rendre l'installation Meson exécutable quel que soit le
préfixe, y compris un préfixe jetable utilisé pour vérifier la fenêtre en
local.

Deux interpréteurs coexistent sur la machine de développement : le venv du
projet en Python 3.13 sans PyGObject, qui sert à `ruff` et `pytest`, et le
`python3` système en 3.14 avec PyGObject, qui sert à lancer l'application
hors Flatpak.

Installer le paquet dans le `site-packages` de l'interpréteur lie
l'application à cet interpréteur et à un préfixe système. Un `--prefix`
arbitraire ne place alors pas le paquet sur le chemin d'import.

## Décision

Le paquet est installé sous `<datadir>/rature/rature`. Le lanceur
`src/rature.in`, configuré par Meson, ajoute ce dossier en tête de
`sys.path`. Le `.gresource` et le `config.py` généré vivent au même endroit.

Une option Meson `python`, valeur par défaut `python3`, choisit
l'interpréteur visé par le shebang du lanceur. En local :
`meson setup build -Dpython=/usr/bin/python3`. Sous Flatpak et en CI, la
valeur par défaut convient, `python3` y porte PyGObject.

L'installation en paquet Python classique, par un backend de build et
`pip install .`, a été écartée. Le build passe par Meson, pas par un
backend Python, et cette voie réintroduirait le couplage au préfixe et au
`site-packages`.

## Conséquences

- L'installation fonctionne sous n'importe quel préfixe, vérifié avec un
  `--prefix` jetable
- L'application tourne sous le `python3` du runtime GNOME 50 en Flatpak, et
  sous le `python3` doté de PyGObject de la machine en local
- `meson test` résout `pytest` depuis le `PATH`, donc le venv activé, et
  laisse `required: false` pour le développement. La CI installe `pytest`
  explicitement dans son propre job
- La liste des `__pycache__` passée à `exclude_directories` dans
  `src/meson.build` est tenue à la main. Un déplacement de l'arborescence
  source oblige à la revoir
