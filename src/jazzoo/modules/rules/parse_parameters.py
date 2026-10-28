import typing as T

from jazzoo.functions.models.parameter import Parameter
from jazzoo.utils.split_top_level import split_top_level


def parse_parameters(text: str, filename: str, line: int) -> T.List[Parameter]:
    parameters: T.List[Parameter] = []
    for chunk in split_top_level(text, ","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            name, _, default = chunk.partition("=")
            parameters.append(Parameter(name=name.strip(), default=default.strip()))
        else:
            parameters.append(Parameter(name=chunk, default=None))
    return parameters
