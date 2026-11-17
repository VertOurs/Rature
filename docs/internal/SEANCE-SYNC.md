# Séance de test de la synchronisation, chantier 10

Remplace la semaine d'usage réel du critère de fin (décision de VertOurs du
17 novembre 2026). Deux PC, notés **PC1** et **PC2**, côte à côte, pCloud
(fonction Sync) sur `~/Rature-sync`. Durée prévue : 1 h 15.

Document de travail, à supprimer ou à condenser dans `ROADMAP.md` une fois
la séance faite.

---

## Règles de la séance, à lire avant de commencer

1. **Ne jamais toucher à une vraie tâche.** Toutes les tâches de test
   commencent par `TEST`. On ne raye, ne renomme, ne supprime que celles-là.
2. **Ne jamais cliquer « Utiliser ce dossier » quand le dossier courant est
   `~/Rature-sync`.** Rejoindre un dossier qui contient déjà des données
   renomme le `data.json` de l'ancien dossier, et pCloud propagerait cette
   disparition à l'autre PC (issue #235). Le seul passage par ce bouton autorisé est
   celui de l'étape 0.4, depuis le dossier par défaut.
3. **Dans un dialogue inattendu, cliquer « Annuler ».** Puis noter ce qui
   s'est affiché.
4. **Attendre la livraison avant chaque geste sur l'autre PC**, sauf aux
   étapes qui demandent explicitement l'inverse. Moyen de vérifier, sur les
   deux PC dans un terminal :

   ```sh
   sha256sum ~/Rature-sync/data.json
   ```

   Même empreinte sur les deux PC : livré.
5. **Un terminal fait perdre le focus à Rature**, et le retour dans la
   fenêtre relit les données. Certaines étapes demandent de ne pas quitter
   la fenêtre : elles le disent.
6. **Noter tout écart** dans la grille de la fin : étape, PC, ce qui était
   attendu, ce qui s'est passé, heure. Pas de correction pendant la séance.

---

## Étape 0 : préparation (15 min)

### 0.1 Version installée, sur chaque PC

```sh
flatpak update io.github.vertours.Rature
flatpak info io.github.vertours.Rature | grep -i version
```

- [ ] PC1 affiche `2.3.0`
- [ ] PC2 affiche `2.3.0`

Si `2.3.0` n'est pas encore servie, attendre. Ne pas faire la séance en
`2.2.0` : les copies de conflit de pCloud n'y sont pas reconnues.

### 0.2 Réglages pCloud, sur chaque PC

- [ ] PC1 : `~/Rature-sync` est une paire de la fonction **Sync**, pas un
      dossier de `~/pCloudDrive`
- [ ] PC2 : idem, vers le même dossier distant
- [ ] PC1 : `.*.tmp` figure dans la liste des fichiers exclus de pCloud
- [ ] PC2 : idem (le réglage ne voyage pas d'un PC à l'autre)

### 0.3 Sauvegardes, sur chaque PC, Rature fermé

Fermer Rature (Ctrl+Q) sur les deux PC, puis sur chacun :

```sh
STAMP=$(date +%Y%m%d-%H%M)-$(hostname)
cp -a ~/Rature-sync ~/rature-sauvegarde-sync-$STAMP
cp -a ~/.var/app/io.github.vertours.Rature/data/rature ~/rature-sauvegarde-defaut-$STAMP 2>/dev/null
ls -la ~/rature-sauvegarde-*
```

Les sauvegardes vivent **hors** de `~/Rature-sync`, sinon elles partiraient
sur l'autre PC.

- [ ] PC1 : sauvegardes présentes, `data.json` inclus
- [ ] PC2 : sauvegardes présentes

### 0.4 Dossier utilisé, sur chaque PC

Ouvrir Rature, menu principal, **Dossier de données…**. Le dialogue affiche
le dossier courant.

- [ ] PC1 affiche `~/Rature-sync`
- [ ] PC2 affiche `~/Rature-sync`

Si un PC n'affiche **pas** `~/Rature-sync` (il est encore sur le dossier par
défaut) :

