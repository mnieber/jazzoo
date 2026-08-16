import typing as T

from jazzoo.settings import FALSY_VALUES


def is_truthy(value: T.Any) -> bool:
    """Whether a value counts as true in a ternary condition.

    Falsy: `false`, `null`, an empty array or object, the number 0, and a string
    whose lowercased form is an env-var-style negative. The decision is made on the
    value, not on its rendering - an empty array is falsy even though it renders as
    the non-empty text `[]`.
    """
    if isinstance(value, str):
        return value.lower() not in FALSY_VALUES
    if value is None or value is True or value is False:
        return bool(value)
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return bool(value)
