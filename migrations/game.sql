CREATE TABLE IF NOT EXISTS game
(
    chat_id bigint NOT NULL,
    status character varying(10) NOT NULL,
    current_player smallint NOT NULL,
    biggest_bid integer NOT NULL DEFAULT 0,
    bid_time_sec bigint NOT NULL DEFAULT 0,
    bidder_id bigint NOT NULL DEFAULT 0,
    PRIMARY KEY (chat_id)
);
