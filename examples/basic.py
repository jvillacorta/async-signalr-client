import logging
import asyncio
from client.connection import Connection, SignalRConnectionState

logging.basicConfig(level=logging.DEBUG)


async def main(conn):
    await connection.start()
    completion_future = await conn.invoke("SendSample", "test1")
    completion_future = await conn.invoke("InvokeSample", "test2", 500)
    await completion_future
    print(completion_future.result())


connection = Connection("ws://127.0.0.1:5000/chat")
loop = asyncio.get_event_loop()
# loop.create_task(connection.start())
loop.create_task(main(connection))
loop.run_forever()
