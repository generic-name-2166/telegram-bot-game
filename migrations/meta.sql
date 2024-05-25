CREATE TABLE IF NOT EXISTS meta
(
    user_id bigint NOT NULL,
    username character varying(32) NOT NULL,
    PRIMARY KEY (user_id)
);
