import typing as T

from jazzoo.errors import ArgumentError


def validate_arguments(
    path: str,
    name: str,
    parameters,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    for argument_name, _ in arguments:
        if argument_name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)",
                filename=filename,
                line=line,
            )

    supplied = {argument_name for argument_name, _ in arguments}
    declared = {p.name for p in parameters}
    for argument_name in supplied:
        if argument_name not in declared:
            raise ArgumentError(
                f"{name}() has no parameter named '{argument_name}'",
                filename=filename,
                line=line,
            )
    for parameter in parameters:
        if parameter.default is None and parameter.name not in supplied:
            raise ArgumentError(
                f"{name}() is missing a value for '{parameter.name}'",
                filename=filename,
                line=line,
            )
