import typing as T

from jazzoo.modules.models.module import Module


def get_module_by_path(module: Module, path: str) -> T.Optional[Module]:
    """Look up a sub-module by dotted path.

    A single-segment path is the one-iteration case, not a special form. Returns
    None when any segment does not resolve.
    """
    current = module
    for segment in path.split("."):
        match = None
        for child in current.modules:
            if child.name == segment:
                match = child
                break
        if match is None:
            return None
        current = match
    return current
