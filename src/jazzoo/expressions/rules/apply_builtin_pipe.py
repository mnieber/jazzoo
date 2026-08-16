import json
import os
import typing as T

from jazzoo.errors import ExecutionError
from jazzoo.expressions.rules.is_truthy import is_truthy
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.expressions.utils.shell_quote import shell_quote


def _parse(value: T.Any) -> T.Any:
    text = render_value(value)
    try:
        return json.loads(text)
    except ValueError as error:
        raise ExecutionError(f"not valid JSON: {error}") from error


def _is_empty(value: T.Any) -> bool:
    """Whether the value is nothing at all, which is not the same as falsy: a
    command that printed "no" printed something."""
    if value is None:
        return True
    if isinstance(value, (str, list, dict)):
        return len(value) == 0
    return False


# The ⚙️ pipe operators. Each takes the piped value and returns a new one. The path
# operators take text, so they render first; the value operators do not.
_PATH_BUILTINS: T.Dict[str, T.Callable[[str], T.Any]] = {
    "abs": lambda value: os.path.abspath(value),
    "basename": lambda value: os.path.basename(value),
    "dirname": lambda value: os.path.dirname(value),
    "ext": lambda value: os.path.splitext(value)[1],
    "stem": lambda value: os.path.splitext(value)[0],
    "sh-quote": shell_quote,
}

_VALUE_BUILTINS: T.Dict[str, T.Callable[[T.Any], T.Any]] = {
    "parse": _parse,
    "json": lambda value: json.dumps(value, separators=(",", ":")),
    "empty": _is_empty,
    "bool": is_truthy,
}


def is_builtin_pipe(name: str) -> bool:
    return name in _PATH_BUILTINS or name in _VALUE_BUILTINS


def apply_builtin_pipe(name: str, value: T.Any) -> T.Any:
    if name in _VALUE_BUILTINS:
        return _VALUE_BUILTINS[name](value)
    return _PATH_BUILTINS[name](render_value(value))
