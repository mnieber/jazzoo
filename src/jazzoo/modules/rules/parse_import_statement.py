import re
import typing as T

from jazzoo.errors import ParseError
from jazzoo.modules.models.import_statement import ImportedSymbol, ImportStatement

_IMPORT_RE = re.compile(
    r"^from\s+(?P<path>\S+)\s+(?P<kind>import|export)\s+(?P<rest>.*)$"
)

# `<name>` or `<name> as <alias>`
_SYMBOL_RE = re.compile(
    r"^(?P<name>\*|[A-Za-z_][A-Za-z0-9_-]*)"
    r"(?:\s+as\s+(?P<alias>[A-Za-z_][A-Za-z0-9_-]*))?$"
)


def _parse_symbols(text: str) -> T.Tuple[T.List[ImportedSymbol], bool]:
    """Parse the symbol list, which may be a single name or a parenthesised tuple."""
    text = text.strip()
    if text.startswith("("):
        closing = text.rfind(")")
        if closing == -1:
            raise ParseError(f"unterminated symbol list: {text}")
        inner = text[1:closing]
    else:
        inner = text

    symbols: T.List[ImportedSymbol] = []
    is_wildcard = False
    for chunk in inner.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = _SYMBOL_RE.match(chunk)
        if match is None:
            raise ParseError(f"cannot parse imported symbol: {chunk}")
        name = match.group("name")
        if name == "*":
            is_wildcard = True
            continue
        symbols.append(
            ImportedSymbol(name=name, alias=match.group("alias") or name)
        )
    return symbols, is_wildcard


def parse_import_statement(
    text: str, filename: str, line: int
) -> ImportStatement:
    """Parse one `from <path> import|export ...` line.

    `import` places the symbols under a mandatory namespace alias and keeps them
    private; `export` lands them flat in 🐭 and makes them targets.
    """
    match = _IMPORT_RE.match(text.strip())
    if match is None:
        raise ParseError(f"cannot parse import: {text}", filename=filename, line=line)

    rest = match.group("rest").strip()
    is_export = match.group("kind") == "export"

    alias: T.Optional[str] = None
    if not is_export:
        alias, rest = _split_trailing_alias(rest)
        # The trailing `as <namespace>` is mandatory for import.
        if alias is None:
            raise ParseError(
                "an import must end with `as <namespace>`",
                filename=filename,
                line=line,
            )

    symbols, is_wildcard = _parse_symbols(rest)
    return ImportStatement(
        path=match.group("path"),
        symbols=symbols,
        is_wildcard=is_wildcard,
        is_export=is_export,
        alias=alias,
        filename=filename,
        line=line,
    )


def _split_trailing_alias(rest: str) -> T.Tuple[T.Optional[str], str]:
    """Split a trailing `as <name>` off a symbol list.

    The alias is whatever follows the last `as` *outside* the tuple, so a rename
    inside the parentheses is left alone. Returns `(None, rest)` unchanged when
    there is no trailing alias.
    """
    closing = rest.rfind(")")
    tail_start = closing + 1 if closing != -1 else 0
    tail = rest[tail_start:]
    match = re.search(r"\s+as\s+([A-Za-z_][A-Za-z0-9_-]*)\s*$", tail)
    if match is None:
        return None, rest
    return match.group(1), rest[:tail_start] + tail[: match.start()]
