-- Preliminary schema for data storage

-- -----
-- DROPS
-- -----

-- drop table if exists AppInfo cascade;
-- drop table if exists Genres cascade;
-- drop table if exists AppGenres cascade ;
-- drop table if exists AppExtraInfo cascade ;
-- drop table if exists AppRequirements cascade ;
-- drop table if exists AppReviews cascade ;
-- drop table if exists AppPriceHistory cascade ;
-- drop table if exists AppPlayerCounts cascade ;
-- drop table if exists AppCategories cascade ;
-- drop table if exists Categories cascade ;
-- drop table if exists AppTags cascade ;
-- drop table if exists Tags cascade ;

-- --------------------
-- APPINFO & APPREVIEWS
-- --------------------

create type app_type as enum ('game', 'dlc', 'demo');
create table AppInfo
(
    appid        int      not null primary key, -- appinfo:steam_appid
    kind         app_type not null,             -- appinfo:type
    name         text     not null,             -- appinfo:name
    price        int      not null,             -- appinfo:price_overview:initial
    release_date date                           -- null if "coming soon"; appinfo:release_date:[coming_soon|date]
);

create table AppExtraInfo
(
    appid        int      not null primary key references AppInfo (appid),
    required_age int not null,
    dlc          int[],
    categories   int[]    not null,
    platforms    bool[3]  not null, -- [windows, macos, linux]
    achievements int not null  -- appinfo:achievements:total
);

create table AppReviews
(
    appid    int not null primary key references AppInfo (appid),
    total    int not null,
    positive int not null
);

create table Categories
(
    category_id int primary key,
    name        text not null
);

create table AppCategories
(
    appid       int not null references AppInfo (appid),
    category_id int not null references Categories (category_id),
    primary key (appid, category_id)
);

create table Genres
(
    genre_id int primary key,
    name     text not null
);

create table AppGenres
(
    appid    int not null references AppInfo (appid),
    genre_id int not null references Genres (genre_id),
    primary key (appid, genre_id)
);

create table Tags
(
    tag_id int primary key,
    name   text not null
);

create table AppTags
(
    appid  int not null references AppInfo (appid),
    tag_id int not null references Tags (tag_id),
    votes  int not null,
    primary key (appid, tag_id)
);

create type platform_type as enum ('windows', 'macos', 'linux');
create type req_type as enum ('minimum', 'recommended');
create table AppRequirements
(
    appid     int           not null references AppInfo (appid),
    platform  platform_type not null,
    kind      req_type      not null,
    processor text,
    memory    int,
    graphics  text,
    storage   int, -- MB ?
    primary key (appid, platform, kind)
);

-- ------------
-- PLAYERCOUNTS
-- ------------

create table AppPlayerCounts
(
    appid   int   not null references AppInfo (appid),
    month   date  not null,
    average float not null,
    peak    int   not null,
    primary key (appid, month)
);

-- -------------
-- PRICE HISTORY
-- -------------

create table AppPriceHistory
(
    appid      int       not null references AppInfo (appid),
    time       timestamp not null,
    full_price int       not null, -- in cents
    curr_price int       not null, -- in cents
    primary key (appid, time)
);