import pytest
import random
import typing
import asyncio
import functools
from pathlib import Path
from client import SignalRConnectionState, protocols
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
    async def test_json_protocol_negotiation(self, signal_r_client):
        assert self.server.started is True
        signal_r_client.protocol = protocols.JsonProtocol()
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

    @classmethod
    def teardown_class(cls):
        cls.server.stop()
