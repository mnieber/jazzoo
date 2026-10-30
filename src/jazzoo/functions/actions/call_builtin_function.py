import typing as T

from jazzoo.environment.actions.load_config import load_config
from jazzoo.environment.actions.load_env import load_env
from jazzoo.environment.rules.read_config_value import NO_DEFAULT, read_config_value
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.functions.models.parameter import Parameter

# The ⚙️ functions. load_env and load_config are called as statements and yield
# no value; get_config yields a value. Their parameters are checked at load time
# like those of any other call.
BUILTIN_PARAMETERS: T.Dict[str, T.List[Parameter]] = {
    "load_env": [
        Parameter(name="path", default=None),
        Parameter(name="required", default="true"),
    ],
    "load_config": [
        Parameter(name="path", default=None),
        Parameter(name="required", default="true"),
    ],
    "get_config": [
        Parameter(name="path", default=None),
        # Only an omitted default makes a missing path an error, so the call reads
        # whether the argument is there, not this default.
        Parameter(name="default", default="null"),
    ],
}


def _load_env(
    arguments: T.Dict[str, T.Any], filename: T.Optional[str], line: T.Optional[int]
) -> str:
    load_env(
        render_value(arguments["path"]),
        is_required=is_truthy(arguments.get("required", True)),
        filename=filename,
        line=line,
    )
    return ""


def _load_config(
    arguments: T.Dict[str, T.Any], filename: T.Optional[str], line: T.Optional[int]
) -> str:
    load_config(
        render_value(arguments["path"]),
        is_required=is_truthy(arguments.get("required", True)),
        filename=filename,
        line=line,
    )
    return ""


def _get_config(
    arguments: T.Dict[str, T.Any], filename: T.Optional[str], line: T.Optional[int]
) -> T.Any:
    return read_config_value(
        render_value(arguments["path"]),
        default=arguments.get("default", NO_DEFAULT),
        filename=filename,
        line=line,
    )


_BUILTIN_FUNCTIONS: T.Dict[str, T.Callable[..., T.Any]] = {
    "load_env": _load_env,
    "load_config": _load_config,
    "get_config": _get_config,
}


def is_builtin_function(name: str) -> bool:
    return name in _BUILTIN_FUNCTIONS


def call_builtin_function(
    name: str,
    arguments: T.Dict[str, T.Any],
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> T.Any:
    return _BUILTIN_FUNCTIONS[name](arguments, filename, line)
