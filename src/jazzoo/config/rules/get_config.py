import copy
import typing as T

from ..errors import ConfigKeyError
from .get_loaded_config import get_loaded_config
from .get_value import MissingPathError, get_value
from .split_config_path import split_config_path

_NO_DEFAULT = object()


def get_config(path: str, default: T.Any = _NO_DEFAULT) -> T.Any:
    segments = split_config_path(path)
    loaded = get_loaded_config()

    try:
        value = get_value(loaded, segments)
    except MissingPathError as error:
        if default is not _NO_DEFAULT:
            return default
        raise ConfigKeyError(
            f"no such key in the config: {path} ('{error.segment}' was not found)"
        )

    # The caller may change the result, which must not change the cache
    return copy.deepcopy(value)
