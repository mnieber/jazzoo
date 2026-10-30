import configparser
import os
import re
import typing as T

from jazzoo.aliases.errors import AliasError

# A target path: names separated by dots
_ALIAS_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*(\.[A-Za-z_][A-Za-z0-9_-]*)*$")


def read_aliases(config_file: str) -> T.Dict[str, str]:
    if not os.path.exists(config_file):
        return {}

    # No section is special: a section header cannot contain a newline, so the
    # default section of configparser never occurs
    parser = configparser.ConfigParser(
        interpolation=None, strict=True, default_section="\n"
    )
    # Alias names are case-sensitive
    parser.optionxform = str  # type: ignore[assignment]
    try:
        with open(config_file, encoding="utf-8") as f:
            parser.read_file(f, source=config_file)
    except (OSError, UnicodeDecodeError, configparser.Error) as error:
        raise AliasError(f"invalid config file: {error}", filename=config_file)

    if not parser.has_section("alias"):
        return {}

    aliases = dict(parser.items("alias"))
    for name in aliases:
        if not _ALIAS_NAME_RE.match(name):
            raise AliasError(f'invalid alias name "{name}"', filename=config_file)
    return aliases
