import typing
import asyncio
import aiohttp
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError
from client.transports.base_transport import BaseTransport


class LongPollingTransport(BaseTransport):
    """
    Implements Long Polling Transport
    Reference: https://github.com/aspnet/AspNetCore/blob/master/src/SignalR/docs/specs/TransportProtocols.md
    """
    SECURE_SCHEME = 'https'
    UNSECURE_SCHEME = 'http'

    def __init__(self, url):
        super().__init__(url, 'LongPolling')
        self.last_connection_callback = None

    async def connect(self,
                      protocol: BaseSignalRProtocol,
                      queue: asyncio.Queue,
                      on_online: typing.Optional[typing.Callable[[None], None]] = None,
                      on_offline: typing.Optional[typing.Callable[[None], None]] = None):
        """
        Sets up the connection with the server, including the protocol negotiation
        """
        self.on_online = on_online
        self.on_offline = on_offline
        self.stop_event.clear()
        if await self.validate_transport() is not True:
            raise SignalRConnectionError(f"{self.transport_name} transport not available...")

        if self.conn is None:
            self.conn = aiohttp.ClientSession()
        loop = asyncio.get_event_loop()
        self.receive_task = loop.create_task(self.receive(queue))
        await self.send(protocol.encode(protocol.handshake_message()))

    async def receive(self, queue: asyncio.Queue):
        """
        Received packets from the server and adds the to the given queue
        """
        while not self.stop_event.is_set():
            try:
                r = await self.conn.get(self.url, params=dict(id=self.connection_id))
                if r.status == 200:
                    self.connection_state = 1
                    raw = await r.read()
                    content = raw.decode()
                    if content:
                        self.logger.debug(f"Received: {content}")
                        await queue.put(content)
                elif r.status == 204:
                    continue
                else:
                    self.connection_state = 0
                    raise SignalRConnectionError(f"Server returned unexpected status code: {r.status_code}")
            except asyncio.TimeoutError:
                pass
            finally:
                await asyncio.sleep(1)

    def _check_connection(self):
        """
        Triggers callbacks when connection state changes
        """
        if self.last_connection_callback != self.connection_state:
            self.last_connection_callback = self.connection_state
            if self.connection_state == 1:
                if self.on_online:
                    self.on_online()
            else:
                if self.on_offline:
                    self.on_offline()

    async def send(self, packet):
        """
        Sends packets to the server
        """
        self.logger.debug(f"Sent: {packet}")
        if self.conn and self.receive_task and not self.stop_event.is_set():
            await self.conn.post(self.url, params=dict(id=self.connection_id), data=packet)
        else:
            raise SignalRConnectionError("Unable to send packet as connection has not been established")

    async def stop(self):
        """
        Stops Long Polling transport connection
        """
        self.stop_event.set()
        if self.conn:
            self.conn.close()
