import os
import typing as T

from jazzoo.zoo.models.zoo_env import ZooEnv


def format_zoo_env_list(envs: T.List[ZooEnv], active: T.Optional[str]) -> T.List[str]:
    width = max((len(env.name) for env in envs), default=0)
    lines = []
    for env in envs:
        marker = "* " if env.name == active else "  "
        line = f"{marker}{env.name.ljust(width)}  {env.root_dir}"
        if not os.path.isdir(env.root_dir):
            line += " (root dir missing)"
        elif not os.path.isdir(env.venv_dir):
            line += " (venv missing)"
        lines.append(line)
    return lines
