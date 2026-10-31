import copy

from jazzoo.functions.models.function import Function
from jazzoo.module_imports.models.import_statement import ImportStatement
from jazzoo.module_imports.rules.get_origin import get_origin


def bind_copy(function: Function, alias: str, statement: ImportStatement) -> Function:
    bound = copy.copy(function)
    bound.name = alias
    bound.origin = get_origin(function)
    bound.bound_at_line = statement.line
    return bound
