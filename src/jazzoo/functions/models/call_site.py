import typing as T

from jazzoo.utils.dataclass import dataclass


@dataclass
class Argument:
    # None for a positional argument, which is an error inside a .jaz file but is
    # still parsed so the error can name the offending call.
    name: T.Optional[str]
    value: T.Any


@dataclass
class CallSite:
    # Dotted path as written, e.g. "build" or "docker.build".
    target_path: str
    arguments: T.List[Argument] = []
    filename: T.Optional[str] = None
    line: T.Optional[int] = None

    @property
    def name(self) -> str:
        """The final segment - the function's own name, without any namespace."""
        return self.target_path.rsplit(".", 1)[-1]
