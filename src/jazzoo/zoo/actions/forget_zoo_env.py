import os
import shutil

from jazzoo.zoo.actions.write_recent_zoo_envs import write_recent_zoo_envs
from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.get_zoo_env import get_zoo_env
from jazzoo.zoo.rules.get_zoo_env_dir import get_zoo_env_dir
from jazzoo.zoo.rules.get_zoo_link import get_zoo_link
from jazzoo.zoo.rules.read_recent_zoo_envs import read_recent_zoo_envs


def forget_zoo_env(name: str) -> ZooEnv:
    # Only what zoo created itself is removed: never the project or the venv
    env = get_zoo_env(name)
    shutil.rmtree(get_zoo_env_dir(name))

    # The zoo-<name> link is removed only while it still points into the venv
    link = get_zoo_link(name)
    if os.path.islink(link) and _is_inside(os.readlink(link), env.venv_dir):
        os.remove(link)

    recent = read_recent_zoo_envs()
    if name in recent.values():
        write_recent_zoo_envs(
            {key: (None if value == name else value) for key, value in recent.items()}
        )
    return env


def _is_inside(path: str, dir_name: str) -> bool:
    return path.startswith(dir_name.rstrip("/") + "/")
