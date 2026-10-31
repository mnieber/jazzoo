import typing as T

from jazzoo.errors import ArgumentError
from jazzoo.functions.models.function import Function


def bind_arguments(
    function: Function,
    arguments: T.Dict[str, str],
    evaluate_default: T.Callable[[str], T.Any],
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> T.Dict[str, T.Any]:
    """Validate arguments against parameters and produce the 🐆 variables.

    A default is an expression, evaluated by `evaluate_default` only when the
    caller does not supply that argument.
    """
    names = {p.name for p in function.parameters}
    for name in arguments:
        if name not in names:
            raise ArgumentError(
                f"{function.name}() has no parameter named '{name}'",
                filename=filename or function.filename,
                line=line if line is not None else function.line,
            )

    bound: T.Dict[str, T.Any] = {}
    for parameter in function.parameters:
        if parameter.name in arguments:
            bound[parameter.name] = arguments[parameter.name]
        elif parameter.default is not None:
            bound[parameter.name] = evaluate_default(parameter.default)
        else:
            raise ArgumentError(
                f"{function.name}() is missing a value for '{parameter.name}'",
                filename=filename or function.filename,
                line=line if line is not None else function.line,
            )
    return bound
