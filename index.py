# Hate this project structure
from typing import Optional
import json

# import asyncio
# import warnings
from src.lib import App


# application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
# application.run_polling(allowed_updates=Update.ALL_TYPES)


def get_body(event: Optional[dict]) -> dict:
    return json.loads(event.get("body", "{}")) if event is not None else dict()


async def handler(event: Optional[dict], context: Optional[dict]) -> None:
    # TODO
    # body: dict = get_body(event)
    await App().start()
    await App().handle()

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "event": event,
                # "context": context,
            }
        ),
    }


""" async def main() -> None:
    app: App = App()
    await app.start()

    try:
        while True:
            await app.handle()
    finally:
        await app.stop()


if __name__ == "__main__":
    warnings.warn("Main")
    asyncio.run(main()) """
