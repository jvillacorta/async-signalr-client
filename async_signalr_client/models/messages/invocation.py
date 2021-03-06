import typing
from async_signalr_client.models.messages.base import BaseSignalRMessage
from async_signalr_client.models.messages.types import SignalRMessageType


class InvocationMessage(BaseSignalRMessage):
    def __init__(self,
                 invocation_id: str,
                 target: str,
                 arguments: typing.List[typing.Any]):
        super().__init__(SignalRMessageType.INVOCATION)
        self.invocation_id = invocation_id
        self.target = target
        self.arguments = arguments
