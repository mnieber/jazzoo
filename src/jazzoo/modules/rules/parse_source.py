import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ParseError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.assignment import Assignment
from jazzoo.modules.models.builtin_call import BuiltinCall
from jazzoo.modules.models.parsed_source import ParsedSource
from jazzoo.modules.rules.parse_attribute_line import (
    is_attribute_line,
    parse_attribute_line,
)
from jazzoo.modules.rules.parse_body import parse_body
from jazzoo.modules.rules.parse_call_arguments import parse_call_arguments
from jazzoo.modules.rules.parse_dependencies import parse_dependencies
from jazzoo.modules.rules.parse_parameters import parse_parameters
from jazzoo.utils.indent_of import indent_of
from jazzoo.utils.join_continuations import join_continuations

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

# `⚙️.<name>(args)` as a whole top-level line: a call to a ⚙️ function statement.
_BUILTIN_CALL_RE = re.compile(
    r"^(?:⚙️|⚙)\.(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\((?P<args>[^)]*)\)$"
)


def parse_source(source: str, filename: str) -> ParsedSource:
    """Parse a .jaz file into assignments, functions and imports.

    Bodies are captured as opaque lines: phase 1 never inspects their contents
    (design section 11).
    """
    result = ParsedSource(assignments=[], functions=[], imports=[], statements=[])
    entries = join_continuations(source.splitlines())

    pending_attributes: T.List[str] = []
    attribute_line_no = 0
    index = 0
    while index < len(entries):
        line_no, raw = entries[index]
        trimmed = raw.strip()

        if not trimmed or trimmed.startswith("#"):
            index += 1
            continue

        if is_attribute_line(trimmed):
            if not pending_attributes:
                attribute_line_no = line_no
            pending_attributes += parse_attribute_line(trimmed, filename, line_no)
            index += 1
            continue

        function_match = _FUNCTION_RE.match(trimmed)
        is_function = bool(function_match) and indent_of(raw) == 0
        if pending_attributes and not is_function:
            raise _attribute_without_function_error(filename, attribute_line_no)

        if trimmed.startswith("from "):
            result.imports.append((line_no, trimmed))
            index += 1
            continue

        if is_function:
            body_entries: T.List[T.Tuple[int, str]] = []
            index += 1
            while index < len(entries):
                body_no, body_raw = entries[index]
                if body_raw.strip() and indent_of(body_raw) == 0:
                    break
                body_entries.append((body_no, body_raw))
                index += 1
            blocks, local_functions = parse_body(body_entries, filename, 4)
            result.functions.append(
                Function(
                    name=function_match.group("name"),
                    parameters=parse_parameters(
                        function_match.group("params"), filename, line_no
                    ),
                    is_target="private" not in pending_attributes,
                    is_interactive="interactive" in pending_attributes,
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

        raise ParseError(f"cannot parse: {trimmed}", filename=filename, line=line_no)

    if pending_attributes:
        raise _attribute_without_function_error(filename, attribute_line_no)
    return result


def _attribute_without_function_error(filename: str, line: int) -> ParseError:
    return ParseError(
        "an attribute must precede a function", filename=filename, line=line
    )
