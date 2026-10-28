import typing as T

from jazzoo.utils.dataclass import dataclass


@dataclass
class Pipe:
    # `value | stage | stage`. Each stage is a builtin operator or a function
    # value with exactly one unbound parameter.
    value: T.Any
    stages: T.List[T.Any] = []
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
