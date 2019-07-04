import json

from client import models, protocols, exceptions


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        # Return Message Type Integer
        if isinstance(obj, models.SignalRMessageType):
            return obj.value
        # Normalize Invocation Id Property
        if "invocation_id" in obj.__dict__:
            obj.__dict__["invocationId"] = obj.__dict__["invocation_id"]
            del obj.__dict__["invocation_id"]
        return obj.__dict__


class JsonProtocol(protocols.BaseSignalRProtocol):
    def __init__(self):
        super().__init__("json", 1, chr(0x1E))

    def _escape(self, raw: str) -> str:
        return raw.replace(self.separator, "")

    def decode_handshake(self, raw) -> models.HandshakeIncomingMessage:
        data = self.decode(raw)
        return models.HandshakeIncomingMessage(data.get('error', None))

    def handshake_message(self) -> models.HandshakeOutgoingMessage:
        return models.HandshakeOutgoingMessage(self.protocol, self.version)

    def decode(self, raw) -> dict:
        try:
            clean = raw.replace(self.separator, "")
            return json.loads(clean)
        except (TypeError, json.decoder.JSONDecodeError):
            raise exceptions.SignalRInvalidMessageError(f"Unable to decode message.\n{raw}")

    def parse(self, raw) -> models.BaseSignalRMessage:
        decoded_payload = self.decode(raw)
        message_type = models.SignalRMessageType(decoded_payload.get("type", -1))
        if message_type is models.SignalRMessageType.INVALID:
            raise exceptions.SignalRInvalidMessageError(f"Unsupported message received:\n{decoded_payload}")

        # FIND MESSAGE TYPE
        if message_type is models.SignalRMessageType.INVOCATION:
            return models.InvocationMessage(invocation_id=decoded_payload.get('invocationId', None),
                                            target=decoded_payload.get('target', None),
                                            arguments=decoded_payload.get('arguments', None))
        elif message_type is models.SignalRMessageType.STREAM_ITEM:
            return models.StreamItemMessage(invocation_id=decoded_payload.get('invocationId', None),
                                            item=decoded_payload.get('item', None))
        elif message_type is models.SignalRMessageType.COMPLETION:
            return models.CompletionMessage(invocation_id=decoded_payload.get('invocationId', None),
                                            result=decoded_payload.get('result', None),
                                            error=decoded_payload.get('error', None))
        elif message_type is models.SignalRMessageType.STREAM_INVOCATION:
            return models.StreamInvocationMessage(invocation_id=decoded_payload.get('invocationId', None),
                                                  target=decoded_payload.get('target', None),
                                                  arguments=decoded_payload.get('arguments', None))
        elif message_type is models.SignalRMessageType.CANCEL_INVOCATION:
            return models.CancelInvocationMessage(invocation_id=decoded_payload.get('invocationId', None))
        elif message_type is models.SignalRMessageType.PING:
            return models.PingMessage()
        elif message_type is models.SignalRMessageType.CLOSE:
            return models.CloseMessage(error=decoded_payload.get('error', None))

    def encode(self, message: models.BaseMessage):
        return JsonEncoder().encode(message) + self.separator
