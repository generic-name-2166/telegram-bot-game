DO $$
DECLARE 
    this_chat bigint := 0;
    not_ready_chat bigint := 1;
    
    user_0 bigint := 10;
    user_1 bigint := 11;

    player_0 integer;
    player_1 integer;
BEGIN
    INSERT INTO chat (chat_id, user_id, "position", money) 
    VALUES (this_chat, user_0, 0, 1500);

    INSERT INTO chat  (chat_id, user_id, "position", money) 
    VALUES (this_chat, user_1, 0, 1500);

    INSERT INTO game (chat_id, status, current_player)
    VALUES (this_chat, 'roll', 0);

    INSERT INTO meta (user_id, username)
    VALUES (user_0, 'Player 0');

    INSERT INTO meta (user_id, username)
    VALUES (user_1, 'Player 1');

    player_0 := (
        SELECT player_id FROM chat
        WHERE user_id = user_0 AND chat_id = this_chat
    );
    player_1 := (
        SELECT player_id FROM chat
        WHERE user_id = user_1 AND chat_id = this_chat
    );

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_0, 1, 2);

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_0, 3, 2);

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_1, 5, 0);

    INSERT INTO player (player_id, tile_id, house_count)
    VALUES (player_1, 6, 0);

    -- Chat without a game in progress

    INSERT INTO chat  (chat_id, user_id, "position", money) 
    VALUES (not_ready_chat, user_0, -1, -1);

    INSERT INTO chat  (chat_id, user_id, "position", money) 
    VALUES (not_ready_chat, user_1, -1, -1);
END $$;
