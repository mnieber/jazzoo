import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ResolutionError
from jazzoo.expressions.actions.call_curried import call_curried
from jazzoo.expressions.actions.resolve_arguments import resolve_arguments
from jazzoo.expressions.rules.resolve_function_value import resolve_function_value
from jazzoo.functions.rules.lookup_function import lookup_function
from jazzoo.modules.rules.parse_source import _SIGIL_TEXTS

# Splits `🐭.name(args)` into its name and its argument text.
_CALL_PARTS_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>.*)\)$",
    re.S,
)


def evaluate_call(text: str, frame) -> str:
    """Evaluate a `🐭.name(args)` call and return its value."""
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.functions.actions.call_function import call_function

    match = _CALL_PARTS_RE.match(text)
    if match is None:
        raise ResolutionError(f"cannot parse call: {text}")

    path = match.group("path")
    resolved = resolve_arguments(match.group("args"), path, frame)

    sigil_text = match.group("sigil")
    if _SIGIL_TEXTS[sigil_text] is Sigil.SYSTEM:
        return _call_builtin(path, resolved)

    stored = resolve_function_value(f"{sigil_text}.{path}", frame)
    if stored is not None and (stored.bound or stored.explicitly_unbound):
        return call_curried(stored, resolved, frame)

    target = lookup_function(path, frame)
    return call_function(target, resolved, frame, evaluate_expression)


def _call_builtin(name: str, arguments: T.Dict[str, T.Any]) -> str:
    from jazzoo.functions.actions.call_builtin_function import (
        call_builtin_function,
        is_builtin_function,
    )

    if not is_builtin_function(name):
        raise ResolutionError(f"no such function: ⚙️.{name}")
    return call_builtin_function(name, arguments)
