import os
import typing as T

from jazzoo.errors import ModuleImportError
from jazzoo.functions.models.function import Function
from jazzoo.module_imports.models.import_statement import ImportStatement
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


def _find_exported_layer(module: Module, name: str) -> T.Optional[Module]:
    """A layer the module exports, which an importer may re-export by name."""
    for layer in module.layers:
        if layer.name == name:
            return layer
    return None


def select_symbols(
    statement: ImportStatement, source: Module
) -> T.Tuple[T.List[T.Tuple[Function, str]], T.List[T.Tuple[Module, str]]]:
    """The functions and layers that a statement selects from the source module,
    each with the name it is bound under.

    A layer is an exported symbol too, so selection yields both kinds.
    """
    if statement.is_wildcard:
        selected = [(f, f.name) for f in _exported_functions(source)]
        selected_layers = [(l, l.name) for l in source.layers]
        return selected, selected_layers

    selected = []
    selected_layers = []
    for symbol in statement.symbols:
        function = _find_exported(source, symbol.name)
        if function is not None:
            selected.append((function, symbol.alias))
            continue

        layer = _find_exported_layer(source, symbol.name)
        if layer is not None:
            selected_layers.append((layer, symbol.alias))
            continue

        raise ModuleImportError(
            f"{os.path.basename(source.filename)} does not export " f"'{symbol.name}'",
            filename=statement.filename,
            line=statement.line,
        )
    return selected, selected_layers
