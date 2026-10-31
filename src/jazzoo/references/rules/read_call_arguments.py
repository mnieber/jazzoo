import typing as T


def read_call_arguments(text: str, pos: int) -> T.Optional[int]:
    """Return the index just past the `)` matching the `(` at `pos`.

    Nesting and quotes are tracked so a `)` inside an argument value does not end
    the call. This reads jazzoo's own argument syntax, never the interpreter's.
    """
    depth = 0
    quote: T.Optional[str] = None
    while pos < len(text):
        char = text[pos]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return pos + 1
        pos += 1
    return None
