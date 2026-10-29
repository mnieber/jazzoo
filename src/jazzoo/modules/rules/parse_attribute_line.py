import re
import typing as T

from jazzoo.errors import ParseError
from jazzoo.settings import KNOWN_ATTRIBUTES

# `[name, ...]`: the shell needs a space after `[` and `[[`, so a shell test such as
# `[ -d / ]` is never an attribute line.
_ATTRIBUTE_LINE_RE = re.compile(r"^\[[A-Za-z_].*\]$")

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def is_attribute_line(trimmed: str) -> bool:
    return bool(_ATTRIBUTE_LINE_RE.match(trimmed))


def parse_attribute_line(trimmed: str, filename: str, line: int) -> T.List[str]:
    names: T.List[str] = []
    for item in trimmed[1:-1].split(","):
        name = item.strip()
        if not _NAME_RE.match(name):
            raise ParseError(
                f"malformed attribute list: {trimmed}", filename=filename, line=line
            )
        if name not in KNOWN_ATTRIBUTES:
            raise ParseError(
                f"unknown attribute: [{name}]", filename=filename, line=line
            )
        names.append(name)
    return names
