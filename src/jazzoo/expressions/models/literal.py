import typing as T

from dataclassy import dataclass


@dataclass
class Literal:
    # A quoted or bare string. May still contain references to substitute.
    text: str
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
