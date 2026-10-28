import os
import typing as T

from .._vendor import yaml
from ..errors import ConfigFileError


def read_config_file(config_file: str) -> T.Dict[T.Any, T.Any]:
    if not os.path.isfile(config_file):
        raise ConfigFileError(f"{config_file}: config file not found")

    with open(config_file, "r", encoding="utf-8") as handle:
        text = handle.read()

    try:
        tree = yaml.safe_load(text)
    except yaml.MarkedYAMLError as error:
        mark = error.problem_mark or error.context_mark
        location = f"{config_file}:{mark.line + 1}" if mark else config_file
        raise ConfigFileError(f"{location}: {error.problem or error.context}")
    except yaml.YAMLError as error:
        raise ConfigFileError(f"{config_file}: {error}")

    if tree is None:
        return {}
    if not isinstance(tree, dict):
        raise ConfigFileError(
            f"{config_file}: the top level of a config file must be a mapping"
        )
    return tree
