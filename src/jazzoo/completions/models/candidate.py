import typing as T

from jazzoo.utils.dataclass import dataclass


@dataclass
class Candidate:
    text: str
    # Fish shows the description next to the candidate, but does not insert it
    description: T.Optional[str] = None
