import typing as T


def split_config_path(path: str) -> T.List[str]:
    if not path.startswith("/"):
        raise ValueError(f"a config path must start with '/': {path}")
    return [segment for segment in path.split("/") if segment]
