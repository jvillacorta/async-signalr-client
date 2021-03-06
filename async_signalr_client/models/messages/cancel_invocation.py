from async_signalr_client.models.messages.base import BaseSignalRMessage
from async_signalr_client.models.messages.types import SignalRMessageType


class CancelInvocationMessage(BaseSignalRMessage):
    def __init__(self, invocation_id: str):
        super().__init__(SignalRMessageType.CANCEL_INVOCATION)
        self.invocation_id = invocation_id
