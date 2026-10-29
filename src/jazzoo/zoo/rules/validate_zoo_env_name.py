import re

from jazzoo.zoo.errors import InvalidZooEnvNameError

_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


def validate_zoo_env_name(name: str) -> None:
    if not _NAME.fullmatch(name):
        raise InvalidZooEnvNameError(
            f"invalid zoo environment name: {name!r} (use letters, digits, '-', '_' "
            "and '.', and don't start with '-' or '.')"
        )
