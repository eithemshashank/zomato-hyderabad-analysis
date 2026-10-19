-- Q1. Does price predict rating? Average rating by cost band.
SELECT CASE WHEN cost_for_two <= 400  THEN '1: <=400'
            WHEN cost_for_two <= 700  THEN '2: 401-700'
            WHEN cost_for_two <= 1000 THEN '3: 701-1000'
            WHEN cost_for_two <= 1500 THEN '4: 1001-1500'
            ELSE '5: >1500' END AS cost_band,
       COUNT(*) AS restaurants,
       ROUND(AVG(avg_rating), 2) AS avg_rating
FROM (SELECT r.restaurant, r.cost_for_two, AVG(v.rating) AS avg_rating
      FROM restaurants r JOIN reviews v ON v.restaurant = r.restaurant
      GROUP BY r.restaurant, r.cost_for_two) t
GROUP BY cost_band ORDER BY cost_band;

-- Q2. Best rated cheap restaurants (<= Rs 500 for two), with rank (window function).
SELECT restaurant, cost_for_two, avg_rating,
       RANK() OVER (ORDER BY avg_rating DESC) AS rnk
FROM (SELECT r.restaurant, r.cost_for_two, ROUND(AVG(v.rating), 2) AS avg_rating
      FROM restaurants r JOIN reviews v ON v.restaurant = r.restaurant
      WHERE r.cost_for_two <= 500
      GROUP BY r.restaurant, r.cost_for_two) t
ORDER BY rnk LIMIT 8;

-- Q3. Collection tag vs rating, inside price bands (CTE).
WITH rest AS (
    SELECT r.restaurant, r.has_collection,
           CASE WHEN r.cost_for_two <= 500 THEN '1: <=500'
                WHEN r.cost_for_two <= 1000 THEN '2: 501-1000' ELSE '3: >1000' END AS cost_band,
           AVG(v.rating) AS avg_rating
    FROM restaurants r JOIN reviews v ON v.restaurant = r.restaurant
    GROUP BY r.restaurant, r.has_collection, r.cost_for_two
)
SELECT cost_band, has_collection, COUNT(*) AS restaurants, ROUND(AVG(avg_rating), 2) AS avg_rating
FROM rest GROUP BY cost_band, has_collection ORDER BY cost_band, has_collection;

-- Q4. Polarising restaurants: at least 25% 1-2 star AND at least 25% 5 star reviews (people either love or hate them).
SELECT restaurant,
       ROUND(AVG(rating), 2) AS avg_rating,
       ROUND(100 * AVG(rating <= 2), 1) AS pct_low,
       ROUND(100 * AVG(rating = 5), 1)  AS pct_five,
       ROUND(100 * AVG(rating <= 2 OR rating = 5), 1) AS pct_extreme
FROM reviews GROUP BY restaurant
HAVING COUNT(*) >= 50 AND AVG(rating <= 2) >= 0.25 AND AVG(rating = 5) >= 0.25
ORDER BY pct_extreme DESC LIMIT 10;

-- Q5. Reviews with pictures vs without.
SELECT has_pictures, COUNT(*) AS reviews, ROUND(AVG(rating), 2) AS avg_rating
FROM reviews GROUP BY has_pictures;

-- Q6. Rating trend by year, with year-over-year change (LAG).
WITH y AS (SELECT YEAR(time) AS yr, COUNT(*) AS reviews, AVG(rating) AS avg_rating
           FROM reviews GROUP BY YEAR(time))
SELECT yr, reviews, ROUND(avg_rating, 2) AS avg_rating,
       ROUND(avg_rating - LAG(avg_rating) OVER (ORDER BY yr), 2) AS change_vs_prev_year
FROM y ORDER BY yr;

-- Q7. Top restaurant inside each cuisine (ROW_NUMBER), cuisines with >= 8 restaurants.
WITH ra AS (SELECT restaurant, AVG(rating) AS avg_rating FROM reviews GROUP BY restaurant),
     cu AS (SELECT c.cuisine, c.restaurant, ra.avg_rating,
                   COUNT(*) OVER (PARTITION BY c.cuisine) AS n_in_cuisine,
                   ROW_NUMBER() OVER (PARTITION BY c.cuisine ORDER BY ra.avg_rating DESC) AS rn
            FROM restaurant_cuisines c JOIN ra ON ra.restaurant = c.restaurant)
SELECT cuisine, n_in_cuisine, restaurant AS top_restaurant, ROUND(avg_rating, 2) AS avg_rating
FROM cu WHERE rn = 1 AND n_in_cuisine >= 8 ORDER BY avg_rating DESC;
