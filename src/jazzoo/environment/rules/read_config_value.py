import typing as T

from jazzoo.config import ConfigError, get_config
from jazzoo.errors import ExecutionError

# The default of read_config_value when the call has none
NO_DEFAULT = object()


def read_config_value(
    path: str,
    default: T.Any = NO_DEFAULT,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> T.Any:
    """The value at path in the merged config, as a jazzoo value."""
    try:
        if default is NO_DEFAULT:
            value = get_config(path)
        else:
            value = get_config(path, default=default)
    except (ConfigError, ValueError) as error:
        raise ExecutionError(str(error), filename=filename, line=line) from None

    if not _is_json_value(value):
        raise ExecutionError(
            f"the config value at {path} is not a JSON value (e.g. a date, or a key "
            "that is not a string)",
            filename=filename,
            line=line,
        )
    return value


def _is_json_value(value: T.Any) -> bool:
    if value is None or isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(_is_json_value(x) for x in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(x) for key, x in value.items()
        )
    return False
