CREATE TABLE IF NOT EXISTS player
(
    id serial NOT NULL,
    player_id integer NOT NULL,
    tile_id smallint NOT NULL,
    house_count smallint NOT NULL,
    PRIMARY KEY (id)
);
