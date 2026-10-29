import json
import os
import typing as T

from jazzoo.zoo.actions.write_latest_zoo_env_scripts import (
    write_latest_zoo_env_scripts,
)
from jazzoo.zoo.rules.read_recent_zoo_envs import get_recent_zoo_envs_filename


def write_recent_zoo_envs(recent: T.Dict[str, T.Optional[str]]) -> None:
    recent = {key: value for key, value in recent.items() if value}
    filename = get_recent_zoo_envs_filename()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(recent, f)

    # The latest-env scripts always follow the latest env
    write_latest_zoo_env_scripts(recent.get("latest"))
