import typing as T

from dataclassy import dataclass


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
