import typing as T

from jazzoo.completions.models.candidate import Candidate
from jazzoo.completions.rules.get_completions import get_completions
from jazzoo.completions.rules.load_module_for_completion import (
    load_module_for_completion,
)
from jazzoo.modules.models.module import Module
from jazzoo.zoo.rules.complete_zoo_env import complete_zoo_env
from jazzoo.zoo.rules.find_zoo_env_of_venv import find_zoo_env_of_venv
from jazzoo.zoo.rules.get_zoo_venv_dir import get_zoo_venv_dir

# The options of jaz that zoo takes: all but --file
ZOO_OPTIONS = ("--list", "--list-all", "--which", "--trace", "--confirm", "--help")


def get_zoo_completions(words: T.List[str]) -> T.List[Candidate]:
    if words[:1] == ["env"] and len(words) > 1:
        return complete_zoo_env(words[1:])

    candidates = []
    if len(words) <= 1 and "env".startswith(words[0] if words else ""):
        candidates.append(Candidate("env"))
    return candidates + get_completions(words, ZOO_OPTIONS, _load_root_module)


def _load_root_module(filename: T.Optional[str]) -> T.Optional[Module]:
    # The targets come from the root directory of the active env
    env = find_zoo_env_of_venv(get_zoo_venv_dir())
    if env is None:
        return None
    return load_module_for_completion(None, env.root_dir)
