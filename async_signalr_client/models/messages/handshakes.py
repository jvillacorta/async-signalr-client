from async_signalr_client.models.messages.base import BaseMessage


class HandshakeIncomingMessage(BaseMessage):
    def __init__(self, error):
        self.error = error


class HandshakeOutgoingMessage(BaseMessage):
    def __init__(self, protocol, version):
        self.protocol = protocol
        self.version = version
