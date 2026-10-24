import typing as T

from jazzoo.environment.actions.load_env import load_env
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.functions.models.parameter import Parameter

# The ⚙️ functions, which are called as statements and yield no value. Their
# parameters are checked at load time like those of any other call.
BUILTIN_PARAMETERS: T.Dict[str, T.List[Parameter]] = {
    "loadenv": [
        Parameter(name="path", default=None),
        Parameter(name="required", default="true"),
    ],
}


def _loadenv(
    arguments: T.Dict[str, T.Any], filename: T.Optional[str], line: T.Optional[int]
) -> None:
    load_env(
        render_value(arguments["path"]),
        is_required=is_truthy(arguments.get("required", True)),
        filename=filename,
        line=line,
    )


_BUILTIN_FUNCTIONS: T.Dict[str, T.Callable[..., None]] = {
    "loadenv": _loadenv,
}


def is_builtin_function(name: str) -> bool:
    return name in _BUILTIN_FUNCTIONS


def call_builtin_function(
    name: str,
    arguments: T.Dict[str, T.Any],
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> str:
    _BUILTIN_FUNCTIONS[name](arguments, filename, line)
    return ""
