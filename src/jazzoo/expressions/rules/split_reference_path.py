import typing as T

from jazzoo.enums import Sigil

_SIGIL_BY_TEXT = {s.value: s for s in Sigil}
_SIGIL_BY_TEXT["⚙"] = Sigil.SYSTEM

_SIGILS = sorted(_SIGIL_BY_TEXT, key=len, reverse=True)


def split_reference_path(text: str) -> T.Optional[T.Tuple[Sigil, str]]:
    """Split `🐭.h.make-full-path` into its sigil and full dotted path.

    Used where a name may legitimately be dotted because it walks module
    namespaces - function symbols, curry targets and pipe stages. Plain variable
    references stop at the first dot instead, which is what parse_references does.
    """
    text = text.strip()
    for sigil in _SIGILS:
        if text.startswith(sigil):
            rest = text[len(sigil) :]
            if rest.startswith("."):
                return _SIGIL_BY_TEXT[sigil], rest[1:]
            return None
    return None
