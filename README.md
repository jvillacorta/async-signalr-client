# async-signalr-client
Python Async SignalR DotNetCore Client

This library implements the SignalR JSON protocol using asyncio.  Note: Streaming is currently not supported.

### Launching the Client
```python
from async_signalr_client.connection import Connection

async def main():
    # This will create the connection instance but will not launch any connection
    connection = Connection("ws://127.0.0.1:5000/chat")
    # This will establish the connection and negotiate protocol
    await connection.start()
```

**Connection Parameters:**
- url --> Url of the hub (_Note: use ws(s) scheme for Websocket Transport_)
- transport --> `client.transport.WebSocketTransport` (Default) or `client.transport.LongPollingTransport`
- protocol --> `client.protocol.JsonProtocol()` (Default)
- connection_timeout --> Timeout connection when no ping is received for the given interval in seconds
- log_level --> Standard library LogLevel  

### Invoking
```python
from async_signalr_client.connection import Connection

async def main():
    connection = Connection("ws://127.0.0.1:5000/chat")
    await connection.start()
    # Sends a message to target foo with 1 string parameter
    await connection.invoke("foo", "bar")
```

### Invoke Completions
```python
from async_signalr_client.connection import Connection
from async_signalr_client.exceptions import SignalRCompletionServerError

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
from async_signalr_client.connection import Connection

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