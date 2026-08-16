import typing as T

from dataclassy import dataclass


@dataclass
class PathJoin:
    # `a / b`, left-associative, so `left` may itself be a PathJoin.
    left: T.Any
    right: T.Any
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
