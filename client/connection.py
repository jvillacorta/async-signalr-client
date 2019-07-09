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
    handler_prefix = 'on_'

    def __init__(self,
                 url: str,
                 protocol: protocols.BaseSignalRProtocol = protocols.JsonProtocol(),
                 connection_timeout: int = 20,
                 log_level: int = logging.DEBUG):
        self.ws = None  # Will hold reference to the websocket client
        self.process_task = None
        self.url = url
        self.protocol = protocol
        self.connection_timeout = connection_timeout
        self._state = SignalRConnectionState.OFFLINE  # Controls the state of the client
        self.establishing_connection_lock = asyncio.Lock()
        self.connection_established = asyncio.Future()  # Future set when connection and negotiation finishes
        self._completion_futures: typing.Dict[str, models.InvokeCompletionFuture] = dict()
        self.stop_event = asyncio.Event()

        # Register handlers
        self._handlers = dict()
        for x in dir(self):
            if x.startswith(self.handler_prefix):
                event = x[len(self.handler_prefix):]
                self._handlers[event] = [getattr(self, x)]

        # Setup Logger
        self.logger = logging.getLogger("AsyncSignalRClient")
        t = logging.StreamHandler()
        t.setLevel(log_level)
        self.logger.addHandler(t)

    @property
    def state(self) -> SignalRConnectionState:
        return self._state

    async def call_handlers(self, message: models.InvocationMessage):
        handlers = self._handlers.get(message.target)
        if not handlers:
            self.logger.warning(f"Unable to find handler for event: {message.target}")
        else:
            loop = asyncio.get_event_loop()
            for handler in handlers:
                loop.create_task(handler(*message.arguments))

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
                raise exceptions.SignalRCompletionServerError(completion_message.error)
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
        """
        # INITIALIZING THE CONNECTION
        await self.connect()
        loop = asyncio.get_event_loop()
        self.process_task = loop.create_task(self.process())

        try:
            await asyncio.wait_for(self.connection_established, self.connection_timeout)
        except asyncio.TimeoutError:
            raise exceptions.SignalRConnectionError(f"Unable to connect to {self.url} after a"
                                                    f"{self.connection_timeout} seconds timeout")

    async def stop(self):
        self.stop_event.set()
        if self.process_task and not self.process_task.cancelled():
            self.process_task.cancel()
        if self.ws:
            self.ws.close()

    async def process(self):
        """
        Listens for incoming payloads dispatches a new task for each full message received
        """
        loop = asyncio.get_event_loop()
        buffer = StringIO()
        while True:
            try:
                if self.stop_event.is_set():
                    return
                # CYCLE AND WAIT FOR DATA
                data = await asyncio.wait_for(self.ws.recv(), 0.1)
                for _char in data:
                    if _char == self.protocol.separator:
                        loop.create_task(self._execute(buffer.getvalue()))
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

    async def _execute(self, packet: str):
        """
        Executes actions based on message type
        """
        if self.state is SignalRConnectionState.CONNECTING:
            message: models.HandshakeIncomingMessage = self.protocol.decode_handshake(packet)
            if message.error is not None:
                raise exceptions.SignalRConnectionError(message.error)
            else:
                self._state = SignalRConnectionState.ONLINE
                self.connection_established.set_result(SignalRConnectionState.ONLINE)
                await self.on_start()
        else:
            message: models.BaseSignalRMessage = self.protocol.parse(packet)
            if message.type is models.SignalRMessageType.INVOCATION:
                message: models.InvocationMessage
                self.logger.info(f"INVOKE: {message}")
                await self.call_handlers(message)
            elif message.type is models.SignalRMessageType.COMPLETION:
                message: models.CompletionMessage
                self.logger.info(f"COMPLETION: {message}")
                self.set_completion(message)

    async def on_start(self):
        """
        Called when connection is established
        """
        pass

    async def invoke(self, target: str, *args: typing.Any) -> models.InvokeCompletionFuture:
        """
        Sends Upstream Invokes with arguments
        """
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

    def on(self, event: str, callback: typing.Coroutine):
        if event not in self._handlers:
            self._handlers[event] = [callback]
        else:
            self._handlers[event].append(callback)
