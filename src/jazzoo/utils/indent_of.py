def indent_of(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" "))
