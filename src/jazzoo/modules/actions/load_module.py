import os
import typing as T

from jazzoo.errors import ExecutionError, ParseError
from jazzoo.module_imports.actions.resolve_import import resolve_import
from jazzoo.module_imports.rules.parse_import_statement import parse_import_statement
from jazzoo.module_validation.rules.check_name_collisions import check_name_collisions
from jazzoo.module_validation.rules.get_function_valued_variables import (
    get_function_valued_variables,
)
from jazzoo.module_validation.rules.validate_builtin_call import validate_builtin_call
from jazzoo.module_validation.rules.validate_module import validate_module
from jazzoo.modules.models.assignment import Assignment
from jazzoo.modules.models.builtin_call import BuiltinCall
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import parse_source


def _attach_module(function, module: Module) -> None:
    function.module = module
    for local in function.functions:
        _attach_module(local, module)


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


def load_module(
    filename: str,
    cache: T.Dict[str, Module],
    root: T.Optional[Module],
    globals_: T.Dict[str, T.Any],
    invocation_dir: str = "",
    run_statements: bool = True,
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
        module.invocation_dir = invocation_dir

    for function in module.functions:
        _attach_module(function, module)

    for line_no, text in parsed.imports:
        statement = parse_import_statement(text, filename, line_no)
        resolve_import(
            statement,
            module,
            lambda child, importer_file: load_module(
                child, cache, root, globals_, run_statements=run_statements
            ),
        )

    check_name_collisions(parsed, module)
    validate_module(module, get_function_valued_variables(parsed, module))
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

    if run_statements:
        frame = Frame(module=module, root_module=root, globals_=globals_)
        with frame.quietly():
            for statement in parsed.statements:
                _run_statement(statement, frame, evaluate_expression)

    module.is_initialized = True
    return module
