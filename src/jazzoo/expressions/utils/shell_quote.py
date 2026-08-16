import shlex


def shell_quote(value: str) -> str:
    """Render a value as a single, safely quoted POSIX shell word."""
    return shlex.quote(value)
