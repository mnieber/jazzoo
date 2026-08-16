import typing as T

from jazzoo.modules.models.absent import ABSENT


def get_by_path(value: T.Any, parts: T.List[str]) -> T.Any:
    """Walk a dotted path into a value, or return ABSENT.

    An object segment is a key; an array segment is a decimal index. Reaching into
    a scalar, or naming a key or index that is not there, yields ABSENT so the
    caller can apply the `?` and `:-` markers.
    """
    current = value
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return ABSENT
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                return ABSENT
            index = int(part)
            if index >= len(current):
                return ABSENT
            current = current[index]
        else:
            # A scalar has no fields.
            return ABSENT
    return current


def set_by_path(container: T.Dict[str, T.Any], parts: T.List[str], value: T.Any) -> None:
    """Assign into a dotted path, creating the objects along the way.

    Assigning under a value that is not an object replaces it, so a path assignment
    always succeeds rather than failing on the shape of what was there before.
    """
    current: T.Any = container
    for part in parts[:-1]:
        nxt = current.get(part) if isinstance(current, dict) else None
        if not isinstance(nxt, dict):
            nxt = {}
            current[part] = nxt
        current = nxt
    current[parts[-1]] = value
