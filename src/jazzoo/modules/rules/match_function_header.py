import typing as T

from jazzoo.modules.models.function_header import FunctionHeader
from jazzoo.utils.find_closing_paren import find_closing_paren


def match_function_header(
    name_re: T.Pattern[str], text: str
) -> T.Optional[FunctionHeader]:
    """Match `<name>(<params>):<rest>`.

    `name_re` matches up to and including the opening parenthesis, and has a `name`
    group. A default may be a call or a string with a parenthesis, so the closing
    parenthesis is found by counting rather than by a regex.
    """
    match = name_re.match(text)
    if match is None:
        return None
    end = find_closing_paren(text, match.end())
    if end is None:
        return None
    rest = text[end + 1 :].lstrip()
    if not rest.startswith(":"):
        return None
    return FunctionHeader(
        name=match.group("name"), params=text[match.end() : end], rest=rest[1:]
    )
