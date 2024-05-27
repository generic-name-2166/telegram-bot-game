DO $$
DECLARE 
    status_0 varchar(10) := {status};
BEGIN
    UPDATE chat SET "position" = %(position)s, money = %(money)s
    WHERE player_id = (
        SELECT player_id FROM chat
        WHERE user_id = %(user_id)s AND chat_id = %(chat_id)s
    );

    UPDATE game SET status = status_0
    WHERE chat_id = %(chat_id)s;
END $$;
