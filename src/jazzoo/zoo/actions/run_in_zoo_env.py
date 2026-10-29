import os
import typing as T

from jazzoo.zoo.errors import NotInZooEnvError, RootDirMissingError
from jazzoo.zoo.rules.find_zoo_env_of_venv import find_zoo_env_of_venv
from jazzoo.zoo.rules.get_zoo_venv_dir import get_zoo_venv_dir


def run_in_zoo_env(argv: T.List[str]) -> int:
    from jazzoo.runtime.entrypoints.jazzoo import run as run_jaz

    venv_dir = get_zoo_venv_dir()
    env = find_zoo_env_of_venv(venv_dir)
    if env is None:
        raise NotInZooEnvError(
            f"not in a zoo environment (venv: {venv_dir}); "
            "activate one with `zoo env <name>`"
        )
    if not os.path.isdir(env.root_dir):
        raise RootDirMissingError(
            f"the root directory of zoo environment {env.name} does not exist: "
            + env.root_dir
        )

    # The target runs in the root directory, but ⚙️.invocation_dir is where zoo
    # was called from
    invocation_dir = os.getcwd()
    os.chdir(env.root_dir)
    return run_jaz(argv, invocation_dir=invocation_dir)
