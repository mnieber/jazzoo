import typing as T

from jazzoo.modules.models.variable import Variable
from jazzoo.utils.dataclass import dataclass

if T.TYPE_CHECKING:
    from jazzoo.functions.models.function import Function


@dataclass
class Scope:
    variables: T.List[Variable] = []
    functions: T.List["Function"] = []
