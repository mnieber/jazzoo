import os
import stat
import subprocess
import sys
import typing as T
from pathlib import Path

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.commands import run

__all__ = ["Context", "TestEnv"]


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.result: T.Any = None
        self.printed: T.Optional[str] = None
        self.printed_err: T.Optional[str] = None
        self.completed: T.Optional[subprocess.CompletedProcess] = None

    def run(self, command: T.Any, store_as: str = "result", **kwargs: T.Any):
        setattr(self, store_as, run(command, **kwargs))

    def run_and_catch_error(
        self, command: T.Any, store_as: str = "error", **kwargs: T.Any
    ):
        setattr(self, store_as, None)
        try:
            run(command, **kwargs)
        except Exception as error:
            setattr(self, store_as, error)

    def read_printed(self):
        """Stores what was printed on stdout and stderr since the last call."""
        self.printed, self.printed_err = self.context.capsys.readouterr()

    def write_executable(self, name: str, text: str):
        self.write_file(name, text)
        path = self.path(name)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def run_python_script(self, name: str, input: T.Optional[str] = None):
        """Runs a script below tmp_path in a subprocess, in a new session, so that a
        signal that the script sends to its process group cannot reach pytest."""
        self.completed = subprocess.run(
            [sys.executable, self.path(name)],
            cwd=self.path(""),
            input=input if input is not None else "",
            capture_output=True,
            text=True,
            start_new_session=True,
            timeout=30,
        )

    # Queries

    def read_file(self, name: str) -> str:
        return Path(self.path(name)).read_text(encoding="utf-8")

    def cwd(self) -> str:
        return os.getcwd()
