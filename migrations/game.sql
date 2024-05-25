CREATE TABLE IF NOT EXISTS game
(
    chat_id bigint NOT NULL,
    status character varying(10) NOT NULL,
    current_player smallint NOT NULL,
    PRIMARY KEY (chat_id)
);
