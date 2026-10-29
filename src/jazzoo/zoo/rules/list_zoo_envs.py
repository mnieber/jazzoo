import os
import typing as T

from jazzoo.settings import get_zoo_config_dir
from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.get_zoo_env import get_zoo_env


def list_zoo_envs() -> T.List[ZooEnv]:
    envs_dir = os.path.join(get_zoo_config_dir(), "envs")
    if not os.path.isdir(envs_dir):
        return []
    return [
        get_zoo_env(name)
        for name in sorted(os.listdir(envs_dir))
        if os.path.isdir(os.path.join(envs_dir, name))
    ]
