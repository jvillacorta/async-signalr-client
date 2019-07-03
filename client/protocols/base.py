from client.models.messages.base import BaseSignalRMessage


class BaseSignalRProtocol:
    def __init__(self, protocol, version, separator):
        self.protocol = protocol
        self.version = version
        self.separator = separator

    def decode_handshake(self, raw):
        raise NotImplementedError("Implementation Required")

    def handshake_message(self):
        raise NotImplementedError("Implementation Required")

    def decode(self, raw) -> BaseSignalRMessage:
        raise NotImplementedError("Implementation Required")

    def encode(self, message: BaseSignalRMessage):
        raise NotImplementedError("Implementation Required")
