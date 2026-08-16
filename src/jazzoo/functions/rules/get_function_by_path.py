import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module


def get_function_by_path(module: Module, path: str) -> T.Optional[Function]:
    raise NotImplementedError
