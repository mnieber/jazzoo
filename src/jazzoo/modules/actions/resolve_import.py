import copy
import os
import typing as T

from jazzoo.errors import ModuleImportError, ParseError
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


def _find_exported_layer(module: Module, name: str) -> T.Optional[Module]:
    """A layer the module exports, which an importer may re-export by name."""
    for layer in module.layers:
        if layer.name == name:
            return layer
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

    # A layer is an exported symbol too, so selection yields both kinds. Layers are
    # only meaningful to a layered export; the other binders ignore them.
    selected_layers: T.List[T.Tuple[Module, str]] = []

    if statement.is_wildcard:
        selected = [(f, f.name) for f in _exported_functions(source)]
        selected_layers = [(l, l.name) for l in source.layers]
    else:
        selected = []
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
                f"{os.path.basename(source_path)} does not export "
                f"'{symbol.name}'",
                filename=statement.filename,
                line=statement.line,
            )

    if statement.is_export:
        if statement.alias is None:
            _bind_flat_export(selected, into, statement)
        else:
            _bind_layered_export(
                selected, selected_layers, into, statement, source
            )
        return

    _bind_private_import(selected, into, statement, source)


def _origin(function: Function) -> Function:
    return function.origin or function


def _bind_copy(
    function: Function, alias: str, statement: ImportStatement
) -> Function:
    bound = copy.copy(function)
    bound.name = alias
    bound.origin = _origin(function)
    bound.bound_at_line = statement.line
    return bound


def _find_bound(functions: T.List[Function], alias: str) -> T.Optional[Function]:
    for function in functions:
        if function.name == alias:
            return function
    return None


def _is_same_definition(existing: T.Optional[Function], function: Function) -> bool:
    """Whether a name is already bound to this very definition, e.g. because it
    arrived along another path. Binding it again is then a no-op."""
    return existing is not None and _origin(existing) is _origin(function)


def _bind_flat_export(
    selected: T.List[T.Tuple[Function, str]],
    into: Module,
    statement: ImportStatement,
) -> None:
    """Re-exported functions land flat in 🐭 and become targets of this module.

    A different function under a name that is already taken is left in place, so
    the module's collision check can report whichever declaration came second.
    """
    for function, alias in selected:
        if _is_same_definition(_find_bound(into.functions, alias), function):
            continue
        exported = _bind_copy(function, alias, statement)
        exported.is_target = True
        into.functions.append(exported)


def _bind_layered_export(
    selected: T.List[T.Tuple[Function, str]],
    selected_layers: T.List[T.Tuple[Module, str]],
    into: Module,
    statement: ImportStatement,
    source: Module,
) -> None:
    """Exported symbols grouped under a layer, reachable from the CLI only.

    The layer is created on first use and reused afterwards, which is what makes
    repeated exports into one alias aggregate. A name may be taken by a function or
    by a nested layer, so both are checked: two exports landing different symbols
    under one name in a layer is a ParseError, attributed to the second statement.
    """
    layer = _get_or_create_layer(into, statement.alias, source, statement.line)

    for nested, alias in selected_layers:
        _check_free(layer, alias, statement)
        # Re-bound under its new name, so renaming a layer renames the path segment
        # without disturbing the layer it came from.
        layer.layers.append(_rebind_layer(nested, alias))

    for function, alias in selected:
        if _is_same_definition(_find_bound(layer.functions, alias), function):
            continue
        _check_free(layer, alias, statement)
        exported = _bind_copy(function, alias, statement)
        exported.is_target = True
        layer.functions.append(exported)


def _check_free(layer: Module, alias: str, statement: ImportStatement) -> None:
    """A name in a layer denotes one thing: a target or a nested layer, never both."""
    taken = any(f.name == alias for f in layer.functions) or any(
        l.name == alias for l in layer.layers
    )
    if taken:
        raise ParseError(
            f"'{alias}' is already exported into '{statement.alias}'",
            filename=statement.filename,
            line=statement.line,
        )


def _rebind_layer(layer: Module, alias: str) -> Module:
    """The same layer under a possibly different name."""
    if layer.name == alias:
        return layer
    renamed = copy.copy(layer)
    renamed.name = alias
    return renamed


def _get_or_create_layer(
    into: Module, alias: str, source: Module, line: T.Optional[int] = None
) -> Module:
    """The export layer an alias names, created on first use.

    It starts empty: nested layers arrive through selection, the same way functions
    do, so that naming a layer and using `*` take the identical path.
    """
    for existing in into.layers:
        if existing.name == alias:
            return existing

    layer = Module(
        filename=source.filename,
        name=alias,
        functions=[],
        modules=[],
        layers=[],
        namespace=source.namespace,
        variables=[],
        is_initialized=source.is_initialized,
        imported_at_line=line,
    )
    into.layers.append(layer)
    return layer


def _bind_private_import(
    selected: T.List[T.Tuple[Function, str]],
    into: Module,
    statement: ImportStatement,
    source: Module,
) -> None:
    """A private import: the symbols live under a namespace sub-module."""
    namespace = _get_or_create_namespace(
        into, statement.alias, source, statement.line
    )
    for function, alias in selected:
        existing = _find_bound(namespace.functions, alias)
        if _is_same_definition(existing, function):
            continue
        if existing is not None:
            raise ParseError(
                f"'{alias}' is already imported into '{statement.alias}'",
                filename=statement.filename,
                line=statement.line,
            )
        namespace.functions.append(_bind_copy(function, alias, statement))


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
