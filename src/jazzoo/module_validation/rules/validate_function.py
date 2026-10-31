import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.module_validation.rules.get_braced_expressions import (
    get_braced_expressions,
)
from jazzoo.module_validation.rules.get_function_valued_locals import (
    get_function_valued_locals,
)
from jazzoo.module_validation.rules.validate_call import validate_call
from jazzoo.module_validation.rules.validate_call_text import validate_call_text
from jazzoo.module_validation.rules.validate_expression import validate_expression
from jazzoo.module_validation.rules.validate_pipes import validate_pipes
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE, _SIGIL_TEXTS


def validate_function(
    function: Function, module: Module, function_valued: T.Dict[str, Function]
) -> None:
    # A default is an expression, so an unquoted string in it is a ParseError, and a
    # call in it is checked like a call in the body.
    for parameter in function.parameters:
        if parameter.default is not None:
            validate_expression(parameter.default, function.filename, function.line)
            validate_call_text(
                parameter.default.strip(),
                module,
                function,
                function.filename,
                function.line,
                function_valued,
            )

    for dependency in function.dependencies:
        validate_call(
            dependency.target_path,
            [(a.name, a.value) for a in dependency.arguments],
            module,
            function,
            dependency.filename,
            dependency.line,
            function_valued,
        )

    # A body may assign a function to a 🐆 variable and then call through it, so
    # those names are collected before the calls in this body are checked.
    in_scope = dict(function_valued)
    in_scope.update(get_function_valued_locals(function, module, function_valued))

    for block in function.body:
        for block_line in block.lines:
            trimmed = block_line.text.strip()
            assignment = _ASSIGNMENT_RE.match(trimmed)
            if assignment is not None:
                # ⚙️ is read-only everywhere, including inside a body. Bodies are
                # opaque to the parser, so the check belongs here rather than in
                # parse_source.
                if _SIGIL_TEXTS[assignment.group("sigil")] is Sigil.SYSTEM:
                    raise ParseError(
                        "cannot assign to the read-only ⚙️ namespace",
                        filename=block.filename,
                        line=block_line.line,
                    )
            for expression in get_braced_expressions(
                block_line.text, block.filename, block_line.line
            ):
                validate_expression(expression, block.filename, block_line.line)
                validate_call_text(
                    expression.strip(),
                    module,
                    function,
                    block.filename,
                    block_line.line,
                    in_scope,
                )
            candidate = assignment.group("rhs").strip() if assignment else trimmed
            if assignment is not None:
                # An unquoted string on the right-hand side is a ParseError, and is
                # decidable from the source alone.
                validate_expression(candidate, block.filename, block_line.line)
            validate_pipes(candidate, module, in_scope, block.filename, block_line.line)
            validate_call_text(
                candidate, module, function, block.filename, block_line.line, in_scope
            )

    for local in function.functions:
        validate_function(local, module, in_scope)
