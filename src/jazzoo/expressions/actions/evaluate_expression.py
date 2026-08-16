import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.expressions.rules.parse_references import parse_references
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.modules.rules.parse_source import _split_top_level, parse_call_arguments

# `<sigil>.<dotted path>(...)` - a call, as opposed to a bare reference. The
# parenthesis must follow the name directly, so `🐆.who (x=1)` inside a shell line
# is not read as a call.
_CALL_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>.*)\)$",
    re.S,
)

_SIGILS = {s.value: s for s in Sigil}
_SIGILS["⚙"] = Sigil.SYSTEM


def _strip_quotes(text: str) -> T.Tuple[str, bool]:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1], True
    return text, False


def evaluate_expression(source: str, frame) -> str:
    """Evaluate one jazzoo expression against the current namespace state."""
    from jazzoo.expressions.rules.resolve_reference import resolve_reference
    from jazzoo.functions.actions.call_function import call_function, _lookup_function

    source = source.strip()
    if not source:
        return ""

    call = _CALL_RE.match(source)
    if call:
        sigil = _SIGILS[call.group("sigil")]
        path = call.group("path")
        arguments = parse_call_arguments(call.group("args"), None, None)
        for argument in arguments:
            if argument.name is None:
                raise ArgumentError(
                    f"arguments must be named in a .jaz file: {path}(...)",
                )
        resolved = {
            argument.name: evaluate_expression(argument.value, frame)
            for argument in arguments
        }

        class _Site:
            filename = None
            line = None

        target = _lookup_function(path, frame, _Site())
        return call_function(target, resolved, frame, evaluate_expression)

    # A quoted or bare string, with any references inside substituted.
    text, was_quoted = _strip_quotes(source)
    matches = parse_references(text)
    if not was_quoted and len(matches) == 1 and matches[0].start == 0 and matches[0].end == len(text):
        # A lone reference keeps its value's type rather than being stringified.
        return resolve_reference(matches[0].reference, frame)

    return substitute_references(
        text, lambda reference: resolve_reference(reference, frame)
    )
