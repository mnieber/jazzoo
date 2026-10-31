import typing as T

from jazzoo.errors import ArgumentError, ParseError
from jazzoo.module_validation.models.alternatives import Alternatives


def validate_against_alternatives(
    held: Alternatives,
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Require every candidate to accept the call.

    Which candidate runs is decided at run time, so demanding that all of them
    accept is what makes the call correct whichever one wins. Checking only that
    *some* candidate accepts would make a boolean-valued name looser than a plain
    one, which is the opposite of what load-time checking is for.
    """
    if held.not_functions:
        # Some branch yields a value that cannot be called at all, so the call is
        # wrong whenever that branch wins.
        names = ", ".join(sorted(set(held.not_functions)))
        raise ParseError(
            f"{path} cannot always be called: {names} is not a function",
            filename=filename,
            line=line,
        )

    for name, _ in arguments:
        if name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)",
                filename=filename,
                line=line,
            )

    supplied = {name for name, _ in arguments}
    for function in held.functions:
        declared = {p.name for p in function.parameters}
        for name in sorted(supplied - declared):
            raise ArgumentError(
                f"{function.name}() has no parameter named '{name}'",
                filename=filename,
                line=line,
            )
        for parameter in function.parameters:
            if parameter.default is None and parameter.name not in supplied:
                raise ArgumentError(
                    f"{function.name}() is missing a value for " f"'{parameter.name}'",
                    filename=filename,
                    line=line,
                )
