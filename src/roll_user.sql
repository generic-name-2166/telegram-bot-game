UPDATE chat SET "position" = %(position)s, money = %(money)s
WHERE player_id = (
    SELECT player_id FROM chat
    WHERE user_id = %(user_id)s AND chat_id = %(chat_id)s
);