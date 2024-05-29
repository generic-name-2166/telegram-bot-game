CREATE TABLE IF NOT EXISTS game
(
    chat_id bigint NOT NULL,
    status character varying(10) NOT NULL,
    current_player smallint NOT NULL,
    biggest_bid integer,
    bid_time_sec bigint,
    bidder_id bigint,
    PRIMARY KEY (chat_id)
);
