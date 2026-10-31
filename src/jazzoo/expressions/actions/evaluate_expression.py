import typing as T

from jazzoo.errors import ResolutionError
from jazzoo.expressions.actions.apply_pipe_stage import apply_pipe_stage
from jazzoo.expressions.actions.bind_curry import bind_curry
from jazzoo.expressions.actions.call_value import call_value
from jazzoo.expressions.actions.evaluate_call import evaluate_call
from jazzoo.expressions.models.boolean import And, Not, Or
from jazzoo.expressions.models.literal import Literal
from jazzoo.expressions.models.path_join import PathJoin
from jazzoo.expressions.models.pipe import Pipe
from jazzoo.expressions.models.ternary import Comparison, Ternary
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.rules.parse_expression import (
    CallValue,
    Call,
    Curry,
    JsonLiteral,
    ReferenceText,
    parse_expression,
)
from jazzoo.expressions.rules.resolve_function_value import resolve_function_value
from jazzoo.expressions.rules.resolve_reference_text import resolve_reference_text
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.expressions.utils.join_path import join_path
from jazzoo.expressions.utils.render_value import render_value


def evaluate_node(node: T.Any, frame) -> T.Any:
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
        return resolve_reference_text(node.text, frame)

    if isinstance(node, PathJoin):
        return join_path(
            render_value(evaluate_node(node.left, frame)),
            render_value(evaluate_node(node.right, frame)),
        )

    if isinstance(node, CallValue):
        return call_value(evaluate_node(node.target, frame), node.args, frame)

    if isinstance(node, Comparison):
        # A comparison can now sit inside `and`/`or`, so it has to yield a value of
        # its own rather than only being asked whether it holds.
        return render_value(evaluate_node(node.left, frame)) == render_value(
            evaluate_node(node.right, frame)
        )

    if isinstance(node, Or):
        # Yields an operand, not a boolean, and leaves the right one unevaluated
        # when the left already decides the answer.
        left = evaluate_node(node.left, frame)
        return left if is_truthy(left) else evaluate_node(node.right, frame)

    if isinstance(node, And):
        left = evaluate_node(node.left, frame)
        return evaluate_node(node.right, frame) if is_truthy(left) else left

    if isinstance(node, Not):
        return not is_truthy(evaluate_node(node.operand, frame))

    if isinstance(node, Ternary):
        if is_truthy(evaluate_node(node.condition, frame)):
            return evaluate_node(node.value, frame)
        return evaluate_node(node.otherwise, frame)

    if isinstance(node, Pipe):
        value = evaluate_node(node.value, frame)
        for stage in node.stages:
            value = apply_pipe_stage(stage, value, frame)
        return value

    if isinstance(node, Curry):
        target = resolve_function_value(node.target.text, frame)
        if target is None:
            raise ResolutionError(f"no such function: {node.target.text}")
        return bind_curry(target.function, node.text, frame)

    raise ResolutionError(f"cannot evaluate expression node: {node!r}")


def evaluate_expression(source: str, frame) -> str:
    """Evaluate one jazzoo expression against the current namespace state."""
    source = source.strip()
    if not source:
        return ""
    return evaluate_node(parse_expression(source), frame)
