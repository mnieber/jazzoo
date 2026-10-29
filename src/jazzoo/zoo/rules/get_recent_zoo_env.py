from jazzoo.zoo.errors import NoRecentZooEnvError
from jazzoo.zoo.rules.read_recent_zoo_envs import read_recent_zoo_envs


def get_recent_zoo_env(which: str) -> str:
    # which is "latest" or "previous"
    name = read_recent_zoo_envs().get(which)
    if not name:
        raise NoRecentZooEnvError(f"there is no {which} zoo environment")
    return name
