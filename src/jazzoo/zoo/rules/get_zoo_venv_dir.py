import sys


def get_zoo_venv_dir() -> str:
    # The venv that this zoo runs in
    return sys.prefix
