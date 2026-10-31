import copy
import typing as T

from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.module_imports.models.import_statement import ImportStatement
from jazzoo.module_imports.rules.bind_copy import bind_copy
from jazzoo.module_imports.rules.find_bound_function import find_bound_function
from jazzoo.module_imports.rules.is_same_definition import is_same_definition
from jazzoo.modules.models.module import Module


def bind_layered_export(
    selected: T.List[T.Tuple[Function, str]],
    selected_layers: T.List[T.Tuple[Module, str]],
    into: Module,
    statement: ImportStatement,
    source: Module,
    layer_alias: str,
) -> None:
    """Exported symbols grouped under a layer, reachable from the CLI only.

    The layer is created on first use and reused afterwards, which is what makes
    repeated exports into one alias aggregate. A name may be taken by a function or
    by a nested layer, so both are checked: two exports landing different symbols
    under one name in a layer is a ParseError, attributed to the second statement.
    """
    layer = _get_or_create_layer(into, layer_alias, source, statement.line)

    for nested, alias in selected_layers:
        _check_free(layer, alias, layer_alias, statement)
        # Re-bound under its new name, so renaming a layer renames the path segment
        # without disturbing the layer it came from.
        layer.layers.append(_rebind_layer(nested, alias))

    for function, alias in selected:
        if is_same_definition(find_bound_function(layer.functions, alias), function):
            continue
        _check_free(layer, alias, layer_alias, statement)
        exported = bind_copy(function, alias, statement)
        exported.is_target = True
        layer.functions.append(exported)


def _check_free(
    layer: Module, alias: str, layer_alias: str, statement: ImportStatement
) -> None:
    """A name in a layer denotes one thing: a target or a nested layer, never both."""
    taken = any(f.name == alias for f in layer.functions) or any(
        l.name == alias for l in layer.layers
    )
    if taken:
        raise ParseError(
            f"'{alias}' is already exported into '{layer_alias}'",
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
