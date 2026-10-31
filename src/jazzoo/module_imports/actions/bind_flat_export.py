import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.module_imports.actions.bind_layered_export import bind_layered_export
from jazzoo.module_imports.models.import_statement import ImportStatement
from jazzoo.module_imports.rules.bind_copy import bind_copy
from jazzoo.module_imports.rules.find_bound_function import find_bound_function
from jazzoo.module_imports.rules.is_same_definition import is_same_definition
from jazzoo.modules.models.module import Module


def bind_flat_export(
    selected: T.List[T.Tuple[Function, str]],
    selected_layers: T.List[T.Tuple[Module, str]],
    into: Module,
    statement: ImportStatement,
) -> None:
    """Re-exported functions land flat in 🐭 and become targets of this module.

    A different function under a name that is already taken is left in place, so
    the module's collision check can report whichever declaration came second.

    A re-exported layer becomes a layer of this module. Its contents are exported
    into a layer of the same name, so it aggregates with other exports into that
    name.
    """
    for function, alias in selected:
        if is_same_definition(find_bound_function(into.functions, alias), function):
            continue
        exported = bind_copy(function, alias, statement)
        exported.is_target = True
        into.functions.append(exported)

    for layer, alias in selected_layers:
        bind_layered_export(
            [(f, f.name) for f in layer.functions],
            [(l, l.name) for l in layer.layers],
            into,
            statement,
            layer,
            alias,
        )
