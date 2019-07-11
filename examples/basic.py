import logging
import asyncio
from client.connection import Connection
from client.protocols import MessagePackProtocol

logging.basicConfig(level=logging.DEBUG)


async def on_message(name, message):
    print(f"Received Message: name={name},message={message}")


async def main(conn):
    await connection.start()
    await conn.invoke("SendSample", "test1")
    # completion_future = await conn.invoke("InvokeSample", "signalr completion", 500)
    # await completion_future
    # print(completion_future.result())
    # conn.on("message", on_message)
    # await conn.invoke("RequestMessage", "message", "test", "signalr message")


connection = Connection("ws://127.0.0.1:5000/chat", protocol=MessagePackProtocol())
loop = asyncio.get_event_loop()
loop.create_task(main(connection))
loop.run_forever()
