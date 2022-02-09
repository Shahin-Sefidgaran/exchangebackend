import asyncio

from files.shared.handlers import delete_all_files


async def main():
    await delete_all_files()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())