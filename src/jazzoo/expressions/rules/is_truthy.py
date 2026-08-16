from jazzoo.settings import FALSY_VALUES


def is_truthy(value: str) -> bool:
    """A string is falsy if its lowercased form is one of the env-var-style flags."""
    return value.lower() not in FALSY_VALUES
