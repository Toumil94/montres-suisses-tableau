# Cahier des charges

## Contexte

Une maison horlogère suisse de prestige, positionnée sur la **montre mécanique haut de gamme**, veut suivre ses marchés à l'export avec des données publiques et neutres, en complément de ses chiffres de ventes internes. La question est simple : **où se crée la valeur dans l'horlogerie suisse, et où va-t-elle ?**

Le cas s'inspire du segment où opère Rolex : montres-bracelets mécaniques automatiques, en acier et en or. Selon le rapport annuel Morgan Stanley et LuxeConsult, Rolex réalise environ un tiers de la valeur du marché horloger suisse (estimation 2025). Les données utilisées ici sont celles de toute l'industrie suisse, pas celles d'une marque.

## Parties prenantes

| Rôle | Besoin |
|---|---|
| Direction commerciale | Voir en un coup d'œil la tendance, les marchés qui progressent et ceux qui reculent |
| Responsables de marché (Amériques, Asie, Europe, Moyen-Orient) | Comparer leur zone aux autres, suivre le prix moyen par pays |
| Planification et supply chain | Anticiper la saisonnalité des expéditions |
| Contrôle de gestion | Disposer de chiffres traçables jusqu'à la source officielle |

## Questions métier

1. Les exportations horlogères suisses progressent-elles, et cette croissance vient-elle du **volume** ou du **prix** ?
2. Quelle est la part des montres **mécaniques** et des boîtes en **métal précieux** dans la valeur ?
3. Quels sont les **marchés clés**, lesquels progressent, et comment se positionnent-ils en prix moyen ?
4. Quelle est la **saisonnalité** mensuelle des exportations ?

## Exigences

| ID | Exigence | Priorité |
|---|---|---|
| E-01 | Données officielles, mises à jour automatiquement chaque mois | Haute |
| E-02 | Un sélecteur d'année qui recalcule tous les indicateurs | Haute |
| E-03 | Valeurs en CHF, converties au cours moyen de la BNS | Haute |
| E-04 | Contrôles qualité bloquants avant chaque publication | Haute |
| E-05 | Tableaux de bord publics, consultables sans licence (Tableau Public) | Haute |
| E-06 | Classeur reproductible et versionné (généré par script) | Moyenne |

## User stories

- En tant que **directeur commercial**, je veux voir l'évolution de la valeur et du prix moyen par montre, pour savoir si la croissance vient du volume ou de la montée en gamme.
- En tant que **responsable de marché**, je veux le top 15 des pays avec leur évolution, pour prioriser mes actions.
- En tant que **planificateur**, je veux la courbe mensuelle des exportations, pour anticiper les pics d'expédition.

## Hors périmètre

- Ventes au détail et marché de l'occasion : les données douanières mesurent les **expéditions depuis la Suisse**, pas les ventes au client final.
- Données par marque : les douanes ne publient pas de détail par marque.
