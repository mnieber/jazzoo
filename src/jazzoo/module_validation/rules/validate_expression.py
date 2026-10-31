import typing as T

from jazzoo.errors import ParseError


def validate_expression(
    source: str, filename: T.Optional[str], line: T.Optional[int]
) -> None:
    """Parse an expression so its parse-time errors surface at load time."""
    from jazzoo.expressions.rules.parse_expression import parse_expression

    try:
        parse_expression(source)
    except ParseError as error:
        raise ParseError(error.message, filename=filename, line=line) from None
