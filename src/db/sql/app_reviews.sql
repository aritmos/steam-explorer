CREATE TEMPORARY TABLE temp_apps AS
SELECT *
FROM apps
WHERE FALSE;

COPY temp_apps (id, reviews_positive, reviews_total) FROM STDIN;

UPDATE apps
SET reviews_positive = temp_apps.reviews_positive,
    reviews_total    = temp_apps.reviews_total
FROM temp_apps
WHERE apps.id = temp_apps.id;
