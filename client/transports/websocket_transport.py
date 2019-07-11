import asyncio
import websockets
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError
from client.transports.base_transport import BaseTransport


class WebSocketTransport(BaseTransport):
    """
    Implements WebSocket Transport
    Reference: https://github.com/aspnet/AspNetCore/blob/master/src/SignalR/docs/specs/TransportProtocols.md
    """
    SECURE_SCHEME = 'wss'
    UNSECURE_SCHEME = 'ws'

    def __init__(self, url):
        super().__init__(url, 'WebSockets')

    async def connect(self, protocol: BaseSignalRProtocol, queue: asyncio.Queue):
        """
        Sets up the connection with the websocket server, including the protocol negotiation
        """
        self.stop_event.clear()
        if await self.validate_transport() is not True:
            raise SignalRConnectionError(f"{self.transport_name} transport not available...")
        if not self.conn:
            self.conn: websockets.WebSocketClientProtocol = await websockets.connect(self.url)
        await self.send(protocol.encode(protocol.handshake_message()))
        loop = asyncio.get_event_loop()
        self.receive_task = loop.create_task(self.receive(queue))

    async def receive(self, queue: asyncio.Queue):
        """
        Received packets from the websocket server and adds the to the given queue
        """
        while not self.stop_event.is_set():
            try:
                data = await asyncio.wait_for(self.conn.recv(), 0.1)
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
        if self.conn and self.receive_task and not self.stop_event.is_set():
            await self.conn.send(packet)
        else:
            raise SignalRConnectionError("Unable to send packet as connection has not been established")

    async def stop(self):
        """
        Stops websocket transport connection
        """
        self.stop_event.set()
        if self.conn:
            self.conn.close()
