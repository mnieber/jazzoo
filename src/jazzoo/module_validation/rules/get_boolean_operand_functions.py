import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def _operand_label(node: T.Any) -> str:
    """How a non-reference operand is named in an error message."""
    text = getattr(node, "text", None)
    if text is not None:
        return f'"{text}"'
    return str(getattr(node, "value", node))


def get_boolean_operand_functions(
    node: T.Any, module: Module, known: T.Dict[str, T.Any]
) -> T.Optional[T.Tuple[T.List[Function], T.List[str]]]:
    """Every function a boolean expression could yield, or None if it is not one.

    `and` and `or` yield one of their operands, and which one is a run-time
    question. Collecting them all lets the call be checked against every function it
    could reach, so a call site is only accepted when it is correct whichever
    operand wins.

    Operands that do not name a function are reported alongside the ones that do,
    because a name is only safely callable when *every* branch yields a function.
    The check itself belongs to the call site: assigning such a value is fine, and
    only calling through it is an error.
    """
    from jazzoo.expressions.models.boolean import And, Or
    from jazzoo.expressions.rules.parse_expression import Curry, ReferenceText
    from jazzoo.references.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    if not isinstance(node, (And, Or)):
        return None

    found: T.List[Function] = []
    not_functions: T.List[str] = []
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, (And, Or)):
            pending.extend([current.left, current.right])
            continue
        if isinstance(current, Curry):
            current = current.target
        if not isinstance(current, ReferenceText):
            # A literal operand - a string or number - can never be called.
            not_functions.append(_operand_label(current))
            continue
        split = split_reference_path(current.text)
        if split is None:
            not_functions.append(current.text)
            continue
        path = split[1]
        held = known.get(path)
        function = (
            held.function if held is not None else get_function_by_path(module, path)
        )
        if function is not None:
            found.append(function)
        else:
            not_functions.append(current.text)
    return found, not_functions
