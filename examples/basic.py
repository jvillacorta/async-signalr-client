import asyncio
from client.connection import Connection

connection = Connection("ws://127.0.0.1:5000/chat")
loop = asyncio.get_event_loop()
loop.run_until_complete(connection.start())
