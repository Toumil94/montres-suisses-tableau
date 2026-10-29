# Cahier de recette

## 1. Contrôles automatiques (à chaque mise à jour)

| Contrôle | Attendu | Résultat |
|---|---|---|
| Somme des pays = total « Monde » publié, chaque année | couverture > 98 % | 99,98 % en moyenne (voir `data/donnees/controles.json`) |
| Unicité des clés (année, pays, code SH) | aucun doublon | conforme |
| Valeurs et quantités positives | 100 % | conforme |
| Ordre de grandeur annuel | 10 à 40 Mrd CHF | 20 à 26 Mrd CHF depuis 2012 |
| Cohérence du classeur (champs référencés, formules, feuilles) | 0 erreur | conforme |

## 2. Recette des tableaux de bord (année 2025)

Valeurs de référence calculées indépendamment en Python ([`pipeline/analyse.py`](../pipeline/analyse.py)). Tableau doit afficher les mêmes.

| ID | Tableau de bord | Indicateur | Valeur attendue | OK ? |
|---|---|---|---|---|
| R-01 | Vue d'ensemble | Exportations (Mrd CHF) | 24,54 | ☐ |
| R-02 | Vue d'ensemble | Évolution vs N-1 | −0,0 % | ☐ |
| R-03 | Vue d'ensemble | Montres exportées | 14 615 791 | ☐ |
| R-04 | Vue d'ensemble | Prix moyen par montre | 1 679 CHF | ☐ |
| R-05 | Vue d'ensemble | Part mécanique | 85,6 % | ☐ |
| R-06 | Luxe mécanique | Automatiques (Mrd CHF) | 18,47 | ☐ |
| R-07 | Luxe mécanique | Part de la valeur suisse | 75,3 % | ☐ |
| R-08 | Luxe mécanique | Prix moyen d'une automatique | 3 707 CHF | ☐ |
| R-09 | Luxe mécanique | Part de l'or dans les automatiques | 37,2 % | ☐ |
| R-10 | Marchés | États-Unis, valeur | 4,20 Mrd CHF | ☐ |
| R-11 | Marchés | Premier marché d'Asie | Japon, 1,79 Mrd CHF | ☐ |
| R-12 | Vue d'ensemble, année 2019 | Exportations (Mrd CHF) | 20,50 | ☐ |

## 3. Tests fonctionnels

| ID | Scénario | Attendu | OK ? |
|---|---|---|---|
| F-01 | Changer l'année dans le curseur | Toutes les tuiles et le top 15 se mettent à jour | ☐ |
| F-02 | Survoler un pays sur la carte | Info-bulle avec le pays, la valeur et l'évolution | ☐ |
| F-03 | Ouvrir le lien Tableau Public sans compte | Les tableaux de bord s'affichent | ☐ |
