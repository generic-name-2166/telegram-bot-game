import os
import asyncio

import monopoly
from index import handler


async def test() -> None:
    with open("secret.txt") as F:
        start = F.readline().strip()
        begin = F.readline().strip()
        roll = F.readline().strip()
        bot_token = F.readline().strip()

    os.environ["BOT_TOKEN"] = bot_token

    start_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": start,
                    }
                }
            }
        ]
    }
    begin_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": begin,
                    }
                }
            }
        ]
    }
    roll_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": roll,
                    }
                }
            }
        ]
    }
    await handler(start_msg, None)
    await handler(begin_msg, None)
    await handler(roll_msg, None)


if __name__ == "__main__":
    asyncio.run(test())
    game = monopoly.Game(((0, "Gaming"),))
    output = game.roll(0)
    print(output.out)
    print(output.warning)
