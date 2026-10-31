import typing as T

from jazzoo.functions.models.function import Function


def find_bound_function(
    functions: T.List[Function], alias: str
) -> T.Optional[Function]:
    for function in functions:
        if function.name == alias:
            return function
    return None
