import typing as T

from jazzoo.references.models.reference import Reference
from jazzoo.references.models.reference_match import ReferenceMatch
from jazzoo.references.rules.contains_sigil import contains_sigil
from jazzoo.references.rules.match_sigil import SIGIL_BY_TEXT, match_sigil
from jazzoo.references.rules.read_call_arguments import read_call_arguments
from jazzoo.references.rules.scan_markers import scan_markers
from jazzoo.references.rules.scan_name import scan_name


def _expression_match(
    expression_text: str,
    start: int,
    end: int,
    filename: T.Optional[str],
    line: T.Optional[int],
) -> ReferenceMatch:
    first = next(
        match
        for match in parse_references(expression_text, filename, line)
        if match.reference is not None
    )
    return ReferenceMatch(
        reference=first.reference,
        start=start,
        end=end,
        expression_text=expression_text,
    )


def parse_references(
    text: str, filename: T.Optional[str] = None, line: T.Optional[int] = None
) -> T.List[ReferenceMatch]:
    """Find every jazzoo reference in a line, bare or braced.

    Braced references (`{{ ... }}`) are reported spanning the whole brace group, so
    substitution replaces the braces too. A brace group that holds more than one
    reference is reported as an expression. Braces containing no sigil are not
    references and are left alone.
    """
    matches: T.List[ReferenceMatch] = []
    pos = 0
    while pos < len(text):
        # A braced group is a reference only if a sigil appears inside it.
        if text.startswith("{{", pos):
            close = text.find("}}", pos + 2)
            if close != -1:
                inner_start = pos + 2
                inner = text[inner_start:close]
                stripped = inner.strip()
                escaped = stripped.startswith("\\")
                probe = stripped[1:] if escaped else stripped
                sigil = match_sigil(probe, 0)
                if sigil is None and not escaped and contains_sigil(stripped):
                    # A sigil that is not at the start, as in `{{ not 🐆.x }}`.
                    matches.append(
                        _expression_match(stripped, pos, close + 2, filename, line)
                    )
                    pos = close + 2
                    continue
                if sigil is not None:
                    offset = inner_start + inner.index(stripped) + (1 if escaped else 0)
                    parts, after = scan_name(text, offset + len(sigil))
                    if parts:
                        is_optional, default, after = scan_markers(text, after)
                        if not escaped and text[after:close].strip():
                            # More follows the reference, so the group is an
                            # expression rather than a reference.
                            matches.append(
                                _expression_match(
                                    stripped, pos, close + 2, filename, line
                                )
                            )
                            pos = close + 2
                            continue
                        matches.append(
                            ReferenceMatch(
                                reference=Reference(
                                    sigil=SIGIL_BY_TEXT[sigil],
                                    parts=parts,
                                    is_optional=is_optional,
                                    default=default,
                                    filename=filename,
                                    line=line,
                                ),
                                start=pos,
                                end=close + 2,
                                is_escaped=escaped,
                            )
                        )
                        pos = close + 2
                        continue

        escaped = text[pos] == "\\"
        probe_pos = pos + 1 if escaped else pos
        sigil = match_sigil(text, probe_pos)
        if sigil is not None:
            name_start = probe_pos + len(sigil)

            parts, after = scan_name(text, name_start)
            if parts and not escaped and after < len(text) and text[after] == "(":
                call_end = read_call_arguments(text, after)
                if call_end is not None:
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=SIGIL_BY_TEXT[sigil],
                                parts=parts,
                                filename=filename,
                                line=line,
                            ),
                            start=pos,
                            end=call_end,
                            call_text=text[pos:call_end],
                        )
                    )
                    pos = call_end
                    continue

            if parts:
                if escaped:
                    # The name still terminates at a `\`, but nothing is resolved.
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=SIGIL_BY_TEXT[sigil],
                                parts=parts,
                                filename=filename,
                                line=line,
                            ),
                            start=pos,
                            end=after,
                            is_escaped=True,
                        )
                    )
                else:
                    if after < len(text) and text[after] == "\\":
                        # A `\` terminates the name and is consumed, so the text
                        # after it stays literal - and a marker after it is not a
                        # marker.
                        is_optional, default, after = False, None, after + 1
                    else:
                        is_optional, default, after = scan_markers(text, after)
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=SIGIL_BY_TEXT[sigil],
                                parts=parts,
                                is_optional=is_optional,
                                default=default,
                                filename=filename,
                                line=line,
                            ),
                            start=pos,
                            end=after,
                        )
                    )
                pos = after
                continue
        pos += 1
    return matches
