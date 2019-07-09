# async-signalr-client
Python Async SignalR DotNetCore Client

This library implements the SignalR JSON protocol using asyncio.  Note: Streaming is currently not supported.

### Launching the Client
```python
from client.connection import Connection

async def main():
    # This will create the connection instance but will not launch any connection
    connection = Connection("ws://127.0.0.1:5000/chat")
    # This will establish the connection and negotiate protocol
    await connection.start()
```

### Invoking
```python
from client.connection import Connection

async def main():
    connection = Connection("ws://127.0.0.1:5000/chat")
    await connection.start()
    # Sends a message to target foo with 1 string parameter
    await connection.invoke("foo", "bar")
```

### Invoke Completions
```python
from client.connection import Connection
from client.exceptions import SignalRCompletionServerError

async def main():
    connection = Connection("ws://127.0.0.1:5000/chat")
    await connection.start()
    completion = await connection.invoke("foo", "bar")
    # ... perform other tasks ...
    try:
        # Wait until completion is received
        # Retrieve completion payload
        await completion
        # Note: If completions returns an error "SignalRCompletionServerError" will be raised
        print(completion.result())
    except SignalRCompletionServerError as e:
        print(e) 
```


### Receiving a message
```python
import asyncio
from client.connection import Connection

class ChatClient(Connection):

    async def activity(self):
        await self.start()

    # Using the prefix "on_" the handler is automatically added 
    async def on_foo(self, bar):
        print(f"Received Foo: bar={bar}")

async def test(bar):
    print(f"Received Foo: bar={bar}")

connection = ChatClient("ws://127.0.0.1:5000/chat")
# Register a handler for foo
connection.on("foo", test)
loop = asyncio.get_event_loop()
loop.create_task(connection.activity())
loop.run_forever()
```