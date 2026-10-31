import typing as T

from jazzoo.errors import ResolutionError
from jazzoo.expressions.actions.call_curried import call_curried
from jazzoo.expressions.actions.resolve_arguments import resolve_arguments
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.functions.models.curried_function import CurriedFunction


def call_value(value: T.Any, args_text: str, frame) -> str:
    """Call whatever a computed expression produced.

    The callee is not a name, so it cannot be looked up: it has to already be a
    function value. Anything else is a ResolutionError, which is the same answer
    calling a string by name gives.
    """
    if not isinstance(value, CurriedFunction):
        raise ResolutionError(
            f"cannot call a value that is not a function: {render_value(value)!r}"
        )
    return call_curried(
        value, resolve_arguments(args_text, "a computed function", frame), frame
    )
