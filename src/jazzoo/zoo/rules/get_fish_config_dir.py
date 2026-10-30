import os

from jazzoo.settings import get_config_home


def get_fish_config_dir() -> str:
    # The directory where fish itself looks for its config
    return os.path.join(get_config_home(), "fish")
