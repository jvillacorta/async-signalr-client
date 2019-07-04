import pytest
from client import Connection, SignalRConnectionState, protocols


@pytest.mark.asyncio
async def test_json_protocol_negotiation(signalr_url):
    conn = Connection(signalr_url, protocol=protocols.JsonProtocol())
    await conn.start()
    assert conn.state == SignalRConnectionState.ONLINE
