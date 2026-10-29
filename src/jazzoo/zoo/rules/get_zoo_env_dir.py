import os

from jazzoo.settings import get_zoo_config_dir


def get_zoo_env_dir(name: str) -> str:
    return os.path.join(get_zoo_config_dir(), "envs", name)
