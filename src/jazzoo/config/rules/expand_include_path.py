import os
import typing as T

from ..errors import ConfigFileError
from ..utils.split_expressions import (
    Expression,
    UnclosedExpressionError,
    split_expressions,
)


def expand_include_path(
    include: str, including_file: str, environ: T.Dict[str, str]
) -> str:
    """Return the absolute path of an include of including_file.

    Environment variables and a leading ~ are expanded; a reference to a config
    value is not allowed, because the config is not built yet. A relative path is
    resolved against the dir of including_file.
    """
    path = _expand(include, include, including_file, environ)

    if path == "~" or path.startswith("~/"):
        home = environ.get("HOME")
        if not home:
            raise ConfigFileError(
                f"{including_file}: cannot expand ~ in include, HOME is not set: "
                f"{include}"
            )
        path = home + path[1:]

    return os.path.normpath(os.path.join(os.path.dirname(including_file), path))


def _expand(
    text: str, include: str, including_file: str, environ: T.Dict[str, str]
) -> str:
    try:
        parts = split_expressions(text)
    except UnclosedExpressionError:
        raise ConfigFileError(f"{including_file}: unclosed '${{' in include: {include}")

    result = []
    for part in parts:
        if isinstance(part, Expression):
            result.append(_evaluate(part.content, include, including_file, environ))
        else:
            result.append(part)
    return "".join(result)


def _evaluate(
    content: str, include: str, including_file: str, environ: T.Dict[str, str]
) -> str:
    # Nested expressions are expanded first
    expression = _expand(content, include, including_file, environ)

    if expression.startswith("/"):
        raise ConfigFileError(
            f"{including_file}: an include cannot reference a config value: "
            f"{include}"
        )

    name, has_default, default = expression.partition(":-")
    value = environ.get(name)
    if has_default and not value:
        return default
    if value is None:
        raise ConfigFileError(
            f"{including_file}: environment variable is not set: {name} "
            f"(in include: {include})"
        )
    return value
