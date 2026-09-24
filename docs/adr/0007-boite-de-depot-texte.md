# ADR 0007 : boîte de dépôt texte

- **Date** : 2026-09-22
- **Statut** : acceptée

## Contexte

La capture depuis le téléphone existait dans le POC, abandonné (ADR 0004).
Le besoin reste réel : pouvoir ajouter des tâches à la réserve depuis un
téléphone, sans application dédiée à maintenir (écartée, voir
`ROADMAP.md`, « Repoussé volontairement »), sans réseau et sans compte
tiers (synchronisation cloud et Todoist repoussées à la v3, même document).

Le manifeste Flatpak actuel n'accorde aucune permission de système de
fichiers (`build-aux/flatpak/io.github.vertours.Rature.yml`, seuls
`wayland`, `fallback-x11`, `dri` et `ipc` sont présents). L'ajout d'une
permission `--filesystem` large romprait le sandboxing et la discipline du
projet sur ce point ; toute lecture d'un dossier choisi par l'utilisateur
doit donc passer par le portail de fichiers (`xdg-desktop-portal`), qui
n'apparaît pas dans `finish-args` et ne nécessite aucune permission
statique nouvelle.

L'utilisateur type dépose un fichier texte dans un dossier synchronisé
(Syncthing, Nextcloud ou équivalent) depuis une application de notes
quelconque sur son téléphone. Rature doit retrouver ce fichier au prochain
lancement ou retour au premier plan, l'importer en réserve, et ne jamais le
perdre en cas d'erreur.

## Décision

Une boîte de dépôt basée sur un dossier texte, sans surveillance continue.

- **Choix du dossier** : sélectionné une fois par l'utilisateur via le
  portail de fichiers (`Gtk.FileDialog.select_folder`), qui accorde un
  accès persistant sans permission `--filesystem` dans le manifeste.
  L'identifiant retourné par le portail est mémorisé dans GSettings.
- **Moment de lecture, et pas d'`inotify`** : au démarrage de l'application,
  puis à chaque retour de focus de la fenêtre. Le dossier choisi via le
  portail de fichiers est vu par l'application au travers du montage FUSE
  du portail de documents, pas du chemin réel sur le disque. Sur ce
  montage, `inotify` ne détecte pas de façon fiable les fichiers déposés
  par un processus extérieur au sandbox, un client de synchronisation en
  premier lieu : la surveillance continue serait un mécanisme qui semble
  fonctionner en test local puis se tait en usage réel. La lecture aux
  deux moments ci-dessus est donc le choix robuste, pas seulement le plus
  simple. Contrepartie assumée : un dépôt fait pendant que la fenêtre
  reste au premier plan sans perdre puis reprendre le focus n'est vu qu'au
  lancement suivant.
- **Format du fichier** : texte brut, une tâche par ligne, lignes vides
  ignorées, aucune syntaxe à interpréter. Le format le plus simple
  possible côté téléphone, où n'importe quelle application de notes suffit.
- **Un fichier par source** : chaque appareil ou application qui dépose
  écrit son propre fichier, nommé `inbox-<machine>-<horodatage>.txt`.
  Élimine tout risque de deux écrivains concurrents sur un même fichier,
  sans verrouillage à implémenter.
- **Filtrage strict au listing** : seuls les fichiers dont le nom
  correspond exactement au motif `inbox-*.txt` sont considérés comme des
  dépôts. Les fichiers temporaires des clients de synchronisation pendant
  un transfert (`.tmp`, `.part`, et équivalents propres à chaque client)
  ne correspondent pas au motif et sont ignorés, y compris s'ils
  apparaissent puis disparaissent entre deux lectures.
- **Ordre des opérations à l'import** : `data.json` est sauvegardé
  d'abord, le fichier source n'est déplacé vers `processed/` qu'ensuite.
  Un plantage entre les deux étapes laisse le fichier source en place :
  au prochain lancement, il est réimporté et produit un doublon dans la
  réserve, réparable à la main. L'ordre inverse ferait perdre les tâches
  du dépôt sans aucune trace en cas de plantage au même endroit ; entre un
  doublon et une perte, le doublon est le risque à assumer.
- **Après import** : le fichier est déplacé dans un sous-dossier
  `processed/` du dossier surveillé, jamais supprimé. Nom en anglais et en
  ASCII plutôt que `traité/` : cohérent avec la langue du code
  (`CLAUDE.md` §4 règle 3), et insensible aux différences de normalisation
  Unicode (NFC/NFD) entre les plateformes de synchronisation, qui
  pourraient sinon faire apparaître deux dossiers distincts pour un même
  nom accentué. L'utilisateur garde une trace de ce qui a été importé et
  peut vérifier ou récupérer manuellement.
- **Aucun dédoublonnage à l'import** : cohérent avec `SPECIFICATION.md`
  §2.7.4, qui réserve le dédoublonnage au passage du jour. Un fichier
  déposé deux fois par erreur crée deux entrées ; c'est un cas rare laissé
  à la charge de l'utilisateur plutôt que traité en code.
