# Publier le classeur sur Tableau Public (10 minutes)

Prérequis : **Tableau Public Desktop** (gratuit) et un compte Tableau Public.

## 1. Ouvrir

1. Télécharge [`Montres-Suisses.twbx`](Montres-Suisses.twbx) (bouton **Download raw file** sur GitHub).
2. Double-clique dessus : Tableau Public s'ouvre avec les données incluses (extrait Hyper, exigé par Tableau Public).
3. Les onglets en bas montrent les 3 tableaux de bord : **Vue d'ensemble**, **Luxe mécanique**, **Marchés**.

## 2. Vérifier

Sur **Vue d'ensemble**, avec l'année 2025 : 24,54 Mrd CHF, 14 615 791 montres, 1 679 CHF par montre. La liste complète est dans le [cahier de recette](../docs/03_recette.md).

## 3. Publier

1. **Fichier**, puis **Enregistrer sur Tableau Public**.
2. Connecte-toi, donne le titre « Montres suisses à l'export ».
3. Le navigateur s'ouvre sur ta page Tableau Public : copie le lien et envoie-le-moi pour que je l'ajoute au README et au portfolio.

## En cas de problème

Le classeur est généré par script (`build_twb.py`). Si un message d'erreur apparaît ou qu'un graphique s'affiche mal, une capture d'écran suffit pour corriger.

## Questions d'entretien

- **Pourquoi un paramètre « Année » plutôt qu'un filtre ?** Un filtre retirerait l'année précédente du contexte : impossible alors de calculer l'évolution vs N-1. Les mesures filtrent elles-mêmes l'année avec `IF [annee] = [Année]`.
- **Pourquoi une expression LOD `{FIXED}` pour la part de marché ?** Le total suisse doit rester fixe quand on regarde un pays : `{FIXED : SUM(...)}` calcule le total indépendamment des dimensions de la vue.
- **Pourquoi le prix moyen et pas le volume ?** Le volume baisse de moitié depuis 2012 alors que la valeur progresse : piloter au volume ferait passer à côté de la montée en gamme.
- **Pourquoi générer le classeur par script ?** Il est versionné, relu, régénéré chaque mois avec les nouvelles données et contrôlé automatiquement, comme du code.
