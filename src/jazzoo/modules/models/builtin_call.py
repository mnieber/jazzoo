import typing as T

from jazzoo.functions.models.call_site import Argument
from jazzoo.utils.dataclass import dataclass


@dataclass
class BuiltinCall:
    # The whole `⚙️.name(args)` text, which is evaluated like any other call.
    text: str
    name: str
    arguments: T.List[Argument] = []
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
