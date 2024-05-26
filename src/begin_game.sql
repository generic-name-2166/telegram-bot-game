INSERT INTO game (chat_id, status, current_player)
VALUES (%s, 'roll', 0)
ON CONFLICT UPDATE;
