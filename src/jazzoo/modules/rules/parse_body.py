import re
import typing as T

from jazzoo.blocks.models.block import Block, BlockLine
from jazzoo.enums import BlockMode
from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.modules.rules.parse_parameters import parse_parameters
from jazzoo.settings import KNOWN_ATTRIBUTES
from jazzoo.utils.indent_of import indent_of

# A local function definition: `🐆.name(params):`
_LOCAL_FUNCTION_RE = re.compile(
    r"^🐆\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*\((?P<params>[^)]*)\)\s*:\s*$"
)

# An attribute of a local function: `[name]`
_ATTRIBUTE_RE = re.compile(r"^\[(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\]$")


def parse_body(
    entries: T.List[T.Tuple[int, str]], filename: str, base_indent: int
) -> T.Tuple[T.List[Block], T.List[Function]]:
    """Split an indented body into blocks, extracting nested local functions."""
    blocks: T.List[Block] = []
    locals_: T.List[Function] = []

    current = Block(mode=BlockMode.JAZZOO, shebang=None, lines=[], filename=filename)
    pending_attributes: T.List[str] = []
    index = 0
    while index < len(entries):
        line_no, raw = entries[index]
        trimmed = raw.strip()

        if not trimmed:
            index += 1
            continue

        # A `[name]` line is an attribute only when a local function header follows
        # it; otherwise it stays a shell line, as before.
        attribute_match = _ATTRIBUTE_RE.match(trimmed)
        if (
            attribute_match
            and current.mode == BlockMode.JAZZOO
            and _precedes_local_function(entries, index)
        ):
            name = attribute_match.group("name")
            if name not in KNOWN_ATTRIBUTES:
                raise ParseError(
                    f"unknown attribute: [{name}]", filename=filename, line=line_no
                )
            if name == "private":
                raise ParseError(
                    "a local function cannot be [private]: it is never a target",
                    filename=filename,
                    line=line_no,
                )
            pending_attributes.append(name)
            index += 1
            continue

        local_match = _LOCAL_FUNCTION_RE.match(trimmed)
        if local_match:
            # Everything indented further than this header belongs to the local body.
            header_indent = indent_of(raw)
            inner: T.List[T.Tuple[int, str]] = []
            index += 1
            while index < len(entries):
                inner_no, inner_raw = entries[index]
                if inner_raw.strip() and indent_of(inner_raw) <= header_indent:
                    break
                inner.append((inner_no, inner_raw))
                index += 1
            inner_blocks, inner_locals = parse_body(inner, filename, header_indent + 4)
            local_fn = Function(
                name=local_match.group("name"),
                parameters=parse_parameters(
                    local_match.group("params"), filename, line_no
                ),
                is_target=False,
                is_interactive="interactive" in pending_attributes,
                body=inner_blocks,
                functions=inner_locals,
                filename=filename,
                line=line_no,
            )
            locals_.append(local_fn)
            pending_attributes = []
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


def _precedes_local_function(entries: T.List[T.Tuple[int, str]], index: int) -> bool:
    # Skip blank lines and further attributes, so that attributes may be stacked
    for _, raw in entries[index + 1 :]:
        trimmed = raw.strip()
        if not trimmed or _ATTRIBUTE_RE.match(trimmed):
            continue
        return bool(_LOCAL_FUNCTION_RE.match(trimmed))
    return False
