import json
import msgpack
from client.models import messages
from client import protocols, exceptions


class JsonEncoder(json.JSONEncoder):
    """
    Custom Json Encoder to handle nuances of custom models and types
    """

    def default(self, obj):
        # Return Message Type Integer
        if isinstance(obj, messages.SignalRMessageType):
            return obj.value
        # Normalize Invocation Id Property
        if "invocation_id" in obj.__dict__:
            obj.__dict__["invocationId"] = obj.__dict__["invocation_id"]
            del obj.__dict__["invocation_id"]
        return obj.__dict__


class MessagePackProtocol(protocols.BaseSignalRProtocol):
    def __init__(self):
        super().__init__("messagepack", 1, chr(0x1E))

    def _escape(self, raw: str) -> str:
        return raw.replace(self.separator, "")

    def decode_handshake(self, raw) -> messages.HandshakeIncomingMessage:
        """
        Process downstream handshake
        """
        data = json.loads(self._escape(raw.decode()))
        return messages.HandshakeIncomingMessage(data.get('error', None))

    def handshake_message(self) -> messages.HandshakeOutgoingMessage:
        """
        Prepare handshake request message
        """
        return messages.HandshakeOutgoingMessage(self.protocol, self.version)

    def decode(self, raw) -> dict:
        """
        Decodes downstream packets
        """
        print(msgpack.loads(raw))
        # try:
        #     # Remove separator character
        #     clean = self._escape(raw)
        #     # Parse JSON String into a python object
        #     return json.loads(self._escape(clean))
        # except (TypeError, json.decoder.JSONDecodeError):
        #     raise exceptions.SignalRInvalidMessageError(f"Unable to decode message.\n{raw}")

    def parse(self, raw) -> messages.BaseSignalRMessage:
        """
        Parse downstream packets into client models
        """
        pass

    def encode(self, message: messages.BaseMessage):
        """
        Converts a client message into a JSON string with a separation character
        """
        if isinstance(message, messages.HandshakeOutgoingMessage):
            return JsonEncoder().encode(message) + self.separator
        else:
            message_type = messages.SignalRMessageType(getattr(message, 'type', -1))
            packed = [
                message_type.value,
                {}
            ]
            if message_type == messages.SignalRMessageType.INVOCATION:
                message: messages.InvocationMessage
                print(bytearray(message.invocation_id.encode(encoding='UTF-8')))
                packed.append(message.invocation_id.encode(encoding='UTF-8'))
                packed.append(message.target)
                packed.append(message.arguments)
                packed.append([])
            ret = msgpack.packb(packed, use_bin_type=True)
            print(msgpack.unpackb(ret, raw=False))
            return ret
        # msgpack.loads(packed)
