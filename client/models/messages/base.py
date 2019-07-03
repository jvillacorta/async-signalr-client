from .types import SignalRMessageType


class BaseMessage:
    def __str__(self):
        attrs = {f"{k}={v}" for k, v in self.__dict__}
        return f"{self.__class__}[{attrs}]"


class BaseSignalRMessage(BaseMessage):
    def __init__(self, message_type: SignalRMessageType):
        self.type = message_type
