import time
import shutil
import requests
from pathlib import Path
from subprocess import Popen, PIPE
from project import PROJECT_PATH


class SignalRServerLauncher:
    SERVER_DLL = 'SignalRSimpleChat.dll'
    SERVER_PROJECT_FOLDER = 'demo-server'
    SERVER_BUILD_FOLDER = 'bin'
    TEST_URL = 'http://localhost:5000'

    def __init__(self, path: Path = PROJECT_PATH, clean_build: bool = False):
        self.process = None
        self.control = None
        self.launch_time = None
        self.started = False

        self.path = path
        if clean_build is True:
            shutil.rmtree(self.path.joinpath(self.SERVER_BUILD_FOLDER))
        if self.check_dll() is False:
            print(f"{self.SERVER_DLL} not found, rebuilding project...")
            build_folder = str(self.path.joinpath(self.SERVER_BUILD_FOLDER).resolve())
            cmd = ["dotnet",
                   "publish",
                   f"-o {build_folder}"]
            out, err = Popen(' '.join(cmd),
                             cwd=str(self.path.joinpath(self.SERVER_PROJECT_FOLDER).resolve()),
                             shell=True,
                             stdout=PIPE,
                             stderr=PIPE).communicate()
            assert self.check_dll(), f'Build Process failed:\n{out.decode()}\n{err.decode()}'

    def check_dll(self):
        path = self.path.joinpath(self.SERVER_BUILD_FOLDER)
        if path.exists():
            for x in path.iterdir():
                if x.name == self.SERVER_DLL:
                    return True
        return False

    def pid(self):
        return self.process.pid

    def start(self, timeout: int = 30):
        self.launch_time = time.time()
        executable_path = str(self.path.joinpath(self.SERVER_BUILD_FOLDER).joinpath(self.SERVER_DLL).resolve())
        self.process = Popen(["dotnet", executable_path])
        while time.time() < self.launch_time + timeout:
            time.sleep(0.5)
            try:
                r = requests.get(self.TEST_URL)
                if r.status_code == 200:
                    self.started = True
                    return True
            except:
                continue
        return False

    def stop(self):
        self.process.terminate()
