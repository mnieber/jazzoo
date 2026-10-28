import re
import typing as T

from jazzoo.blocks.models.block import Block, BlockLine
from jazzoo.enums import BlockMode
from jazzoo.functions.models.function import Function
from jazzoo.modules.rules.parse_parameters import parse_parameters
from jazzoo.utils.indent_of import indent_of

# A local function definition: `🐆.name(params):`
_LOCAL_FUNCTION_RE = re.compile(
    r"^🐆\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*\((?P<params>[^)]*)\)\s*:\s*$"
)


def parse_body(
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
