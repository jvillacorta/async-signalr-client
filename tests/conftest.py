import pytest
import asyncio
from pathlib import Path
from .helper.launch_server import SignalRServerLauncher


@pytest.yield_fixture(scope='class')
def event_loop():
    loop = asyncio.ProactorEventLoop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def signalr_url():
    return 'ws://127.0.0.1:5000/chat'


@pytest.yield_fixture(scope='class')
async def signal_r_base():
    server = SignalRServerLauncher(Path("./demo-server/"))
    await server.start()
    yield server
    await server.stop()
