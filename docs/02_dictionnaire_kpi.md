# Dictionnaire des indicateurs

Tous les indicateurs suivent l'**année choisie** dans le sélecteur du tableau de bord.

| Indicateur | Définition | Calcul Tableau | Piège à éviter |
|---|---|---|---|
| Exportations (Mrd CHF) | Valeur des montres exportées dans l'année | `SUM(IF [annee] = [Année] THEN [valeur_chf] END) / 1e9` | Valeur à l'export (prix de sortie de Suisse), pas prix de vente en boutique |
| Évolution vs N-1 | Variation de la valeur par rapport à l'année précédente | `(Valeur année - Valeur N-1) / Valeur N-1` | Une hausse peut venir du change : les douanes déclarent en CHF, la conversion USD vers CHF est neutralisée en reconvertissant au cours de la BNS |
| Montres exportées | Nombre de pièces | `SUM(IF [annee] = [Année] THEN [pieces] END)` | Une montre de 50 CHF et une de 50 000 CHF comptent chacune pour 1 |
| Prix moyen à l'export | Valeur par montre | `Valeur année / Pièces année` | C'est une moyenne : elle monte aussi quand le mix évolue vers le haut de gamme, sans hausse de prix catalogue |
| Part mécanique | Part de la valeur faite par les montres mécaniques (automatiques et manuelles) | `SUM(valeur des mouvements mécaniques) / Valeur année` | Mesurée en valeur, pas en volume |
| Part métal précieux | Part de la valeur faite par les boîtes en or ou platine (code SH 9101) | `SUM(valeur métal précieux) / Valeur année` | L'acier inclut aussi titane, céramique et autres matières |
| Part des exportations suisses | Poids d'un pays dans le total | `Valeur pays / {FIXED : Valeur totale}` | Le total est fixe : il ne change pas si l'on filtre une région |
| Top 15 des marchés | Les 15 premiers pays en valeur dans l'année | `{FIXED [pays] : MIN(rang de l'année)} <= 15` | Le rang est recalculé chaque année par le pipeline |
| Contribution à la croissance | Variation en CHF d'un pays | `Valeur année - Valeur N-1` | À lire avec la taille du marché |

## Segments

Les codes douaniers (Système harmonisé) permettent de distinguer :

| Code SH | Matière de la boîte | Mouvement |
|---|---|---|
| 9101.11, 9101.19 | Métal précieux | Électronique (quartz) |
| 9101.21 | Métal précieux | Mécanique automatique |
| 9101.29 | Métal précieux | Mécanique à remontage manuel |
| 9102.11, 9102.12, 9102.19 | Acier et autres | Électronique (quartz) |
| 9102.21 | Acier et autres | Mécanique automatique |
| 9102.29 | Acier et autres | Mécanique à remontage manuel |
| 9101.91 à 9102.99 | Montres de poche et autres | |

Le cœur du segment du luxe mécanique (celui de Rolex, Patek Philippe ou Audemars Piguet) correspond aux codes **9101.21** (or, automatique) et **9102.21** (acier, automatique).
