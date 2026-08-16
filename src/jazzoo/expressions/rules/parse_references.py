import typing as T

from dataclassy import dataclass

from jazzoo.enums import Sigil
from jazzoo.expressions.models.reference import Reference

# Longest first, so ⚙️ (which carries a variation selector) is tried before its
# bare codepoint form.
_SIGILS = sorted(
    [s.value for s in Sigil] + ["⚙"], key=len, reverse=True
)
_SIGIL_BY_TEXT = {s.value: s for s in Sigil}
_SIGIL_BY_TEXT["⚙"] = Sigil.SYSTEM

# Hyphens and underscores are part of a name; a dot continues into the next part.
_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

# Characters that end an unquoted default value, besides whitespace.
_BARE_DEFAULT_TERMINATORS = set("\"'[]{}()")


@dataclass
class ReferenceMatch:
    reference: Reference
    start: int
    end: int
    # True when the sigil was escaped with a backslash: the text is emitted
    # literally (minus the backslash) rather than substituted.
    is_escaped: bool = False
    # Set when a `(` follows the name directly, making this a call rather than a
    # plain reference. Holds the whole `🐭.name(args)` text.
    call_text: T.Optional[str] = None


def _read_call_arguments(text: str, pos: int) -> T.Optional[int]:
    """Return the index just past the `)` matching the `(` at `pos`.

    Nesting and quotes are tracked so a `)` inside an argument value does not end
    the call. This reads jazzoo's own argument syntax, never the interpreter's.
    """
    depth = 0
    quote: T.Optional[str] = None
    while pos < len(text):
        char = text[pos]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return pos + 1
        pos += 1
    return None


def _match_sigil(text: str, pos: int) -> T.Optional[str]:
    for sigil in _SIGILS:
        if text.startswith(sigil, pos):
            return sigil
    return None


def _scan_name(
    text: str, pos: int, allow_dots: bool = False
) -> T.Tuple[T.List[str], int]:
    """Read the name after a sigil. A `\\` terminates the name.

    A reference is always `<sigil>.<name>`, so the leading dot is required; without
    it the sigil is just an emoji in the text.

    Names themselves are letters, numbers, hyphens and underscores - never dots. A
    further dot is therefore literal text, which is what makes `🐭.bare.com` the
    variable `bare` followed by ".com". `allow_dots` is set only for ⚙️, whose
    built-in names really are dotted (`⚙️.module.basename`), and for a call path,
    where the dots separate module aliases (`🐭.docker.build`).
    """
    if pos >= len(text) or text[pos] != ".":
        return [], pos
    pos += 1

    if not allow_dots:
        start = pos
        while pos < len(text) and text[pos] in _NAME_CHARS:
            pos += 1
        name = text[start:pos]
        # A name may contain hyphens but not end on one: in `🐆.target-🐆.mode`
        # the trailing hyphen is separator text.
        trimmed = name.rstrip("-")
        pos -= len(name) - len(trimmed)
        return ([trimmed] if trimmed else []), pos

    parts: T.List[str] = []
    current = ""
    while pos < len(text):
        char = text[pos]
        if char in _NAME_CHARS:
            current += char
            pos += 1
        elif char == "." and current and pos + 1 < len(text) and text[pos + 1] in _NAME_CHARS:
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


def _scan_markers(text: str, pos: int) -> T.Tuple[bool, T.Optional[str], int]:
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


def parse_references(
    text: str, filename: T.Optional[str] = None, line: T.Optional[int] = None
) -> T.List[ReferenceMatch]:
    """Find every jazzoo reference in a line, bare or braced.

    Braced references (`{{ ... }}`) are reported spanning the whole brace group, so
    substitution replaces the braces too. Braces containing no sigil are not
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
                sigil = _match_sigil(probe, 0)
                if sigil is not None:
                    offset = inner_start + inner.index(stripped) + (1 if escaped else 0)
                    parts, after = _scan_name(
                        text,
                        offset + len(sigil),
                        allow_dots=_SIGIL_BY_TEXT[sigil] is Sigil.SYSTEM,
                    )
                    if parts:
                        is_optional, default, after = _scan_markers(text, after)
                        matches.append(
                            ReferenceMatch(
                                reference=Reference(
                                    sigil=_SIGIL_BY_TEXT[sigil],
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
        sigil = _match_sigil(text, probe_pos)
        if sigil is not None:
            is_system = _SIGIL_BY_TEXT[sigil] is Sigil.SYSTEM
            name_start = probe_pos + len(sigil)

            # A call path may be dotted (`🐭.docker.build`), so scan the dotted form
            # first and keep it only if a `(` really follows.
            dotted_parts, dotted_after = _scan_name(text, name_start, allow_dots=True)
            if (
                dotted_parts
                and not escaped
                and dotted_after < len(text)
                and text[dotted_after] == "("
            ):
                call_end = _read_call_arguments(text, dotted_after)
                if call_end is not None:
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=_SIGIL_BY_TEXT[sigil],
                                parts=dotted_parts,
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

            parts, after = _scan_name(text, name_start, allow_dots=is_system)

            if parts:
                if escaped:
                    # The name still terminates at a `\`, but nothing is resolved.
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=_SIGIL_BY_TEXT[sigil],
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
                        is_optional, default, after = _scan_markers(text, after)
                    matches.append(
                        ReferenceMatch(
                            reference=Reference(
                                sigil=_SIGIL_BY_TEXT[sigil],
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
