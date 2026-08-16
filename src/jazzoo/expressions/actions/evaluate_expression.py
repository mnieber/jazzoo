import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.expressions.models.literal import Literal
from jazzoo.expressions.models.path_join import PathJoin
from jazzoo.expressions.models.pipe import Pipe
from jazzoo.expressions.models.ternary import Comparison, Ternary
from jazzoo.expressions.rules.apply_builtin_pipe import (
    apply_builtin_pipe,
    is_builtin_pipe,
)
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.rules.parse_expression import (
    Call,
    Curry,
    ReferenceText,
    parse_expression,
)
from jazzoo.expressions.rules.parse_references import parse_references
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.expressions.utils.join_path import join_path
from jazzoo.modules.rules.parse_source import parse_call_arguments

# Splits `🐭.name(args)` into its name and its argument text.
_CALL_PARTS_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>.*)\)$",
    re.S,
)


def evaluate_call(text: str, frame) -> str:
    """Evaluate a `🐭.name(args)` call and return its value."""
    from jazzoo.functions.actions.call_function import _lookup_function, call_function

    match = _CALL_PARTS_RE.match(text)
    if match is None:
        raise ResolutionError(f"cannot parse call: {text}")

    path = match.group("path")
    arguments = parse_call_arguments(match.group("args"), None, None)
    for argument in arguments:
        if argument.name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)"
            )

    resolved = {
        argument.name: evaluate_expression(argument.value, frame)
        for argument in arguments
    }

    class _Site:
        filename = None
        line = None

    target = _lookup_function(path, frame, _Site())
    return call_function(target, resolved, frame, evaluate_expression)


def _evaluate_node(node: T.Any, frame) -> T.Any:
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    if isinstance(node, Literal):
        # A literal may still contain references to substitute.
        return substitute_references(
            node.text, lambda reference: str(resolve_reference(reference, frame))
        )

    if isinstance(node, Call):
        return evaluate_call(node.text, frame)

    if isinstance(node, ReferenceText):
        return _resolve_reference_text(node.text, frame)

    if isinstance(node, PathJoin):
        return join_path(
            str(_evaluate_node(node.left, frame)),
            str(_evaluate_node(node.right, frame)),
        )

    if isinstance(node, Ternary):
        if _is_condition_true(node.condition, frame):
            return _evaluate_node(node.value, frame)
        return _evaluate_node(node.otherwise, frame)

    if isinstance(node, Pipe):
        value = _evaluate_node(node.value, frame)
        for stage in node.stages:
            value = _apply_stage(stage, value, frame)
        return value

    if isinstance(node, Curry):
        raise ResolutionError("currying is not supported yet")

    raise ResolutionError(f"cannot evaluate expression node: {node!r}")


def _resolve_reference_text(text: str, frame) -> T.Any:
    """Resolve a reference in expression position.

    Variable names never contain dots, so the scanner already ends the name at the
    first one and anything after it is literal text - which is what makes
    `🐭.bare.com` the variable `bare` followed by ".com".
    """
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    matches = parse_references(text)
    if not matches:
        return text

    match = matches[0]
    value = resolve_reference(match.reference, frame)
    suffix = text[match.end :]
    if not suffix:
        # A lone reference keeps its value's type rather than being stringified.
        return value
    return f"{value}{suffix}"


def _is_condition_true(node: T.Any, frame) -> bool:
    if isinstance(node, Comparison):
        left = str(_evaluate_node(node.left, frame))
        right = str(_evaluate_node(node.right, frame))
        return left == right
    return is_truthy(str(_evaluate_node(node, frame)))


def _apply_stage(stage: T.Any, value: str, frame) -> str:
    """Apply one pipe stage to the piped value."""
    if isinstance(stage, ReferenceText):
        matches = parse_references(stage.text)
        if matches and matches[0].reference.sigil is Sigil.SYSTEM:
            name = matches[0].reference.name
            if is_builtin_pipe(name):
                return apply_builtin_pipe(name, str(value))
            raise ResolutionError(f"no such pipe operator: ⚙️.{name}")

    if isinstance(stage, PathJoin):
        # `a | ⚙️.abs / b` - the pipe applies to the join's left side only.
        left = _apply_stage(stage.left, value, frame)
        return join_path(str(left), str(_evaluate_node(stage.right, frame)))

    raise ResolutionError("only ⚙️ operators may be piped yet")


def evaluate_expression(source: str, frame) -> str:
    """Evaluate one jazzoo expression against the current namespace state."""
    source = source.strip()
    if not source:
        return ""
    return _evaluate_node(parse_expression(source), frame)
