import sys
import asyncio
from pathlib import Path


class SignalRServerLauncher:
    def __init__(self, path: Path):
        self.proc = None
        self.path = path
        self.started = False

    def pid(self):
        return self.proc.pid

    async def start(self, timeout: int = 10):
        loop = asyncio.get_event_loop()
        start_future = asyncio.Future()
        loop.create_task(self._process(start_future))
        await asyncio.wait_for(start_future, timeout)
        self.started = True

    async def _process(self, start_future: asyncio.Future):
        self.proc = await asyncio.create_subprocess_exec(
            *['dotnet', 'run'],
            stdout=asyncio.subprocess.PIPE,
            cwd=self.path
        )
        try:
            while True:
                line = await self.proc.stdout.readline()
                if self.proc.returncode:
                    break
                if not line:
                    break
                else:
                    line = line.decode().replace('\n', '')
                    print(line)
                    if 'Application started.' in line:
                        start_future.set_result(None)
        except asyncio.CancelledError:
            self.proc.terminate()

    async def stop(self):
        self.proc.terminate()
        await self.proc.wait()


if __name__ == '__main__':
    launcher = SignalRServerLauncher(Path('../../demo-server/'))
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.get_event_loop()
    loop.create_task(launcher.start())
    loop.run_forever()
