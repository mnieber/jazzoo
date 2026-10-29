import os
import shlex
import stat
import subprocess
import sys
import typing as T

from jazzoo_test_env import CTRL_C, CTRL_D, Context, TestEnv as JazzooTestEnv

__all__ = ["CTRL_C", "CTRL_D", "Context", "TestEnv"]

# Runs the jaz entrypoint with the arguments of the subprocess
RUN_JAZ = (
    "import sys; "
    "from jazzoo.runtime.entrypoints.jazzoo import main; "
    "sys.exit(main(sys.argv[1:]))"
)

# The console scripts that the blocks of a run call. They run the code of the test
# environment, so that the tests don't depend on an installed jazzoo.
CONSOLE_SCRIPTS = {
    "jaz": f'exec {shlex.quote(sys.executable)} -c {shlex.quote(RUN_JAZ)} "$@"',
    "jaz-run": f'exec {shlex.quote(sys.executable)} -m jazzoo.commands "$@"',
}


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.printed_err: T.Optional[str] = None
        self._install_console_scripts()

    def run_jaz_in_pty(
        self,
        *args: str,
        answers: T.Sequence[str] = (),
        stdout_file: T.Optional[str] = None,
    ):
        """Runs jaz in a terminal, and answers its confirmation prompts (see
        _run_in_pty)."""
        self._run_in_pty(
            [sys.executable, "-c", RUN_JAZ, *args],
            answers=answers,
            stdout_file=stdout_file,
        )

    def run_jaz_without_terminal(self, *args: str):
        """Runs jaz in a new session, which has no controlling terminal."""
        completed = subprocess.run(
            [sys.executable, "-c", RUN_JAZ, *args],
            cwd=self.path(""),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            start_new_session=True,
            timeout=30,
        )
        self.exit_code = completed.returncode
        self.output = completed.stdout
        self.printed_err = completed.stderr

    def _install_console_scripts(self):
        for name, command in CONSOLE_SCRIPTS.items():
            path = self.path(f"bin/{name}")
            self.write_file(f"bin/{name}", f"#!/bin/sh\n{command}\n")
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.context.monkeypatch.setenv(
            "PATH", self.path("bin") + os.pathsep + os.environ.get("PATH", "")
        )

    # Queries

    def read_file(self, name: str) -> str:
        with open(self.path(name), encoding="utf-8") as f:
            return f.read()
