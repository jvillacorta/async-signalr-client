import json
import time
import uuid
import random
import typing
import logging
import asyncio
import inspect
import traceback
import websockets
from enum import Enum

from client import protocols, models
from client.exceptions import SignalRConnectionError


class SignalRConnectionState(Enum):
    OFFLINE = 1
    CONNECTING = 2
    ONLINE = 3
    RE_CONNECTING = 4


class Connection:
    def __init__(self,
                 url: str,
                 protocol: protocols.BaseSignalRProtocol = protocols.JsonProtocol(),
                 log_level: int = logging.DEBUG):
        self.ws = None
        self.url = url
        self.protocol = protocol
        self._state = SignalRConnectionState.OFFLINE
        # Setup Logger
        self.logger = logging.getLogger("AsyncSignalRClient")
        t = logging.StreamHandler()
        t.setLevel(log_level)
        self.logger.addHandler(t)

    @property
    def state(self) -> SignalRConnectionState:
        return self._state

    async def connect(self):
        """
        Connects to SignalR Server
        """
        if self.state == SignalRConnectionState.OFFLINE:
            self.ws: websockets.WebSocketClientProtocol = await websockets.connect(self.url)
            self._state = SignalRConnectionState.CONNECTING
            await self.ws.send(self.protocol.encode(self.protocol.handshake_message()))

    async def start(self):
        """
        Starts SignalR Connection and Processing
        """
        await self.connect()
        buffer = ''
        while True:
            try:
                # CYCLE AND WAIT FOR DATA
                data = await asyncio.wait_for(self.ws.recv(), 0.1)
                for _char in data:
                    if _char == self.protocol.separator:
                        await self._execute(buffer)
                        buffer = ''
                    else:
                        buffer += _char
            except asyncio.TimeoutError:
                pass
            except websockets.ConnectionClosed as e:
                if self.state is SignalRConnectionState.ONLINE:
                    self._state = SignalRConnectionState.DISCONNECTED
                else:
                    raise SignalRConnectionError(e.reason)

    async def _execute(self, packet):
        if self.state is SignalRConnectionState.CONNECTING:
            message: models.HandshakeIncomingMessage = self.protocol.decode_handshake(packet)
            if message.error is not None:
                raise SignalRConnectionError(message.error)
            else:
                self._state = SignalRConnectionState.ONLINE
        else:
            message: models.BaseSignalRMessage = self.protocol.decode(packet)
