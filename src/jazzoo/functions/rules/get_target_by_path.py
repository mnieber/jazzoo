import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_layer_by_path(module: Module, path: str) -> T.Optional[Module]:
    """Look up an export layer by dotted path, descending through nested layers."""
    current = module
    for segment in path.split("."):
        match = None
        for layer in current.layers:
            if layer.name == segment:
                match = layer
                break
        if match is None:
            return None
        current = match
    return current


def get_target_by_path(module: Module, path: str) -> T.Optional[Function]:
    """Look up a CLI target by name, or by dotted path into an export layer.

    This is the CLI's counterpart to `get_function_by_path`: it walks the *export*
    surface, so an import namespace is not reachable and only targets are found.
    Every segment but the last names a layer; the last names a target.
    """
    from jazzoo.functions.rules.get_targets import get_targets

    segments = path.split(".")
    if len(segments) > 1:
        module = get_layer_by_path(module, ".".join(segments[:-1]))
        if module is None:
            return None

    name = segments[-1]
    for function in get_targets(module):
        if function.name == name:
            return function
    return None
