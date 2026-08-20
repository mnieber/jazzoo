import typing as T

from jazzoo.modules.models.module import Module

# A layer is shown as a single entry with this suffix, so a listing stays the size
# of the file that produced it rather than expanding the whole tree.
LAYER_SUFFIX = "..."


def list_one_level(module: Module, prefix: str = "") -> T.List[str]:
    """The targets and layers directly under `module`, one level deep.

    Targets are listed by name; a layer is listed as `name...` rather than being
    expanded, which is what `jaz --list` and `jaz --list <layer>` print.
    """
    from jazzoo.functions.rules.get_targets import get_targets

    lines = [prefix + f.name for f in get_targets(module)]
    lines.extend(prefix + layer.name + LAYER_SUFFIX for layer in module.layers)
    return lines


def list_all(module: Module, prefix: str = "") -> T.List[str]:
    """Every target at every depth, as dotted paths.

    Circular imports are allowed (design section 14), so the walk tracks the layers
    it has already entered along the current path: one that reappears is skipped
    rather than descended into. That makes the walk terminate and keeps any one
    target from being printed twice.

    Layers are tracked by identity, not by source file: a layer is a *binding*, and
    two different layers may be bound from the same .jaz file. Keying on the
    filename would mistake such a pair for a cycle and hide real targets.
    """
    return _walk(module, prefix, set())


def _walk(module: Module, prefix: str, entered: T.FrozenSet[int]) -> T.List[str]:
    from jazzoo.functions.rules.get_targets import get_targets

    lines = [prefix + f.name for f in get_targets(module)]
    for layer in module.layers:
        if id(layer) in entered:
            continue
        lines.extend(
            _walk(layer, prefix + layer.name + ".", entered | {id(layer)})
        )
    return lines
