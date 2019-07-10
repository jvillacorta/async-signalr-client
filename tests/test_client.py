import pytest
import random
import typing
import asyncio
import functools
from client import SignalRConnectionState, protocols, transports
from .helper.launch_server import SignalRServerLauncher


def run_until_complete(function: typing.Callable) -> typing.Callable:
    @functools.wraps(function)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return asyncio.get_event_loop().run_until_complete(function(*args, **kwargs))

    return wrapper


class TestAsyncSignalRClient:
    server: SignalRServerLauncher

    @classmethod
    def setup_class(cls):
        cls.server = SignalRServerLauncher()
        cls.server.start()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("transport", [
        transports.WebSocketTransport,
        transports.LongPollingTransport
    ])
    async def test_json_transport_protocol_negotiation(self, signal_r_client, transport):
        assert self.server.started is True
        signal_r_client.protocol = protocols.JsonProtocol()
        signal_r_client.transport = transport(signal_r_client.url)
        await signal_r_client.start()
        assert signal_r_client.state == SignalRConnectionState.ONLINE

    @pytest.mark.asyncio
    async def test_json_invoke_completion(self, signal_r_client):
        assert self.server.started is True
        signal_r_client.protocol = protocols.JsonProtocol()
        await signal_r_client.start()
        completion_result = str(random.randrange(1000, 9999))
        completion_future = await signal_r_client.invoke("InvokeSample", completion_result, 50)
        await completion_future
        assert completion_future.result() == completion_result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("outgoing_event, incoming_event, sample, expected_type", [
        ("RequestInvokeString", "callback", str(random.randrange(1000, 9999)), str),
        ("RequestInvokeInteger", "callback", random.randrange(1000, 9999), int),
        ("RequestInvokeFloat", "callback", 0.001, float),
        ("RequestInvokeStringArray", "callback", ['a', 'b', 'c', 'd'], list)
    ])
    async def test_json_invoke_string(self, signal_r_client, outgoing_event, incoming_event, sample, expected_type):
        assert self.server.started is True
        signal_r_client.protocol = protocols.JsonProtocol()
        await signal_r_client.start()
        done = asyncio.Event()

        async def callback(return_sample):
            assert type(return_sample) == expected_type
            assert sample == return_sample
            done.set()

        signal_r_client.on(incoming_event, callback)

        await signal_r_client.invoke(outgoing_event, incoming_event, sample)
        await asyncio.wait_for(done.wait(), timeout=10)

    @classmethod
    def teardown_class(cls):
        cls.server.stop()
