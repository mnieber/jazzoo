import typing as T

from jazzoo.modules.models.module import Module


def get_module_by_path(module: Module, path: str) -> T.Optional[Module]:
    raise NotImplementedError
