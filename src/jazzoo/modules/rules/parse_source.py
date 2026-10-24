import re
import typing as T

from dataclassy import dataclass

from jazzoo.blocks.models.block import Block, BlockLine
from jazzoo.enums import BlockMode, Sigil
from jazzoo.errors import ParseError
from jazzoo.functions.models.call_site import Argument, CallSite
from jazzoo.functions.models.function import Function
from jazzoo.functions.models.parameter import Parameter
from jazzoo.settings import DEFAULT_SHEBANG

_SIGIL_TEXTS = {s.value: s for s in Sigil}
_SIGIL_TEXTS["⚙"] = Sigil.SYSTEM

# `<sigil>.<name> = <rhs>` at the start of a trimmed line.
_ASSIGNMENT_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<name>[A-Za-z0-9_][A-Za-z0-9_.-]*)\s*=\s*(?P<rhs>.*)$"
)

# `name(params):` optionally preceded by nothing, optionally followed by deps.
_FUNCTION_RE = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*\((?P<params>[^)]*)\)\s*:(?P<deps>.*)$"
)

# A local function definition: `🐆.name(params):`
_LOCAL_FUNCTION_RE = re.compile(
    r"^🐆\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*\((?P<params>[^)]*)\)\s*:\s*$"
)

_ATTRIBUTE_RE = re.compile(r"^\[(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\]$")

# `⚙️.<name>(args)` as a whole top-level line: a call to a ⚙️ function statement.
_BUILTIN_CALL_RE = re.compile(
    r"^(?:⚙️|⚙)\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\((?P<args>[^)]*)\)$"
)


@dataclass
class Assignment:
    sigil: Sigil
    name: str
    rhs: str
    filename: T.Optional[str] = None
    line: T.Optional[int] = None


@dataclass
class BuiltinCall:
    # The whole `⚙️.name(args)` text, which is evaluated like any other call.
    text: str
    name: str
    arguments: T.List[Argument] = []
    filename: T.Optional[str] = None
    line: T.Optional[int] = None


@dataclass
class ParsedSource:
    assignments: T.List[Assignment] = []
    functions: T.List[Function] = []
    imports: T.List[T.Any] = []
    # Assignments and ⚙️ calls in file order, which is the order they run in.
    statements: T.List[T.Union[Assignment, BuiltinCall]] = []


def _indent_of(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" "))


def _split_top_level(text: str, separator: str) -> T.List[str]:
    """Split on `separator`, ignoring occurrences inside quotes or brackets."""
    parts: T.List[str] = []
    depth = 0
    quote: T.Optional[str] = None
    current = ""
    for char in text:
        if quote is not None:
            current += char
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current += char
            continue
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        if char == separator and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    if current.strip():
        parts.append(current)
    return parts


def parse_parameters(
    text: str, filename: str, line: int
) -> T.List[Parameter]:
    parameters: T.List[Parameter] = []
    for chunk in _split_top_level(text, ","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            name, _, default = chunk.partition("=")
            parameters.append(Parameter(name=name.strip(), default=default.strip()))
        else:
            parameters.append(Parameter(name=chunk, default=None))
    return parameters


def parse_call_arguments(
    text: str, filename: str, line: int
) -> T.List[Argument]:
    arguments: T.List[Argument] = []
    for chunk in _split_top_level(text, ","):
        chunk = chunk.strip()
        if not chunk:
            continue
        name, sep, value = chunk.partition("=")
        if not sep:
            # Positional - parsed so validation can report it, per design section 12.
            arguments.append(Argument(name=None, value=chunk))
        else:
            arguments.append(Argument(name=name.strip(), value=value.strip()))
    return arguments


def parse_dependencies(
    text: str, filename: str, line: int
) -> T.List[CallSite]:
    """Parse the dependency list that follows a function's colon."""
    dependencies: T.List[CallSite] = []
    for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_.-]*)\s*\(([^)]*)\)", text):
        dependencies.append(
            CallSite(
                target_path=match.group(1),
                arguments=parse_call_arguments(match.group(2), filename, line),
                filename=filename,
                line=line,
            )
        )
    return dependencies


def _join_continuations(
    lines: T.List[str],
) -> T.List[T.Tuple[int, str]]:
    """Fold backslash-continued lines into one, keeping the first line's number."""
    joined: T.List[T.Tuple[int, str]] = []
    buffer = ""
    start_line = 0
    for index, raw in enumerate(lines, start=1):
        stripped = raw.rstrip("\n")
        if buffer:
            buffer = buffer + " " + stripped.strip()
        else:
            start_line = index
            buffer = stripped
        if buffer.rstrip().endswith("\\"):
            buffer = buffer.rstrip()[:-1].rstrip()
            continue
        joined.append((start_line, buffer))
        buffer = ""
    if buffer:
        joined.append((start_line, buffer))
    return joined


