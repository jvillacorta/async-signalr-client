import typing
import asyncio
import aiohttp
import logging
from urllib import parse
from client.protocols import BaseSignalRProtocol
from client.exceptions import SignalRConnectionError


class BaseTransport:
    SECURE_SCHEME = 'https'
    UNSECURE_SCHEME = 'http'

    def __init__(self,
                 url: str,
                 transport_name: str):
        self.url = self.normalize_url_scheme(url)
        self.conn = None  # Will hold client connection
        self.transport_name = transport_name
        self.logger = logging.getLogger(f"AsyncSignalRClient-{transport_name}Transport")
        self.connection_id = None
        self.stop_event = asyncio.Event()  # Event to notify that processing should stop
        self.receive_task = None  # This will hold the reference to the task receiving packets
        self.connection_state = None
        self.on_online = None
        self.on_offline = None

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

    async def connect(self,
                      protocol: BaseSignalRProtocol,
                      queue: asyncio.Queue,
                      on_online: typing.Optional[typing.Callable[[None], None]] = None,
                      on_offline: typing.Optional[typing.Callable[[None], None]] = None):
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

    SCHEMES = {
        "NON-SECURE": [
            "",
            "http",
            "ws"
        ],
        "SECURE": [
            "https",
            "wss"
        ]
    }

    def normalize_url_scheme(self, url: str):
        """
        This method replaces the url scheme with the expected scheme required for the transport
        """
        normalized_url = None
        parsed_url = parse.urlparse(url)
        scheme = parsed_url.scheme
        if self.UNSECURE_SCHEME == scheme or self.SECURE_SCHEME == scheme:
            normalized_url = url
        else:
            for scheme_type, scheme_list in self.SCHEMES.items():
                for valid_scheme in scheme_list:
                    if scheme == valid_scheme:
                        normalized_url = parse.urlunparse((scheme_type == "SECURE" and
                                                           self.SECURE_SCHEME or self.UNSECURE_SCHEME,
                                                           parsed_url.netloc,
                                                           parsed_url.path,
                                                           parsed_url.params,
                                                           parsed_url.query,
                                                           parsed_url.fragment))
        if normalized_url is None:
            raise SignalRConnectionError(f"Unable to normalize url: {self.url}")
        return normalized_url
