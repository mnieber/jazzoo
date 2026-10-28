import typing as T

from jazzoo.utils.dataclass import dataclass

if T.TYPE_CHECKING:
    from jazzoo.functions.models.curried_function import CurriedFunction


@dataclass
class Variable:
    name: str
    # A variable holds a string, or a function value once currying lands (stage 5).
    value: T.Union[str, "CurriedFunction"]
