from client.models import messages


class BaseSignalRProtocol:
    """
    Base SignalR Protocol class
    - Defines interface that all protocols should implement
    """

    def __init__(self, protocol: str, version: int, separator: str):
        self.protocol = protocol
        self.version = version
        self.separator = separator

    def decode_handshake(self, raw):
        """
        This method should decode the downstream handshake packet and return a message object
        """
        raise NotImplementedError("Implementation Required")

    def handshake_message(self):
        """
        This method assemble and return a handshake request message
        """
        raise NotImplementedError("Implementation Required")

    def decode(self, raw) -> messages.BaseSignalRMessage:
        """
        This method should decode a raw packet into a python object
        """
        raise NotImplementedError("Implementation Required")

    def parse(self, raw) -> messages.BaseSignalRMessage:
        """
        This method should parse a raw packet into a SignalRMessage
        """
        raise NotImplementedError("Implementation Required")

    def encode(self, message: messages.BaseSignalRMessage):
        """
        This method should encode a SignalRMessage into a protocol standard payload
        """
        raise NotImplementedError("Implementation Required")
