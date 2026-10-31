import typing as T

from jazzoo.functions.models.curried_function import CurriedFunction


def resolve_function_value(text: str, frame) -> T.Optional[CurriedFunction]:
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
