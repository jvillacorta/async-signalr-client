import pytest
import asyncio
from client import Connection


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def signalr_url():
    return 'ws://127.0.0.1:5000/chat'


@pytest.fixture(scope='class')
async def signal_r_client(signalr_url):
    conn = Connection(signalr_url)
    yield conn
    await conn.stop()
