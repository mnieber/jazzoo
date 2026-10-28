import typing as T

from ..utils.dataclass import dataclass


@dataclass
class LoadedConfig:
    # The value of JAZZOO_CONFIG_FILES that this config was built from
    config_files: str
    # The raw tree of each config file, in list order
    file_trees: T.List[T.Tuple[str, T.Dict[T.Any, T.Any]]]
    # The merged raw tree
    tree: T.Dict[T.Any, T.Any]
    # The copy of the environment that ${NAME} reads from
    environ: T.Dict[str, str]
    # The expanded value of each string in the tree, by its path
    expanded: T.Dict[T.Tuple[T.Any, ...], T.Any] = {}
