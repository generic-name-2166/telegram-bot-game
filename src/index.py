from typing import Optional, Any
import json
import warnings

from lib import App


def parse_body(message: dict) -> Optional[dict]:
    try:
        body = message["details"]["message"]["body"]
        result = json.loads(body) if message is not None else None
    except (json.JSONDecodeError, KeyError) as e:
        warnings.warn(f"JSON error {e}")
        result = None
    return result


def get_body(event: Optional[dict]) -> Optional[list[dict]]:
    if event is None:
        return None
    messages: Optional[list[dict]] = event.get("messages")
    if messages is None:
        return None
    return list(filter(lambda x: x is not None, map(parse_body, messages)))


async def handler(event: Optional[dict], context: Any) -> dict:
    bodies: Optional[list[dict]] = get_body(event)
    if bodies is not None:
        app: App = App()
        await app.start(context)
        for body in bodies:
            await app.handle_update(body)
        await app.stop()
    else:
        warnings.warn(f"Body is empty {bodies}")
    return {
        "statusCode": 200,
        "body": "",
    }
