SELECT
 	-- chat.chat_id,
	-- chat.player_id,
	chat.user_id,
	chat.position,
	chat.money,
	game.status,
	game.current_player,
	meta.username,
    player.tile_id,
	player.house_count
FROM player
FULL JOIN chat ON chat.player_id = player.player_id
LEFT JOIN meta ON chat.user_id = meta.user_id
LEFT JOIN game ON chat.chat_id = game.chat_id
WHERE chat.chat_id = %s;
