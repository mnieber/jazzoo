import typing as T

from dataclassy import dataclass

from jazzoo.errors import ParseError

_SIGIL_STARTS = ("🐐", "🐭", "🐆", "⚙️", "⚙")

_NAME_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
)

_KEYWORDS = ("if", "else")


@dataclass
class Token:
    kind: str
    text: str
    position: int


def _read_quoted(source: str, pos: int) -> T.Tuple[str, int]:
    quote = source[pos]
    pos += 1
    start = pos
    while pos < len(source) and source[pos] != quote:
        pos += 1
    if pos >= len(source):
        raise ParseError(f"unterminated string in expression: {source!r}")
    return source[start:pos], pos + 1


def _read_call_arguments(source: str, pos: int) -> T.Tuple[str, int]:
    """Read from `(` to its matching `)`, tracking nesting and quotes.

    This is jazzoo's own argument syntax, not the surrounding interpreter's - which
    is why an embedded call can be found without parsing shell.
    """
    depth = 0
    quote: T.Optional[str] = None
    start = pos + 1
    while pos < len(source):
        char = source[pos]
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
                return source[start:pos], pos + 1
        pos += 1
    raise ParseError(f"unterminated call in expression: {source!r}")


def tokenize_expression(source: str) -> T.List[Token]:
    """Split an expression into tokens.

    A reference and its optional call arguments form one token, so the caller never
    has to rediscover where a call ends.
    """
    tokens: T.List[Token] = []
    pos = 0
    while pos < len(source):
        char = source[pos]

        if char.isspace():
            pos += 1
            continue

        if char in "\"'":
            text, pos = _read_quoted(source, pos)
            tokens.append(Token(kind="string", text=text, position=pos))
            continue

        sigil = next((s for s in _SIGIL_STARTS if source.startswith(s, pos)), None)
        if sigil is not None:
            start = pos
            pos += len(sigil)
            while pos < len(source) and source[pos] in _NAME_CHARS:
                pos += 1
            # A `(` directly after the name makes this a call; a space means the
            # paren is ordinary text.
            if pos < len(source) and source[pos] == "(":
                _, pos = _read_call_arguments(source, pos)
                tokens.append(
                    Token(kind="call", text=source[start:pos], position=start)
                )
            elif pos < len(source) and source[pos] == "\\":
                # A `\` ends the name; the text after it is a literal suffix, and
                # belongs to this same reference token.
                pos += 1
                while (
                    pos < len(source)
                    and not source[pos].isspace()
                    and source[pos] not in "|/"
                ):
                    if any(source.startswith(x, pos) for x in _SIGIL_STARTS):
                        break
                    pos += 1
                tokens.append(
                    Token(kind="reference", text=source[start:pos], position=start)
                )
                continue
            else:
                if pos < len(source) and source[pos] in "?":
                    pos += 1
                if source.startswith(":-", pos):
                    pos += 2
                    if pos < len(source) and source[pos] in "\"'":
                        _, pos = _read_quoted(source, pos)
                    else:
                        while pos < len(source) and not source[pos].isspace():
                            pos += 1
                tokens.append(
                    Token(kind="reference", text=source[start:pos], position=start)
                )
            continue

        if source.startswith("==", pos):
            tokens.append(Token(kind="==", text="==", position=pos))
            pos += 2
            continue

        if char == "|":
            tokens.append(Token(kind="|", text="|", position=pos))
            pos += 1
            continue

        if char == "/":
            tokens.append(Token(kind="/", text="/", position=pos))
            pos += 1
            continue

        if char in "[{":
            # `[` after a reference is a curry; anywhere else it opens a JSON
            # array. `{` always opens a JSON object.
            is_curry = char == "[" and bool(tokens) and tokens[-1].kind == "reference"
            closing = "]" if char == "[" else "}"
            depth, start = 0, pos
            if not is_curry:
                quote = None
                while pos < len(source):
                    c = source[pos]
                    if quote is not None:
                        if c == quote:
                            quote = None
                    elif c in "\"'":
                        quote = c
                    elif c == char:
                        depth += 1
                    elif c == closing:
                        depth -= 1
                        if depth == 0:
                            pos += 1
                            break
                    pos += 1
                tokens.append(
                    Token(kind="json", text=source[start:pos], position=start)
                )
                continue
            while pos < len(source):
                if source[pos] == "[":
                    depth += 1
                elif source[pos] == "]":
                    depth -= 1
                    if depth == 0:
                        pos += 1
                        break
                pos += 1
            tokens.append(Token(kind="curry", text=source[start:pos], position=start))
            continue

        # A bare word: an unquoted string, or the `if`/`else` keywords.
        start = pos
        while pos < len(source) and not source[pos].isspace() and source[pos] not in "|/[":
            if any(source.startswith(s, pos) for s in _SIGIL_STARTS):
                break
            if source.startswith("==", pos):
                break
            pos += 1
        if pos == start:
            pos += 1
            continue
        word = source[start:pos]
        kind = word if word in _KEYWORDS else "word"
        tokens.append(Token(kind=kind, text=word, position=start))

    return tokens
