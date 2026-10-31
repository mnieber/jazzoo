import os
import typing as T

from jazzoo.errors import ModuleImportError
from jazzoo.module_imports.actions.bind_flat_export import bind_flat_export
from jazzoo.module_imports.actions.bind_layered_export import bind_layered_export
from jazzoo.module_imports.actions.bind_private_import import bind_private_import
from jazzoo.module_imports.models.import_statement import ImportStatement
from jazzoo.module_imports.rules.select_symbols import select_symbols
from jazzoo.modules.models.module import Module


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
    selected, selected_layers = select_symbols(statement, source)

    if statement.is_export:
        if statement.alias is None:
            bind_flat_export(selected, selected_layers, into, statement)
        else:
            bind_layered_export(
                selected, selected_layers, into, statement, source, statement.alias
            )
        return

    # Layers are only meaningful to an export: an import namespace holds functions.
    bind_private_import(selected, into, statement, source)
