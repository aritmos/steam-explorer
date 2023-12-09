-- change apps that set their release date to unix epoch to `NULL` release date
UPDATE apps
SET release_date = NULL
WHERE release_date = '1969-12-31';
