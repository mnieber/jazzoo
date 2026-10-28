import typing as T


def merge_config(base: T.Dict[T.Any, T.Any], layer: T.Dict[T.Any, T.Any]) -> T.Dict:
    result = dict(base)
    for key, value in layer.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result
