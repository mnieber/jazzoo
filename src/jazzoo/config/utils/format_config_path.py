import typing as T


def format_config_path(segments: T.Sequence[T.Any]) -> str:
    return "/" + "/".join(str(segment) for segment in segments)
