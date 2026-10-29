import typing as T

from ..utils.dataclass import dataclass


@dataclass
class CommandResult:
    # The command, as it was given to run
    command: T.Union[str, T.List[str]]
    returncode: int
    # None unless the output was captured
    stdout: T.Optional[str] = None
    stderr: T.Optional[str] = None
