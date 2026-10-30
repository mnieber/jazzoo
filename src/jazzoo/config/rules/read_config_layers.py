import os
import typing as T

from ..errors import ConfigFileError
from ..settings import INCLUDES_KEY, JAZZOO_KEY
from .expand_include_path import expand_include_path
from .read_config_file import read_config_file

FileTree = T.Tuple[str, T.Dict[T.Any, T.Any]]


def read_config_layers(
    config_file: str, environ: T.Dict[str, str], seen: T.Set[str]
) -> T.Tuple[T.List[FileTree], bool]:
    """Read config_file and, recursively, its includes.

    Return the files in merge order (a file's includes before the file, depth-first)
    and whether config_file has an includes list. A file in seen is skipped; every
    file that is read is added to seen before its includes are read, so that a cycle
    ends.
    """
    seen.add(config_file)
    tree = read_config_file(config_file)
    includes = _pop_includes(config_file, tree)

    result: T.List[FileTree] = []
    for include in includes or []:
        path = expand_include_path(include, config_file, environ)
        if path in seen:
            continue
        if not os.path.isfile(path):
            raise ConfigFileError(f"{config_file}: include not found: {path}")
        result.extend(read_config_layers(path, environ, seen)[0])

    result.append((config_file, tree))
    return result, includes is not None


def _pop_includes(
    config_file: str, tree: T.Dict[T.Any, T.Any]
) -> T.Optional[T.List[str]]:
    """Remove the includes list from the tree and return it; None if there is none."""
    jazzoo = tree.get(JAZZOO_KEY)
    if jazzoo is None:
        return None
    if not isinstance(jazzoo, dict):
        raise ConfigFileError(f"{config_file}: /{JAZZOO_KEY} must be a mapping")

    includes = jazzoo.pop(INCLUDES_KEY, None)
    if includes is None:
        return None
    if not isinstance(includes, list) or not all(
        isinstance(include, str) for include in includes
    ):
        raise ConfigFileError(
            f"{config_file}: /{JAZZOO_KEY}/{INCLUDES_KEY} must be a list of strings"
        )
    return includes
