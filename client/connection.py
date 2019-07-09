import uuid
import typing
import logging
import asyncio
import websockets
from enum import Enum
from io import StringIO

from client.models import messages, futures
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
        self._completion_futures: typing.Dict[str, messages.InvokeCompletionFuture] = dict()
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
        """
        Current client state
        """
        return self._state

    async def _call_handlers(self, message: messages.InvocationMessage):
        """
        Dispatches a task for each event handler registered to the client
        """
        handlers = self._handlers.get(message.target)
        if not handlers:
            self.logger.warning(f"Unable to find handler for event: {message.target}")
        else:
            loop = asyncio.get_event_loop()
            for handler in handlers:
                loop.create_task(handler(*message.arguments))

    def _register_completion_futures(self, completion_future: futures.InvokeCompletionFuture):
        """
        Register the completion future for capturing the downstream result in the near future
        """
        if completion_future.invocation_id in self._completion_futures:
            self.logger.warning(f"InvocationId:{completion_future.invocation_id} already registered...")
        else:
            self._completion_futures[completion_future.invocation_id] = completion_future
        return self._completion_futures.get(completion_future.invocation_id)

    def _set_completion(self, completion_message: messages.CompletionMessage):
        """
        Allocates completion to a pending invocation if available
        Note: An error in the completion message will cause a SignalRCompletionServerError exception to be raised
        """
        # Raise downstream error
        if completion_message.error:
            raise exceptions.SignalRCompletionServerError(completion_message.error)

        # Locate completion future pointer
        completion_future = self._completion_futures.get(completion_message.invocation_id)
        if not completion_future:
            self.logger.warning(f"Completion Future for InvocationId:{completion_message.invocation_id} not found...")
        else:
            # Set completion result
            # It is expected that a reference to this object is kept by the user when invoking
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
        # Initialize connection
        await self.connect()
        loop = asyncio.get_event_loop()
        self.process_task = loop.create_task(self.process())

        # Wait for protocol handshake to be executed
        try:
            await asyncio.wait_for(self.connection_established, self.connection_timeout)
        except asyncio.TimeoutError:
            raise exceptions.SignalRConnectionError(f"Unable to connect to {self.url} after a"
                                                    f"{self.connection_timeout} seconds timeout")

    async def stop(self):
        """
        Stops client and closes websocket connection
        """
        self.stop_event.set()
        if self.process_task and not self.process_task.cancelled():
            self.process_task.cancel()
        if self.ws:
            self.ws.close()
        await self.on_stop()

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
                # Cycle and wait for data
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
            message: messages.HandshakeIncomingMessage = self.protocol.decode_handshake(packet)
            if message.error is not None:
                raise exceptions.SignalRConnectionError(message.error)
            else:
                self._state = SignalRConnectionState.ONLINE
                self.connection_established.set_result(SignalRConnectionState.ONLINE)
                await self.on_start()
        else:
            message: messages.BaseSignalRMessage = self.protocol.parse(packet)
            if message.type is messages.SignalRMessageType.INVOCATION:
                message: messages.InvocationMessage
                self.logger.info(f"INVOKE: {message}")
                await self._call_handlers(message)
            elif message.type is messages.SignalRMessageType.COMPLETION:
                message: messages.CompletionMessage
                self.logger.info(f"COMPLETION: {message}")
                self._set_completion(message)

    async def on_start(self):
        """
        Called when connection is established
        """
        pass

    async def on_stop(self):
        """
        Called when connection is closed
        """
        pass

    async def invoke(self, target: str, *args: typing.Any) -> futures.InvokeCompletionFuture:
        """
        Sends Upstream Invokes with arguments
        """
        # Assemble message
        message = messages.InvocationMessage(invocation_id=str(uuid.uuid4()),
                                             target=target,
                                             arguments=list(args))
        # Prepare Completion Future
        invoke_future = futures.InvokeCompletionFuture(message.invocation_id)
        ret: futures.InvokeCompletionFuture = self._register_completion_futures(invoke_future)
        # Encode and send message
        encoded_message = self.protocol.encode(message)
        self.logger.info(f"INVOKE: {encoded_message}")
        # Send websocket packet
        await self.ws.send(encoded_message)
        return ret

    def on(self, event: str, callback: typing.Coroutine):
        """
        Register an async handler for a given event.
        Note: Events may have more than 1 handler and they will be called in the order they were registered
        """
        if event not in self._handlers:
            self._handlers[event] = [callback]
        else:
            self._handlers[event].append(callback)

    def off(self, event: str, callback: typing.Optional[typing.Coroutine] = None):
        """
        Removes one or all event handlers for a given event.
        Note: If callback is not specified then all handlers will be removed
        """
        if event in self._handlers:
            if callback is None:
                self.logger.info(f"Removing ALL event handler for {event}")
                self._handlers.pop(event)
            else:
                for handler in self._handlers.get('event', []):
                    if handler == callback:
                        self.logger.info(f"Removing an event handler for {event}")
                        self._handlers[event].remove(handler)
