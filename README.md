# Montres suisses à l'export : un projet Tableau de bout en bout

**Question** : où se crée la valeur de l'horlogerie suisse, et où va-t-elle ?

Un projet **Tableau** sur les exportations officielles de montres suisses, de 2012 à 2025 : collecte automatisée, contrôles qualité, classeur Tableau de 3 tableaux de bord avec KPI, et une note de recommandations. Un focus est fait sur le **segment de la montre mécanique automatique, en acier et en or**, celui de Rolex.

> *EN: An end-to-end Tableau project on official Swiss watch export statistics (2012–2025): automated data collection, quality checks, a 3-dashboard Tableau workbook with KPIs, and an executive memo. Focus on the automatic mechanical watch segment, where Rolex operates.*

[![Collecte des données](https://github.com/Toumil94/montres-suisses-tableau/actions/workflows/collecte.yml/badge.svg)](https://github.com/Toumil94/montres-suisses-tableau/actions/workflows/collecte.yml)

## Les résultats en un coup d'œil

- **Deux fois moins de montres, 21 % de valeur en plus** : 14,6 millions de pièces en 2025 contre 29,3 millions en 2012, pour 24,5 Mrd CHF.
- Le **prix moyen à l'export** passe de 691 à **1 679 CHF** par montre (×2,4).
- La **montre mécanique automatique** pèse **75 % de la valeur** : 18,5 Mrd CHF pour 5 millions de pièces. Une automatique en acier s'exporte en moyenne 2 452 CHF, en or 27 257 CHF.
- Les **États-Unis** sont le premier marché (17 %, +83 % depuis 2019), alors que **Hong Kong** recule de 32 % sur la même période.

La note complète : [**recommandations**](docs/04_recommandations.md).

![Valeur, pièces et prix](docs/images/01_valeur_pieces_prix.png)
![Prix des automatiques](docs/images/02_prix_automatiques.png)

## Les tableaux de bord Tableau

| Tableau de bord | Question | Contenu |
|---|---|---|
| Vue d'ensemble | La croissance vient-elle du volume ou du prix ? | 5 KPI (valeur, évolution, pièces, prix moyen, part mécanique), tendance, prix moyen, mix matière et mouvement |
| Luxe mécanique | Que pèse le segment de la montre automatique ? | 5 KPI du segment, poids dans le total, prix acier et or, top 15 des marchés |
| Marchés | Où vont les montres suisses ? | Carte du monde, top 15 avec évolution, volume et prix moyen par pays, régions |

Un **curseur Année** recalcule tous les indicateurs. Fichier : [`tableau/Montres-Suisses.twbx`](tableau/Montres-Suisses.twbx), à ouvrir avec Tableau Public (gratuit). Guide : [`tableau/GUIDE.md`](tableau/GUIDE.md).

## La démarche

| Étape | Livrable |
|---|---|
| 1. Comprendre le besoin | [Cahier des charges](docs/01_cahier_des_charges.md) |
| 2. Définir les indicateurs | [Dictionnaire des KPI](docs/02_dictionnaire_kpi.md), avec les formules Tableau |
| 3. Collecter et fiabiliser | [Collecte](pipeline/fetch.py) et [modélisation](pipeline/build.py), automatisées chaque mois par GitHub Actions, avec [contrôles bloquants](tests/test_donnees.py) |
| 4. Restituer | [Classeur Tableau](tableau/) généré par script, avec contrôle automatique des champs et formules |
| 5. Valider | [Cahier de recette](docs/03_recette.md) |
| 6. Recommander | [Note de synthèse](docs/04_recommandations.md) |

## Points techniques

- **Données officielles** : exportations suisses déclarées par l'Office fédéral de la douane et de la sécurité des frontières, diffusées par l'ONU (UN Comtrade), codes SH 9101 (boîte en métal précieux) et 9102 (autres boîtes), par pays et par type de mouvement. Conversion en CHF au cours moyen de la **Banque nationale suisse**.
- **Qualité** : la somme des pays retrouve le total mondial publié (99,98 %), contrôlé à chaque mise à jour.
- **Tableau** : paramètre d'année, calculs conditionnels (`IF [annee] = [Année]`), expressions LOD (`{FIXED}`) pour les parts et le top 15, carte par rôle géographique, tri calculé.
- **Dashboard as code** : le classeur (`.twb`) est généré par [`build_twb.py`](tableau/build_twb.py) au format XML de Tableau, puis contrôlé automatiquement ([`check_twb.py`](tableau/check_twb.py)) : chaque champ référencé existe, chaque formule est cohérente, chaque feuille d'un tableau de bord existe.

## Reproduire

```bash
pip install -r requirements.txt lxml
python pipeline/fetch.py        # API publique, limitée en débit : la collecte reprend là où elle s'est arrêtée
python pipeline/build.py
python -m pytest tests
python pipeline/analyse.py
python tableau/build_twb.py && python tableau/check_twb.py
```

## Auteur

**Lyes Toumi**, Data & AI Engineer, Business Analyst BI à Genève. [Portfolio](https://toumilyes.netlify.app) · [LinkedIn](https://www.linkedin.com/in/lyes-toumi/)

*Projet indépendant, sans lien avec les marques citées. Sources : OFDF via UN Comtrade, BNS. L'estimation de la part de Rolex provient du rapport Morgan Stanley et LuxeConsult.*
