CREATE TABLE IF NOT EXISTS chat
(
    player_id serial NOT NULL,
    chat_id bigint NOT NULL,
    user_id bigint NOT NULL,
    "position" smallint NOT NULL,
    money integer NOT NULL,
    is_jailed boolean NOT NULL DEFAULT FALSE,
    PRIMARY KEY (player_id)
);
