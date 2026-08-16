from jazzoo.modules.actions.parse_module import _GLOBALS
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module


def evaluate(module: Module, source: str) -> str:
    """Evaluate a jazzoo expression in the context of `module`.

    A call is one kind of expression, so `🐭.go()` and `🐭.some-variable` both go
    through here.
    """
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    frame = Frame(module=module, root_module=module, globals_=_GLOBALS)
    return evaluate_expression(source, frame)
