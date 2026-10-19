# Power BI dashboard: build steps

Import `data/processed/restaurants.csv`, `reviews.csv`, `restaurant_cuisines.csv`, `restaurant_collections.csv`.
Model: restaurants[restaurant] 1-to-many reviews[restaurant]; same for cuisines and collections (single direction).

## Measures (see dax_measures.dax)
Avg Rating, Review Count, % Low (1-2 star), % Five Star, Avg Cost for Two.

## Page 1: Overview
- Cards: Review Count, Avg Rating, % Five Star, % Low.
- Column chart: Avg Rating by cost band (create a calculated column `Cost Band`, see DAX file).
- Bar chart: top 10 restaurants by Avg Rating (filter Review Count >= 50).
- Slicers: Cuisine, Collection, Cost Band.

## Page 2: Problem restaurants
- Scatter: X = Avg Rating, Y = % Low + % Five, details = restaurant (polarising places sit top-middle).
- Table: restaurant, Avg Rating, % Low, % Five, sorted by % Low.
- Line chart: Avg Rating by month (reviews[time]).

Take a screenshot of each page, save as `powerbi/page1.png` and `powerbi/page2.png`, and link them in the README.
