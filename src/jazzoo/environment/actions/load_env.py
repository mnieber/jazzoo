import os
import typing as T

from jazzoo.environment.utils.parse_dotenv import parse_dotenv
from jazzoo.errors import ExecutionError


def load_env(
    path: str,
    is_required: bool = True,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> None:
    """Export the variables of a dotenv file into the environment.

    A variable that is already set keeps its value, so the caller's environment
    overrides the file.
    """
    if not os.path.isfile(path):
        if is_required:
            raise ExecutionError(
                f"env file not found: {path}", filename=filename, line=line
            )
        return

    with open(path, "r", encoding="utf-8") as handle:
        values = parse_dotenv(handle.read())

    for key, value in values.items():
        os.environ.setdefault(key, value)
