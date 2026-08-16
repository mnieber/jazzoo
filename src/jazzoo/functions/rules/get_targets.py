import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_targets(module: Module) -> T.List[Function]:
    """The functions callable from the CLI: this module's own, minus [private] ones.

    Functions reached through an imported namespace are targets of the module that
    defines them, not of the module that imported it.
    """
    return [function for function in module.functions if function.is_target]
