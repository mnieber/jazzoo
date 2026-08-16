import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_function_by_path(module: Module, path: str) -> T.Optional[Function]:
    """Look up a function by dotted path, descending through sub-modules.

    Every segment but the last names a sub-module; the last names a function.
    Returns None when any segment does not resolve.
    """
    from jazzoo.modules.rules.get_module_by_path import get_module_by_path

    segments = path.split(".")
    if len(segments) > 1:
        module = get_module_by_path(module, ".".join(segments[:-1]))
        if module is None:
            return None

    name = segments[-1]
    for function in module.functions:
        if function.name == name:
            return function
    return None
