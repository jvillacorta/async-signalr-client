import logging
import asyncio
from client.connection import Connection

logging.basicConfig(level=logging.DEBUG)


class ChatClient(Connection):

    async def activity(self):
        await self.start()
        completion_future = await self.invoke("InvokeSample", "signalr completion", 500)
        await completion_future
        print(completion_future.result())
        await self.invoke("RequestMessage", "message", "test", "signalr message")
        await self.invoke("RequestBroadcast", "broadcast", "signalr broadcast")

    async def on_message(self, name, message):
        print(f"Received Message: name={name},message={message}")

    async def on_broadcast(self, message):
        print(f"Received Broadcast:message={message}")


connection = ChatClient("ws://127.0.0.1:5000/chat")
loop = asyncio.get_event_loop()
loop.create_task(connection.activity())
loop.run_forever()
