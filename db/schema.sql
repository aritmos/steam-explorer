create type app_type as enum ('game', 'dlc', 'demo');
create table Apps
(
    id           int      not null primary key,
    kind         app_type not null,
    name         text     not null,
    windows      bool     not null,
    mac          bool     not null,
    linux        bool     not null,
    price        int      not null,
    metacritic   int,
    reviews_tot  int, -- switch to non-null after populating
    reviews_pos  int, -- switch to non-null after populating
    age          int,
    release_date date,
    drm          bool     not null,
    ext_acc      bool     not null
);

create table Categories
(
    category_id int primary key,
    name        text not null
);

create table AppCategories
(
    app_id      int not null references Apps (id),
    category_id int not null references Categories (category_id),
    primary key (app_id, category_id)
);

create table Genres
(
    id   int primary key,
    name text not null
);

create table AppGenres
(
    app_id   int not null references Apps (id),
    genre_id int not null references Genres (id),
    primary key (app_id, genre_id)
);

create table Tags
(
    id   int primary key,
    name text not null
);

create table AppTags
(
    app_id int not null references Apps (id),
    tag_id int not null references Tags (id),
    votes  int not null,
    primary key (app_id, tag_id)
);

create table Developers
(
    name text primary key
);

create table AppDevelopers
(
    app_id    int references Apps (id),
    developer text references Developers (name),
    primary key (app_id, developer)
);

create table Publishers
(
    name text primary key
);

create table AppPublishers
(
    app_id    int references Apps (id),
    publisher text references Publishers (name),
    primary key (app_id, publisher)
);


create type platform_type as enum ('windows', 'mac', 'linux');
create type req_type as enum ('minimum', 'recommended');
create table AppRequirements
(
    app_id    int           not null references Apps (id),
    platform  platform_type not null,
    kind      req_type      not null,
    processor text,
    memory    int,
    graphics  text,
    storage   int, -- MB ?
    primary key (app_id, platform, kind)
);

create table AppPlayerCounts
(
    app_id  int   not null references Apps (id),
    month   date  not null,
    average float not null,
    peak    int   not null,
    primary key (app_id, month)
);

create table AppPriceHistory
(
    app_id     int       not null references Apps (id),
    time       timestamp not null,
    full_price int       not null, -- in cents
    curr_price int       not null, -- in cents
    primary key (app_id, time)
);

create table DLCs
(
    game_app_id int references Apps (id),
    dlc_app_id int references Apps (id),
    primary key (game_app_id, dlc_app_id)
);

create table Demos
(
    game_app_id int references Apps (id),
    demo_app_id int references Apps (id),
    primary key (game_app_id, demo_app_id)
);