import os

from jazzoo.zoo.rules.get_shell_name import get_shell_name
from jazzoo.zoo.rules.get_zoo_env_dir import get_zoo_env_dir


def get_activate_filename(name: str) -> str:
    return os.path.join(get_zoo_env_dir(name), f"activate.{get_shell_name()}")
