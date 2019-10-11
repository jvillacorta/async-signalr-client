import json
from async_signalr_client.models import messages
from async_signalr_client import protocols, exceptions


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


class JsonProtocol(protocols.BaseSignalRProtocol):
    """
    Implements the SignalR JSON Hub protocol.
    Reference: https://github.com/aspnet/AspNetCore/blob/master/src/SignalR/docs/specs/HubProtocol.md
    """

    def __init__(self):
        super().__init__("json", 1, chr(0x1E))

    def _escape(self, raw: str) -> str:
        return raw.replace(self.separator, "")

    def decode_handshake(self, raw) -> messages.HandshakeIncomingMessage:
        """
        Process downstream handshake
        """
        data = self.decode(raw)
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
        try:
            # Remove separator character
            clean = self._escape(raw)
            # Parse JSON String into a python object
            return json.loads(self._escape(clean))
        except (TypeError, json.decoder.JSONDecodeError):
            raise exceptions.SignalRInvalidMessageError(f"Unable to decode message.\n{raw}")

    def parse(self, raw) -> messages.BaseSignalRMessage:
        """
        Parse downstream packets into async_signalr_client models
        """
        # Convert packet into a python object
        decoded_payload = self.decode(raw)
        # Retrieve message type
        # Assume message without type is invalid
        message_type = messages.SignalRMessageType(decoded_payload.get("type", messages.SignalRMessageType.INVALID))
        if message_type is messages.SignalRMessageType.INVALID:
            raise exceptions.SignalRInvalidMessageError(f"Unsupported message received:\n{decoded_payload}")

        # Convert payload to appropriate Client Message
        if message_type is messages.SignalRMessageType.INVOCATION:
            return messages.InvocationMessage(invocation_id=decoded_payload.get('invocationId', None),
                                              target=decoded_payload.get('target', None),
                                              arguments=decoded_payload.get('arguments', None))

        elif message_type is messages.SignalRMessageType.STREAM_ITEM:
            return messages.StreamItemMessage(invocation_id=decoded_payload.get('invocationId', None),
                                              item=decoded_payload.get('item', None))

        elif message_type is messages.SignalRMessageType.COMPLETION:
            return messages.CompletionMessage(invocation_id=decoded_payload.get('invocationId', None),
                                              result=decoded_payload.get('result', None),
                                              error=decoded_payload.get('error', None))

        elif message_type is messages.SignalRMessageType.STREAM_INVOCATION:
            return messages.StreamInvocationMessage(invocation_id=decoded_payload.get('invocationId', None),
                                                    target=decoded_payload.get('target', None),
                                                    arguments=decoded_payload.get('arguments', None))

        elif message_type is messages.SignalRMessageType.CANCEL_INVOCATION:
            return messages.CancelInvocationMessage(invocation_id=decoded_payload.get('invocationId', None))

        elif message_type is messages.SignalRMessageType.PING:
            return messages.PingMessage()

        elif message_type is messages.SignalRMessageType.CLOSE:
            return messages.CloseMessage(error=decoded_payload.get('error', None))

    def encode(self, message: messages.BaseMessage):
        """
        Converts a async_signalr_client message into a JSON string with a separation character
        """
        return JsonEncoder().encode(message) + self.separator
