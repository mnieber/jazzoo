import os
import typing as T

from jazzoo.config.settings import CONFIG_FILES_ENV_VAR
from jazzoo.errors import ExecutionError


def load_config(
    path: str,
    is_required: bool = True,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> None:
    if not os.path.isfile(path):
        if is_required:
            raise ExecutionError(
                f"config file not found: {path}", filename=filename, line=line
            )
        return

    value = os.environ.get(CONFIG_FILES_ENV_VAR, "")
    config_files = value.split(os.pathsep) if value else []

    config_file = os.path.abspath(path)
    if config_file not in config_files:
        os.environ[CONFIG_FILES_ENV_VAR] = os.pathsep.join(config_files + [config_file])
