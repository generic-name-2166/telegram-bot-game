INSERT INTO chat  (chat_id, user_id, "position", money) 
VALUES (%(chat_id)s, %(user_id)s, %(position)s, %(money)s)
ON CONFLICT DO NOTHING;

INSERT INTO meta (user_id, username)
VALUES (%(user_id)s, %(username))
ON CONFLICT DO NOTHING;
