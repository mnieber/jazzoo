import re
import typing as T

from jazzoo.blocks.models.block import Block, BlockLine
from jazzoo.enums import BlockMode
from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.modules.rules.parse_attribute_line import (
    is_attribute_line,
    parse_attribute_line,
)
from jazzoo.modules.rules.match_function_header import match_function_header
from jazzoo.modules.rules.parse_parameters import parse_parameters
from jazzoo.utils.indent_of import indent_of
from jazzoo.utils.join_continuations import join_continuations

# The start of a local function definition: `🐆.name(params):`
_LOCAL_FUNCTION_NAME_RE = re.compile(r"^🐆\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*\(")


def parse_body(
    entries: T.List[T.Tuple[int, str]], filename: str, base_indent: int
) -> T.Tuple[T.List[Block], T.List[Function]]:
    """Split an indented body into blocks, extracting nested local functions."""
    blocks: T.List[Block] = []
    locals_: T.List[Function] = []

    entries = list(entries)
    current = Block(mode=BlockMode.JAZZOO, shebang=None, lines=[], filename=filename)
    pending_attributes: T.List[str] = []
    attribute_line_no = 0
    index = 0
    while index < len(entries):
        line_no, raw = entries[index]
        trimmed = raw.strip()

        if not trimmed:
            index += 1
            continue

        # Only jazzoo-mode lines continue: a shebang body is the interpreter's, and a
        # comment never continues
        if current.mode == BlockMode.JAZZOO and not trimmed.startswith("#"):
            joined, end = join_continuations(entries, index)
            entries[index:end] = [joined]
            raw = joined[1]
            trimmed = raw.strip()

        # Inside a shebang block the line belongs to that interpreter
        if current.mode == BlockMode.JAZZOO and is_attribute_line(trimmed):
            names = parse_attribute_line(trimmed, filename, line_no)
            if "private" in names:
                raise ParseError(
                    "a local function cannot be [private]: it is never a target",
                    filename=filename,
                    line=line_no,
                )
            if not pending_attributes:
                attribute_line_no = line_no
            pending_attributes += names
            index += 1
            continue

        local_match = match_function_header(_LOCAL_FUNCTION_NAME_RE, trimmed)
        if local_match is not None and local_match.rest.strip():
            local_match = None
        if pending_attributes and not local_match:
            raise _attribute_without_function_error(filename, attribute_line_no)

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
                name=local_match.name,
                parameters=parse_parameters(local_match.params, filename, line_no),
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

    if pending_attributes:
        raise _attribute_without_function_error(filename, attribute_line_no)
    if current.lines:
        blocks.append(current)
    return blocks, locals_


def _attribute_without_function_error(filename: str, line: int) -> ParseError:
    return ParseError(
        "an attribute must precede a local function", filename=filename, line=line
    )
