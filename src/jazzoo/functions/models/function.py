import typing as T

from dataclassy import dataclass

from jazzoo.functions.models.parameter import Parameter
from jazzoo.modules.models.scope import Scope

if T.TYPE_CHECKING:
    from jazzoo.blocks.models.block import Block
    from jazzoo.functions.models.call_site import CallSite


@dataclass
class Function(Scope):
    name: str = ""
    parameters: T.List[Parameter] = []
    # False for [private] functions, which are not callable from the CLI.
    is_target: bool = True
    # Calls declared after the colon, run before the body.
    dependencies: T.List["CallSite"] = []
    body: T.List["Block"] = []
    # The module this function was defined in, so 🐭 and ⚙️.module resolve against
    # the defining file even when the caller lives elsewhere.
    module: T.Any = None
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
