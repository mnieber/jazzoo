import typing as T


def split_top_level(text: str, separator: str) -> T.List[str]:
    """Split on `separator`, ignoring occurrences inside quotes or brackets."""
    parts: T.List[str] = []
    depth = 0
    quote: T.Optional[str] = None
    current = ""
    for char in text:
        if quote is not None:
            current += char
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current += char
            continue
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        if char == separator and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    if current.strip():
        parts.append(current)
    return parts
