import typing as T

from jazzoo.references.models.reference import Reference
from jazzoo.utils.dataclass import dataclass


@dataclass
class ReferenceMatch:
    reference: Reference
    start: int
    end: int
    # True when the sigil was escaped with a backslash: the text is emitted
    # literally (minus the backslash) rather than substituted.
    is_escaped: bool = False
    # Set when a `(` follows the name directly, making this a call rather than a
    # plain reference. Holds the whole `🐭.name(args)` text.
    call_text: T.Optional[str] = None
    # Set when a brace group holds more than a single reference, e.g. a ternary.
    # Holds the expression text between the braces; `reference` is then the first
    # reference in it, which is only used for its location.
    expression_text: T.Optional[str] = None
