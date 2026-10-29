import os

from jazzoo.settings import get_zoo_bin_dir


def get_zoo_link(name: str) -> str:
    return os.path.join(get_zoo_bin_dir(), f"zoo-{name}")
