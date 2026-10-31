import typing as T

from jazzoo.errors import ArgumentError
from jazzoo.modules.rules.parse_call_arguments import parse_call_arguments


def resolve_arguments(args_text: str, path: str, frame) -> T.Dict[str, str]:
    """Parse a call's argument text and evaluate each value.

    Shared by a named call and by a call on a computed value, so both enforce the
    same rule that arguments are named.
    """
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    arguments = parse_call_arguments(args_text, None, None)
    for argument in arguments:
        if argument.name is None:
            raise ArgumentError(f"arguments must be named in a .jaz file: {path}(...)")
    # An argument's value is used by the callee, so calls inside it are quiet.
    with frame.quietly():
        return {
            argument.name: evaluate_expression(argument.value, frame)
            for argument in arguments
        }
