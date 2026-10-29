import json
import os
import typing as T

from jazzoo.settings import get_zoo_config_dir


def get_recent_zoo_envs_filename() -> str:
    return os.path.join(get_zoo_config_dir(), "recent.json")


def read_recent_zoo_envs() -> T.Dict[str, str]:
    filename = get_recent_zoo_envs_filename()
    if not os.path.exists(filename):
        return {}
    with open(filename, encoding="utf-8") as f:
        return json.load(f)
