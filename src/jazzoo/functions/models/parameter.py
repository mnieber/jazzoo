import typing as T

from dataclassy import dataclass


@dataclass
class Parameter:
    name: str
    # The default's expression source, evaluated at call time. None means the
    # parameter is required.
    default: T.Optional[str] = None
