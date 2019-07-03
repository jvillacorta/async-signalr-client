from client import models


class BaseSignalRProtocol:
    def __init__(self, protocol, version, separator):
        self.protocol = protocol
        self.version = version
        self.separator = separator

    def decode_handshake(self, raw):
        raise NotImplementedError("Implementation Required")

    def handshake_message(self):
        raise NotImplementedError("Implementation Required")

    def decode(self, raw) -> models.BaseSignalRMessage:
        raise NotImplementedError("Implementation Required")

    def parse(self, raw) -> models.BaseSignalRMessage:
        raise NotImplementedError("Implementation Required")

    def encode(self, message: models.BaseSignalRMessage):
        raise NotImplementedError("Implementation Required")
