import typing as T

# Characters that end an unquoted default value, besides whitespace.
_BARE_DEFAULT_TERMINATORS = set("\"'[]{}()")


def scan_markers(text: str, pos: int) -> T.Tuple[bool, T.Optional[str], int]:
    """Read the optional `?` and `:-<default>` markers following a name."""
    is_optional = False
    if pos < len(text) and text[pos] == "?":
        is_optional = True
        pos += 1

    default = None
    if text.startswith(":-", pos):
        pos += 2
        if pos < len(text) and text[pos] == '"':
            end = text.find('"', pos + 1)
            if end != -1:
                default = text[pos + 1 : end]
                pos = end + 1
                return is_optional, default, pos
        # A bare default ends at the first whitespace, or at a character that
        # cannot continue a bare word. References sit inside quoted shell strings
        # and braced groups, so a quote, bracket or brace ends it too - otherwise
        # `"[⚙️.env.X?:-hello]"` would take the default as `hello]"`.
        start = pos
        while (
            pos < len(text)
            and not text[pos].isspace()
            and text[pos] not in _BARE_DEFAULT_TERMINATORS
        ):
            pos += 1
        default = text[start:pos]
    return is_optional, default, pos
