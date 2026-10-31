import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.module_imports.rules.get_origin import get_origin


def is_same_definition(existing: T.Optional[Function], function: Function) -> bool:
    """Whether a name is already bound to this very definition, e.g. because it
    arrived along another path. Binding it again is then a no-op."""
    return existing is not None and get_origin(existing) is get_origin(function)
