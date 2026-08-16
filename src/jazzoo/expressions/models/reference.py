import typing as T

from dataclassy import dataclass

from jazzoo.enums import Sigil


@dataclass
class Reference:
    sigil: Sigil
    # Dotted name parts: ["log-level"], or ["module", "basename"] for ⚙️.
    parts: T.List[str]
    # Set by `?`: an absent reference resolves to "" instead of raising.
    is_optional: bool = False
    # Set by `:-`: used when the resolved value is empty.
    default: T.Optional[str] = None
    filename: T.Optional[str] = None
    line: T.Optional[int] = None

    @property
    def name(self) -> str:
        return ".".join(self.parts)
