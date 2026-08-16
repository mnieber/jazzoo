import copy
import os
import typing as T

from jazzoo.errors import ModuleImportError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.import_statement import ImportStatement
from jazzoo.modules.models.module import Module


def _exported_functions(module: Module) -> T.List[Function]:
    """The symbols a module offers its importers.

    Only the module's own targets. Functions it imported privately are not part of
    its surface, which is why `export *` does not pull them in transitively.
    """
    return [f for f in module.functions if f.is_target]


def _find_exported(module: Module, name: str) -> T.Optional[Function]:
    for function in _exported_functions(module):
        if function.name == name:
            return function
    return None


def resolve_import(
    statement: ImportStatement, into: Module, load: T.Callable[[str, str], Module]
) -> None:
    """Apply one import or export statement to the importing module.

    `import` binds the named symbols under a namespace sub-module and leaves them
    private. `export` binds them flat in the importing module and marks them
    targets, so they are reachable from the CLI.
    """
    source_path = statement.path
    if not os.path.isabs(source_path):
        source_path = os.path.join(os.path.dirname(into.filename), source_path)
    source_path = os.path.normpath(source_path)

    if not os.path.exists(source_path):
        raise ModuleImportError(
            f"no such module: {statement.path}",
            filename=statement.filename,
            line=statement.line,
        )

    source = load(source_path, statement.filename)

    if statement.is_wildcard:
        selected = [(f, f.name) for f in _exported_functions(source)]
    else:
        selected = []
        for symbol in statement.symbols:
            function = _find_exported(source, symbol.name)
            if function is None:
                raise ModuleImportError(
                    f"{os.path.basename(source_path)} does not export "
                    f"'{symbol.name}'",
                    filename=statement.filename,
                    line=statement.line,
                )
            selected.append((function, symbol.alias))

    if statement.is_export:
        # Re-exported functions land flat in 🐭 and become targets of this module.
        for function, alias in selected:
            exported = copy.copy(function)
            exported.name = alias
            exported.is_target = True
            into.functions.append(exported)
        return

    # A private import: the symbols live under a namespace sub-module.
    namespace = _get_or_create_namespace(
        into, statement.alias, source, statement.line
    )
    for function, alias in selected:
        bound = copy.copy(function)
        bound.name = alias
        namespace.functions.append(bound)


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
