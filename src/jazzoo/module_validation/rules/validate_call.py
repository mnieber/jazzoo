import typing as T

from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.functions.models.function import Function
from jazzoo.module_validation.models.alternatives import Alternatives
from jazzoo.module_validation.rules.validate_against_alternatives import (
    validate_against_alternatives,
)
from jazzoo.module_validation.rules.validate_arguments import validate_arguments
from jazzoo.modules.models.module import Module


def _find_function(
    path: str,
    module: Module,
    enclosing: Function,
    function_valued: T.Dict[str, Function],
) -> T.Optional[Function]:
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    for local in enclosing.functions:
        if local.name == path:
            return local
    if path in function_valued:
        return function_valued[path].function
    return get_function_by_path(module, path)


def validate_call(
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    module: Module,
    enclosing: Function,
    filename: T.Optional[str],
    line: T.Optional[int],
    function_valued: T.Dict[str, Function],
) -> None:
    held_alternatives = function_valued.get(path)
    if isinstance(held_alternatives, Alternatives):
        validate_against_alternatives(
            held_alternatives, path, arguments, filename, line
        )
        return

    target = _find_function(path, module, enclosing, function_valued)
    if target is None:
        raise ResolutionError(f"no such function: {path}", filename=filename, line=line)

    held = function_valued.get(path)
    if held is not None:
        for name, _ in arguments:
            if name in held.bound:
                raise ArgumentError(
                    f"{target.name}() already has a value for '{name}' from currying",
                    filename=filename,
                    line=line,
                )
    validate_arguments(path, target.name, target.parameters, arguments, filename, line)
