import os
import typing as T

from jazzoo.settings import get_zoo_config_dir
from jazzoo.zoo.rules.get_zoo_env_dir import get_zoo_env_dir


def write_latest_zoo_env_scripts(name: T.Optional[str]) -> None:
    for shell in ("bash", "fish"):
        if name is None:
            text = "# There is no latest zoo environment\n"
        else:
            activate = os.path.join(get_zoo_env_dir(name), f"activate.{shell}")
            text = (
                f"[ -f {activate} ] && source {activate}\n"
                if shell == "bash"
                else f"test -f {activate}; and source {activate}\n"
            )
        filename = os.path.join(get_zoo_config_dir(), f"latest.{shell}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
