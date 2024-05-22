import os
import asyncio

from index import handler


async def test() -> None:
    with open("secret.txt") as F:
        body = F.readline().strip()
        bot_token = F.readline().strip()

    os.environ["BOT_TOKEN"] = bot_token

    test_msg = {
        "messages": [
            {
                "details": {
                    "message": {
                        "body": body,
                    }
                }
            }
        ]
    }
    await handler(test_msg, None)


if __name__ == "__main__":
    asyncio.run(test())
