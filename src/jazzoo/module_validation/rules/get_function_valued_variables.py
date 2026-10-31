import typing as T

from jazzoo.modules.models.module import Module


def _function_valued_branch(node: T.Any) -> T.Any:
    """The branch of a boolean expression that decides whether it is callable.

    Shares the reasoning in get_boolean_operand_functions: `and` and `or` yield one
    of their operands, so the left one stands in for a value only known at run time.
    """
    from jazzoo.expressions.models.boolean import And, Or

    while isinstance(node, (And, Or)):
        node = node.left
    return node


def get_function_valued_variables(parsed, module: Module) -> T.Dict[str, T.Any]:
    """Module-level variables whose value is a function, keyed by variable name.

    A curry expression assigns a function to a variable, so a later call through
    that name has to resolve at parse time like any other call. This also validates
    the curry itself - binding an unknown parameter is an ArgumentError.
    """
    from jazzoo.expressions.rules.parse_expression import (
        Curry,
        ReferenceText,
        parse_expression,
    )
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.functions.rules.parse_curry import parse_curry

    found: T.Dict[str, T.Any] = {}
    for assignment in parsed.assignments:
        try:
            node = parse_expression(assignment.rhs)
        except Exception:
            continue

        node = _function_valued_branch(node)
        if isinstance(node, Curry):
            target_text = node.target.text
            brackets = node.text
        elif isinstance(node, ReferenceText):
            target_text = node.text
            brackets = "[]"
        else:
            continue

        split = split_reference_path(target_text)
        if split is None:
            continue
        name = split[1]

        function = get_function_by_path(module, name)
        if function is None:
            # May name another function-valued variable assigned above.
            inherited = found.get(name)
            function = inherited.function if inherited is not None else None
        if function is None:
            continue

        # Raises ArgumentError for an unknown bound or bare-named parameter.
        curried = parse_curry(
            function, brackets, filename=assignment.filename, line=assignment.line
        )
        found[assignment.name] = curried

    return found
