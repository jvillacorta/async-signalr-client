import typing
from async_signalr_client.models.messages.base import BaseSignalRMessage
from async_signalr_client.models.messages.types import SignalRMessageType


class CompletionMessage(BaseSignalRMessage):
    def __init__(self, invocation_id: str, result: typing.Optional[str] = None, error: typing.Optional[str] = None):
        super().__init__(SignalRMessageType.COMPLETION)
        self.invocation_id = invocation_id
        self.result = result
        self.error = error
