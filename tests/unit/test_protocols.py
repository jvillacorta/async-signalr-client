import pytest
from client.models.messages import InvocationMessage, CompletionMessage, PingMessage
from client.protocols import JsonProtocol


@pytest.mark.parametrize("raw, result", [
    ('{}', None),
    ('{"error": "invalid"}', "invalid")
])
def test_decode_handshake(raw, result):
    protocol = JsonProtocol()
    r = protocol.decode_handshake(raw)
    assert r.error == result


def test_handshake_message():
    protocol = JsonProtocol()
    assert protocol.handshake_message().protocol == 'json'
    assert protocol.handshake_message().version == 1


@pytest.mark.parametrize("raw, obj_type", [
    (
            "{\"type\": 1, \"target\": \"RequestMessage\", \"arguments\": [\"message\", \"test\", "
            "\"signalr message\"], \"invocationId\": \"e7899dfc-a5f4-447f-8107-a2d86cf26666\"}",
            InvocationMessage),
    (
            "{\"type\":3,\"invocationId\":\"b6f2cf89-18e8-44ff-a1ff-63abce936960\",\"result\":"
            "\"signalr completion\"}",
            CompletionMessage
    ),
    (
            "{\"type\": 6}",
            PingMessage
    )
])
def test_parse(raw, obj_type):
    protocol = JsonProtocol()
    assert type(protocol.parse(raw)) is obj_type
