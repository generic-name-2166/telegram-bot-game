import asyncio

from index import handler


async def test() -> None:
    await handler(dict(), None)


if __name__ == "__main__":
    asyncio.run(test())