1. Vérifier que `~/Rature-sync/data.json` est arrivé sur ce PC
   (`ls -la ~/Rature-sync`)
2. **Choisir un dossier…**, choisir `~/Rature-sync`
3. Le dialogue doit proposer **Utiliser ce dossier** et donner le nom sous
   lequel le fichier local est mis de côté. Confirmer
4. Rouvrir **Dossier de données…** : il affiche `~/Rature-sync`

Si le dialogue propose au contraire **Copier les données ici**, c'est que
`data.json` n'est pas arrivé : **Annuler**, attendre pCloud, recommencer.

### 0.5 Refus du dossier courant (essai du portail face à `samefile`)

Sur PC1 : **Dossier de données…**, **Choisir un dossier…**, choisir
`~/Rature-sync`, le dossier déjà utilisé.

- [ ] Rature refuse avec « C'est déjà le dossier de données : … », sans
      rien écrire

Si un autre dialogue s'ouvre : **Annuler**, noter, et refaire l'essai sur
PC2. Ne surtout pas confirmer (règle 2).

### 0.6 État de départ

- [ ] Aucune bannière de conflit sur aucun PC
- [ ] `ls -la ~/Rature-sync` sur les deux PC : aucun nom qui contient
      `conflicted` ni `sync-conflict`
- [ ] Même empreinte `sha256sum` sur les deux PC

---

## Étape 1 : gestes alternés (15 min)

Après chaque geste : attendre la livraison (règle 4), puis cliquer dans la
fenêtre Rature de l'autre PC pour lui rendre le focus.

| # | PC | Geste | Attendu sur l'autre PC après le focus |
|---|---|---|---|
| 1.1 | PC1 | Ajouter `TEST 1` | `TEST 1` apparaît |
| 1.2 | PC2 | Ajouter `TEST 2` | `TEST 2` apparaît, `TEST 1` toujours là |
| 1.3 | PC1 | Rayer `TEST 2` | `TEST 2` rayée |
| 1.4 | PC2 | Renommer `TEST 1` en `TEST 1 bis` | renommée |
| 1.5 | PC1 | Ajouter `TEST 3`, puis la glisser au-dessus de `TEST 1 bis` | ordre identique |
| 1.6 | PC2 | Dérayer `TEST 2` | `TEST 2` non rayée |
| 1.7 | PC1 | Ajouter `TEST réserve` dans la Réserve | présente dans la Réserve |
| 1.8 | PC2 | Supprimer `TEST réserve` | absente de la Réserve |

- [ ] Les huit gestes arrivent sur l'autre PC, aucun n'est perdu
- [ ] Aucune bannière de conflit

---

## Étape 2 : relecture avant d'écrire (5 min)

But : un PC qui n'a pas encore affiché le geste de l'autre ne doit pas
l'écraser.

1. PC2 : cliquer dans la fenêtre Rature, puis **ne plus quitter la fenêtre
   de PC2** jusqu'au point 4 (pas de terminal sur PC2)
