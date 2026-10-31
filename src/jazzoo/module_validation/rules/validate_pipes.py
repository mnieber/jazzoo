import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def validate_pipes(
    source: str,
    module: Module,
    function_valued: T.Dict[str, Function],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Check that each pipe stage leaves exactly one parameter unbound.

    Which parameter is free must be decidable from the expression alone, so a stage
    binding all of them, or leaving two, is an ArgumentError at parse time.
    """
    from jazzoo.expressions.models.pipe import Pipe
    from jazzoo.expressions.rules.parse_expression import (
        Curry,
        ReferenceText,
        parse_expression,
    )
    from jazzoo.references.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.functions.rules.parse_curry import get_free_parameters, parse_curry

    if "|" not in source:
        return
    try:
        node = parse_expression(source)
    except Exception:
        return
    if not isinstance(node, Pipe):
        return

    for stage in node.stages:
        if isinstance(stage, Curry):
            target_text, brackets = stage.target.text, stage.text
        elif isinstance(stage, ReferenceText):
            target_text, brackets = stage.text, "[]"
        else:
            continue

        split = split_reference_path(target_text)
        if split is None:
            continue
        sigil, path = split
        if sigil is Sigil.SYSTEM:
            # A built-in operator, not a user function.
            continue

        held = function_valued.get(path)
        target = (
            held.function if held is not None else get_function_by_path(module, path)
        )
        if target is None:
            continue

        curried = parse_curry(target, brackets, filename=filename, line=line)
        if held is not None and brackets == "[]":
            # Piping a variable that already holds a curry keeps its bindings.
            curried = held
        free = get_free_parameters(curried)
        if len(free) != 1:
            raise ArgumentError(
                f"a pipe stage must leave exactly one parameter unbound; "
                f"{target.name}() leaves {len(free)}",
                filename=filename,
                line=line,
            )
