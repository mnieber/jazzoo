import typing as T

from jazzoo.expressions.rules.parse_references import parse_references
from jazzoo.expressions.rules.resolve_function_value import resolve_function_value
from jazzoo.expressions.utils.render_value import render_value
from jazzoo.modules.models.absent import ABSENT


def resolve_reference_text(text: str, frame) -> T.Any:
    """Resolve a reference in expression position.

    A dotted name walks into a structured value, so the first segment names the
    variable and the rest is a path. Text after the reference - which only occurs
    when a `\\` terminated the name - is literal.
    """
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    matches = parse_references(text)
    if not matches:
        return text

    match = matches[0]
    suffix = text[match.end :]

    # A bare symbol in expression position may name a function rather than a
    # variable, in which case it is the function value (same as `f[]`).
    stored = frame.lookup(match.reference.sigil, match.reference.parts[0])
    if stored is ABSENT:
        function_value = resolve_function_value(text, frame)
        if function_value is not None:
            return function_value

    value = resolve_reference(match.reference, frame)
    if not suffix:
        # A lone reference keeps its value's type rather than being rendered.
        return value
    return f"{render_value(value)}{suffix}"
