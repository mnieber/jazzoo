import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.functions.models.function import Function
from jazzoo.module_validation.rules.validate_builtin_call import validate_builtin_call
from jazzoo.module_validation.rules.validate_call import validate_call
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_call_arguments import parse_call_arguments
from jazzoo.modules.rules.parse_source import _SIGIL_TEXTS

# A call is only a call when it is the whole line, or the whole right-hand side of
# an assignment. Scanning shell text for anything call-shaped would misread
# `echo "Hello 🐆.who (tracing=🐭.tracing)"` as a call to `who`.
_CALL_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>[^)]*)\)$"
)


def validate_call_text(
    text: str,
    module: Module,
    function: Function,
    filename: T.Optional[str],
    line: T.Optional[int],
    function_valued: T.Dict[str, Function],
) -> None:
    """Check the call that is the whole of text, if text is a call."""
    match = _CALL_RE.match(text)
    if match is None:
        return
    arguments = parse_call_arguments(match.group("args"), None, None)
    if _SIGIL_TEXTS[match.group("sigil")] is Sigil.SYSTEM:
        validate_builtin_call(
            match.group("path"), [(a.name, a.value) for a in arguments], filename, line
        )
        return
    validate_call(
        match.group("path"),
        [(a.name, a.value) for a in arguments],
        module,
        function,
        filename,
        line,
        function_valued,
    )
