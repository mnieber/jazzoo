import os

from jazzoo.zoo.errors import NoSuchZooEnvError
from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.get_zoo_env_dir import get_zoo_env_dir


def get_zoo_env(name: str) -> ZooEnv:
    env_dir = get_zoo_env_dir(name)
    if not os.path.isdir(env_dir):
        raise NoSuchZooEnvError(f"no such zoo environment: {name}")

    return ZooEnv(
        name=name,
        root_dir=os.readlink(os.path.join(env_dir, "root_dir")),
        venv_dir=os.readlink(os.path.join(env_dir, "venv_dir")),
    )
