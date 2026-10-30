import typing as T


class Expression:
    """The content of a ${...} in a string."""

    def __init__(self, content: str):
        self.content = content


class UnclosedExpressionError(Exception):
    pass


def split_expressions(text: str) -> T.List[T.Union[str, Expression]]:
    """Split text into literal parts and ${...} expressions. $${ yields a literal ${."""
    parts: T.List[T.Union[str, Expression]] = []
    literal: T.List[str] = []
    index = 0

    while index < len(text):
        if text.startswith("$${", index):
            literal.append("${")
            index += 3
        elif text.startswith("${", index):
            end = _find_closing_brace(text, index + 2)
            if end is None:
                raise UnclosedExpressionError(text)
            if literal:
                parts.append("".join(literal))
                literal = []
            parts.append(Expression(text[index + 2 : end]))
            index = end + 1
        else:
            literal.append(text[index])
            index += 1

    if literal:
        parts.append("".join(literal))
    return parts


def _find_closing_brace(text: str, start: int) -> T.Optional[int]:
    depth = 1
    index = start
    while index < len(text):
        if text.startswith("$${", index):
            index += 3
        elif text.startswith("${", index):
            depth += 1
            index += 2
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
            index += 1
        else:
            index += 1
    return None
