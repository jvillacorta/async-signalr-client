import asyncio
import logging
import websockets
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError
from client.transports.base_transport import BaseTransport


class WebSocketTransport(BaseTransport):
    """
    Implements WebSocket Transport
    Reference: https://github.com/aspnet/AspNetCore/blob/master/src/SignalR/docs/specs/TransportProtocols.md
    """

    def __init__(self, url):
        super().__init__(url, 'WebSockets')
        self.ws = None  # This will hold the reference to the websocket client
        self.stop = asyncio.Event()  # Event to notify that processing should stop
        self.receive_task = None  # This will hold the reference to the task receiving packets
        self.logger = logging.getLogger("AsyncSignalRClient-WebSocketTransport")

    async def connect(self, protocol: BaseSignalRProtocol, queue: asyncio.Queue):
        """
        Sets up the connection with the websocket server, including the protocol negotiation
        """
        self.stop.clear()
        if self.validate_transport() is not True:
            raise SignalRConnectionError(f"{self.transport_name} transport not available...")
        self.ws: websockets.WebSocketClientProtocol = await websockets.connect(self.url)
        await self.send(protocol.encode(protocol.handshake_message()))
        loop = asyncio.get_event_loop()
        self.receive_task = loop.create_task(self.receive(queue))

    async def receive(self, queue: asyncio.Queue):
        """
        Received packets from the websocket server and adds the to the given queue
        """
        while not self.stop.is_set():
            try:
                data = await asyncio.wait_for(self.ws.recv(), 0.1)
                self.logger.debug(f"Received: {data}")
                if data:
                    await queue.put(data)
            except asyncio.TimeoutError:
                pass

    async def send(self, packet):
        """
        Sends packets to the websocket server
        """
        self.logger.debug(f"Sent: {packet}")
        await self.ws.send(packet)

    async def stop(self):
        """
        Stops websocket transport connection
        """
        self.stop.set()
        if self.ws:
            self.ws.close()
