import os

from jazzoo.zoo.models.zoo_env import ZooEnv


def format_zoo_env_line(env: ZooEnv, width: int = 0) -> str:
    # The name (padded to width), the root directory, and what is missing
    line = f"{env.name.ljust(width)}  {env.root_dir}"
    if not os.path.isdir(env.root_dir):
        line += " (root dir missing)"
    elif not os.path.isdir(env.venv_dir):
        line += " (venv missing)"
    return line
