import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.expressions.models.literal import Literal
from jazzoo.expressions.models.path_join import PathJoin
from jazzoo.expressions.models.pipe import Pipe
from jazzoo.expressions.models.boolean import And, Not, Or
from jazzoo.expressions.models.ternary import Comparison, Ternary
from jazzoo.expressions.rules.apply_builtin_pipe import (
    apply_builtin_pipe,
    is_builtin_pipe,
)
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.rules.parse_expression import (
    CallValue,
    Call,
    Curry,
    JsonLiteral,
    ReferenceText,
    parse_expression,
)
from jazzoo.expressions.rules.parse_references import parse_references
from jazzoo.modules.models.absent import ABSENT
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.expressions.utils.join_path import join_path
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.functions.models.curried_function import CurriedFunction
from jazzoo.modules.rules.parse_source import _SIGIL_TEXTS, parse_call_arguments

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
    resolved = _resolve_arguments(match.group("args"), path, frame)

    class _Site:
        filename = None
        line = None

    sigil_text = match.group("sigil")
    if _SIGIL_TEXTS[sigil_text] is Sigil.SYSTEM:
        return _call_builtin(path, resolved)

    stored = _resolve_function_value(f"{sigil_text}.{path}", frame)
    if stored is not None and (stored.bound or stored.explicitly_unbound):
        return call_curried(stored, resolved, frame)

    target = _lookup_function(path, frame, _Site())
    return call_function(target, resolved, frame, evaluate_expression)


def _call_builtin(name: str, arguments: T.Dict[str, T.Any]) -> str:
    from jazzoo.functions.actions.call_builtin_function import (
        call_builtin_function,
        is_builtin_function,
    )

    if not is_builtin_function(name):
        raise ResolutionError(f"no such function: ⚙️.{name}")
    return call_builtin_function(name, arguments)


def _resolve_arguments(args_text: str, path: str, frame) -> T.Dict[str, str]:
    """Parse a call's argument text and evaluate each value.

    Shared by a named call and by a call on a computed value, so both enforce the
    same rule that arguments are named.
    """
    arguments = parse_call_arguments(args_text, None, None)
    for argument in arguments:
        if argument.name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)"
            )
    # An argument's value is used by the callee, so calls inside it are quiet.
    with frame.quietly():
        return {
            argument.name: evaluate_expression(argument.value, frame)
            for argument in arguments
        }


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
        value, _resolve_arguments(args_text, "a computed function", frame), frame
    )


def call_curried(
    curried: "CurriedFunction", arguments: T.Dict[str, str], frame
) -> str:
    """Call a curried function, merging the bound arguments with the caller's."""
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


def _evaluate_node(node: T.Any, frame) -> T.Any:
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    if isinstance(node, Literal):
        # A literal may still contain references and calls to substitute.
        return substitute_references(
            node.text,
            lambda reference: resolve_reference(reference, frame),
            evaluate_call=lambda call_text: evaluate_call(call_text, frame),
            evaluate_braced=lambda source: evaluate_expression(source, frame),
        )

    if isinstance(node, JsonLiteral):
        return node.value

    if isinstance(node, Call):
        return evaluate_call(node.text, frame)

    if isinstance(node, ReferenceText):
        return _resolve_reference_text(node.text, frame)

    if isinstance(node, PathJoin):
        return join_path(
            render_value(_evaluate_node(node.left, frame)),
            render_value(_evaluate_node(node.right, frame)),
        )

    if isinstance(node, CallValue):
        return call_value(
            _evaluate_node(node.target, frame), node.args, frame
        )

    if isinstance(node, Comparison):
        # A comparison can now sit inside `and`/`or`, so it has to yield a value of
        # its own rather than only being asked whether it holds.
        return render_value(_evaluate_node(node.left, frame)) == render_value(
            _evaluate_node(node.right, frame)
        )

    if isinstance(node, Or):
        # Yields an operand, not a boolean, and leaves the right one unevaluated
        # when the left already decides the answer.
        left = _evaluate_node(node.left, frame)
        return left if is_truthy(left) else _evaluate_node(node.right, frame)

    if isinstance(node, And):
        left = _evaluate_node(node.left, frame)
        return _evaluate_node(node.right, frame) if is_truthy(left) else left

    if isinstance(node, Not):
        return not is_truthy(_evaluate_node(node.operand, frame))

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
        target = _resolve_function_value(node.target.text, frame)
        if target is None:
            raise ResolutionError(f"no such function: {node.target.text}")
        return bind_curry(target.function, node.text, frame)

    raise ResolutionError(f"cannot evaluate expression node: {node!r}")


