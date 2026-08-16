def strip_one_newline(text: str) -> str:
    """Remove a single trailing newline, if there is one."""
    if text.endswith("\n"):
        return text[:-1]
    return text
