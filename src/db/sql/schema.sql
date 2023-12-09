CREATE SCHEMA IF NOT EXISTS public;
SET SEARCH_PATH TO public;

CREATE TYPE app_kind AS enum ('game', 'dlc', 'demo');
CREATE TABLE apps
(
    id               int PRIMARY KEY,
    kind             app_kind NOT NULL,
    name             text     NOT NULL,
    supports_windows bool     NOT NULL,
    supports_mac     bool     NOT NULL,
    supports_linux   bool     NOT NULL,
    price            int      NOT NULL,
    metacritic_score int,
    reviews_total    int,  -- switch to non-null after populating
    reviews_positive int,  -- switch to non-null after populating
    age_check        int,
    release_date     date, -- NULL if not released yet
    has_drm          bool     NOT NULL,
    has_ext_acc      bool     NOT NULL,
    achievements     int      NOT NULL
);

CREATE TABLE categories
(
    id   int PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE app_categories
(
    app_id      int REFERENCES apps (id),
    category_id int REFERENCES categories (id),
    PRIMARY KEY (app_id, category_id)
);

CREATE TABLE genres
(
    id   int PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE app_genres
(
    app_id   int REFERENCES apps (id),
    genre_id int REFERENCES genres (id),
    PRIMARY KEY (app_id, genre_id)
);

CREATE TABLE tags
(
    id   int PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE app_tags
(
    app_id int REFERENCES apps (id),
    tag_id int REFERENCES tags (id),
    votes  int NOT NULL,
    PRIMARY KEY (app_id, tag_id)
);

CREATE TABLE app_developers
(
    app_id    int REFERENCES apps (id),
    developer text,
    PRIMARY KEY (app_id, developer)
);

CREATE TABLE app_publishers
(
    app_id    int REFERENCES apps (id),
    publisher text,
    PRIMARY KEY (app_id, publisher)
);

CREATE TABLE languages
(
    language_code varchar(6) PRIMARY KEY,
    name          varchar(23) NOT NULL
);

CREATE TABLE app_languages
(
    app_id        int REFERENCES apps (id),
    language_code varchar(6) REFERENCES languages (language_code),
    PRIMARY KEY (app_id, language_code)
);


CREATE TYPE platform_kind AS enum ('windows', 'mac', 'linux');
CREATE TYPE performance_category AS enum ('minimum', 'recommended');
CREATE TYPE requirement_classifier AS
(
    platform    platform_kind,
    performance performance_category
);
CREATE TABLE app_requirements
(
    app_id     int REFERENCES apps (id),
    classifier requirement_classifier,
    processor  text,
    memory     int,
    graphics   text,
    storage    int, -- MB ?
    PRIMARY KEY (app_id, classifier)
);

CREATE TABLE app_playercounts
(
    app_id              int REFERENCES apps (id),
    month_date          date,
    playercount_average float NOT NULL,
    playercount_peak    int   NOT NULL,
    PRIMARY KEY (app_id, month_date)
);

CREATE TABLE app_pricehistory
(
    app_id        int REFERENCES apps (id),
    time          timestamp,
    price_full    int NOT NULL, -- in cents
    price_current int NOT NULL, -- in cents
    PRIMARY KEY (app_id, time, price_full, price_current)
);

CREATE TABLE game_dlcs
(
    game_app_id int REFERENCES apps (id),
    dlc_app_id  int REFERENCES apps (id),
    PRIMARY KEY (game_app_id, dlc_app_id)
);

CREATE TABLE game_demos
(
    game_app_id int REFERENCES apps (id),
    demo_app_id int REFERENCES apps (id),
    PRIMARY KEY (game_app_id, demo_app_id)
);
