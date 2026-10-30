import typing as T

from jazzoo.aliases.errors import AliasError
from jazzoo.aliases.rules.expand_alias import expand_alias
from jazzoo.completions.models.candidate import Candidate
from jazzoo.functions.models.function import Function
from jazzoo.functions.rules.get_target_by_path import get_target_by_path
from jazzoo.modules.models.module import Module


def complete_arguments(
    module: Module, target_name: str, arguments: T.List[str], word: str
) -> T.List[Candidate]:
    target = _get_target(module, target_name)
    if target is None:
        return []
    parameters = [parameter.name for parameter in target.parameters]

    # The parameters that are already given, by name or (the first) positionally
    given = {argument.partition("=")[0] for argument in arguments if "=" in argument}
    if arguments and "=" not in arguments[0] and parameters:
        given.add(parameters[0])

    return [
        Candidate(name + "=")
        for name in parameters
        if name not in given and (name + "=").startswith(word)
    ]


def _get_target(module: Module, target_name: str) -> T.Optional[Function]:
    target = get_target_by_path(module, target_name)
    if target is not None:
        return target

    # The parameters of an alias are those of the target of its expansion
    try:
        expansion = expand_alias(target_name)
    except AliasError:
        return None
    for token in expansion or []:
        if not token.startswith("-"):
            return get_target_by_path(module, token)
    return None
