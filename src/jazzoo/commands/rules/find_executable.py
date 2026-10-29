import os
import shutil
import typing as T

from ..errors import CommandNotFoundError


def find_executable(name: str, environ: T.Dict[str, str]) -> str:
    # A name with a slash is a path, as in a shell
    if "/" in name:
        if os.path.isfile(name) and os.access(name, os.X_OK):
            return name
        raise CommandNotFoundError(f"command not found: {name}")

    path = shutil.which(name, path=environ.get("PATH", os.defpath))
    if path is None:
        raise CommandNotFoundError(f"command not found: {name}")
    return path
