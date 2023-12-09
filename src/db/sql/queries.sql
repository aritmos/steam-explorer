-- get all categories (name) for a given app_id
SELECT name
FROM categories AS cat
WHERE id IN (SELECT category_id FROM app_categories WHERE app_id = 632360);

-- alt ^
SELECT name
FROM app_categories
         LEFT JOIN public.categories ON app_categories.category_id = categories.id
WHERE app_categories.app_id = 632360;

-- count how many games have 'Online PvP' as a category
SELECT COUNT(*)
FROM app_categories
         LEFT JOIN apps ON app_categories.app_id = apps.id
WHERE app_categories.category_id = (SELECT id FROM categories WHERE name = 'Online PvP')
  AND kind = 'game';

WITH category_counts AS (SELECT COUNT(category_id) AS count, category_id
                         FROM app_categories
                         GROUP BY category_id)
SELECT count, name
FROM category_counts
         JOIN categories ON category_counts.category_id = categories.id
ORDER BY count DESC
;