- **Définition de « fichier illisible »** : un fichier dont le contenu
  n'est pas de l'UTF-8 valide est mis en quarantaine, mêmes conditions
  qu'un `data.json` corrompu ; rien n'est importé, le fichier reste dans
  le dossier surveillé (pas dans `processed/`), une bannière prévient.
  Réutilise le motif de quarantaine déjà en place pour `data.json`
  (`StartupOutcome`, voir chantier 3) plutôt que d'en inventer un
  nouveau. Un fichier vide n'est pas une erreur : aucune tâche à importer,
  il est déplacé directement vers `processed/` sans déclencher de
  quarantaine.
- **Dossier surveillé devenu inaccessible** (supprimé, ou droit accordé
  par le portail révoqué) : l'application ne tente aucune reconstruction
  silencieuse. Elle affiche un message et propose de rechoisir le dossier
  via le portail, exactement le même chemin que le premier réglage.

## Conséquences

- Aucune permission nouvelle dans `finish-args` : la lecture passe par le
  portail de fichiers, dont l'usage est déjà admis par les règles du
  projet (`CLAUDE.md` §4 règle 6, pas de nouvelle dépendance d'exécution).
- La logique d'import (lecture, filtrage, sauvegarde puis déplacement vers
  `processed/`, détection d'erreur) vit dans `core/`, testable sans `gi`,
  conformément à `CLAUDE.md` §4 règle 1. Seuls le choix du dossier via le
  portail et la reprise sur dossier inaccessible touchent `ui/`.
- Le dossier `processed/` grossit sans limite avec le temps ; aucune purge
  n'est prévue pour l'instant. Coût accepté, à revoir seulement si
  l'usage réel le justifie.
- Pas de notification en temps réel : l'utilisateur découvre un ajout au
  prochain lancement ou retour de focus, jamais pendant que la fenêtre
  reste ouverte sans perdre le focus.
- Prépare le terrain pour 7.2 (renvoi manuel vers la réserve, priorité)
  sans le conditionner : la boîte de dépôt alimente la réserve existante,
  elle n'introduit pas de nouvelle structure de données hors le champ
  déjà prévu par `SPECIFICATION.md`.

## Addendum (2026-09-24)

Revue de bugs et de sécurité ciblée sur le code de 7.1, six lots. Ce qui
suit affine la décision ci-dessus sans la rouvrir.

- **Déplacement en deux temps** : `move_to_processed` (un seul
  renommage) est remplacé par `claim` (déplacement vers
  `processed/<nom>.pending`) puis `finalize` (renommage vers `<nom>` une
  fois le contenu importé). Nécessaire pour que « fichier illisible ou
  trop gros » (ci-dessous) et « sauvegarde puis déplacement » restent
  vrais en même temps : sans cette étape intermédiaire, vérifier un
  fichier avant de le réserver l'aurait laissé dans le dossier surveillé
  pendant la vérification, alors que le réserver d'abord l'aurait fait
  sortir du dossier surveillé avant que son contenu soit accepté,
  contradiction directe avec `SPECIFICATION.md` §2.8. L'ordre retenu :
  vérifier (taille, décodage) sur le fichier d'origine, réserver
  (`claim`), relire depuis le `.pending` pour importer, puis finaliser.
- **Anti-collision** : `claim` et `finalize` refusent tous deux
  d'écraser un fichier déjà présent sous le nom cible, même esprit que
  `storage.quarantine()` : un suffixe `-2`, `-3`... est inséré avant
  l'extension finale plutôt que d'écraser un `.pending` non finalisé
  d'un lancement précédent ou un fichier déjà dans `processed/`.
- **Cas rare documenté** : si la relecture depuis le `.pending` échoue
  (le contenu a changé entre la vérification et `claim`, en pratique une
  resynchronisation concurrente), le fichier reste en `.pending`,
  signalé par la bannière, sans tentative de réparation automatique.
- **Duplication bornée à un par lancement** : si l'import est sauvegardé
  mais que `finalize` échoue ensuite, l'application mémorise ce
  `.pending` pour la durée du lancement et ne le réimporte pas à chaque
  retour de focus (ce qui produirait un doublon supplémentaire à
  chaque fois) ; seul le lancement suivant retente. Affine la
  contrepartie doublon-plutôt-que-perte déjà actée ci-dessus, sans la
  changer.
- **Écoute du dossier surveillé** : une erreur de lecture au listage du
  dossier surveillé lui-même (droit révoqué en cours de route) est
  traitée comme un dossier devenu inaccessible, pas comme un échec
  d'écriture : ce sont deux bannières différentes de `SPECIFICATION.md`
  §3.6, et confondre les deux aurait pointé l'utilisateur vers le
  mauvais correctif.
- **Marque d'ordre d'octets** : une BOM UTF-8 en tête de fichier est
  ignorée plutôt que traitée comme un caractère de la première tâche,
  utile pour les applications de notes qui en écrivent une par défaut.
- **Taille maximale** : 1 Mo par fichier (`SPECIFICATION.md` §2.8), pour
  ne jamais charger un dépôt anormalement volumineux en mémoire avant de
  savoir s'il doit être importé. Un fichier plus gros reçoit le même
  traitement qu'un fichier illisible.
- **Liens symboliques exclus** : un lien symbolique dans le dossier
  surveillé peut pointer n'importe où sur le disque, en dehors de ce que
  le portail a effectivement accordé au moment du choix du dossier.
  L'ignorer, même si son nom correspond au motif, maintient le
  périmètre d'accès à ce que l'utilisateur a réellement autorisé.
