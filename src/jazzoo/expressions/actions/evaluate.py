from jazzoo.modules.actions.parse_module import _GLOBALS
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module


def evaluate(module: Module, source: str) -> str:
    """Evaluate a jazzoo expression in the context of `module`.

    A call is one kind of expression, so `🐭.go()` and `🐭.some-variable` both go
    through here. The result is rendered as text, the same way substitution would
    splice it into a line.
    """
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.expressions.utils.render_value import render_value

    frame = Frame(module=module, root_module=module, globals_=_GLOBALS)
    return render_value(evaluate_expression(source, frame))
