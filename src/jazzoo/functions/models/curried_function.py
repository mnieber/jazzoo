import typing as T

from dataclassy import dataclass

if T.TYPE_CHECKING:
    from jazzoo.functions.models.function import Function


@dataclass
class CurriedFunction:
    function: "Function"
    # Parameters bound by the curry expression; the caller may not re-supply these.
    bound: T.Dict[str, str] = {}
    # Parameters named bare in the brackets, i.e. explicitly left open. Empty
    # brackets and a bare function symbol both leave this empty, which is why
    # `f` and `f[]` are the same value.
    explicitly_unbound: T.List[str] = []
