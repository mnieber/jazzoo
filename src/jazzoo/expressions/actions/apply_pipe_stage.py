import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.expressions.actions.bind_curry import bind_curry
from jazzoo.expressions.actions.call_curried import call_curried
from jazzoo.expressions.models.boolean import And, Not, Or
from jazzoo.expressions.models.path_join import PathJoin
from jazzoo.expressions.models.ternary import Ternary
from jazzoo.expressions.rules.apply_builtin_pipe import (
    apply_builtin_pipe,
    is_builtin_pipe,
)
from jazzoo.expressions.rules.parse_expression import CallValue, Curry, ReferenceText
from jazzoo.expressions.rules.parse_references import parse_references
from jazzoo.expressions.rules.resolve_function_value import resolve_function_value
from jazzoo.expressions.utils.join_path import join_path
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.functions.models.curried_function import CurriedFunction


def apply_pipe_stage(stage: T.Any, value: str, frame) -> str:
    """Apply one pipe stage to the piped value.

    A stage is either a built-in ⚙️ operator or a function value with exactly one
    unbound parameter, which the piped value fills.
    """
    from jazzoo.expressions.actions.evaluate_expression import evaluate_node

    if isinstance(stage, ReferenceText):
        matches = parse_references(stage.text)
        if matches and matches[0].reference.sigil is Sigil.SYSTEM:
            name = matches[0].reference.name
            if is_builtin_pipe(name):
                return apply_builtin_pipe(name, value)
            raise ResolutionError(f"no such pipe operator: ⚙️.{name}")

        curried = resolve_function_value(stage.text, frame)
        if curried is not None:
            return _pipe_into(curried, value, frame)

    if isinstance(stage, Curry):
        target = resolve_function_value(stage.target.text, frame)
        if target is None:
            raise ResolutionError(f"no such function: {stage.target.text}")
        return _pipe_into(bind_curry(target.function, stage.text, frame), value, frame)

    if isinstance(stage, PathJoin):
        # `a | ⚙️.abs / b` - the pipe applies to the join's left side only.
        left = apply_pipe_stage(stage.left, value, frame)
        return join_path(
            render_value(left), render_value(evaluate_node(stage.right, frame))
        )

    if isinstance(stage, (And, Or, Not, CallValue, Ternary)):
        # A computed stage: evaluate it, then pipe into whatever it produced. This
        # is what lets `3 | (🐭.f1 or 🐭.f2)` choose a function and apply it.
        produced = evaluate_node(stage, frame)
        if isinstance(produced, CurriedFunction):
            return _pipe_into(produced, value, frame)
        raise ResolutionError(
            f"cannot pipe into a value that is not a function: "
            f"{render_value(produced)!r}"
        )

    raise ResolutionError(f"cannot pipe into: {stage!r}")


def _pipe_into(curried: CurriedFunction, value: str, frame) -> str:
    """Feed the piped value to the stage's single free parameter."""
    from jazzoo.functions.rules.parse_curry import get_free_parameters

    free = get_free_parameters(curried)
    if len(free) != 1:
        raise ArgumentError(
            f"a pipe stage must leave exactly one parameter unbound; "
            f"{curried.function.name}() leaves {len(free)}"
        )
    arguments = dict(curried.bound)
    arguments[free[0]] = value
    return call_curried(
        CurriedFunction(function=curried.function, bound={}, explicitly_unbound=[]),
        arguments,
        frame,
    )
