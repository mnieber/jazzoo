import os
import typing as T

from ..models.loaded_config import LoadedConfig
from ..settings import CONFIG_FILES_ENV_VAR, INCLUDES_KEY, JAZZOO_KEY
from ..utils.merge_config import merge_config
from .read_config_layers import read_config_layers

# One config is cached: the one for the current value of JAZZOO_CONFIG_FILES
_loaded_config: T.Optional[LoadedConfig] = None


def get_loaded_config() -> LoadedConfig:
    global _loaded_config

    config_files = os.environ.get(CONFIG_FILES_ENV_VAR, "")
    if _loaded_config is None or _loaded_config.config_files != config_files:
        _loaded_config = _load_config(config_files)
    return _loaded_config


def _load_config(config_files: str) -> LoadedConfig:
    # Include paths and values read the same copy of the environment
    environ = dict(os.environ)

    # Every file is read once, at its first position in the merge order
    seen: T.Set[str] = set()
    file_trees: T.List[T.Tuple[str, T.Dict[T.Any, T.Any]]] = []
    includes: T.List[str] = []
    has_includes = False

    for config_file in config_files.split(os.pathsep):
        if not config_file:
            continue
        config_file = os.path.abspath(config_file)
        if config_file in seen:
            continue
        layers, file_has_includes = read_config_layers(config_file, environ, seen)
        file_trees.extend(layers)
        # The layers of the file: all files that were read, except the file itself
        includes.extend(path for path, _ in layers[:-1])
        has_includes = has_includes or file_has_includes

    tree: T.Dict[T.Any, T.Any] = {}
    for _, file_tree in file_trees:
        tree = merge_config(tree, file_tree)

    if has_includes:
        tree = merge_config(
            tree, {JAZZOO_KEY: {INCLUDES_KEY: [_escape(path) for path in includes]}}
        )

    return LoadedConfig(
        config_files=config_files,
        file_trees=file_trees,
        tree=tree,
        environ=environ,
    )


def _escape(path: str) -> str:
    # The paths are final, so the expansion of values must leave them unchanged
    return path.replace("${", "$${")
