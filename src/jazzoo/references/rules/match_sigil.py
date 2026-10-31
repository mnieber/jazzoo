import typing as T

from jazzoo.enums import Sigil

# Longest first, so ⚙️ (which carries a variation selector) is tried before its
# bare codepoint form.
SIGILS = sorted([s.value for s in Sigil] + ["⚙"], key=len, reverse=True)
SIGIL_BY_TEXT = {s.value: s for s in Sigil}
SIGIL_BY_TEXT["⚙"] = Sigil.SYSTEM


def match_sigil(text: str, pos: int) -> T.Optional[str]:
    for sigil in SIGILS:
        if text.startswith(sigil, pos):
            return sigil
    return None
