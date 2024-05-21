# Hate this project structure
from typing import Optional
import json
from src.lib import App


# application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
# application.run_polling(allowed_updates=Update.ALL_TYPES)


def get_body(event: Optional[dict]) -> dict:
    return json.loads(event.get("body", "{}")) if event is not None else dict()


async def handler(event: Optional[dict], context: Optional[dict]) -> None:
    # TODO
    body: dict = get_body(event)
    await App().webserve(body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "event": event,
                # "context": context,
            }
        ),
    }
