import os
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ModuleImportError, ParseError
from jazzoo.modules.actions.resolve_import import resolve_import
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_import_statement import parse_import_statement
from jazzoo.modules.rules.parse_source import parse_source
from jazzoo.modules.rules.validate_module import validate_module

# 🐐 is shared by every module in a run.
_GLOBALS: T.Dict[str, T.Any] = {}


def parse_module(path: str) -> Module:
    """Load a .jaz file: parse it, wire its imports, validate it, and run its
    top-level assignments.

    Everything decidable from the parse tree is raised here rather than when a
    target runs (design section 12), so a bad call site fails even if a different
    target is invoked. Note that loading also *executes*: a top-level assignment
    may call a function whose body is a shebang block.
    """
    _GLOBALS.clear()
    cache: T.Dict[str, Module] = {}
    return _load_module(os.path.abspath(path), None, cache, root=None)


def _load_module(
    filename: str,
    importer: T.Optional[str],
    cache: T.Dict[str, Module],
    root: T.Optional[Module],
) -> Module:
    """Load one file, honouring the module cache.

    The order matters and is fixed by design section 14: the cache entry is created
    *before* the imports are resolved, so a cycle terminates by finding the
    partially-initialized module; and this file's own assignments run *after* its
    imports, so they can call into them.
    """
    filename = os.path.abspath(filename)
    if filename in cache:
        return cache[filename]

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
        is_initialized=False,
    )
    # Registered before recursing, so a circular import finds this module rather
    # than loading it a second time.
    cache[filename] = module
    if root is None:
        root = module

    for function in module.functions:
        _attach_module(function, module)

    for line_no, text in parsed.imports:
        statement = parse_import_statement(text, filename, line_no)
        resolve_import(
            statement,
            module,
            lambda child, importer_file: _load_module(
                child, importer_file, cache, root
            ),
        )

    _check_name_collisions(parsed, module)
    validate_module(module)

    # Top-level assignments run last, and may call into the imported modules.
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    frame = Frame(module=module, root_module=root, globals_=_GLOBALS)
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
