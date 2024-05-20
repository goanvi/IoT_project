import asyncio
from datetime import datetime
import json
import random
import sys

import asyncpg
import websockets
from asyncio_mqtt import Client
from prometheus_client import start_http_server, Summary, Gauge, Histogram
from websockets import ConnectionClosedError

clients = {}
machines = []

SERVER_CLIENTS_GAUGE = Gauge('server_clients', 'Description of my counter')
COFFEE_MACHINES_GAUGE = Gauge('coffee_machines', 'Description of my counter')
REQUEST_TIME_SUMMARY = Summary('coffee_server_requests', 'Time spent in request')
DRINK_TYPE_HIST = Histogram('coffee_type', 'Coffee type buy')


async def on_connect(websocket, path, address):
    SERVER_CLIENTS_GAUGE.inc()
    client_id = path.lstrip("/")
    print(f"Client connected, id:{client_id}")
    clients[client_id] = websocket
    try:
        async with Client(address) as client:
            async for message in websocket:
                print(f"Client[{client_id}]: {message}")
                message = json.loads(message)
                if message["type"] == 'get':
                    await websocket.send(json.dumps(machines))
                    print("Machines sent")
                else:
                    start = datetime.now()
                    machine_id = message["machine_id"]
                    await client.publish(f"machine/command/{machine_id}", json.dumps(message))
                    end = datetime.now()
                    REQUEST_TIME_SUMMARY.observe((end - start).microseconds)
    except ConnectionClosedError:
        pass
    clients.pop(client_id)
    SERVER_CLIENTS_GAUGE.dec()
    print(f"Client disconnected, id:{client_id}")


async def on_machine_connect(address):
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("machine/register")
            async for message in messages:
                COFFEE_MACHINES_GAUGE.inc()
                machine_id = message.payload.decode("utf-8")
                print(f"Coffee machine id={machine_id} connected")
                machines.append(machine_id)


async def on_machine_disconnect(address):
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("machine/deregister")
            async for message in messages:
                COFFEE_MACHINES_GAUGE.dec()
                machine_id = message.payload.decode("utf-8")
                print(f"Coffee machine id={machine_id} disconnected")
                machines.remove(machine_id)


async def on_ticket_create(address):
    database_connection = await asyncpg.connect(user='postgres',
                                                password='password',
                                                database='postgres',
                                                host='localhost')
    async with Client(address) as client:
        async with client.messages() as messages:
            await client.subscribe("machine/status")
            async for message in messages:
                status = json.loads(message.payload.decode("utf-8"))
                machine_id = status["machine_id"]
                ticket_id = status["ticket_id"]
                DRINK_TYPE_HIST.observe(status["drink_id"])
                await save_order(status, database_connection)
                print(f"Произошла покупка на кофемашине {machine_id}, покупка {ticket_id}")
    await database_connection.close()


async def save_order(order: dict, conn):
    try:
        await conn.execute('INSERT INTO "tickets" VALUES ($1, $2, $3, $4, $5, $6)',
                           order["ticket_id"],
                           order["machine_id"],
                           order["drink_id"],
                           datetime.strptime(order["created_at"], '%Y-%m-%d %H:%M:%S'),
                           order["milk"],
                           order["coffee"]
                           )
    except Exception as e:
        print(e)
        exit(1)


async def main(address):
    await asyncio.gather(
        on_ticket_create(address),
        on_machine_connect(address),
        on_machine_disconnect(address),
        websockets.serve(lambda websocket, path: on_connect(websocket, path, address), "0.0.0.0", 8765),
    )


if __name__ == '__main__':
    start_http_server(8000)

    server_address = sys.argv[1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(server_address))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
