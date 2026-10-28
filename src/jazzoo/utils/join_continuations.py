import typing as T


def join_continuations(
    lines: T.List[str],
) -> T.List[T.Tuple[int, str]]:
    """Fold backslash-continued lines into one, keeping the first line's number."""
    joined: T.List[T.Tuple[int, str]] = []
    buffer = ""
    start_line = 0
    for index, raw in enumerate(lines, start=1):
        stripped = raw.rstrip("\n")
        if buffer:
            buffer = buffer + " " + stripped.strip()
        else:
            start_line = index
            buffer = stripped
        if buffer.rstrip().endswith("\\"):
            buffer = buffer.rstrip()[:-1].rstrip()
            continue
        joined.append((start_line, buffer))
        buffer = ""
    if buffer:
        joined.append((start_line, buffer))
    return joined
