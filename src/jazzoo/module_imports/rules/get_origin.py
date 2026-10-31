from jazzoo.functions.models.function import Function


def get_origin(function: Function) -> Function:
    return function.origin or function
