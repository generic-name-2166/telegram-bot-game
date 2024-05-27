DO $$
DECLARE
    player_0 integer;
BEGIN
    player_0 := (
        SELECT player_id FROM chat
        WHERE user_id = %(user_id)s AND chat_id = %(chat_id)s
    );

    UPDATE chat SET money = %(money)s
    WHERE player_id = player_0;

    UPDATE game SET status = 'roll'
    WHERE chat_id = %(chat_id)s;

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_0, %(tile_id)s, 0)
    ON CONFLICT UPDATE;
END $$;
