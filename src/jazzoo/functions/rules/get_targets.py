import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_targets(module: Module) -> T.List[Function]:
    raise NotImplementedError
