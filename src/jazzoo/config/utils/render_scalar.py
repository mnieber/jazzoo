import json
import typing as T


def render_scalar(value: T.Any) -> str:
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
    # E.g. a date that YAML parsed
    return str(value)
