import typing as T


def join_continuations(
    entries: T.List[T.Tuple[int, str]], index: int
) -> T.Tuple[T.Tuple[int, str], int]:
    """Fold the backslash-continued line at `index` with the lines that follow it.

    Returns the joined entry, which keeps the first line's number, and the index of
    the first entry after it.
    """
    start_line, buffer = entries[index]
    index += 1
    while buffer.rstrip().endswith("\\") and index < len(entries):
        buffer = buffer.rstrip()[:-1].rstrip() + " " + entries[index][1].strip()
        index += 1
    if buffer.rstrip().endswith("\\"):
        buffer = buffer.rstrip()[:-1].rstrip()
    return (start_line, buffer), index
