import asyncio

import websockets

token = 'f62e381c8d83401aba3b54748847b280'


async def hello():
    async with websockets.connect(f'ws://localhost:8080/{token}/ws') as websocket:
        while True:
            print("< {}".format(await websocket.recv()))


asyncio.get_event_loop().run_until_complete(hello())
