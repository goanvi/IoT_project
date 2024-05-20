import asyncio
import datetime
import json
import random
import sys

import websockets
import uuid


async def send(websocket, client_id):
    while True:
        await websocket.send(json.dumps({
            "type": "get"
        }))
        response = await websocket.recv()
        machine = random.choice(response["machines"])
        await websocket.send(json.dumps({
            "type": "get",
            "machine_id": machine,
            "command": "test",
            "created_at": str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        }))
        print("Command sent")
        await asyncio.sleep(15)


async def main(address):
    client_id = uuid.uuid4()
    async with websockets.connect(f"ws://{address}:8765/{client_id}") as websocket:
        await asyncio.gather(
            send(websocket, client_id),
        )


if __name__ == '__main__':
    server_address = sys.argv[1]
    asyncio.get_event_loop().run_until_complete(main(server_address))
