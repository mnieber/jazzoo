import os

from jazzoo.settings import get_zoo_config_dir


def get_alias_config_file() -> str:
    return os.path.join(get_zoo_config_dir(), "config")