def bind_curry(function, bracket_text: str, frame) -> CurriedFunction:
    """Build a curried function and evaluate its bound values, once, in the scope
    where the curry is written."""
    from jazzoo.functions.rules.parse_curry import parse_curry

    curried = parse_curry(function, bracket_text)
    # A bound value is used by the curried function, so calls inside it are quiet.
    with frame.quietly():
        curried.bound = {
            name: evaluate_expression(source, frame)
            for name, source in curried.bound.items()
        }
    return curried


def _resolve_function_value(text: str, frame) -> T.Optional[CurriedFunction]:
    """Resolve a reference that names a function, or a variable holding one.

    Returns None when the name resolves to an ordinary string, which is what makes
    calling a string a ResolutionError rather than a silent no-op.
    """
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    split = split_reference_path(text)
    if split is None:
        return None
    sigil, path = split

    # A variable may hold a function value, and passes it on when reassigned. A
    # variable name is never dotted, so only an undotted path can be one.
    if "." not in path:
        value = frame.lookup(sigil, path)
        if isinstance(value, CurriedFunction):
            return value

    function = get_function_by_path(frame.module, path)
    if function is None:
        return None
    # A bare function symbol is the same as applying empty brackets to it.
    return CurriedFunction(function=function, bound={}, explicitly_unbound=[])


def _resolve_reference_text(text: str, frame) -> T.Any:
    """Resolve a reference in expression position.

    A dotted name walks into a structured value, so the first segment names the
    variable and the rest is a path. Text after the reference - which only occurs
    when a `\\` terminated the name - is literal.
    """
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    matches = parse_references(text)
    if not matches:
        return text

    match = matches[0]
    suffix = text[match.end :]

    # A bare symbol in expression position may name a function rather than a
    # variable, in which case it is the function value (same as `f[]`).
    stored = frame.lookup(match.reference.sigil, match.reference.parts[0])
    if stored is ABSENT:
        function_value = _resolve_function_value(text, frame)
        if function_value is not None:
            return function_value

    value = resolve_reference(match.reference, frame)
    if not suffix:
        # A lone reference keeps its value's type rather than being rendered.
        return value
    return f"{render_value(value)}{suffix}"


def _is_condition_true(node: T.Any, frame) -> bool:
    return is_truthy(_evaluate_node(node, frame))


def _apply_stage(stage: T.Any, value: str, frame) -> str:
    """Apply one pipe stage to the piped value.

    A stage is either a built-in ⚙️ operator or a function value with exactly one
    unbound parameter, which the piped value fills.
    """
    if isinstance(stage, ReferenceText):
        matches = parse_references(stage.text)
        if matches and matches[0].reference.sigil is Sigil.SYSTEM:
            name = matches[0].reference.name
            if is_builtin_pipe(name):
                return apply_builtin_pipe(name, value)
            raise ResolutionError(f"no such pipe operator: ⚙️.{name}")

        curried = _resolve_function_value(stage.text, frame)
        if curried is not None:
            return _pipe_into(curried, value, frame)

    if isinstance(stage, Curry):
        target = _resolve_function_value(stage.target.text, frame)
        if target is None:
            raise ResolutionError(f"no such function: {stage.target.text}")
        return _pipe_into(bind_curry(target.function, stage.text, frame), value, frame)

    if isinstance(stage, PathJoin):
        # `a | ⚙️.abs / b` - the pipe applies to the join's left side only.
        left = _apply_stage(stage.left, value, frame)
        return join_path(
            render_value(left), render_value(_evaluate_node(stage.right, frame))
        )

    if isinstance(stage, (And, Or, Not, CallValue, Ternary)):
        # A computed stage: evaluate it, then pipe into whatever it produced. This
        # is what lets `3 | (🐭.f1 or 🐭.f2)` choose a function and apply it.
        produced = _evaluate_node(stage, frame)
        if isinstance(produced, CurriedFunction):
            return _pipe_into(produced, value, frame)
        raise ResolutionError(
            f"cannot pipe into a value that is not a function: "
            f"{render_value(produced)!r}"
        )

    raise ResolutionError(f"cannot pipe into: {stage!r}")


def _pipe_into(curried: "CurriedFunction", value: str, frame) -> str:
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


def evaluate_expression(source: str, frame) -> str:
    """Evaluate one jazzoo expression against the current namespace state."""
    source = source.strip()
    if not source:
        return ""
    return _evaluate_node(parse_expression(source), frame)
