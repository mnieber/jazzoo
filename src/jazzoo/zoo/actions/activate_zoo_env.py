from jazzoo.zoo.actions.write_recent_zoo_envs import write_recent_zoo_envs
from jazzoo.zoo.rules.get_activate_filename import get_activate_filename
from jazzoo.zoo.rules.get_zoo_env import get_zoo_env
from jazzoo.zoo.rules.read_recent_zoo_envs import read_recent_zoo_envs


def activate_zoo_env(name: str) -> str:
    # Returns the line that the shell must source. The recent envs are updated when
    # the line is printed, not when it is sourced.
    get_zoo_env(name)

    recent = read_recent_zoo_envs()
    if recent.get("latest") != name:
        write_recent_zoo_envs({"latest": name, "previous": recent.get("latest")})

    return f"source {get_activate_filename(name)}"
