import typing as T

from jazzoo.functions.rules.get_target_by_path import (
    get_layer_by_path,
    get_target_by_path,
)
from jazzoo.modules.models.module import Module


def get_definition_file(module: Module, path: str) -> T.Optional[str]:
    """The file that defines the target at a dotted path, or the file of the layer
    that the path names. None when the path names neither.

    A target that an export bound is a copy; its origin is the definition, which
    may be several exports away.
    """
    target = get_target_by_path(module, path)
    if target is not None:
        return (target.origin or target).filename

    layer = get_layer_by_path(module, path)
    if layer is not None:
        return layer.filename
    return None
