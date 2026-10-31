from jazzoo.functions.models.curried_function import CurriedFunction


def bind_curry(function, bracket_text: str, frame) -> CurriedFunction:
    """Build a curried function and evaluate its bound values, once, in the scope
    where the curry is written."""
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.functions.rules.parse_curry import parse_curry

    curried = parse_curry(function, bracket_text)
    # A bound value is used by the curried function, so calls inside it are quiet.
    with frame.quietly():
        curried.bound = {
            name: evaluate_expression(source, frame)
            for name, source in curried.bound.items()
        }
    return curried
