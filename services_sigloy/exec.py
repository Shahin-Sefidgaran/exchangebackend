"""Command handler script"""
import asyncio
import sys

from scripts.commands.migrate import migrate
from scripts.commands.seed import seed


async def command_handler():
    command = sys.argv[1]
    if command == "migrate":
        if '--seed' in sys.argv:
            await migrate(seed_db=True)
        else:
            await migrate()
    elif command == "seed":
        await seed()
    return


asyncio.run(command_handler())
