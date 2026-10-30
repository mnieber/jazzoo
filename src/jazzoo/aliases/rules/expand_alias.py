import shlex
import typing as T

from jazzoo.aliases.errors import AliasError
from jazzoo.aliases.rules.get_alias_config_file import get_alias_config_file
from jazzoo.aliases.rules.read_aliases import read_aliases

# The options of jaz that an expansion may contain
_ALLOWED_OPTIONS = ("--confirm", "--trace")


def expand_alias(name: str) -> T.Optional[T.List[str]]:
    config_file = get_alias_config_file()
    expansion = read_aliases(config_file).get(name)
    if expansion is None:
        return None

    try:
        tokens = shlex.split(expansion)
    except ValueError as error:
        raise AliasError(
            f'alias "{name}" has an invalid expansion: {error}', filename=config_file
        )
    if not tokens:
        raise AliasError(f'alias "{name}" has an empty expansion', filename=config_file)

    # Only the options that change how the target runs are allowed
    for token in tokens:
        option = token.partition("=")[0]
        if option.startswith("-") and option not in _ALLOWED_OPTIONS:
            raise AliasError(
                f'alias "{name}" may not use the option {option}',
                filename=config_file,
            )
    if all(token in _ALLOWED_OPTIONS for token in tokens):
        raise AliasError(f'alias "{name}" names no target', filename=config_file)

    return tokens
