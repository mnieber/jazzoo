import os
import typing as T

from ..errors import CommandAbortedError, CommandError
from ..settings import CONFIRM_PROMPT, TERMINAL
from ..utils.format_command import format_command


def confirm_command(
    command: T.Union[str, T.List[str]], cwd: T.Optional[str] = None
) -> bool:
    try:
        reader = open(TERMINAL, "r", encoding="utf-8")
        writer = open(TERMINAL, "w", encoding="utf-8")
    except OSError:
        raise CommandError("--confirm needs a terminal")

    with reader, writer:
        # Asks again until the answer is y, n, q or Enter
        while True:
            writer.write(format_command(command, cwd or os.getcwd()) + "\n")
            writer.write(CONFIRM_PROMPT)
            writer.flush()

            line = reader.readline()
            # An empty line has a newline; no newline means the end of input
            if not line:
                raise CommandAbortedError("aborted by the user")

            answer = line.strip().lower()
            if answer in ("", "y"):
                return True
            if answer == "n":
                return False
            if answer == "q":
                raise CommandAbortedError("aborted by the user")
