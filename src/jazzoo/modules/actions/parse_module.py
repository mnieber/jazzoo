import os
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ParseError
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import parse_source
from jazzoo.modules.rules.validate_module import validate_module

# 🐐 is shared by every module in a run.
_GLOBALS: T.Dict[str, T.Any] = {}


def parse_module(path: str) -> Module:
    """Load a .jaz file: parse it, validate it, and run its top-level assignments.

    Everything decidable from the parse tree is raised here rather than when a
    target runs (design section 12), so a bad call site fails even if a different
    target is invoked.
    """
    filename = os.path.abspath(path)
    with open(filename, "r", encoding="utf-8") as handle:
        source = handle.read()

    parsed = parse_source(source, filename)

    module = Module(
        filename=filename,
        name=os.path.basename(filename),
        functions=parsed.functions,
        modules=[],
        namespace={},
        variables=[],
    )
    for function in module.functions:
        _attach_module(function, module)

    _check_name_collisions(parsed, module)
    validate_module(module)

    # Module-level assignments run at load time, and may call functions.
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    frame = Frame(module=module, root_module=module, globals_=_GLOBALS)
    for assignment in parsed.assignments:
        value = evaluate_expression(assignment.rhs, frame)
        frame.assign(assignment.sigil, assignment.name, value)

    module.is_initialized = True
    return module


def _attach_module(function, module: Module) -> None:
    function.module = module
    for local in function.functions:
        _attach_module(local, module)


def _check_name_collisions(parsed, module: Module) -> None:
    """A scope may not define a variable and a function under the same name, nor
    two functions with the same name (design section 13)."""
    seen: T.Set[str] = set()
    for function in module.functions:
        if function.name in seen:
            raise ParseError(
                f"'{function.name}' is already defined in this scope",
                filename=function.filename,
                line=function.line,
            )
        seen.add(function.name)

    for assignment in parsed.assignments:
        if assignment.sigil is not Sigil.MOUSE:
            continue
        if assignment.name in seen:
            raise ParseError(
                f"'{assignment.name}' is already defined in this scope",
                filename=assignment.filename,
                line=assignment.line,
            )
