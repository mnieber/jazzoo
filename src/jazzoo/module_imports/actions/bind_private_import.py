import typing as T

from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.module_imports.models.import_statement import ImportStatement
from jazzoo.module_imports.rules.bind_copy import bind_copy
from jazzoo.module_imports.rules.find_bound_function import find_bound_function
from jazzoo.module_imports.rules.is_same_definition import is_same_definition
from jazzoo.modules.models.module import Module


def bind_private_import(
    selected: T.List[T.Tuple[Function, str]],
    into: Module,
    statement: ImportStatement,
    source: Module,
) -> None:
    """A private import: the symbols live under a namespace sub-module."""
    namespace = _get_or_create_namespace(into, statement.alias, source, statement.line)
    for function, alias in selected:
        existing = find_bound_function(namespace.functions, alias)
        if is_same_definition(existing, function):
            continue
        if existing is not None:
            raise ParseError(
                f"'{alias}' is already imported into '{statement.alias}'",
                filename=statement.filename,
                line=statement.line,
            )
        namespace.functions.append(bind_copy(function, alias, statement))


def _get_or_create_namespace(
    into: Module, alias: str, source: Module, line: T.Optional[int] = None
) -> Module:
    """The sub-module an alias names, created on first use.

    It shares the source module's namespace dict and filename, so 🐭 and ⚙️.module
    inside an imported function resolve against the defining file.
    """
    for child in into.modules:
        if child.name == alias:
            return child

    namespace = Module(
        filename=source.filename,
        name=alias,
        functions=[],
        modules=source.modules,
        namespace=source.namespace,
        variables=[],
        is_initialized=source.is_initialized,
        imported_at_line=line,
    )
    into.modules.append(namespace)
    return namespace
