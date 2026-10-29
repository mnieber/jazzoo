import os
import shutil
import signal
import subprocess
import sys
import typing as T

from ..errors import CommandFailedError
from ..models.command_result import CommandResult
from ..rules.find_executable import find_executable
from ..utils.format_command import format_command
from ..utils.ignoring_sigint import ignoring_sigint


def run(
    command: T.Union[str, T.List[str]],
    cwd: T.Optional[str] = None,
    env: T.Optional[T.Dict[str, str]] = None,
    capture: bool = False,
    check: bool = True,
    echo: bool = False,
) -> CommandResult:
    # Check the arguments before anything runs
    if isinstance(command, str):
        if not command.strip():
            raise ValueError("the command is empty")
    elif not command:
        raise ValueError("the command is empty")
    if cwd is not None and not os.path.isdir(cwd):
        raise ValueError(f"directory not found: {cwd}")

    environ = {**os.environ, **(env or {})}

    # A string runs in bash; a list runs directly
    if isinstance(command, str):
        args = ["bash", "-c", command]
        executable = shutil.which("bash") or "/bin/bash"
    else:
        args = list(command)
        executable = find_executable(args[0], environ)

    if echo:
        print(format_command(command, cwd))

    # The command writes to the same file descriptors as the script, so what the
    # script printed before must come first
    sys.stdout.flush()
    sys.stderr.flush()

    output = subprocess.PIPE if capture else None
    process = subprocess.Popen(
        args,
        executable=executable,
        cwd=cwd,
        env=environ,
        stdout=output,
        stderr=output,
        text=True,
    )

    # SIGINT is ignored only after the command has started, because an ignored
    # signal would be inherited by the command. A ctrl-c then reaches the command
    # only.
    with ignoring_sigint():
        stdout, stderr = process.communicate()

    if process.returncode == -signal.SIGINT:
        raise KeyboardInterrupt

    result = CommandResult(
        command=command,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
    if check and result.returncode != 0:
        raise CommandFailedError(_failure_message(result, cwd), result)
    return result


def _failure_message(result: CommandResult, cwd: T.Optional[str]) -> str:
    message = f"command failed with exit code {result.returncode}: " + format_command(
        result.command, cwd
    )
    if result.stderr and result.stderr.strip():
        message += "\n" + result.stderr.strip()
    return message
