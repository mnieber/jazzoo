import typing as T


def find_closing_paren(text: str, start: int) -> T.Optional[int]:
    """The index of the `)` that closes the parenthesis opened just before `start`.

    Brackets inside quotes are ignored. None when the parenthesis is not closed.
    """
    depth = 0
    quote: T.Optional[str] = None
    for index in range(start, len(text)):
        char = text[index]
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            if depth == 0:
                return index if char == ")" else None
            depth -= 1
    return None
