import typing as T

from jazzoo.errors import ArgumentError
from jazzoo.functions.models.curried_function import CurriedFunction
from jazzoo.functions.models.function import Function
from jazzoo.modules.rules.parse_source import _split_top_level, _strip_quotes


def parse_curry(
    function: Function,
    bracket_text: str,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> CurriedFunction:
    """Build a curried function from a `[...]` expression.

    `name=value` binds a parameter; a bare `name` marks it explicitly unbound.
    Empty brackets bind nothing, which is why `f` and `f[]` are the same value.
    """
    inner = bracket_text.strip()
    if inner.startswith("["):
        inner = inner[1:]
    if inner.endswith("]"):
        inner = inner[:-1]

    declared = {p.name for p in function.parameters}
    bound: T.Dict[str, str] = {}
    explicitly_unbound: T.List[str] = []

    for chunk in _split_top_level(inner, ","):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, separator, value = chunk.partition("=")
        name = name.strip()
        if name not in declared:
            raise ArgumentError(
                f"{function.name}() has no parameter named '{name}'",
                filename=filename,
                line=line,
            )
        if separator:
            bound[name] = _strip_quotes(value)
        else:
            explicitly_unbound.append(name)

    return CurriedFunction(
        function=function, bound=bound, explicitly_unbound=explicitly_unbound
    )


def get_free_parameters(curried: CurriedFunction) -> T.List[str]:
    """The parameters a caller may still supply.

    Naming a parameter bare makes it the only free one; otherwise every parameter
    the curry did not bind is free. Defaults play no part - which is why a pipe
    stage over `f(path, style="posix")` is ambiguous unless it says which is free.
    """
    if curried.explicitly_unbound:
        return list(curried.explicitly_unbound)
    return [
        parameter.name
        for parameter in curried.function.parameters
        if parameter.name not in curried.bound
    ]
