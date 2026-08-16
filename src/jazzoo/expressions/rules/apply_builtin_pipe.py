import os
import typing as T

from jazzoo.expressions.utils.shell_quote import shell_quote

# The ⚙️ pipe operators. Each takes the piped value and returns a new one.
_BUILTINS: T.Dict[str, T.Callable[[str], str]] = {
    "abs": lambda value: os.path.abspath(value),
    "basename": lambda value: os.path.basename(value),
    "dirname": lambda value: os.path.dirname(value),
    "ext": lambda value: os.path.splitext(value)[1],
    "stem": lambda value: os.path.splitext(value)[0],
    "sh-quote": shell_quote,
}


def is_builtin_pipe(name: str) -> bool:
    return name in _BUILTINS


def apply_builtin_pipe(name: str, value: str) -> str:
    return _BUILTINS[name](value)
