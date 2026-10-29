import os
import typing as T

from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.list_zoo_envs import list_zoo_envs


def find_zoo_env_of_venv(venv_dir: str) -> T.Optional[ZooEnv]:
    # A venv belongs to at most one env, so the first match is the only one
    venv_dir = os.path.realpath(venv_dir)
    for env in list_zoo_envs():
        if os.path.realpath(env.venv_dir) == venv_dir:
            return env
    return None
