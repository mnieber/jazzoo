import shlex
import typing as T


def format_command(
    command: T.Union[str, T.List[str]], cwd: T.Optional[str] = None
) -> str:
    text = command if isinstance(command, str) else shlex.join(command)
    return f"({cwd}) {text}" if cwd else text
