import typing as T

from jazzoo.completions.models.candidate import Candidate
from jazzoo.completions.rules.complete_file_names import complete_file_names
from jazzoo.zoo.rules.list_zoo_envs import list_zoo_envs

# The options of zoo env that the completions offer
ZOO_ENV_OPTIONS = (
    "--latest",
    "--list",
    "--names",
    "--init",
    "--forget",
    "--install-fish",
    "--create-venv",
    "--use-venv",
    "--without-pip",
)


def complete_zoo_env(words: T.List[str]) -> T.List[Candidate]:
    *done, word = words or [""]
    previous = done[-1] if done else None

    if previous == "--use-venv":
        return complete_file_names(word)

    names = [env.name for env in list_zoo_envs()]
    if previous != "--forget":
        names += ["-", *ZOO_ENV_OPTIONS]
    return [Candidate(name) for name in names if name.startswith(word)]
