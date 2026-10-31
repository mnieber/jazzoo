import os
import typing as T

# A string is falsy if its lowercased form is one of these; everything else is truthy.
FALSY_VALUES: T.FrozenSet[str] = frozenset(["0", "false", "no", ""])

# Tried in order when no --file is given.
DEFAULT_FILENAMES: T.Tuple[str, ...] = ("jazzoo", "jazzoo.jaz")

# Used for jazzoo-mode lines and for a bare `#!` returning to jazzoo mode.
DEFAULT_SHEBANG = "#!/usr/bin/env bash"

# The attributes that may precede a function definition.
KNOWN_ATTRIBUTES: T.FrozenSet[str] = frozenset(["private", "interactive"])


# The oldest python that can run jazzoo; the same as requires-python in pyproject.toml.
# zoo checks it before it links jazzoo into a venv.
MIN_PYTHON_VERSION: T.Tuple[int, int] = (3, 10)


# The zoo registry, and where the zoo-<name> links go. These are functions, because
# they depend on environment variables that may change after jazzoo is imported.
def get_config_home() -> str:
    return os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")


def get_zoo_config_dir() -> str:
    return os.path.join(get_config_home(), "jazzoo")


def get_zoo_bin_dir() -> str:
    return os.path.expanduser("~/.local/bin")


def get_path_dirs() -> T.List[str]:
    return os.environ.get("PATH", "").split(os.pathsep)


def get_shell() -> str:
    return os.environ.get("SHELL", "")


def get_active_zoo_env() -> T.Optional[str]:
    return os.environ.get("JAZZOO_ENV")
