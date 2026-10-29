import os

from ..settings import CONFIRM_ENV_VAR


def is_confirm_on() -> bool:
    return os.environ.get(CONFIRM_ENV_VAR) == "1"
