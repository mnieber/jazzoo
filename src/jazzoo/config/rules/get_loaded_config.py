import os
import typing as T

from ..models.loaded_config import LoadedConfig
from ..settings import CONFIG_FILES_ENV_VAR
from ..utils.merge_config import merge_config
from .read_config_file import read_config_file

# One config is cached: the one for the current value of JAZZOO_CONFIG_FILES
_loaded_config: T.Optional[LoadedConfig] = None


def get_loaded_config() -> LoadedConfig:
    global _loaded_config

    config_files = os.environ.get(CONFIG_FILES_ENV_VAR, "")
    if _loaded_config is None or _loaded_config.config_files != config_files:
        _loaded_config = _load_config(config_files)
    return _loaded_config


def _load_config(config_files: str) -> LoadedConfig:
    file_trees = [
        (config_file, read_config_file(config_file))
        for config_file in config_files.split(os.pathsep)
        if config_file
    ]

    tree: T.Dict[T.Any, T.Any] = {}
    for _, file_tree in file_trees:
        tree = merge_config(tree, file_tree)

    return LoadedConfig(
        config_files=config_files,
        file_trees=file_trees,
        tree=tree,
        environ=dict(os.environ),
    )
