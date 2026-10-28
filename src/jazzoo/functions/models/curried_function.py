import typing as T

from jazzoo.utils.dataclass import dataclass

if T.TYPE_CHECKING:
    from jazzoo.functions.models.function import Function


@dataclass
class CurriedFunction:
    function: "Function"
    # Parameters bound by the curry expression; the caller may not re-supply these.
    # Holds expression sources until the curry is evaluated, and values after.
    bound: T.Dict[str, T.Any] = {}
    # Parameters named bare in the brackets, i.e. explicitly left open. Empty
    # brackets and a bare function symbol both leave this empty, which is why
    # `f` and `f[]` are the same value.
    explicitly_unbound: T.List[str] = []
