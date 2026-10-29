import os
import pty
import subprocess
import sys
import typing as T

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

__all__ = ["Context", "TestEnv"]

# Runs the jaz entrypoint with the arguments of the subprocess
RUN_JAZ = (
    "import sys; "
    "from jazzoo.runtime.entrypoints.jazzoo import main; "
    "sys.exit(main(sys.argv[1:]))"
)


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.printed: T.Optional[str] = None
        self.printed_err: T.Optional[str] = None
        self.pty_output: T.Optional[str] = None
        self.exit_code: T.Optional[int] = None

    def read_printed(self):
        """Stores what was printed on stdout and stderr since the last call."""
        self.printed, self.printed_err = self.context.capsys.readouterr()

    def run_jaz_in_pty(self, *args: str):
        """Runs jaz in a subprocess whose stdin, stdout and stderr are a
        pseudo-terminal, as when a developer runs it in a terminal."""
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.path(""))
            os.execv(sys.executable, [sys.executable, "-c", RUN_JAZ, *args])

        output = b""
        while True:
            try:
                chunk = os.read(fd, 1024)
            except OSError:
                # Raised on Linux when the child has closed the terminal
                break
            if not chunk:
                break
            output += chunk
        os.close(fd)

        _, status = os.waitpid(pid, 0)
        self.exit_code = os.waitstatus_to_exitcode(status)
        self.pty_output = output.decode("utf-8").replace("\r\n", "\n")

    def run_jaz(self, *args: str, input: str = ""):
        """Runs jaz in a subprocess whose stdin is fed with `input`."""
        completed = subprocess.run(
            [sys.executable, "-c", RUN_JAZ, *args],
            cwd=self.path(""),
            input=input,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.exit_code = completed.returncode
        self.output = completed.stdout
        self.printed_err = completed.stderr

    # Queries

    def pty_lines(self) -> T.List[str]:
        return (self.pty_output or "").splitlines()
