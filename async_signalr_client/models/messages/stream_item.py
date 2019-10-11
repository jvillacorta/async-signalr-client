import typing
from async_signalr_client.models.messages.base import BaseSignalRMessage
from async_signalr_client.models.messages.types import SignalRMessageType


class StreamItemMessage(BaseSignalRMessage):
    def __init__(self, invocation_id: str, item: typing.Any):
        super().__init__(SignalRMessageType.STREAM_ITEM)
        self.invocation_id = invocation_id
        self.item = item
