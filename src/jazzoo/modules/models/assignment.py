import typing as T

from jazzoo.enums import Sigil
from jazzoo.utils.dataclass import dataclass


@dataclass
class Assignment:
    sigil: Sigil
    name: str
    rhs: str
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
