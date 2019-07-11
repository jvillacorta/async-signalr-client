import asyncio
import logging
import aiohttp
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError
from client.transports.base_transport import BaseTransport


class LongPollingTransport(BaseTransport):
    """
    Implements Long Polling Transport
    Reference: https://github.com/aspnet/AspNetCore/blob/master/src/SignalR/docs/specs/TransportProtocols.md
    """

    def __init__(self, url):
        super().__init__(url, 'LongPolling')

    async def connect(self, protocol: BaseSignalRProtocol, queue: asyncio.Queue):
        """
        Sets up the connection with the server, including the protocol negotiation
        """
        self.stop_event.clear()
        if await self.validate_transport() is not True:
            raise SignalRConnectionError(f"{self.transport_name} transport not available...")

        if self.conn is None:
            self.conn = aiohttp.ClientSession()
        await self.send(protocol.encode(protocol.handshake_message()))
        loop = asyncio.get_event_loop()
        self.receive_task = loop.create_task(self.receive(queue))

    async def receive(self, queue: asyncio.Queue):
        """
        Received packets from the server and adds the to the given queue
        """
        while not self.stop_event.is_set():
            try:
                r = await self.conn.get(self.url, params=dict(id=self.connection_id))
                if r.status == 200:
                    raw = await r.read()
                    content = raw.decode()
                    if content:
                        self.logger.debug(f"Received: {content}")
                        await queue.put(content)
                elif r.status == 204:
                    continue
                else:
                    raise SignalRConnectionError(f"Server returned unexpected status code: {r.status_code}")
            except asyncio.TimeoutError:
                pass
            finally:
                await asyncio.sleep(1)

    async def send(self, packet):
        """
        Sends packets to the server
        """
        self.logger.debug(f"Sent: {packet}")
        await self.conn.post(self.url, params=dict(id=self.connection_id), data=packet)

    async def stop(self):
        """
        Stops Long Polling transport connection
        """
        self.stop_event.set()
        if self.conn:
            self.conn.close()
