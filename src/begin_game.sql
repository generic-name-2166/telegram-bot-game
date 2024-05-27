INSERT INTO game (chat_id, status, current_player)
VALUES (%s, 'roll', 0)
ON CONFLICT (chat_id) UPDATE SET
    status = EXCLUDED.status,
    current_player = EXCLUDED.current_player;
