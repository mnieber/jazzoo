import typing as T

from jazzoo.utils.dataclass import dataclass


@dataclass
class Comparison:
    left: T.Any
    right: T.Any


@dataclass
class Ternary:
    # `value if condition else otherwise`. Chaining is right-associative, so
    # `otherwise` may itself be a Ternary.
    value: T.Any
    condition: T.Any
    otherwise: T.Any
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
