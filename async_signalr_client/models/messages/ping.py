from async_signalr_client.models.messages.base import BaseSignalRMessage
from async_signalr_client.models.messages.types import SignalRMessageType


class PingMessage(BaseSignalRMessage):
    def __init__(self):
        super().__init__(SignalRMessageType.PING)
