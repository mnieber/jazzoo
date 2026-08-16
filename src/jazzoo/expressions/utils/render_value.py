import json
import typing as T


def render_value(value: T.Any) -> str:
    """Render a value as the text substitution splices into a line.

    A scalar renders bare, so a variable holding a string behaves exactly as it did
    before structured values existed. A container renders as compact JSON, which a
    tool like `jq` can consume. `null` renders as the empty string.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    return json.dumps(value, separators=(",", ":"))
