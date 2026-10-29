import typing as T

# A string is falsy if its lowercased form is one of these; everything else is truthy.
FALSY_VALUES: T.FrozenSet[str] = frozenset(["0", "false", "no", ""])

# Tried in order when no --file is given.
DEFAULT_FILENAMES: T.Tuple[str, ...] = ("jazzoo", "jazzoo.jaz")

# Used for jazzoo-mode lines and for a bare `#!` returning to jazzoo mode.
DEFAULT_SHEBANG = "#!/usr/bin/env bash"

# The attributes that may precede a function definition.
KNOWN_ATTRIBUTES: T.FrozenSet[str] = frozenset(["private", "interactive"])
