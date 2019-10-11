import pytest
import asyncio
import aiohttp
import websockets
from asynctest import CoroutineMock, MagicMock
from async_signalr_client.protocols import BaseSignalRProtocol
from async_signalr_client.exceptions import SignalRConnectionError
from async_signalr_client.transports import LongPollingTransport, WebSocketTransport


@pytest.mark.parametrize("transport, actual_url, expected_url", [
    (LongPollingTransport, "http://foo.bar", "http://foo.bar"),
    (LongPollingTransport, "https://foo.bar", "https://foo.bar"),
    (LongPollingTransport, "ws://foo.bar", "http://foo.bar"),
    (LongPollingTransport, "wss://foo.bar", "https://foo.bar"),
    (WebSocketTransport, "http://foo.bar", "ws://foo.bar"),
    (WebSocketTransport, "https://foo.bar", "wss://foo.bar"),
    (WebSocketTransport, "ws://foo.bar", "ws://foo.bar"),
    (WebSocketTransport, "wss://foo.bar", "wss://foo.bar")
])
def test_normalize_url(transport, actual_url, expected_url):
    instance = transport(actual_url)
    assert instance.url == expected_url


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", [
    LongPollingTransport,
    WebSocketTransport
])
async def test_connect(transport):
    instance = transport('http://foo.bar:5000')
    # Mock Dependencies
    instance.conn = CoroutineMock()
    instance.send = CoroutineMock()
    protocol = CoroutineMock(BaseSignalRProtocol)
    queue = CoroutineMock(asyncio.Queue)
    instance.validate_transport = CoroutineMock(return_value=True)
    instance.receive = CoroutineMock()
    # Initialize Instance
    await instance.connect(protocol, queue)
    # Expect that receive is called with specified Queue
    instance.send.assert_called_once()
    instance.receive.assert_called_once_with(queue)


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", [
    LongPollingTransport,
    WebSocketTransport
])
async def test_connect_invalid_transport(transport):
    instance = transport('http://foo.bar:5000')
    # Mock Dependencies
    instance.conn = CoroutineMock()
    instance.send = CoroutineMock()
    protocol = CoroutineMock(BaseSignalRProtocol)
    queue = CoroutineMock(asyncio.Queue)
    instance.validate_transport = CoroutineMock(return_value=False)
    instance.receive = CoroutineMock()
    # Expect connection error to be raised
    with pytest.raises(SignalRConnectionError):
        # Initialize Instance
        await instance.connect(protocol, queue)


@pytest.mark.asyncio
async def test_send_long_polling():
    instance = LongPollingTransport('http://foo.bar:5000')
    instance.connection_id = 'abc'
    instance.conn = CoroutineMock(aiohttp.ClientSession())
    instance.conn.post = CoroutineMock(aiohttp.ClientSession().post)
    instance.receive_task = CoroutineMock()
    packet = 100
    await instance.send(packet)
    instance.conn.post.assert_called_once_with('http://foo.bar:5000',
                                               data=packet,
                                               params={"id": "abc"})


@pytest.mark.asyncio
async def test_send_websockets():
    instance = WebSocketTransport('http://foo.bar:5000')
    instance.connection_id = 'abc'
    instance.conn = CoroutineMock(websockets.client.WebSocketClientProtocol)
    instance.conn.send = CoroutineMock()
    instance.conn.state = MagicMock(return_value=websockets.protocol.State.OPEN)
    instance.receive_task = CoroutineMock()
    packet = 100
    await instance.send(packet)
    instance.conn.send.assert_called_once_with(packet)


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", [
    LongPollingTransport,
    WebSocketTransport
])
@pytest.mark.parametrize("property_missing", [
    "conn",
    "receive_task"
])
async def test_send_not_connected(transport, property_missing):
    instance = transport('http://foo.bar:5000')
    instance.connection_id = 'abc'
    instance.conn = CoroutineMock(aiohttp.ClientSession())
    instance.conn.send = CoroutineMock(aiohttp.ClientSession().post)
    instance.receive_task = CoroutineMock()
    packet = 100
    # Set missing property
    setattr(instance, property_missing, None)
    # Expect connection error to be raised
    with pytest.raises(SignalRConnectionError):
        await instance.send(packet)


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", [
    LongPollingTransport,
    WebSocketTransport
])
async def test_send_connection_stopped(transport):
    instance = transport('http://foo.bar:5000')
    instance.connection_id = 'abc'
    instance.conn = CoroutineMock(aiohttp.ClientSession())
    instance.conn.send = CoroutineMock(aiohttp.ClientSession().post)
    instance.receive_task = CoroutineMock()
    packet = 100
    # Set stop event
    instance.stop_event.set()
    # Expect connection error to be raised
    with pytest.raises(SignalRConnectionError):
        await instance.send(packet)
