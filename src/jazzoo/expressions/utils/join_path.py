def join_path(left: str, right: str) -> str:
    """Join two path segments as a pure string join.

    `..`, symlinks and redundant separators are left untouched - only ⚙️.abs
    canonicalizes.
    """
    if not left:
        return right
    if not right:
        return left
    if left.endswith("/"):
        return left + right
    return left + "/" + right
