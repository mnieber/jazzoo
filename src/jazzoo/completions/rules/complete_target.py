import typing as T

from jazzoo.aliases.errors import AliasError
from jazzoo.aliases.rules.get_alias_config_file import get_alias_config_file
from jazzoo.aliases.rules.read_aliases import read_aliases
from jazzoo.completions.models.candidate import Candidate
from jazzoo.functions.rules.format_signature import format_signature
from jazzoo.functions.rules.get_target_by_path import (
    get_layer_by_path,
    get_target_by_path,
)
from jazzoo.functions.rules.get_targets import get_targets
from jazzoo.modules.models.module import Module


def complete_target(module: Module, word: str) -> T.List[Candidate]:
    # The members of the layer before the last dot, or of the root module
    layer_path = word.rpartition(".")[0]
    layer = get_layer_by_path(module, layer_path) if layer_path else module
    if layer is None:
        return []
    prefix = layer_path + "." if layer_path else ""

    candidates = [
        Candidate(prefix + target.name, format_signature(target, prefix + target.name))
        for target in get_targets(layer)
    ]
    candidates.extend(
        Candidate(prefix + member.name + ".", "layer") for member in layer.layers
    )

    # An alias with the name of a target is left out, because the target wins
    candidates.extend(
        Candidate(alias)
        for alias in _read_aliases()
        if get_target_by_path(module, alias) is None
    )
    return [candidate for candidate in candidates if candidate.text.startswith(word)]


def _read_aliases() -> T.List[str]:
    try:
        return list(read_aliases(get_alias_config_file()))
    except AliasError:
        return []
