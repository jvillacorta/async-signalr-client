import typing
from client.models.messages.base import BaseSignalRMessage
from client.models.messages.types import SignalRMessageType


class CloseMessage(BaseSignalRMessage):
    def __init__(self, error: typing.Optional[str] = None):
        super().__init__(SignalRMessageType.CLOSE)
        self.error = error
