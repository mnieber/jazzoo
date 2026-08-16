import typing as T

from jazzoo.expressions.rules.parse_references import ReferenceMatch, parse_references


def substitute_references(
    text: str,
    resolve: T.Callable[[object], str],
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> str:
    """Replace every jazzoo reference in `text` with its resolved value.

    Substitution is textual and values are not escaped - see design section 4.
    `resolve` takes a Reference and returns its string value.
    """
    matches: T.List[ReferenceMatch] = parse_references(text, filename=filename, line=line)
    if not matches:
        return text

    out: T.List[str] = []
    cursor = 0
    for match in matches:
        out.append(text[cursor : match.start])
        if match.is_escaped:
            # Emit the reference literally, with the escaping backslash removed.
            out.append(text[match.start : match.end].replace("\\", "", 1))
        else:
            out.append(resolve(match.reference))
        cursor = match.end
    out.append(text[cursor:])
    return "".join(out)
