from jazzoo.utils.dataclass import dataclass


@dataclass
class ZooEnv:
    name: str
    # The targets of the env run in this directory, which has the root jazzoo file
    root_dir: str
    venv_dir: str
