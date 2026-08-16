import typing as T

from dataclassy import dataclass


@dataclass
class Parameter:
    name: str
    # None means the parameter is required.
    default: T.Optional[str] = None
