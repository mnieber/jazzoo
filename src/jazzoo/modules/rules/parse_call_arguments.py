import typing as T

from jazzoo.functions.models.call_site import Argument
from jazzoo.utils.split_top_level import split_top_level


def parse_call_arguments(text: str, filename: str, line: int) -> T.List[Argument]:
    arguments: T.List[Argument] = []
    for chunk in split_top_level(text, ","):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, sep, value = chunk.partition("=")
        if not sep:
            # Positional - parsed so validation can report it, per design section 12.
            arguments.append(Argument(name=None, value=chunk))
        else:
            arguments.append(Argument(name=name.strip(), value=value.strip()))
    return arguments
