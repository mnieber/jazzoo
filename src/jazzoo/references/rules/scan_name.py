import typing as T

# Hyphens and underscores are part of a name; a dot continues into the next part.
_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

# A dot only continues the name when what follows could begin a segment. A hyphen
# cannot start one, so `🐆.name.-b` ends at `name` and the rest is literal text -
# the same reasoning that stops a name ending on a hyphen.
_SEGMENT_START_CHARS = _NAME_CHARS - set("-")


def scan_name(text: str, pos: int) -> T.Tuple[T.List[str], int]:
    """Read the dotted name after a sigil. A `\\` terminates the name.

    A reference is always `<sigil>.<name>`, so the leading dot is required; without
    it the sigil is just an emoji in the text.

    A dot continues the name into a further segment: a field of a structured value
    (`🐆.config.name`), an array index (`🐆.hosts.0`), a built-in's sub-name
    (`⚙️.module.basename`), or a module alias before a function (`🐭.docker.build`).
    A literal dot after a reference therefore needs the `\\` terminator.
    """
    if pos >= len(text) or text[pos] != ".":
        return [], pos
    pos += 1

    parts: T.List[str] = []
    current = ""
    while pos < len(text):
        char = text[pos]
        if char in _NAME_CHARS:
            current += char
            pos += 1
        elif (
            char == "."
            and current
            and pos + 1 < len(text)
            and text[pos + 1] in _SEGMENT_START_CHARS
        ):
            parts.append(current)
            current = ""
            pos += 1
        else:
            break
    if current:
        parts.append(current)

    # A name may contain hyphens but not end on one: in `🐆.target-🐆.mode` the
    # trailing hyphen is separator text, not part of `target`. Underscores are left
    # alone, since a name may legitimately end in one.
    if parts and parts[-1].endswith("-"):
        trimmed = parts[-1].rstrip("-")
        pos -= len(parts[-1]) - len(trimmed)
        if trimmed:
            parts[-1] = trimmed
        else:
            parts.pop()

    return parts, pos
