import typing
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

    async def connect(self,
                      protocol: BaseSignalRProtocol,
                      queue: asyncio.Queue,
                      on_online: typing.Optional[typing.Callable[[None], None]] = None,
                      on_offline: typing.Optional[typing.Callable[[None], None]] = None):
        """
        Sets up the connection with the websocket server, including the protocol negotiation
        """
        self.on_online = on_online
        self.on_offline = on_offline
        self.stop_event.clear()
        if await self.validate_transport() is not True:
            raise SignalRConnectionError(f"{self.transport_name} transport not available...")
        if not self.conn:
            self.conn: websockets.WebSocketClientProtocol = await websockets.connect(self.url)
        loop = asyncio.get_event_loop()
        self.receive_task = loop.create_task(self.receive(queue))
        await self.send(protocol.encode(protocol.handshake_message()))

    async def receive(self, queue: asyncio.Queue):
        """
        Received packets from the websocket server and adds the to the given queue
        """
        while not self.stop_event.is_set():
            try:
                self._check_connection()
                data = await asyncio.wait_for(self.conn.recv(), 0.1)
                self.logger.debug(f"Received: {data}")
                if data:
                    await queue.put(data)
            except asyncio.TimeoutError:
                pass
            except (websockets.ConnectionClosed, websockets.InvalidState, websockets.ProtocolError) as e:

                raise SignalRConnectionError(e)

    def _check_connection(self):
        """
        Triggers callbacks when connection state changes
        """
        state = self.conn.state
        if self.connection_state != state:
            self.connection_state = self.conn.state
            if state is websockets.protocol.State.OPEN:
                if self.on_online:
                    self.on_online()
            elif state in (websockets.protocol.State.CLOSED, websockets.protocol.State.CLOSING):
                if self.on_offline:
                    self.on_offline()

    async def send(self, packet):
        """
        Sends packets to the websocket server
        """
        self.logger.debug(f"Sent: {packet}")
        if self.conn and self.receive_task and not self.stop_event.is_set():
            try:
                self._check_connection()
                await self.conn.send(packet)
            except websockets.WebSocketException:
                self._check_connection()
                raise SignalRConnectionError("Connection was closed unexpectedly")
        else:
            raise SignalRConnectionError("Unable to send packet as connection has not been established")

    async def stop(self):
        """
        Stops websocket transport connection
        """
        self.stop_event.set()
        if self.conn:
            self.conn.close()
