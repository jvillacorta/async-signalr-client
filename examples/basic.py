import logging
import asyncio
from client.connection import Connection, SignalRConnectionState

logging.basicConfig(level=logging.DEBUG)


async def main(conn):
    assert await conn.connection_established == SignalRConnectionState.ONLINE
    await conn.invoke("SendSample", "test1")
    await conn.invoke("InvokeSample", "test2", 500)


connection = Connection("ws://127.0.0.1:5000/chat")
loop = asyncio.get_event_loop()
loop.create_task(connection.start())
loop.create_task(main(connection))
loop.run_forever()
