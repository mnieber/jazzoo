import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.module_validation.models.alternatives import Alternatives
from jazzoo.module_validation.rules.get_boolean_operand_functions import (
    get_boolean_operand_functions,
)
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE


def get_function_valued_locals(
    function: Function, module: Module, outer: T.Dict[str, Function]
) -> T.Dict[str, T.Any]:
    """🐆 variables in this body that hold a function, keyed by name."""
    from jazzoo.expressions.rules.parse_expression import (
        Curry,
        ReferenceText,
        parse_expression,
    )
    from jazzoo.references.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.functions.rules.parse_curry import parse_curry

    found: T.Dict[str, T.Any] = {}
    for block in function.body:
        for block_line in block.lines:
            assignment = _ASSIGNMENT_RE.match(block_line.text.strip())
            if assignment is None:
                continue
            try:
                node = parse_expression(assignment.group("rhs").strip())
            except Exception:
                continue

            collected = get_boolean_operand_functions(node, module, {**outer, **found})
            if collected is not None:
                functions, not_functions = collected
                if functions:
                    # One of several values, decided at run time. Assigning it is
                    # fine; whether it can be *called* is settled at the call site.
                    found[assignment.group("name")] = Alternatives(
                        functions=functions, not_functions=not_functions
                    )
                continue

            if isinstance(node, Curry):
                target_text, brackets = node.target.text, node.text
            elif isinstance(node, ReferenceText):
                target_text, brackets = node.text, "[]"
            else:
                continue

            split = split_reference_path(target_text)
            if split is None:
                continue
            path = split[1]

            held = outer.get(path) or found.get(path)
            target = (
                held.function
                if held is not None
                else get_function_by_path(module, path)
            )
            if target is None:
                continue
            found[assignment.group("name")] = parse_curry(
                target, brackets, filename=block.filename, line=block_line.line
            )
    return found
