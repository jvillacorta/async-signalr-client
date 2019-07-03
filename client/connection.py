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
from io import StringIO

from client import protocols, models, exceptions


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
        self.ws = None  # Will hold reference to the websocket client
        self.url = url
        self.protocol = protocol
        self._state = SignalRConnectionState.OFFLINE  # Controls the state of the client
        self.establishing_connection_lock = asyncio.Lock()
        self.connection_established = asyncio.Future()  # Future set when connection and negotiation finishes
        self._completion_futures: typing.Dict[str, models.InvokeCompletionFuture] = dict()

        # Setup Logger
        self.logger = logging.getLogger("AsyncSignalRClient")
        t = logging.StreamHandler()
        t.setLevel(log_level)
        self.logger.addHandler(t)

    @property
    def state(self) -> SignalRConnectionState:
        return self._state

    def register_completion_futures(self, completion_future: models.InvokeCompletionFuture):
        if completion_future.invocation_id in self._completion_futures:
            self.logger.warning(f"InvocationId:{completion_future.invocation_id} already registered...")
        else:
            self._completion_futures[completion_future.invocation_id] = completion_future
        return self._completion_futures.get(completion_future.invocation_id)

    def set_completion(self, completion_message: models.CompletionMessage):
        completion_future = self._completion_futures.get(completion_message.invocation_id)
        if not completion_future:
            self.logger.warning(f"Completion Future for InvocationId:{completion_message.invocation_id} not found...")
        else:
            if completion_message.error:
                completion_future.set_exception(exceptions.SignalRCompletionServerError(completion_message.error))
            else:
                completion_future.set_result(completion_message.result)

    async def connect(self):
        """
        Connects to SignalR Server
        """
        if self.state == SignalRConnectionState.OFFLINE:
            async with self.establishing_connection_lock:
                self.ws: websockets.WebSocketClientProtocol = await websockets.connect(self.url)
                self._state = SignalRConnectionState.CONNECTING
                await self.ws.send(self.protocol.encode(self.protocol.handshake_message()))

    async def start(self):
        """
        Starts SignalR Connection and Processing
        - When starting the client it is recommended to wait for self.connection_established
          before executing any request
        """
        # INITIALIZING THE CONNECTION
        await self.connect()
        buffer = StringIO()
        while True:
            try:
                # CYCLE AND WAIT FOR DATA
                data = await asyncio.wait_for(self.ws.recv(), 0.1)
                for _char in data:
                    if _char == self.protocol.separator:
                        await self._execute(buffer.getvalue())
                        buffer = StringIO()
                    else:
                        buffer.write(_char)
            except asyncio.TimeoutError:
                pass
            except websockets.ConnectionClosed as e:
                if self.state is SignalRConnectionState.ONLINE:
                    self._state = SignalRConnectionState.DISCONNECTED
                else:
                    raise exceptions.SignalRConnectionError(e.reason)

    async def _execute(self, packet):
        if self.state is SignalRConnectionState.CONNECTING:
            message: models.HandshakeIncomingMessage = self.protocol.decode_handshake(packet)
            if message.error is not None:
                raise exceptions.SignalRConnectionError(message.error)
            else:
                self._state = SignalRConnectionState.ONLINE
                self.connection_established.set_result(SignalRConnectionState.ONLINE)
        else:
            message: models.BaseSignalRMessage = self.protocol.parse(packet)
            if message.type is models.SignalRMessageType.COMPLETION:
                message: models.CompletionMessage
                self.logger.info(f"COMPLETION: {message}")
                self.set_completion(message)

    async def invoke(self, target, *args) -> models.InvokeCompletionFuture:
        # Assemble message
        message = models.InvocationMessage(invocation_id=str(uuid.uuid4()),
                                           target=target,
                                           arguments=list(args))
        # Prepare Completion Future
        invoke_future = models.InvokeCompletionFuture(message.invocation_id)
        ret = self.register_completion_futures(invoke_future)
        # Encode and send message
        encoded_message = self.protocol.encode(message)
        self.logger.info(f"INVOKE: {encoded_message}")
        await self.ws.send(encoded_message)
        return ret
