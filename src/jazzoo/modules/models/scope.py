import typing as T

from dataclassy import dataclass

from jazzoo.modules.models.variable import Variable

if T.TYPE_CHECKING:
    from jazzoo.functions.models.function import Function


@dataclass
class Scope:
    variables: T.List[Variable] = []
    functions: T.List["Function"] = []
