import asyncio
import sys
from datetime import datetime
import random
import json
import uuid

from asyncio_mqtt import Client

machine_id = str(uuid.uuid4())
topic_register = "machine/register"
topic_status = f"machine/status"
topic_command = f"machine/command/{machine_id}"


async def publish_status(client):
    while True:
        status = {
            "machine_id": machine_id,
            "ticket_id": str(uuid.uuid4()),
            "drink_id": random.randint(1, 4),
            "created_at": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "milk": random.randint(1, 99),
            "coffee": random.randint(1, 99)
        }
        await client.publish(topic_status, json.dumps(status))
        print(f"Покупка № {status}")
        await asyncio.sleep(15)


async def handle_commands(client):
    async with client.filtered_messages(topic_command) as messages:
        await client.subscribe(topic_command)
        async for message in messages:
            try:
                command = json.loads(message.payload)
                print(f"Получена команда: {command}")
            except json.JSONDecodeError:
                print("Ошибка декодирования команды")


async def main(address):
    # try:
    async with Client(address) as client:
        await client.publish(topic_register, payload=f"{machine_id}")
        print(f"Кофемашина {machine_id} зарегистрирована")

        await asyncio.gather(
            publish_status(client),
            handle_commands(client)
        )
    # except  as error:
    #     print(f"MQTT ошибка: {error}")
    #     await client.publish("machine/deregister", payload=f"{machine_id}")


if __name__ == '__main__':
    server_address = sys.argv[1]
    asyncio.run(main(server_address))
