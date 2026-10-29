import codecs
import os
import pty
import select
import signal
import termios
import textwrap
import time
import typing as T
from pathlib import Path

import pytest

from jazzoo import evaluate, parse_module
from jazzoo.utils.dataclass import dataclass

# The prompt of a confirmation, and the keys that a test can send instead of an answer
CONFIRM_PROMPT = "confirm? [Y/n/q] "
CTRL_C = "\x03"
CTRL_D = "\x04"

PTY_TIMEOUT = 30


@dataclass
class Context:
    tmp_path: Path
    monkeypatch: pytest.MonkeyPatch
    capsys: pytest.CaptureFixture


class TestEnv:
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.root_module: T.Any = None
        self.output: T.Optional[str] = None
        self.error: T.Optional[Exception] = None
        self.exit_code: T.Optional[int] = None
        self.pty_output: T.Optional[str] = None
        self.prompts: T.List[str] = []

        # ⚙️.load_config changes os.environ directly. Registering the variable with
        # monkeypatch makes sure that it starts unset and is restored afterwards.
        context.monkeypatch.delenv("JAZZOO_CONFIG_FILES", raising=False)

        # A developer's shell must not switch on the confirmation of commands
        context.monkeypatch.delenv("JAZZOO_CONFIRM", raising=False)

        self.__post_init__()

    def __post_init__(self):
        pass

    def step(self, *_):
        return True

    def write_file(self, name: str, text: str):
        """Writes a file below tmp_path. The text is dedented, so that a test can
        indent it like the surrounding code."""
        path = Path(self.path(name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")

    def change_dir(self, name: str = ""):
        self.context.monkeypatch.chdir(self.path(name))

    def set_env(self, name: str, value: str):
        self.context.monkeypatch.setenv(name, value)

    def unset_env(self, name: str):
        self.context.monkeypatch.delenv(name, raising=False)

    def parse_module(self, name: str):
        self.root_module = parse_module(self.path(name))

    def parse_module_and_catch_error(self, name: str):
        self.error = None
        try:
            self.parse_module(name)
        except Exception as error:
            self.error = error

    def evaluate(self, expression: str, store_as: str = "output"):
        setattr(self, store_as, evaluate(self.root_module, expression))

    def evaluate_and_catch_error(self, expression: str):
        self.error = None
        try:
            self.evaluate(expression)
        except Exception as error:
            self.error = error

    def _run_in_pty(
        self,
        argv: T.List[str],
        answers: T.Sequence[str] = (),
        stdout_file: T.Optional[str] = None,
    ):
        """Runs argv in a subprocess whose controlling terminal is a pseudo-terminal,
        and answers its confirmation prompts.

        Each time the output ends with a prompt, the next answer is typed (CTRL_C and
        CTRL_D are sent as keys, other answers as a line). A prompt for which no
        answer is left, and an answer that is left at the end, fail the test.

        Stores the exit code in exit_code, the command lines of the prompts in
        prompts, and the output without the prompts in pty_output. With stdout_file,
        the stdout of the subprocess is redirected to that file.
        """
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.chdir(self.path(""))
                if stdout_file:
                    out = os.open(
                        self.path(stdout_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                    )
                    os.dup2(out, 1)
                os.execvp(argv[0], argv)
            finally:
                os._exit(127)

        # The typed answers are not echoed, so that they don't end up in the output
        attributes = termios.tcgetattr(fd)
        attributes[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, attributes)

        answers = list(answers)
        decoder = codecs.getincrementaldecoder("utf-8")()
        output = ""
        answered_until = 0
        prompt_ranges: T.List[T.Tuple[int, int]] = []
        self.prompts = []
        failure = None
        deadline = time.monotonic() + PTY_TIMEOUT

        while True:
            ready, _, _ = select.select([fd], [], [], deadline - time.monotonic())
            if not ready:
                failure = "timed out"
                break
            try:
                chunk = os.read(fd, 1024)
            except OSError:
                # Raised on Linux when the child has closed the terminal
                break
            if not chunk:
                break
            output += decoder.decode(chunk).replace("\r\n", "\n")

            if output.endswith(CONFIRM_PROMPT) and len(output) > answered_until:
                # The prompt is "<command line>\n" + CONFIRM_PROMPT. The typed
                # answers are not echoed, so the command line may also start right
                # after the previous prompt.
                head = output[: -len(CONFIRM_PROMPT)].rstrip("\n")
                start = max(head.rfind("\n") + 1, answered_until)
                command_line = head[start:]
                prompt_ranges.append((start, len(output)))
                answered_until = len(output)
                self.prompts.append(command_line)
                if not answers:
                    failure = f"unexpected prompt: {command_line}"
                    break
                answer = answers.pop(0)
                os.write(
                    fd,
                    (answer if answer in (CTRL_C, CTRL_D) else answer + "\n").encode(),
                )

        if failure:
            os.kill(pid, signal.SIGKILL)
        os.close(fd)
        _, status = os.waitpid(pid, 0)
        self.exit_code = os.waitstatus_to_exitcode(status)

        self.pty_output = output
        for start, end in reversed(prompt_ranges):
            self.pty_output = self.pty_output[:start] + self.pty_output[end:]

        if failure is None and answers:
            failure = f"answers left: {answers}"
        if failure:
            raise AssertionError(f"{failure}\n--- output:\n{output}")

    # Queries

    def path(self, name: str) -> str:
        return str(self.context.tmp_path / name)

    def env_var(self, name: str) -> T.Optional[str]:
        return os.environ.get(name)

    def pty_lines(self) -> T.List[str]:
        return (self.pty_output or "").splitlines()

    def file_exists(self, name: str) -> bool:
        return os.path.exists(self.path(name))
