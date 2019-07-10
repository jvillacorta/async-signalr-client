import asyncio
import aiohttp
from urllib import parse
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError


class BaseTransport:
    def __init__(self, url: str, trasport_name: str):
        self.url = url
        self.transport_name = trasport_name
        self.logger = None
        self.connection_id = None

    @staticmethod
    def _assemble_negotiate_url(url: str):
        parsed_url = parse.urlparse(url)
        scheme = parsed_url.scheme
        if 'http' not in scheme:
            if 'ws' in scheme:
                scheme = 'http'
            elif 'wss' in scheme:
                scheme = 'https'
            else:
                raise SignalRConnectionError(f"Unsupported scheme: {scheme}")

        return parse.urlunparse((scheme,
                                 parsed_url.netloc,
                                 f"{parsed_url.path}/negotiate",
                                 parsed_url.params,
                                 parsed_url.query,
                                 parsed_url.fragment))

    async def validate_transport(self):
        """
        Ensures transport is compatible with server
        """
        async with aiohttp.ClientSession() as session:
            r = await session.post(self._assemble_negotiate_url(self.url))
            response = await r.json()
            if self.logger:
                self.logger.debug(f"Available transports: {response}")
            for protocol in response.get('availableTransports', []):
                if self.transport_name == protocol.get('transport', ''):
                    self.connection_id = response.get('connectionId', None)
                    return True
        return False

    async def connect(self, protocol: BaseSignalRProtocol, queue: asyncio.Queue):
        """
        This method connects the client with the server using the selected transport
        """
        raise NotImplementedError("Implementation Required")

    async def receive(self, queue: asyncio.Queue):
        """
        This method starts receiving information from the server and adds each payload to the given queue
        """
        raise NotImplementedError("Implementation Required")

    async def send(self, packet):
        """
        This method sends packet to the server
        """
        raise NotImplementedError("Implementation Required")

    async def stop(self):
        """
        This method stops the transport connection
        """
        raise NotImplementedError("Implementation Required")
