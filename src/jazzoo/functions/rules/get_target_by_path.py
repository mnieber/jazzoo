import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_target_by_path(module: Module, path: str) -> T.Optional[Function]:
    """Look up a CLI target by name, or by dotted path once export layers exist.

    This is the CLI's counterpart to `get_function_by_path`: it walks the *export*
    surface, so only targets are reachable and an import namespace is not. A
    single-segment path is the common case - the name of a target in this module.
    """
    from jazzoo.functions.rules.get_targets import get_targets

    segments = path.split(".")
    if len(segments) == 1:
        for function in get_targets(module):
            if function.name == path:
                return function
        return None

    # Dotted paths reach into export layers, which do not exist yet. Returning None
    # keeps `no such target` as the CLI's answer until they do.
    return None