2. PC1 : ajouter `TEST 4`
3. Attendre **deux minutes** que pCloud livre (vérifier l'empreinte
   **sur PC1 seulement**, et l'icône pCloud de PC1 indique synchronisé)
4. PC2 : sans avoir quitté la fenêtre, ajouter `TEST 5`

- [ ] PC2 affiche `TEST 4` et `TEST 5`
- [ ] Après livraison, PC1 affiche aussi `TEST 4` et `TEST 5`

---

## Étape 3 : rejeu refusé (5 min)

But : un geste sur une tâche supprimée ailleurs est abandonné, avec un
message, sans rien écrire.

1. PC2 : cliquer dans la fenêtre Rature, puis ne plus la quitter
2. PC1 : supprimer `TEST 5`
3. Attendre deux minutes (vérifier sur PC1 seulement)
4. PC2 : rayer `TEST 5`, toujours affichée sur PC2

- [ ] PC2 affiche le message « Cette tâche a changé sur un autre
      appareil. » et `TEST 5` disparaît
- [ ] Aucune bannière de conflit

Si `TEST 5` a disparu de PC2 avant le clic, le message ne peut pas
s'afficher : ce n'est pas un défaut, le noter et passer à la suite.

---

## Étape 4 : annulation par identifiant (5 min)

1. PC1 : supprimer `TEST 4`
2. Attendre la livraison, focus sur PC2
3. PC2 : rayer `TEST 3`
4. Attendre la livraison, focus sur PC1
5. PC1 : **Annuler la suppression**

- [ ] `TEST 4` revient sur PC1
- [ ] `TEST 3` reste rayée sur PC1
- [ ] Après livraison, PC2 affiche `TEST 4` revenue et `TEST 3` rayée
- [ ] Sur PC2, **Annuler la suppression** n'est pas proposé pour `TEST 4`
      (la pile d'annulation est propre à chaque PC)

---

## Étape 5 : PC fermé qui revient (5 min)

1. PC2 : fermer Rature (Ctrl+Q)
2. PC1 : ajouter `TEST 6`, rayer `TEST 1 bis`
3. Attendre la livraison (empreintes égales)
4. PC2 : ouvrir Rature

- [ ] PC2 affiche `TEST 6` et `TEST 1 bis` rayée dès l'ouverture
- [ ] Aucun dialogue au démarrage, aucune bannière

---

## Étape 6 : PC hors ligne, sans conflit (5 min)

But : un PC qui travaille seul hors ligne livre ses gestes au retour du
réseau, sans conflit, si l'autre n'a rien fait entre-temps.

1. PC2 : couper le réseau

   ```sh
   nmcli networking off
   ```

2. PC2 : ajouter `TEST hors ligne`
3. PC1 : **ne rien faire**
4. PC2 : rétablir le réseau

   ```sh
   nmcli networking on
   ```

5. Attendre la livraison, focus sur PC1

- [ ] PC1 affiche `TEST hors ligne`
- [ ] Aucune bannière, aucun fichier `conflicted` (`ls -la ~/Rature-sync`
      sur les deux PC)

---

## Étape 7 : conflit provoqué (15 min)

But : deux modifications réellement différentes donnent une copie de
conflit, signalée par la bannière. C'est l'étape qui vérifie les noms de
pCloud : la noter avec soin.

1. PC2 : `nmcli networking off`
2. PC2 : ajouter `TEST conflit PC2`
3. PC1 : ajouter `TEST conflit PC1`
4. Attendre que l'icône pCloud de PC1 indique synchronisé
5. PC2 : `nmcli networking on`
6. Attendre deux minutes
7. Sur les deux PC :

   ```sh
   ls -la ~/Rature-sync ~/Rature-sync/archive
   ```

   **Recopier tels quels les noms des nouveaux fichiers** dans la grille.

8. Sur les deux PC : cliquer hors de la fenêtre Rature, puis dedans

- [ ] Une copie de conflit existe, et son nom contient `conflicted`
- [ ] La bannière « Deux appareils ont modifié les données en même temps.
      Les deux versions ont été conservées. » s'affiche sur les deux PC
- [ ] Le bouton de la bannière ouvre `~/Rature-sync` dans Fichiers
- [ ] Noter quelle tâche figure dans `data.json` (celle de PC1, de PC2, ou
      les deux) : `grep -o 'TEST conflit[^"]*' ~/Rature-sync/data.json`

Cas à noter sans rien corriger :

- **Copie présente, mais sans bannière** : son nom n'est pas reconnu.
  Recopier le nom exact, c'est un correctif pour l'expression de
  `storage.py`
- **Aucune copie, une seule tâche survit** : pCloud écrase sans garder de
  copie. C'est un résultat majeur : noter quelle tâche a disparu

### 7.1 Résoudre le conflit

Rature ne fusionne pas : on garde `data.json` et on retire la copie.

1. Sur **PC1 seulement**, supprimer chaque copie de conflit, en mettant le
   nom entre guillemets (les crochets et espaces sont fréquents) :

   ```sh
   rm -i "$HOME/Rature-sync/NOM EXACT DE LA COPIE"
   ```

2. Attendre deux minutes, puis `ls -la ~/Rature-sync` sur PC2 : la copie a
   disparu aussi
3. Sur les deux PC : cliquer hors de la fenêtre Rature, puis dedans

- [ ] La bannière disparaît sur les deux PC
- [ ] Si `TEST conflit PC2` a disparu de `data.json`, la rajouter à la main
      sur PC2 : c'est le geste que la limite connue de l'ADR 0009 fait
      perdre, et la bannière l'a signalé

---

## Étape 8 : quasi simultané, sans couper le réseau (5 min)

1. Les deux PC sur la fenêtre Rature, la main sur la souris
2. Au compte de trois, rayer `TEST 6` sur PC1 et `TEST hors ligne` sur PC2
3. Attendre deux minutes, `ls -la ~/Rature-sync` sur les deux PC, focus sur
   les deux fenêtres

Deux issues acceptables, à noter :

- [ ] Pas de copie de conflit, les deux tâches rayées partout
- [ ] Ou une copie de conflit et la bannière : la résoudre comme en 7.1

Inacceptable : une tâche rayée qui ne l'est plus, **sans** bannière.

---

## Étape 9 : nettoyage et contrôle final (10 min)

1. Sur PC1 : supprimer toutes les tâches `TEST` qui restent, Jour et
   Réserve
2. Attendre la livraison, focus sur PC2 : plus aucune tâche `TEST`
3. Sur les deux PC :

   ```sh
   ls -la ~/Rature-sync ~/Rature-sync/archive
   sha256sum ~/Rature-sync/data.json
   ```

4. Comparer avec la sauvegarde de PC1 (remplacer le nom par le vrai) :

   ```sh
   diff <(python3 -m json.tool ~/rature-sauvegarde-sync-XXXX/data.json) \
        <(python3 -m json.tool ~/Rature-sync/data.json)
   ```

   Seules différences attendues : le journal des suppressions du jour
   (`deletions`) et l'ordre ou les identifiants liés aux tâches `TEST`.
   **Aucune vraie tâche ne doit manquer ni avoir changé.**

- [ ] Plus aucune tâche `TEST` sur les deux PC
- [ ] Aucune copie de conflit, aucune bannière
- [ ] Empreintes identiques sur les deux PC
- [ ] Toutes les vraies tâches présentes et inchangées
- [ ] Garder les sauvegardes quelques jours avant de les effacer

---

## En cas de problème : retour arrière

À n'utiliser que si une vraie tâche est perdue ou abîmée.

1. Fermer Rature sur les deux PC (Ctrl+Q)
2. Sur **PC1 seulement** :

   ```sh
   cp ~/rature-sauvegarde-sync-XXXX/data.json ~/Rature-sync/data.json
   ```

3. Attendre la livraison sur PC2 (empreintes égales)
4. Supprimer les copies de conflit éventuelles (7.1)
5. Rouvrir Rature sur les deux PC, noter l'incident dans la grille

---

## Ce que la séance ne couvre pas, et pourquoi

- **Passage du jour à 04:00 et sortie de veille** : demanderait de changer
  l'horloge système. Couvert par les tests automatiques, et vérifié
  naturellement demain matin : premier geste sur un PC, puis focus sur
  l'autre, sans conflit attendu
- **Fichiers temporaires laissés par un plantage** : demanderait de tuer
  Rature en pleine écriture. Couvert par les tests ; l'exclusion `.*.tmp`
  est vérifiée en 0.2
- **Dossier inaccessible** : demanderait de renommer `~/Rature-sync`, ce que
  pCloud propagerait. Couvert par les tests et le contrôle visuel de B3

---

## Grille des écarts

| Étape | PC | Attendu | Constaté | Heure |
|---|---|---|---|---|
| | | | | |

Noms exacts des copies de conflit vues à l'étape 7 :

-

---

## Critère de fin

Atteint si, à l'étape 9 : aucune vraie tâche perdue ni changée, chaque
geste de test arrivé sur l'autre PC ou refusé avec le message, et chaque
copie de conflit signalée par la bannière. Le résultat est ensuite reporté
dans `ROADMAP.md`, et le chantier 10 est clos.
