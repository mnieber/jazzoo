import typing as T

from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.format_zoo_env_line import format_zoo_env_line


def format_zoo_env_list(envs: T.List[ZooEnv], active: T.Optional[str]) -> T.List[str]:
    width = max((len(env.name) for env in envs), default=0)
    return [
        ("* " if env.name == active else "  ") + format_zoo_env_line(env, width)
        for env in envs
    ]
