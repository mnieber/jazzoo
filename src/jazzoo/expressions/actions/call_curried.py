import typing as T

from jazzoo.errors import ArgumentError
from jazzoo.functions.models.curried_function import CurriedFunction


def call_curried(curried: CurriedFunction, arguments: T.Dict[str, str], frame) -> str:
    """Call a curried function, merging the bound arguments with the caller's."""
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.functions.actions.call_function import call_function

    for name in arguments:
        if name in curried.bound:
            raise ArgumentError(
                f"{curried.function.name}() already has a value for '{name}' "
                "from currying"
            )
    merged = dict(curried.bound)
    merged.update(arguments)
    return call_function(curried.function, merged, frame, evaluate_expression)
