import os
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ExecutionError, ModuleImportError, ParseError
from jazzoo.modules.actions.resolve_import import resolve_import
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_import_statement import parse_import_statement
from jazzoo.modules.rules.parse_source import Assignment, BuiltinCall, parse_source
from jazzoo.modules.rules.validate_module import (
    validate_builtin_call,
    validate_module,
)

# 🐐 is shared by every module in a run.
_GLOBALS: T.Dict[str, T.Any] = {}


def parse_module(path: str) -> Module:
    """Load a .jaz file: parse it, wire its imports, validate it, and run its
    top-level assignments.

    Everything decidable from the parse tree is raised here rather than when a
    target runs (design section 12), so a bad call site fails even if a different
    target is invoked. Note that loading also *executes*: a top-level assignment
    may call a function whose body is a shebang block, and a top-level ⚙️.loadenv
    changes the environment.
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
    validate_module(module, _resolve_function_valued(parsed, module))
    for statement in parsed.statements:
        if isinstance(statement, BuiltinCall):
            validate_builtin_call(
                statement.name,
                [(a.name, a.value) for a in statement.arguments],
                statement.filename,
                statement.line,
            )

    # Top-level statements run last, and may call into the imported modules. Their
    # values are used, not shown, so they run quietly.
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    frame = Frame(module=module, root_module=root, globals_=_GLOBALS)
    with frame.quietly():
        for statement in parsed.statements:
            _run_statement(statement, frame, evaluate_expression)

    module.is_initialized = True
    return module


def _run_statement(statement, frame: Frame, evaluate_expression) -> None:
    source = statement.text if isinstance(statement, BuiltinCall) else statement.rhs
    try:
        value = evaluate_expression(source, frame)
    except (ParseError, ExecutionError) as error:
        # Attribute the error to the statement, not to jazzoo's internals.
        raise type(error)(
            error.message,
            filename=error.filename or statement.filename,
            line=error.line if error.line is not None else statement.line,
        ) from None
    if isinstance(statement, Assignment):
        frame.assign(statement.sigil, statement.name, value)


def _resolve_function_valued(parsed, module: Module) -> T.Dict[str, T.Any]:
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


def _function_valued_branch(node: T.Any) -> T.Any:
    """The branch of a boolean expression that decides whether it is callable.

    Shares the reasoning in validate_module's copy: `and` and `or` yield one of
    their operands, so the left one stands in for a value only known at run time.
    """
    from jazzoo.expressions.models.boolean import And, Or

    while isinstance(node, (And, Or)):
        node = node.left
    return node


def _attach_module(function, module: Module) -> None:
    function.module = module
    for local in function.functions:
        _attach_module(local, module)


def _check_name_collisions(parsed, module: Module) -> None:
    """A name denotes one of a variable, a function or a namespace - never two.

    A reference names only a sigil and a name, so `🐭.foo` does not say which to look
    in (design section 13). Only the first segment of a dotted name is checked, since
    that is what names something in this scope: `🐭.docker.build` collides with a
    `docker` namespace but not with a module-level `build`.
    """
    # Every declaration this scope makes, as (line, name), so the error can point at
    # whichever of a colliding pair came second in the file.
    declarations: T.List[T.Tuple[int, str]] = []

    for function in module.functions:
        declarations.append((function.line or 0, function.name))

    for child in module.modules:
        declarations.append((child.imported_at_line or 0, child.name))

    # A variable may be assigned more than once - `🐭.cfg = "x"` then
    # `🐭.cfg.name = "y"` is a re-assignment, not a redeclaration - so each variable
    # contributes one declaration, at the line it first appears.
    first_assignment: T.Dict[str, int] = {}
    for assignment in parsed.assignments:
        if assignment.sigil is not Sigil.MOUSE:
            continue
        # Only the first segment names something in this scope.
        name = assignment.name.split(".")[0]
        first_assignment.setdefault(name, assignment.line or 0)
    declarations.extend((line, name) for name, line in first_assignment.items())

    seen: T.Set[str] = set()
    for line, name in sorted(declarations):
        if name in seen:
            raise ParseError(
                f"'{name}' is already defined in this scope",
                filename=module.filename,
                line=line,
            )
        seen.add(name)