def _parse_body(
    entries: T.List[T.Tuple[int, str]], filename: str, base_indent: int
) -> T.Tuple[T.List[Block], T.List[Function]]:
    """Split an indented body into blocks, extracting nested local functions."""
    blocks: T.List[Block] = []
    locals_: T.List[Function] = []

    current = Block(mode=BlockMode.JAZZOO, shebang=None, lines=[], filename=filename)
    index = 0
    while index < len(entries):
        line_no, raw = entries[index]
        trimmed = raw.strip()

        if not trimmed:
            index += 1
            continue

        local_match = _LOCAL_FUNCTION_RE.match(trimmed)
        if local_match:
            # Everything indented further than this header belongs to the local body.
            header_indent = _indent_of(raw)
            inner: T.List[T.Tuple[int, str]] = []
            index += 1
            while index < len(entries):
                inner_no, inner_raw = entries[index]
                if inner_raw.strip() and _indent_of(inner_raw) <= header_indent:
                    break
                inner.append((inner_no, inner_raw))
                index += 1
            inner_blocks, inner_locals = _parse_body(
                inner, filename, header_indent + 4
            )
            local_fn = Function(
                name=local_match.group("name"),
                parameters=parse_parameters(
                    local_match.group("params"), filename, line_no
                ),
                is_target=False,
                body=inner_blocks,
                functions=inner_locals,
                filename=filename,
                line=line_no,
            )
            locals_.append(local_fn)
            continue

        if trimmed.startswith("#!"):
            if current.lines:
                blocks.append(current)
            if trimmed == "#!":
                # A bare shebang returns to the default jazzoo mode.
                current = Block(
                    mode=BlockMode.JAZZOO, shebang=None, lines=[], filename=filename
                )
            else:
                current = Block(
                    mode=BlockMode.SHEBANG,
                    shebang=trimmed,
                    lines=[],
                    filename=filename,
                )
            index += 1
            continue

        if trimmed.startswith("#") and current.mode == BlockMode.JAZZOO:
            # A full-line comment is dropped here, so it never becomes a block: it is
            # not substituted, not echoed, and does not touch ⚙️.stdout. `#!` already
            # returned above. Inside a shebang block the `#` belongs to that
            # interpreter, so this only applies in jazzoo mode.
            index += 1
            continue

        is_quiet = trimmed.startswith("@")
        text = trimmed[1:] if is_quiet else raw.rstrip()
        if current.mode == BlockMode.SHEBANG and not is_quiet:
            # Keep the interpreter's own indentation, relative to the body.
            text = raw.rstrip()
            if text.startswith(" " * base_indent):
                text = text[base_indent:]
        elif not is_quiet:
            text = trimmed

        current.lines.append(BlockLine(text=text, line=line_no, is_quiet=is_quiet))
        index += 1

    if current.lines:
        blocks.append(current)
    return blocks, locals_


def parse_source(source: str, filename: str) -> ParsedSource:
    """Parse a .jaz file into assignments, functions and imports.

    Bodies are captured as opaque lines: phase 1 never inspects their contents
    (design section 11).
    """
    result = ParsedSource(assignments=[], functions=[], imports=[], statements=[])
    entries = _join_continuations(source.splitlines())

    pending_attributes: T.List[str] = []
    index = 0
    while index < len(entries):
        line_no, raw = entries[index]
        trimmed = raw.strip()

        if not trimmed or trimmed.startswith("#"):
            index += 1
            continue

        attribute_match = _ATTRIBUTE_RE.match(trimmed)
        if attribute_match:
            pending_attributes.append(attribute_match.group("name"))
            index += 1
            continue

        if trimmed.startswith("from "):
            result.imports.append((line_no, trimmed))
            index += 1
            continue

        function_match = _FUNCTION_RE.match(trimmed)
        if function_match and _indent_of(raw) == 0:
            body_entries: T.List[T.Tuple[int, str]] = []
            index += 1
            while index < len(entries):
                body_no, body_raw = entries[index]
                if body_raw.strip() and _indent_of(body_raw) == 0:
                    break
                body_entries.append((body_no, body_raw))
                index += 1
            blocks, local_functions = _parse_body(body_entries, filename, 4)
            result.functions.append(
                Function(
                    name=function_match.group("name"),
                    parameters=parse_parameters(
                        function_match.group("params"), filename, line_no
                    ),
                    is_target="private" not in pending_attributes,
                    dependencies=parse_dependencies(
                        function_match.group("deps"), filename, line_no
                    ),
                    body=blocks,
                    functions=local_functions,
                    filename=filename,
                    line=line_no,
                )
            )
            pending_attributes = []
            continue

        assignment_match = _ASSIGNMENT_RE.match(trimmed)
        if assignment_match:
            sigil = _SIGIL_TEXTS[assignment_match.group("sigil")]
            if sigil is Sigil.SYSTEM:
                raise ParseError(
                    "cannot assign to the read-only ⚙️ namespace",
                    filename=filename,
                    line=line_no,
                )
            assignment = Assignment(
                sigil=sigil,
                name=assignment_match.group("name"),
                rhs=assignment_match.group("rhs").strip(),
                filename=filename,
                line=line_no,
            )
            result.assignments.append(assignment)
            result.statements.append(assignment)
            index += 1
            continue

        builtin_match = _BUILTIN_CALL_RE.match(trimmed)
        if builtin_match:
            result.statements.append(
                BuiltinCall(
                    text=trimmed,
                    name=builtin_match.group("name"),
                    arguments=parse_call_arguments(
                        builtin_match.group("args"), filename, line_no
                    ),
                    filename=filename,
                    line=line_no,
                )
            )
            index += 1
            continue

        raise ParseError(
            f"cannot parse: {trimmed}", filename=filename, line=line_no
        )

    return result
