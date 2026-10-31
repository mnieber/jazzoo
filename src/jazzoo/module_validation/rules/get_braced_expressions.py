import typing as T


def get_braced_expressions(
    text: str, filename: T.Optional[str], line: T.Optional[int]
) -> T.List[str]:
    """The expressions written between braces in a body line."""
    from jazzoo.expressions.rules.parse_references import parse_references

    return [
        match.expression_text
        for match in parse_references(text, filename=filename, line=line)
        if match.expression_text is not None
    ]
