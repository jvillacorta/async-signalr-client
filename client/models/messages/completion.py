import typing
from client.models.messages.base import BaseSignalRMessage
from client.models.messages.types import SignalRMessageType


class CompletionMessage(BaseSignalRMessage):
    def __init__(self, invocation_id: str, result: str, error: str):
        super().__init__(SignalRMessageType.INVOCATION)
        self.invocation_id = invocation_id
        self.result = result
        self.error = error
