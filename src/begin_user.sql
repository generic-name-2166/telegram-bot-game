UPDATE chat SET "position" = 1, money = 2500
WHERE player_id = (
    SELECT player_id FROM chat
    WHERE user_id = %(user_id)s AND chat_id = %(chat_id)s
);
