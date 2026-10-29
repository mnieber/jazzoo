import os

from jazzoo.settings import get_shell


def get_shell_name() -> str:
    # Every shell other than fish can source the bash scripts
    return "fish" if os.path.basename(get_shell()) == "fish" else "bash"
